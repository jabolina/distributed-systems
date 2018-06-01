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
import snapshooter

shared_queues = dict()
lock = threading.Lock()

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

    def send_message_socket(self, message, client_socket):
        message = message.encode('utf-8')
        client_socket.sendto(message, (self.sock_host, self.sock_port))

    @staticmethod
    def receive_message_socket(client_socket, pid):
        while True:
            data, addr = client_socket.recvfrom(int(os.getenv('BUFFER_SIZE')))
            shared_queues[pid]['response'].put(data.decode('utf-8'))

    def keep_stream_alive(self, pid):
        while True:
            if not shared_queues[pid]['commands'].empty():
                self.send_message_socket(shared_queues[pid]['commands'].get(), shared_queues[pid]['sock'])

    @staticmethod
    def snap_structure():
        while True:
            time.sleep(int(os.getenv('SNAPSHOT_SEC')))

            snapshooter.move_structures()
            snapshooter.save_structs('struct_', time.time(), shared_queues, '.struct')
            snapshooter.remove_old_structs()

    def run(self):
        global shared_queues
        try:
            name = os.popen('ls | grep -m 1 struct_').readlines()
            pid_list = []
            if len(name) > 0:
                shared_queues, pid_list = snapshooter.retrieve_structs(name[0].replace('\n', ''))

            if shared_queues is None:
                name = os.popen('ls -c dir_struct/ | grep -m 1 struct_').readlines()
                if len(name) > 0:
                    shared_queues, pid_list = snapshooter.retrieve_structs('dir_struct/' + name[0].replace('\n', ''))

            self.create_send_receive_threads(pid_list)

            server = threading.Thread(name='server_grpc', target=self.start_server)
            server.start()

            snaping = threading.Thread(name='save_structure', target=self.snap_structure)
            snaping.start()
        except KeyboardInterrupt:
            exit(0)

    def create_send_receive_threads(self, pid_list, command=None):

        for pid in pid_list:
            commands_object = shared_queues[pid]

            if command is not None:
                commands_object['commands'].put(command)

            receive = threading.Thread(target=self.receive_message_socket,
                                       args=(commands_object['sock'], pid))
            receive.start()

            stream = threading.Thread(target=self.keep_stream_alive, args=(pid,))
            stream.start()

    @staticmethod
    def verify_queue(command, context):
        while True:
            while not shared_queues[command.pid]['response'].empty():
                yield configuration_pb2.listenKeyReply(message=shared_queues[command.pid]['response'].get())

    def listen_key(self, command, context):
        metadata = dict(context.invocation_metadata())
        print('gRPC--->\t' + str(metadata))

        lock.acquire()

        if command.pid in shared_queues.keys():
            shared_queues[command.pid]['commands'].put(command.command)
        elif command.pid not in shared_queues.keys():
            shared_queues[command.pid] = {'commands': queue.Queue(),
                                          'sock': self.create_socket(),
                                          'response': queue.Queue()}
            self.create_send_receive_threads([command.pid], command.command)
        lock.release()

        return configuration_pb2.listenKeyReply()
