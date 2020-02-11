//
// Created by zbh on 2019/12/9.
//

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
//#include "vm.h"
#include "lib.h"
#include "heap.h"

#define STACK_SIZE 1024
#define MEMORY_SIZE 134217728
#define RECURSION_LIMIT 1000
#define USE_HEAP_MEM 1  // whether to use a 'heap' data structure to manage heap memory

#define true_ptr(ptr) (ptr < LITERAL_START && FSP >= 0 ? ptr + FP : ptr)
#define true_ptr_sp(ptr) (ptr < LITERAL_START ? ptr + SP : ptr)

#define rshift_logical(val, n) ((int_fast64_t) ((uint_fast64_t) val >> n));

#define exit_func {             \
    FP = CALL_STACK[FSP--];     \
    PC = PC_STACK[PSP--];       \
}

const int INT_LEN = 8;
const int PTR_LEN = 8;
const int FLOAT_LEN = 8;
const int CHAR_LEN = 1;
//const int BOOLEAN_LEN = 1;
//const int VOID_LEN = 0;

const int INT_LEN_2 = 16;
//const int INT_LEN_3 = 24;
//const int INT_LEN_4 = 32;

//int_fast64_t CALL_STACK_BEGINS = 1;
int_fast64_t LITERAL_START = STACK_SIZE;
int_fast64_t GLOBAL_START = STACK_SIZE;
int_fast64_t FUNCTIONS_START = STACK_SIZE;
int_fast64_t CODE_START = STACK_SIZE;
int_fast64_t HEAP_START = STACK_SIZE;

int MAIN_HAS_ARG = 0;

unsigned char MEMORY[MEMORY_SIZE];

uint_fast64_t SP = 9;  // stack pointer
uint_fast64_t FP = 1;  // frame pointer
uint_fast64_t PC = STACK_SIZE;

uint_fast64_t CALL_STACK[RECURSION_LIMIT];  // recursion limit
int FSP = -1;

int PC_STACK[RECURSION_LIMIT];
int PSP = -1;

uint_fast64_t RET_STACK[RECURSION_LIMIT];
int RSP = -1;

// The error code, set by virtual machine. Used to tell the main loop that the process is interrupted
// Interrupt the vm if the code is not 0
//
// 0: No error
// 1: Memory address error
// 2: Native invoke error
// 3: VM option error

const int ERR_STACK_OVERFLOW = 1;
const int ERR_NATIVE_INVOKE = 2;
const int ERR_VM_OPT = 3;
const int ERR_HEAP_COLLISION = 4;
const int ERR_INSTRUCTION = 5;

int_fast64_t ERROR_CODE = 0;

void print_memory() {
    int i = 0;
    printf("Stack ");
    for (; i < LITERAL_START; i++) {
        printf("%d ", MEMORY[i]);
        if (i % 8 == 0) printf("| ");
    }

    printf("\nLiteral %lld: ", LITERAL_START);
    for (; i < GLOBAL_START; ++i) {
        printf("%d ", MEMORY[i]);
    }

    printf("\nGlobal %lld: ", GLOBAL_START);
    for (; i < FUNCTIONS_START; ++i) {
        printf("%d ", MEMORY[i]);
    }

    printf("\nFunctions %lld: ", FUNCTIONS_START);
    for (; i < CODE_START; i++) {
        printf("%d ", MEMORY[i]);
    }
//    printf("\nFunctions %lld: ...", FUNCTIONS_START);
//    i = CODE_START;

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
    for (int i = 0; i <= FSP; i++) {
        printf("%lld, ", CALL_STACK[i]);
    }
    printf("\n");
}

