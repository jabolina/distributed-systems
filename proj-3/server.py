import os
import queue
import socket
import threading
import time
import ast

import dotenv
import server_grpc
import snapshooter

dotenv.load()

# python -m grpc_tools.protoc -I./ --python_out=. --grpc_python_out=. ./configuration.proto


'''
    O server, que ficara disponivel numa porta que pode tanto ser passada por
    parametro ou utilizara a padrao 8000.
    
    O server realiza transferência de dados UDP da seguinte maneira:
        Existem 2 threads, uma thread irá receber os comandos via socket e irá coloca-los numa
        fila.
        
        A outra thread irá retirar da fila, e inserir o mesmo comando em outras duas filas,
        sendo uma fila para execução e outra fila para a requisição ser loggada em disco.
        
        Os comandos são INSERT, READ, DELETE, UPDATE, que são realizados em cima de um hash map,
        após cada execução, o hash map é salvo em disco, para que caso acorra algum erro no server,
        durante a reinicialização, o map é restaurado para a forma de antes da ocorrência do erro.
        
        O tamanho do pacote é definido por uma variavel de ambiente, e o tamanho da chave foi definido
        para ter uma tamanho máximo de 20 bytes. 
'''


class Server:
    def __init__(self, host, open_port=8000):
        self.host = host
        self.port = open_port
        self.socket = self.create_socket()
        self.queue = queue.Queue(maxsize=-1)
        self.log = queue.Queue(maxsize=-1)
        self.process = queue.Queue(maxsize=-1)
        self.available_keys = []
        self.listen_keys = {}
        self.hash_crud = {}
        self.gRPC_server = server_grpc.ServerGRPC()

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))

        return sock

    def receive_and_enqueue(self):
        try:
            while True:
                data, addr = self.socket.recvfrom(int(os.getenv('BUFFER_SIZE')))
                print('Received message: ' + data.decode('utf-8') + '\tfrom: ' + str(addr))
                self.queue.put((data, addr))
        except KeyboardInterrupt:
            exit(0)

    def unqueue_commands(self):
        try:
            while True:
                if not self.queue.empty():
                    data, addr = self.queue.get()
                    self.process.put((data, addr))
                    self.log.put((data, addr))

                    self.process_commands()
                    self.log_command()
        except KeyboardInterrupt:
            exit(0)

    def grpc_server(self):
        self.gRPC_server.run()

    def process_commands(self):
        if not self.process.empty():
            data, addr = self.process.get()
            data = data.decode('utf-8')
            verify_keys = {'verify': False}
            send_bytes = ''

            if data.split()[0] == 'INSERT':
                if inside_bytes_length(len(self.hash_crud)):
                    try:
                        key = int(data.split()[1])
                        insert_data = data.split()[2:]
                        verify_keys['verify'] = True
                        verify_keys['key'] = key
                        verify_keys['command'] = data.split()[0]
                    except Exception:
                        key = len(self.hash_crud)
                        insert_data = data.split()[1:]

                    if key in self.available_keys:
                        self.available_keys.remove(key)
                    if len(self.available_keys) > 0:
                        key = self.available_keys.pop()

                    insert_data = ' '.join(insert_data)
                    self.hash_crud[key] = insert_data
                    send_bytes = 'Inserted (key=' + str(key) + ', value=' + insert_data + ')'

            elif data.split()[0] == 'UPDATE':
                key = data.split()[1]
                insert_data = data.split()[2:]
                insert_data = ' '.join(insert_data)
                if int(key) in self.hash_crud:
                    verify_keys['verify'] = True
                    verify_keys['key'] = key
                    verify_keys['command'] = data.split()[0]
                    self.hash_crud[int(key)] = insert_data
                    send_bytes = 'Updated (key=' + key + ', value=' + self.hash_crud[int(key)] + ')'
                else:
                    send_bytes = 'Key not found for update.'

            elif data.split()[0] == 'DELETE':
                key = data.split()[1]
                if int(key) in self.hash_crud:
                    verify_keys['verify'] = True
                    verify_keys['key'] = key
                    verify_keys['command'] = data.split()[0]
                    del self.hash_crud[int(key)]
                    self.available_keys.append(int(key))
                    send_bytes = 'Deleted key=' + key
                else:
                    send_bytes = 'Key not found for delete.'

            elif data.split()[0] == 'READ':
                key = data.split()[1]
                if int(key) in self.hash_crud:
                    verify_keys['verify'] = True
                    verify_keys['key'] = key
                    verify_keys['command'] = data.split()[0]
                    send = self.hash_crud[int(key)]
                    send_bytes = '(key=' + key + ', value=' + send + ')'
                else:
                    send_bytes = 'Key not found for read.'

            elif data.split()[0] == 'LISTEN':
                key = data.split()[1]
                if int(key) in self.hash_crud:
                    if key not in self.listen_keys.keys():
                        self.listen_keys[key] = []

                    self.listen_keys[key].append(addr)
                    verify_keys['verify'] = True
                    verify_keys['key'] = key
                    verify_keys['command'] = data.split()[0]
                else:
                    send_bytes = 'Key not found for read.'

            else:
                send_bytes = 'Command not found.'

            self.socket_send_message(send_bytes, (self.host, addr[1]))

            if verify_keys['verify']:
                self.command_in_key(verify_keys, addr)

    def socket_send_message(self, message, addr):
        if isinstance(addr, str):
            print(str(addr))
