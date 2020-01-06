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

//#define rel_ptr(ptr) (ptr < LITERAL_START && CSP >= 0 ? ptr - CALL_STACK[CSP] : ptr)

const int INT_LEN = 8;
const int PTR_LEN = 8;
const int FLOAT_LEN = 8;
const int CHAR_LEN = 1;
//const int BOOLEAN_LEN = 1;
const int VOID_LEN = 0;

const int INT_LEN_2 = 16;
//const int INT_LEN_3 = 24;
//const int INT_LEN_4 = 32;

const int_fast64_t STACK_START = 1;
int_fast64_t LITERAL_START = 1024;
int_fast64_t FUNCTIONS_START = 1024;
int_fast64_t CODE_START = 1024;
int_fast64_t HEAP_START = 1024;

const int_fast64_t MEMORY_SIZE = 4096;
unsigned char MEMORY[4096];

uint_fast64_t SP = 1;
uint_fast64_t PC = 1024;

uint_fast64_t CALL_STACK[1000];  // recursion limit
int CSP = -1;

int PC_STACK[1000];
int PSP = -1;

int LOOP_STACK[1000];  // 1000 nested loop
int LSP = -1;

int MAIN_RTN_PTR = 1;

// The error code, set by virtual machine. Used to tell the main loop that the process is interrupted
// Interrupt the vm if the code is not 0
//
// 0: No error
// 1: Memory address error
// 2: Native function error
// 3: VM option error
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
        printf("%lld, ", CALL_STACK[i]);
    }
    printf("\n");
}

void vm_load(const unsigned char *codes, int read) {
    int_fast64_t stack_size = bytes_to_int(codes);

    if (stack_size != LITERAL_START) {
        fprintf(stderr, "Unmatched stack size\n");
        ERROR_CODE = 3;
        return;
    }

    int_fast64_t literal_size = bytes_to_int(codes + INT_LEN);
    int_fast64_t functions_size = bytes_to_int(codes + INT_LEN_2);

    FUNCTIONS_START += literal_size;
    CODE_START = FUNCTIONS_START + functions_size;
    PC = CODE_START;

    int copy_len = read - INT_LEN * 3;
    HEAP_START = LITERAL_START + copy_len;

    memcpy(MEMORY + LITERAL_START, codes + INT_LEN * 3, copy_len);

    AVAILABLE = build_heap(HEAP_START, MEMORY_SIZE, &AVA_SIZE);
//    print_memory();
}

void vm_shutdown() {
    free(AVAILABLE);
}

void exit_func() {
    SP = CALL_STACK[CSP--];
    PC = PC_STACK[PSP--];
}