int vm_load(const unsigned char *codes, int read) {
    int_fast64_t stack_size = bytes_to_int(codes);

    if (stack_size != LITERAL_START) {
        fprintf(stderr, "Unmatched stack size\n");
        ERROR_CODE = ERR_VM_OPT;
        return 1;
    }

    int_fast64_t literal_size = bytes_to_int(codes + INT_LEN);
    int_fast64_t global_len = bytes_to_int(codes + INT_LEN * 2);
    int_fast64_t functions_size = bytes_to_int(codes + INT_LEN * 3);
    MAIN_HAS_ARG = codes[INT_LEN * 4];

    int head_len = INT_LEN * 4 + 1;

    GLOBAL_START = LITERAL_START + literal_size;
    FUNCTIONS_START = GLOBAL_START + global_len;
    CODE_START = FUNCTIONS_START + functions_size;
    PC = CODE_START;

    int_fast64_t func_and_code_len = read - head_len - literal_size;
    HEAP_START = FUNCTIONS_START + func_and_code_len;

    if (HEAP_START >= MEMORY_SIZE) {
        fprintf(stderr, "Not enough memory to start vm\n");
        ERROR_CODE = ERR_VM_OPT;
        return 1;
    }

    memcpy(MEMORY + LITERAL_START, codes + head_len, literal_size);  // copy literal
    memcpy(MEMORY + FUNCTIONS_START, codes + head_len + literal_size, func_and_code_len);
//    memcpy(MEMORY + LITERAL_START, codes + INT_LEN * 4 + 1, copy_len);

    if (USE_HEAP_MEM)
        AVAILABLE = build_heap(HEAP_START, MEMORY_SIZE, &AVA_SIZE);
    else
        AVAILABLE2 = build_ava_link(HEAP_START, MEMORY_SIZE);
//    print_memory();
    return 0;
}

void vm_shutdown() {
    if (USE_HEAP_MEM)
        free(AVAILABLE);
    else
        free_link(AVAILABLE2);
}

StringBuilder *str_format(int_fast64_t arg_len, const unsigned char *arg_array) {
    int_fast64_t fmt_ptr = bytes_to_int(arg_array);
    int_fast64_t fmt_end = fmt_ptr;
    while (MEMORY[fmt_end] != 0) fmt_end++;

    int_fast64_t i = fmt_ptr;
    int arg_ptr = INT_LEN;
    int f = 0;

    StringBuilder *builder = create_string();

    char buffer[100];

    for (; i < fmt_end; i++) {
        unsigned char ch = MEMORY[i];
        if (ch == '%') {
            f = 1;
        } else if (f) {
            if (ch == 'd') {  // int
                f = 0;
                int_fast64_t value = bytes_to_int(arg_array + arg_ptr);
                arg_ptr += INT_LEN;

                int buf_len = sprintf(buffer, "%lld", value);
                append_string_ptr(builder, buf_len, buffer);
            } else if (ch == 'c') {  // char
                f = 0;
                unsigned char value = arg_array[arg_ptr++];
                append_string(builder, value);
            } else if (ch == 'f') {  // float
                f = 0;
                double value = bytes_to_double(arg_array + arg_ptr);
                arg_ptr += FLOAT_LEN;
                int buf_len = sprintf(buffer, "%f", value);
                append_string_ptr(builder, buf_len, buffer);
            } else if (ch == 's') {  // string
                f = 0;
                int_fast64_t str_ptr = bytes_to_int(arg_array + arg_ptr);
                arg_ptr += INT_LEN;
                for (; MEMORY[str_ptr] != 0; str_ptr++) append_string(builder, MEMORY[str_ptr]);
            } else {
                fprintf(stderr, "Unknown flag: '%c'\n", ch);
                f = 0;
            }
        } else {
            append_string(builder, ch);
        }
    }
    return builder;
}

void native_printf(int_fast64_t arg_len, const unsigned char *arg_array) {
    if (arg_len < 8) {
        printf("'printf' takes at least 1 argument\n");
        ERROR_CODE = ERR_NATIVE_INVOKE;
        return;
    }
    StringBuilder *builder = str_format(arg_len, arg_array);
    print_string(builder);
    free_string(builder);
}