#            addr = ast.literal_eval(str(addr))

        print('Sending message: ' + message + '\tto: ' + str(addr))
        message = '\t\t' + message
        message += '\n\n'
        message = message.encode('utf-8')
        self.socket.sendto(message, addr)

    def command_in_key(self, info, who_sent_addr):
        for key in self.listen_keys:
            if int(info['key']) == int(key):
                for addr in self.listen_keys[key]:
                    if addr != who_sent_addr:
                        self.socket_send_message('(key=' + str(key) + '\tcommand=' + str(info['command']) + ')', addr)

    def log_command(self):
        if not self.log.empty():
            log = open('commands_log.log', 'a')
            data, addr = self.log.get()
            log.write(data.decode('utf-8') + '\tfrom\t' + str(addr) + '\n')
            log.close()

    def backup_hash(self):
        while True:
            snapshooter.move_snaps()
            snapshooter.create_snap('./listen_', time.time(), self.listen_keys, '.snap')
            snapshooter.create_snap('./hash_', time.time(), self.hash_crud, '.snap')

            time.sleep(int(os.getenv('SNAPSHOT_SEC')))

    def reload_hash(self):
        try:
            names = os.popen('ls -c | grep -m 2 .snap').readlines()

            if len(names) > 0:
                for name in names:
                    if 'listen_' in name:
                        self.listen_keys = snapshooter.reload_snap(name.replace('\n', ''))
                    elif 'hash_' in name:
                        self.hash_crud = snapshooter.reload_snap(name.replace('\n', ''))

            if self.listen_keys is None or self.hash_crud is None:
                names = os.popen('ls -c ./old_rep/ | grep -m 2 .snap').readlines()
                if len(names) > 0:
                    for name in names:
                        if 'listen_' in name:
                            self.listen_keys = snapshooter.reload_snap(name.replace('\n', ''))
                        elif 'hash_' in name:
                            self.hash_crud = snapshooter.reload_snap(name.replace('\n', ''))

        except Exception as ex:
            print(ex)

    def run(self):
        try:
            self.reload_hash()
            self.gRPC_server.create_grpc_server()

            unqueue_thread = threading.Thread(name='unqueue_commands', target=self.unqueue_commands)
            unqueue_thread.start()

            receive_thread = threading.Thread(name='receive_and_enqueue', target=self.receive_and_enqueue)
            receive_thread.start()

            grpc_server = threading.Thread(name='grpc_server', target=self.grpc_server)
            grpc_server.start()

            snaps = threading.Thread(name='snapshooter', target=self.backup_hash)
            snaps.start()

            return receive_thread, unqueue_thread, grpc_server
        except KeyboardInterrupt:
            exit(0)


def inside_bytes_length(number):
    bytes_length = 0
    while number > 0 and bytes_length <= 22:
        number = int(number / 256)
        bytes_length += 1

    return bytes_length <= 20
