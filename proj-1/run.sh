#!/bin/bash

xterm -hold -e python ~/Git/distributed-systems/proj-1/main_server.py &
xterm -hold -e python ~/Git/distributed-systems/proj-1/main_client.py &