void native_stringf(int_fast64_t arg_len, int_fast64_t ret_ptr, const unsigned char *arg_array) {
    if (arg_len < 8) {
        printf("'stringf' takes at least 1 argument\n");
        ERROR_CODE = ERR_NATIVE_INVOKE;
        return;
    }
    int_fast64_t buffer_ptr = bytes_to_int(arg_array);
    StringBuilder *builder = str_format(arg_len, arg_array + PTR_LEN);
    memcpy(MEMORY + buffer_ptr, builder->array, builder->size);
    int_to_bytes(MEMORY + ret_ptr, builder->size);
    free_string(builder);
}

void native_scanf(int_fast64_t arg_len, int_fast64_t ret_ptr, const unsigned char *arg_array) {
    if (arg_len < 8) {
        printf("'scanf' takes at least 1 argument\n");
        ERROR_CODE = ERR_NATIVE_INVOKE;
        return;
    }

    int len = 0;
    int capacity = 8;
    int cha;
    char *input = malloc(capacity);
    while ((cha = fgetc(stdin)) != EOF && cha != '\n') {
        input[len++] = (char) cha;
        if (len == capacity) {
            capacity *= 2;
            input = realloc(input, capacity);
        }
    }
    input[len] = '\0';
//    printf("inputs: %s\n", input);

    int_fast64_t fmt_ptr = bytes_to_int(arg_array);
    int_fast64_t fmt_end = fmt_ptr;
    while (MEMORY[fmt_end] != 0) fmt_end++;

//    printf("%lld %lld\n", fmt_ptr, fmt_end);

    int_fast64_t i = fmt_ptr;

    int f = 0;
    int_fast64_t arg_ptr = INT_LEN;

    char *processing = input;

    int_fast64_t success_count = 0;

    for (; i < fmt_end; ++i) {
        unsigned char ch = MEMORY[i];
        if (ch == '%') {
            f = 1;
        } else if (f) {
            char *post = processing;

            if (ch == 'd') {
                f = 0;
                int_fast64_t ptr = bytes_to_int(arg_array + arg_ptr);
                arg_ptr += PTR_LEN;
                int_fast64_t scanned = strtoll(processing, &post, 10);
                int_to_bytes(MEMORY + ptr, scanned);
                success_count++;
            } else if (ch == 'f') {
                f = 0;
                int_fast64_t ptr = bytes_to_int(arg_array + arg_ptr);
                arg_ptr += PTR_LEN;
                double scanned = strtod(processing, &post);
                double_to_bytes(MEMORY + ptr, scanned);
                success_count++;
            } else if (ch == 'c') {
                f = 0;
                int_fast64_t ptr = bytes_to_int(arg_array + arg_ptr);
                arg_ptr += PTR_LEN;
                while (*processing == ' ') {
                    processing++;
                    post++;
                }
                char scanned = *post;
                if (scanned != '\0' && scanned != '\n')
                    post++;
                MEMORY[ptr] = scanned;
                success_count++;
            } else if (ch == 's') {
                f = 0;
                int_fast64_t ptr = bytes_to_int(arg_array + arg_ptr);
                arg_ptr += PTR_LEN;
                while (*processing == ' ') {  // skip spaces
                    processing++;
                    post++;
                }
                while (*post != ' ' && *post != '\n' && *post != '\0') {
                    post++;
                }
                int_fast64_t str_len = post - processing;
                memcpy(MEMORY + ptr, processing, str_len);
                MEMORY[ptr + str_len] = '\0';
                success_count++;
            }

            if (post == processing) {  // does not scan anything in this iteration
                success_count--;
                break;
            } else {
                processing = post;
            }
        }
    }

    int_to_bytes(MEMORY + ret_ptr, success_count);

    free(input);
}

int_fast64_t find_ava_link(int length) {
    LinkedNode *head = AVAILABLE2;
    while (head->next != NULL) {
        int i = 0;
        LinkedNode *cur = head->next;
        for (; i < length - 1; ++i) {
            LinkedNode *next = cur->next;
            if (next == NULL || next->addr != cur->addr + HEAP_GAP) {
                break;
            }
            cur = next;
        }
        if (i == length - 1) {  // found!
            LinkedNode *node = head->next;
            int_fast64_t found = node->addr;
            head->next = cur->next;
            for (int j = 0; j < length; ++j) {
                LinkedNode *next_free = node->next;
                free(node);
                node = next_free;
            }
            return found;
        } else {
            head = cur;
        }
    }
    return 0;  // not enough space in heap, ask for re-manage
}

