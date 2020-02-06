//
// Created by zbh on 2019/12/23.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "heap.h"

const int HEAP_GAP = 8;

#define swap(heap, i, j) {\
int_fast64_t temp = heap[i];\
heap[i] = heap[j];\
heap[j] = temp;\
}

void heapify(int_fast64_t *heap, int heap_size, int index) {
    int left = (index + 1) * 2 - 1;
    int right = (index + 1) * 2;

    int_fast64_t extreme = heap[index];
    int is_left = 1;
    if (left < heap_size) {
        if (extreme > heap[left]) {  // change if max/min heap
            extreme = heap[left];
        }
    }
    if (right < heap_size) {
        if (extreme > heap[right]) {    // change if max/min heap
            extreme = heap[right];
            is_left = 0;
        }
    }

    if (heap[index] > extreme) {    // change if max/min heap
        if (is_left) {
            swap(heap, index, left)
            heapify(heap, heap_size, left);
        } else {
            swap(heap, index, right)
            heapify(heap, heap_size, right);
        }
    }
}

void rise_node(int_fast64_t *heap, int index) {
    int parent_index = (index + 1) / 2 - 1;
    if (parent_index >= 0) {
        if (heap[parent_index] > heap[index]) {  // change if max/min heap
            swap(heap, index, parent_index)
            rise_node(heap, parent_index);
        }
    }
}

int insert_heap(int_fast64_t *heap, int *heap_size, int_fast64_t value) {
    heap[*heap_size] = value;
    rise_node(heap, (*heap_size)++);
    if ((*heap_size > 1 && heap[0] == heap[1]) ||
        (*heap_size > 2 && heap[0] == heap[2])) {
        return 1;
    }
    return 0;
}

int_fast64_t *build_heap(int lower, int upper, int *capacity_ptr) {
    int capacity = (upper - lower) / HEAP_GAP;
    *capacity_ptr = capacity;

    int_fast64_t *heap = malloc(sizeof(int_fast64_t) * capacity);

    for (int i = 0; i < capacity; i++) {
        heap[i] = lower + i * HEAP_GAP;
    }

    int mid = capacity / 2 - 1;
    for (int i = mid; i >= 0; i--) {
        heapify(heap, capacity, i);
    }

//    for(int i = 0; i < capacity; i++) {printf("%lld ", heap[i]);}

    return heap;
}

int_fast64_t peek_heap(int_fast64_t *heap) {
    return heap[0];
}

int_fast64_t extract_heap(int_fast64_t *heap, int *heap_size) {
    (*heap_size) -= 1;
    swap(heap, 0, *heap_size)
    int_fast64_t minimum = heap[*heap_size];
    if (*heap_size > 0) {
        heapify(heap, *heap_size, 0);
    }
    return minimum;
}

void print_sorted(int_fast64_t *heap, int heap_size) {
//    printf("\nOrig heap: [");

    int_fast64_t *cpy_heap = malloc(sizeof(int_fast64_t) * heap_size);
    int size = heap_size;

    memcpy(cpy_heap, heap, sizeof(int_fast64_t) * size);

//    for (int i = 0; i < size; i++) {
//        printf("%lld ", cpy_heap[i]);
//    }
//    printf("]\n");

    printf("\nSorted heap: [");

    while (size > 0) {
        int_fast64_t peek = extract_heap(cpy_heap, &size);
        printf("%lld ", peek);
    }
    printf("]\n");

    free(cpy_heap);
}
