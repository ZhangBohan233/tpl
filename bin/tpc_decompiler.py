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

        self.in_func = False

    def decompile(self, out_stream):
        length = len(self.codes)
        out_stream.write("LITERALS:\n")
        for i in range(self.global_begin):
            out_stream.write(str(self.codes[i]))
        out_stream.write("\n")

        out_stream.write("NATIVE FUNCTIONS: {}\n".format(cpl.NATIVE_FUNCTION_COUNT))
        self.pc += cpl.NATIVE_FUNCTION_COUNT * INT_LEN
        self.in_func = True

        out_stream.write("\nFUNCTIONS: \n")

        while self.pc < self.code_begin:  # function codes
            out_stream.write("#{} ".format(self.pc))
            self.one_loop(out_stream)

        out_stream.write("\nMAIN: \n")

        while self.pc < length:  # main codes
            out_stream.write("#{} ".format(self.pc))
            self.one_loop(out_stream)

    def one_loop(self, out_stream):
        instruction = self.codes[self.pc]
        self.pc += 1
        if instruction == cpl.STOP:
            out_stream.write("STOP\n\n")
        elif instruction == cpl.ASSIGN:
            out_stream.write("ASSIGN          {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.CALL:
            i1, i2, i3 = self.read_3_ints()
            out_stream.write("CALL            {}  {}  {}\n".format(i1, i2, i3))
            out_stream.write("    ARGS:\n")
            for i in range(i3):
                arg_ptr, arg_len = self.read_2_ints()
                out_stream.write("        {}  {}\n".format(arg_ptr, arg_len))
        elif instruction == cpl.RETURN:
            out_stream.write("RETURN          {}  {}\n".format(*self.read_2_ints()))
        elif instruction == cpl.GOTO:
            out_stream.write("GOTO            {}\n".format(self.read_1_int()))
        elif instruction == cpl.PUSH:
            out_stream.write("PUSH            {}\n".format(self.read_1_int()))
        elif instruction == cpl.ASSIGN_I:
            out_stream.write("ASSIGN_I        {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.ADD_I:
            out_stream.write("ADD_I           {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.SUB_I:
            out_stream.write("SUB_I           {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.MUL_I:
            out_stream.write("MUL_I           {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.DIV_I:
            out_stream.write("DIV_I           {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.MOD_I:
            out_stream.write("MOD_I           {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.EQ_I:
            out_stream.write("EQ_I            {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.GT_I:
            out_stream.write("GT_I            {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.LT_I:
            out_stream.write("LT_I            {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.AND:
            out_stream.write("AND_I           {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.OR:
            out_stream.write("OR_I            {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.IF_ZERO_GOTO:
            out_stream.write("IF_ZERO_GOTO    {}  {}\n".format(*self.read_2_ints()))
        elif instruction == cpl.CALL_NAT:
            i1, i2, i3, i4 = self.read_4_ints()
            out_stream.write("CALL_NAT        {}  {}  {}  {}\n".format(i1, i2, i3, i4))
            out_stream.write("    ARGS:\n")
            for i in range(i4):
                arg_ptr, arg_len = self.read_2_ints()
                out_stream.write("        {}  {}\n".format(arg_ptr, arg_len))
        elif instruction == cpl.UNPACK_ADDR:
            out_stream.write("UNPACK_ADDR     {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.PTR_ASSIGN:
            out_stream.write("PTR_ASSIGN      {}  {}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.STORE_SP:
            out_stream.write("STORE_SP\n")
        elif instruction == cpl.RES_SP:
            out_stream.write("RES_SP\n")
        else:
            print("Unknown instruction: {}".format(instruction))

    def read_4_ints(self) -> (int, int, int, int):
        i1 = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        i2 = typ.bytes_to_int(self.get(self.pc + INT_LEN, INT_LEN))
        i3 = typ.bytes_to_int(self.get(self.pc + INT_LEN * 2, INT_LEN))
        i4 = typ.bytes_to_int(self.get(self.pc + INT_LEN * 3, INT_LEN))
        self.pc += INT_LEN * 4
        return i1, i2, i3, i4

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

    def read_1_int(self) -> int:
        i1 = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        self.pc += INT_LEN
        return i1

    def get(self, index, length):
        return self.codes[index: index + length]
