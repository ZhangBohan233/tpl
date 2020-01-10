import bin.spl_ast as ast
import bin.spl_environment as en
import bin.spl_types as typ
import bin.spl_lib as lib

STACK_SIZE = 1024

INT_LEN = 8
FLOAT_LEN = 8
PTR_LEN = 8
# BOOLEAN_LEN = 1
CHAR_LEN = 1
VOID_LEN = 0

PUSH = 1
STOP = 2  # STOP                                  | stop current process
ASSIGN = 3  # ASSIGN   TARGET    SOURCE   LENGTH    | copy LENGTH bytes from SOURCE to TARGET
CALL = 4  # CALL
RETURN = 5  # RETURN   VALUE_PTR
GOTO = 6  # JUMP       CODE_PTR
LOAD_A = 7  # LOAD_A                             | loads addr to register
LOAD = 8  # LOAD     %DES_REG   $ADDR                   |
STORE = 9  # STORE   %TEMP   %REG   $DES_ADDR
LOAD_I = 10
ADD = 11  # ADD     %REG1   %REG2
SUB = 12
MUL = 13
DIV = 14
MOD = 15
EQ = 16  # EQ       RES PTR   LEFT_P   RIGHT_P   | set RES PTR to 0 if LEFT_P == RIGHT_P
GT = 17  # GT
LT = 18
AND = 19
OR = 20
NOT = 21
NE = 22
NEG = 23
RSHIFT_A = 24  # | arithmetic left shift.  Copy the sign bit
RSHIFT_L = 25  # | logical left shift.  Fill the sign bit with 0
LSHIFT = 26
B_AND = 27
B_OR = 28
B_XOR = 29

IF_ZERO_GOTO = 30  # IF0  SKIP  SRC_PTR
CALL_NAT = 31
STORE_ADDR = 32
UNPACK_ADDR = 33
# PTR_ASSIGN = 34  # | assign the addr stored in ptr with the value stored in right
STORE_SP = 35
RES_SP = 36
MOVE_REG = 37  # MOVE_REG   %DST  %SRC       | copy between registers
# TO_REL = 37  # | transform absolute addr to
# ADD_I = 38       # | add with real value
CAST_INT = 38  # CAST_INT  RESULT_P  SRC_P              | cast int-like to int
INT_TO_FLOAT = 39
FLOAT_TO_INT = 40
# SUB_I = 41
# ADD_FI = 42
# SUB_FI = 43

ADD_F = 50
SUB_F = 51
MUL_F = 52
DIV_F = 53
MOD_F = 54
EQ_F = 55
GT_F = 56
LT_F = 57
NE_F = 58
NEG_F = 59

LOAD_LEN = 11
STORE_LEN = 11

# Number of native functions, used for generating tpa
NATIVE_FUNCTION_COUNT = 6


# Optimizations starting level
OPTIMIZE_LOOP_INDICATOR = 2
OPTIMIZE_LOOP_REG = 3

INT_RESULT_TABLE_INT = {
    "+": ADD,
    "-": SUB,
    "*": MUL,
    "/": DIV,
    "%": MOD,
    ">>": RSHIFT_A,
    ">>>": RSHIFT_L,
    "<<": LSHIFT,
    "&": B_AND,
    "|": B_OR,
    "^": B_XOR,
    ">": GT,
    "==": EQ,
    "!=": NE,
    "<": LT,
    "&&": AND,
    "||": OR
}

BOOL_RESULT_TABLE = {  # this table only used for getting tal
    ">",
    "==",
    "!=",
    "<",
    "&&",
    "||",
    ">=",
    "<="
}

INT_RESULT_TABLE_INT_FULL = {
    **INT_RESULT_TABLE_INT,
    "+=": ADD,
    "-=": SUB,
    "*=": MUL,
    "/=": DIV,
    "%=": MOD,
    ">>=": RSHIFT_A,
    ">>>=": RSHIFT_L,
    "<<=": LSHIFT,
    "&=": B_AND,
    "|=": B_OR,
    "^=": B_XOR
}

EXTENDED_INT_RESULT_TABLE_INT = {
    **INT_RESULT_TABLE_INT,
    ">=": (GT, EQ),
    "<=": (LT, EQ),
}

OTHER_BOOL_RESULT_UNARY = {
    "!"
}

FLOAT_RESULT_TABLE_FLOAT = {
    "+": ADD_F,
    "-": SUB_F,
    "*": MUL_F,
    "/": DIV_F,
    "%": MOD_F
}

FLOAT_RESULT_TABLE_FLOAT_FULL = {
    **FLOAT_RESULT_TABLE_FLOAT,
    "+=": ADD_F,
    "-=": SUB_F,
    "*=": MUL_F,
    "/=": DIV_F,
    "%=": MOD_F
}

INT_RESULT_TABLE_FLOAT = {
    ">": GT_F,
    "==": EQ_F,
    "!=": NE_F,
    "<": LT_F
}

EXTENDED_INT_RESULT_TABLE_FLOAT = {
    **INT_RESULT_TABLE_FLOAT,
    ">=": (GT_F, EQ_F),
    "<=": (LT_F, EQ_F),
}

WITH_ASSIGN = {
    "+=", "-=", "*=", "/=", "%=", ">>=", ">>>=", "<<=", "|=", "&=", "^="
}