void manage_heap() {

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
        ERROR_CODE = ERR_HEAP_COLLISION;
        return -1;
    }
}

int_fast64_t _inner_malloc_link(int_fast64_t allocate_len) {
    int_fast64_t location = find_ava_link(allocate_len);
//    printf("%lld, ", location);
    if (location == 0) {
        manage_heap();
        // TODO

        return -1;
    }
    return location;
}

void _native_malloc_link(int_fast64_t ret_ptr, int_fast64_t asked_len) {
    int_fast64_t real_len = asked_len + INT_LEN;
    int_fast64_t allocate_len = real_len % HEAP_GAP == 0 ? real_len / HEAP_GAP : real_len / HEAP_GAP + 1;
    int_fast64_t location = _inner_malloc_link(allocate_len);

    if (location <= 0) {
        fprintf(stderr, "Cannot allocate length %lld, available memory %d\n", asked_len, AVA_SIZE);
        ERROR_CODE = ERR_HEAP_COLLISION;
        return;
    }

    int_to_bytes(MEMORY + location, allocate_len);  // stores the allocated length
    int_to_bytes(MEMORY + ret_ptr, location + INT_LEN);
}

void _native_malloc(int_fast64_t ret_ptr, int_fast64_t asked_len) {
    int_fast64_t real_len = asked_len + INT_LEN;
    int_fast64_t allocate_len = real_len % HEAP_GAP == 0 ? real_len / HEAP_GAP : real_len / HEAP_GAP + 1;

    int_fast64_t location = find_ava(allocate_len);

    int_to_bytes(MEMORY + location, allocate_len);
    int_to_bytes(MEMORY + ret_ptr, location + INT_LEN);
}

void native_malloc(int_fast64_t arg_len, int_fast64_t ret_ptr, const unsigned char *args) {
    if (arg_len != INT_LEN) {
        printf("Unmatched arg length or return length\n");
        ERROR_CODE = ERR_NATIVE_INVOKE;
        return;
    }

    int_fast64_t asked_len = bytes_to_int(args);
    if (USE_HEAP_MEM)
        _native_malloc(ret_ptr, asked_len);
    else
        _native_malloc_link(ret_ptr, asked_len);
}

void native_clock(int_fast64_t arg_len, int_fast64_t ret_ptr) {
    if (arg_len != 0) {
        printf("Unmatched arg length or return length\n");
        ERROR_CODE = ERR_NATIVE_INVOKE;
        return;
    }
    int_fast64_t t = clock();
    int_to_bytes(MEMORY + ret_ptr, t);
}

void _free_link(int_fast64_t real_ptr, int_fast64_t alloc_len) {
    LinkedNode *head = AVAILABLE2;
    LinkedNode *after = AVAILABLE2;
    while (after->addr < real_ptr) {
        head = after;
        after = after->next;
    }
//    printf("%lld, %lld\n", head->addr, after->addr);
    for (int i = 0; i < alloc_len; ++i) {
        LinkedNode *node = malloc(sizeof(LinkedNode));
        node->addr = real_ptr + i * HEAP_GAP;
        head->next = node;
        head = node;
    }
    if (head->addr >= after->addr) {
        fprintf(stderr, "Heap memory collision");
        ERROR_CODE = ERR_HEAP_COLLISION;
        head->next = NULL;  // avoid cyclic reference
        return;
    }
    head->next = after;
}

void _free_heap(int_fast64_t real_ptr, int_fast64_t alloc_len) {
    for (int i = 0; i < alloc_len; i++) {
        if (insert_heap(AVAILABLE, &AVA_SIZE, real_ptr + i * HEAP_GAP) != 0) {
            fprintf(stderr, "Heap memory collision");
            ERROR_CODE = ERR_HEAP_COLLISION;
            return;
        }
//        printf("free %lld \n", real_ptr + i * HEAP_GAP);
    }
}

