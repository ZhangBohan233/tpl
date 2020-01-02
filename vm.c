//
// Created by zbh on 2019/12/9.
//

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "vm.h"
#include "lib.h"
#include "heap.h"

#define true_ptr(ptr) (ptr < LITERAL_START && CSP >= 0 ? ptr + CALL_STACK[CSP] : ptr)

#define rel_ptr(ptr) (ptr < LITERAL_START && CSP >= 0 ? ptr - CALL_STACK[CSP] : ptr)

#define read_2_ints {\
reg1 = bytes_to_int(MEMORY + PC);\
reg2 = bytes_to_int(MEMORY + PC + INT_LEN);\
PC += INT_LEN_2;\
}

#define read_3_ints {\
reg1 = bytes_to_int(MEMORY + PC);\
reg2 = bytes_to_int(MEMORY + PC + INT_LEN);\
reg3 = bytes_to_int(MEMORY + PC + INT_LEN_2);\
PC += INT_LEN_3;\
}

#define read_4_ints {\
reg1 = bytes_to_int(MEMORY + PC);\
reg2 = bytes_to_int(MEMORY + PC + INT_LEN);\
reg3 = bytes_to_int(MEMORY + PC + INT_LEN_2);\
reg4 = bytes_to_int(MEMORY + PC + INT_LEN_3);\
PC += INT_LEN_4;\
}

#define read_3_true_ptr {\
read_3_ints;\
reg1 = true_ptr(reg1);\
reg2 = true_ptr(reg2);\
reg3 = true_ptr(reg3);\
}

const int INT_LEN = 8;
const int PTR_LEN = 8;
const int FLOAT_LEN = 8;
const int CHAR_LEN = 1;
const int BOOLEAN_LEN = 1;
const int VOID_LEN = 0;

const int INT_LEN_2 = 16;
const int INT_LEN_3 = 24;
const int INT_LEN_4 = 32;

const int_fast64_t STACK_START = 1;
int_fast64_t LITERAL_START = 1024;
int_fast64_t FUNCTIONS_START = 1024;
int_fast64_t CODE_START = 1024;
int_fast64_t HEAP_START = 1024;

const int_fast64_t MEMORY_SIZE = 4096;
unsigned char MEMORY[4096];

int_fast64_t SP = 1;
int_fast64_t PC = 1024;

int CALL_STACK[1000];  // recursion limit
int CSP = -1;

int PC_STACK[1000];
int PSP = -1;

int LOOP_STACK[1000];  // 1000 nested loop
int LSP = -1;

// The error code, set by virtual machine. Used to tell the main loop that the process is interrupted
// Interrupt the vm if the code is not 0
//
// 0: No error
// 1: Memory address error
// 2: Native function error
int ERROR_CODE = 0;

void print_memory() {
    int i = 0;
    printf("Stack ");
    for (; i < LITERAL_START; i++) {
        printf("%d ", MEMORY[i]);
        if (i % 8 == 0) printf("| ");
    }

    printf("\nLiteral %lld: ", LITERAL_START);
    for (; i < FUNCTIONS_START; i++) {
        printf("%d ", MEMORY[i]);
    }

    printf("\nFunctions %lld: ", FUNCTIONS_START);
    for (; i < CODE_START; i++) {
        printf("%d ", MEMORY[i]);
    }

    printf("\nCode %lld: ", CODE_START);
    for (; i < HEAP_START; i++) {
        printf("%d ", MEMORY[i]);
    }

    printf("\nHeap %lld: ", HEAP_START);
    for (; i < HEAP_START + 128; i++) {
        printf("%d ", MEMORY[i]);
        if ((i - HEAP_START) % 8 == 7) printf("| ");
    }
    printf("\n");
}

void print_call_stack() {
    printf("Call stack: ");
    for (int i = 0; i <= CSP; i++) {
        printf("%d, ", CALL_STACK[CSP]);
    }
    printf("\n");
}