class ByteOutput:
    def __init__(self, manager):
        self.manager: MemoryManager = manager
        self.codes = bytearray()

    def __len__(self):
        return len(self.codes)

    def __bytes__(self):
        return bytes(self.codes)

    def write_one(self, b):
        self.codes.append(b)

    def push_stack(self, value: int):
        reg1 = self.manager.require_regs64(1)[0]

        self.write_one(LOAD_I)
        self.write_one(reg1)
        self.write_int(value)

        self.write_one(PUSH)
        self.write_one(reg1)

        self.manager.append_regs64(reg1)

    def assign(self, tar: int, src: int, length: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD_A)
        self.write_one(reg1)
        self.write_int(tar)

        self.write_one(LOAD_A)
        self.write_one(reg2)
        self.write_int(src)

        self.write_one(LOAD_I)
        self.write_one(reg3)
        self.write_int(length)

        self.write_one(ASSIGN)
        self.write_one(reg1)
        self.write_one(reg2)
        self.write_one(reg3)

        self.manager.append_regs64(reg3, reg2, reg1)

    def assign_reg(self, reg_id, src):
        reg = -reg_id - 1

        self.write_one(LOAD)
        self.write_one(reg)
        self.write_int(src)

    def assign_reg_i(self, reg_id, real_value):
        reg = -reg_id - 1

        self.write_one(LOAD_I)
        self.write_one(reg)
        self.write_int(real_value)

    def store_from_reg(self, des, reg_id):
        temp_reg = self.manager.require_reg64()

        self.write_one(STORE)
        self.write_one(temp_reg)
        self.write_one(-reg_id - 1)
        self.write_int(des)

        self.manager.append_regs64(temp_reg)

    def assign_i(self, des: int, real_value: int):
        reg1, reg2 = self.manager.require_regs64(2)

        self.write_one(LOAD_I)
        self.write_one(reg1)
        self.write_int(real_value)

        self.write_one(STORE)
        self.write_one(reg2)
        self.write_one(reg1)
        self.write_int(des)

        self.manager.append_regs64(reg2, reg1)

    def call_main(self, ftn_ptr: int, args: list):
        reg1, reg2 = self.manager.require_regs64(2)

        spb = self.manager.sp + 8
        i = 0
        for arg in args:
            ptr = spb + i

            self.assign(ptr, arg[0], arg[1])
            self.push_stack(arg[1])

            i += arg[1]

        self.manager.sp = spb

        self.write_one(LOAD_I)
        self.write_one(reg1)  # ftn ptr
        self.write_int(ftn_ptr)

        self.write_one(LOAD_I)
        self.write_one(reg2)  # args length
        self.write_int(i)

        self.write_one(CALL)
        self.write_one(reg1)
        self.write_one(reg2)

        self.manager.append_regs64(reg2, reg1)

    def call(self, is_native: bool, ftn_ptr: int, args: list):
        """

        :param is_native:
        :param ftn_ptr:
        :param args: list of tuple(arg_ptr, arg_len)
        :return:
        """
        reg1, reg2 = self.manager.require_regs64(2)

        spb = self.manager.sp
        i = 0
        for arg in args:
            ptr = self.manager.allocate(arg[1], self)
            # print(ptr)
            # self.push_stack(arg[1])

            if arg[0] < 0:  # register:
                self.store_from_reg(ptr, arg[0])
            else:
                self.assign(ptr, arg[0], arg[1])

            i += arg[1]

        self.manager.sp = spb

        self.write_one(LOAD_I)
        self.write_one(reg1)  # ftn ptr
        self.write_int(ftn_ptr)

        self.write_one(LOAD_I)
        self.write_one(reg2)  # args length
        self.write_int(i)

        if is_native:
            self.write_one(CALL_NAT)
        else:
            self.write_one(CALL)
        self.write_one(reg1)
        self.write_one(reg2)

        self.manager.append_regs64(reg2, reg1)

    def int_to_float(self, des: int, src: int):
        reg1, reg2 = self.manager.require_regs64(2)

        self.write_one(LOAD)
        self.write_one(reg1)
        self.write_int(src)

        self.write_one(INT_TO_FLOAT)
        self.write_one(reg1)

        self.write_one(STORE)
        self.write_one(reg2)
        self.write_one(reg1)
        self.write_int(des)

        self.manager.append_regs64(reg2, reg1)

    def float_to_int(self, des: int, src: int):
        reg1, reg2 = self.manager.require_regs64(2)

        self.write_one(LOAD)
        self.write_one(reg1)
        self.write_int(src)

        self.write_one(FLOAT_TO_INT)
        self.write_one(reg1)

        self.write_one(STORE)
        self.write_one(reg2)
        self.write_one(reg1)
        self.write_int(des)

        self.manager.append_regs64(reg2, reg1)

    def store_addr_to_des(self, des: int, rel_value: int):
        reg1, reg2 = self.manager.require_regs64(2)

        self.write_one(LOAD_A)
        self.write_one(reg1)
        self.write_int(des)

        self.write_one(LOAD_A)
        self.write_one(reg2)
        self.write_int(rel_value)

        self.write_one(STORE_ADDR)
        self.write_one(reg1)
        self.write_one(reg2)

        self.manager.append_regs64(reg2, reg1)

    def unpack_addr(self, des: int, addr_ptr: int, length: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD_A)
        self.write_one(reg1)
        self.write_int(des)

        self.write_one(LOAD)
        self.write_one(reg2)
        self.write_int(addr_ptr)

        self.write_one(LOAD_I)
        self.write_one(reg3)
        self.write_int(length)

        self.write_one(UNPACK_ADDR)
        self.write_one(reg1)
        self.write_one(reg2)
        self.write_one(reg3)

        self.manager.append_regs64(reg3, reg2, reg1)

    def ptr_assign(self, des_ptr: int, right: int, length: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD)
        self.write_one(reg1)
        self.write_int(des_ptr)

        self.write_one(LOAD_A)
        self.write_one(reg2)
        self.write_int(right)

        self.write_one(LOAD_I)
        self.write_one(reg3)
        self.write_int(length)

        self.write_one(UNPACK_ADDR)
        self.write_one(reg1)
        self.write_one(reg2)
        self.write_one(reg3)

        self.manager.append_regs64(reg3, reg2, reg1)

    def cast_to_int(self, tar: int, src: int, src_len: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD_A)
        self.write_one(reg1)
        self.write_int(tar)

        self.write_one(LOAD_A)
        self.write_one(reg2)
        self.write_int(src)

        self.write_one(LOAD_I)
        self.write_one(reg3)
        self.write_int(src_len)

        self.write_one(CAST_INT)
        self.write_one(reg1)
        self.write_one(reg2)
        self.write_one(reg3)

        self.manager.append_regs64(reg3, reg2, reg1)

    def add_binary_op(self, op: int, res: int, left: int, right: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        if left < 0:  # left is reg
            self.write_one(MOVE_REG)
            self.write_one(reg1)
            self.write_one(-left - 1)
        else:
            self.write_one(LOAD)
            self.write_one(reg1)
            self.write_int(left)

        if right < 0:
            self.write_one(MOVE_REG)
            self.write_one(reg2)
            self.write_one(-right - 1)
        else:
            self.write_one(LOAD)
            self.write_one(reg2)
            self.write_int(right)

        self.write_one(op)
        self.write_one(reg1)
        self.write_one(reg2)

        if res < 0:
            self.write_one(MOVE_REG)
            self.write_one(-res - 1)
            self.write_one(reg1)
        else:
            self.write_one(STORE)
            self.write_one(reg3)
            self.write_one(reg1)
            self.write_int(res)

        self.manager.append_regs64(reg3, reg2, reg1)

    def add_unary_op(self, op: int, res: int, value: int):
        reg1, reg2 = self.manager.require_regs64(2)

        if value < 0:  # value is reg
            self.write_one(MOVE_REG)
            self.write_one(reg1)
            self.write_one(-value - 1)
        else:
            self.write_one(LOAD)
            self.write_one(reg1)
            self.write_int(value)

        self.write_one(op)
        self.write_one(reg1)

        if res < 0:
            self.write_one(MOVE_REG)
            self.write_one(-res - 1)
            self.write_one(reg1)
        else:
            self.write_one(STORE)
            self.write_one(reg2)
            self.write_one(reg1)
            self.write_int(res)

        self.manager.append_regs64(reg2, reg1)

    def add_return(self, src, total_len):
        reg1, reg2 = self.manager.require_regs64(2)

        if src < 0:
            raise lib.CompileTimeException("Cannot return a register.")
        else:
            self.write_one(LOAD_A)
            self.write_one(reg1)  # return ptr
            self.write_int(src)

        self.write_one(LOAD_I)
        self.write_one(reg2)  # return length
        self.write_int(total_len)

        self.write_one(RETURN)
        self.write_one(reg1)
        self.write_one(reg2)

        self.manager.append_regs64(reg2, reg1)

    def op_i(self, op_code, operand_addr, adder_value: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD_I)
        self.write_one(reg1)  # right
        self.write_int(adder_value)

        if operand_addr < 0:
            self.write_one(MOVE_REG)
            self.write_one(reg2)
            self.write_one(-operand_addr - 1)
        else:
            self.write_one(LOAD)
            self.write_one(reg2)  # left
            self.write_int(operand_addr)

        self.write_one(op_code)
        self.write_one(reg2)
        self.write_one(reg1)

        if operand_addr < 0:
            self.write_one(MOVE_REG)
            self.write_one(-operand_addr - 1)
            self.write_one(reg2)
        else:
            self.write_one(STORE)
            self.write_one(reg3)
            self.write_one(reg2)
            self.write_int(operand_addr)

        self.manager.append_regs64(reg3, reg2, reg1)

    def if_zero_goto(self, offset: int, cond_ptr: int) -> int:
        """
        Returns the occupied length

        :param offset:
        :param cond_ptr:
        :return:
        """
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD_I)
        self.write_one(reg1)  # reg stores skip len
        self.write_int(offset)

        if cond_ptr < 0:  # cond is register:
            self.write_one(MOVE_REG)
            self.write_one(reg2)
            self.write_one(-cond_ptr - 1)
            length = 16
        else:
            self.write_one(LOAD)
            self.write_one(reg2)  # reg stores cond ptr
            self.write_int(cond_ptr)
            length = 23

        self.write_one(IF_ZERO_GOTO)
        self.write_one(reg1)
        self.write_one(reg2)

        self.manager.append_regs64(reg3, reg2, reg1)

        return length

    def goto(self, offset: int) -> int:
        reg1, = self.manager.require_regs64(1)

        self.write_one(LOAD_I)
        self.write_one(reg1)
        self.write_int(offset)

        self.write_one(GOTO)
        self.write_one(reg1)

        self.manager.append_regs64(reg1)

    def write_int(self, i):
        self.codes.extend(typ.int_to_bytes(i))

    def reserve_space(self, n) -> int:
        i = len(self.codes)
        self.codes.extend(bytes(n))
        return i

    def set_bytes(self, from_: int, b: bytes):
        self.codes[from_: from_ + len(b)] = b

    def get_loop_indicator(self):
        raise lib.CompileTimeException("Break outside loop")

    def get_loop_length(self):
        raise lib.CompileTimeException("Continue outside loop")


class LoopByteOutput(ByteOutput):
    def __init__(self, manager, loop_indicator_pos, cond_len, step_node):
        ByteOutput.__init__(self, manager)

        # self.outer = outer
        self.loop_indicator_pos = loop_indicator_pos
        self.cond_len = cond_len
        self.step_node = step_node

    def get_loop_indicator(self):
        return self.loop_indicator_pos

    def get_loop_length(self):
        return self.step_node, self.cond_len + len(self)


class BlockByteOutput(ByteOutput):
    def __init__(self, manager, outer):
        ByteOutput.__init__(self, manager)

        self.outer: ByteOutput = outer

    def get_loop_indicator(self):
        return self.outer.get_loop_indicator()

    def get_loop_length(self):
        out_res = self.outer.get_loop_length()
        return out_res[0], out_res[1] + len(self) + INT_LEN * 2 + 1


