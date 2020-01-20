import bin.spl_types as typ


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