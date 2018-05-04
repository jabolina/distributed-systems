from __future__ import print_function
import dotenv
import os
import grpc
import time
import configuration_pb2
import configuration_pb2_grpc
import threading

dotenv.load()


class ClientGRPC:
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:' + os.getenv('GRPC_PORT'))
        self.stub = configuration_pb2_grpc.ServerGRPCStub(self.channel)
        self.need_verify = False
        self.create_verify = True

    def generate_command(self):
        self.need_verify = True
        return configuration_pb2.listenKeyRequest(command=input(''), pid=os.getpid())

    def verify_queue_interval(self, interval=1):
        while True:
            responses = self.stub.verify_queue(configuration_pb2.verifyQueueRequest(pid=os.getpid()))
            try:
                if responses is not None:
                    for response in responses:
                        print(response.message)
            except grpc._channel._Rendezvous as err:
                print(err)
                exit(0)

            time.sleep(interval)

    def send_message(self):
        print('Client initialized.')
        while True:
            responses = self.stub.listen_key(self.generate_command())
            try:
                if responses is not None:
                    for response in responses:
                        print(response.message)
                if self.need_verify and self.create_verify:
                    self.create_verify = False
                    verify_queue = threading.Thread(target=self.verify_queue_interval,
                                                    args=(float(os.getenv('GRPC_LISTEN_INTERVAL')),))
                    verify_queue.start()
            except grpc._channel._Rendezvous as err:
                print(err)
