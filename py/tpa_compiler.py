import py.tpl_types as typ
import py.tpl_compiler as cmp  # used by eval


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


class Label(InstructionSet):
    def __init__(self, *args):
        InstructionSet.__init__(self, *args)

    def get_label(self):
        return self.lines[0][1][0]


class Link(InstructionSet):
    def __init__(self, *args):
        InstructionSet.__init__(self, *args)

    def get_label(self):
        return self.lines[0][2][0]

    def transform(self, real_offset):
        raise NotImplementedError

    # def set_offset(self, offset):
    #     self.lines[0][2] = (offset, "num")


class IfZeroGotoL(Link):
    def __init__(self, *args):
        Link.__init__(self, *args)

    def transform(self, real_offset):
        self.lines[2][0] = ("IF_ZERO_GOTO", "ins")
        self.lines[0][2] = (real_offset, "num")


class GotoL(Link):
    def __init__(self, *args):
        Link.__init__(self, *args)

    def transform(self, real_offset):
        self.lines[1][0] = ("GOTO", "ins")
        self.lines[0][2] = (real_offset, "num")


# class Push(InstructionSet):
#     def __init__(self, *args):
#         InstructionSet.__init__(self, *args)
#
#     def get_count(self):
#         return self.lines[0][2][0]


class TpaParser:
    def __init__(self, text: str):
        lines = text.split("\n")

        tokens: [Line] = []
        self.instructions: [InstructionSet] = []

        self.ins_begins = 9
        self.label_indices = {}

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
        self.ori_function_length = tokens[3][0]  # This includes the LABEL's, so is not accurate
        self.main_takes_arg = tokens[4][0]
        self.literal = tokens[5]
        self.func_count = tokens[6][0]
        self.func_pointers = tokens[7]
        self.nat_func_count = tokens[8][0]

        self.make_instructions(tokens)
        self.calculate_labels()
        # self.linking()

    def make_instructions(self, tokens: list):
        i = self.ins_begins
        tk_len = len(tokens)
        while i < tk_len:
            tk: Line = tokens[i]
            if tk[0] == ("GOTO_L", "ins"):
                load_i: InstructionSet = self.instructions.pop()
                ins_set = GotoL(load_i.lines[0], tk)
                self.instructions.append(ins_set)
            elif tk[0] == ("IF_ZERO_GOTO_L", "ins"):
                load: InstructionSet = self.instructions.pop()
                load_i: InstructionSet = self.instructions.pop()
                ins_set = IfZeroGotoL(load_i.lines[0], load.lines[0], tk)
                self.instructions.append(ins_set)
            # elif tk[0] == ("PUSH", "ins"):
            #     load_i: InstructionSet = self.instructions.pop()
            #     ins_set = Push(load_i.lines[0], tk)
            #     self.instructions.append(ins_set)
            elif tk[0] == ("LABEL", "ins"):
                ins_set = Label(tk)
                self.instructions.append(ins_set)
            else:
                ins_set = InstructionSet(tk)
                self.instructions.append(ins_set)
            i += 1

    def calculate_labels(self):
        byte_len = 0
        for ins_set in self.instructions:
            ins_set: InstructionSet
            if isinstance(ins_set, Label):
                self.label_indices[ins_set.get_label()] = byte_len
            else:
                byte_len += ins_set.byte_len()

    def to_byte_code(self) -> bytes:
        # print(self.label_indices)
        out = bytearray()
        out.extend(typ.int_to_bytes(self.stack_size))
        out.extend(typ.int_to_bytes(self.lit_len))
        out.extend(typ.int_to_bytes(self.global_len))
        out.extend(typ.int_to_bytes(self.ori_function_length - len(self.label_indices) * 9))
        out.append(self.main_takes_arg)

        for ch in self.literal:  # write literal
            out.append(int(ch))

        out.extend(typ.int_to_bytes(self.func_count))

        fp_index = len(out)
        out.extend(bytes(self.func_count * 8))
        # for fp in self.func_pointers:
        #     out.extend(typ.int_to_bytes(fp))

        first_function_pos = self.func_pointers[cmp.NATIVE_FUNCTION_COUNT]

        new_func_pointers: list = self.func_pointers[:cmp.NATIVE_FUNCTION_COUNT + 1]  # the starting pos of the first
        # user function will not change
        nfp_i = cmp.NATIVE_FUNCTION_COUNT

        for i in range(self.nat_func_count):
            out.extend(typ.int_to_bytes(i + 1))  # native functions

        ins_byt_begin = len(out)

        current_func_begin = ins_byt_begin
        len_diff_sum = 0

        for ins in self.instructions:  # instructions
            if isinstance(ins, Link):
                lab = ins.get_label()
                off = ins_byt_begin + self.label_indices[lab] - len(out) - ins.byte_len()
                ins.transform(off)
            if not isinstance(ins, Label):
                out.extend(bytes(ins))
                if ins.lines[0][0] == ("STOP", "ins"):
                    cur_len = len(out) - current_func_begin
                    current_func_begin = len(out)
                    if nfp_i < self.func_count - 1:
                        old_len = self.func_pointers[nfp_i + 1] - self.func_pointers[nfp_i]
                        len_diff = old_len - cur_len
                        new_func_pointers.append(self.func_pointers[nfp_i + 1] - len_diff - len_diff_sum)
                        len_diff_sum += len_diff
                        nfp_i += 1
        for i in range(self.func_count):
            index = fp_index + (i * 8)
            out[index: index + 8] = typ.int_to_bytes(new_func_pointers[i])

        return bytes(out)

    def get_literal(self, addr: int, length: int) -> bytes:
        index = addr - self.stack_size
        ba = bytearray()
        for i in range(length):
            ba.append(int(self.literal[index + i]))
        return bytes(ba)

    def is_lit_addr(self, addr: int) -> bool:
        return self.stack_size <= addr < self.stack_size + self.lit_len
