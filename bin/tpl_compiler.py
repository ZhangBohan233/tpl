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

STOP = 2  # STOP                                  | stop current process
ASSIGN = 3  # ASSIGN   TARGET    SOURCE   LENGTH    | copy LENGTH bytes from SOURCE to TARGET
CALL = 4  # CALL
RETURN = 5  # RETURN   VALUE_PTR
GOTO = 6  # JUMP       CODE_PTR
PUSH = 7  # PUSH
LOAD = 8  # LOAD     %DES_REG   $ADDR                   |
STORE = 9  # STORE   %TEMP   %REG   $DES_ADDR
# ASSIGN_I = 8  # A      PTR       REAL VALUE         | store the real value in PTR
# ASSIGN_B = 9
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
CAST_INT = 24  # CAST_INT  RESULT_P  SRC_P              | cast int-like to int

IF_ZERO_GOTO = 30  # IF0  SKIP  SRC_PTR
CALL_NAT = 31
STORE_ADDR = 32
UNPACK_ADDR = 33
PTR_ASSIGN = 34  # | assign the addr stored in ptr with the value stored in right
STORE_SP = 35
RES_SP = 36
# TO_REL = 37  # | transform absolute addr to
# ADD_I = 38       # | add with real value
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

NATIVE_FUNCTION_COUNT = 5

