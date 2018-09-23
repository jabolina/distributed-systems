#define _GNU_SOURCE
#include "packet.h"

typedef struct node {
    Packet packet;
    struct node *next;
} Node;

typedef struct queue {
    Node *head;
    Node *tail;
    int length;
} Queue;

Queue *create_queue();
int enqueue(Queue *queue, Packet packet);
int dequeue(Queue *queue);
int peek(Queue *queue, Packet *packet);
void free_queue(Queue* queue);
int is_empty(Queue *queue);
void print_queue(Queue *queue);

