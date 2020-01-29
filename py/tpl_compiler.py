import py.tpl_ast as ast
import py.tpl_environment as en
import py.tpl_types as typ
import py.tpl_lib as lib
from py.tpl_types import INT_LEN, FLOAT_LEN, PTR_LEN, CHAR_LEN, VOID_LEN

STACK_SIZE = 1024

EXIT = 1  # completely exit function
STOP = 2  # STOP                                  | stop current process
ASSIGN = 3  # ASSIGN   TARGET    SOURCE   LENGTH    | copy LENGTH bytes from SOURCE to TARGET
CALL = 4  # CALL
RETURN = 5  # RETURN   VALUE_PTR
GOTO = 6  # JUMP       CODE_PTR
LOAD_A = 7  # LOAD_A                             | loads rel_addr + fp to register
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
CAST_INT = 38  # CAST_INT  RESULT_P  SRC_P              | cast int-like to int
INT_TO_FLOAT = 39
FLOAT_TO_INT = 40
LOAD_AS = 41  # | load addr from rel_addr + sp
# MOVE_REG_SPE = 42  # MOVE_REG_SPE   %DST  %SRC       | copy between special regs.  1: sp 2: fp
PUSH = 42
SP_TO_FP = 43
FP_TO_SP = 44
EXIT_V = 45  # | exit with value
SET_RET = 46

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

LABEL = 128
GOTO_L = 129
IF_ZERO_GOTO_L = 130

# Number of native functions, used for generating tpa
NATIVE_FUNCTION_COUNT = 7

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


# SPE_REGS = {
#     "SP": 1,
#     "FP": 2
# }


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

    # def reserve_space(self, length: int) -> int:
    #     i = len(self.codes)
    #     self.codes.extend(bytes(length))
    #     return i

    def push(self, value: int):
        reg1 = self.manager.require_reg64()

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

    def assign_as(self, tar: int, src: int, length: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD_AS)
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

    def call_main(self, ftn_ptr: int, r_ptr: int, args: list):
        reg1, reg2 = self.manager.require_regs64(2)
        i = 0
        for arg in args:
            self.assign_as(i, arg[0], arg[1])

            i += arg[1]

        self.write_one(LOAD_A)
        self.write_one(reg1)  # ftn ptr
        self.write_int(ftn_ptr)

        self.write_one(LOAD_A)
        self.write_one(reg2)
        self.write_int(r_ptr)

        self.write_one(SET_RET)
        self.write_one(reg2)

        self.write_one(CALL)
        self.write_one(reg1)
        # self.write_one(reg2)

        self.manager.append_regs64(reg2, reg1)

    def call(self, ftn_ptr: int, not_void: bool, r_ptr: int, args: list):
        """
        :param ftn_ptr:
        :param not_void: True iff the return type of this function is not void
        :param r_ptr: return ptr
        :param args: list of tuple(arg_ptr, arg_len)
        :return:
        """
        reg1, reg2 = self.manager.require_regs64(2)

        i = 0
        for arg in args:
            if arg[0] < 0:  # register:
                self.store_from_reg(i, arg[0])
            else:
                self.assign_as(i, arg[0], arg[1])

            i += arg[1]

        self.write_one(LOAD_A)
        self.write_one(reg1)  # ftn ptr
        self.write_int(ftn_ptr)

        if not_void:
            self.write_one(LOAD_A)
            self.write_one(reg2)  # return ptr
            self.write_int(r_ptr)

            self.write_one(SET_RET)
            self.write_one(reg2)

        self.write_one(CALL)
        self.write_one(reg1)
        # self.write_one(reg2)

        self.manager.append_regs64(reg2, reg1)

    def call_nat(self, ftn_ptr: int, r_ptr: int, args: list):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        i = 0
        for arg in args:
            if arg[0] < 0:  # register:
                self.store_from_reg(i, arg[0])
            else:
                self.assign_as(i, arg[0], arg[1])

            i += arg[1]

        self.write_one(LOAD_A)
        self.write_one(reg1)  # ftn ptr
        self.write_int(ftn_ptr)

        self.write_one(LOAD_A)
        self.write_one(reg2)  # return ptr
        self.write_int(r_ptr)

        self.write_one(LOAD_I)
        self.write_one(reg3)
        self.write_int(i)  # stores arguments length for native functions

        self.write_one(CALL_NAT)
        self.write_one(reg1)
        self.write_one(reg2)
        self.write_one(reg3)

        self.manager.append_regs64(reg3, reg2, reg1)

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

        self.write_one(FP_TO_SP)

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

    def exit_with_value(self, value_addr: int):
        reg1 = self.manager.require_reg64()

        self.write_one(LOAD)
        self.write_one(reg1)
        self.write_int(value_addr)

        self.write_one(EXIT_V)
        self.write_one(reg1)

        self.manager.append_regs64(reg1)

    def add_label(self, label: int):
        self.write_one(LABEL)
        self.write_int(label)

    def if_zero_goto_l(self, label: int, cond_ptr: int):
        """
        Returns the occupied length

        :param label:
        :param cond_ptr:
        """
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD_I)
        self.write_one(reg1)  # reg stores skip len
        self.write_int(label)

        if cond_ptr < 0:  # cond is register:
            self.write_one(MOVE_REG)
            self.write_one(reg2)
            self.write_one(-cond_ptr - 1)
        else:
            self.write_one(LOAD)
            self.write_one(reg2)  # reg stores cond ptr
            self.write_int(cond_ptr)

        self.write_one(IF_ZERO_GOTO_L)
        self.write_one(reg1)
        self.write_one(reg2)

        self.manager.append_regs64(reg3, reg2, reg1)

    def goto_l(self, label: int):
        reg1, = self.manager.require_regs64(1)

        self.write_one(LOAD_I)
        self.write_one(reg1)
        self.write_int(label)

        self.write_one(GOTO_L)
        self.write_one(reg1)

        self.manager.append_regs64(reg1)

    def write_int(self, i):
        self.codes.extend(typ.int_to_bytes(i))

    def set_bytes(self, from_: int, b: bytes):
        self.codes[from_: from_ + len(b)] = b

    def get_loop_indicator(self):
        raise lib.CompileTimeException("Break outside loop")

    def get_loop_length(self):
        raise lib.CompileTimeException("Continue outside loop")


