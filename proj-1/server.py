import socket
import threading
import dotenv
import re
import os
import queue

dotenv.load()


class Server:
    def __init__(self, host, open_port=8000):
        self.host = host
        self.port = open_port
        self.socket = self.create_socket()
        self.queue = queue.Queue(maxsize=-1)
        self.log = queue.Queue(maxsize=-1)
        self.process = queue.Queue(maxsize=-1)
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
            self.queue.put((data, addr))

    def unqueue_commands(self):
        while True:
            if not self.queue.empty():
                data, addr = self.queue.get()
                self.process.put((data, addr))
                self.log.put((data, addr))

                self.process_commands()
                self.log_command()

    def process_commands(self):
        if not self.process.empty():
            data, addr = self.process.get()
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
                    self.socket.sendto(send_bytes, (self.host, addr[1]))

            elif data.split()[0] == 'UPDATE':
                key = data.split()[1]
                if int(key) in self.hash_crud:
                    self.hash_crud[int(key)] = data.replace(data.split()[0] + ' ' + data.split()[1], '')
                    send_bytes = 'Updated (key=' + key + ', value=' + self.hash_crud[int(key)] + ')'
                else:
                    send_bytes = 'Key not found for update.'

                send_bytes = send_bytes.encode('utf-8')
                self.socket.sendto(send_bytes, (self.host, addr[1]))

            elif data.split()[0] == 'DELETE':
                key = data.split()[1]
                if int(key) in self.hash_crud:
                    del self.hash_crud[int(key)]
                    self.available_keys.append(int(key))
                    send_bytes = 'Deleted key=' + key
                else:
                    send_bytes = 'Key not found for delete.'

                send_bytes = send_bytes.encode('utf-8')
                self.socket.sendto(send_bytes, (self.host, addr[1]))

            elif data.split()[0] == 'READ':
                key = data.split()[1]
                if int(key) in self.hash_crud:
                    send = self.hash_crud[int(key)]
                    send_bytes = '(key=' + key + ', value=' + send + ')'
                else:
                    send_bytes = 'Key not found for read.'

                send_bytes = send_bytes.encode('utf-8')
                self.socket.sendto(send_bytes, (self.host, addr[1]))

            else:
                send_bytes = 'Command not found.'
                send_bytes = send_bytes.encode('utf-8')
                self.socket.sendto(send_bytes, (self.host, addr[1]))

            self.backup_hash()

    def log_command(self):
        if not self.log.empty():
            log = open('commands_log.log', 'a')
            data, addr = self.log.get()
            log.write(data.decode('utf-8') + '\tfrom\t' + str(addr) + '\n')
            log.close()

    def backup_hash(self):
        log = open('log_hash.log', 'w')
        for key in self.hash_crud:
            self.hash_crud[key] = re.sub('\n$', '', self.hash_crud[key])
            log.write(str(key) + '&#!#&' + str(self.hash_crud[key]) + '\n')
        log.close()

    def reload_hash(self):
        try:
            with open('log_hash.log', 'r') as file:
                for line in file:
                    self.hash_crud[int(line.split('&#!#&')[0])] = line.split('&#!#&')[1]

            file.close()

        except Exception:
            pass

    def run(self):
        self.reload_hash()

        unqueue_thread = threading.Thread(name='unqueue_commands', target=self.unqueue_commands)
        unqueue_thread.start()

        receive_thread = threading.Thread(name='receive_and_enqueue', target=self.receive_and_enqueue)
        receive_thread.start()

        return receive_thread, unqueue_thread


def inside_bytes_length(number):
    bytes_length = 0
    while number > 0 and bytes_length <= 22:
        number = int(number / 256)
        bytes_length += 1

    return bytes_length <= 20
