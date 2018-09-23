#define _GNU_SOURCE
#include "packet.h"

Packet create_packet(char *command, char *body) {
    Packet packet = {
        .command = command,
        .body = body
    };

    return packet;
}
