import socket
import threading
import dotenv
import os

dotenv.load()


class Client:
    def __init__(self, host, connect_to_port=8000):
        self.host = host
        self.port = connect_to_port
        self.socket = self.create_socket()

    @staticmethod
    def create_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        return sock

    def send_command(self):
        print('Client initialized.')
        while True:
            command = input('')
            command = command.encode('utf-8')
            self.socket.sendto(command, (self.host, self.port))

    def receive_result(self):
        while True:
            data, addr = self.socket.recvfrom(int(os.getenv('BUFFER_SIZE')))
            print(data.decode('utf-8'))

    def run(self):
        try:
            command_thread = threading.Thread(name='send_commands', target=self.send_command)
            command_thread.start()

            listen_thread = threading.Thread(name='receive_results', target=self.receive_result)
            listen_thread.start()

            return command_thread, listen_thread
        except KeyboardInterrupt:
            exit(0)
