#define _GNU_SOURCE
#include "queue.h"

Queue *create_queue() {
    Queue *queue = (Queue*)malloc(sizeof(Queue));

    if (queue != NULL) {
        queue->head = NULL;
        queue->tail = NULL;
        queue->length = 0;
    }

    return queue;
}

int enqueue(Queue *queue, Packet packet) {
    if (queue != NULL) {
        Node *node = (Node*)malloc(sizeof(Node));

        if (node != NULL) {
            node->packet = packet;
            node->next = NULL;

            if (queue->tail == NULL) {
                queue->head = node;
            } else {
                queue->tail->next = node;
            }

            queue->tail = node;
            queue->length++;

            return 1;
        }
    }

    return 0;
}

int dequeue(Queue *queue) {
    if (queue != NULL) {
        if (queue->head != NULL) {
            Node *node = queue->head;

            queue->head = queue->head->next;

            if (queue->head == NULL) {
                queue->tail = NULL;
            }

            free(node);
            queue->length--;

            return 1;
        }
    }

    return 0;
}

int peek(Queue *queue, Packet *packet) {
    if (queue != NULL) {
        if (queue->head != NULL) {
            *packet = queue->head->packet;

            return 1;
        }
    }

    return 0;
}

void free_queue(Queue* queue) {
    if (queue != NULL) {
        Node *node = NULL;

        while (queue->head != NULL) {
            node = queue->head;
            queue->head = queue->head->next;

            free(node);
        }

        free(queue);
    }
}

int is_empty(Queue *queue) {
    if (queue != NULL) {
        if (queue->head != NULL) {
            return 1;
        }
    }

    return 0;
}
void print_queue(Queue *queue) {
    int i = 0;

    if (queue != NULL) {
        Node *node = queue->head;

        while (node != NULL) {
            printf("%d\tContent: [%s] <--> [%s]\n\n", i++, node->packet.command, node->packet.body);

            node = node->next;
        }
    }
}
