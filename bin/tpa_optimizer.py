import bin.spl_types as typ
import bin.tpl_compiler as cmp  # used in eval


# import bin.tpa_generator as gen


class Line:
    def __init__(self, *args):
        self.tokens = list(args)

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
                    if len(tk) > 0 and tk[0] != "#":
                        line_obj.tokens.append(tk)
                if len(line_obj) == 2 and line_obj[0].isdigit():
                    last_line: Line = self.tokens[-1]
                    last_line.tokens.extend(line_obj.tokens)
                elif len(line_obj) > 0:
                    self.tokens.append(line_obj)

        self.lit_len = int(self.tokens[0][0])
        self.global_len = int(self.tokens[1][0])
        self.func_count = int(self.tokens[3][0])
        self.nat_func_count = int(self.tokens[self.func_count + 4][0])
        self.ins_begins = self.func_count + 5

    def to_byte_code(self) -> bytes:
        out = bytearray()
        out.extend(typ.int_to_bytes(self.lit_len))
        out.extend(typ.int_to_bytes(self.global_len))

        literal = self.tokens[2][0]
        for ch in literal:  # write literal
            out.append(int(ch))

        out.extend(typ.int_to_bytes(self.func_count))

        for i in range(self.func_count):
            fp = int(self.tokens[i + 4][0])  # function
            out.extend(typ.int_to_bytes(fp))

        for i in range(self.nat_func_count):
            out.extend(typ.int_to_bytes(i + 1))  # native functions

        for line in self.tokens[self.func_count + 5:]:  # instructions
            instruction = "cmp." + line[0]
            a = eval(instruction)
            out.append(a)
            for num_str in line[1:]:
                out.extend(typ.int_to_bytes(int(num_str)))
            if line[0] == "ABSENT_8":
                out.extend(bytes(7))
            elif line[0] == "ABSENT_24":
                out.extend(bytes(23))

        return bytes(out)


BINARY_OP_INS = {
    "ADD", "SUB", "MUL", "DIV", "MOD"
}

# NEED_LESS_PUSH = {
#     "ADD": (1, 2, 3),
#     "SUB": (1, 2, 3),
#     "MUL": (1, 2, 3),
#     "DIV": (1, 2, 3),
#     "MOD": (1, 2, 3),
#     "ASSIGN": (1, 2),
#     "RETURN": (1,)
# }
#
#
# NEED_LESS_PUSH_SPECIAL = {"CALL", "CALL_NAT"}
#
#
# def _modify_ptr(line: Line, less_push: int):
#     if line[0] in NEED_LESS_PUSH_SPECIAL:
#         if line[0] == "CALL":
#             for i in range(4, len(line), 2):
#                 ptr = int(line[i])
#                 line[i] = ptr - less_push
#         elif line[0] == "CALL_NAT":
#             for i in range(5, len(line), 2):
#                 ptr = int(line[i])
#                 line[i] = ptr - less_push
#     elif line[0] in NEED_LESS_PUSH:
#         mod_pos = NEED_LESS_PUSH[line[0]]
#         for pos in mod_pos:
#             orig_ptr = int(line[pos])
#             if 0 < orig_ptr < cmp.STACK_SIZE:
#                 line[pos] = orig_ptr - less_push


class Optimizer:
    def __init__(self, tpa_psr: TpaParser):
        self.parser = tpa_psr

    def optimize(self, level: int):
        if level >= 1:
            self.merge_variables()

    def merge_variables(self):
        new_lst = self.parser.tokens[:self.parser.ins_begins]
        tk_count = len(self.parser.tokens)
        i = self.parser.ins_begins
        while i < tk_count:
            line = self.parser.tokens[i]
            if i < tk_count - 4:  # check duplicate assignment: push, op, push assign
                if line[0] == "PUSH" and self.parser.tokens[i + 1][0] in BINARY_OP_INS and \
                        self.parser.tokens[i + 2][0] == "PUSH" and self.parser.tokens[i + 3][0] == "ASSIGN":
                    push1 = line
                    op = self.parser.tokens[i + 1]
                    push2 = self.parser.tokens[i + 2]
                    assign = self.parser.tokens[i + 3]
                    if push1[1] == push2[1] and op[1] == assign[2]:
                        op[1] = assign[1]

                        new_lst.append(push1)
                        new_lst.append(op)
                        new_lst.append(push2)
                        new_lst.append(Line("ABSENT_1"))
                        new_lst.append(Line("ABSENT_24"))
                        i += 4
                        continue

            new_lst.append(line)
            i += 1

        self.parser.tokens = new_lst
        # print(self.parser.tokens)
