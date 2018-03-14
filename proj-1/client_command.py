import socket
import threading
import dotenv
import os

dotenv.load()


class Client:
    def __init__(self, host, open_port=8001, listen_to_port=8000):
        self.host = host
        self.port = open_port
        self.target = listen_to_port
        self.socket = self.create_socket()
        self.show_cli = True

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))

        return sock

    def send_command(self):
        while True:
            if self.show_cli:
                command = input('\n$ ')
                command = command.encode('utf-8')
                self.show_cli = False
                self.socket.sendto(command, (self.host, self.target))
                print('--------------------------------------------------------------->')

    def receive_result(self):
        while True:
            data, addr = self.socket.recvfrom(int(os.getenv('BUFFER_SIZE')))
            print('Receive response: ' + data.decode('utf-8') + ' from ' + str(addr))
            print('<---------------------------------------------------------------')
            self.show_cli = True

    def run(self):
        command_thread = threading.Thread(name='send_commands', target=self.send_command)
        command_thread.start()

        listen_thread = threading.Thread(name='receive_results', target=self.receive_result)
        listen_thread.start()

        return command_thread, listen_thread
