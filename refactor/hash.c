#define _GNU_SOURCE
#include "hash.h"

Hash *create_hash(int max_size) {
    Hash *hash = (Hash*)malloc(sizeof(Hash));
    int i;

    if (hash != NULL) {
        hash->max_size = max_size;
        hash->packets = (Packet**)malloc(max_size * sizeof(Packet*));

        if (hash->packets != NULL) {
            hash->size = 0;

            for (i=0; i<max_size; i++) {
                hash->packets[i] = NULL;
            }
        } else {
            free(hash);
            exit(0);
            return NULL;
        }
    }

    return hash;
}

/*
    TODO verify empty string
*/
int get_key(char *body) {
    char *endptr;

    if (*body != '\0' && *body != '\n') {
        return strtoimax(body, &endptr, 10);
    }

    return -1;
}

void free_hash(Hash *hash) {
    int i;

    if (hash != NULL) {
        for (i=0; i<hash->max_size; i++) {
            free(hash->packets[i]);
        }

        free(hash->packets);
        free(hash);
    }
}

int put(Hash *hash, Packet packet) {
    int key;
    Packet *new_packet;

    if (hash != NULL && hash->size < hash->max_size) {
        key = get_key(packet.body);

        if (key >= 0 && key < hash->max_size) {
            new_packet = (Packet*)malloc(sizeof(Packet));

            if (new_packet != NULL) {
                *new_packet = packet;

                hash->packets[key] = new_packet;
                hash->size++;

                return 1;
            }
        }
    }

    return 0;
}

int get(Hash *hash, int key, Packet *packet) {
    if (hash != NULL && key >= 0 && key <= hash->max_size) {
        if (hash->packets[key] != NULL) {
            *packet = *(hash->packets[key]);

            return 1;
        }
    }

    return 0;
}
