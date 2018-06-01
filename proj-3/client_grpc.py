from __future__ import print_function

import os
import threading
import time

import configuration_pb2
import configuration_pb2_grpc
import dotenv
import grpc

dotenv.load()


class ClientGRPC:
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:' + os.getenv('GRPC_PORT'))
        self.stub = configuration_pb2_grpc.ServerGRPCStub(self.channel)
        self.need_verify = False
        self.create_verify = True
        self.pid = os.getpid()

    def generate_command(self):
        self.need_verify = True
        return configuration_pb2.listenKeyRequest(command=input(''), pid=self.pid)

    def verify_queue_interval(self):
        responses = self.stub.verify_queue(configuration_pb2.listenKeyRequest(command='', pid=self.pid))

        while True:
            try:
                if responses is not None:
                    for response in responses:
                        print(response.message)

            except grpc._channel._Rendezvous as err:
                print(err)
                time.sleep(10)
                responses = self.stub.verify_queue(configuration_pb2.listenKeyRequest(command='', pid=self.pid))

    def send_message(self):
        print('Client initialized.')
        while True:
            response = self.stub.listen_key(self.generate_command())
            if self.need_verify and self.create_verify:
                self.create_verify = False
                verify_queue = threading.Thread(target=self.verify_queue_interval)
                verify_queue.start()
