import bin.spl_ast as ast
import bin.spl_environment as en
import bin.spl_types as typ
import bin.spl_lib as lib

INT_LEN = 8
FLOAT_LEN = 8
PTR_LEN = 8
BOOLEAN_LEN = 1
CHAR_LEN = 1
VOID_LEN = 0

STOP = 2  # STOP                                  | stop current process
ASSIGN = 3  # ASSIGN   TARGET    SOURCE   LENGTH    | copy LENGTH bytes from SOURCE to TARGET
CALL = 4  # CALL
RETURN = 5  # RETURN   VALUE_PTR
GOTO = 6  # JUMP       CODE_PTR
PUSH = 7  # PUSH
ASSIGN_I = 8  # A      PTR       REAL VALUE         | store the real value in PTR
ADD_I = 10  # ADD_I    RESULT_P  LEFT_P   RIGHT_P   | add the ints pointed by pointers, store the result to RESULT_P
CAST_I = 11  # CAST_I                               | cast to int
SUB_I = 12
MUL_I = 13
DIV_I = 14
MOD_I = 15
EQ_I = 16  # EQ       RES PTR   LEFT_P   RIGHT_P   | set RES PTR to 0 if LEFT_P == RIGHT_P
GT_I = 17  # GT
LT_I = 18
AND = 19
OR = 20
IF_ZERO_GOTO = 30
# IF_ZERO   GOTO      VALUE_P            | if VALUE P is 0 then goto
CALL_NAT = 31
STORE_ADDR = 32
UNPACK_ADDR = 33
PTR_ASSIGN = 34  # | assign the addr stored in ptr with the value stored in right
STORE_SP = 35
RES_SP = 36

INT_RESULT_TABLE_INT = {
    "+": ADD_I,
    "-": SUB_I,
    "*": MUL_I,
    "/": DIV_I,
    "%": MOD_I
}

BOOL_RESULT_TABLE_INT = {
    ">": GT_I,
    "==": EQ_I,
    "<": LT_I
}

EXTENDED_BOOL_RESULT_TABLE_INT = {
    **BOOL_RESULT_TABLE_INT,
    ">=": (GT_I, EQ_I),
    "<=": (LT_I, EQ_I)
}

BOOL_RESULT_TABLE_BOOL = {
    "&&": AND,
    "||": OR
}


class ByteOutput:
    def __init__(self):
        self.codes = bytearray()

    def __len__(self):
        return len(self.codes)

    def __bytes__(self):
        return bytes(self.codes)

    def write_one(self, b):
        self.codes.append(b)

    def push_stack(self, value: int):
        self.write_one(PUSH)
        self.write_int(value)

    def assign(self, tar: int, src: int, length: int):
        # print("assign", tar, src, length)
        self.codes.append(ASSIGN)
        self.write_int(tar)
        self.write_int(src)
        self.write_int(length)

    def assign_i(self, des: int, real_value: int):
        self.write_one(ASSIGN_I)
        self.write_int(des)
        self.write_int(real_value)

    def unpack_addr(self, des: int, addr_ptr: int, length: int):
        self.write_one(UNPACK_ADDR)
        self.write_int(des)
        self.write_int(addr_ptr)
        self.write_int(length)

    def ptr_assign(self, des_ptr: int, right: int, length: int):
        self.write_one(PTR_ASSIGN)
        self.write_int(des_ptr)
        self.write_int(right)
        self.write_int(length)

    def cast_to_int(self, tar: int, src: int):
        self.write_one(CAST_I)
        self.write_int(tar)
        self.write_int(src)

    def add_binary_op_int(self, op: int, res: int, left: int, right: int):
        self.write_one(op)
        self.write_int(res)
        self.write_int(left)
        self.write_int(right)

    # def add_binary_op_bool(self, op: int, res: int, left: int, right: int):
    #     self.write_one(op)

    def add_return(self, src, total_len):
        self.codes.append(RETURN)
        self.write_int(src)
        self.write_int(total_len)

    def write_int(self, i):
        self.codes.extend(typ.int_to_bytes(i))

    def reserve_space(self, n) -> int:
        i = len(self.codes)
        self.codes.extend(bytes(n))
        return i

    def set_bytes(self, from_: int, b: bytes):
        self.codes[from_: from_ + len(b)] = b


