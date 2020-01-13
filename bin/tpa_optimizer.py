import sys
import math
import bin.spl_types as typ
import bin.tpl_compiler as cmp  # used in eval

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


class Line:
    def __init__(self):
        self.tokens = []

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


class InstructionLine(Line):
    def __init__(self):
        Line.__init__(self)

    def append(self, value, type_):
        self.tokens.append((value, type_))

    def byte_len(self):
        i = 0
        for tup in self.tokens:
            ty = tup[1]
            if ty == "ins":
                i += 1
            elif ty == "num":
                i += 8
            elif ty == "%":
                i += 1
            elif ty == "&":
                i += 1
            elif ty == "$":
                i += 8
        return i

    def __bytes__(self):
        ba = bytearray()
        for tup in self.tokens:
            ty = tup[1]
            if ty == "ins":
                instruction = "cmp." + tup[0]
                ba.append(eval(instruction))
            elif ty == "num" or ty == "$":
                ba.extend(typ.int_to_bytes(tup[0]))
            elif ty == "%" or ty == "&":
                ba.append(tup[0])
        return bytes(ba)


class InstructionSet:
    def __init__(self, *args):
        self.lines: [InstructionLine] = args

        self.pointed_by: set = set()

    def byte_len(self):
        return sum([line.byte_len() for line in self.lines])

    def __bytes__(self):
        ba = bytearray()
        for line in self.lines:
            ba.extend(bytes(line))
        return bytes(ba)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "InsSet{}".format(self.lines)


class Link(InstructionSet):
    link: InstructionSet

    def __init__(self, *args):
        InstructionSet.__init__(self, *args)

    def get_offset(self):
        return self.lines[0][2][0]

    def set_offset(self, offset):
        self.lines[0][2] = (offset, "num")


class Push(InstructionSet):
    def __init__(self, *args):
        InstructionSet.__init__(self, *args)

    def get_count(self):
        return self.lines[0][2][0]


