import client_grpc

if __name__ == '__main__':
    client = client_grpc.ClientGRPC()
    client.send_message()