void native_printf(int_fast64_t arg_len, const unsigned char *arg_array) {
    if (arg_len < 8) {
        printf("'printf' takes at least 1 argument");
        ERROR_CODE = 1;
        return;
    }
    int_fast64_t fmt_ptr = bytes_to_int(arg_array);
//    for (int j = 0; j < arg_len; j++) printf("%d ", arg_array[j]);
//    printf("\n");
    int_fast64_t fmt_end = fmt_ptr;
    while (MEMORY[fmt_end] != 0) fmt_end++;

    int_fast64_t i = fmt_ptr;
    int arg_ptr = INT_LEN;
    int f = 0;
    for (; i < fmt_end; i++) {
        unsigned char ch = MEMORY[i];
        if (ch == '%') {
            f = 1;
        } else if (f) {
            if (ch == 'd') {  // int
                f = 0;
                int_fast64_t value = bytes_to_int(arg_array + arg_ptr);
                arg_ptr += INT_LEN;
                printf("%lld", value);
            } else if (ch == 'c') {  // char
                f = 0;
                unsigned char value = arg_array[arg_ptr++];
                printf("%c", value);
            } else if (ch == 'f') {  // float
                f = 0;
                double value = bytes_to_double(arg_array + arg_ptr);
                arg_ptr += FLOAT_LEN;
                printf("%f", value);
            } else if (ch == 's') {  // string
                f = 0;
                int_fast64_t str_ptr = bytes_to_int(arg_array + arg_ptr);
                arg_ptr += INT_LEN;
                for (; MEMORY[str_ptr] != 0; str_ptr++) printf("%c", MEMORY[str_ptr]);
            } else {
                fprintf(stderr, "Unknown flag: '%c'\n", ch);
                f = 0;
            }
        } else {
            printf("%c", ch);
        }
    }
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

void _native_malloc(int_fast64_t ret_ptr, int_fast64_t asked_len) {
    int_fast64_t real_len = asked_len + INT_LEN;
    int_fast64_t allocate_len = real_len % 8 == 0 ? real_len / 8 : real_len / 8 + 1;

    int_fast64_t location = find_ava(allocate_len);

    int_to_bytes(MEMORY + location, allocate_len);
    int_to_bytes(MEMORY + ret_ptr, location + INT_LEN);
}

void native_malloc(int_fast64_t arg_len, int_fast64_t ret_ptr, const unsigned char *args) {
    if (arg_len != INT_LEN) {
        printf("Unmatched arg length or return length");
        ERROR_CODE = 2;
        return;
    }

    int_fast64_t asked_len = bytes_to_int(args);
    _native_malloc(ret_ptr, asked_len);
}

void native_clock(int_fast64_t arg_len, int_fast64_t ret_ptr) {
    if (arg_len != 0) {
        printf("Unmatched arg length or return length");
        ERROR_CODE = 2;
        return;
    }
    int_fast64_t t = clock();
    int_to_bytes(MEMORY + ret_ptr, t);
}

void native_free(int_fast64_t arg_len, const unsigned char *args) {
    if (arg_len != PTR_LEN) {
        printf("Unmatched arg length or return length");
        ERROR_CODE = 2;
        return;
    }
    int_fast64_t free_ptr = bytes_to_int(args);
    int_fast64_t real_ptr = free_ptr - INT_LEN;
    int_fast64_t alloc_len = bytes_to_int(MEMORY + real_ptr);

    if (real_ptr < HEAP_START || real_ptr > MEMORY_SIZE) {
        printf("Cannot free pointer: %lld outside heap\n", real_ptr);
        ERROR_CODE = 2;
        return;
    }

    for (int i = 0; i < alloc_len; i++) {
        insert_heap(AVAILABLE, &AVA_SIZE, real_ptr + i * HEAP_GAP);
//        printf("free %lld \n", real_ptr + i * HEAP_GAP);
    }

//    print_sorted(AVAILABLE, AVA_SIZE);
}

void native_mem_copy(int_fast64_t arg_len, const unsigned char *args) {
    if (arg_len != INT_LEN * 3) {
        fprintf(stderr, "'mem_copy' takes 3 arguments.\n");
        ERROR_CODE = 2;
        return;
    }
    int_fast64_t dest = bytes_to_int(args);
    int_fast64_t src = bytes_to_int(args + INT_LEN);
    int_fast64_t length = bytes_to_int(args + INT_LEN_2);

//    printf("%lld %lld %lld\n", dest_addr, src_addr, length_ptr);
    memcpy(MEMORY + dest, MEMORY + src, length);
}

void call_native(int_fast64_t func, int_fast64_t ret_ptr_end, int_fast64_t arg_len, unsigned char *args) {
    int ret_len;
//    printf("func: %lld, arg len: %lld\n", func, arg_len);
    switch (func) {
        case 1:  // clock
            ret_len = INT_LEN;
            native_clock(arg_len, ret_ptr_end - ret_len);
            break;
        case 2:  // malloc
            ret_len = PTR_LEN;
            native_malloc(arg_len, ret_ptr_end - ret_len, args);
            break;
        case 3:  // printf
            native_printf(arg_len, args);
            break;
        case 4:  // mem_copy
            native_mem_copy(arg_len, args);
            break;
        case 5:  // free
            native_free(arg_len, args);
            break;
        default:
            printf("Unknown native function %lld", func);
            return;
    }
}

void vm_set_args(int vm_argc, char **vm_argv) {
    if (MEMORY[PC + 12] == 4) {  // no args
        MAIN_RTN_PTR = 1;
    } else {
        int_to_bytes(MEMORY + 1, vm_argc);
        int_to_bytes(MEMORY + INT_LEN + 1, 234);
        MAIN_RTN_PTR = 1 + INT_LEN;

        _native_malloc(INT_LEN + 1, PTR_LEN * vm_argc);
        int_fast64_t first_arg_pos = bytes_to_int(MEMORY + INT_LEN + 1);
//        printf("%lld\n", first_arg_pos);

        for (int i = 0; i < vm_argc; i++) {
            unsigned int arg_len = strlen(vm_argv[i]) + 1;
//            printf("%u\n", arg_len);
            _native_malloc(first_arg_pos + PTR_LEN * i, arg_len);
            int_fast64_t ptr = bytes_to_int(MEMORY + first_arg_pos + PTR_LEN * i);
            memcpy(MEMORY + ptr, vm_argv[i], arg_len);
        }
    }
}

void vm_run() {
    union reg64 {
        int_fast64_t int_value;
        double double_value;
        unsigned char bytes[8];
    };

    union reg64 regs64[8];

    unsigned int reg_p1;
    unsigned int reg_p2;
    unsigned int reg_p3;

    int_fast64_t ret;

    register unsigned char instruction;

    while (PC < HEAP_START) {
        instruction = MEMORY[PC++];
        switch (instruction) {
            case 2:  // Stop
                exit_func();
                break;
            case 3:  // ASSIGN
                reg_p1 = MEMORY[PC++];  // dest
                reg_p2 = MEMORY[PC++];  // src
                reg_p3 = MEMORY[PC++];  // len
                memcpy(MEMORY + true_ptr(regs64[reg_p1].int_value),
                       MEMORY + true_ptr(regs64[reg_p2].int_value),
                       regs64[reg_p3].int_value);
                break;
            case 4:  // CALL
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];

//                regs64[reg_p1].int_value = bytes_to_int(MEMORY + regs64[reg_p1].int_value);  // true ftn ptr
                memcpy(regs64[reg_p1].bytes, MEMORY + regs64[reg_p1].int_value, PTR_LEN);  // true ftn ptr

                PC_STACK[++PSP] = PC;
                CALL_STACK[++CSP] = SP - regs64[reg_p2].int_value;
//                printf("%lld\n", CALL_STACK[CSP]);

                PC = regs64[reg_p1].int_value;
                break;
            case 31:  // CALL_NAT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];

//                regs64[reg_p1].int_value = bytes_to_int(MEMORY + regs64[reg_p1].int_value);  // true ftn ptr
//                regs64[reg_p1].int_value = bytes_to_int(MEMORY + regs64[reg_p1].int_value);  // ftn content
                memcpy(regs64[reg_p1].bytes, MEMORY + regs64[reg_p1].int_value, PTR_LEN);  // true ftn ptr
                memcpy(regs64[reg_p1].bytes, MEMORY + regs64[reg_p1].int_value, PTR_LEN);  // ftn content

//                printf("call nat %lld\n", regs64[reg_p1].int_value);

                call_native(regs64[reg_p1].int_value,
                            SP - regs64[reg_p2].int_value,
                            regs64[reg_p2].int_value,
                            MEMORY + SP - regs64[reg_p2].int_value);

                SP -= regs64[reg_p2].int_value;
                break;
            case 5:  // RETURN
                reg_p1 = MEMORY[PC++];  // reg of value ptr
                reg_p2 = MEMORY[PC++];  // reg of length
                ret = CALL_STACK[CSP] - regs64[reg_p2].int_value;
                memcpy(MEMORY + ret,
                        MEMORY + true_ptr(regs64[reg_p1].int_value),
                        regs64[reg_p2].int_value);

                exit_func();
                break;
            case 6:  // GOTO
                reg_p1 = MEMORY[PC++];
                PC += regs64[reg_p1].int_value;
                break;
            case 7:  // PUSH STACK
                reg_p1 = MEMORY[PC++];
                SP += regs64[reg_p1].int_value;
                if (SP >= LITERAL_START) {
                    fprintf(stderr, "Stack Overflow\n");
                    ERROR_CODE = 1;
                    return;
                }
                break;
            case 8:  // LOAD
                reg_p1 = MEMORY[PC++];  // reg index of loading reg
                memcpy(regs64[reg_p1].bytes, MEMORY + PC, INT_LEN);
                PC += INT_LEN;
//                regs64[reg_p1].int_value = bytes_to_int(MEMORY + true_ptr(regs64[reg_p1].int_value));
                memcpy(regs64[reg_p1].bytes, MEMORY + true_ptr(regs64[reg_p1].int_value), INT_LEN);
                break;
            case 9:  // STORE
                reg_p1 = MEMORY[PC++];  // reg index of value addr
                reg_p2 = MEMORY[PC++];  // reg index of loading reg
                regs64[reg_p1].int_value = true_ptr(bytes_to_int(MEMORY + PC));
                PC += INT_LEN;
                memcpy(MEMORY + regs64[reg_p1].int_value, regs64[reg_p2].bytes, 8);
                break;
            case 10:  // LOAD_I
                reg_p1 = MEMORY[PC++];
                memcpy(regs64[reg_p1].bytes, MEMORY + PC, INT_LEN);
                PC += INT_LEN;
                break;
            case 11:  // ADD INT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
//                printf("addend %lld, adder %lld\n", regs64[reg_p1].int_value, regs64[reg_p2].int_value);
                regs64[reg_p1].int_value = regs64[reg_p1].int_value + regs64[reg_p2].int_value;
                break;
            case 24:  // CAST INT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                reg_p3 = MEMORY[PC++];

                if (regs64[reg_p3].int_value <= INT_LEN) {
                    memcpy(MEMORY + true_ptr(regs64[reg_p1].int_value),
                           MEMORY + true_ptr(regs64[reg_p2].int_value),
                           regs64[reg_p3].int_value);
                }
                break;
            case 12:  // SUB INT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value - regs64[reg_p2].int_value;
                break;
            case 13:  // MUL INT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value * regs64[reg_p2].int_value;
                break;
            case 14:  // DIV INT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value / regs64[reg_p2].int_value;
                break;
            case 15:  // MOD INT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value % regs64[reg_p2].int_value;
                break;
            case 16:  // EQ
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value - regs64[reg_p2].int_value;  // cmp result

                regs64[reg_p1].int_value = regs64[reg_p1].int_value == 0 ? 1 : 0;
                break;
            case 17:  // GT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value - regs64[reg_p2].int_value;  // cmp result

                regs64[reg_p1].int_value = regs64[reg_p1].int_value > 0 ? 1 : 0;
                break;
            case 18:  // LT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value - regs64[reg_p2].int_value;  // cmp result

                regs64[reg_p1].int_value = regs64[reg_p1].int_value < 0 ? 1 : 0;
                break;
            case 19:  // AND
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value && regs64[reg_p2].int_value;
                break;
            case 20:  // OR
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value || regs64[reg_p2].int_value;
                break;
            case 21:  // NOT
                reg_p1 = MEMORY[PC++];
                regs64[reg_p1].int_value = !regs64[reg_p1].int_value;
                break;
            case 22:  // NE
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value - regs64[reg_p2].int_value;  // cmp result

                regs64[reg_p1].int_value = regs64[reg_p1].int_value == 0 ? 0 : 1;
                break;
            case 23:  // NEG
                reg_p1 = MEMORY[PC++];
                regs64[reg_p1].int_value = -regs64[reg_p1].int_value;
                break;
            case 30:  // IF ZERO GOTO
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
//                printf("%lld ", regs64[reg_p2]);
                if (regs64[reg_p2].int_value == 0) {
                    PC += regs64[reg_p1].int_value;
                }
                break;
            case 32:  // STORE ADDR, store addr to des
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = true_ptr(regs64[reg_p1].int_value);
                regs64[reg_p2].int_value = true_ptr(regs64[reg_p2].int_value);
//                printf("%lld %lld\n", regs64[reg_p1], regs64[reg_p2]);
                int_to_bytes(MEMORY + regs64[reg_p1].int_value, regs64[reg_p2].int_value);
                break;
            case 33:  // UNPACK ADDR
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                reg_p3 = MEMORY[PC++];

                memcpy(MEMORY + true_ptr(regs64[reg_p1].int_value),
                       MEMORY + regs64[reg_p2].int_value,
                       regs64[reg_p3].int_value);
                break;
            case 34:  // PTR ASSIGN
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                reg_p3 = MEMORY[PC++];

                memcpy(MEMORY + regs64[reg_p1].int_value,
                       MEMORY + true_ptr(regs64[reg_p2].int_value),
                       regs64[reg_p3].int_value);
                break;
            case 35:  // STORE SP
                LOOP_STACK[++LSP] = SP;
//                printf("add: %lld ", SP);
                break;
            case 36:  // RESTORE SP
                SP = LOOP_STACK[LSP--];
//                printf("res: %lld %d ", SP, LSP);
                break;
            case 37:  // MOVE_REG
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1] = regs64[reg_p2];
                break;
            case 39:  // INT_TO_FLOAT
                reg_p1 = MEMORY[PC++];
                regs64[reg_p1].double_value = (double) regs64[reg_p1].int_value;
                break;
            case 40:  // FLOAT_TO_INT
                reg_p1 = MEMORY[PC++];
                regs64[reg_p1].int_value = (int_fast64_t) regs64[reg_p1].double_value;
                break;
            case 50:  // ADD_F
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].double_value = regs64[reg_p1].double_value + regs64[reg_p2].double_value;
                break;
            case 51:  // SUB_F
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].double_value = regs64[reg_p1].double_value - regs64[reg_p2].double_value;
                break;
            case 52:  // MUL_F
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].double_value = regs64[reg_p1].double_value * regs64[reg_p2].double_value;
                break;
            case 53:  // DIV_F
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].double_value = regs64[reg_p1].double_value / regs64[reg_p2].double_value;
                break;
            case 54:  // MOD_F
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].double_value = double_mod(regs64[reg_p1].double_value, regs64[reg_p2].double_value);
                break;
            case 55:  // EQ_F
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].double_value = regs64[reg_p1].double_value - regs64[reg_p2].double_value;  // cmp result

                regs64[reg_p1].int_value = regs64[reg_p1].double_value == 0 ? 1 : 0;
                break;
            case 56:  // GT_F
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].double_value = regs64[reg_p1].double_value - regs64[reg_p2].double_value;  // cmp result

                regs64[reg_p1].int_value = regs64[reg_p1].double_value > 0 ? 1 : 0;
                break;
            case 57:  // LT_F
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].double_value = regs64[reg_p1].double_value - regs64[reg_p2].double_value;  // cmp result

                regs64[reg_p1].int_value = regs64[reg_p1].double_value < 0 ? 1 : 0;
                break;
            case 58:  // NE_F
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].double_value = regs64[reg_p1].double_value - regs64[reg_p2].double_value;  // cmp result

                regs64[reg_p1].int_value = regs64[reg_p1].double_value == 0 ? 0 : 1;
                break;
            case 59:  // NEG_F
                reg_p1 = MEMORY[PC++];
                regs64[reg_p1].double_value = -regs64[reg_p1].double_value;
                break;
            default:
                fprintf(stderr, "Unknown instruction %d\n", instruction);
                return;
        }