void native_free(int_fast64_t arg_len, const unsigned char *args) {
    if (arg_len != PTR_LEN) {
        printf("Unmatched arg length or return length\n");
        ERROR_CODE = ERR_NATIVE_INVOKE;
        return;
    }
    int_fast64_t free_ptr = bytes_to_int(args);
    int_fast64_t real_ptr = free_ptr - INT_LEN;
    int_fast64_t alloc_len = bytes_to_int(MEMORY + real_ptr);

    if (real_ptr < HEAP_START || real_ptr > MEMORY_SIZE) {
        printf("Cannot free pointer: %lld outside heap\n", real_ptr);
        ERROR_CODE = ERR_HEAP_COLLISION;
        return;
    }

    if (USE_HEAP_MEM)
        _free_heap(real_ptr, alloc_len);
    else
        _free_link(real_ptr, alloc_len);

}

void native_mem_copy(int_fast64_t arg_len, const unsigned char *args) {
    if (arg_len != INT_LEN * 3) {
        fprintf(stderr, "'mem_copy' takes 3 arguments.\n");
        ERROR_CODE = ERR_NATIVE_INVOKE;
        return;
    }
    int_fast64_t dest = bytes_to_int(args);
    int_fast64_t src = bytes_to_int(args + INT_LEN);
    int_fast64_t length = bytes_to_int(args + INT_LEN_2);

//    printf("%lld %lld %lld\n", dest_addr, src_addr, length_ptr);
    memcpy(MEMORY + dest, MEMORY + src, length);
}

void call_native(int_fast64_t func, int_fast64_t ret_ptr, int_fast64_t arg_len, unsigned char *args) {
    switch (func) {
        case 1:  // clock
            native_clock(arg_len, ret_ptr);
            break;
        case 2:  // malloc
            native_malloc(arg_len, ret_ptr, args);
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
        case 6:  // stringf
            native_stringf(arg_len, ret_ptr, args);
            break;
        case 7:  // scanf
            native_scanf(arg_len, ret_ptr, args);
            break;
        default:
            printf("Unknown native function %lld\n", func);
            return;
    }
}

int str_len(const char *s) {
    int i = 0;
    while (s[i] != '\0') i++;
    return i;
}