void vm_load(const unsigned char *codes, int read) {
    int_fast64_t literal_size = bytes_to_int(codes);
    int_fast64_t functions_size = bytes_to_int(codes + INT_LEN);

    FUNCTIONS_START += literal_size;
    CODE_START = FUNCTIONS_START + functions_size;
    PC = CODE_START;

    int copy_len = read - INT_LEN * 2;
    HEAP_START = LITERAL_START + copy_len;

    memcpy(MEMORY + LITERAL_START, codes + INT_LEN * 2, copy_len);

    AVAILABLE = build_heap(HEAP_START, MEMORY_SIZE, &AVA_SIZE);
//    print_memory();
}

void vm_shutdown() {
    free(AVAILABLE);
}

void mem_copy(int_fast64_t from, int_fast64_t to, int_fast64_t len) {
    memcpy(MEMORY + to, MEMORY + from, len);
}

void exit_func() {
    SP = CALL_STACK[CSP--];
    PC = PC_STACK[PSP--];
}

void native_printf(int_fast64_t argc, const int_fast64_t *argv) {
    if (argc <= 0) {
        printf("'printf' takes at least 1 argument");
        ERROR_CODE = 1;
        return;
    }
    int_fast64_t fmt_end = argv[0];
    while (MEMORY[fmt_end] != 0) fmt_end++;
    int fmt_len = (int) (fmt_end - argv[0]);
    char *fmt = malloc(fmt_len + 1);
    memcpy(fmt, MEMORY + argv[0], fmt_len);
    fmt[fmt_len] = '\0';

    int i = 0;
    int f = 0;
    int a_index = 1;

    while (i < fmt_len) {
        char ch = fmt[i];
        if (ch == '%') {
            f = 1;
        } else if (f) {
            if (ch == 'd') {  // int
                f = 0;
                int_fast64_t ptr = argv[a_index++];
                int_fast64_t value = bytes_to_int(MEMORY + ptr);
                printf("%lld", value);
            } else if (ch == 'c') {  // char
                f = 0;
                int_fast64_t ptr = argv[a_index++];
                unsigned char value = MEMORY[ptr];
                printf("%c", value);
            } else if (ch == 'f') {  // float
                f = 0;
                int_fast64_t ptr = argv[a_index++];
                double value = bytes_to_double(MEMORY + ptr);
                printf("%f", value);
            } else if (ch == 'b') {  // boolean
                f = 0;
                int_fast64_t ptr = argv[a_index++];
                unsigned char value = MEMORY[ptr];
                if (value == 0) printf("false");
                else printf("true");
            } else if (ch == 's') {  // string
                f = 0;
                int_fast64_t ptr = argv[a_index++];
                int_fast64_t value_addr = true_ptr(bytes_to_int(MEMORY + ptr));
//                printf("%lld\n", value_addr);

                for (int_fast64_t end = value_addr; MEMORY[end] != 0; end++) printf("%c", MEMORY[end]);
            } else {
                fprintf(stderr, "Unknown flag: '%c'\n", ch);
                f = 0;
            }
        } else {
            printf("%c", ch);
        }
        i++;
    }

    free(fmt);
}

int_fast64_t find_ava(int length) {
    Int64List *pool = create_list();
    int found = 0;
    while (found == 0) {
        if (AVA_SIZE < length) {
            break;
        }
        int i = 0;
        while (i < length) {
            i++;
            int_fast64_t x = extract_heap(AVAILABLE, &AVA_SIZE);
            append_list(pool, x);
            int_fast64_t y = peek_heap(AVAILABLE);
//            printf("x %lld y %lld\n", x, y);
            if (x != y - HEAP_GAP) {
                break;
            }
        }
        if (i == length) {
            found = 1;
        }
    }

    if (found) {
        for (int i = 0; i < pool->size - length; i++) {
            insert_heap(AVAILABLE, &AVA_SIZE, pool->array[i]);
        }
        int_fast64_t result = pool->array[pool->size - length];
        free_list(pool);
        return result;
    } else {
        free_list(pool);
        fprintf(stderr, "Cannot allocate length %d, available memory %d\n", length, AVA_SIZE);
        ERROR_CODE = 2;
        return -1;
    }
}