class MemoryManager:
    def __init__(self, literal_bytes):
        self.stack_begin = 9
        self.sp = 9
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

        self.label_accumulator = 0
        self.text_labels = {}

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

    def generate_label(self):
        label = self.label_accumulator
        self.label_accumulator += 1
        return label

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

    def allocate(self, length, bo) -> int:
        if len(self.blocks) == 0:  # global
            ptr = self.gp
            self.gp += length
        else:  # in call
            ptr = self.sp - self.blocks[-1]
            self.sp += length
            # if bo is not None:
            #     bo.push_stack(length)
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
            # print(ptr, self.func_p)
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


class CompileTimeFunctionType(en.FuncType):
    def __init__(self, param_types: list, rtype: en.Type, func):
        en.FuncType.__init__(self, param_types, rtype, "c")

        self.func = func


class Struct:
    def __init__(self, name: str):
        self.name = name
        self.vars: {str: (int, en.Type)} = {}  # position in struct, type
        self.method_pointers: {str: int} = {}  # absolute addr of real function

    def get_attr_pos(self, attr_name: str) -> int:
        return self.vars[attr_name][0]

    def get_attr_tal(self, attr_name: str) -> en.Type:
        return self.vars[attr_name][1]

    def implement_func_tal(self, func_name, new_tal: en.FuncType):
        ptr_tal = self.vars[func_name]
        if not isinstance(ptr_tal[1], en.AbstractFuncType):
            raise lib.CompileTimeException("Attribute '{}' is not a member function.".format(func_name))
        if isinstance(ptr_tal[1], en.FuncType):
            raise lib.CompileTimeException("Member function '{}' is already implemented.".format(func_name))
        self.vars[func_name] = (ptr_tal[0], new_tal)

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
            ast.IN_DECREMENT_OPERATOR: self.compile_in_decrement,
            ast.LABEL: self.compile_label,
            ast.GOTO: self.compile_goto
        }

    def configs(self, **kwargs):
        if "optimize" in kwargs:
            self.optimize_level = kwargs["optimize"]

    def add_native_functions(self, env: en.GlobalEnvironment):
        p1 = self.memory.define_func_ptr()  # 1: clock
        self.memory.implement_func(p1, typ.int_to_bytes(1))
        ft1 = en.FuncType([], en.Type("int"), 'n')
        env.define_const("clock", ft1, p1)

        p2 = self.memory.define_func_ptr()  # 2: malloc
        self.memory.implement_func(p2, typ.int_to_bytes(2))
        ft2 = en.FuncType([en.Type("int")], en.Type("*void"), 'n')
        env.define_const("malloc", ft2, p2)

        p3 = self.memory.define_func_ptr()  # 3: printf
        self.memory.implement_func(p3, typ.int_to_bytes(3))
        ft3 = en.FuncType([en.Type("*void")], en.Type("void"), 'n')
        env.define_const("printf", ft3, p3)

        p4 = self.memory.define_func_ptr()  # 4: mem_copy
        self.memory.implement_func(p4, typ.int_to_bytes(4))
        ft4 = en.FuncType([en.Type("*char"), en.Type("*char"), en.Type("int")], en.Type("void"), 'n')
        env.define_const("mem_copy", ft4, p4)

        p5 = self.memory.define_func_ptr()  # 5: free
        self.memory.implement_func(p5, typ.int_to_bytes(5))
        ft5 = en.FuncType([en.Type("*void")], en.Type("void"), 'n')
        env.define_const("free", ft5, p5)

        p6 = self.memory.define_func_ptr()  # 6: stringf
        self.memory.implement_func(p6, typ.int_to_bytes(6))
        ft6 = en.FuncType([en.Type("*void")], en.Type("int"), 'n')
        env.define_const("stringf", ft6, p6)

        p7 = self.memory.define_func_ptr()  # 7: scanf
        self.memory.implement_func(p7, typ.int_to_bytes(7))
        ft7 = en.FuncType([en.Type("*void")], en.Type("int"), 'n')
        env.define_const("scanf", ft7, p7)

    def add_compile_time_functions(self, env: en.GlobalEnvironment):
        env.define_const("sizeof", CompileTimeFunctionType([], en.Type("int"), self.function_sizeof), 0)
        env.define_const("char", CompileTimeFunctionType([], en.Type("char"), self.function_char), 0)
        env.define_const("int", CompileTimeFunctionType([], en.Type("int"), self.function_int), 0)
        env.define_const("float", CompileTimeFunctionType([], en.Type("float"), self.function_float), 0)
        env.define_const("exit", CompileTimeFunctionType([], en.Type("void"), self.function_exit), 0)
        env.define_const("new", CompileTimeFunctionType([], en.Type("*void"), self.function_new), 0)

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

        lf = (0, "system")

        main_take_arg = 0
        if env.contains_ptr("main"):
            main_ptr: int = env.get("main", lf, False)
            main_tal: en.FuncType = env.get_type_arr_len("main", lf)
            # main_stack_len = self.memory.function_stack_sizes["main"]
            if len(main_tal.param_types) == 0:
                self.call_main(main_ptr, [], bo)
            elif len(main_tal.param_types) == 2 and \
                    main_tal.param_types[0].type_name == "int" and \
                    main_tal.param_types[1].type_name == "**char":
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
        final_result.write_one(EXIT)
        return bytes(final_result)

    def compile(self, node: ast.Node, env: en.Environment, bo: ByteOutput, **kwargs):
        if node is None:
            return 0
        nt = node.node_type
        cmp_ftn = self.node_table[nt]
        return cmp_ftn(node, env, bo, **kwargs)

    def compile_block_stmt(self, node: ast.BlockStmt, env: en.Environment, bo: ByteOutput):
        if node.standalone:
            return self.compile_preset_array(node, env, bo)
        else:
            for line in node.lines:
                self.compile(line, env, bo)

    def compile_preset_array(self, node: ast.BlockStmt, env: en.Environment, bo: ByteOutput):
        first = None
        ptr = self.memory.allocate(PTR_LEN, bo)
        for i in range(len(node.lines)):
            p = self.memory.allocate(INT_LEN, bo)
            if first is None:
                first = p
            lit_pos = self.compile(node.lines[i], env, bo)
            bo.assign(p, lit_pos, INT_LEN)
        if first is None:
            raise lib.CompileTimeException("Preset array must have at least one element.")
        bo.store_addr_to_des(ptr, first)
        return ptr

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

    def get_function(self, name: str, env: en.Environment, func_tal: en.Type, lf: tuple) -> int:
        if env.contains_ptr(name):  # is implementing
            ftn_ptr: int = env.get(name, lf, False)
            prev_func_tal = env.get_type_arr_len(name, lf)
            if prev_func_tal != func_tal:
                raise lib.CompileTimeException("Incompatible parameter or return types")
        else:
            ftn_ptr = self.memory.define_func_ptr()  # pre-defined for recursion
            env.define_var(name, func_tal, ftn_ptr)
        return ftn_ptr

    def compile_def_stmt(self, node: ast.DefStmt, env: en.Environment, bo: ByteOutput):
        if self.memory.functions_begin == 0:  # not set. 第一次遍历ast获取global长度时用
            if isinstance(node.title, ast.NameNode) and node.title.name == "main":
                # reserve argc and argv len in global
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

        title = node.title

        param_pairs = []
        param_types = []

        if isinstance(title, ast.NameNode):
            is_method = False
        elif isinstance(title, ast.BinaryOperator) and title.operation == "::" and \
                isinstance(title.left, ast.NameNode) and isinstance(title.right, ast.NameNode):
            # add 'this: *Struct' as the first parameter
            is_method = True
            tal = en.Type("*" + title.left.name)
            param_types.append(tal)
            ptr = self.memory.allocate(PTR_LEN, None)
            scope.define_const("this", tal, ptr)
            param_pair = ParameterPair("this", tal)
            param_pairs.append(param_pair)
        else:
            raise lib.CompileTimeException()

        for param in node.params.lines:
            tn: ast.TypeNode = param
            name_node: ast.NameNode = tn.left
            tal = get_tal_of_defining_node(tn.right, env, self.memory)
            total_len = tal.total_len(self.memory)

            param_types.append(tal)

            ptr = self.memory.allocate(total_len, None)

            scope.define_var(name_node.name, tal, ptr)

            param_pair = ParameterPair(name_node.name, tal)
            param_pairs.append(param_pair)

        func_tal = en.FuncType(param_types, r_tal)

        if is_method:
            ftn_ptr = self.memory.define_func_ptr()
            struct = env.get_struct(title.left.name)
            struct.method_pointers[title.right.name] = ftn_ptr
            struct.implement_func_tal(title.right.name, func_tal)
        else:
            ftn_ptr = self.get_function(title.name, env, func_tal, (node.line_num, node.file))

        if node.body is not None:  # implementing
            self.generate_labels(node.body)  # preprocess the labels to make sure future-pointing goto's work

            inner_bo = ByteOutput(self.memory)
            self.compile(node.body, scope, inner_bo)
            inner_bo.write_one(FP_TO_SP)
            inner_bo.write_one(STOP)

            for reg_id_neg in scope.registers:  # restore registers usage
                self.memory.append_regs64(-reg_id_neg - 1)

            stack_len = self.memory.sp - self.memory.blocks[-1]

            fn_bo = ByteOutput(self.memory)
            fn_bo.write_one(SP_TO_FP)
            fn_bo.push(stack_len)
            fn_bo.codes.extend(bytes(inner_bo))

            self.memory.implement_func(ftn_ptr, bytes(fn_bo))

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

        if not isinstance(node.right, ast.UndefinedNode):
            right_tal = get_tal_of_evaluated_node(node.right, env)
            if right_tal.type_name == "void":
                raise lib.CompileTimeException("Cannot assign variable with value type 'void'. " + generate_lf(node))

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

                return ptr

        elif node.left.node_type == ast.TYPE_NODE:  # define
            type_node: ast.TypeNode = node.left
            if node.level == ast.VAR or node.level == ast.CONST:
                tal = get_tal_of_defining_node(type_node.right, env, self.memory)
                total_len = tal.total_len(self.memory)

                if total_len == 0:  # pull the right
                    tal = get_tal_of_evaluated_node(node.right, env)
                    total_len = tal.total_len(self.memory)

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

                return ptr

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

                return reg

        elif node.left.node_type == ast.INDEXING_NODE:  # set item
            left_node: ast.IndexingNode = node.left
            r = self.compile(node.right, env, bo)
            self.compile_setitem(left_node, r, env, bo)

            return r

        elif node.left.node_type == ast.UNARY_OPERATOR:
            left_node: ast.UnaryOperator = node.left
            r = self.compile(node.right, env, bo)
            l_tal = get_tal_of_evaluated_node(left_node, env)
            if left_node.operation == "unpack" or en.is_array(l_tal):
                res_ptr = self.get_unpack_final_pos(left_node, env, bo)
                right_tal = get_tal_of_evaluated_node(node.right, env)
                # orig_tal = get_tal_of_evaluated_node(left_node, env)
                bo.ptr_assign(res_ptr, r, right_tal.total_len(self.memory))

                return res_ptr

        elif isinstance(node.left, ast.Dot):
            r = self.compile(node.right, env, bo)
            self.compile_attr_assign(node.left, r, env, bo)
            return r

        raise lib.CompileTimeException("Cannot assign to type {}.".format(type(node.left).__name__) + generate_lf(node))

    def compile_array_creation(self, right_node, env, tal: en.Type, bo: ByteOutput) -> int:
        ptr = self.create_array(tal, bo, True, env, right_node)

        return ptr

    def create_array(self, tal: en.Type, bo: ByteOutput, assign_right: bool, env=None, right_node=None) -> int:
        # print(tal)
        if len(tal.array_lengths) != 1:
            raise lib.CompileTimeException("High dimensional local array not supported. Use pointer array instead.")
        total_len = tal.total_len(self.memory)
        ptr = self.memory.allocate(PTR_LEN, bo)
        arr_addr = self.memory.allocate(total_len, bo)
        bo.store_addr_to_des(ptr, arr_addr)

        if assign_right:
            r = self.compile(right_node, env, bo)
            if r != 0:  # preset array
                r_tal = get_tal_of_evaluated_node(right_node, env)
                if r_tal.array_lengths[0] > tal.array_lengths[0]:
                    raise lib.CompileTimeException(
                        "Preset array has length longer than its definition. " + generate_lf(right_node))

                bo.unpack_addr(arr_addr, r, total_len)

        return ptr

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
        attr_addr, attr_tal, call = self.get_struct_attr_ptr_and_len(node, env, bo)

        bo.ptr_assign(attr_addr, value_ptr, attr_tal.total_len(self.memory))

    def attr_assign(self, ):
        pass

    def compile_dot(self, node: ast.Dot, env: en.Environment, bo: ByteOutput, assign_const=False):
        """

        :param node:
        :param env:
        :param bo:
        :param assign_const: must be false since struct does not support constant attributes
        :return:
        """
        attr_addr, attr_tal, call = self.get_struct_attr_ptr_and_len(node, env, bo)

        if call:
            call_node: ast.FuncCall = node.right
            args = call_node.args.lines.copy()
            args.insert(0, node.left)
            res_ptr = self.memory.allocate(PTR_LEN, bo)
            bo.unpack_addr(res_ptr, attr_addr, PTR_LEN)
            return self.compile_ptr_call(res_ptr, attr_tal, args, env, bo)
        else:
            length = attr_tal.total_len(self.memory)
            res_ptr = self.memory.allocate(length, bo)
            bo.unpack_addr(res_ptr, attr_addr, length)
            return res_ptr

    def get_indexing_ptr_and_unit_len(self, node: ast.IndexingNode, env: en.Environment, bo: ByteOutput):

        indexing_addr, tal, length = self.indexing_ptr(node, env, bo)

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

    def get_struct_attr_ptr_and_len(self, node: ast.Dot, env: en.Environment, bo: ByteOutput) -> \
            (int, en.Type, bool):
        left_tal = get_tal_of_evaluated_node(node.left, env)
        ptr_depth = pointer_depth(left_tal.type_name)
        if ptr_depth != node.dot_count - 1:
            raise lib.CompileTimeException("Must be struct")

        ltn = left_tal.type_name[ptr_depth:]
        # attr_tal = get_tal_of_evaluated_node(node, env)
        left_ptr = self.compile(node.left, env, bo)
        struct = env.get_struct(ltn)
        if isinstance(node.right, ast.NameNode):
            name = node.right.name
            call = False
        elif isinstance(node.right, ast.FuncCall):
            name = node.right.call_obj.name
            call = True
        else:
            raise lib.CompileTimeException()
        attr_tal = struct.get_attr_tal(name)

        attr_len = attr_tal.total_len(self.memory)
        attr_pos = struct.get_attr_pos(name)

        if node.dot_count == 1:  # self
            addr_ptr = self.memory.allocate(PTR_LEN, bo)
            bo.store_addr_to_des(addr_ptr, left_ptr + attr_pos)
            return addr_ptr, attr_tal, call
        elif node.dot_count == 2:
            real_addr_ptr = self.memory.allocate(PTR_LEN, bo)
            bo.assign(real_addr_ptr, left_ptr, attr_len)
            bo.op_i(ADD, real_addr_ptr, attr_pos)
            return real_addr_ptr, attr_tal, call
        elif node.dot_count == 3:
            real_addr_ptr = self.memory.allocate(PTR_LEN, bo)
            bo.unpack_addr(real_addr_ptr, left_ptr, attr_len)
            bo.op_i(ADD, real_addr_ptr, attr_pos)
            return real_addr_ptr, attr_tal, call
        else:
            raise lib.CompileTimeException("Pointer too deep.")

    def compile_ptr_call(self, ftn: int, ftn_tal: en.FuncType, arg_nodes: list, env: en.Environment,
                         bo: ByteOutput) -> int:
        args = []  # args tuple
        for arg_node in arg_nodes:
            tal = get_tal_of_evaluated_node(arg_node, env)
            total_len = tal.total_len(self.memory)

            if en.is_pointer(tal) or en.is_array(tal):
                total_len = PTR_LEN

            arg_ptr = self.compile(arg_node, env, bo)
            tup = arg_ptr, total_len
            args.append(tup)

        # print(args)
        if ftn_tal.func_type == "f":
            return self.function_call(ftn, ftn_tal, args, env, bo)
        elif ftn_tal.func_type == "n":
            return self.native_function_call(ftn, ftn_tal, args, env, bo)
        else:
            raise lib.CompileTimeException("Unexpected function type")

    def compile_call(self, node: ast.FuncCall, env: en.Environment, bo: ByteOutput):
        assert isinstance(node.call_obj, ast.NameNode)

        lf = node.line_num, node.file

        # ftn = env.get_function(node.call_obj.name, lf)
        ftn = env.get(node.call_obj.name, lf, False)
        ftn_tal: en.FuncType = env.get_type_arr_len(node.call_obj.name, lf)

        if not isinstance(ftn_tal, en.FuncType):
            raise lib.CompileTimeException("Object is not callable")

        if ftn_tal.func_type == "c":
            ftn_tal: CompileTimeFunctionType
            return self.call_compile_time_functions(ftn, ftn_tal, node.args, env, bo)

        return self.compile_ptr_call(ftn, ftn_tal, node.args.lines, env, bo)

    def call_main(self, func_ptr: int, args: list, bo: ByteOutput):
        r_ptr = 1
        bo.call_main(func_ptr, r_ptr, args)

    def function_call(self, func_ptr: int, func_tal: en.FuncType, args: list,
                      call_env: en.Environment, bo: ByteOutput):
        if len(args) != len(func_tal.param_types):
            raise lib.CompileTimeException("Function requires {} arguments, {} given"
                                           .format(len(func_tal.param_types), len(args)))

        r_len = func_tal.rtype.total_len(self.memory)
        r_ptr = self.memory.allocate(r_len, bo)

        bo.call(func_ptr, r_len > 0, r_ptr, args)

        return r_ptr

    def native_function_call(self, func: int, func_tal: en.FuncType, args: list, call_env, bo: ByteOutput):
        r_len = func_tal.rtype.total_len(self.memory)

        r_ptr = self.memory.allocate(r_len, bo)
        # bo.push_stack(r_len)

        bo.call_nat(func, r_ptr, args)

        return r_ptr

    def compile_unary_op(self, node: ast.UnaryOperator, env: en.Environment, bo: ByteOutput):
        if node.operation == "pack":
            num_ptr = self.compile(node.value, env, bo)
            if num_ptr < 0:
                raise lib.CompileTimeException("Register has no memory address")
            ptr_ptr = self.memory.allocate(PTR_LEN, bo)
            bo.store_addr_to_des(ptr_ptr, num_ptr)
            return ptr_ptr
        elif node.operation == "unpack":
            orig_tal = get_tal_of_evaluated_node(node, env)
            total_len = orig_tal.total_len(self.memory)
            ptr_ptr = self.compile(node.value, env, bo)
            num_ptr = self.memory.allocate(total_len, bo)
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
        if node.value is not None:
            r = self.compile(node.value, env, bo)
            tal = get_tal_of_evaluated_node(node.value, env)
            bo.add_return(r, tal.total_len(self.memory))
            return r

    def compile_if(self, node: ast.IfStmt, env: en.Environment, bo: ByteOutput):
        # print(node.condition.lines[0])
        cond_ptr = self.compile_condition(node.condition.lines[0], env, bo)

        else_begin_label = self.memory.generate_label()
        end_label = self.memory.generate_label()

        if_env = en.BlockEnvironment(env)
        else_env = en.BlockEnvironment(env)

        bo.if_zero_goto_l(else_begin_label, cond_ptr)
        self.compile(node.then_block, if_env, bo)
        bo.goto_l(end_label)
        bo.add_label(else_begin_label)
        self.compile(node.else_block, else_env, bo)
        bo.add_label(end_label)

    def compile_for_loop(self, node: ast.ForLoopStmt, env: en.Environment, bo: ByteOutput):
        if len(node.condition.lines) != 3:
            raise lib.CompileTimeException("For loop title must have 3 parts, got {}".format(len(node.condition.lines)))

        body_label = self.memory.generate_label()
        step_label = self.memory.generate_label()
        end_label = self.memory.generate_label()

        title_env = en.LoopEnvironment(env, step_label, end_label)
        body_env = en.BlockEnvironment(title_env)

        self.compile(node.condition.lines[0], title_env, bo)  # start
        bo.add_label(body_label)

        cond_ptr = self.compile_condition(node.condition.lines[1], title_env, bo)

        bo.if_zero_goto_l(end_label, cond_ptr)

        self.compile(node.body, body_env, bo)
        bo.add_label(step_label)
        self.compile(node.condition.lines[2], title_env, bo)  # step

        bo.goto_l(body_label)
        bo.add_label(end_label)

    def compile_while_loop(self, node: ast.WhileStmt, env: en.Environment, bo: ByteOutput):
        if len(node.condition.lines) != 1:
            raise lib.CompileTimeException("While loop title must have 1 part.")

        body_label = self.memory.generate_label()
        step_label = self.memory.generate_label()
        end_label = self.memory.generate_label()

        bo.add_label(body_label)

        title_env = en.LoopEnvironment(env, step_label, end_label)
        body_env = en.BlockEnvironment(title_env)

        cond_ptr = self.compile_condition(node.condition.lines[0], env, bo)
        bo.if_zero_goto_l(end_label, cond_ptr)

        self.compile(node.body, body_env, bo)
        bo.add_label(step_label)

        bo.goto_l(body_label)
        bo.add_label(end_label)

    def compile_condition(self, node: ast.Expr, env: en.Environment, bo: ByteOutput):
        tal = get_tal_of_evaluated_node(node, env)
        if tal.type_name != "int":
            raise lib.CompileTimeException("Conditional statement can only have boolean output. Got '{}'."
                                           .format(tal.type_name))
        return self.compile(node, env, bo)

    def compile_break(self, node: ast.BreakStmt, env: en.Environment, bo: ByteOutput):
        end_label = env.get_end_label()
        bo.goto_l(end_label)

    def compile_continue(self, node: ast.ContinueStmt, env: en.Environment, bo: ByteOutput):
        step_label = env.get_step_label()
        bo.goto_l(step_label)

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
            # if isinstance(tal, en.AbstractFuncType):  # is a method, add pointer to struct as the first parameter
            #     tal.param_types.insert(0, en.Type("*" + node.name))
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

    def compile_goto(self, node: ast.GotoStmt, env: en.Environment, bo: ByteOutput):
        label_id = self.memory.text_labels[node.label]
        bo.goto_l(label_id)

    def compile_label(self, node: ast.LabelStmt, env: en.Environment, bo: ByteOutput):
        label_id = self.memory.text_labels[node.label]
        bo.add_label(label_id)

    def get_unpack_final_pos(self, node: ast.UnaryOperator, env: en.Environment, bo):
        if isinstance(node, ast.UnaryOperator) and node.operation == "unpack":
            return self.get_unpack_final_pos(node.value, env, bo)
        elif isinstance(node, ast.NameNode):
            return env.get(node.name, (node.line_num, node.file), False)
        elif isinstance(node, ast.Expr):
            return self.compile(node, env, bo)
        else:
            raise lib.CompileTimeException()

    def call_compile_time_functions(self, func: int, func_tal: CompileTimeFunctionType, arg_node: ast.BlockStmt,
                                    env: en.Environment, bo: ByteOutput):
        r_len = func_tal.rtype.total_len(self.memory)
        r_ptr = self.memory.allocate(r_len, bo)
        # bo.push_stack(r_len)

        return func_tal.func(r_ptr, env, bo, arg_node.lines)

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

    def function_exit(self, r_ptr: int, env: en.Environment, bo: ByteOutput, args: list):
        arg_len = len(args)
        if arg_len == 0:
            bo.write_one(EXIT)
        elif arg_len == 1:
            arg_ptr = self.compile(args[0], env, bo)
            arg_tal = get_tal_of_evaluated_node(args[0], env)
            if arg_tal.type_name != "int" or en.is_array(arg_tal):
                raise lib.CompileTimeException("Argument of function 'exit' must be int")
            bo.exit_with_value(arg_ptr)
        else:
            raise lib.CompileTimeException("Function 'exit' takes 0 to 1 arguments, {} given."
                                           .format(arg_len))

    def function_new(self, r_ptr: int, env: en.Environment, bo: ByteOutput, args: list):
        lf = (0, "compiler")
        if len(args) != 1:
            raise lib.CompileTimeException("Function 'new' takes exactly 1 argument.")
        arg = args[0]
        struct = self.compile(arg, env, bo)
        if not isinstance(struct, Struct):
            raise lib.CompileTimeException("Argument of 'new' must be struct name.")

        size_ptr = self.memory.allocate(INT_LEN, bo)
        size_ptr = self.function_sizeof(size_ptr, env, bo, args)

        malloc = env.get("malloc", lf, False)
        malloc_tal = env.get_type_arr_len("malloc", lf)
        malloc_rtn = self.native_function_call(malloc, malloc_tal, [(size_ptr, INT_LEN)], env, bo)

        for method_name in struct.method_pointers:
            method_ptr = struct.method_pointers[method_name]
            loc_in_struct = struct.get_attr_pos(method_name)
            # declared_tal = struct.get_attr_tal(method_name)
            # print(actual_tal)
            # print(declared_tal)
            # if actual_tal != declared_tal:
            #     raise lib.CompileTimeException("Method type does not match declared type")

            real_attr_addr = self.memory.allocate(INT_LEN, bo)
            bo.assign(real_attr_addr, malloc_rtn, PTR_LEN)
            bo.op_i(ADD, real_attr_addr, loc_in_struct)
            bo.ptr_assign(real_attr_addr, method_ptr, PTR_LEN)

        return malloc_rtn

    def generate_labels(self, node: ast.Node):
        if isinstance(node, ast.LabelStmt):
            if node.label not in self.memory.text_labels:
                label_id = self.memory.generate_label()
                self.memory.text_labels[node.label] = label_id
        elif isinstance(node, ast.Node):
            attr_names = dir(node)
            for attr_name in attr_names:
                attr = getattr(node, attr_name)
                if isinstance(attr, ast.Node):
                    self.generate_labels(attr)
                elif isinstance(attr, list):
                    for item in attr:
                        self.generate_labels(item)


