//
// Created by zbh on 2019/12/9.
//

#ifndef TPL3_VM_H
#define TPL3_VM_H

#include <stdint.h>

extern const int INT_LEN, PTR_LEN, FLOAT_LEN, CHAR_LEN, BOOLEAN_LEN, VOID_LEN;

void vm_load(const unsigned char *codes, int read);

void print_memory();

#endif //TPL3_VM_H
