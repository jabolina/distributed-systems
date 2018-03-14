import os
import dotenv
import server

dotenv.load()


if __name__ == '__main__':
    srvr = server.Server(os.getenv("HOST"), int(os.getenv('SERVER_PORT')), int(os.getenv('RESPONSE_PORT')))
    receive, unqueue = srvr.run()