class MemoryManager:
    def __init__(self, literal_bytes):
        self.stack_begin = 1
        self.sp = 1
        self.literal_begins = STACK_SIZE
        self.global_begins = STACK_SIZE + len(literal_bytes)
        self.functions_begin = 0
        self.func_p = 0
        self.gp = self.global_begins

        self.literal: bytearray = literal_bytes
        self.global_bytes = bytearray()
        self.functions_bytes = bytearray(INT_LEN)  # function counts
        self.functions = {}

        self.blocks = []
        self.loop_sp_stack = []

        self.type_sizes = {
            "int": INT_LEN,
            "float": FLOAT_LEN,
            "char": CHAR_LEN,
            "void": VOID_LEN
        }
        self.pointer_length = PTR_LEN

        self.available_regs64 = [7, 6, 5, 4, 3, 2, 1, 0]

    def set_global_length(self, gl):
        self.functions_begin = self.global_begins + gl
        self.func_p = self.functions_begin + INT_LEN  # reserve space for functions count

    def get_global_len(self):
        return self.functions_begin - self.global_begins

    def require_regs64(self, count):
        if count > len(self.available_regs64):
            raise lib.CompileTimeException("Virtual Machine does not have enough registers")
        return [self.available_regs64.pop() for _ in range(count)]

    def require_reg64(self):
        return self.available_regs64.pop()

    def append_regs64(self, *regs):
        for reg in regs:
            self.available_regs64.append(reg)

    def has_enough_regs(self):
        return len(self.available_regs64) > 4

    def get_type_size(self, name):
        if name[0] == "*":  # is a pointer
            return self.pointer_length
        return self.type_sizes[name]

    def add_type(self, name, length):
        self.type_sizes[name] = length

    def push_stack(self):
        self.blocks.append(self.sp)

    def restore_stack(self):
        self.sp = self.blocks.pop()

    def store_sp(self):
        self.loop_sp_stack.append(self.sp)

    def restore_sp(self):
        self.sp = self.loop_sp_stack.pop()

    def allocate(self, length, bo) -> int:
        if len(self.blocks) == 0:  # global
            ptr = self.gp
            self.gp += length
        else:  # in call
            ptr = self.sp - self.blocks[-1]
            self.sp += length
            if bo is not None and length > 0:
                bo.push_stack(length)
        return ptr

    def calculate_lit_ptr(self, lit_num):
        return lit_num + self.literal_begins

    def get_last_call(self):
        return self.blocks[-1]

    def compile_all_functions(self):
        # print(self.functions)
        self.functions_bytes[0:INT_LEN] = typ.int_to_bytes(len(self.functions))
        for ptr in self.functions:
            fb = self.functions[ptr]
            ptr_in_g = ptr - self.functions_begin
            self.functions_bytes[ptr_in_g: ptr_in_g + PTR_LEN] = typ.int_to_bytes(self.func_p)
            self.functions_bytes.extend(fb)
            self.func_p += len(fb)

    def define_func_ptr(self):
        i = self.func_p
        self.functions_bytes.extend(bytes(PTR_LEN))
        self.func_p += PTR_LEN
        return i

    def implement_func(self, func_ptr: int, fn_bytes: bytes):
        self.functions[func_ptr] = fn_bytes


class ParameterPair:
    def __init__(self, name: str, tal: en.Type):
        self.name: str = name
        self.tal = tal

    def __str__(self):
        return "{}".format(self.name)

    def __repr__(self):
        return self.__str__()


class Function:
    def __init__(self, params, r_tal: en.Type, ptr: int):
        self.params: [ParameterPair] = params
        self.r_tal: en.Type = r_tal
        self.ptr = ptr


class NativeFunction:
    def __init__(self, r_tal: en.Type, ptr: int):
        self.r_tal: en.Type = r_tal
        self.ptr = ptr


class CompileTimeFunction:
    def __init__(self, r_tal, func):
        self.r_tal: en.Type = r_tal
        self.func = func


class Struct:
    def __init__(self, name: str):
        self.name = name
        self.vars: {str: (int, en.Type)} = {}  # position, type

    def get_attr_pos(self, attr_name: str) -> int:
        return self.vars[attr_name][0]

    def get_attr_tal(self, attr_name: str) -> en.Type:
        return self.vars[attr_name][1]

    def __str__(self):
        return "Struct {}: {}".format(self.name, self.vars)


