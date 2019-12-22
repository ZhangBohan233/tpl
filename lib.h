//
// Created by zbh on 2019/12/3.
//

#ifndef TPL3_LIB_H
#define TPL3_LIB_H

#include <stdint.h>

unsigned char *read_file(char *file_name, int *length_ptr);

int64_t bytes_to_int(const unsigned char *bytes);

unsigned char *bytes_to_str(const unsigned char *bytes, int *str_len);

void int_to_bytes(unsigned char *b, int64_t i);

#endif //TPL3_LIB_H