def index_node_depth(node: ast.IndexingNode):
    if node.call_obj.node_type == ast.INDEXING_NODE:
        return index_node_depth(node.call_obj) + 1
    else:
        return 1


def get_tal_of_defining_node(node: ast.Node, env: en.Environment, mem: MemoryManager) -> en.Type:
    if node.node_type == ast.NAME_NODE:
        node: ast.NameNode
        if node.name == "fn":
            return en.AbstractFuncType()
        else:
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
    elif node.node_type == ast.BINARY_OPERATOR:
        node: ast.BinaryOperator
        if node.operation == "->":
            # print(node.left)
            # print("===================")
            left: ast.BlockStmt = node.left.expr
            lst = []
            for param_t in left.lines:
                p_type = get_tal_of_defining_node(param_t, env, mem)
                lst.append(p_type)
            r_type = get_tal_of_defining_node(node.right, env, mem)
            return en.FuncType(lst, r_type)


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
            # func: Function = env.get_function(call_obj.name, (node.line_num, node.file))
            func_tal: en.FuncType = env.get_type_arr_len(call_obj.name, (node.line_num, node.file))
            return func_tal.rtype
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
        real_l_tal = en.Type(left_tal.type_name[ptr_depth:], left_tal.array_lengths)
        if env.is_struct(real_l_tal.type_name):
            struct = env.get_struct(real_l_tal.type_name)
            if isinstance(node.right, ast.NameNode):
                return struct.get_attr_tal(node.right.name)
            elif isinstance(node.right, ast.FuncCall):
                f_tal: en.FuncType = struct.get_attr_tal(node.right.call_obj.name)
                return f_tal.rtype
            else:
                raise lib.TypeException()
        else:
            raise lib.TypeException()
    elif node.node_type == ast.IN_DECREMENT_OPERATOR:
        node: ast.InDecrementOperator
        return get_tal_of_evaluated_node(node.value, env)
    elif isinstance(node, ast.BlockStmt) and node.standalone:
        ele_tal = get_tal_of_evaluated_node(node.lines[0], env)
        return en.Type(ele_tal.type_name, len(node.lines))
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
