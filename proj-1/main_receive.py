import os
import client_receive as client
import dotenv

dotenv.load()


if __name__ == '__main__':
    clnt = client.Client(os.getenv("HOST"), int(os.getenv('RESPONSE_PORT')), int(os.getenv('SERVER_PORT')))
    listen_thread = clnt.run()
