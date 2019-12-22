import bin.spl_types as typ


INT_LEN = 8
FLOAT_LEN = 8
PTR_LEN = 8
BOOLEAN_LEN = 1
CHAR_LEN = 1
VOID_LEN = 0


class Decompiler:
    def __init__(self, codes: bytes):

        self.stack_begin = 1
        self.literal_begin = 1024
        self.global_begin = 1024
        self.code_begin = 1024
        self.heap_begin = 1024

        literal_len = typ.bytes_to_int(codes[:INT_LEN])
        global_len = typ.bytes_to_int(codes[INT_LEN: INT_LEN * 2])
        self.global_begin += literal_len
        self.code_begin = self.global_begin + global_len
        self.pc = self.code_begin
        copy_len = len(codes) - INT_LEN * 2
        self.heap_begin += copy_len

        self.memory = bytearray(self.heap_begin)

        self.memory[self.literal_begin: self.heap_begin] = codes[INT_LEN * 2:]

    def decompile(self, out_stream):
        while self.pc < self.heap_begin:
            instruction = self.memory[self.pc]
            self.pc += 1
            if instruction == 2:
                out_stream.write("exit\n")
            elif instruction == 3:

                out_stream.write()

    def read_3_ints(self) -> (int, int, int):
        i1 = typ.bytes_to_int(self.get(self.pc, INT_LEN))
        i2 = typ.bytes_to_int(self.get(self.pc + INT_LEN, INT_LEN))
        i3 = typ.bytes_to_int(self.get(self.pc + INT_LEN * 2, INT_LEN))
        self.pc += INT_LEN * 3
        return i1, i2, i3
