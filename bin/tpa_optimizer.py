import sys
import math
import bin.spl_types as typ
import bin.tpl_compiler as cmp  # used in eval


# Optimization level works:
MERGE_VARIABLE = 2
SUBSTITUTE_OPERATORS = 2


class Line:
    def __init__(self, *args):
        self.tokens = list(args)
        self.pointers = set()
        self.registers = set()
        self.byte_index = -1

    def __getitem__(self, item):
        return self.tokens[item]

    def __setitem__(self, key, value):
        self.tokens[key] = value

    def __len__(self):
        return len(self.tokens)

    def __str__(self):
        return "Line" + str(self.tokens)

    def __repr__(self):
        return self.__str__()


class TpaParser:
    def __init__(self, text: str):
        lines = text.split("\n")
        self.tokens: [Line] = []
        for line in lines:
            stripped = line.strip()
            if len(stripped) < 2 or stripped[:2] != "//":
                line_tk = stripped.split(" ")
                line_obj = Line()
                for tk in line_tk:
                    if len(tk) > 0:
                        if tk[0] == "#":
                            line_obj.byte_index = int(tk[1:])
                        elif tk[0] == "$":
                            line_obj.pointers.add(len(line_obj))
                            line_obj.tokens.append(int(tk[1:]))
                        elif tk[0] == "%":
                            line_obj.registers.add(len(line_obj))
                            line_obj.tokens.append(int(tk[1:]))
                        else:
                            line_obj.tokens.append(tk)
                if len(line_obj) > 0:
                    if line_obj[0] == "@":  # is function call
                        last_line: Line = self.tokens[-1]
                        for p in line_obj.pointers:
                            last_line.pointers.add(p + len(last_line) - 1)
                        for r in line_obj.registers:
                            last_line.registers.add(r + len(last_line) - 1)
                        last_line.tokens.extend(line_obj.tokens[1:])
                    else:
                        self.tokens.append(line_obj)

        self.stack_size = 0
        self.lit_len = 0
        self.global_len = 0
        self.function_length = 0
        self.main_takes_arg = 0
        self.func_count = 0
        self.nat_func_count = 0
        self.ins_begins = 0
        self.generate_lengths()

        self.lit_loc = 5

    def generate_lengths(self):
        self.stack_size = int(self.tokens[0][0])
        self.lit_len = int(self.tokens[1][0])
        self.global_len = int(self.tokens[2][0])
        self.function_length = int(self.tokens[3][0])
        self.main_takes_arg = int(self.tokens[4][0])
        self.func_count = int(self.tokens[6][0])
        self.nat_func_count = int(self.tokens[self.func_count + 7][0])
        self.ins_begins = self.func_count + 8

    def to_byte_code(self) -> bytes:
        out = bytearray()
        out.extend(typ.int_to_bytes(self.stack_size))
        out.extend(typ.int_to_bytes(self.lit_len))
        out.extend(typ.int_to_bytes(self.global_len))
        out.extend(typ.int_to_bytes(self.function_length))
        out.append(self.main_takes_arg)

        literal = self.tokens[self.lit_loc]
        for ch in literal:  # write literal
            out.append(int(ch))

        out.extend(typ.int_to_bytes(self.func_count))

        for i in range(self.func_count):
            fp = int(self.tokens[i + 7][0])  # function
            out.extend(typ.int_to_bytes(fp))

        for i in range(self.nat_func_count):
            out.extend(typ.int_to_bytes(i + 1))  # native functions

        func_begin_pc = len(out)

        for line in self.tokens[self.ins_begins:]:  # instructions
            if line.byte_index != -1:
                if line.byte_index != len(out) - func_begin_pc:
                    print("error: recorded byte index: {}, actual byte index: {}"
                          .format(line.byte_index, len(out) - func_begin_pc),
                          file=sys.stderr)
            instruction = "cmp." + line[0]
            a = eval(instruction)
            out.append(a)
            for i in range(1, len(line)):
                num_str = line[i]
                if i in line.registers:
                    out.append(int(num_str))
                else:
                    out.extend(typ.int_to_bytes(int(num_str)))
            # for num_str in line[1:]:
            #     out.extend(typ.int_to_bytes(int(num_str)))
            if line[0] == "STOP":
                func_begin_pc = len(out)

        return bytes(out)

    def get_literal(self, addr: int, length: int) -> bytes:
        lit_tk = self.tokens[self.lit_loc]
        index = addr - self.stack_size
        ba = bytearray()
        for i in range(length):
            ba.append(int(lit_tk[index + i]))
        return bytes(ba)

    def is_lit_addr(self, addr: int) -> bool:
        return self.stack_size <= addr < self.stack_size + self.lit_len


