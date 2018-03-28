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
        self.show_cli = True

    @staticmethod
    def create_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        return sock

    def send_command(self):
        while True:
            if self.show_cli:
                command = input('\n$ ')
                command = command.encode('utf-8')
                self.show_cli = False
                self.socket.sendto(command, (self.host, self.port))
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