class MemoryManager:
    def __init__(self, literal_bytes):
        self.stack_begin = 1
        self.sp = 1
        self.literal_begins = 1024
        self.global_begins = 1024 + len(literal_bytes)
        self.gp = self.global_begins

        self.literal = literal_bytes
        self.global_bytes = bytearray()
        # self.functions = {}

        self.blocks = []

        self.type_sizes = {
            "int": INT_LEN,
            "float": FLOAT_LEN,
            "char": CHAR_LEN,
            "boolean": BOOLEAN_LEN,
            "void": VOID_LEN
        }
        self.pointer_length = PTR_LEN

    def get_type_size(self, name):
        if name[0] == "*":  # is a pointer
            return self.pointer_length
        return self.type_sizes[name]

    def push_stack(self):
        self.blocks.append(self.sp)

    def restore_stack(self):
        self.sp = self.blocks.pop()

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

    def define_func(self, fn_bytes: bytes):
        i = self.gp
        self.global_bytes.extend(fn_bytes)
        self.gp += len(fn_bytes)
        return i


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


class Compiler:
    def __init__(self, literal_bytes: bytes):
        self.memory = MemoryManager(literal_bytes)
        self.literal_bytes = literal_bytes

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
            ast.INDEXING_NODE: self.compile_getitem
        }

    def add_native_functions(self, env: en.GlobalEnvironment):
        p1 = self.memory.define_func(typ.int_to_bytes(1))  # 1: clock
        env.define_function("clock", NativeFunction(en.Type("int"), p1))
        p2 = self.memory.define_func(typ.int_to_bytes(2))  # 2: malloc
        env.define_function("malloc", NativeFunction(en.Type("*void"), p2))
        p3 = self.memory.define_func(typ.int_to_bytes(3))  # 3: printf
        env.define_function("printf", NativeFunction(en.Type("void"), p3))
        p4 = self.memory.define_func(typ.int_to_bytes(4))  # 3: mem_copy
        env.define_function("mem_copy", NativeFunction(en.Type("void"), p4))
        p5 = self.memory.define_func(typ.int_to_bytes(5))  # 3: free
        env.define_function("free", NativeFunction(en.Type("void"), p5))

    def compile_all(self, root: ast.Node) -> bytes:
        bo = ByteOutput()

        env = en.GlobalEnvironment()
        self.add_native_functions(env)

        # print(self.memory.global_bytes)

        self.compile(root, env, bo)

        if "main" in env.functions:
            main_ptr = env.functions["main"]
            self.function_call(main_ptr, [], env, bo)

        print(self.memory.global_bytes)
        lit_and_global = ByteOutput()
        lit_and_global.write_int(len(self.literal_bytes))
        lit_and_global.write_int(len(self.memory.global_bytes))
        lit_and_global.codes.extend(self.literal_bytes)
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
        # print(self.literal_bytes)
        # print(node.literal)
        # print(node.byte_length)
        return self.compile(node.literal, env, bo)

    def compile_def_stmt(self, node: ast.DefStmt, env: en.Environment, bo: ByteOutput):
        r_tal = get_tal_of_defining_node(node.r_type, env, self.memory)

        inner_bo = ByteOutput()
        scope = en.FunctionEnvironment(env)
        self.memory.push_stack()

        param_pairs = []
        for param in node.params.lines:
            tn: ast.TypeNode = param
            name_node: ast.NameNode = tn.left
            tal = get_tal_of_defining_node(tn.right, env, self.memory)
            total_len = tal.total_len(self.memory)

            ptr = self.memory.allocate(total_len)
            # print(ptr)
            # inner_bo.push_stack(total_len)

            scope.define_var(name_node.name, tal, ptr)

            param_pair = ParameterPair(name_node.name, tal)
            param_pairs.append(param_pair)

        fake_ftn_ptr = self.memory.define_func(bytes(0))  # pre-defined for recursion
        # print("allocated to", fake_ftn_ptr, self.memory.global_bytes)
        fake_ftn = Function(param_pairs, r_tal, fake_ftn_ptr)
        env.define_function(node.name, fake_ftn)

        self.compile(node.body, scope, inner_bo)

        self.memory.restore_stack()
        inner_bo.write_one(STOP)

        ftn_ptr = self.memory.define_func(bytes(inner_bo))

        assert fake_ftn_ptr == ftn_ptr
        # print(ftn_ptr)

        ftn = Function(param_pairs, r_tal, ftn_ptr)
        env.define_function(node.name, ftn)

    def compile_name_node(self, node: ast.NameNode, env: en.Environment, bo: ByteOutput):
        lf = node.line_num, node.file
        ptr = env.get(node.name, lf)
        return ptr

    def compile_assignment_node(self, node: ast.AssignmentNode, env: en.Environment, bo: ByteOutput):
        r = self.compile(node.right, env, bo)
        lf = node.line_num, node.file

        if node.left.node_type == ast.NAME_NODE:  # assign
            if node.level == ast.ASSIGN:
                ptr = env.get(node.left.name, lf)
                tal = get_tal_of_evaluated_node(node.left, env)
                total_len = tal.total_len(self.memory)

                bo.assign(ptr, r, total_len)

        elif node.left.node_type == ast.TYPE_NODE:  # define
            type_node: ast.TypeNode = node.left
            if node.level == ast.VAR:
                tal = get_tal_of_defining_node(type_node.right, env, self.memory)
                total_len = tal.total_len(self.memory)

                if total_len == 0:  # pull the right
                    tal = get_tal_of_evaluated_node(node.right, env)
                    total_len = tal.total_len(self.memory)
                    # print(total_len)

                if en.is_pointer(tal):
                    assert total_len == PTR_LEN
                    ptr = self.memory.allocate(PTR_LEN)
                    bo.push_stack(PTR_LEN)
                    bo.assign(ptr, r, PTR_LEN)
                elif en.is_array(tal):
                    if len(tal.array_lengths) > 1:
                        raise lib.CompileTimeException("High dimensional array not supported")
                    ptr = self.memory.allocate(PTR_LEN)
                    bo.push_stack(PTR_LEN)
                    arr_ptr = self.memory.allocate(total_len)
                    # print(total_len)
                    bo.push_stack(total_len)
                    bo.assign_i(ptr, arr_ptr)

                    if r != 0:
                        bo.assign(arr_ptr, r, total_len)
                    # print(ptr)
                else:
                    ptr = self.memory.allocate(total_len)
                    bo.push_stack(total_len)
                    bo.assign(ptr, r, total_len)

                env.define_var(type_node.left.name, tal, ptr)

        elif node.left.node_type == ast.INDEXING_NODE:  # set item
            left_node: ast.IndexingNode = node.left
            self.compile_setitem(left_node, r, env, bo)

        elif node.left.node_type == ast.UNARY_OPERATOR:
            left_node: ast.UnaryOperator = node.left
            l_tal = get_tal_of_evaluated_node(left_node, env)
            if left_node.operation == "unpack" or en.is_array(l_tal):
                res_ptr = self.get_unpack_final_pos(left_node, env, bo)
                # print(res_ptr)
                orig_tal = get_tal_of_evaluated_node(left_node, env)
                bo.ptr_assign(res_ptr, r, orig_tal.unit_len(self.memory))

    def compile_setitem(self, node: ast.IndexingNode, value_ptr: int, env: en.Environment, bo: ByteOutput):
        indexing_ptr, unit_len = self.get_indexing_ptr_and_unit_len(node, env, bo)

        bo.ptr_assign(indexing_ptr, value_ptr, unit_len)

    def compile_getitem(self, node: ast.IndexingNode, env: en.Environment, bo: ByteOutput):
        indexing_ptr, unit_len = self.get_indexing_ptr_and_unit_len(node, env, bo)

        result_ptr = self.memory.allocate(unit_len)
        bo.push_stack(unit_len)
        bo.unpack_addr(result_ptr, indexing_ptr, unit_len)
        return result_ptr

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
        bo.add_binary_op_int(MUL_I, indexing_ptr, index_ptr, unit_len_ptr)
        array_ptr = self.compile(node.call_obj, env, bo)
        bo.add_binary_op_int(ADD_I, indexing_ptr, array_ptr, indexing_ptr)

        # print(unit_len)

        return indexing_ptr, unit_len

    def compile_call(self, node: ast.FuncCall, env: en.Environment, bo: ByteOutput):
        assert node.call_obj.node_type == ast.NAME_NODE

        lf = node.line_num, node.file

        ftn = env.get_function(node.call_obj.name, lf)

        args = []  # args tuple
        for arg_node in node.args.lines:
            tal = get_tal_of_evaluated_node(arg_node, env)
            total_len = tal.total_len(self.memory)

            arg_ptr = self.compile(arg_node, env, bo)
            tup = arg_ptr, total_len
            args.append(tup)

        if isinstance(ftn, Function):
            return self.function_call(ftn, args, env, bo)
        elif isinstance(ftn, NativeFunction):
            return self.native_function_call(ftn, args, env, bo)
        else:
            raise lib.CompileTimeException("Unexpected function type")

    def function_call(self, func: Function, args: list, call_env: en.Environment, bo: ByteOutput):
        r_len = func.r_tal.total_len(self.memory)
        r_ptr = self.memory.allocate(r_len)
        bo.push_stack(r_len)

        bo.write_one(CALL)
        bo.write_int(func.ptr)
        # bo.write_int(r_ptr)  # return value ptr
        bo.write_int(r_len)  # rtype length
        bo.write_int(len(args))
        for arg in args:
            bo.write_int(arg[0])
            bo.write_int(arg[1])

        return r_ptr

    def native_function_call(self, func: NativeFunction, args: list, call_env, bo: ByteOutput):
        r_len = func.r_tal.total_len(self.memory)
        r_ptr = self.memory.allocate(r_len)
        bo.push_stack(r_len)

        bo.write_one(CALL_NAT)
        bo.write_int(func.ptr)
        bo.write_int(r_len)  # rtype length
        bo.write_int(r_ptr)  # return value ptr
        bo.write_int(len(args))

        for arg in args:
            bo.write_int(arg[0])
            bo.write_int(arg[1])

        return r_ptr

    def compile_unary_op(self, node: ast.UnaryOperator, env: en.Environment, bo: ByteOutput):
        if node.operation == "pack":
            num_ptr = self.compile(node.value, env, bo)
            ptr_ptr = self.memory.allocate(PTR_LEN)
            bo.push_stack(PTR_LEN)
            bo.assign_i(ptr_ptr, num_ptr)
            return ptr_ptr
        elif node.operation == "unpack":
            orig_tal = get_tal_of_evaluated_node(node, env)
            total_len = orig_tal.total_len(self.memory)
            ptr_ptr = self.compile(node.value, env, bo)
            # print(unit_len)
            num_ptr = self.memory.allocate(total_len)
            # print(num_ptr)
            bo.push_stack(total_len)
            bo.unpack_addr(num_ptr, ptr_ptr, total_len)
            return num_ptr
        else:  # normal unary operators
            raise lib.CompileTimeException("Not implemented")

    def compile_binary_op(self, node: ast.BinaryOperator, env: en.Environment, bo: ByteOutput):
        l_tal = get_tal_of_evaluated_node(node.left, env)
        r_tal = get_tal_of_evaluated_node(node.right, env)
        # print(l_tal, r_tal, node.operation)
        if l_tal.type_name == "int" or l_tal.type_name[0] == "*" or en.is_array(l_tal):
            lp = self.compile(node.left, env, bo)
            rp = self.compile(node.right, env, bo)
            if r_tal.type_name != "int" and r_tal.type_name[0] != "*":
                rp = self.case_to_int(rp, bo)

            if node.operation in INT_RESULT_TABLE_INT:
                res_pos = self.memory.allocate(INT_LEN)
                bo.push_stack(INT_LEN)
                op_code = INT_RESULT_TABLE_INT[node.operation]
                bo.add_binary_op_int(op_code, res_pos, lp, rp)
                return res_pos
            elif node.operation in EXTENDED_BOOL_RESULT_TABLE_INT:
                res_pos = self.memory.allocate(BOOLEAN_LEN)
                bo.push_stack(BOOLEAN_LEN)
                if node.operation in BOOL_RESULT_TABLE_INT:
                    op_code = BOOL_RESULT_TABLE_INT[node.operation]
                    bo.add_binary_op_int(op_code, res_pos, lp, rp)
                    return res_pos
                else:
                    op_tup = EXTENDED_BOOL_RESULT_TABLE_INT[node.operation]
                    l_res = self.memory.allocate(BOOLEAN_LEN)
                    bo.push_stack(INT_LEN)
                    r_res = self.memory.allocate(BOOLEAN_LEN)
                    bo.push_stack(INT_LEN)
                    bo.add_binary_op_int(op_tup[0], l_res, lp, rp)
                    bo.add_binary_op_int(op_tup[1], r_res, lp, rp)
                    bo.add_binary_op_int(OR, res_pos, l_res, r_res)
                    return res_pos

        elif l_tal.type_name == "boolean":
            if r_tal.type_name != "boolean":
                raise lib.CompileTimeException("Must be boolean")
            lp = self.compile_condition(node.left, env, bo)
            rp = self.compile_condition(node.right, env, bo)

            if node.operation in BOOL_RESULT_TABLE_BOOL:
                res_pos = self.memory.allocate(BOOLEAN_LEN)
                bo.push_stack(BOOLEAN_LEN)
                op_code = BOOL_RESULT_TABLE_BOOL[node.operation]
                bo.add_binary_op_int(op_code, res_pos, lp, rp)
                return res_pos

        raise lib.CompileTimeException("Unsupported binary operation '{}'".format(node.operation))

    def case_to_int(self, ptr, bo: ByteOutput):
        res_pos = self.memory.allocate(INT_LEN)
        bo.push_stack(INT_LEN)
        bo.cast_to_int(res_pos, ptr)
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
        if_bo = ByteOutput()
        else_bo = ByteOutput()
        if_env = en.BlockEnvironment(env)
        else_env = en.BlockEnvironment(env)
        self.compile(node.then_block, if_env, if_bo)
        self.compile(node.else_block, else_env, else_bo)
        if_branch_len = len(if_bo) + INT_LEN + 1  # skip if branch + goto stmt after if branch
        # end = else_begin + len(else_bo)

        if_bo.write_one(GOTO)
        if_bo.write_int(len(else_bo))  # goto the pos after else block

        bo.write_one(IF_ZERO_GOTO)
        bo.write_int(if_branch_len)
        bo.write_int(cond_ptr)

        bo.codes.extend(if_bo.codes)
        bo.codes.extend(else_bo.codes)
        # bo.add_if_zero_goto(, cond_ptr)

    def compile_for_loop(self, node: ast.ForLoopStmt, env: en.Environment, bo: ByteOutput):
        pass

    def compile_while_loop(self, node: ast.WhileStmt, env: en.Environment, bo: ByteOutput):
        init_len = len(bo)
        bo.write_one(STORE_SP)
        cond_ptr = self.compile_condition(node.condition.lines[0], env, bo)

        body_bo = ByteOutput()

        title_env = en.LoopEnvironment(env)
        body_env = en.BlockEnvironment(title_env)

        self.compile(node.body, body_env, body_bo)
        body_bo.write_one(RES_SP)
        body_len = len(body_bo) + INT_LEN + 1

        bo.write_one(IF_ZERO_GOTO)
        bo.write_int(body_len)
        bo.write_int(cond_ptr)

        cond_len = len(bo) - init_len
        body_bo.write_one(GOTO)
        body_bo.write_int(-body_len - cond_len)

        bo.codes.extend(body_bo.codes)
        # print(len(bo) - body_len - cond_len, init_len)
        bo.write_one(RES_SP)

    def compile_condition(self, node: ast.Expr, env: en.Environment, bo: ByteOutput):
        tal = get_tal_of_evaluated_node(node, env)
        if tal.type_name != "boolean":
            raise lib.CompileTimeException("Conditional statement can only have boolean output. Got '{}'."
                                           .format(tal.type_name))
        return self.compile(node, env, bo)

    def compile_undefined(self, node: ast.UndefinedNode, env: en.Environment, bo: ByteOutput):
        return 0

    def get_unpack_final_pos(self, node: ast.UnaryOperator, env: en.Environment, bo):
        if isinstance(node, ast.UnaryOperator) and node.operation == "unpack":
            return self.get_unpack_final_pos(node.value, env, bo)
        elif isinstance(node, ast.NameNode):
            return env.get(node.name, (node.line_num, node.file))
        elif isinstance(node, ast.Expr):
            return self.compile(node, env, bo)
        else:
            raise lib.CompileTimeException()


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
            raise lib.CompileTimeException("Array length must be fixed int literal")
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
    2: en.Type("boolean"),
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
        else:
            return tal
    elif node.node_type == ast.BINARY_OPERATOR:
        node: ast.BinaryOperator
        if node.operation in EXTENDED_BOOL_RESULT_TABLE_INT:
            return en.Type("boolean")
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