class TpaParser:
    def __init__(self, text: str):
        lines = text.split("\n")

        tokens: [Line] = []
        self.instructions: [InstructionSet] = []

        self.ins_begins = 9

        for line in lines:
            stripped = line.strip()
            if len(stripped) < 2 or stripped[:2] != "//":
                line_tk = stripped.split(" ")

                if len(tokens) < self.ins_begins:
                    line_obj = Line()
                    for tk in line_tk:
                        if tk[0] == "%":
                            line_obj.tokens.append(int(tk[1]))
                        else:
                            line_obj.tokens.append(int(tk))
                else:
                    line_obj = InstructionLine()
                    for tk in line_tk:
                        if len(tk) > 0:
                            if tk[0] == "#":
                                pass
                                # line_obj.byte_index = int(tk[1:])
                            elif tk[0] == "$":
                                line_obj.append(int(tk[1:]), "$")
                            elif tk[0] == "%":
                                line_obj.append(int(tk[1:]), "%")
                            elif tk.isdigit() or (tk[0] == "-" and tk[1:].isdigit()):
                                line_obj.append(int(tk), "num")
                            else:
                                line_obj.append(tk, "ins")
                if len(line_obj) > 0:
                    tokens.append(line_obj)

        self.stack_size = tokens[0][0]
        self.lit_len = tokens[1][0]
        self.global_len = tokens[2][0]
        self.function_length = tokens[3][0]
        self.main_takes_arg = tokens[4][0]
        self.literal = tokens[5]
        self.func_count = tokens[6][0]
        self.func_pointers = tokens[7]
        self.nat_func_count = tokens[8][0]

        self.make_instructions(tokens)
        self.linking()

    def make_instructions(self, tokens: list):
        i = self.ins_begins
        tk_len = len(tokens)
        while i < tk_len:
            tk: Line = tokens[i]
            if tk[0] == ("GOTO", "ins"):
                load_i: InstructionSet = self.instructions.pop()
                ins_set = Link(load_i.lines[0], tk)
                self.instructions.append(ins_set)
            elif tk[0] == ("IF_ZERO_GOTO", "ins"):
                load: InstructionSet = self.instructions.pop()
                load_i: InstructionSet = self.instructions.pop()
                ins_set = Link(load_i.lines[0], load.lines[0], tk)
                self.instructions.append(ins_set)
            elif tk[0] == ("PUSH", "ins"):
                load_i: InstructionSet = self.instructions.pop()
                ins_set = Push(load_i.lines[0], tk)
                self.instructions.append(ins_set)
            else:
                ins_set = InstructionSet(tk)
                self.instructions.append(ins_set)
            i += 1

    def linking(self):
        tk_len = len(self.instructions)
        cur_byte_len = 0
        for i in range(tk_len):
            tk: InstructionSet = self.instructions[i]
            cur_byte_len += tk.byte_len()
            if isinstance(tk, Link):
                off = tk.get_offset()
                j = i
                if off < 0:
                    while off < 0:
                        off += self.instructions[j].byte_len()
                        j -= 1
                    tar = self.instructions[j + 1]
                else:
                    j = i + 1
                    while off > 0:
                        off -= self.instructions[j].byte_len()
                        j += 1
                    tar = self.instructions[j]
                tk.link = tar
                tar.pointed_by.add(tk)

    def re_link(self):
        tk_len = len(self.instructions)
        byte_len = 0
        for i in range(tk_len):
            tk: InstructionSet = self.instructions[i]
            byte_len += tk.byte_len()
            if isinstance(tk, Link):
                tar = tk.link
                off = 0
                j = i
                if tk.get_offset() < 0:  # front will always be at front
                    while self.instructions[j] is not tar:
                        off -= self.instructions[j].byte_len()
                        j -= 1
                    off -= 1
                else:
                    j += 1
                    while self.instructions[j] is not tar:
                        off += self.instructions[j].byte_len()
                        j += 1

                # print(tk.get_offset(), off)
                tk.set_offset(off)

    def to_byte_code(self) -> bytes:
        out = bytearray()
        out.extend(typ.int_to_bytes(self.stack_size))
        out.extend(typ.int_to_bytes(self.lit_len))
        out.extend(typ.int_to_bytes(self.global_len))
        out.extend(typ.int_to_bytes(self.function_length))
        out.append(self.main_takes_arg)

        for ch in self.literal:  # write literal
            out.append(int(ch))

        out.extend(typ.int_to_bytes(self.func_count))

        for fp in self.func_pointers:
            out.extend(typ.int_to_bytes(fp))

        for i in range(self.nat_func_count):
            out.extend(typ.int_to_bytes(i + 1))  # native functions

        for ins in self.instructions:  # instructions
            out.extend(bytes(ins))
            # if line.byte_index != -1:
            #     if line.byte_index != len(out) - func_begin_pc:
            #         print("error: recorded byte index: {}, actual byte index: {}"
            #               .format(line.byte_index, len(out) - func_begin_pc),
            #               file=sys.stderr)
            # for line in ins.lines:
            # instruction = "cmp." + line[0]
            # a = eval(instruction)
            # out.append(a)
            # for i in range(1, len(line)):
            #     num_str = line[i]
            #     if i in line.registers:
            #         out.append(int(num_str))
            #     else:
            #         out.extend(typ.int_to_bytes(int(num_str)))
            # for num_str in line[1:]:
            #     out.extend(typ.int_to_bytes(int(num_str)))
            # if line[0] == "STOP":
            #     func_begin_pc = len(out)

        return bytes(out)

    def get_literal(self, addr: int, length: int) -> bytes:
        index = addr - self.stack_size
        ba = bytearray()
        for i in range(length):
            ba.append(int(self.literal[index + i]))
        return bytes(ba)

    def is_lit_addr(self, addr: int) -> bool:
        return self.stack_size <= addr < self.stack_size + self.lit_len


def _in_modify_range(begin_sp, ptr):
    return begin_sp < ptr < cmp.STACK_SIZE


def is_2_power(n):
    return (n & n - 1) == 0 and n != 0


class Optimizer:
    def __init__(self, tpa_psr: TpaParser):
        self.parser = tpa_psr

    def change_functions_len(self, change_value: int):
        self.parser.function_length += change_value

    def optimize(self, level: int):
        if level >= DELETE_EMPTY:
            self.delete_empty()
            self.parser.re_link()
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
                    shift = int(math.log2(rv))
                    if is_2_power(rv):
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
                if tk.get_offset() == 0:
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
