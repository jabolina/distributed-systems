import socket
import threading
import dotenv

dotenv.load()


class Client:
    def __init__(self, host, open_port=8001, listen_to_port=8000):
        self.host = host
        self.port = open_port
        self.target = listen_to_port
        self.socket = self.create_socket()

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))

        return sock

    def send_command(self):
        while True:
            command = input('> ')
            command = command.encode('utf-8')
            self.socket.sendto(command, (self.host, self.target))

    def run(self):
        command_thread = threading.Thread(name='send_commands', target=self.send_command)
        command_thread.start()

        return command_thread