//        printf("sp: %lld\n", SP);

//        if (SP >= LITERAL_START) {
//            fprintf(stderr, "Stack Overflow\n");
//            return;
//        }
//        if (ERROR_CODE != 0) {
//            fprintf(stderr, "Error code: %d \n", ERROR_CODE);
//            return;
//        }
//        if (MEMORY[0] != 0) {
//            fprintf(stderr, "Segmentation fault: core dumped \n");
//            return;
//        }
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

    int vm_args_begin = 0;

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
            vm_args_begin = i;
            break;
        }
    }

    int vm_argc = argc - vm_args_begin;
    char **vm_argv = malloc(sizeof(char**));
    for (int i = vm_args_begin; i < argc; i++) {
        vm_argv[i - vm_args_begin] = argv[i];
    }

    int read;

    unsigned char *codes = read_file(file_name, &read);

    vm_load(codes, read);
    vm_set_args(vm_argc, vm_argv);
    vm_run();

    if (ERROR_CODE != 0) int_to_bytes(MEMORY + MAIN_RTN_PTR, ERROR_CODE);

    if (p_memory) print_memory();
    if (p_exit) printf("Process finished with exit code %lld\n", bytes_to_int(MEMORY + MAIN_RTN_PTR));

    vm_shutdown();

    exit(0);
}