BINARY_OP_SUBSTITUTE = {
    "MUL", "DIV", "MOD",
}

# NEED_LESS_PUSH = {
#     "ADD": (1, 2, 3),
#     "SUB": (1, 2, 3),
#     "MUL": (1, 2, 3),
#     "DIV": (1, 2, 3),
#     "MOD": (1, 2, 3),
#     "LT": (1, 2, 3),
#     "GT": (1, 2, 3),
#     "EQ": (1, 2, 3),
#     "NE": (1, 2, 3),
#     "AND": (1, 2, 3),
#     "OR": (1, 2, 3),
#     "NOT": (1, 2),
#     "ADD_F": (1, 2, 3),
#     "SUB_F": (1, 2, 3),
#     "MUL_F": (1, 2, 3),
#     "DIV_F": (1, 2, 3),
#     "MOD_F": (1, 2, 3),
#     "LT_F": (1, 2, 3),
#     "GT_F": (1, 2, 3),
#     "EQ_F": (1, 2, 3),
#     "NE_F": (1, 2, 3),
#     "ASSIGN": (1, 2),
#     "RETURN": (1,),
#     "INT_TO_FLOAT": (1, 2),
#     "FLOAT_TO_INT": (1, 2),
#     "CAST_INT": (1, 2),
#     "STORE_ADDR": (1, ),
#     "UNPACK_ADDR": (1, 2),
#     "PTR_ASSIGN": (1, 2)
# }
#
#
# NEED_LESS_PUSH_SPECIAL = {"CALL", "CALL_NAT"}


def _in_modify_range(begin_sp, ptr):
    return begin_sp < ptr < cmp.STACK_SIZE


def _modify_ptr(line: Line, begin_sp: int, less_push: int):
    # if line.tokens[0] == "CALL_NAT":
    #     print(line.pointers)
    for i in range(len(line)):
        if i in line.pointers:
            ptr = int(line[i])
            if _in_modify_range(begin_sp, ptr):
                line[i] = ptr - less_push
    # if line[0] in NEED_LESS_PUSH_SPECIAL:
    #     if line[0] == "CALL":
    #         for i in range(4, len(line), 2):
    #             ptr = int(line[i])
    #             if _in_modify_range(begin_sp, ptr):
    #                 line[i] = ptr - less_push
    #     elif line[0] == "CALL_NAT":
    #         r_ptr = int(line[3])
    #         if _in_modify_range(begin_sp, r_ptr):
    #             line[3] = r_ptr - less_push
    #         for i in range(5, len(line), 2):
    #             ptr = int(line[i])
    #             if _in_modify_range(begin_sp, ptr):
    #                 line[i] = ptr - less_push
    # elif line[0] in NEED_LESS_PUSH:
    #     mod_pos = NEED_LESS_PUSH[line[0]]
    #     for pos in mod_pos:
    #         orig_ptr = int(line[pos])
    #         if _in_modify_range(begin_sp, orig_ptr):
    #             line[pos] = orig_ptr - less_push


