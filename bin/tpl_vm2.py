import bin.spl_types as typ
import time

INT_LEN = 8
FLOAT_LEN = 8
PTR_LEN = 8
BOOLEAN_LEN = 1
CHAR_LEN = 1
VOID_LEN = 0


class VMException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


class VirtualMachine:
    def __init__(self):
        self.memory_size = 4096
        self.stack_begin = 1
        self.literal_begin = 1024
        self.global_begin = 1024
        self.code_begin = 1024
        self.heap_begin = 1024

        self.pc = 1024  # program counter
        self.sp = 1
        # self.ret = 1

        self.exit_code = 0

        self.memory = bytearray(self.memory_size)

        self.call_stack = []
        self.pc_stack = []

        self.op_table = {
            2: self.exit_func,
            3: self.assign,
            4: self.call,
            5: self.return_,
            6: self.goto,
            7: self.push_stack,
            10: self.add_i,
            12: self.sub_i,
            16: self.eq_i,
            17: self.gt_i,
            18: self.lt_i,
            30: self.if_zero_goto,
            31: self.native_call
        }

        self.native_functions = {
            1: self.native_clock
        }

    def load_code(self, codes: bytes):
        literal_len = typ.bytes_to_int(codes[:INT_LEN])
        global_len = typ.bytes_to_int(codes[INT_LEN: INT_LEN * 2])
        self.global_begin += literal_len
        self.code_begin = self.global_begin + global_len
        self.pc = self.code_begin
        copy_len = len(codes) - INT_LEN * 2
        self.heap_begin += copy_len
        self.memory[self.literal_begin: self.heap_begin] = codes[INT_LEN * 2:]

    def run(self):
        # self.print_memory()
        while self.pc < self.heap_begin:
            instruction = self.memory[self.pc]
            self.pc += 1
            # print(instruction)
            if instruction in self.op_table:
                op = self.op_table[instruction]
                op()
            else:
                print("Unknown instruction {}".format(instruction))
                return
        self.print_memory()
        print("Process finished with exit code {}".format(typ.bytes_to_int(self.memory[1:9])))

    def push_stack(self):
        push_num = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        self.pc += INT_LEN
        self.sp += push_num
        # print("push to", self.sp)

    def read_2_ints(self) -> (int, int):
        i1 = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        i2 = typ.bytes_to_int(self.get(self.pc + INT_LEN, INT_LEN))
        self.pc += INT_LEN * 2
        return i1, i2

    def read_3_ints(self) -> (int, int, int):
        i1 = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        i2 = typ.bytes_to_int(self.get(self.pc + INT_LEN, INT_LEN))
        i3 = typ.bytes_to_int(self.get(self.pc + INT_LEN * 2, INT_LEN))
        self.pc += INT_LEN * 3
        return i1, i2, i3

    def read_4_ints(self) -> (int, int, int, int):
        i1, i2, i3 = self.read_3_ints()
        i4 = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        self.pc += INT_LEN
        return i1, i2, i3, i4

    def read_3_real_ptr(self):
        i1, i2, i3 = self.read_3_ints()
        return self.generate_true_ptr(i1), self.generate_true_ptr(i2), self.generate_true_ptr(i3)

    def assign(self):
        tar, src, length = self.read_3_ints()
        # self.pc += INT_LEN * 3
        real_tar = self.generate_true_ptr(tar)
        real_src = self.generate_true_ptr(src)
        self.mem_copy(real_src, real_tar, length)

    def call(self):
        func_ptr, r_len, arg_count = self.read_3_ints()
        pc_b = self.pc
        self.pc += arg_count * (PTR_LEN + INT_LEN)  # arg ptr, arg length
        # print("call", func_ptr, r_len, arg_count)

        # self.r_ptr_stack.append(self.generate_true_ptr(r_ptr))

        sp_b = self.sp

        for i in range(arg_count):
            arg_ptr = typ.bytes_to_int(self.get(pc_b, PTR_LEN))
            pc_b += PTR_LEN
            arg_len = typ.bytes_to_int(self.get(pc_b, INT_LEN))
            pc_b += INT_LEN
            real_arg_ptr = self.generate_true_ptr(arg_ptr)
            # print("arg", self.get(real_arg_ptr, arg_len))
            self.mem_copy(real_arg_ptr, self.sp, arg_len)
            self.sp += arg_len

        self.pc_stack.append(self.pc)
        self.call_stack.append(sp_b)

        self.pc = func_ptr

    def native_call(self):
        func_ptr, r_len, r_ptr, arg_count = self.read_4_ints()
        func_code = typ.bytes_to_int(self.get(func_ptr, INT_LEN))
        # print("nat call", func_code)
        real_r_ptr = self.generate_true_ptr(r_ptr)
        pc_b = self.pc
        self.pc += arg_count * (PTR_LEN + INT_LEN)  # arg ptr, arg length

        args = []
        for i in range(arg_count):
            arg_ptr = typ.bytes_to_int(self.get(pc_b, PTR_LEN))
            pc_b += PTR_LEN
            arg_len = typ.bytes_to_int(self.get(pc_b, INT_LEN))
            pc_b += INT_LEN
            true_arg_ptr = self.generate_true_ptr(arg_ptr)
            args.append((true_arg_ptr, arg_len))

        func = self.native_functions[func_code]
        self.call_native(func, args, real_r_ptr, r_len)

    def return_(self):
        v_ptr = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        rtn_len = typ.bytes_to_int(self.get(self.pc + INT_LEN, INT_LEN))
        real_v_ptr = self.generate_true_ptr(v_ptr)

        to = self.call_stack[-1] - rtn_len
        self.mem_copy(real_v_ptr, to, rtn_len)

        self.exit_func()

    def generate_true_ptr(self, i):
        if i < self.literal_begin and len(self.call_stack) > 0:
            return i + self.call_stack[-1]
        else:
            return i

    def get(self, pos, length):
        self._check_range(pos)
        return self.memory[pos:pos + length]

    def set(self, pos: int, byt: bytes):
        self._check_range(pos)
        self.memory[pos:pos + len(byt)] = byt

    def _check_range(self, i):
        if i < 0 or i > self.memory_size:
            raise VMException("Unreached memory address {}".format(i))

    def add_i(self):
        real_res, real_lp, real_rp = self.read_3_real_ptr()
        lv = self.get(real_lp, INT_LEN)
        rv = self.get(real_rp, INT_LEN)
        res_v = typ.int_add_int(lv, rv)
        self.set(real_res, res_v)

    def sub_i(self):
        real_res, real_lp, real_rp = self.read_3_real_ptr()
        lv = self.get(real_lp, INT_LEN)
        rv = self.get(real_rp, INT_LEN)
        res_v = typ.int_sub_int(lv, rv)
        self.set(real_res, res_v)

    # def enter_func(self):
    #     # print("enter", self.sp)
    #     self.call_stack.append(self.sp)
    #     self.pc_stack.append(self.pc)

    def exit_func(self):
        self.sp = self.call_stack.pop()
        self.pc = self.pc_stack.pop()
        # print("exit", self.sp)

    def eq_i(self):
        real_res, res_v = self.int_cmp()

        b = 1 if res_v == 0 else 0
        self.set(real_res, bytes((b,)))

    def lt_i(self):
        real_res, res_v = self.int_cmp()

        b = 1 if res_v < 0 else 0
        self.set(real_res, bytes((b,)))

    def gt_i(self):
        real_res, res_v = self.int_cmp()

        b = 1 if res_v > 0 else 0
        self.set(real_res, bytes((b,)))

    def int_cmp(self) -> (int, int):
        """
        Compares two int and return the (ptr to store result, comparison result)
        """
        res, lp, rp = self.read_3_ints()
        real_res = self.generate_true_ptr(res)
        real_lp = self.generate_true_ptr(lp)
        real_rp = self.generate_true_ptr(rp)
        lv = self.get(real_lp, INT_LEN)
        rv = self.get(real_rp, INT_LEN)
        res_v = typ.int_cmp_int(lv, rv)
        return real_res, res_v

    def goto(self):
        skip_count = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        self.pc += INT_LEN
        self.pc += skip_count

    def if_zero_goto(self):
        skip_len = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        cond_ptr = typ.bytes_to_int(self.get(self.pc + INT_LEN, INT_LEN))
        real_cond_ptr = self.generate_true_ptr(cond_ptr)
        self.pc += INT_LEN * 2
        b = self.memory[real_cond_ptr]
        if b == 0:
            self.pc += skip_len

    def mem_copy(self, from_: int, to: int, length: int):
        self.set(to, self.get(from_, length))

    def native_clock(self):
        t = time.time()
        t_int = int(t * 1000)
        return typ.int_to_bytes(t_int)

    def call_native(self, ftn, args, r_ptr, r_len):
        res = ftn(*args)
        assert len(res) == r_len
        if r_len > 0:
            self.set(r_ptr, res)

    def print_memory(self):
        print("STACK: ", list(self.memory[:self.literal_begin]))
        print("LITERAL: ", self.literal_begin, list(self.memory[self.literal_begin: self.global_begin]))
        print("GLOBAL: ", self.global_begin, list(self.memory[self.global_begin:self.code_begin]))
        print("CODES: ", self.code_begin, list(self.memory[self.code_begin:self.heap_begin]))
        print("HEAP: ", list(self.memory[self.heap_begin:]))