class Compiler:
    def __init__(self, literal_bytes: bytearray):
        self.memory = MemoryManager(literal_bytes)

        self.modified_string_poses = set()
        self.optimize_level = 0

        self.node_table = {
            ast.LITERAL: self.compile_literal,
            ast.STRING_LITERAL: self.compile_string_literal,
            ast.DEF_STMT: self.compile_def_stmt,
            ast.NAME_NODE: self.compile_name_node,
            ast.BLOCK_STMT: self.compile_block_stmt,
            ast.FUNCTION_CALL: self.compile_call,
            ast.BINARY_OPERATOR: self.compile_binary_op,
            ast.UNARY_OPERATOR: self.compile_unary_op,
            ast.RETURN_STMT: self.compile_return,
            ast.ASSIGNMENT_NODE: self.compile_assignment_node,
            ast.IF_STMT: self.compile_if,
            ast.FOR_LOOP_STMT: self.compile_for_loop,
            ast.WHILE_STMT: self.compile_while_loop,
            ast.UNDEFINED_NODE: self.compile_undefined,
            ast.INDEXING_NODE: self.compile_getitem,
            ast.BREAK_STMT: self.compile_break,
            ast.CONTINUE_STMT: self.compile_continue,
            ast.NULL_STMT: self.compile_null,
            ast.STRUCT_NODE: self.compile_struct,
            ast.DOT: self.compile_dot,
            ast.QUICK_ASSIGNMENT: self.compile_quick_assignment,
            ast.IN_DECREMENT_OPERATOR: self.compile_in_decrement
        }

    def configs(self, **kwargs):
        if "optimize" in kwargs:
            self.optimize_level = kwargs["optimize"]

    def add_native_functions(self, env: en.GlobalEnvironment):
        p1 = self.memory.define_func_ptr()  # 1: clock
        self.memory.implement_func(p1, typ.int_to_bytes(1))
        env.define_function("clock", NativeFunction(en.Type("int"), p1))

        p2 = self.memory.define_func_ptr()  # 2: malloc
        self.memory.implement_func(p2, typ.int_to_bytes(2))
        env.define_function("malloc", NativeFunction(en.Type("*void"), p2))

        p3 = self.memory.define_func_ptr()  # 3: printf
        self.memory.implement_func(p3, typ.int_to_bytes(3))
        env.define_function("printf", NativeFunction(en.Type("void"), p3))

        p4 = self.memory.define_func_ptr()  # 4: mem_copy
        self.memory.implement_func(p4, typ.int_to_bytes(4))
        env.define_function("mem_copy", NativeFunction(en.Type("void"), p4))

        p5 = self.memory.define_func_ptr()  # 5: free
        env.define_function("free", NativeFunction(en.Type("void"), p5))
        self.memory.implement_func(p5, typ.int_to_bytes(5))

        p6 = self.memory.define_func_ptr()  # 6: stringf
        env.define_function("stringf", NativeFunction(en.Type("int"), p6))
        self.memory.implement_func(p6, typ.int_to_bytes(6))

    def add_compile_time_functions(self, env: en.GlobalEnvironment):
        env.define_function("sizeof", CompileTimeFunction(en.Type("int"), self.function_sizeof))
        env.define_function("char", CompileTimeFunction(en.Type("char"), self.function_char))
        env.define_function("int", CompileTimeFunction(en.Type("int"), self.function_int))
        env.define_function("float", CompileTimeFunction(en.Type("float"), self.function_float))

    def calculate_global_len(self, root: ast.Node, is_child: bool):
        if is_child:
            test_env = en.GlobalEnvironment()
            test_bo = ByteOutput(self.memory)

            self.compile(root, test_env, test_bo)
            return self.memory.gp - self.memory.global_begins
        else:
            child = Compiler(self.memory.literal.copy())
            return child.calculate_global_len(root, True)

    def compile_all(self, root: ast.Node) -> bytes:
        global_len = self.calculate_global_len(root, False)

        self.memory.set_global_length(global_len)
        bo = ByteOutput(self.memory)

        env = en.GlobalEnvironment()
        self.add_native_functions(env)
        self.add_compile_time_functions(env)

        # print(self.memory.global_bytes)

        self.compile(root, env, bo)
        self.memory.compile_all_functions()

        global_ends = self.memory.functions_begin

        main_take_arg = 0
        if "main" in env.functions:
            main_ptr: Function = env.functions["main"]
            if len(main_ptr.params) == 0:
                self.call_main(main_ptr, [], bo)
            elif len(main_ptr.params) == 2 and \
                    main_ptr.params[0].tal.type_name == "int" and \
                    main_ptr.params[1].tal.type_name == "**char":
                main_take_arg = 1
                # self.memory.allocate(INT_LEN + PTR_LEN, None)
                # bo.push_stack(INT_LEN + PTR_LEN)
                self.call_main(main_ptr, [(global_ends - 16, INT_LEN), (global_ends - 8, PTR_LEN)], bo)
            else:
                raise lib.CompileTimeException("Function main must either have zero parameters or two parameters "
                                               "arg count(int) and arg array(**char).")

        # print(self.memory.global_bytes)
        final_result = ByteOutput(self.memory)
        final_result.write_int(STACK_SIZE)
        final_result.write_int(len(self.memory.literal))
        final_result.write_int(self.memory.get_global_len())
        final_result.write_int(len(self.memory.functions_bytes))
        final_result.write_one(main_take_arg)
        final_result.codes.extend(self.memory.literal)
        final_result.codes.extend(self.memory.functions_bytes)
        final_result.codes.extend(bo.codes)
        return bytes(final_result)

    def compile(self, node: ast.Node, env: en.Environment, bo: ByteOutput, **kwargs):
        if node is None:
            return 0
        nt = node.node_type
        cmp_ftn = self.node_table[nt]
        return cmp_ftn(node, env, bo, **kwargs)

    def compile_block_stmt(self, node: ast.BlockStmt, env: en.Environment, bo: ByteOutput):
        for line in node.lines:
            self.compile(line, env, bo)

    def compile_literal(self, node: ast.Literal, env: en.Environment, bo: ByteOutput):
        return self.memory.calculate_lit_ptr(node.lit_pos)

    def compile_string_literal(self, node: ast.StringLiteralNode, env: en.Environment, bo: ByteOutput):
        lit_pos = node.literal.lit_pos
        if lit_pos not in self.modified_string_poses:
            self.modified_string_poses.add(lit_pos)
            orig_string_ptr = typ.bytes_to_int(self.memory.literal[lit_pos: lit_pos + PTR_LEN])
            new_string_ptr = orig_string_ptr + self.memory.literal_begins
            self.memory.literal[lit_pos: lit_pos + PTR_LEN] = typ.int_to_bytes(new_string_ptr)
        return self.compile(node.literal, env, bo)

    def compile_def_stmt(self, node: ast.DefStmt, env: en.Environment, bo: ByteOutput):
        if self.memory.functions_begin == 0:  # not set
            if node.name == "main":
                if len(node.params.lines) == 2:
                    argc: ast.TypeNode = node.params.lines[0]
                    argv: ast.TypeNode = node.params.lines[1]
                    if argc.right.name == "int":
                        if isinstance(argv.right, ast.UnaryOperator) and \
                                argv.right.operation == "unpack" and \
                                isinstance(argv.right.value, ast.UnaryOperator) and \
                                argv.right.value.operation == "unpack":
                            argv_type: ast.NameNode = argv.right.value.value
                            if argv_type.name == "char":
                                self.memory.gp += INT_LEN + PTR_LEN
            return 0
        r_tal = get_tal_of_defining_node(node.r_type, env, self.memory)

        scope = en.FunctionEnvironment(env)
        self.memory.push_stack()

        param_pairs = []
        for param in node.params.lines:
            tn: ast.TypeNode = param
            name_node: ast.NameNode = tn.left
            tal = get_tal_of_defining_node(tn.right, env, self.memory)
            total_len = tal.total_len(self.memory)

            ptr = self.memory.allocate(total_len, None)

            scope.define_var(name_node.name, tal, ptr)

            param_pair = ParameterPair(name_node.name, tal)
            param_pairs.append(param_pair)

        if env.contains_function(node.name):  # is implementing
            func = env.get_function(node.name, (node.line_num, node.file))
            ftn_ptr = func.ptr
        else:
            ftn_ptr = self.memory.define_func_ptr()  # pre-defined for recursion
            # print("allocated to", fake_ftn_ptr, self.memory.global_bytes)
            ftn = Function(param_pairs, r_tal, ftn_ptr)
            env.define_function(node.name, ftn)

        if node.body is not None:  # implementing
            inner_bo = ByteOutput(self.memory)
            self.compile(node.body, scope, inner_bo)
            inner_bo.write_one(STOP)
            self.memory.implement_func(ftn_ptr, bytes(inner_bo))

            for reg_id_neg in scope.registers:  # return back registers
                self.memory.append_regs64(-reg_id_neg - 1)

        self.memory.restore_stack()

    def compile_name_node(self, node: ast.NameNode, env: en.Environment, bo: ByteOutput, assign_const: bool = False):
        lf = node.line_num, node.file
        ptr = env.get(node.name, lf, assign_const)
        return ptr

    def compile_quick_assignment(self, node: ast.QuickAssignmentNode, env: en.Environment, bo: ByteOutput):
        name: str = node.left.name
        tal = get_tal_of_evaluated_node(node.right, env)
        length = tal.total_len(self.memory)
        r_ptr = self.memory.allocate(length, bo)
        # bo.push_stack(length)
        r = self.compile(node.right, env, bo)  # TODO: optimize
        env.define_var(name, tal, r_ptr)
        bo.assign(r_ptr, r, length)
        return r_ptr

    def compile_assignment_node(self, node: ast.AssignmentNode, env: en.Environment, bo: ByteOutput):
        lf = node.line_num, node.file

        if node.left.node_type == ast.NAME_NODE:  # assign
            r = self.compile(node.right, env, bo)
            if node.level == ast.ASSIGN:
                tal = get_tal_of_evaluated_node(node.left, env)
                ptr = env.get(node.left.name, lf, assign_const=True)
                total_len = tal.total_len(self.memory)

                if r < 0:  # r is a register
                    bo.store_from_reg(ptr, r)
                else:
                    bo.assign(ptr, r, total_len)

        elif node.left.node_type == ast.TYPE_NODE:  # define
            type_node: ast.TypeNode = node.left
            if node.level == ast.VAR or node.level == ast.CONST:
                tal = get_tal_of_defining_node(type_node.right, env, self.memory)
                total_len = tal.total_len(self.memory)

                if total_len == 0:  # pull the right
                    tal = get_tal_of_evaluated_node(node.right, env)
                    total_len = tal.total_len(self.memory)
                    # print(total_len)

                if en.is_pointer(tal):
                    assert total_len == PTR_LEN
                    ptr = self.memory.allocate(PTR_LEN, bo)
                    # bo.push_stack(PTR_LEN)

                    r = self.compile(node.right, env, bo)

                    bo.assign(ptr, r, PTR_LEN)
                elif en.is_array(tal):  # right cannot be binary operator
                    ptr = self.compile_array_creation(node.right, env, tal, bo)

                else:
                    ptr = self.memory.allocate(total_len, bo)
                    # bo.push_stack(total_len)

                    r = self.compile(node.right, env, bo)

                    if r < 0:  # r is a register
                        bo.store_from_reg(ptr, r)
                    else:
                        bo.assign(ptr, r, total_len)

                if node.level == ast.CONST:
                    env.define_const(type_node.left.name, tal, ptr)
                else:
                    env.define_var(type_node.left.name, tal, ptr)

            elif node.level == ast.REGISTER:
                tal = get_tal_of_defining_node(type_node.right, env, self.memory)
                total_len = tal.total_len(self.memory)

                if en.is_array(tal) or en.is_pointer(tal) or total_len != INT_LEN:
                    raise lib.CompileTimeException("Register variable can only be primitive type that has the same "
                                                   "length as int.")

                r = self.compile(node.right, env, bo)
                reg = self.memory.require_regs64(1)[0]
                reg = -reg - 1

                bo.assign_reg(reg, r)

                env.define_var(type_node.left.name, tal, reg)
                env.add_register(reg)

        elif node.left.node_type == ast.INDEXING_NODE:  # set item
            left_node: ast.IndexingNode = node.left
            r = self.compile(node.right, env, bo)
            self.compile_setitem(left_node, r, env, bo)

        elif node.left.node_type == ast.UNARY_OPERATOR:
            left_node: ast.UnaryOperator = node.left
            r = self.compile(node.right, env, bo)
            l_tal = get_tal_of_evaluated_node(left_node, env)
            if left_node.operation == "unpack" or en.is_array(l_tal):
                res_ptr = self.get_unpack_final_pos(left_node, env, bo)
                right_tal = get_tal_of_evaluated_node(node.right, env)
                # orig_tal = get_tal_of_evaluated_node(left_node, env)
                bo.ptr_assign(res_ptr, r, right_tal.total_len(self.memory))

        elif isinstance(node.left, ast.Dot):
            r = self.compile(node.right, env, bo)
            self.compile_attr_assign(node.left, r, env, bo)

    def compile_array_creation(self, right_node, env, tal: en.Type, bo: ByteOutput) -> int:
        ptr = self.create_array(tal, bo, True, env, right_node)

        return ptr

    def create_array(self, tal: en.Type, bo: ByteOutput, assign_right: bool, env=None, right_node=None) -> int:
        # print(tal)
        # if len(tal.array_lengths) == 1:
        total_len = tal.total_len(self.memory)
        ptr = self.memory.allocate(PTR_LEN, bo)
        # bo.push_stack(PTR_LEN)
        arr_addr = self.memory.allocate(total_len, bo)
        # bo.push_stack(total_len)
        bo.store_addr_to_des(ptr, arr_addr)

        if assign_right:
            r = self.compile(right_node, env, bo)
            if r != 0:  # preset array
                bo.unpack_addr(arr_addr, r, total_len)

        return ptr
        # else:
        #     # ptr = self.memory.allocate(PTR_LEN)
        #     # bo.push_stack(PTR_LEN)
        #     partial_tal = en.Type(tal.type_name, *tal.array_lengths[1:])
        #     this_arr_len = tal.array_lengths[0]
        #     ptr_arr_addr = self.memory.allocate(PTR_LEN * this_arr_len)
        #     bo.push_stack(PTR_LEN * this_arr_len)
        #     for i in range(this_arr_len):
        #         sub_array_addr = self.create_array(partial_tal, bo, False)
        #         bo.store_addr_to_des(ptr_arr_addr + i * PTR_LEN, sub_array_addr)
        #     # bo.store_addr_to_des(ptr, ptr_arr_addr)
        #     return ptr_arr_addr

    def compile_setitem(self, node: ast.IndexingNode, value_ptr: int, env: en.Environment, bo: ByteOutput):
        indexing_ptr, unit_len = self.get_indexing_ptr_and_unit_len(node, env, bo)

        bo.ptr_assign(indexing_ptr, value_ptr, unit_len)

    def compile_getitem(self, node: ast.IndexingNode, env: en.Environment, bo: ByteOutput):
        indexing_ptr, unit_len = self.get_indexing_ptr_and_unit_len(node, env, bo)

        result_ptr = self.memory.allocate(unit_len, bo)
        # bo.push_stack(unit_len)
        bo.unpack_addr(result_ptr, indexing_ptr, unit_len)
        return result_ptr

    def compile_attr_assign(self, node: ast.Dot, value_ptr: int, env: en.Environment, bo: ByteOutput):
        attr_addr, length = self.get_struct_attr_ptr_and_len(node, env, bo)

        bo.ptr_assign(attr_addr, value_ptr, length)

    def compile_dot(self, node: ast.Dot, env: en.Environment, bo: ByteOutput):
        attr_addr, length = self.get_struct_attr_ptr_and_len(node, env, bo)

        res_ptr = self.memory.allocate(length, bo)
        # bo.push_stack(length)

        bo.unpack_addr(res_ptr, attr_addr, length)
        # print(res_ptr, attr_addr, length)
        return res_ptr

    # def get_indexing_ptr_and_unit_len(self, node: ast.IndexingNode, env: en.Environment, bo: ByteOutput):
    #     if isinstance(node.call_obj, ast.IndexingNode):
    #         raise lib.CompileTimeException("High dimensional indexing not supported")
    #     obj_tal = get_tal_of_evaluated_node(node.call_obj, env)
    #     unit_len = obj_tal.unit_len(self.memory)
    #     index_ptr = self.compile(node.arg.lines[0], env, bo)
    #     unit_len_ptr = self.memory.allocate(INT_LEN)
    #     bo.push_stack(INT_LEN)
    #     bo.assign_i(unit_len_ptr, unit_len)
    #     indexing_ptr = self.memory.allocate(INT_LEN)
    #     bo.push_stack(INT_LEN)
    #     bo.add_binary_op(MUL, indexing_ptr, index_ptr, unit_len_ptr)
    #     array_ptr = self.compile(node.call_obj, env, bo)
    #     bo.add_binary_op(ADD, indexing_ptr, array_ptr, indexing_ptr)
    #
    #     return indexing_ptr, unit_len

    def get_indexing_ptr_and_unit_len(self, node: ast.IndexingNode, env: en.Environment, bo: ByteOutput):
        # node_depth = index_node_depth(node)
        #
        # tal_depth = len(tal.array_lengths) + pointer_depth(tal.type_name)
        #
        # if node_depth == tal_depth:
        #     length = tal.unit_len(self.memory)
        # elif node_depth > tal_depth:
        #     raise lib.CompileTimeException()
        # else:
        #     length = PTR_LEN

        indexing_addr, tal, length = self.indexing_ptr(node, env, bo)
        # print(length)

        return indexing_addr, length

    def indexing_ptr(self, node: ast.IndexingNode, env: en.Environment, bo: ByteOutput):
        if isinstance(node.call_obj, ast.IndexingNode):  # call obj is array
            arr_addr_ptr, tal, lll = self.indexing_ptr(node.call_obj, env, bo)
        elif isinstance(node.call_obj, ast.NameNode):
            arr_self_addr = self.compile(node.call_obj, env, bo)
            arr_addr_ptr = self.memory.allocate(PTR_LEN, bo)  # pointer storing the addr of arr head
            # bo.push_stack(PTR_LEN)
            bo.store_addr_to_des(arr_addr_ptr, arr_self_addr)
            tal = get_tal_of_evaluated_node(node.call_obj, env)
        else:
            raise lib.CompileTimeException()

        if len(node.arg.lines) != 1:
            raise lib.CompileTimeException("Indexing takes exactly 1 argument")

        node_depth = index_node_depth(node)
        tal_depth = len(tal.array_lengths) + pointer_depth(tal.type_name)

        if node_depth == tal_depth:
            length = tal.unit_len(self.memory)
        elif node_depth > tal_depth:
            raise lib.CompileTimeException()
        else:
            length = PTR_LEN

        index_num_ptr = self.compile(node.arg.lines[0], env, bo)

        indexing_addr = self.memory.allocate(PTR_LEN, bo)
        # bo.push_stack(PTR_LEN)

        bo.unpack_addr(indexing_addr, arr_addr_ptr, PTR_LEN)  # now store the addr of array content
        unit_len_ptr = self.memory.allocate(INT_LEN, bo)
        # bo.push_stack(INT_LEN)
        bo.assign_i(unit_len_ptr, length)
        bo.add_binary_op(MUL, unit_len_ptr, unit_len_ptr, index_num_ptr)
        bo.add_binary_op(ADD, indexing_addr, indexing_addr, unit_len_ptr)

        return indexing_addr, tal, length

    def get_struct_attr_ptr_and_len(self, node: ast.Dot, env: en.Environment, bo: ByteOutput) -> (int, int):
        left_tal = get_tal_of_evaluated_node(node.left, env)
        ptr_depth = pointer_depth(left_tal.type_name)
        if ptr_depth != node.dot_count - 1:
            raise lib.CompileTimeException("Must be struct")

        ltn = left_tal.type_name[ptr_depth:]
        # attr_tal = get_tal_of_evaluated_node(node, env)
        struct_ptr = self.compile(node.left, env, bo)
        struct = env.get_struct(ltn)
        attr_tal = struct.get_attr_tal(node.right.name)

        attr_len = attr_tal.total_len(self.memory)
        attr_pos = struct.get_attr_pos(node.right.name)

        # print(struct, attr_tal, struct_ptr)

        if node.dot_count == 1:  # self
            addr_ptr = self.memory.allocate(PTR_LEN, bo)
            # bo.push_stack(PTR_LEN)
            bo.store_addr_to_des(addr_ptr, struct_ptr + attr_pos)
            return addr_ptr, attr_len
        elif node.dot_count == 2:
            # print(struct_ptr)
            real_addr_ptr = self.memory.allocate(PTR_LEN, bo)
            # bo.push_stack(PTR_LEN)
            bo.assign(real_addr_ptr, struct_ptr, attr_len)
            bo.op_i(ADD, real_addr_ptr, attr_pos)
            return real_addr_ptr, attr_len

    def compile_call(self, node: ast.FuncCall, env: en.Environment, bo: ByteOutput):
        assert isinstance(node.call_obj, ast.NameNode)

        lf = node.line_num, node.file

        ftn = env.get_function(node.call_obj.name, lf)

        if isinstance(ftn, CompileTimeFunction):
            return self.call_compile_time_functions(ftn, node.args, env, bo)

        args = []  # args tuple
        for arg_node in node.args.lines:
            tal = get_tal_of_evaluated_node(arg_node, env)
            total_len = tal.total_len(self.memory)

            if en.is_pointer(tal) or en.is_array(tal):
                total_len = PTR_LEN

            arg_ptr = self.compile(arg_node, env, bo)
            tup = arg_ptr, total_len
            args.append(tup)

        # print(args)
        if isinstance(ftn, Function):
            return self.function_call(ftn, args, env, bo)
        elif isinstance(ftn, NativeFunction):
            return self.native_function_call(ftn, args, env, bo)
        else:
            raise lib.CompileTimeException("Unexpected function type")

    def call_main(self, func: Function, args: list, bo: ByteOutput):
        # self.memory.push_stack()
        r_ptr = self.memory.allocate(INT_LEN, bo)
        bo.call_main(func.ptr, args)
        # self.memory.restore_stack()

    def function_call(self, func: Function, args: list, call_env: en.Environment, bo: ByteOutput):
        if len(args) != len(func.params):
            raise lib.CompileTimeException("Function requires {} arguments, {} given"
                                           .format(len(func.params), len(args)))

        r_len = func.r_tal.total_len(self.memory)

        r_ptr = self.memory.allocate(r_len, bo)
        # bo.push_stack(r_len)

        bo.call(False, func.ptr, args)

        return r_ptr

    def native_function_call(self, func: NativeFunction, args: list, call_env, bo: ByteOutput):
        r_len = func.r_tal.total_len(self.memory)

        r_ptr = self.memory.allocate(r_len, bo)
        # bo.push_stack(r_len)

        bo.call(True, func.ptr, args)

        return r_ptr

    def compile_unary_op(self, node: ast.UnaryOperator, env: en.Environment, bo: ByteOutput):
        if node.operation == "pack":
            num_ptr = self.compile(node.value, env, bo)
            if num_ptr < 0:
                raise lib.CompileTimeException("Register has no memory address")
            ptr_ptr = self.memory.allocate(PTR_LEN, bo)
            # bo.push_stack(PTR_LEN)
            # bo.assign_i(ptr_ptr, num_ptr)
            bo.store_addr_to_des(ptr_ptr, num_ptr)
            return ptr_ptr
        elif node.operation == "unpack":
            orig_tal = get_tal_of_evaluated_node(node, env)
            total_len = orig_tal.total_len(self.memory)
            ptr_ptr = self.compile(node.value, env, bo)
            # print(total_len)
            num_ptr = self.memory.allocate(total_len, bo)
            # print(num_ptr)
            # bo.push_stack(total_len)
            bo.unpack_addr(num_ptr, ptr_ptr, total_len)
            return num_ptr
        elif node.operation == "!":
            v_tal = get_tal_of_evaluated_node(node.value, env)
            if v_tal.total_len(self.memory) != INT_LEN:
                raise lib.CompileTimeException()
            vp = self.compile(node.value, env, bo)
            res_ptr = self.memory.allocate(INT_LEN, bo)
            # bo.push_stack(INT_LEN)
            bo.add_unary_op(NOT, res_ptr, vp)
            return res_ptr
        elif node.operation == "neg":
            v_tal = get_tal_of_evaluated_node(node.value, env)
            vp = self.compile(node.value, env, bo)
            if v_tal.type_name == "int":
                res_ptr = self.memory.allocate(INT_LEN, bo)
                # bo.push_stack(INT_LEN)
                bo.add_unary_op(NEG, res_ptr, vp)
                return res_ptr
            elif v_tal.type_name == "char":  # TODO: May contain bugs
                res_ptr = self.memory.allocate(CHAR_LEN, bo)
                # bo.push_stack(CHAR_LEN)
                trans_ptr = self.memory.allocate(INT_LEN, bo)
                # bo.push_stack(INT_LEN)
                bo.cast_to_int(trans_ptr, vp, CHAR_LEN)
                bo.add_unary_op(NEG, res_ptr, trans_ptr)
                return res_ptr
            elif v_tal.type_name == "float":
                res_ptr = self.memory.allocate(FLOAT_LEN, bo)
                # bo.push_stack(FLOAT_LEN)
                bo.add_unary_op(NEG_F, res_ptr, vp)
                return res_ptr
            else:
                raise lib.CompileTimeException("Cannot take negation of type '{}'".format(v_tal.type_name))
        else:  # normal unary operators
            raise lib.CompileTimeException("Not implemented")

    def compile_binary_op(self, node: ast.BinaryOperator, env: en.Environment, bo: ByteOutput):
        l_tal = get_tal_of_evaluated_node(node.left, env)
        r_tal = get_tal_of_evaluated_node(node.right, env)
        # print(l_tal, r_tal, node.operation)

        if node.operation in WITH_ASSIGN:
            # is assignment
            lp = self.compile(node.left, env, bo, assign_const=True)
        else:
            lp = self.compile(node.left, env, bo)
        rp = self.compile(node.right, env, bo)

        if l_tal.type_name == "int" or l_tal.type_name[0] == "*" or en.is_array(l_tal):
            if r_tal.type_name == "float":
                rip = self.memory.allocate(FLOAT_LEN, bo)
                # bo.push_stack(FLOAT_LEN)
                bo.float_to_int(rip, rp)
                rp = rip
            elif r_tal.type_name != "int" and r_tal.type_name[0] != "*":
                rip = self.memory.allocate(INT_LEN, bo)
                # bo.push_stack(INT_LEN)
                bo.cast_to_int(rip, rp, r_tal.total_len(self.memory))
                rp = rip

            return self.binary_op_int(node.operation, lp, rp, bo)

        elif l_tal.type_name == "char":

            lip = self.memory.allocate(INT_LEN, bo)
            # bo.push_stack(INT_LEN)
            bo.cast_to_int(lip, lp, CHAR_LEN)

            if r_tal.type_name == "float":
                rip = self.memory.allocate(FLOAT_LEN, bo)
                # bo.push_stack(FLOAT_LEN)
                bo.float_to_int(rip, rp)
            elif r_tal.type_name != "int":
                rip = self.memory.allocate(INT_LEN, bo)
                # bo.push_stack(INT_LEN)
                bo.cast_to_int(rip, rp, r_tal.total_len(self.memory))
            else:
                rip = rp

            return self.binary_op_int(node.operation, lip, rip, bo)

        elif l_tal.type_name == "float":

            if r_tal.type_name != "float":
                if r_tal.type_name == "int":
                    rip = rp
                else:
                    rip = self.memory.allocate(INT_LEN, bo)
                    # bo.push_stack(INT_LEN)
                    bo.cast_to_int(rip, rp, r_tal.total_len(self.memory))
                rfp = self.memory.allocate(FLOAT_LEN, bo)
                # bo.push_stack(FLOAT_LEN)
                bo.int_to_float(rfp, rip)
                rp = rfp

            return self.binary_op_float(node.operation, lp, rp, bo)

        raise lib.CompileTimeException("Unsupported binary operation '{}'".format(node.operation))

    def binary_op_float(self, op: str, lp: int, rp: int, bo: ByteOutput) -> int:
        if op in FLOAT_RESULT_TABLE_FLOAT_FULL:
            if op in FLOAT_RESULT_TABLE_FLOAT:
                res_pos = self.memory.allocate(FLOAT_LEN, bo)
                # bo.push_stack(FLOAT_LEN)

                op_code = FLOAT_RESULT_TABLE_FLOAT[op]
                bo.add_binary_op(op_code, res_pos, lp, rp)
                return res_pos
            else:
                op_code = FLOAT_RESULT_TABLE_FLOAT_FULL[op]
                bo.add_binary_op(op_code, lp, lp, rp)
                return lp
        elif op in EXTENDED_INT_RESULT_TABLE_FLOAT:
            res_pos = self.memory.allocate(INT_LEN, bo)
            # bo.push_stack(INT_LEN)

            if op in INT_RESULT_TABLE_FLOAT:
                op_code = INT_RESULT_TABLE_FLOAT[op]
                bo.add_binary_op(op_code, res_pos, lp, rp)
                return res_pos
            else:
                op_tup = EXTENDED_INT_RESULT_TABLE_FLOAT[op]
                l_res = self.memory.allocate(INT_LEN, bo)
                # bo.push_stack(INT_LEN)
                r_res = self.memory.allocate(INT_LEN, bo)
                # bo.push_stack(INT_LEN)
                bo.add_binary_op(op_tup[0], l_res, lp, rp)
                bo.add_binary_op(op_tup[1], r_res, lp, rp)
                bo.add_binary_op(OR, res_pos, l_res, r_res)
                return res_pos
        else:
            raise lib.CompileTimeException("Binary operator '{}' between floats is unsupported"
                                           .format(op))

    def binary_op_int(self, op: str, lp: int, rp: int, bo: ByteOutput) -> int:
        if op in INT_RESULT_TABLE_INT_FULL:
            if op in INT_RESULT_TABLE_INT:
                res_pos = self.memory.allocate(INT_LEN, bo)
                # bo.push_stack(INT_LEN)

                op_code = INT_RESULT_TABLE_INT[op]
                bo.add_binary_op(op_code, res_pos, lp, rp)
                return res_pos
            else:
                op_code = INT_RESULT_TABLE_INT_FULL[op]
                bo.add_binary_op(op_code, lp, lp, rp)
                return lp
        elif op in EXTENDED_INT_RESULT_TABLE_INT:
            res_pos = self.memory.allocate(INT_LEN, bo)
            # bo.push_stack(INT_LEN)

            # if op in BOOL_RESULT_TABLE_INT:
            #     op_code = BOOL_RESULT_TABLE_INT[op]
            #     bo.add_binary_op_int(op_code, res_pos, lp, rp)
            #     return res_pos
            # else:
            op_tup = EXTENDED_INT_RESULT_TABLE_INT[op]
            l_res = self.memory.allocate(INT_LEN, bo)
            # bo.push_stack(INT_LEN)
            r_res = self.memory.allocate(INT_LEN, bo)
            # bo.push_stack(INT_LEN)
            bo.add_binary_op(op_tup[0], l_res, lp, rp)
            bo.add_binary_op(op_tup[1], r_res, lp, rp)
            bo.add_binary_op(OR, res_pos, l_res, r_res)
            return res_pos
        else:
            raise lib.CompileTimeException("Binary operator '{}' between ints is unsupported"
                                           .format(op))

    def compile_return(self, node: ast.ReturnStmt, env: en.Environment, bo: ByteOutput):
        r = self.compile(node.value, env, bo)
        tal = get_tal_of_evaluated_node(node.value, env)
        bo.add_return(r, tal.total_len(self.memory))
        return r

    def compile_if(self, node: ast.IfStmt, env: en.Environment, bo: ByteOutput):
        # print(node.condition.lines[0])
        cond_ptr = self.compile_condition(node.condition.lines[0], env, bo)
        # print(cond_ptr)
        if_bo = BlockByteOutput(self.memory, bo)
        else_bo = BlockByteOutput(self.memory, bo)

        if_env = en.BlockEnvironment(env)
        else_env = en.BlockEnvironment(env)
        self.compile(node.then_block, if_env, if_bo)
        self.compile(node.else_block, else_env, else_bo)
        # if_branch_len = len(if_bo) + INT_LEN + 1  # skip if branch + goto stmt after if branch
        if_branch_len = len(if_bo) + 10 + 2  # load_i(10), goto(2)

        if_bo.goto(len(else_bo))  # goto the pos after else block

        bo.if_zero_goto(if_branch_len, cond_ptr)

        bo.codes.extend(if_bo.codes)
        bo.codes.extend(else_bo.codes)
        # bo.add_if_zero_goto(, cond_ptr)

    def compile_for_loop(self, node: ast.ForLoopStmt, env: en.Environment, bo: ByteOutput):
        if len(node.condition.lines) != 3:
            raise lib.CompileTimeException("For loop title must have 3 parts.")

        # if loop body does not contains break, no loop_indicator needed
        optimize_able = self.optimize_level >= OPTIMIZE_LOOP_INDICATOR and not has_child_node(node.body, ast.BreakStmt)

        self.memory.store_sp()
        bo.write_one(STORE_SP)  # before loop

        if optimize_able:
            loop_indicator = None
        elif self.optimize_level >= OPTIMIZE_LOOP_REG and self.memory.has_enough_regs():
            reg = self.memory.require_reg64()
            loop_indicator = -reg - 1
            bo.assign_reg_i(loop_indicator, 1)
        else:
            loop_indicator = self.memory.allocate(INT_LEN, bo)
            bo.assign_i(loop_indicator, 1)

        title_env = en.LoopEnvironment(env)
        body_env = en.BlockEnvironment(title_env)

        self.compile(node.condition.lines[0], title_env, bo)  # start

        init_len = len(bo)

        self.memory.store_sp()
        bo.write_one(STORE_SP)
        cond_ptr = self.compile_condition(node.condition.lines[1], title_env, bo)

        if optimize_able:
            real_cond_ptr = cond_ptr
        elif self.optimize_level >= OPTIMIZE_LOOP_REG and self.memory.has_enough_regs():
            reg = self.memory.require_reg64()
            real_cond_ptr = -reg - 1
            bo.add_binary_op(AND, real_cond_ptr, cond_ptr, loop_indicator)
        else:
            real_cond_ptr = self.memory.allocate(INT_LEN, bo)
            bo.add_binary_op(AND, real_cond_ptr, cond_ptr, loop_indicator)

        cond_len = len(bo) - init_len

        body_bo = LoopByteOutput(self.memory, loop_indicator, cond_len, node.condition.lines[2])

        self.compile(node.body, body_env, body_bo)
        self.compile(node.condition.lines[2], title_env, body_bo)  # step
        body_bo.write_one(RES_SP)

        body_len = len(body_bo) + 10 + 2  # load_i(10), goto(2)

        if_len = bo.if_zero_goto(body_len, real_cond_ptr)

        body_bo.goto(-body_len - cond_len - if_len)  # the length of if_zero_goto(3), load_i(10), load(10)

        bo.codes.extend(body_bo.codes)
        # print(len(bo) - body_len - cond_len, init_len)
        bo.write_one(RES_SP)
        self.memory.restore_sp()
        bo.write_one(RES_SP)
        self.memory.restore_sp()

        if real_cond_ptr < 0:
            self.memory.append_regs64(-real_cond_ptr - 1)
        if loop_indicator is not None and loop_indicator < 0:
            self.memory.append_regs64(-loop_indicator - 1)

    def compile_while_loop(self, node: ast.WhileStmt, env: en.Environment, bo: ByteOutput):
        if len(node.condition.lines) != 1:
            raise lib.CompileTimeException("While loop title must have 1 part.")

        # if loop body does not contains break, no loop_indicator needed
        optimize_able = self.optimize_level >= OPTIMIZE_LOOP_INDICATOR and not has_child_node(node.body, ast.BreakStmt)

        self.memory.store_sp()  # 进loop之前
        bo.write_one(STORE_SP)

        if optimize_able:
            loop_indicator = None
        elif self.optimize_level >= OPTIMIZE_LOOP_REG and self.memory.has_enough_regs():
            reg = self.memory.require_reg64()
            loop_indicator = -reg - 1
            bo.assign_reg_i(loop_indicator, 1)
        else:
            loop_indicator = self.memory.allocate(INT_LEN, bo)
            bo.assign_i(loop_indicator, 1)

        init_len = len(bo)
        self.memory.store_sp()  # 循环开始
        bo.write_one(STORE_SP)

        title_env = en.LoopEnvironment(env)
        body_env = en.BlockEnvironment(title_env)

        cond_ptr = self.compile_condition(node.condition.lines[0], env, bo)

        if optimize_able:
            real_cond_ptr = cond_ptr
        elif self.optimize_level >= OPTIMIZE_LOOP_REG and self.memory.has_enough_regs():
            reg = self.memory.require_reg64()
            real_cond_ptr = -reg - 1
            bo.add_binary_op(AND, real_cond_ptr, cond_ptr, loop_indicator)
        else:
            real_cond_ptr = self.memory.allocate(INT_LEN, bo)
            bo.add_binary_op(AND, real_cond_ptr, cond_ptr, loop_indicator)

        cond_len = len(bo) - init_len

        body_bo = LoopByteOutput(self.memory, loop_indicator, cond_len, None)

        self.compile(node.body, body_env, body_bo)
        # self.memory.restore_sp()
        body_bo.write_one(RES_SP)
        body_len = len(body_bo) + 10 + 2  # load_i(10), goto(2)

        if_len = bo.if_zero_goto(body_len, real_cond_ptr)

        body_bo.goto(-body_len - cond_len - if_len)  # the length of if_zero_goto(3), load_i(10), load(10)

        bo.codes.extend(body_bo.codes)
        # print(len(bo) - body_len - cond_len, init_len)
        self.memory.restore_sp()
        bo.write_one(RES_SP)

        self.memory.restore_sp()
        bo.write_one(RES_SP)

        if real_cond_ptr < 0:
            self.memory.append_regs64(-real_cond_ptr - 1)
        if loop_indicator is not None and loop_indicator < 0:
            self.memory.append_regs64(-loop_indicator - 1)

    def compile_condition(self, node: ast.Expr, env: en.Environment, bo: ByteOutput):
        tal = get_tal_of_evaluated_node(node, env)
        if tal.type_name != "int":
            raise lib.CompileTimeException("Conditional statement can only have boolean output. Got '{}'."
                                           .format(tal.type_name))
        return self.compile(node, env, bo)

    def compile_break(self, node: ast.BreakStmt, env: en.Environment, bo: ByteOutput):
        loop_indicator = bo.get_loop_indicator()
        if loop_indicator < 0:  # is register
            bo.assign_reg_i(loop_indicator, 0)
        else:
            bo.assign_i(loop_indicator, 0)
        self.compile_continue(None, env, bo)

    def compile_continue(self, node: ast.ContinueStmt, env: en.Environment, bo: ByteOutput):
        step_node, length_before = bo.get_loop_length()

        cur_len = len(bo)
        self.compile(step_node, env, bo)
        len_diff = len(bo) - cur_len

        li = bo.get_loop_indicator()
        if li is None:
            back = 42
        elif li < 0:
            back = 35
        else:
            back = 42

        bo.write_one(RES_SP)
        bo.goto(-length_before - len_diff - back)
        # bo.write_one(GOTO)
        # bo.write_int(-length_before - len_diff - INT_LEN - 1)

    def compile_undefined(self, node: ast.UndefinedNode, env: en.Environment, bo: ByteOutput):
        return 0

    def compile_null(self, node, env, bo: ByteOutput):
        null_ptr = self.memory.allocate(PTR_LEN, bo)
        # bo.push_stack(PTR_LEN)
        bo.assign_i(null_ptr, 0)
        return null_ptr

    def compile_struct(self, node: ast.StructNode, env: en.Environment, bo: ByteOutput):
        struct = Struct(node.name)
        pos = 0
        for line in node.block.lines:
            if not isinstance(line, ast.AssignmentNode):
                raise lib.CompileTimeException("Struct must only contain variable declaration. " +
                                               generate_lf(node))
            if not isinstance(line.right, ast.UndefinedNode):
                raise lib.CompileTimeException("Variable assignment not supported in struct declaration" +
                                               generate_lf(node))
            type_node: ast.TypeNode = line.left
            tal = get_tal_of_defining_node(type_node.right, env, self.memory)
            name = type_node.left.name
            struct.vars[name] = pos, tal
            total_len = tal.total_len(self.memory)
            pos += total_len

        self.memory.add_type(node.name, pos)
        env.add_struct(node.name, struct)

    def compile_in_decrement(self, node: ast.InDecrementOperator, env: en.Environment, bo: ByteOutput):
        ptr = self.compile(node.value, env, bo, assign_const=True)
        tal = get_tal_of_evaluated_node(node.value, env)
        if node.is_post:
            if node.operation == "++":
                if tal.type_name == "int":
                    r_ptr = self.memory.allocate(INT_LEN, bo)
                    # bo.push_stack(INT_LEN)
                    bo.assign(r_ptr, ptr, INT_LEN)
                    bo.op_i(ADD, ptr, 1)
                    return r_ptr
            elif node.operation == "--":
                if tal.type_name == "int":
                    r_ptr = self.memory.allocate(INT_LEN, bo)
                    # bo.push_stack(INT_LEN)
                    bo.assign(r_ptr, ptr, INT_LEN)
                    bo.op_i(SUB, ptr, 1)
                    return r_ptr
        else:
            if node.operation == "++":
                if tal.type_name == "int":
                    bo.op_i(ADD, ptr, 1)
                    return ptr
            elif node.operation == "--":
                if tal.type_name == "int":
                    bo.op_i(SUB, ptr, 1)
                    return ptr

    def get_unpack_final_pos(self, node: ast.UnaryOperator, env: en.Environment, bo):
        if isinstance(node, ast.UnaryOperator) and node.operation == "unpack":
            return self.get_unpack_final_pos(node.value, env, bo)
        elif isinstance(node, ast.NameNode):
            return env.get(node.name, (node.line_num, node.file), False)
        elif isinstance(node, ast.Expr):
            return self.compile(node, env, bo)
        else:
            raise lib.CompileTimeException()

    def call_compile_time_functions(self, func: CompileTimeFunction, arg_node: ast.BlockStmt, env: en.Environment,
                                    bo: ByteOutput):
        r_len = func.r_tal.total_len(self.memory)
        r_ptr = self.memory.allocate(r_len, bo)
        # bo.push_stack(r_len)

        return func.func(r_ptr, env, bo, arg_node.lines)

    def function_sizeof(self, r_ptr: int, env: en.Environment, bo: ByteOutput, args: list):
        if len(args) != 1:
            raise lib.CompileTimeException("Function 'sizeof' takes exactly 1 argument, {} given."
                                           .format(len(args)))
        arg = args[0]
        if not isinstance(arg, ast.NameNode):
            raise lib.CompileTimeException("Unexpected argument type. Got {}"
                                           .format(type(arg)))
        size = self.memory.get_type_size(arg.name)
        bo.assign_i(r_ptr, size)
        return r_ptr

    def function_char(self, r_ptr: int, env: en.Environment, bo: ByteOutput, args: list):
        pass

    def function_int(self, r_ptr: int, env: en.Environment, bo: ByteOutput, args: list):
        if len(args) != 1:
            raise lib.CompileTimeException("Function 'int' takes exactly 1 argument, {} given."
                                           .format(len(args)))
        arg = args[0]
        arg_ptr = self.compile(arg, env, bo)
        arg_tal = get_tal_of_evaluated_node(arg, env)
        if arg_tal.type_name == "int":
            bo.assign(r_ptr, arg_ptr, INT_LEN)
            return r_ptr
        if arg_tal.type_name == "float":
            bo.float_to_int(r_ptr, arg_ptr)
            return r_ptr
        elif arg_tal.type_name == "char":
            bo.cast_to_int(r_ptr, arg_ptr, CHAR_LEN)
            return r_ptr
        else:
            raise lib.CompileTimeException("Cannot cast '{}' to int".format(arg_tal.type_name))

    def function_float(self, r_ptr: int, env: en.Environment, bo: ByteOutput, args: list):
        if len(args) != 1:
            raise lib.CompileTimeException("Function 'float' takes exactly 1 argument, {} given."
                                           .format(len(args)))
        arg = args[0]
        arg_ptr = self.compile(arg, env, bo)
        arg_tal = get_tal_of_evaluated_node(arg, env)
        if arg_tal.type_name == "int":
            bo.int_to_float(r_ptr, arg_ptr)
            return r_ptr
        elif arg_tal.type_name == "float":
            bo.assign(r_ptr, arg_ptr, FLOAT_LEN)
            return r_ptr
        else:
            raise lib.CompileTimeException("Cannot cast '{}' to float".format(arg_tal.type_name))


