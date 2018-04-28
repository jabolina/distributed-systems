import os
import dotenv
import server

dotenv.load()


if __name__ == '__main__':
    srvr = server.Server(os.getenv('HOST'), int(os.getenv('SERVER_PORT')))
    receive, unqueue, grpc = srvr.run()

