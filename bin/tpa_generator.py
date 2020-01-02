import bin.spl_types as typ
import bin.tpl_compiler as cpl

INT_LEN = 8
FLOAT_LEN = 8
PTR_LEN = 8
BOOLEAN_LEN = 1
CHAR_LEN = 1
VOID_LEN = 0


class TPAssemblyCompiler:
    def __init__(self, codes: bytes):

        self.codes = codes[INT_LEN * 3:]

        self.stack_size, self.literal_len, self.global_len = \
            typ.bytes_to_int(codes[:INT_LEN]), \
            typ.bytes_to_int(codes[INT_LEN:INT_LEN * 2]), \
            typ.bytes_to_int(codes[INT_LEN * 2:INT_LEN * 3])
        self.global_begin = self.literal_len
        self.code_begin = self.global_begin + self.global_len
        self.pc = self.global_begin

        self.func_begin_pc = 0

    def compile(self, out_stream):
        length = len(self.codes)

        out_stream.write("//STACK SIZE\n")
        out_stream.write(str(self.stack_size))
        out_stream.write("\n//LITERAL LENGTH:\n")
        out_stream.write(str(self.literal_len))
        out_stream.write("\n//GLOBAL LENGTH:\n")
        out_stream.write(str(self.global_len))
        out_stream.write("\n//LITERALS:\n")
        for i in range(self.global_begin):
            out_stream.write(str(self.codes[i]) + " ")
        out_stream.write("\n")

        # out_stream.write("NATIVE FUNCTIONS: {}\n".format(cpl.NATIVE_FUNCTION_COUNT))
        # self.pc += cpl.NATIVE_FUNCTION_COUNT * INT_LEN
        # self.in_func = True

        func_count = self.read_1_int()

        out_stream.write("//FUNCTIONS COUNT:\n")
        out_stream.write(str(func_count))

        out_stream.write("\n//FUNCTION POINTERS:\n")
        for i in range(func_count):
            out_stream.write(str(self.read_1_int()) + "\n")

        out_stream.write("//NATIVE FUNCTIONS COUNT:\n{}\n".format(cpl.NATIVE_FUNCTION_COUNT))
        self.pc += cpl.NATIVE_FUNCTION_COUNT * INT_LEN

        out_stream.write("\n//FUNCTIONS: \n")
        self.func_begin_pc = self.pc
        while self.pc < self.code_begin:  # function codes
            out_stream.write("#{} ".format(self.pc - self.func_begin_pc))
            self.one_loop(out_stream)

        out_stream.write("\n//MAIN: \n")

        while self.pc < length:  # main codes
            # out_stream.write("#{} ".format(self.pc))
            self.one_loop(out_stream)

    def one_loop(self, out_stream):
        instruction = self.codes[self.pc]
        self.pc += 1
        if instruction == cpl.STOP:
            out_stream.write("STOP\n\n")
            self.func_begin_pc = self.pc
        elif instruction == cpl.ASSIGN:
            out_stream.write("ASSIGN          ${}  ${}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.CALL:
            i1, i2, i3 = self.read_3_ints()
            out_stream.write("CALL            ${}  {}  {}\n".format(i1, i2, i3))
            out_stream.write("//ARGS:\n")
            for i in range(i3):
                arg_ptr, arg_len = self.read_2_ints()
                out_stream.write("@        ${}  {}\n".format(arg_ptr, arg_len))
        elif instruction == cpl.RETURN:
            out_stream.write("RETURN          ${}  {}\n".format(*self.read_2_ints()))
        elif instruction == cpl.GOTO:
            out_stream.write("GOTO            {}\n".format(self.read_1_int()))
        elif instruction == cpl.PUSH:
            out_stream.write("PUSH            {}\n".format(self.read_1_int()))
        elif instruction == cpl.ASSIGN_I:
            out_stream.write("ASSIGN_I        ${}  {}\n".format(*self.read_2_ints()))
        elif instruction == cpl.ASSIGN_B:
            out_stream.write("ASSIGN_B        ${}  {}\n".format(*self.read_2_ints()))
        elif instruction == cpl.ADD:
            out_stream.write("ADD             ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.CAST_INT:
            out_stream.write("CAST_INT        ${}  ${}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.SUB:
            out_stream.write("SUB             ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.MUL:
            out_stream.write("MUL             ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.DIV:
            out_stream.write("DIV             ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.MOD:
            out_stream.write("MOD             ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.EQ:
            out_stream.write("EQ              ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.GT:
            out_stream.write("GT              ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.LT:
            out_stream.write("LT              ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.AND:
            out_stream.write("AND             ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.OR:
            out_stream.write("OR              ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.NOT:
            out_stream.write("NOT             ${}  ${}\n".format(*self.read_2_ints()))
        elif instruction == cpl.NE:
            out_stream.write("NE              ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.NEG:
            out_stream.write("NEG             ${}  ${}\n".format(*self.read_2_ints()))
        elif instruction == cpl.NEG_F:
            out_stream.write("NEG_F           ${}  ${}\n".format(*self.read_2_ints()))
        elif instruction == cpl.IF_ZERO_GOTO:
            out_stream.write("IF_ZERO_GOTO    {}  ${}\n".format(*self.read_2_ints()))
        elif instruction == cpl.CALL_NAT:
            i1, i2, i3, i4 = self.read_4_ints()
            out_stream.write("CALL_NAT        ${}  {}  ${}  {}\n".format(i1, i2, i3, i4))
            out_stream.write("//ARGS:\n")
            for i in range(i4):
                arg_ptr, arg_len = self.read_2_ints()
                out_stream.write("@        ${}  {}\n".format(arg_ptr, arg_len))
        elif instruction == cpl.STORE_ADDR:
            out_stream.write("STORE_ADDR      ${}  {}\n".format(*self.read_2_ints()))
        elif instruction == cpl.UNPACK_ADDR:
            out_stream.write("UNPACK_ADDR     ${}  ${}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.PTR_ASSIGN:
            out_stream.write("PTR_ASSIGN      ${}  ${}  {}\n".format(*self.read_3_ints()))
        elif instruction == cpl.STORE_SP:
            out_stream.write("STORE_SP\n")
        elif instruction == cpl.RES_SP:
            out_stream.write("RES_SP\n")
        elif instruction == cpl.TO_REL:
            out_stream.write("TO_REL          ${}\n".format(self.read_1_int()))
        elif instruction == cpl.ADD_I:
            out_stream.write("ADD_I           ${}  {}\n".format(*self.read_2_ints()))
        elif instruction == cpl.INT_TO_FLOAT:
            out_stream.write("INT_TO_FLOAT    ${}  ${}\n".format(*self.read_2_ints()))
        elif instruction == cpl.FLOAT_TO_INT:
            out_stream.write("FLOAT_TO_INT    ${}  ${}\n".format(*self.read_2_ints()))
        elif instruction == cpl.SUB_I:
            out_stream.write("SUB_I           ${}  {}\n".format(*self.read_2_ints()))
        elif instruction == cpl.ADD_FI:
            out_stream.write("ADD_FI          ${}  {}\n".format(*self.read_2_ints()))
        elif instruction == cpl.SUB_FI:
            out_stream.write("SUB_FI          ${}  {}\n".format(*self.read_2_ints()))
        elif instruction == cpl.ADD_F:
            out_stream.write("ADD_F           ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.SUB_F:
            out_stream.write("SUB_F           ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.MUL_F:
            out_stream.write("MUL_F           ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.DIV_F:
            out_stream.write("DIV_F           ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.MOD_F:
            out_stream.write("MOD_F           ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.EQ_F:
            out_stream.write("EQ_F            ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.GT_F:
            out_stream.write("GT_F            ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.LT_F:
            out_stream.write("LT_F            ${}  ${}  ${}\n".format(*self.read_3_ints()))
        elif instruction == cpl.NE_F:
            out_stream.write("NE_F            ${}  ${}  ${}\n".format(*self.read_3_ints()))
        else:
            print("Unknown instruction: {}".format(instruction))
            raise Exception

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
