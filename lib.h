//
// Created by zbh on 2019/12/3.
//

#ifndef TPL3_LIB_H
#define TPL3_LIB_H

#include <stdint.h>

typedef struct {
    int capacity;
    int size;
    int_fast64_t *array;
} Int64List;

unsigned char *read_file(char *file_name, int *length_ptr);

int_fast64_t bytes_to_int(const unsigned char *bytes);

void int_to_bytes(unsigned char *b, int_fast64_t i);

//int_fast64_t bytes_to_uint7(const unsigned char *bytes);
//
//void uint7_to_bytes(unsigned char *b, int_fast64_t i);

double bytes_to_double(const unsigned char *bytes);

void double_to_bytes(unsigned char *b, double d);

Int64List *create_list();

void append_list(Int64List *list, int_fast64_t value);

void free_list(Int64List *list);

double double_mod(double d1, double d2);

#endif //TPL3_LIB_H
