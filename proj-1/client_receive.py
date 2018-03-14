import socket
import threading
import dotenv
import os

dotenv.load()


class Client:
    def __init__(self, host, open_port=8002, listen_to_port=8000):
        self.host = host
        self.port = open_port
        self.target = listen_to_port
        self.socket = self.create_socket()

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))

        return sock

    def receive_result(self):
        while True:
            data, addr = self.socket.recvfrom(int(os.getenv('BUFFER_SIZE')))
            print('Receive response: ' + data.decode('utf-8') + ' from ' + str(addr))

    def run(self):
        listen_thread = threading.Thread(name='receive_results', target=self.receive_result)
        listen_thread.start()

        return listen_thread
