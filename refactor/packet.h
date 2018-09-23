#include <stdio.h>
#include <stdlib.h>

typedef struct packet {
    char *command;
    char *body;
} Packet;


Packet create_packet(char *command, char *body);

