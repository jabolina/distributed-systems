from __future__ import print_function
import dotenv
import os
import grpc
import time
import configuration_pb2
import configuration_pb2_grpc

dotenv.load()


class ClientGRPC:
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:' + os.getenv('GRPC_PORT'))
        self.stub = configuration_pb2_grpc.ServerGRPCStub(self.channel)

    @staticmethod
    def generate_command(command):
        time.sleep(0.1)
        yield configuration_pb2.listenKeyRequest(command=command)

    def send_message(self):
        while True:
            command = input('\n> ')

            responses = self.stub.listen_key(self.generate_command(command))
            try:
                for response in responses:
                    print(response.message)
            except grpc._channel._Rendezvous as err:
                print(err)