INT_RESULT_TABLE_INT = {
    "+": ADD,
    "-": SUB,
    "*": MUL,
    "/": DIV,
    "%": MOD,
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
    "%=": MOD
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

EXTENDED_FLOAT_RESULT_TABLE_FLOAT = {
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

        self.write_one(LOAD_I)
        self.write_one(reg1)
        self.write_int(tar)

        self.write_one(LOAD_I)
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
            ptr = self.manager.allocate(arg[1])
            self.push_stack(arg[1])

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

        self.write_one(LOAD_I)
        self.write_one(reg1)
        self.write_int(des)

        self.write_one(LOAD_I)
        self.write_one(reg2)
        self.write_int(rel_value)

        self.write_one(STORE_ADDR)
        self.write_one(reg1)
        self.write_one(reg2)

        self.manager.append_regs64(reg2, reg1)

    def unpack_addr(self, des: int, addr_ptr: int, length: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD_I)
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

        self.write_one(LOAD_I)
        self.write_one(reg2)
        self.write_int(right)

        self.write_one(LOAD_I)
        self.write_one(reg3)
        self.write_int(length)

        self.write_one(PTR_ASSIGN)
        self.write_one(reg1)
        self.write_one(reg2)
        self.write_one(reg3)

        self.manager.append_regs64(reg3, reg2, reg1)

    def cast_to_int(self, tar: int, src: int, src_len: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD_I)
        self.write_one(reg1)
        self.write_int(tar)

        self.write_one(LOAD_I)
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

    def add_binary_op_int(self, op: int, res: int, left: int, right: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD)
        self.write_one(reg1)
        self.write_int(left)

        self.write_one(LOAD)
        self.write_one(reg2)
        self.write_int(right)

        self.write_one(op)
        self.write_one(reg1)
        self.write_one(reg2)

        self.write_one(STORE)
        self.write_one(reg3)
        self.write_one(reg1)
        self.write_int(res)

        self.manager.append_regs64(reg3, reg2, reg1)

    def add_unary_op_int(self, op: int, res: int, value: int):
        reg1, reg2 = self.manager.require_regs64(2)

        self.write_one(LOAD)
        self.write_one(reg1)
        self.write_int(value)

        self.write_one(op)
        self.write_one(reg1)

        self.write_one(STORE)
        self.write_one(reg2)
        self.write_one(reg1)
        self.write_int(res)

        self.manager.append_regs64(reg2, reg1)

    def add_return(self, src, total_len):
        reg1, reg2 = self.manager.require_regs64(2)

        self.write_one(LOAD_I)
        # self.write_one(reg3)
        self.write_one(reg1)  # return ptr
        self.write_int(src)

        self.write_one(LOAD_I)
        self.write_one(reg2)  # return length
        self.write_int(total_len)

        self.write_one(RETURN)
        self.write_one(reg1)
        self.write_one(reg2)

        self.manager.append_regs64(reg2, reg1)

    # def add_to_rel_addr(self, addr_addr: int):
    #     self.write_one(TO_REL)
    #     self.write_int(addr_addr)

    def op_i(self, op_code, operand_addr, adder_value: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD_I)
        self.write_one(reg1)  # right
        self.write_int(adder_value)

        self.write_one(LOAD)
        self.write_one(reg2)  # left
        self.write_int(operand_addr)

        self.write_one(op_code)
        self.write_one(reg2)
        self.write_one(reg1)

        self.write_one(STORE)
        self.write_one(reg3)
        self.write_one(reg2)
        self.write_int(operand_addr)

        self.manager.append_regs64(reg3, reg2, reg1)

    def if_zero_goto(self, offset: int, cond_ptr: int):
        reg1, reg2, reg3 = self.manager.require_regs64(3)

        self.write_one(LOAD_I)
        self.write_one(reg1)  # reg stores skip len
        self.write_int(offset)

        self.write_one(LOAD)
        self.write_one(reg2)  # reg stores cond ptr
        self.write_int(cond_ptr)

        self.write_one(IF_ZERO_GOTO)
        self.write_one(reg1)
        self.write_one(reg2)

        self.manager.append_regs64(reg3, reg2, reg1)

    def goto(self, offset: int):
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
        return self.step_node, self.cond_len + len(self) + INT_LEN * 2 + 1


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
        self.gp = self.global_begins + INT_LEN

        self.literal = literal_bytes
        self.global_bytes = bytearray(INT_LEN)  # function counts
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

    def require_regs64(self, count):
        return [self.available_regs64.pop() for _ in range(count)]

    def append_regs64(self, *regs):
        for reg in regs:
            self.available_regs64.append(reg)

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

    def allocate(self, length) -> int:
        if len(self.blocks) == 0:  # global
            ptr = self.sp
        else:  # in call
            ptr = self.sp - self.blocks[-1]
        self.sp += length
        return ptr

    def calculate_lit_ptr(self, lit_num):
        return lit_num + self.literal_begins

    def get_last_call(self):
        return self.blocks[-1]

    def compile_all_functions(self):
        # print(self.functions)
        self.global_bytes[0:INT_LEN] = typ.int_to_bytes(len(self.functions))
        for ptr in self.functions:
            fb = self.functions[ptr]
            ptr_in_g = ptr - self.global_begins
            self.global_bytes[ptr_in_g: ptr_in_g + PTR_LEN] = typ.int_to_bytes(self.gp)
            self.global_bytes.extend(fb)
            self.gp += len(fb)

    def define_func_ptr(self):
        i = self.gp
        self.global_bytes.extend(bytes(PTR_LEN))
        self.gp += PTR_LEN
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
    def __init__(self, literal_bytes: bytes):
        self.memory = MemoryManager(literal_bytes)

        self.modified_string_poses = set()

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

    def add_compile_time_functions(self, env: en.GlobalEnvironment):
        env.define_function("sizeof", CompileTimeFunction(en.Type("int"), self.function_sizeof))
        env.define_function("int", CompileTimeFunction(en.Type("int"), self.function_int))
        env.define_function("float", CompileTimeFunction(en.Type("float"), self.function_float))

    def compile_all(self, root: ast.Node) -> bytes:
        bo = ByteOutput(self.memory)

        env = en.GlobalEnvironment()
        self.add_native_functions(env)
        self.add_compile_time_functions(env)

        # print(self.memory.global_bytes)

        self.compile(root, env, bo)
        self.memory.compile_all_functions()

        if "main" in env.functions:
            main_ptr = env.functions["main"]
            self.function_call(main_ptr, [], env, bo)

        # print(self.memory.global_bytes)
        lit_and_global = ByteOutput(self.memory)
        lit_and_global.write_int(STACK_SIZE)
        lit_and_global.write_int(len(self.memory.literal))
        lit_and_global.write_int(len(self.memory.global_bytes))
        lit_and_global.codes.extend(self.memory.literal)
        lit_and_global.codes.extend(self.memory.global_bytes)
        lit_and_global.codes.extend(bo.codes)
        # print(self.memory.global_bytes)
        return bytes(lit_and_global)

    def compile(self, node: ast.Node, env: en.Environment, bo: ByteOutput):
        if node is None:
            return 0
        nt = node.node_type
        cmp_ftn = self.node_table[nt]
        return cmp_ftn(node, env, bo)

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
        r_tal = get_tal_of_defining_node(node.r_type, env, self.memory)

        scope = en.FunctionEnvironment(env)
        self.memory.push_stack()

        param_pairs = []
        for param in node.params.lines:
            tn: ast.TypeNode = param
            name_node: ast.NameNode = tn.left
            tal = get_tal_of_defining_node(tn.right, env, self.memory)
            total_len = tal.total_len(self.memory)

            ptr = self.memory.allocate(total_len)

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

        self.memory.restore_stack()
        # print(ftn_ptr)

        # ftn = Function(param_pairs, r_tal, ftn_ptr)
        # env.define_function(node.name, ftn)

    def compile_name_node(self, node: ast.NameNode, env: en.Environment, bo: ByteOutput):
        lf = node.line_num, node.file
        ptr = env.get(node.name, lf)
        return ptr

    def compile_quick_assignment(self, node: ast.QuickAssignmentNode, env: en.Environment, bo: ByteOutput):
        name: str = node.left.name
        tal = get_tal_of_evaluated_node(node.right, env)
        length = tal.total_len(self.memory)
        r_ptr = self.memory.allocate(length)
        bo.push_stack(length)
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
                ptr = env.get(node.left.name, lf)
                total_len = tal.total_len(self.memory)

                bo.assign(ptr, r, total_len)

        elif node.left.node_type == ast.TYPE_NODE:  # define
            type_node: ast.TypeNode = node.left
            if node.level == ast.VAR:
                tal = get_tal_of_defining_node(type_node.right, env, self.memory)
                total_len = tal.total_len(self.memory)
                # print(total_len)

                if total_len == 0:  # pull the right
                    tal = get_tal_of_evaluated_node(node.right, env)
                    total_len = tal.total_len(self.memory)
                    # print(total_len)

                if en.is_pointer(tal):
                    assert total_len == PTR_LEN
                    ptr = self.memory.allocate(PTR_LEN)
                    bo.push_stack(PTR_LEN)

                    r = self.compile(node.right, env, bo)

                    bo.assign(ptr, r, PTR_LEN)
                elif en.is_array(tal):  # right cannot be binary operator
                    if len(tal.array_lengths) > 1:
                        raise lib.CompileTimeException("High dimensional array not supported")
                    ptr = self.memory.allocate(PTR_LEN)
                    bo.push_stack(PTR_LEN)
                    arr_ptr = self.memory.allocate(total_len)
                    # print(total_len)
                    bo.push_stack(total_len)
                    bo.store_addr_to_des(ptr, arr_ptr)

                    r = self.compile(node.right, env, bo)

                    if r != 0:  # preset array
                        # bo.ptr_assign(arr_ptr, r, total_len)
                        bo.unpack_addr(arr_ptr, r, total_len)
                        # bo.assign(arr_ptr, r, total_len)
                    # print(ptr)
                else:
                    ptr = self.memory.allocate(total_len)
                    bo.push_stack(total_len)

                    r = self.compile(node.right, env, bo)

                    bo.assign(ptr, r, total_len)

                env.define_var(type_node.left.name, tal, ptr)

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

    def compile_setitem(self, node: ast.IndexingNode, value_ptr: int, env: en.Environment, bo: ByteOutput):
        indexing_ptr, unit_len = self.get_indexing_ptr_and_unit_len(node, env, bo)

        bo.ptr_assign(indexing_ptr, value_ptr, unit_len)

    def compile_getitem(self, node: ast.IndexingNode, env: en.Environment, bo: ByteOutput):
        indexing_ptr, unit_len = self.get_indexing_ptr_and_unit_len(node, env, bo)

        result_ptr = self.memory.allocate(unit_len)
        bo.push_stack(unit_len)
        bo.unpack_addr(result_ptr, indexing_ptr, unit_len)
        return result_ptr

    def compile_attr_assign(self, node: ast.Dot, value_ptr: int, env: en.Environment, bo: ByteOutput):
        attr_addr, length = self.get_struct_attr_ptr_and_len(node, env, bo)

        bo.ptr_assign(attr_addr, value_ptr, length)

    def compile_dot(self, node: ast.Dot, env: en.Environment, bo: ByteOutput):
        attr_addr, length = self.get_struct_attr_ptr_and_len(node, env, bo)

        res_ptr = self.memory.allocate(length)
        bo.push_stack(length)

        bo.unpack_addr(res_ptr, attr_addr, length)
        # print(res_ptr, attr_addr, length)
        return res_ptr

    def get_indexing_ptr_and_unit_len(self, node: ast.IndexingNode, env: en.Environment, bo: ByteOutput):
        if isinstance(node.call_obj, ast.IndexingNode):
            raise lib.CompileTimeException("High dimensional indexing not supported")
        obj_tal = get_tal_of_evaluated_node(node.call_obj, env)
        unit_len = obj_tal.unit_len(self.memory)
        index_ptr = self.compile(node.arg.lines[0], env, bo)
        unit_len_ptr = self.memory.allocate(INT_LEN)
        bo.push_stack(INT_LEN)
        bo.assign_i(unit_len_ptr, unit_len)
        indexing_ptr = self.memory.allocate(INT_LEN)
        bo.push_stack(INT_LEN)
        bo.add_binary_op_int(MUL, indexing_ptr, index_ptr, unit_len_ptr)
        array_ptr = self.compile(node.call_obj, env, bo)
        bo.add_binary_op_int(ADD, indexing_ptr, array_ptr, indexing_ptr)

        return indexing_ptr, unit_len

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
            addr_ptr = self.memory.allocate(PTR_LEN)
            bo.push_stack(PTR_LEN)
            bo.store_addr_to_des(addr_ptr, struct_ptr + attr_pos)
            return addr_ptr, attr_len
        elif node.dot_count == 2:
            # print(struct_ptr)
            real_addr_ptr = self.memory.allocate(PTR_LEN)
            bo.push_stack(PTR_LEN)
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

    def function_call(self, func: Function, args: list, call_env: en.Environment, bo: ByteOutput):
        if len(args) != len(func.params):
            raise lib.CompileTimeException("Function requires {} arguments, {} given"
                                           .format(len(func.params), len(args)))

        r_len = func.r_tal.total_len(self.memory)

        r_ptr = self.memory.allocate(r_len)
        bo.push_stack(r_len)

        bo.call(False, func.ptr, args)

        return r_ptr

    def native_function_call(self, func: NativeFunction, args: list, call_env, bo: ByteOutput):
        r_len = func.r_tal.total_len(self.memory)

        r_ptr = self.memory.allocate(r_len)
        bo.push_stack(r_len)

        bo.call(True, func.ptr, args)

        return r_ptr

    def compile_unary_op(self, node: ast.UnaryOperator, env: en.Environment, bo: ByteOutput):
        if node.operation == "pack":
            num_ptr = self.compile(node.value, env, bo)
            ptr_ptr = self.memory.allocate(PTR_LEN)
            bo.push_stack(PTR_LEN)
            # bo.assign_i(ptr_ptr, num_ptr)
            bo.store_addr_to_des(ptr_ptr, num_ptr)
            return ptr_ptr
        elif node.operation == "unpack":
            orig_tal = get_tal_of_evaluated_node(node, env)
            total_len = orig_tal.total_len(self.memory)
            ptr_ptr = self.compile(node.value, env, bo)
            # print(total_len)
            num_ptr = self.memory.allocate(total_len)
            # print(num_ptr)
            bo.push_stack(total_len)
            bo.unpack_addr(num_ptr, ptr_ptr, total_len)
            return num_ptr
        elif node.operation == "!":
            v_tal = get_tal_of_evaluated_node(node.value, env)
            if v_tal.total_len(self.memory) != INT_LEN:
                raise lib.CompileTimeException()
            vp = self.compile(node.value, env, bo)
            res_ptr = self.memory.allocate(INT_LEN)
            bo.push_stack(INT_LEN)
            bo.add_unary_op_int(NOT, res_ptr, vp)
            return res_ptr
        elif node.operation == "neg":
            v_tal = get_tal_of_evaluated_node(node.value, env)
            vp = self.compile(node.value, env, bo)
            if v_tal.type_name == "int":
                res_ptr = self.memory.allocate(INT_LEN)
                bo.push_stack(INT_LEN)
                bo.add_unary_op_int(NEG, res_ptr, vp)
                return res_ptr
            elif v_tal.type_name == "char":  # TODO: May contain bugs
                res_ptr = self.memory.allocate(CHAR_LEN)
                bo.push_stack(CHAR_LEN)
                trans_ptr = self.memory.allocate(INT_LEN)
                bo.push_stack(INT_LEN)
                bo.cast_to_int(trans_ptr, vp, CHAR_LEN)
                bo.add_unary_op_int(NEG, res_ptr, trans_ptr)
                return res_ptr
            elif v_tal.type_name == "float":
                res_ptr = self.memory.allocate(FLOAT_LEN)
                bo.push_stack(FLOAT_LEN)
                bo.add_unary_op_int(NEG_F, res_ptr, vp)
                return res_ptr
            else:
                raise lib.CompileTimeException("Cannot take negation of type '{}'".format(v_tal.type_name))
        else:  # normal unary operators
            raise lib.CompileTimeException("Not implemented")

    def compile_binary_op(self, node: ast.BinaryOperator, env: en.Environment, bo: ByteOutput):
        l_tal = get_tal_of_evaluated_node(node.left, env)
        r_tal = get_tal_of_evaluated_node(node.right, env)
        # print(l_tal, r_tal, node.operation)
        if l_tal.type_name == "int" or l_tal.type_name[0] == "*" or en.is_array(l_tal):
            lp = self.compile(node.left, env, bo)
            rp = self.compile(node.right, env, bo)
            if r_tal.type_name == "float":
                rip = self.memory.allocate(FLOAT_LEN)
                bo.push_stack(FLOAT_LEN)
                bo.float_to_int(rip, rp)
                rp = rip
            elif r_tal.type_name != "int" and r_tal.type_name[0] != "*":
                rip = self.memory.allocate(INT_LEN)
                bo.push_stack(INT_LEN)
                bo.cast_to_int(rip, rp, r_tal.total_len(self.memory))
                rp = rip

            return self.binary_op_int(node.operation, lp, rp, bo)

        elif l_tal.type_name == "char":
            lp = self.compile(node.left, env, bo)
            rp = self.compile(node.right, env, bo)

            lip = self.memory.allocate(INT_LEN)
            bo.push_stack(INT_LEN)
            bo.cast_to_int(lip, lp, CHAR_LEN)

            if r_tal.type_name == "float":
                rip = self.memory.allocate(FLOAT_LEN)
                bo.push_stack(FLOAT_LEN)
                bo.float_to_int(rip, rp)
            elif r_tal.type_name != "int":
                rip = self.memory.allocate(INT_LEN)
                bo.push_stack(INT_LEN)
                bo.cast_to_int(rip, rp, r_tal.total_len(self.memory))
            else:
                rip = rp

            return self.binary_op_int(node.operation, lip, rip, bo)

        elif l_tal.type_name == "float":
            lp = self.compile(node.left, env, bo)
            rp = self.compile(node.right, env, bo)

            if r_tal.type_name != "float":
                if r_tal.type_name == "int":
                    rip = rp
                else:
                    rip = self.memory.allocate(INT_LEN)
                    bo.push_stack(INT_LEN)
                    bo.cast_to_int(rip, rp, r_tal.total_len(self.memory))
                rfp = self.memory.allocate(FLOAT_LEN)
                bo.push_stack(FLOAT_LEN)
                bo.int_to_float(rfp, rip)
                rp = rfp

            return self.binary_op_float(node.operation, lp, rp, bo)

        raise lib.CompileTimeException("Unsupported binary operation '{}'".format(node.operation))

    def binary_op_float(self, op: str, lp: int, rp: int, bo: ByteOutput) -> int:
        if op in EXTENDED_FLOAT_RESULT_TABLE_FLOAT:
            if op in FLOAT_RESULT_TABLE_FLOAT:
                res_pos = self.memory.allocate(FLOAT_LEN)
                bo.push_stack(FLOAT_LEN)

                op_code = FLOAT_RESULT_TABLE_FLOAT[op]
                bo.add_binary_op_int(op_code, res_pos, lp, rp)
                return res_pos
            else:
                op_code = EXTENDED_FLOAT_RESULT_TABLE_FLOAT[op]
                bo.add_binary_op_int(op_code, lp, lp, rp)
                return lp
        elif op in EXTENDED_INT_RESULT_TABLE_FLOAT:
            res_pos = self.memory.allocate(INT_LEN)
            bo.push_stack(INT_LEN)

            if op in INT_RESULT_TABLE_FLOAT:
                op_code = INT_RESULT_TABLE_FLOAT[op]
                bo.add_binary_op_int(op_code, res_pos, lp, rp)
                return res_pos
            else:
                op_tup = EXTENDED_INT_RESULT_TABLE_FLOAT[op]
                l_res = self.memory.allocate(INT_LEN)
                bo.push_stack(INT_LEN)
                r_res = self.memory.allocate(INT_LEN)
                bo.push_stack(INT_LEN)
                bo.add_binary_op_int(op_tup[0], l_res, lp, rp)
                bo.add_binary_op_int(op_tup[1], r_res, lp, rp)
                bo.add_binary_op_int(OR, res_pos, l_res, r_res)
                return res_pos

    def binary_op_int(self, op: str, lp: int, rp: int, bo: ByteOutput) -> int:
        if op in INT_RESULT_TABLE_INT_FULL:
            if op in INT_RESULT_TABLE_INT:
                res_pos = self.memory.allocate(INT_LEN)
                bo.push_stack(INT_LEN)

                op_code = INT_RESULT_TABLE_INT[op]
                bo.add_binary_op_int(op_code, res_pos, lp, rp)
                return res_pos
            else:
                op_code = INT_RESULT_TABLE_INT_FULL[op]
                bo.add_binary_op_int(op_code, lp, lp, rp)
                return lp
        elif op in EXTENDED_INT_RESULT_TABLE_INT:
            res_pos = self.memory.allocate(INT_LEN)
            bo.push_stack(INT_LEN)

            # if op in BOOL_RESULT_TABLE_INT:
            #     op_code = BOOL_RESULT_TABLE_INT[op]
            #     bo.add_binary_op_int(op_code, res_pos, lp, rp)
            #     return res_pos
            # else:
            op_tup = EXTENDED_INT_RESULT_TABLE_INT[op]
            l_res = self.memory.allocate(INT_LEN)
            bo.push_stack(INT_LEN)
            r_res = self.memory.allocate(INT_LEN)
            bo.push_stack(INT_LEN)
            bo.add_binary_op_int(op_tup[0], l_res, lp, rp)
            bo.add_binary_op_int(op_tup[1], r_res, lp, rp)
            bo.add_binary_op_int(OR, res_pos, l_res, r_res)
            return res_pos

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

        self.memory.store_sp()
        bo.write_one(STORE_SP)  # before loop

        loop_indicator = self.memory.allocate(INT_LEN)
        bo.push_stack(INT_LEN)
        bo.assign_i(loop_indicator, 1)

        title_env = en.LoopEnvironment(env)
        body_env = en.BlockEnvironment(title_env)

        self.compile(node.condition.lines[0], title_env, bo)  # start

        init_len = len(bo)

        self.memory.store_sp()
        bo.write_one(STORE_SP)
        cond_ptr = self.compile_condition(node.condition.lines[1], title_env, bo)

        real_cond_ptr = self.memory.allocate(INT_LEN)
        bo.push_stack(INT_LEN)
        bo.add_binary_op_int(AND, real_cond_ptr, cond_ptr, loop_indicator)

        cond_len = len(bo) - init_len

        body_bo = LoopByteOutput(self.memory, loop_indicator, cond_len, node.condition.lines[2])

        self.compile(node.body, body_env, body_bo)
        self.compile(node.condition.lines[2], title_env, body_bo)  # step
        body_bo.write_one(RES_SP)

        body_len = len(body_bo) + 10 + 2  # load_i(10), goto(2)

        bo.if_zero_goto(body_len, real_cond_ptr)

        body_bo.goto(-body_len - cond_len - 10 - 10 - 3)  # the length of if_zero_goto(3), load_i(10), load(10)

        bo.codes.extend(body_bo.codes)
        # print(len(bo) - body_len - cond_len, init_len)
        bo.write_one(RES_SP)
        self.memory.restore_sp()
        bo.write_one(RES_SP)
        self.memory.restore_sp()

    def compile_while_loop(self, node: ast.WhileStmt, env: en.Environment, bo: ByteOutput):
        if len(node.condition.lines) != 1:
            raise lib.CompileTimeException("While loop title must have 1 part.")

        self.memory.store_sp()  # 进loop之前
        bo.write_one(STORE_SP)

        loop_indicator = self.memory.allocate(INT_LEN)
        bo.push_stack(INT_LEN)
        bo.assign_i(loop_indicator, 1)

        init_len = len(bo)
        self.memory.store_sp()  # 循环开始
        bo.write_one(STORE_SP)

        title_env = en.LoopEnvironment(env)
        body_env = en.BlockEnvironment(title_env)

        cond_ptr = self.compile_condition(node.condition.lines[0], env, bo)

        real_cond_ptr = self.memory.allocate(INT_LEN)
        bo.push_stack(INT_LEN)
        bo.add_binary_op_int(AND, real_cond_ptr, cond_ptr, loop_indicator)

        cond_len = len(bo) - init_len

        body_bo = LoopByteOutput(self.memory, loop_indicator, cond_len, None)

        self.compile(node.body, body_env, body_bo)
        # self.memory.restore_sp()
        body_bo.write_one(RES_SP)
        body_len = len(body_bo) + 10 + 2  # load_i(10), goto(2)

        bo.if_zero_goto(body_len, real_cond_ptr)

        body_bo.goto(-body_len - cond_len - 10 - 10 - 3)  # the length of if_zero_goto(3), load_i(10), load(10)

        bo.codes.extend(body_bo.codes)
        # print(len(bo) - body_len - cond_len, init_len)
        self.memory.restore_sp()
        bo.write_one(RES_SP)

        self.memory.restore_sp()
        bo.write_one(RES_SP)

    def compile_condition(self, node: ast.Expr, env: en.Environment, bo: ByteOutput):
        tal = get_tal_of_evaluated_node(node, env)
        if tal.type_name != "int":
            raise lib.CompileTimeException("Conditional statement can only have boolean output. Got '{}'."
                                           .format(tal.type_name))
        return self.compile(node, env, bo)

    def compile_break(self, node: ast.BreakStmt, env: en.Environment, bo: ByteOutput):
        loop_indicator = bo.get_loop_indicator()
        bo.assign_i(loop_indicator, 0)
        self.compile_continue(None, env, bo)

    def compile_continue(self, node: ast.ContinueStmt, env: en.Environment, bo: ByteOutput):
        step_node, length_before = bo.get_loop_length()

        cur_len = len(bo)
        self.compile(step_node, env, bo)
        len_diff = len(bo) - cur_len

        bo.write_one(GOTO)
        bo.write_int(-length_before - len_diff - INT_LEN - 1)

    def compile_undefined(self, node: ast.UndefinedNode, env: en.Environment, bo: ByteOutput):
        return 0

    def compile_null(self, node, env, bo: ByteOutput):
        null_ptr = self.memory.allocate(PTR_LEN)
        bo.push_stack(PTR_LEN)
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
        ptr = self.compile(node.value, env, bo)
        tal = get_tal_of_evaluated_node(node.value, env)
        if node.is_post:
            if node.operation == "++":
                if tal.type_name == "int":
                    r_ptr = self.memory.allocate(INT_LEN)
                    bo.push_stack(INT_LEN)
                    bo.assign(r_ptr, ptr, INT_LEN)
                    bo.op_i(ADD, ptr, 1)
                    return r_ptr
            elif node.operation == "--":
                if tal.type_name == "int":
                    r_ptr = self.memory.allocate(INT_LEN)
                    bo.push_stack(INT_LEN)
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
            return env.get(node.name, (node.line_num, node.file))
        elif isinstance(node, ast.Expr):
            return self.compile(node, env, bo)
        else:
            raise lib.CompileTimeException()

    def call_compile_time_functions(self, func: CompileTimeFunction, arg_node: ast.BlockStmt, env: en.Environment,
                                    bo: ByteOutput):
        r_len = func.r_tal.total_len(self.memory)
        r_ptr = self.memory.allocate(r_len)
        bo.push_stack(r_len)

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


def pointer_depth(type_name: str) -> int:
    for i in range(len(type_name)):
        if type_name[i] != "*":
            return i
    raise lib.CompileTimeException()


def generate_lf(node: ast.Node) -> str:
    return "In file '{}', at line {}.".format(node.file, node.line_num)