def index_node_depth(node: ast.IndexingNode):
    if node.call_obj.node_type == ast.INDEXING_NODE:
        return index_node_depth(node.call_obj) + 1
    else:
        return 1


def get_tal_of_defining_node(node: ast.Node, env: en.Environment, mem: MemoryManager) -> en.Type:
    if node.node_type == ast.NAME_NODE:
        node: ast.NameNode
        return en.Type(node.name)
    elif node.node_type == ast.INDEXING_NODE:  # array
        node: ast.IndexingNode
        tn_al_inner: en.Type = get_tal_of_defining_node(node.call_obj, env, mem)
        if len(node.arg.lines) == 0:
            return en.Type(tn_al_inner.type_name, 0)
        length_lit = node.arg.lines[0]
        if not isinstance(length_lit, ast.Literal) or length_lit.lit_type != 0:
            raise lib.CompileTimeException("Array length must be fixed int literal. " +
                                           generate_lf(node))
        lit_pos = length_lit.lit_pos
        arr_len_b = mem.literal[lit_pos: lit_pos + INT_LEN]
        arr_len_v = typ.bytes_to_int(arr_len_b)
        # return type_name, arr_len_inner * typ.bytes_to_int(arr_len_b)
        return en.Type(tn_al_inner.type_name, *tn_al_inner.array_lengths, arr_len_v)
    elif node.node_type == ast.UNARY_OPERATOR:
        node: ast.UnaryOperator
        tal = get_tal_of_defining_node(node.value, env, mem)
        if node.operation == "unpack":
            return en.Type("*" + tal.type_name, *tal.array_lengths)
        else:
            raise lib.UnexpectedSyntaxException()