void vm_set_args(int vm_argc, char **vm_argv) {
    if (MAIN_HAS_ARG) {
        int_to_bytes(MEMORY + FUNCTIONS_START - 16, vm_argc);

        _native_malloc(FUNCTIONS_START - 8, PTR_LEN * vm_argc);
        int_fast64_t first_arg_pos = bytes_to_int(MEMORY + FUNCTIONS_START - 8);

        for (int i = 0; i < vm_argc; i++) {
            unsigned int arg_len = str_len(vm_argv[i]) + 1;
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

    while (ERROR_CODE == 0) {
        instruction = MEMORY[PC++];
//        printf("ins: %d ", instruction);
        switch (instruction) {
            case 1:  // EXIT
                return;
            case 2:  // Stop
            exit_func;
                break;
            case 3:  // ASSIGN
                reg_p1 = MEMORY[PC++];  // dest
                reg_p2 = MEMORY[PC++];  // src
                reg_p3 = MEMORY[PC++];  // len
                memcpy(MEMORY + regs64[reg_p1].int_value,
                       MEMORY + regs64[reg_p2].int_value,
                       regs64[reg_p3].int_value);
                break;
            case 4:  // CALL
                reg_p1 = MEMORY[PC++];
//                reg_p2 = MEMORY[PC++];
//                reg_p3 = MEMORY[PC++];

                memcpy(regs64[reg_p1].bytes, MEMORY + regs64[reg_p1].int_value, PTR_LEN);  // true ftn ptr

                PC_STACK[++PSP] = PC;
                CALL_STACK[++FSP] = FP;
//                RET_STACK[++RSP] = regs64[reg_p2].int_value;

                PC = regs64[reg_p1].int_value;
                break;
            case 46:  // SET_RET
                reg_p1 = MEMORY[PC++];
                RET_STACK[++RSP] = regs64[reg_p1].int_value;
                break;
            case 31:  // CALL_NAT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                reg_p3 = MEMORY[PC++];

                memcpy(regs64[reg_p1].bytes, MEMORY + regs64[reg_p1].int_value, PTR_LEN);  // true ftn ptr
                memcpy(regs64[reg_p1].bytes, MEMORY + regs64[reg_p1].int_value, PTR_LEN);  // ftn content

                call_native(regs64[reg_p1].int_value,
                            regs64[reg_p2].int_value,
                            regs64[reg_p3].int_value,
                            MEMORY + SP);
                break;
            case 5:  // RETURN
                reg_p1 = MEMORY[PC++];  // reg of value ptr
                reg_p2 = MEMORY[PC++];  // reg of length
                ret = RET_STACK[RSP--];
                memcpy(MEMORY + ret,
                       MEMORY + regs64[reg_p1].int_value,
                       regs64[reg_p2].int_value);
//                printf("ret %lld\n", ret);
                exit_func;
                break;
            case 6:  // GOTO
                reg_p1 = MEMORY[PC++];
                PC += regs64[reg_p1].int_value;
                break;
            case 7:  // LOAD_A
                reg_p1 = MEMORY[PC++];
                memcpy(regs64[reg_p1].bytes, MEMORY + PC, INT_LEN);
                regs64[reg_p1].int_value = true_ptr(regs64[reg_p1].int_value);
                PC += INT_LEN;
                break;
            case 8:  // LOAD
                reg_p1 = MEMORY[PC++];  // reg index of loading reg
                memcpy(regs64[reg_p1].bytes, MEMORY + PC, INT_LEN);
                memcpy(regs64[reg_p1].bytes, MEMORY + true_ptr(regs64[reg_p1].int_value), INT_LEN);
                PC += INT_LEN;
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
            case 38:  // CAST INT
                reg_p1 = MEMORY[PC++];  // dest
                reg_p2 = MEMORY[PC++];  // src
                reg_p3 = MEMORY[PC++];  // len
                if (regs64[reg_p3].int_value == CHAR_LEN) {  // cast char to int
                    regs64[reg_p3].int_value = MEMORY[regs64[reg_p2].int_value];
                    memcpy(MEMORY + regs64[reg_p1].int_value, regs64[reg_p3].bytes, INT_LEN);
                } else if (regs64[reg_p3].int_value == INT_LEN) {
                    memcpy(MEMORY + regs64[reg_p1].int_value,
                           MEMORY + regs64[reg_p2].int_value,
                           INT_LEN);
                }
                break;
            case 11:  // ADD INT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
//                printf("addend %lld, adder %lld\n", regs64[reg_p1].int_value, regs64[reg_p2].int_value);
                regs64[reg_p1].int_value = regs64[reg_p1].int_value + regs64[reg_p2].int_value;
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
            case 24:  // RSHIFT_A
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value >> regs64[reg_p2].int_value;
                break;
            case 25:  // RSHIFT_L
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = rshift_logical(regs64[reg_p1].int_value, regs64[reg_p2].int_value);
                break;
            case 26:  // LSHIFT
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value << regs64[reg_p2].int_value;
                break;
            case 27:  // B_AND
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value & regs64[reg_p2].int_value;
                break;
            case 28:  // B_OR
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value | regs64[reg_p2].int_value;
                break;
            case 29:  // B_XOR
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                regs64[reg_p1].int_value = regs64[reg_p1].int_value ^ regs64[reg_p2].int_value;
                break;
            case 30:  // IF ZERO GOTO
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
//                printf("%lld\n", regs64[reg_p2].int_value);
                if (regs64[reg_p2].int_value == 0) {
                    PC += regs64[reg_p1].int_value;
                }
                break;
            case 32:  // STORE ADDR, store addr to des
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                int_to_bytes(MEMORY + regs64[reg_p1].int_value, regs64[reg_p2].int_value);
                break;
            case 33:  // UNPACK ADDR
                reg_p1 = MEMORY[PC++];
                reg_p2 = MEMORY[PC++];
                reg_p3 = MEMORY[PC++];

                memcpy(MEMORY + regs64[reg_p1].int_value,
                       MEMORY + regs64[reg_p2].int_value,
                       regs64[reg_p3].int_value);
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
            case 41:  // LOAD_AS
                reg_p1 = MEMORY[PC++];
                memcpy(regs64[reg_p1].bytes, MEMORY + PC, INT_LEN);
                regs64[reg_p1].int_value = true_ptr_sp(regs64[reg_p1].int_value);
                PC += INT_LEN;
                break;
            case 42:  // PUSH STACK
                reg_p1 = MEMORY[PC++];
                SP += regs64[reg_p1].int_value;
                if (SP >= LITERAL_START) {
                    fprintf(stderr, "Stack Overflow\n");
                    ERROR_CODE = ERR_STACK_OVERFLOW;
                    return;
                }
                break;
            case 43:  // SP_TO_FP
                FP = SP;
                break;
            case 44:  // FP_TO_SP
                SP = FP;
                break;
            case 45:  // EXIT_V
                reg_p1 = MEMORY[PC++];
                ERROR_CODE = regs64[reg_p1].int_value;
                return;
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
            case 60:  // INC
                reg_p1 = MEMORY[PC++];
//                printf("%d %lld\n", reg_p1, regs64[reg_p1].int_value);
                regs64[reg_p1].int_value++;
                break;
            case 61:  // DEC
                reg_p1 = MEMORY[PC++];
                regs64[reg_p1].int_value--;
                break;
            case 62:  // INC_F
                reg_p1 = MEMORY[PC++];
                regs64[reg_p1].double_value++;
                break;
            case 63:  // DEC_F
                reg_p1 = MEMORY[PC++];
                regs64[reg_p1].double_value--;
                break;
            default:
                fprintf(stderr, "Unknown instruction %d at byte pos %lld\n", instruction, PC);
                ERROR_CODE = ERR_INSTRUCTION;
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

//void test() {
//    int_fast64_t i = 94;
//    unsigned char *arr = malloc(12);
//    int_to_bytes(arr + 1, i);
//    printf("%lld\n", bytes_to_int(arr + 1));
//
//    float c = (int) 6.6;
//}

int run(int argc, char **argv) {
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
    char **vm_argv = malloc(sizeof(char **) * vm_argc);
    for (int i = vm_args_begin; i < argc; i++) {
        vm_argv[i - vm_args_begin] = argv[i];
    }

    int read;

    unsigned char *codes = read_file(file_name, &read);

    if (vm_load(codes, read)) exit(ERR_VM_OPT);
    vm_set_args(vm_argc, vm_argv);
    vm_run();

//    print_link(AVAILABLE2);

    int_fast64_t main_rtn_ptr = 1;

    if (ERROR_CODE != 0) int_to_bytes(MEMORY + main_rtn_ptr, ERROR_CODE);

    if (p_memory) print_memory();
    if (p_exit) printf("Process finished with exit code %lld\n", bytes_to_int(MEMORY + main_rtn_ptr));

    vm_shutdown();
    free(vm_argv);

    return 0;
}

void test() {
    AVAILABLE2 = build_ava_link(HEAP_START, MEMORY_SIZE);
    AVAILABLE2->next->next->next = AVAILABLE2->next->next->next->next->next;
    print_link(AVAILABLE2);
    int_fast64_t ava = find_ava_link(3);
    printf("%lld\n", ava);
    print_link(AVAILABLE2);
    _free_link(ava, 3);
    print_link(AVAILABLE2);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: tpl.exe [VM_FLAGS] FILE [PROGRAM_FLAGS]");
        exit(1);
    }

//    test();

    return run(argc, argv);
}