void native_malloc(int_fast64_t argc, int_fast64_t ret_len, int_fast64_t ret_ptr, int_fast64_t *argv) {
    if (argc != 1 || ret_len != PTR_LEN) {
        printf("Unmatched arg length or return length");
        ERROR_CODE = 2;
        return;
    }

    int_fast64_t asked_len = bytes_to_int(MEMORY + argv[0]);
    int_fast64_t real_len = asked_len + INT_LEN;
    int_fast64_t allocate_len = real_len % 8 == 0 ? real_len / 8 : real_len / 8 + 1;

//    print_sorted(AVAILABLE, AVA_SIZE);

//    printf("alloc %lld\n", allocate_len);
    int_fast64_t location = find_ava(allocate_len);
//    printf("malloc %lld\n", location + INT_LEN);

//    print_sorted(AVAILABLE, AVA_SIZE);

    int_to_bytes(MEMORY + location, allocate_len);

    int_to_bytes(MEMORY + ret_ptr, location + INT_LEN);
}

void native_clock(int_fast64_t arg_count, int_fast64_t ret_len, int_fast64_t ret_ptr) {
    if (arg_count != 0 || ret_len != INT_LEN) {
        printf("Unmatched arg length or return length");
        ERROR_CODE = 2;
        return;
    }
    int_fast64_t t = clock();
    int_to_bytes(MEMORY + ret_ptr, t);
}

void native_free(int_fast64_t argc, const int_fast64_t *argv) {
    if (argc != 1) {
        printf("Unmatched arg length or return length");
        ERROR_CODE = 2;
        return;
    }
    int_fast64_t free_ptr = bytes_to_int(MEMORY + argv[0]);
    int_fast64_t real_ptr = free_ptr - INT_LEN;
    int_fast64_t alloc_len = bytes_to_int(MEMORY + real_ptr);

    if (real_ptr < HEAP_START || real_ptr > MEMORY_SIZE) {
        printf("Cannot free pointer outside heap");
        ERROR_CODE = 2;
        return;
    }

    for (int i = 0; i < alloc_len; i++) {
        insert_heap(AVAILABLE, &AVA_SIZE, real_ptr + i * HEAP_GAP);
//        printf("free %lld \n", real_ptr + i * HEAP_GAP);
    }

//    print_sorted(AVAILABLE, AVA_SIZE);
}

void native_mem_copy(int_fast64_t argc, const int_fast64_t *argv) {
    if (argc != 3) {
        fprintf(stderr, "'mem_copy' takes 3 arguments, %lld given\n", argc);
        ERROR_CODE = 2;
        return;
    }
    int_fast64_t dest_addr = argv[0];
    int_fast64_t src_addr = argv[1];
    int_fast64_t length_ptr = argv[2];
    int_fast64_t dest = true_ptr(bytes_to_int(MEMORY + dest_addr));
    int_fast64_t src = true_ptr(bytes_to_int(MEMORY + src_addr));
    int_fast64_t length = bytes_to_int(MEMORY + length_ptr);
//    printf("%lld %lld %lld\n", dest, src, length);
    mem_copy(src, dest, length);
}

void call_native(int_fast64_t func, int_fast64_t ret_ptr, int_fast64_t ret_len, int_fast64_t arg_count,
                 int_fast64_t *arg_array) {
    switch (func) {
        case 1:  // clock
            native_clock(arg_count, ret_len, ret_ptr);
            break;
        case 2:  // malloc
            native_malloc(arg_count, ret_len, ret_ptr, arg_array);
            break;
        case 3:  // printf
            native_printf(arg_count, arg_array);
            break;
        case 4:  // mem_copy
            native_mem_copy(arg_count, arg_array);
            break;
        case 5:  // free
            native_free(arg_count, arg_array);
            break;
        default:
            printf("Unknown native function %lld", func);
            return;
    }
}

