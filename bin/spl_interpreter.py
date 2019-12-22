# import bin.spl_ast as ast
# import bin.spl_memory as mem
# import bin.spl_environment as en
# import bin.spl_lib as lib
# import bin.spl_types as typ
# import time
# import sys
#
# INVALID = lib.InvalidArgument()
#
# LINE_FILE = 0, "Interpreter"
#
# INT_LEN = mem.MEMORY.get_type_size("int")
# FLOAT_LEN = mem.MEMORY.get_type_size("float")
# CHAR_LEN = mem.MEMORY.get_type_size("char")
# BOOLEAN_LEN = mem.MEMORY.get_type_size("boolean")
# PTR_LEN = mem.MEMORY.pointer_length
#
# PRIMITIVE_TYPES = {
#     "int": INT_LEN,
#     "float": FLOAT_LEN,
#     "boolean": BOOLEAN_LEN,
#     "char": CHAR_LEN
# }
#
#
# class Interpreter:
#     def __init__(self):
#         self.ast = None
#         self.literal_bytes = None
#         self.string_lengths = None
#         self.global_env = en.GlobalEnvironment()
#
#     def set_ast(self, tree, literal_bytes: bytes):
#         self.ast = tree
#         self.literal_bytes = literal_bytes
#
#     def interpret(self):
#         mem.MEMORY.load_literal(self.literal_bytes)
#         self.add_natives()
#         evaluate(self.ast, self.global_env)
#         if "main" in self.global_env.functions:
#             main_group: dict = self.global_env.get_function("main", LINE_FILE)
#             # main_func: Function = main_group[""]
#             # main_rt = main_func.r_tal
#             # if main_rt.type_name != "int" or len(main_rt.array_lengths):
#             #     raise lib.SplException("Function 'main' must return 'int'")
#             r_ptr = call_function(main_group, [], self.global_env)
#             rb = mem.MEMORY.get(r_ptr, mem.MEMORY.get_type_size("int"))
#             return typ.bytes_to_int(rb)
#         return 0
#
#     def add_natives(self):
#         self.add_native_function("printf", NativeFunction(printf, en.Type("void"), eval_before=False))
#         self.add_native_function("malloc", NativeFunction(malloc, en.Type("int")))
#         self.add_native_function("free", NativeFunction(free, en.Type("void")))
#         self.add_native_function("sizeof", NativeFunction(sizeof, en.Type("int"), eval_before=False))
#         self.add_native_function("typeof", NativeFunction(typeof, en.Type("void"), eval_before=False))
#         self.add_native_function("memory_view", NativeFunction(memory_view, en.Type("void")))
#         self.add_native_function("memory_ava", NativeFunction(memory_ava, en.Type("void")))
#         self.add_native_function("memory_sp", NativeFunction(memory_sp, en.Type("void")))
#         self.add_native_function("heap_ava", NativeFunction(heap_ava, en.Type("int")))
#         self.add_native_function("mem_copy", NativeFunction(mem_copy, en.Type("void")))
#         self.add_native_function("clock", NativeFunction(clock, en.Type("int")))
#
#     def add_native_function(self, name, func):
#         self.global_env.define_function(name, func)
#
#
# class ParameterPair:
#     def __init__(self, name: str, tal: en.Type):
#         self.name: str = name
#         self.tal = tal
#
#     def __str__(self):
#         return "{}".format(self.name)
#
#     def __repr__(self):
#         return self.__str__()
#
#
# class Function:
#     def __init__(self, params, body, outer, r_tal):
#         self.params: [ParameterPair] = params
#         # self.annotations = annotations
#         self.body = body
#         self.outer_scope = outer
#         self.r_tal: en.Type = r_tal
#         # self.abstract = abstract
#         # self.doc = lib.CharArray(doc)
#
#     def __str__(self):
#         return "Function({}) -> {}".format([en.type_to_readable(par.tal) for par in self.params],
#                                            en.type_to_readable(self.r_tal))
#
#
# class NativeFunction:
#     def __init__(self, obj, r_tal: en.Type, eval_before=True):
#         """
#         :param obj: the callable object
#         :param r_tal: the returning <Type>
#         :param eval_before: whether to evaluate the args before passing to the function
#         """
#         self.func = obj
#         self.r_tal = r_tal
#         self.eval_before = eval_before
#         self.params = []
#
#     def call(self, *args):
#         return self.func(*args)
#
#
# class Struct:
#     def __init__(self, name: str):
#         self.name = name
#         self.vars: {str: (int, en.Type)} = {}  # records the pos, type name, and array length of each attribute
#
#     def get_attr_pos(self, attr_name: str) -> int:
#         return self.vars[attr_name][0]
#
#     def get_attr_tal(self, attr_name: str) -> en.Type:
#         return self.vars[attr_name][1]
#
#
# def print_warning(txt: str):
#     sys.stderr.write(txt)
#
#
# def printf(env: en.Environment, *args_node):
#     fmt_node = args_node[0]
#     # print(fmt_ptr)
#     # fmt_b: bytes = mem.MEMORY.get_string(fmt_ptr)
#     fmt_tal = get_tal_of_evaluated_node(fmt_node, env)
#     fmt_len = fmt_tal.total_len()
#     fmt_ptr = evaluate(fmt_node, env)
#     fmt_b = mem.MEMORY.get(fmt_ptr, fmt_len)
#     fmt: str = fmt_b.decode("utf-8")
#     i = 0
#     a_index = 0
#     f = False
#     lst = []
#     args = [evaluate(n, env) for n in args_node[1:]]
#     while i < len(fmt):
#         ch = fmt[i]
#         if ch == "%":
#             f = True
#         elif f:
#             if ch == "d":
#                 f = False
#                 num_ptr = args[a_index]
#                 a_index += 1
#                 bs = mem.MEMORY.get(num_ptr, INT_LEN)
#                 lst.append(str(typ.bytes_to_int(bs)))
#             elif ch == "f":
#                 f = False
#                 # TODO: get more pref
#                 num_ptr = args[a_index]
#                 a_index += 1
#                 bs = mem.MEMORY.get(num_ptr, FLOAT_LEN)
#                 lst.append(str(typ.bytes_to_float(bs)))
#             elif ch == "s":
#                 f = False
#                 ch_ptr = args[a_index]
#                 ch_node = args_node[a_index + 1]  # not aligned
#                 ch_tal = get_tal_of_evaluated_node(ch_node, env)
#                 # print(ch_tal)
#                 if en.is_array(ch_tal):
#                     b = mem.MEMORY.get(ch_ptr, ch_tal.total_len())
#                     s = typ.bytes_to_string(b)
#                     lst.append(s)
#                 elif ch_tal.type_name == "*char":
#                     content_ptr_b = mem.MEMORY.get(ch_ptr, PTR_LEN)
#                     content_ptr = typ.bytes_to_int(content_ptr_b)
#                     b = mem.MEMORY.get_char_array(content_ptr)
#                     s = typ.bytes_to_string(b)
#                     lst.append(s)
#                 else:
#                     print_warning("Unknown argument for identifier '%s'.\n")
#                 a_index += 1
#             elif ch == "c":
#                 f = False
#                 c_ptr = args[a_index]
#                 a_index += 1
#                 bs = mem.MEMORY.get(c_ptr, CHAR_LEN)
#                 lst.append(typ.bytes_to_string(bs))
#             elif ch == "b":
#                 f = False
#                 bool_ptr = args[a_index]
#                 a_index += 1
#                 bb = mem.MEMORY.get(bool_ptr, BOOLEAN_LEN)
#                 bv = typ.bytes_to_bool(bb)
#                 lst.append("true" if bv else "false")
#             else:
#                 print_warning("Unknown identifier '%{}'".format(ch))
#                 f = False
#         else:
#             lst.append(ch)
#         i += 1
#     string = "".join(lst)
#     print(string)
#
#
# def malloc(length_ptr: int) -> int:
#     int_len = mem.MEMORY.get_type_size("int")
#     b = mem.MEMORY.get(length_ptr, int_len)
#     v = typ.bytes_to_int(b)
#     ptr = mem.MEMORY.malloc(v)
#     ptr_b = typ.int_to_bytes(ptr)
#     rtn = mem.MEMORY.allocate(ptr_b)
#     return rtn
#
#
# def free(ptr):
#     b = mem.MEMORY.get(ptr, mem.MEMORY.pointer_length)
#     loc = typ.bytes_to_int(b)
#     mem.MEMORY.free(loc)
#
#
# def sizeof(env: en.Environment, node: ast.NameNode) -> int:
#     size = mem.MEMORY.get_type_size(node.name)
#
#     # struct: Struct = evaluate(node, env)
#     # s_name = struct.name
#     # struct_size = mem.MEMORY.get_type_size(s_name)
#     b = typ.int_to_bytes(size)
#     return mem.MEMORY.allocate(b)
#
#
# def typeof(env: en.Environment, node: ast.Node):
#     tal = get_tal_of_evaluated_node(node, env)
#     s = en.type_to_readable(tal)
#     print(s)
#
#
# def memory_view():
#     mem.MEMORY.print_memory()
#
#
# def memory_ava():
#     mem.MEMORY.available2.print_sorted()
#     # print(mem.MEMORY.available)
#     # mem.MEMORY.available2.print_heap()
#
#
# def memory_sp():
#     print(mem.MEMORY.sp)
#
#
# def heap_ava() -> int:
#     size = len(mem.MEMORY.available2)
#     b = typ.int_to_bytes(size)
#     return mem.MEMORY.allocate(b)
#
#
# def mem_copy(from_ptr, to_ptr, len_ptr):
#     fb = mem.MEMORY.get(from_ptr, PTR_LEN)
#     tb = mem.MEMORY.get(to_ptr, PTR_LEN)
#     lb = mem.MEMORY.get(len_ptr, PTR_LEN)
#     fi, ti, li = typ.bytes_to_int(fb), typ.bytes_to_int(tb), typ.bytes_to_int(lb)
#     # print(fi, ti, li)
#     mem.MEMORY.mem_copy(fi, ti, li)
#
#
# def clock() -> int:
#     t_s = time.time()
#     t_ms = int(t_s * 1000)
#     b = typ.int_to_bytes(t_ms)
#     return mem.MEMORY.allocate(b)
#
#
# # #### Evaluation functions #### #
#
#
# def eval_block(node: ast.BlockStmt, env: en.Environment):
#     result = None
#     for line in node.lines:
#         result = evaluate(line, env)
#     return result
#
#
# def eval_name(node: ast.NameNode, env: en.Environment):
#     if env.contains_ptr(node.name):
#         r = env.get(node.name, (node.line_num, node.file))
#     else:
#         r = env.get_function(node.name, (node.line_num, node.file))
#     return r
#
#
# def eval_def(node: ast.DefStmt, env: en.Environment):
#     block: ast.BlockStmt = node.params
#     params_lst = []
#     for p in block.lines:
#         # p: ast.Node
#         if p.node_type == ast.TYPE_NODE:
#             p: ast.TypeNode
#             name = p.left.name
#             tal = get_tal_of_defining_node(p.right, env)
#         else:
#             raise lib.SplException("Unexpected syntax in function parameter, in file '{}', at line {}."
#                                    .format(node.file, node.line_num))
#         pair = ParameterPair(name, tal)
#         params_lst.append(pair)
#
#     f = Function(params_lst, node.body, env, node.doc)
#     f.file = node.file
#     f.line_num = node.line_num
#     f.r_tal = get_tal_of_defining_node(node.r_type, env)
#     return f
#
#
# def eval_call(node: ast.FuncCall, env: en.Environment):
#     func_group: dict = evaluate(node.call_obj, env)
#     some_func = list(func_group.values())[0]
#
#     if isinstance(some_func, Function):
#         return call_function(func_group, node.args.lines, env)
#     elif isinstance(some_func, NativeFunction):
#         return call_native_function(some_func, node.args.lines, env)
#     else:
#         raise lib.TypeException("Call on a non-callable object")
#
#
# def call_native_function(func: NativeFunction, orig_args: list, call_env: en.Environment):
#     rtn_type = func.r_tal
#     rtn_len = rtn_type.total_len()
#     rtn_loc = mem.MEMORY.allocate_empty(rtn_len)
#
#     mem.MEMORY.push_stack()
#
#     if func.eval_before:
#         args = []
#         for i in range(len(orig_args)):
#             orig_arg = orig_args[i]
#             # print(orig_arg)
#             value = evaluate(orig_arg, call_env)
#             args.append(value)
#
#         rtn_ptr = func.call(*args)
#     else:
#         rtn_ptr = func.call(call_env, *orig_args)
#
#     if rtn_len > 0:
#         mem.MEMORY.mem_copy(rtn_ptr, rtn_loc, rtn_len)
#
#         mem.MEMORY.restore_stack()
#         return rtn_loc
#
#
# def call_function(func_group: dict, orig_args: list, call_env: en.Environment):
#     arg_types = []
#     for orig_arg in orig_args:
#         tal = get_tal_of_evaluated_node(orig_arg, call_env)
#         arg_types.append(tal)
#
#     types_id = en.args_type_hash(arg_types)
#     func = func_group[types_id]
#
#     rtn_type = func.r_tal
#     rtn_len = rtn_type.total_len()
#     rtn_loc = mem.MEMORY.allocate_empty(rtn_len)
#
#     scope = en.FunctionEnvironment(func.outer_scope)
#     mem.MEMORY.push_stack()
#
#     for i in range(len(orig_args)):
#         param: ParameterPair = func.params[i]
#         orig_arg = orig_args[i]
#         p = evaluate(orig_arg, call_env)
#         tal = param.tal
#         total_len = tal.total_len()
#         arg_ptr = mem.MEMORY.allocate_empty(total_len)
#         scope.define_var(param.name, tal, arg_ptr)
#         mem.MEMORY.mem_copy(p, arg_ptr, total_len)
#
#     r = evaluate(func.body, scope)
#
#     if rtn_len > 0 and r is None:
#         raise lib.TypeException("Missing return statement of a function declared to return type '{}'"
#                                 .format(en.type_to_readable(rtn_type)))
#     mem.MEMORY.mem_copy(r, rtn_loc, rtn_len)
#
#     mem.MEMORY.restore_stack()
#     return rtn_loc
#
#
# def get_tal_of_defining_node(node: ast.Node, env: en.Environment) -> en.Type:
#     if node.node_type == ast.NAME_NODE:
#         node: ast.NameNode
#         return en.Type(node.name)
#     elif node.node_type == ast.INDEXING_NODE:  # array
#         node: ast.IndexingNode
#         tn_al_inner: en.Type = get_tal_of_defining_node(node.call_obj, env)
#         if len(node.arg.lines) == 0:
#             return en.Type(tn_al_inner.type_name, 0)
#         arr_len_ptr = evaluate(node.arg, env)
#         arr_len_b = mem.MEMORY.get(arr_len_ptr, INT_LEN)
#         arr_len_v = typ.bytes_to_int(arr_len_b)
#         # return type_name, arr_len_inner * typ.bytes_to_int(arr_len_b)
#         return en.Type(tn_al_inner.type_name, *tn_al_inner.array_lengths, arr_len_v)
#     elif node.node_type == ast.UNARY_OPERATOR:
#         node: ast.UnaryOperator
#         tal = get_tal_of_defining_node(node.value, env)
#         if node.operation == "unpack":
#             return en.Type("*" + tal.type_name, *tal.array_lengths)
#         else:
#             raise lib.UnexpectedSyntaxException()
#
#
# LITERAL_TYPE_TABLE = {
#     0: en.Type("int"),
#     1: en.Type("float"),
#     2: en.Type("boolean"),
#     3: en.Type("string"),
#     4: en.Type("char")
# }
#
#
# def get_tal_of_node_self(node: ast.Node, env: en.Environment) -> en.Type:
#     if node.node_type == ast.NAME_NODE:
#         node: ast.NameNode
#         return env.get_type_arr_len(node.name, (node.line_num, node.file))
#     elif node.node_type == ast.INDEXING_NODE:
#         node: ast.IndexingNode
#         return get_tal_of_node_self(node.call_obj, env)
#     elif node.node_type == ast.UNARY_OPERATOR:
#         node: ast.UnaryOperator
#         print(2223)
#
#
# def get_tal_of_evaluated_node(node: ast.Node, env: en.Environment) -> en.Type:
#     if node.node_type == ast.LITERAL:
#         node: ast.Literal
#         return LITERAL_TYPE_TABLE[node.lit_type]
#     elif node.node_type == ast.STRING_LITERAL:
#         node: ast.StringLiteralNode
#         return en.Type("char", node.byte_length)
#     elif node.node_type == ast.NAME_NODE:
#         node: ast.NameNode
#         return env.get_type_arr_len(node.name, (node.line_num, node.file))
#     elif node.node_type == ast.UNARY_OPERATOR:
#         node: ast.UnaryOperator
#         tal = get_tal_of_evaluated_node(node.value, env)
#         if node.operation == "unpack":
#             if len(tal.type_name) > 1 and tal.type_name[0] == "*":
#                 return en.Type(tal.type_name[1:])
#             else:
#                 raise lib.TypeException("Cannot unpack a non-pointer type")
#         elif node.operation == "pack":
#             return en.Type("*" + tal.type_name)
#         else:
#             return tal
#     elif node.node_type == ast.BINARY_OPERATOR:
#         node: ast.BinaryOperator
#         return get_tal_of_evaluated_node(node.left, env)
#     elif node.node_type == ast.FUNCTION_CALL:
#         node: ast.FuncCall
#         call_obj = node.call_obj
#         if call_obj.node_type == ast.NAME_NODE:
#             func_group: dict = env.get_function(call_obj.name, (node.line_num, node.file))
#             arg_types = []
#             for orig_arg in node.args.lines:
#                 tal = get_tal_of_evaluated_node(orig_arg, env)
#                 arg_types.append(tal)
#             types_id = en.args_type_hash(arg_types)
#             func = func_group[types_id]
#             return func.r_tal
#     elif node.node_type == ast.INDEXING_NODE:  # array
#         node: ast.IndexingNode
#         # return get_tal_of_ordinary_node(node.call_obj, env)
#         tal_co = get_tal_of_evaluated_node(node.call_obj, env)
#         if en.is_array(tal_co):
#             return en.Type(tal_co.type_name, *tal_co.array_lengths[1:])
#         elif tal_co.type_name[0] == "*":
#             return en.Type(tal_co.type_name[1:])
#         else:
#             raise lib.TypeException()
#     elif node.node_type == ast.IN_DECREMENT_OPERATOR:
#         node: ast.InDecrementOperator
#         return get_tal_of_evaluated_node(node.value, env)
#     elif node.node_type == ast.NULL_STMT:
#         return en.Type("*void")
#
#
# def eval_assignment_node(node: ast.AssignmentNode, env: en.Environment):
#     r = evaluate(node.right, env)
#     lf = node.line_num, node.file
#
#     if node.left.node_type == ast.NAME_NODE:
#         name: str = node.left.name
#         if node.level == ast.FUNC_DEFINE:
#             if not isinstance(r, Function):
#                 raise lib.TypeException("Unexpected function declaration")
#             env.define_function(name, r)
#         else:
#             tal = get_tal_of_evaluated_node(node.left, env)
#             total_len = tal.total_len()
#             rv = mem.MEMORY.get(r, total_len)
#             current_ptr = env.get(name, lf)
#             mem.MEMORY.set(current_ptr, rv)
#             # env.assign(name, r, lf)
#     elif node.left.node_type == ast.TYPE_NODE:
#         type_node: ast.TypeNode = node.left
#         tal = get_tal_of_defining_node(type_node.right, env)
#         name: str = type_node.left.name
#         total_len = tal.total_len()
#         if total_len == 0:  # array with undefined length
#             tal = get_tal_of_evaluated_node(node.right, env)
#             total_len = tal.total_len()
#
#         ptr = mem.MEMORY.allocate_empty(total_len)
#         if r != 0:  # is not undefined
#             mem.MEMORY.mem_copy(r, ptr, total_len)
#
#         if node.level == ast.VAR:
#             env.define_var(name, tal, ptr)
#         elif node.level == ast.CONST:
#             env.define_const(name, tal, ptr)
#     elif node.left.node_type == ast.DOT:
#         dot: ast.Dot = node.left
#         l_ptr = evaluate(dot.left, env)
#         l_tal = get_tal_of_evaluated_node(dot.left, env)
#         # print(l_tal)
#         struct: Struct = env.get_struct(l_tal.type_name)
#         attr: ast.NameNode = dot.right
#         pos_in_struct = struct.get_attr_pos(attr.name)
#         attr_tal = struct.get_attr_tal(attr.name)
#         attr_len = attr_tal.total_len()
#         rv = mem.MEMORY.get(r, attr_len)
#         mem.MEMORY.set(l_ptr + pos_in_struct, rv)
#     elif node.left.node_type == ast.INDEXING_NODE:
#         eval_setitem(node.left, r, env)
#     elif node.left.node_type == ast.UNARY_OPERATOR:
#         uo: ast.UnaryOperator = node.left
#         tal = get_tal_of_evaluated_node(uo, env)
#         total_len = tal.total_len()
#         l_ptr = evaluate(uo, env)
#         rv = mem.MEMORY.get(r, total_len)
#         if uo.operation == "pack" and uo.value.node_type == ast.NAME_NODE:
#             ri = typ.bytes_to_int(rv)
#             env.assign(uo.value.name, ri, lf)
#         else:
#             mem.MEMORY.set(l_ptr, rv)
#     else:
#         raise lib.TypeException("Currently unimplemented")
#
#
# def eval_setitem(left: ast.IndexingNode, right_ptr: int, env: en.Environment):
#     modifying_ptr, unit_length = get_indexing_location_and_unit_len(left, env)
#     # print(modifying_ptr, unit_length)
#     rb = mem.MEMORY.get(right_ptr, unit_length)
#     mem.MEMORY.set(modifying_ptr, rb)
#
#
# def eval_getitem(node: ast.IndexingNode, env: en.Environment):
#     modifying_ptr, unit_length = get_indexing_location_and_unit_len(node, env)
#     return modifying_ptr
#
#
# def get_indexing_location_and_unit_len(node: ast.IndexingNode, env: en.Environment) -> (int, int):
#     l_ptr = evaluate(node.call_obj, env)
#     l_tal = get_tal_of_node_self(node, env)
#     if en.is_array(l_tal):
#         depth = index_node_depth(node)
#         unit_length = l_tal.total_len()
#         for i in range(depth):
#             unit_length //= l_tal.array_lengths[i]
#     elif l_tal.type_name[0] == "*":
#         ptr_b = mem.MEMORY.get(l_ptr, PTR_LEN)
#         l_ptr = typ.bytes_to_int(ptr_b)
#         unit_length = mem.MEMORY.get_type_size(l_tal.type_name[1:])
#     else:
#         raise lib.TypeException("Type '{}' not supporting indexing".format(en.type_to_readable(l_tal)))
#
#     arg_ptr = evaluate(node.arg, env)  # arg type must be int
#     arg_b = mem.MEMORY.get(arg_ptr, mem.MEMORY.get_type_size("int"))
#     arg_v = typ.bytes_to_int(arg_b)
#     return l_ptr + arg_v * unit_length, unit_length
#
#
# def index_node_depth(node: ast.IndexingNode):
#     if node.call_obj.node_type == ast.INDEXING_NODE:
#         return index_node_depth(node.call_obj) + 1
#     else:
#         return 1
#
#
# def get_array_len_of_node(node: ast.IndexingNode, env: en.Environment) -> int:
#     arr_len_ptr = evaluate(node.arg, env)
#     arr_len_b = mem.MEMORY.get(arr_len_ptr, mem.MEMORY.get_type_size("int"))
#     return typ.bytes_to_int(arr_len_b)
#
#
# def fill_array(ptr, type_length: int, array: list):
#     pass
#
#
# def assignment():
#     pass
#
#
# ADD_SET = {
#     "int": {
#         "int": typ.int_add_int,
#         "float": typ.int_add_float
#     },
#     "float": {
#         "int": typ.float_add_int
#     }
# }
#
# SUB_SET = {
#     "int": {
#         "int": typ.int_sub_int,
#         "float": typ.int_sub_float
#     }
# }
#
# MUL_SET = {
#     "int": {
#         "int": typ.int_mul_int,
#         "float": None
#     }
# }
#
# DIV_SET = {
#
# }
#
# MOD_SET = {
#
# }
#
#
# def eval_addition(left_ptr: int, left_tal: en.Type, right_ptr: int, right_tal: en.Type,
#                   env: en.Environment) -> int:
#     return basic_arithmetic(ADD_SET, left_ptr, left_tal, right_ptr, right_tal, env)
#
#
# def eval_subtraction(left_ptr: int, left_tal: en.Type, right_ptr: int, right_tal: en.Type,
#                      env: en.Environment) -> int:
#     return basic_arithmetic(SUB_SET, left_ptr, left_tal, right_ptr, right_tal, env)
#
#
# def basic_arithmetic(op_set: dict, left_ptr: int, left_tal: en.Type, right_ptr: int, right_tal: en.Type,
#                      env: en.Environment) -> int:
#     if left_tal.type_name in op_set:
#         left_len = left_tal.total_len()
#         lv = mem.MEMORY.get(left_ptr, left_len)
#         # print(right_ptr)
#         return int_op_any(lv, right_ptr, right_tal, op_set[left_tal.type_name])
#     elif left_tal.type_name[0] == "*":
#         ptr_len = mem.MEMORY.pointer_length
#         lv = mem.MEMORY.get(left_ptr, ptr_len)
#         return int_op_any(lv, right_ptr, right_tal, op_set["int"])
#     else:
#         raise lib.TypeException("Cannot operates {}".format(en.type_to_readable(right_tal)))
#
#
# def int_op_any(lv: bytes, right_ptr: int, right_tal: en.Type, op_set: dict) -> int:
#     if right_tal.type_name in op_set:
#         rv = mem.MEMORY.get(right_ptr, right_tal.total_len())
#         op_func = op_set[right_tal.type_name]
#         res = op_func(lv, rv)
#         return mem.MEMORY.allocate(res)
#     elif right_tal.type_name[0] == "*":
#         rv = mem.MEMORY.get(right_ptr, PTR_LEN)
#         op_func = op_set["int"]
#         res = op_func(lv, rv)
#         return mem.MEMORY.allocate(res)
#     else:
#         raise lib.TypeException("Cannot operates int with {}".format(en.type_to_readable(right_tal)))
#
#
# def primitive_comparison(cmp_func, ) -> int:
#     pass
#
#
# def eval_comparison(cmp_func, lp, l_tal: en.Type, rp, r_tal: en.Type, env) -> int:
#     if l_tal.type_name in PRIMITIVE_TYPES and r_tal.type_name in PRIMITIVE_TYPES and not en.is_array(l_tal) and \
#             not en.is_array(r_tal):
#         l_len = PRIMITIVE_TYPES[l_tal.type_name]
#         r_len = PRIMITIVE_TYPES[r_tal.type_name]
#         lb = mem.MEMORY.get(lp, l_len)
#         rb = mem.MEMORY.get(rp, r_len)
#
#         if l_tal.type_name == "int":
#             if r_tal.type_name == "int":
#                 cmp = typ.int_cmp_int(lb, rb)
#                 return cmp_func(cmp)
#         elif l_tal.type_name == "char":
#             if r_tal.type_name == "char":
#                 cmp = typ.char_cmp_char(lb, rb)
#                 return cmp_func(cmp)
#     elif l_tal.type_name[0] == "*":
#         l_ptr_b = mem.MEMORY.get(lp, l_tal.total_len())
#         # l_ptr = typ.bytes_to_int(l_ptr_b)
#         if r_tal.type_name[0] == "*":
#             r_ptr_b = mem.MEMORY.get(rp, r_tal.total_len())
#             # r_ptr = typ.bytes_to_int(r_ptr_b)
#             # print(l_ptr_b ,r_ptr_b)
#             cmp = typ.int_cmp_int(l_ptr_b, r_ptr_b)
#             return cmp_func(cmp)
#         else:
#             raise lib.TypeException("Comparing pointer type '{}' to primitive type '{}'"
#                                     .format(en.type_to_readable(l_tal), en.type_to_readable(r_tal)))
#     else:
#         print(2131212321)
#
#
# BINARY_OP_TABLE = {
#     "+": ADD_SET,
#     "-": SUB_SET,
#     "*": MUL_SET,
#     "/": DIV_SET
# }
#
#
# def get_bool_ptr(v: bool) -> int:
#     return mem.MEMORY.get_literal_ptr(1) if v else mem.MEMORY.get_literal_ptr(0)
#
#
# COMPARE_TABLE = {
#     "<": lambda v: get_bool_ptr(v < 0),
#     ">": lambda v: get_bool_ptr(v > 0),
#     "==": lambda v: get_bool_ptr(v == 0),
#     "!=": lambda v: get_bool_ptr(v != 0),
#     "<=": lambda v: get_bool_ptr(v <= 0),
#     ">=": lambda v: get_bool_ptr(v >= 0)
# }
#
#
# def eval_binary_operation(node: ast.BinaryOperator, env: en.Environment):
#     if node.assignment and node.operation[:-1] in BINARY_OP_TABLE:
#         left = evaluate(node.left, env)
#         right = evaluate(node.right, env)
#
#         ltl = get_tal_of_evaluated_node(node.left, env)
#         rtl = get_tal_of_evaluated_node(node.right, env)
#
#         op_type = BINARY_OP_TABLE[node.operation[:-1]]
#         res = basic_arithmetic(op_type, left, ltl, right, rtl, env)
#         mem.MEMORY.mem_copy(res, left, ltl.total_len())
#         return left
#     elif node.operation in BINARY_OP_TABLE:
#         left = evaluate(node.left, env)
#         right = evaluate(node.right, env)
#
#         ltl = get_tal_of_evaluated_node(node.left, env)
#         rtl = get_tal_of_evaluated_node(node.right, env)
#
#         # print(left, right)
#
#         op_type = BINARY_OP_TABLE[node.operation]
#         return basic_arithmetic(op_type, left, ltl, right, rtl, env)
#     elif node.operation in COMPARE_TABLE:
#         left = evaluate(node.left, env)
#         right = evaluate(node.right, env)
#
#         ltl = get_tal_of_evaluated_node(node.left, env)
#         rtl = get_tal_of_evaluated_node(node.right, env)
#
#         cmp = COMPARE_TABLE[node.operation]
#         return eval_comparison(cmp, left, ltl, right, rtl, env)
#     else:
#         raise lib.TypeException("Unexpected binary operator '{}', in file '{}', at line {}"
#                                 .format(node.operation, node.file, node.line_num))
#
#
# def eval_unpack(vp: int, v_tal: en.Type, env: en.Environment):
#     vb = mem.MEMORY.get(vp, INT_LEN)
#     v = typ.bytes_to_int(vb)
#     # orig_type_name = v_tal[0][1:]  # for example, *int to int, or **int to *int
#     # # rb = mem.MEMORY.get(v, mem.MEMORY.get_type_size(orig_type_name) * v_tal[1])
#     return v
#
#
# def eval_pack(vp: int, v_tal: en.Type, env: en.Environment):
#     b = typ.int_to_bytes(vp)
#     return mem.MEMORY.allocate(b)
#
#
# def eval_neg(vp: int, v_tal: en.Type, env: en.Environment):
#     if v_tal.type_name == "int":
#         int_len = mem.MEMORY.get_type_size("int")
#         v = mem.MEMORY.get(vp, int_len)
#         res = typ.int_neg(v)
#         return mem.MEMORY.allocate(res)
#
#
# UNARY_OP_TABLE = {
#     "unpack": eval_unpack,
#     "pack": eval_pack,
#     "neg": eval_neg
# }
#
#
# def eval_unary_operation(node: ast.UnaryOperator, env: en.Environment):
#     if node.operation in UNARY_OP_TABLE:
#         value_ptr = evaluate(node.value, env)
#         tal = get_tal_of_evaluated_node(node.value, env)
#         op = UNARY_OP_TABLE[node.operation]
#         return op(value_ptr, tal, env)
#
#
# def eval_struct_node(node: ast.StructNode, env: en.Environment):
#     struct = Struct(node.name)
#     pos = 0
#     for line in node.block.lines:
#         type_node: ast.TypeNode = line.left
#         tal = get_tal_of_defining_node(type_node.right, env)
#         name: str = type_node.left.name
#         struct.vars[name] = pos, tal
#         total_len = tal.total_len()
#         pos += total_len
#     mem.MEMORY.add_type(node.name, pos)
#     env.add_struct(node.name, struct)
#
#
# def eval_dot(node: ast.Dot, env: en.Environment):
#     l_ptr = evaluate(node.left, env)
#     l_tal = get_tal_of_evaluated_node(node.left, env)
#     struct: Struct = env.get_struct(l_tal.type_name)
#     attr: ast.NameNode = node.right
#     pos_in_struct = struct.get_attr_pos(attr.name)
#     return l_ptr + pos_in_struct
#
#
# def eval_literal(node: ast.Literal, env: en.Environment):
#     return mem.MEMORY.get_literal_ptr(node.lit_pos)
#
#
# def eval_string_literal(node: ast.StringLiteralNode, env: en.Environment):
#     return evaluate(node.literal, env)
#
#
# def eval_return(node: ast.ReturnStmt, env: en.Environment):
#     r = evaluate(node.value, env)
#     env.terminate(r)
#     return r
#
#
# def eval_if_stmt(node: ast.IfStmt, env: en.Environment):
#     boolean = eval_boolean(node.condition, env)
#
#     scope = en.BlockEnvironment(env)
#     if boolean:
#         res = evaluate(node.then_block, scope)
#     else:
#         res = evaluate(node.else_block, scope)
#     return res
#
#
# def eval_boolean(node: ast.Node, env: en.Environment) -> bool:
#     p = evaluate(node, env)
#     b = mem.MEMORY.get(p, mem.MEMORY.get_type_size("boolean"))
#     # print(b)
#     return bool(b[0])
#
#
# def eval_for_loop(node: ast.ForLoopStmt, env: en.Environment):
#     title_scope = en.LoopEnvironment(env)
#     block_scope = en.BlockEnvironment(title_scope)
#
#     start = node.condition.lines[0]
#     stop = node.condition.lines[1]
#     step = node.condition.lines[2]
#
#     evaluate(start, title_scope)
#     if step.node_type == ast.IN_DECREMENT_OPERATOR and not step.is_post:
#         while not title_scope.is_stopped() and eval_boolean(stop, title_scope):
#             mem.MEMORY.push_stack()
#             block_scope.invalidate()
#             evaluate(step, title_scope)
#             evaluate(node.body, block_scope)
#             title_scope.resume_loop()
#             mem.MEMORY.restore_stack()
#     else:
#         while not title_scope.is_stopped() and eval_boolean(stop, title_scope):
#             mem.MEMORY.push_stack()
#             block_scope.invalidate()
#             evaluate(node.body, block_scope)
#             evaluate(step, title_scope)
#             title_scope.resume_loop()
#             mem.MEMORY.restore_stack()
#
#
# def eval_while_loop(node: ast.WhileStmt, env: en.Environment):
#     title_scope = en.LoopEnvironment(env)
#     block_scope = en.BlockEnvironment(title_scope)
#
#     cond = node.condition
#
#     while not title_scope.is_stopped() and eval_boolean(cond, title_scope):
#         mem.MEMORY.push_stack()
#         block_scope.invalidate()
#         evaluate(node.body, block_scope)
#         title_scope.resume_loop()
#         mem.MEMORY.restore_stack()
#
#
# INCREMENT_TABLE = {
#     "int": (typ.bytes_to_int, typ.int_add_int, 1)
# }
#
# DECREMENT_TABLE = {
#     "int": (typ.bytes_to_int, typ.int_sub_int, 1)
# }
#
#
# def eval_in_decrement(node: ast.InDecrementOperator, env: en.Environment):
#     ptr = evaluate(node.value, env)
#     tal = get_tal_of_evaluated_node(node, env)
#     b = mem.MEMORY.get(ptr, tal.total_len())
#     if node.operation == "++" and tal.type_name in INCREMENT_TABLE:
#         tup = INCREMENT_TABLE[tal.type_name]
#
#     elif node.operation == "--" and tal.type_name in DECREMENT_TABLE:
#         tup = DECREMENT_TABLE[tal.type_name]
#
#     else:
#         lib.UnexpectedSyntaxException("Unexpected type of increment or decrement, in file '{}', at line {}"
#                                       .format(node.file, node.line_num))
#
#
# def eval_null(node: ast.NullStmt, env: en.Environment):
#     return 1
#
#
# NODE_TABLE = {
#     ast.NAME_NODE: eval_name,
#     ast.DEF_STMT: eval_def,
#     ast.ASSIGNMENT_NODE: eval_assignment_node,
#     ast.BLOCK_STMT: eval_block,
#     ast.FUNCTION_CALL: eval_call,
#     ast.BINARY_OPERATOR: eval_binary_operation,
#     ast.UNARY_OPERATOR: eval_unary_operation,
#     ast.LITERAL: eval_literal,
#     ast.STRING_LITERAL: eval_string_literal,
#     ast.UNDEFINED_NODE: lambda n, e: 0,
#     ast.STRUCT_NODE: eval_struct_node,
#     ast.DOT: eval_dot,
#     ast.INDEXING_NODE: eval_getitem,
#     ast.RETURN_STMT: eval_return,
#     ast.IF_STMT: eval_if_stmt,
#     ast.FOR_LOOP_STMT: eval_for_loop,
#     ast.WHILE_STMT: eval_while_loop,
#     ast.IN_DECREMENT_OPERATOR: eval_in_decrement,
#     ast.NULL_STMT: eval_null
# }
#
#
# def evaluate(node: ast.Node, env: en.Environment):
#     if env.is_terminated():
#         return env.returned_ptr()
#     fn = NODE_TABLE[node.node_type]
#     # print(fn)
#     return fn(node, env)
