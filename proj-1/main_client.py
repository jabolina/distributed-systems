import os
import client_command as client
import dotenv

dotenv.load()


if __name__ == '__main__':
    clnt = client.Client(os.getenv("HOST"), int(os.getenv('SERVER_PORT')))
    command = clnt.run()
