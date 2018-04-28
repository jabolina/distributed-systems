#!/bin/bash

xterm -hold -e python $PWD/main_server.py &
xterm -hold -e python $PWD/main_client.py &
xterm -hold -e python $PWD/main_client_grpc.py &
