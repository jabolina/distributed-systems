from concurrent import futures
import socket
import dotenv
import os
import threading

import grpc
import configuration_pb2
import configuration_pb2_grpc


dotenv.load()


class ServerGRPC(configuration_pb2_grpc.ServerGRPCServicer):
    def __init__(self):
        self.sock = self.connect_to_socket()
        self.sock_port = int(os.getenv('SERVER_PORT'))
        self.sock_host = os.getenv('HOST')
        self.server = None
        self.port = int(os.getenv('GRPC_PORT'))

    def create_grpc_server(self):
        print('Initialized gRPC server.')
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=int(os.getenv('MAX_WORKERS'))))
        configuration_pb2_grpc.add_ServerGRPCServicer_to_server(ServerGRPC(), self.server)
        self.server.add_insecure_port('[::]:' + os.getenv('GRPC_PORT'))

    @staticmethod
    def connect_to_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock

    def _start_server(self):
        self.server.start()

    def send_message_socket(self, message):
        message = message.encode('utf-8')
        self.sock.sendto(message, (self.sock_host, self.sock_port))

    def receive_change_message(self):
        while True:
            data, addr = self.sock.recvfrom(int(os.getenv('BUFFER_SIZE')))
            print('uai mano')
            self.key_changed(data.decode('utf-8'))

    @staticmethod
    def key_changed(info):
        key = info.split()[0]
        command = info.split()[1]
        yield configuration_pb2.listenKeyReply(message='(key=' + key + ', command=' + command + ')')

    def start_server(self):
        server = threading.Thread(name='server_grpc', target=self._start_server)
        server.start()

        sock = threading.Thread(name='receive_change_message', target=self.receive_change_message)
        sock.start()

    def listen_key(self, request, context):
        metadata = dict(context.invocation_metadata())
        print('gRPC--->\t' + str(metadata))

        commands = request
        for command in commands:
            if command.command.split()[0] == 'LISTEN':
                self.send_message_socket(command.command)
                yield configuration_pb2.listenKeyReply(message='Listening key=' + command.command.split()[1])
            else:
                yield configuration_pb2.listenKeyReply(message='Command not found.')
