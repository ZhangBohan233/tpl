import sys
import math
import bin.spl_types as typ
import bin.tpl_compiler as cmp  # used in eval
from bin.tpa_compiler import Link, InstructionSet, TpaParser

# Optimization level works:
MERGE_VARIABLE = 2
SUBSTITUTE_OPERATORS = 3
DELETE_EMPTY = 2

# BINARY_OP = {
#     "ADD", "SUB", "MUL", "DIV", "MOD",
#     "ADD_F", "SUB_F", "MUL_F", "DIV_F", "MOD_F",
#     "AND", "OR", "EQ", "NE", "EQ_F", "NE_F",
#     "LSHIFT", "RSHIFT_L", "RSHIFT_A", "B_AND", "B_OR", "B_XOR"
# }

BINARY_OP_SUBSTITUTE = {
    "MUL", "DIV", "MOD",
}


def _in_modify_range(begin_sp, ptr):
    return begin_sp < ptr < cmp.STACK_SIZE


def is_2_power(n):
    return (n & n - 1) == 0 and n != 0


class Optimizer:
    def __init__(self, tpa_psr: TpaParser):
        self.parser = tpa_psr

    def change_functions_len(self, change_value: int):
        self.parser.ori_function_length += change_value

    def optimize(self, level: int):
        # if level >= DELETE_EMPTY:
        #     self.delete_empty()
        if level >= SUBSTITUTE_OPERATORS:
            self.substitute_operators()
        # if level >= MERGE_VARIABLE:
        #     self.merge_variables()

    def substitute_operators(self):
        for i in range(len(self.parser.instructions)):
            line: InstructionSet = self.parser.instructions[i]
            if line.lines[0][0][0] in BINARY_OP_SUBSTITUTE and \
                    self.parser.instructions[i - 1].lines[0][0] == ("LOAD", "ins"):
                rtk: InstructionSet = self.parser.instructions[i - 1]
                right_operand = rtk.lines[0][2]
                if right_operand[1] == "$" and self.parser.is_lit_addr(right_operand[0]):
                    rb = self.parser.get_literal(right_operand[0], 8)
                    rv = typ.bytes_to_int(rb)
                    if is_2_power(rv):
                        shift = int(math.log2(rv))
                        rtk.lines[0][0] = ("LOAD_I", "ins")
                        if line.lines[0][0][0] == "MOD":
                            and_er = 0
                            for bit in range(shift):
                                and_er <<= 1
                                and_er |= 1
                            rtk.lines[0][2] = (and_er, "num")
                            line.lines[0][0] = ("B_AND", "ins")
                        else:
                            rtk.lines[0][2] = (shift, "num")
                            if line.lines[0][0][0] == "MUL":
                                line.lines[0][0] = ("LSHIFT", "ins")
                            else:  # div
                                line.lines[0][0] = ("RSHIFT_A", "ins")

    def delete_one(self, i):
        tk = self.parser.instructions[i]
        if len(tk.pointed_by) > 0:
            next_ = self.parser.instructions[i + 1]
            for src in tk.pointed_by:
                src: Link
                src.link = next_
            next_.pointed_by = tk.pointed_by
            tk.pointed_by = set()
        self.length_change(i, tk, -tk.byte_len())

    def delete_empty(self):
        new_lst = []
        tk_count = len(self.parser.instructions)
        i = 0

        while i < tk_count:
            tk: InstructionSet = self.parser.instructions[i]
            if isinstance(tk, Push):
                if tk.get_count() == 0:
                    self.delete_one(i)
                    i += 1
                    continue
            elif isinstance(tk, Link):
                if tk.get_label() == 0:
                    self.delete_one(i)
                    i += 1
                    continue

            new_lst.append(tk)
            i += 1
        self.parser.instructions = new_lst

        # print(new_lst[26])

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
                        self.change_functions_len(-34)
                        self.check_jumps_before_mod(i, push.byte_index, -34)
                        self.check_jumps_after_mod(i, push.byte_index, -34)
                        self.modify_byte_indices(i, -34)
                        continue

            new_lst.append(line)
            i += 1

        self.parser.tokens = new_lst
        # print(self.parser.tokens)

    def check_in_sequence(self, i: int, seq: list) -> bool:
        if i < len(self.parser.tokens) - len(seq):
            for j in range(len(seq)):
                if self.parser.tokens[i + j][0] != seq[j]:
                    return False
            return True
        else:
            return False

    def length_change(self, ins_index, ins: InstructionSet, length_change):
        self.change_functions_len(length_change)
        # self.check_jumps_before_mod(line_index, byte_index, length_change)
        # self.check_jumps_after_mod(line_index, byte_index, length_change)
        # self.modify_byte_indices(line_index, length_change)

    def check_less_push(self, index, modified_sp, less_push):
        while index < len(self.parser.tokens):
            line = self.parser.tokens[index]
            if line[0] == "STOP":
                break
            _modify_ptr(line, modified_sp, less_push)
            index += 1

    # def _modify_jump(self, line_index: int, modifying_byte_index, length_change):
    #     line = self.parser.tokens[line_index]
    #     byte_index = line.byte_index
    #     if line[0] == "GOTO":
    #         load_i = self.parser.tokens[line_index - 1]
    #         assert load_i[0] == "LOAD_I"
    #         skip_len = int(load_i[2])
    #         orig_target = byte_index + skip_len + 12  # len of
    #         if byte_index < modifying_byte_index < orig_target:  # go forward
    #             load_i[2] = skip_len + length_change
    #         elif byte_index > modifying_byte_index > orig_target:  # go backward
    #             load_i[2] = skip_len - length_change
    #     elif line[0] == "IF_ZERO_GOTO":
    #         load_i = self.parser.tokens[line_index - 2]
    #         assert load_i[0] == "LOAD_I"
    #         skip_len = int(load_i[2])
    #         orig_target = byte_index + skip_len + 23  # len of if_zero_goto set
    #         if byte_index < modifying_byte_index < orig_target:  # go forward
    #             load_i[2] = skip_len + length_change
    #         elif byte_index > modifying_byte_index > orig_target:  # go backward
    #             load_i[2] = skip_len - length_change
    #
    # def check_jumps_before_mod(self, line_index, byte_index, length_change):
    #     i = line_index - 1
    #     while i >= self.parser.ins_begins:
    #         line = self.parser.tokens[i]
    #         if line[0] == "STOP":
    #             break
    #         self._modify_jump(i, byte_index, length_change)
    #         i -= 1
    #
    # def check_jumps_after_mod(self, line_index, byte_index, length_change):
    #     i = line_index + 1
    #     while i < len(self.parser.tokens):
    #         line = self.parser.tokens[i]
    #         if line[0] == "STOP":
    #             break
    #         self._modify_jump(i, byte_index, length_change)
    #         i += 1

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
