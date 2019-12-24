//
// Created by zbh on 2019/12/23.
//

#ifndef TPL_HEAP_H
#define TPL_HEAP_H

#include <stdint.h>

extern const int HEAP_GAP;

int64_t *AVAILABLE;
int AVA_SIZE;

void insert_heap(int64_t *heap, int *heap_size, int64_t value);

int64_t *build_heap(int lower, int upper, int *capacity_ptr);

int64_t peek_heap(int64_t *heap);

int64_t extract_heap(int64_t *heap, int *heap_size);

void print_sorted(int64_t *heap, int heap_size);

#endif //TPL_HEAP_H
