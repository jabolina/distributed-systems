from concurrent import futures
import socket
import dotenv
import os
import threading

import grpc
import server
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
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=int(os.getenv('MAX_WORKERS'))))
        configuration_pb2_grpc.add_ServerGRPCServicer_to_server(ServerGRPC(), self.server)
        self.server.add_insecure_port('[::]:' + os.getenv('GRPC_PORT'))

    @staticmethod
    def connect_to_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock

    def start_server(self):
        print('Started gRPC server.')
        self.server.start()

    def send_message_socket(self, message):
        message = message.encode('utf-8')
        self.sock.sendto(message, (self.sock_host, self.sock_port))

    def receive_message_socket(self):
        while True:
            data, addr = self.sock.recvfrom(int(os.getenv('BUFFER_SIZE')))
            return data.decode('utf-8')

    @staticmethod
    def changed_key(message):
        print(message)
        key = message.split()[0]
        command = message.split()[1]
        yield configuration_pb2.listenKeyReply(message='(key=' + key + 'command=' + command + ')')

    def run(self):
        server = threading.Thread(name='server_grpc', target=self.start_server)
        server.start()

    def listen_key(self, request, context):
        metadata = dict(context.invocation_metadata())
        print('gRPC--->\t' + str(metadata))

        commands = request
        for command in commands:
            self.send_message_socket(command.command)
            yield configuration_pb2.listenKeyReply(message=self.receive_message_socket())