LITERAL_TYPE_TABLE = {
    0: en.Type("int"),
    1: en.Type("float"),
    3: en.Type("string"),
    4: en.Type("char")
}


def get_tal_of_node_self(node: ast.Node, env: en.Environment) -> en.Type:
    if node.node_type == ast.NAME_NODE:
        node: ast.NameNode
        return env.get_type_arr_len(node.name, (node.line_num, node.file))
    elif node.node_type == ast.INDEXING_NODE:
        node: ast.IndexingNode
        return get_tal_of_node_self(node.call_obj, env)
    elif node.node_type == ast.UNARY_OPERATOR:
        node: ast.UnaryOperator
        print(2223)


def get_tal_of_evaluated_node(node: ast.Node, env: en.Environment) -> en.Type:
    if node.node_type == ast.LITERAL:
        node: ast.Literal
        return LITERAL_TYPE_TABLE[node.lit_type]
    elif node.node_type == ast.STRING_LITERAL:
        node: ast.StringLiteralNode
        return en.Type("char", node.byte_length)
    elif node.node_type == ast.NAME_NODE:
        node: ast.NameNode
        return env.get_type_arr_len(node.name, (node.line_num, node.file))
    elif node.node_type == ast.UNARY_OPERATOR:
        node: ast.UnaryOperator
        tal = get_tal_of_evaluated_node(node.value, env)
        if node.operation == "unpack":
            if len(tal.type_name) > 1 and tal.type_name[0] == "*":
                return en.Type(tal.type_name[1:])
            elif len(tal.array_lengths) > 0:
                return en.Type(tal.type_name, *tal.array_lengths[1:])
            else:
                raise lib.TypeException("Cannot unpack a non-pointer type")
        elif node.operation == "pack":
            return en.Type("*" + tal.type_name)
        # elif node.operation in OTHER_BOOL_RESULT_UNARY:
        #     return en.Type("int")
        else:
            return tal
    elif node.node_type == ast.BINARY_OPERATOR:
        node: ast.BinaryOperator
        if node.operation in BOOL_RESULT_TABLE:
            return en.Type("int")
        return get_tal_of_evaluated_node(node.left, env)
    elif node.node_type == ast.FUNCTION_CALL:
        node: ast.FuncCall
        call_obj = node.call_obj
        if call_obj.node_type == ast.NAME_NODE:
            func: Function = env.get_function(call_obj.name, (node.line_num, node.file))
            return func.r_tal
    elif node.node_type == ast.INDEXING_NODE:  # array
        node: ast.IndexingNode
        # return get_tal_of_ordinary_node(node.call_obj, env)
        tal_co = get_tal_of_evaluated_node(node.call_obj, env)
        if en.is_array(tal_co):
            return en.Type(tal_co.type_name, *tal_co.array_lengths[1:])
        elif tal_co.type_name[0] == "*":
            return en.Type(tal_co.type_name[1:])
        else:
            raise lib.TypeException()
    elif node.node_type == ast.IN_DECREMENT_OPERATOR:
        node: ast.InDecrementOperator
        return get_tal_of_evaluated_node(node.value, env)
    elif node.node_type == ast.NULL_STMT:
        return en.Type("*void")
    elif node.node_type == ast.DOT:
        node: ast.Dot
        left_tal = get_tal_of_evaluated_node(node.left, env)
        ptr_depth = pointer_depth(left_tal.type_name)
        if ptr_depth != node.dot_count - 1:
            raise lib.TypeException()
        real_l_tal = en.Type(left_tal.type_name[ptr_depth], left_tal.array_lengths)
        if env.is_struct(real_l_tal.type_name):
            struct = env.get_struct(real_l_tal.type_name)
            return struct.get_attr_tal(node.right.name)
        else:
            raise lib.TypeException()
    elif node.node_type == ast.IN_DECREMENT_OPERATOR:
        node: ast.InDecrementOperator
        return get_tal_of_evaluated_node(node.value, env)
    else:
        raise lib.TypeException("Cannot get type and array length")


def has_child_node(node: ast.Node, target: type) -> bool:
    if isinstance(node, target):
        return True
    elif isinstance(node, ast.Node):
        attr_names = dir(node)
        for attr_name in attr_names:
            attr = getattr(node, attr_name)
            if isinstance(attr, ast.Node):
                if has_child_node(attr, target):
                    return True
            elif isinstance(attr, list):
                for i in range(len(attr)):
                    if has_child_node(attr[i], target):
                        return True
    return False


def pointer_depth(type_name: str) -> int:
    for i in range(len(type_name)):
        if type_name[i] != "*":
            return i
    raise lib.CompileTimeException()


def generate_lf(node: ast.Node) -> str:
    return "In file '{}', at line {}.".format(node.file, node.line_num)


def indexing_remain_depth(node: ast.IndexingNode, tal: en.Type):
    i = 0
    while len(tal.array_lengths) > 0:
        print(12312313131)
        node = node.call_obj
        tal.array_lengths = tal.array_lengths[1:]
        i += 1
    return i
