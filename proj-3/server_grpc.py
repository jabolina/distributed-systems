from concurrent import futures
import socket
import dotenv
import os
import threading

import grpc
import time
import queue
import configuration_pb2
import configuration_pb2_grpc


dotenv.load()


ONE_DAY_IN_SECONDS = 60 * 60 * 24


class ServerGRPC(configuration_pb2_grpc.ServerGRPCServicer):
    def __init__(self):
        self.sock = self.create_socket()
        self.sock_port = int(os.getenv('SERVER_PORT'))
        self.sock_host = os.getenv('HOST')
        self.server = None
        self.port = int(os.getenv('GRPC_PORT'))
        self.queues = dict()

    def create_grpc_server(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=int(os.getenv('MAX_WORKERS'))))
        configuration_pb2_grpc.add_ServerGRPCServicer_to_server(ServerGRPC(), self.server)
        self.server.add_insecure_port('[::]:' + os.getenv('GRPC_PORT'))

    @staticmethod
    def create_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock

    def start_server(self):
        if self.server is not None:
            print('Started gRPC server.')
            self.server.start()
            try:
                while True:
                    time.sleep(ONE_DAY_IN_SECONDS)
            except KeyboardInterrupt:
                exit(0)
        else:
            print('Server gRPC was not created to start.')

    def send_message_socket(self, message, client_socket):
        message = message.encode('utf-8')
        client_socket.sendto(message, (self.sock_host, self.sock_port))

    def receive_message_socket(self, client_socket, pid):
        while True:
            data, addr = client_socket.recvfrom(int(os.getenv('BUFFER_SIZE')))
            self.queues[pid]['response'].put(data.decode('utf-8'))

    def keep_stream_alive(self, pid):
        while True:
            if not self.queues[pid]['commands'].empty():
                self.send_message_socket(self.queues[pid]['commands'].get(), self.queues[pid]['sock'])

    def run(self):
        try:
            server = threading.Thread(name='server_grpc', target=self.start_server)
            server.start()
        except KeyboardInterrupt:
            exit(0)

    def verify_queue(self, command, context):
        while True:
            while not self.queues[command.pid]['response'].empty():
                yield configuration_pb2.listenKeyReply(message=self.queues[command.pid]['response'].get())

    def listen_key(self, command, context):
        metadata = dict(context.invocation_metadata())
        print('gRPC--->\t' + str(metadata))

        if command.pid in self.queues.keys():
            self.queues[command.pid]['commands'].put(command.command)
        elif command.pid not in self.queues.keys():
            self.queues[command.pid] = {'commands': queue.Queue(),
                                        'sock': self.create_socket(),
                                        'response': queue.Queue(),
                                        'grpc': configuration_pb2.listenKeyReply}
            commands_object = self.queues[command.pid]
            commands_object['commands'].put(command.command)

            receive = threading.Thread(target=self.receive_message_socket, args=(commands_object['sock'], command.pid))
            receive.start()

            stream = threading.Thread(target=self.keep_stream_alive, args=(command.pid,))
            stream.start()

        return self.queues[command.pid]['grpc']()
