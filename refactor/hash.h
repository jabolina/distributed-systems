#define _GNU_SOURCE

#include <inttypes.h>
#include <errno.h>
#include <string.h>

#include "packet.h"

typedef struct hash {
    int size;
    int max_size;
    Packet **packets;
} Hash;

Hash *create_hash(int max_size);
void free_hash(Hash* hash);
int put(Hash *hash, Packet packet);
int get(Hash *hash, int key, Packet *packet);

