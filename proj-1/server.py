import socket
import threading
import dotenv
import os

dotenv.load()


class Server:
    def __init__(self, host, open_port=8000, response_port=8002):
        self.host = host
        self.port = open_port
        self.response_port = response_port
        self.socket = self.create_socket()
        self.queue = []
        self.available_keys = []
        self.hash_crud = {}

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))

        return sock

    def receive_and_enqueue(self):
        while True:
            data, addr = self.socket.recvfrom(int(os.getenv('BUFFER_SIZE')))
            print('Received command from' + str(addr) + '\tInfo: ' + str(data))
            self.queue.append((data, addr))

    def unqueue_commands(self):
        while True:
            if len(self.queue) > 0:
                data, addr = self.queue.pop()
                data = data.decode('utf-8')

                if data.split()[0] == 'INSERT':
                    if inside_bytes_length(len(self.hash_crud)):
                        if len(self.available_keys) > 0:
                            key = self.available_keys.pop()
                        else:
                            key = len(self.hash_crud)

                        self.hash_crud[key] = data.replace(data.split()[0], '')
                        send_bytes = 'Inserted (key=' + str(key) + ', value=' + data.replace(data.split()[0], '') + ')'
                        send_bytes = send_bytes.encode('utf-8')
                        self.socket.sendto(send_bytes, (self.host, self.response_port))

                elif data.split()[0] == 'UPDATE':
                    key = data.split()[1]
                    if int(key) in self.hash_crud:
                        self.hash_crud[int(key)] = data.replace(data.split()[0] + ' ' + data.split()[1], '')
                        send_bytes = 'Updated (key=' + key + ', value=' + self.hash_crud[int(key)] + ')'
                    else:
                        send_bytes = 'Key not found for update.'

                    send_bytes = send_bytes.encode('utf-8')
                    self.socket.sendto(send_bytes, (self.host, self.response_port))

                elif data.split()[0] == 'DELETE':
                    key = data.split()[1]
                    if int(key) in self.hash_crud:
                        del self.hash_crud[int(key)]
                        self.available_keys.append(int(key))
                        send_bytes = 'Deleted key=' + key
                    else:
                        send_bytes = 'Key not found for delete.'

                    send_bytes = send_bytes.encode('utf-8')
                    self.socket.sendto(send_bytes, (self.host, self.response_port))

                elif data.split()[0] == 'READ':
                    key = data.split()[1]
                    if int(key) in self.hash_crud:
                        send = self.hash_crud[int(key)]
                        send_bytes = '(key=' + key + ', value=' + send + ')'
                    else:
                        send_bytes = 'Key not found for read.'

                    send_bytes = send_bytes.encode('utf-8')
                    self.socket.sendto(send_bytes, (self.host, self.response_port))

                else:
                    send_bytes = 'Command not found.'
                    send_bytes = send_bytes.encode('utf-8')
                    self.socket.sendto(send_bytes, (self.host, self.response_port))

    def run(self):
        unqueue_thread = threading.Thread(name='unqueue_commands', target=self.unqueue_commands)
        unqueue_thread.start()

        receive_thread = threading.Thread(name='receive_and_enqueue', target=self.receive_and_enqueue)
        receive_thread.start()

        return receive_thread, unqueue_thread


def inside_bytes_length(number):
    bytes_length = 0
    while number > 0 and bytes_length < 21:
        number = int(number / 256)
        bytes_length += 1

    return bytes_length <= 20
