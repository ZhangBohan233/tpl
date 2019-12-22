//
// Created by zbh on 2019/12/3.
//

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "lib.h"


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
int64_t bytes_to_int(const unsigned char *b) {
    return ((int64_t) *b << 56U) |
           ((int64_t) *(b + 1) << 48U) |
           ((int64_t) *(b + 2) << 40U) |
           ((int64_t) *(b + 3) << 32U) |
           ((int64_t) *(b + 4) << 24U) |
           ((int64_t) *(b + 5) << 16U) |
           ((int64_t) *(b + 6) << 8U) |
           (int64_t) *(b + 7);
}

/*
 * The actual push length should be str_len + 8
 */
unsigned char *bytes_to_str(const unsigned char *bytes, int *str_len) {
    *str_len = bytes_to_int(bytes);
    unsigned char *ptr = malloc(*str_len);
    memcpy(ptr, bytes + 8, *str_len);
    return ptr;
}

void int_to_bytes(unsigned char *b, int64_t i) {
    *b = (i >> 56U);
    *(b + 1) = (i >> 48U);
    *(b + 2) = (i >> 40U);
    *(b + 3) = (i >> 32U);
    *(b + 4) = (i >> 24U);
    *(b + 5) = (i >> 16U);
    *(b + 6) = (i >> 8U);
    *(b + 7) = i;
}