def _modify_jump(line: Line, modifying_byte_index, length_change):
    byte_index = line.byte_index
    if line[0] == "GOTO":
        skip_len = int(line[1])
        orig_target = byte_index + 9 + skip_len
        if byte_index < modifying_byte_index < orig_target:  # go forward
            line[1] = skip_len + length_change
        elif byte_index > modifying_byte_index > orig_target:  # go backward
            line[1] = skip_len - length_change
    elif line[0] == "IF_ZERO_GOTO":
        skip_len = int(line[1])
        orig_target = byte_index + 17 + skip_len
        if byte_index < modifying_byte_index < orig_target:  # go forward
            line[1] = skip_len + length_change
        elif byte_index > modifying_byte_index > orig_target:  # go backward
            line[1] = skip_len - length_change


def is_2_power(n):
    return (n & n - 1) == 0 and n != 0


class Optimizer:
    def __init__(self, tpa_psr: TpaParser):
        self.parser = tpa_psr

    def change_global_len(self, change_value: int):
        self.parser.tokens[2][0] = int(self.parser.tokens[2][0]) + change_value
        self.parser.generate_lengths()

    def optimize(self, level: int):
        if level >= SUBSTITUTE_OPERATORS:
            self.substitute_operators()
        if level >= MERGE_VARIABLE:
            self.merge_variables()

    def substitute_operators(self):
        tk_count = len(self.parser.tokens)
        i = self.parser.ins_begins

        while i < tk_count:
            line = self.parser.tokens[i]
            if line[0] in BINARY_OP_SUBSTITUTE and self.parser.tokens[i - 1][0] == "LOAD":
                rtk = self.parser.tokens[i - 1]
                right_operand_addr = int(rtk[2])
                if self.parser.is_lit_addr(right_operand_addr):
                    rb = self.parser.get_literal(right_operand_addr, 8)
                    rv = typ.bytes_to_int(rb)
                    shift = int(math.log2(rv))
                    if is_2_power(rv):
                        rtk[0] = "LOAD_I"
                        if line[0] == "MOD":
                            and_er = 0
                            for bit in range(shift):
                                and_er <<= 1
                                and_er |= 1
                            rtk[2] = and_er
                            line[0] = "B_AND"
                        else:
                            rtk[2] = shift
                            rtk.pointers.remove(2)
                            if line[0] == "MUL":
                                line[0] = "LSHIFT"
                            else:  # div
                                line[0] = "RSHIFT_A"
            i += 1

    def merge_variables(self):
        new_lst = self.parser.tokens[:self.parser.ins_begins]
        tk_count = len(self.parser.tokens)
        i = self.parser.ins_begins

        seq = ["LOAD_I", "PUSH", ]

        while i < tk_count:
            line = self.parser.tokens[i]

            if i < tk_count - 3:  # check duplicate assignment: push, op, assign
                if line[0] == "STORE" and self.parser.tokens[i + 1][0] == "PUSH" \
                        and self.parser.tokens[i + 2][0] == "ASSIGN":
                    store = line
                    push = self.parser.tokens[i + 1]
                    assign = self.parser.tokens[i + 2]
                    if store[3] == assign[2]:
                        # op[1] = assign[1]
                        # op.byte_index -= 9  # one less push
                        new_lst.append(store)
                        i += 3
                        self.check_less_push(i, int(store[3]), int(push[1]))
                        self.change_global_len(-34)
                        self.check_jumps_before_mod(i, push.byte_index, -34)
                        self.check_jumps_after_mod(i, push.byte_index, -34)
                        self.modify_byte_indices(i, -34)
                        continue

            new_lst.append(line)
            i += 1

        self.parser.tokens = new_lst
        # print(self.parser.tokens)

    def check_in_sequence(self, i: int, seq: list) -> bool:
        if i < len(self.parser.tokens):
            for j in range(len(seq)):
                if self.parser.tokens[i + j][0] != seq[j]:
                    return False
            return True
        else:
            return False

    # def merge_variables(self):
    #     new_lst = self.parser.tokens[:self.parser.ins_begins]
    #     tk_count = len(self.parser.tokens)
    #     i = self.parser.ins_begins
    #     while i < tk_count:
    #         line = self.parser.tokens[i]
    #         if i < tk_count - 4:  # check duplicate assignment: push, op, push assign
    #             if line[0] == "PUSH" and self.parser.tokens[i + 1][0] in BINARY_OP_INS and \
    #                     self.parser.tokens[i + 2][0] == "PUSH" and self.parser.tokens[i + 3][0] == "ASSIGN":
    #                 push1 = line
    #                 op = self.parser.tokens[i + 1]
    #                 push2 = self.parser.tokens[i + 2]
    #                 assign = self.parser.tokens[i + 3]
    #                 if push1[1] == push2[1] and op[1] == assign[2]:
    #                     # op[1] = int(op[1]) - cmp.PTR_LEN
    #
    #                     new_lst.append(push1)
    #                     new_lst.append(op)
    #                     # new_lst.append(push2)
    #                     # new_lst.append(Line("ABSENT_1"))
    #                     # new_lst.append(Line("ABSENT_24"))
    #                     i += 4
    #                     self.check_less_push(i, int(op[1]), int(push2[1]))
    #                     self.change_global_len(-34)
    #                     self.check_jumps_before_mod(i, push1.byte_index, -34)
    #                     self.check_jumps_after_mod(i, push1.byte_index, -34)
    #                     self.modify_byte_indices(i, -34)
    #                     continue
    #
    #         if i < tk_count - 3:  # check duplicate assignment: push, op, assign
    #             if line[0] == "PUSH" and self.parser.tokens[i + 1][0] in BINARY_OP_INS \
    #                     and self.parser.tokens[i + 2][0] == "ASSIGN":
    #                 push1 = line
    #                 op = self.parser.tokens[i + 1]
    #                 assign = self.parser.tokens[i + 2]
    #                 if op[1] == assign[2]:
    #                     op[1] = assign[1]
    #                     op.byte_index -= 9  # one less push
    #                     new_lst.append(op)
    #                     # new_lst.append(push2)
    #                     # new_lst.append(Line("ABSENT_1"))
    #                     # new_lst.append(Line("ABSENT_24"))
    #                     i += 3
    #                     self.check_less_push(i, int(op[1]), int(push1[1]))
    #                     self.change_global_len(-34)
    #                     self.check_jumps_before_mod(i, push1.byte_index, -34)
    #                     self.check_jumps_after_mod(i, push1.byte_index, -34)
    #                     self.modify_byte_indices(i, -34)
    #                     continue
    #
    #         new_lst.append(line)
    #         i += 1
    #
    #     self.parser.tokens = new_lst
    #     # print(self.parser.tokens)

    def check_less_push(self, index, modified_sp, less_push):
        while index < len(self.parser.tokens):
            line = self.parser.tokens[index]
            if line[0] == "STOP":
                break
            _modify_ptr(line, modified_sp, less_push)
            index += 1

    def check_jumps_before_mod(self, line_index, byte_index, length_change):
        i = line_index - 1
        while i >= self.parser.ins_begins:
            line = self.parser.tokens[i]
            if line[0] == "STOP":
                break
            _modify_jump(line, byte_index, length_change)
            i -= 1

    def check_jumps_after_mod(self, line_index, byte_index, length_change):
        i = line_index + 1
        while i < len(self.parser.tokens):
            line = self.parser.tokens[i]
            if line[0] == "STOP":
                break
            _modify_jump(line, byte_index, length_change)
            i += 1

    def modify_byte_indices(self, begin_line_index, length_change):
        stop = len(self.parser.tokens)
        for i in range(begin_line_index, stop):
            line = self.parser.tokens[i]
            line.byte_index += length_change
            if line[0] == "STOP":
                break

    def tail_call_optimization(self):
        pass
    
    def function_inline(self):
        pass

    def loop_unrolling(self):
        pass
