import bin.spl_types as typ
import bin.tpl_compiler as cpl

INT_LEN = 8
FLOAT_LEN = 8
PTR_LEN = 8
BOOLEAN_LEN = 1
CHAR_LEN = 1
VOID_LEN = 0


class Decompiler:
    def __init__(self, codes: bytes):

        self.codes = codes[INT_LEN * 2:]

        literal_len = typ.bytes_to_int(codes[:INT_LEN])
        global_len = typ.bytes_to_int(codes[INT_LEN: INT_LEN * 2])
        self.global_begin = literal_len
        self.code_begin = self.global_begin + global_len
        self.pc = self.global_begin

    def decompile(self, out_stream):
        length = len(self.codes)
        out_stream.write("LITERALS:\n")
        for i in range(self.global_begin):
            out_stream.write(str(self.codes[i]))
        out_stream.write("\n")
        while self.pc < length:
            instruction = self.codes[self.pc]
            self.pc += 1
            if instruction == cpl.STOP:
                out_stream.write("STOP\n")
            elif instruction == cpl.ASSIGN:
                out_stream.write("ASSIGN     {} {} {}\n".format(*self.read_3_ints()))
            elif instruction == cpl.CALL:
                out_stream.write("CALL       {} {} {}\n".format(*self.read_3_ints()))
            elif instruction == cpl.RETURN:
                out_stream.write("RETURN     {} {}\n".format(*self.read_2_ints()))

    def read_3_ints(self) -> (int, int, int):
        i1 = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        i2 = typ.bytes_to_int(self.get(self.pc + INT_LEN, INT_LEN))
        i3 = typ.bytes_to_int(self.get(self.pc + INT_LEN * 2, INT_LEN))
        self.pc += INT_LEN * 3
        return i1, i2, i3

    def read_2_ints(self) -> (int, int):
        i1 = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        i2 = typ.bytes_to_int(self.get(self.pc + INT_LEN, INT_LEN))
        self.pc += INT_LEN * 2
        return i1, i2

    def get(self, index, length):
        return self.codes[index: index + length]