void vm_run() {
    int_fast64_t reg1;
    int_fast64_t reg2;
    int_fast64_t reg3;
    int_fast64_t reg4;
    int_fast64_t reg5;
    int_fast64_t reg6;
    int_fast64_t reg7;
    int_fast64_t reg8;

    int reg9;
    int reg10;

    unsigned char reg11;
    unsigned char reg12;

    double reg13;
    double reg14;

    register unsigned char instruction;

    while (PC < HEAP_START) {
        instruction = MEMORY[PC++];
        switch (instruction) {
            case 2:  // Stop
                exit_func();
                break;
            case 3:  // ASSIGN
            read_3_ints  // tar, src, len
                reg1 = true_ptr(reg1);  // true tar
                reg2 = true_ptr(reg2);  // true src
                mem_copy(reg2, reg1, reg3);
                break;
            case 4:  // CALL
            read_3_ints  // addr of func_ptr, r_len, arg_count
                reg4 = PC;  // pc backup
                PC += reg3 * (INT_LEN + PTR_LEN);
                reg5 = SP;  // sp backup

                reg1 = bytes_to_int(MEMORY + reg1);  // true func ptr

                for (reg9 = 0; reg9 < reg3; reg9++) {
                    reg6 = bytes_to_int(MEMORY + reg4);  // arg_ptr
                    reg4 += PTR_LEN;
                    reg7 = bytes_to_int(MEMORY + reg4);  // arg_len
                    reg4 += INT_LEN;
                    reg6 = true_ptr(reg6);  // true arg ptr
                    mem_copy(reg6, SP, reg7);
                    SP += reg7;
//                    printf("%lld\n", reg6);
                }

                PC_STACK[++PSP] = PC;
                CALL_STACK[++CSP] = reg5;

//                printf("sp: %lld\n", reg5);

                PC = reg1;
                break;
            case 5:  // RETURN
            read_2_ints  // value ptr, rtype len
                reg3 = true_ptr(reg1);  // true value ptr

                reg4 = CALL_STACK[CSP] - reg2;  // where to put the return value
                mem_copy(reg3, reg4, reg2);

                exit_func();
                break;
            case 6:  // GOTO
                reg1 = bytes_to_int(MEMORY + PC);
                PC += INT_LEN;
                PC += reg1;
                break;
            case 7:  // PUSH STACK
                reg1 = bytes_to_int(MEMORY + PC);
                PC += INT_LEN;
                SP += reg1;
                break;
            case 8:  // ASSIGN_I
            read_2_ints
                reg1 = true_ptr(reg1);
                int_to_bytes(MEMORY + reg1, reg2);
//                printf("%lld %lld\n", reg1, reg2);
                break;
            case 9:  // ASSIGN_B
            read_2_ints
                reg1 = true_ptr(reg1);
                MEMORY[reg1] = (unsigned char) reg2;
                break;
            case 10:  // ADD INT
            read_3_true_ptr  // res ptr, left ptr, right ptr
                reg2 = bytes_to_int(MEMORY + reg2);  // left value
                reg3 = bytes_to_int(MEMORY + reg3);  // right value
                reg2 = reg2 + reg3;  // result
                int_to_bytes(MEMORY + reg1, reg2);
                break;
            case 11:  // CAST INT
            read_3_ints  // res ptr, src ptr, src len
                reg1 = true_ptr(reg1);
                reg2 = true_ptr(reg2);
                // TODO: float cast
                if (reg3 <= 8) {
                    mem_copy(reg2, reg1, reg3);
//                    reg4 = bytes_to_int(MEMORY + reg2);
//
                } // TODO: else
                break;
            case 12:  // SUB INT
            read_3_true_ptr  // res ptr, left ptr, right ptr
                reg2 = bytes_to_int(MEMORY + reg2);  // left value
                reg3 = bytes_to_int(MEMORY + reg3);  // right value
                reg2 = reg2 - reg3;  // result
                int_to_bytes(MEMORY + reg1, reg2);
                break;
            case 13:  // MUL INT
            read_3_true_ptr  // res ptr, left ptr, right ptr
                reg2 = bytes_to_int(MEMORY + reg2);  // left value
                reg3 = bytes_to_int(MEMORY + reg3);  // right value
                reg2 = reg2 * reg3;  // result
                int_to_bytes(MEMORY + reg1, reg2);
                break;
            case 14:  // DIV INT
            read_3_true_ptr  // res ptr, left ptr, right ptr
                reg2 = bytes_to_int(MEMORY + reg2);  // left value
                reg3 = bytes_to_int(MEMORY + reg3);  // right value
                reg2 = reg2 / reg3;  // result
                int_to_bytes(MEMORY + reg1, reg2);
                break;
            case 15:  // MOD INT
            read_3_true_ptr  // res ptr, left ptr, right ptr
                reg2 = bytes_to_int(MEMORY + reg2);  // left value
                reg3 = bytes_to_int(MEMORY + reg3);  // right value
                reg2 = reg2 % reg3;  // result
                int_to_bytes(MEMORY + reg1, reg2);
                break;
            case 16:  // EQ
            read_3_true_ptr  // res ptr, left ptr, right ptr
                reg2 = bytes_to_int(MEMORY + reg2);  // left value
                reg3 = bytes_to_int(MEMORY + reg3);  // right value
                reg2 = reg2 - reg3;  // cmp_result

                reg11 = reg2 == 0 ? 1 : 0;
                MEMORY[reg1] = reg11;
                break;
            case 17:  // GT
            read_3_true_ptr  // res ptr, left ptr, right ptr
                reg2 = bytes_to_int(MEMORY + reg2);  // left value
                reg3 = bytes_to_int(MEMORY + reg3);  // right value
                reg2 = reg2 - reg3;  // cmp_result

                reg11 = reg2 > 0 ? 1 : 0;
                MEMORY[reg1] = reg11;
                break;
            case 18:  // LT
            read_3_true_ptr  // res ptr, left ptr, right ptr
                reg2 = bytes_to_int(MEMORY + reg2);  // left value
                reg3 = bytes_to_int(MEMORY + reg3);  // right value
                reg2 = reg2 - reg3;  // cmp_result

                reg11 = reg2 < 0 ? 1 : 0;
                MEMORY[reg1] = reg11;
                break;
            case 19:  // AND
            read_3_true_ptr  // res ptr, left ptr, right ptr
                reg11 = MEMORY[reg2];  // left value
                reg12 = MEMORY[reg3];  // right value
                reg11 = reg11 && reg12;
                MEMORY[reg1] = reg11;
                break;
            case 20:  // OR
            read_3_true_ptr  // res ptr, left ptr, right ptr
                reg11 = MEMORY[reg2];  // left value
                reg12 = MEMORY[reg3];  // right value
                reg11 = reg11 || reg12;
                MEMORY[reg1] = reg11;
                break;
            case 21:  // NOT
            read_2_ints  // res ptr, bool value ptr
                reg11 = MEMORY[reg2];
                reg11 = !reg11;
                MEMORY[reg1] = reg11;
                break;
            case 22:  // NE
            read_3_true_ptr  // res ptr, left ptr, right ptr
                reg2 = bytes_to_int(MEMORY + reg2);  // left value
                reg3 = bytes_to_int(MEMORY + reg3);  // right value
                reg2 = reg2 - reg3;  // cmp_result

                reg11 = reg2 != 0 ? 1 : 0;
                MEMORY[reg1] = reg11;
                break;
            case 30:  // IF ZERO GOTO
            read_2_ints  // skip len, cond ptr
                reg2 = true_ptr(reg2);  // true cond ptr

                reg11 = MEMORY[reg2];
//                printf("%d vvv\n", reg11);
                if (reg11 == 0) {
                    PC += reg1;
                }
                break;
            case 31:  // NATIVE CALL
            read_4_ints  // func ptr, rtype len, r ptr, arg count
                reg1 = bytes_to_int(MEMORY + reg1);  // true func ptr
                reg5 = bytes_to_int(MEMORY + reg1);  // function code
                reg3 = true_ptr(reg3);  // true return ptr
                reg6 = PC;  // PC backup
                PC += reg4 * (INT_LEN + PTR_LEN);

                int_fast64_t *args = malloc(reg4 * 8);
                for (reg9 = 0; reg9 < reg4; reg9++) {
                    reg7 = bytes_to_int(MEMORY + reg6);  // arg_ptr
                    reg6 += PTR_LEN;
//                    reg8 = bytes_to_int(MEMORY + reg6);  // arg_len
                    reg6 += INT_LEN;
                    reg7 = true_ptr(reg7);  // true arg ptr
                    args[reg9] = reg7;
//                    printf("%lld\n", reg7);
//                    args[reg9 * 2 + 1] = reg8;
                }
                call_native(reg5, reg3, reg2, reg4, args);

                free(args);
                break;
            case 32:  // STORE ADDR, store addr to des
            read_2_ints
                reg1 = true_ptr(reg1);
                reg2 = true_ptr(reg2);
                int_to_bytes(MEMORY + reg1, reg2);
                break;
            case 33:  // UNPACK ADDR
            read_3_ints  // result ptr, pointer address, length
                reg1 = true_ptr(reg1);
                reg2 = true_ptr(reg2);   // address of pointer

                reg4 = bytes_to_int(MEMORY + reg2);  // address stored in pointer
//                printf("unpack %lld, value %lld\n", reg2, reg4);
                mem_copy(reg4, reg1, reg3);
                break;
            case 34:  // PTR ASSIGN
            read_3_ints  // address of ptr, src, len
                reg1 = true_ptr(reg1);
                reg2 = true_ptr(reg2);
                reg4 = bytes_to_int(MEMORY + reg1);  // address of value
//                reg4 = true_ptr(reg4);
//                printf("ptr assign: ptr at %lld, src %lld, len %lld\n", reg1, reg2, reg3);
                mem_copy(reg2, reg4, reg3);
                break;
            case 35:  // STORE SP
                LOOP_STACK[++LSP] = SP;
//                printf("add: %lld ", SP);
                break;
            case 36:  // RESTORE SP
                SP = LOOP_STACK[LSP--];
//                printf("res: %lld %d ", SP, LSP);
                break;
            case 37:  // TO REL
                reg1 = bytes_to_int(MEMORY + PC);  // addr of ptr
                PC += INT_LEN;
                reg2 = bytes_to_int(MEMORY + reg1);
                reg2 = rel_ptr(reg2);
                int_to_bytes(MEMORY + reg1, reg2);
                break;
            case 38:  // ADD_I
            read_2_ints
                reg1 = true_ptr(reg1);
                reg3 = bytes_to_int(MEMORY + reg1);
                reg3 = reg3 + reg2;
                int_to_bytes(MEMORY + reg1, reg3);
//                printf("addi, addr %lld\n", reg1);
                break;
//            case 40:  // ABSENT_1
//                break;
//            case 41:  // ABSENT_8
//                PC += 7;
//                break;
//            case 42:  // ABSENT_24
//                PC += 23;
//                break;
            case 39:  // INT_TO_FLOAT
            read_2_ints  // des, src
                reg1 = true_ptr(reg1);
                reg2 = true_ptr(reg2);
                reg3 = bytes_to_int(MEMORY + reg2);  // int value
                reg13 = (double) reg3;
                double_to_bytes(MEMORY + reg1, reg13);
                break;
            case 40:  // FLOAT_TO_INT
            read_2_ints  // des, src
                reg1 = true_ptr(reg1);
                reg2 = true_ptr(reg2);
                reg13 = bytes_to_double(MEMORY + reg2);
                reg3 = (int_fast64_t) reg13;
//                printf("%lld %f\n", reg3, reg13);
                int_to_bytes(MEMORY + reg1, reg3);
                break;
            case 50:  // ADD_F
            read_3_true_ptr // des, left, right
                reg13 = bytes_to_double(MEMORY + reg2);
                reg14 = bytes_to_double(MEMORY + reg3);
                reg13 = reg13 + reg14;
                double_to_bytes(MEMORY + reg1, reg13);
                break;
            case 51:  // SUB_F
            read_3_true_ptr // des, left, right
                reg13 = bytes_to_double(MEMORY + reg2);
                reg14 = bytes_to_double(MEMORY + reg3);
                reg13 = reg13 - reg14;
                double_to_bytes(MEMORY + reg1, reg13);
                break;
            case 52:  // MUL_F
            read_3_true_ptr // des, left, right
                reg13 = bytes_to_double(MEMORY + reg2);
                reg14 = bytes_to_double(MEMORY + reg3);
                reg13 = reg13 * reg14;
                double_to_bytes(MEMORY + reg1, reg13);
                break;
            case 53:  // DIV_F
            read_3_true_ptr // des, left, right
                reg13 = bytes_to_double(MEMORY + reg2);
                reg14 = bytes_to_double(MEMORY + reg3);
                reg13 = reg13 / reg14;
                double_to_bytes(MEMORY + reg1, reg13);
                break;
            case 54:  // MOD_F
            read_3_true_ptr // des, left, right
                reg13 = bytes_to_double(MEMORY + reg2);
                reg14 = bytes_to_double(MEMORY + reg3);
                reg13 = double_mod(reg13, reg14);
                double_to_bytes(MEMORY + reg1, reg13);
                break;
            case 55:  // EQ_F
            read_3_true_ptr // des, left, right
                reg13 = bytes_to_double(MEMORY + reg2);
                reg14 = bytes_to_double(MEMORY + reg3);
                reg13 = reg13 - reg14;

                reg11 = reg13 == 0 ? 1 : 0;
                MEMORY[reg1] = reg11;
                break;
            case 56:  // GT_F
            read_3_true_ptr // des, left, right
                reg13 = bytes_to_double(MEMORY + reg2);
                reg14 = bytes_to_double(MEMORY + reg3);
                reg13 = reg13 - reg14;

                reg11 = reg13 > 0 ? 1 : 0;
                MEMORY[reg1] = reg11;
                break;
            case 57:  // LT_F
            read_3_true_ptr // des, left, right
                reg13 = bytes_to_double(MEMORY + reg2);
                reg14 = bytes_to_double(MEMORY + reg3);
                reg13 = reg13 - reg14;

                reg11 = reg13 < 0 ? 1 : 0;
                MEMORY[reg1] = reg11;
                break;
            case 58:  // NE_F
            read_3_true_ptr // des, left, right
                reg13 = bytes_to_double(MEMORY + reg2);
                reg14 = bytes_to_double(MEMORY + reg3);
                reg13 = reg13 - reg14;

                reg11 = reg13 != 0 ? 1 : 0;
                MEMORY[reg1] = reg11;
                break;
            default:
                fprintf(stderr, "Unknown instruction %d\n", instruction);
                return;
        }
//        printf("sp: %lld\n", SP);

        if (SP >= LITERAL_START) {
            fprintf(stderr, "Stack Overflow\n");
            return;
        }
        if (ERROR_CODE != 0) {
            fprintf(stderr, "Error code: %d \n", ERROR_CODE);
            return;
        }
        if (MEMORY[0] != 0) {
            fprintf(stderr, "Segmentation fault: core dumped \n");
            return;
        }
    }
}

void test() {
    int_fast64_t i = 94;
    unsigned char *arr = malloc(12);
    int_to_bytes(arr + 1, i);
    printf("%lld\n", bytes_to_int(arr + 1));

    float c = (int) 6.6;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: tpl.exe -[FLAG] TPC_FILE");
        exit(1);
    }

    int p_memory = 0;
    int p_exit = 0;
    char *file_name = argv[1];

    for (int i = 1; i < argc; i++) {
        char *arg = argv[i];
        if (arg[0] == '-') {
            switch (arg[1]) {
                case 'e':
                    p_exit = 1;
                    break;
                case 'm':
                    p_memory = 1;
                    break;
                default:
                    printf("Unknown flag: -%c", arg[1]);
                    break;
            }
        } else {
            file_name = arg;
        }
    }

    int read;

    unsigned char *codes = read_file(file_name, &read);

    vm_load(codes, read);

    vm_run();

    if (p_memory) print_memory();
    if (p_exit) printf("Process finished with exit code %lld\n", bytes_to_int(MEMORY + 1));

    vm_shutdown();

    exit(0);
}
