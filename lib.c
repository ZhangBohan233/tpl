//
// Created by zbh on 2019/12/3.
//

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "lib.h"


void print_array(const unsigned char *b, int length) {
    for (int i = 0; i < length; i++) {
        printf("%d ", b[i]);
    }
    printf("\n");
}


unsigned char *read_file(char *file_name, int *length_ptr) {
    FILE *fp = malloc(sizeof(FILE));
    int res = fopen_s(&fp, file_name, "rb");
    if (res != 0) {
        fclose(fp);
        perror("Open error");
        return NULL;
    }
    fseek(fp, 0, SEEK_END);
    int len = ftell(fp);
    *length_ptr = len;
    unsigned char *array = malloc(sizeof(unsigned char) * len);
    fseek(fp, 0, SEEK_SET);
    unsigned int read = fread(array, sizeof(unsigned char), len, fp);
    if (read != len) {
        fclose(fp);
        printf("Read error. Expected length %d, actual bytes %d\n", len, read);
        return NULL;
    }
    fclose(fp);
    return array;
}

/*
 * This function is only valid when INT_LEN == 8
 */
int_fast64_t bytes_to_int(const unsigned char *b) {
    union {
        int_fast64_t value;
        unsigned char arr[8];
    } i64;
    memcpy(i64.arr, b, 8);
    return i64.value;
}

void int_to_bytes(unsigned char *b, int_fast64_t i) {
    union {
        int_fast64_t value;
        unsigned char arr[8];
    } i64;
    i64.value = i;
    memcpy(b, i64.arr, 8);
}

double bytes_to_double(const unsigned char *bytes) {
    union {
        double d;
        unsigned char b[8];
    } dou;
    memcpy(dou.b, bytes, 8);
    return dou.d;
}

void double_to_bytes(unsigned char *bytes, double d) {
    union {
        double d;
        unsigned char b[8];
    } dou;
    dou.d = d;
    memcpy(bytes, dou.b, 8);
}

Int64List *create_list() {
    Int64List *list = malloc(sizeof(Int64List));
    list->capacity = 8;
    list->size = 0;
    list->array = malloc(sizeof(int_fast64_t) * list->capacity);
    return list;
}

void list_expand(Int64List *list) {
    list->capacity *= 2;
    int_fast64_t *new_array = malloc(sizeof(int_fast64_t) * list->capacity);
    memcpy(new_array, list->array, sizeof(int_fast64_t) * list->size);
    free(list->array);
    list->array = new_array;
}

void append_list(Int64List *list, int_fast64_t value) {
    if (list->size == list->capacity) {
        list_expand(list);
    }
    list->array[list->size++] = value;
}

void free_list(Int64List *list) {
    free(list->array);
    free(list);
}

double double_mod(double d1, double d2) {
    while (d1 >= d2) {
        d1 -= d2;
    }
    return d1;
}
