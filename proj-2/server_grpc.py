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

    def send_message_socket(self, message):
        message = message.encode('utf-8')
        self.sock.sendto(message, (self.sock_host, self.sock_port))

    def receive_message_socket(self):
        while True:
            data, addr = self.sock.recvfrom(int(os.getenv('BUFFER_SIZE')))
            return data.decode('utf-8')

    def run(self):
        try:
            server = threading.Thread(name='server_grpc', target=self.start_server)
            server.start()
        except KeyboardInterrupt:
            exit(0)

    def listen_key(self, request, context):
        metadata = dict(context.invocation_metadata())
        print('gRPC--->\t' + str(metadata))

        commands = request
        for command in commands:
            self.send_message_socket(command.command)
            return_data = self.receive_message_socket()
            yield configuration_pb2.listenKeyReply(message=return_data)
