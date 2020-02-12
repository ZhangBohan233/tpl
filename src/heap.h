//
// Created by zbh on 2019/12/23.
//

#ifndef TPL_HEAP_H
#define TPL_HEAP_H

#include <stdint.h>

extern const int HEAP_BLOCK_SIZE;

typedef struct LinkedNode {
    int_fast64_t addr;
    struct LinkedNode *next;
} LinkedNode;

int_fast64_t *AVAILABLE;
int AVA_SIZE;

LinkedNode *AVAILABLE2;
LinkedNode *POOL_LINKS;

/**
 * Return 0 iff insertion succeed.
 */
int insert_heap(int_fast64_t *heap, int *heap_size, int_fast64_t value);

int_fast64_t *build_heap(int lower, int upper, int *capacity_ptr);

int_fast64_t peek_heap(int_fast64_t *heap);

int_fast64_t extract_heap(int_fast64_t *heap, int *heap_size);

void print_sorted(int_fast64_t *heap, int heap_size);

LinkedNode *build_ava_link(int_fast64_t lower, int_fast64_t upper);

void print_link(LinkedNode *head);

void free_link(LinkedNode *pool);

#endif //TPL_HEAP_H
