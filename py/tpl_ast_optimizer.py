import sys
import py.tpl_ast as ast
import py.tpl_types as typ
import py.tpl_parser as psr

INT_LEN = 8
FLOAT_LEN = 8
PTR_LEN = 8
BOOLEAN_LEN = 1
CHAR_LEN = 1
VOID_LEN = 0

LF = 0, "TreeOptimizer"


def logical_rs1(v: int):
    v >>= 1
    temp = v.to_bytes(8, sys.byteorder, signed=True)
    if sys.byteorder == "little":
        sign_byte = temp[7]
        if sign_byte > 127:  # negative
            sign_byte -= 128
        res_b = temp[:7] + bytes((sign_byte,))
    else:
        sign_byte = temp[0]
        if sign_byte > 127:  # negative
            sign_byte -= 128
        res_b = bytes((sign_byte,)) + temp[1:]
    return int.from_bytes(res_b, sys.byteorder, signed=True)


def logical_right_shift(a: int, b: int):
    for i in range(b):
        a = logical_rs1(a)
    return a


INT_BIN_OP_TABLE = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a // b,
    "%": lambda a, b: a % b,
    ">>": lambda a, b: a >> b,
    ">>>": logical_right_shift,
    "<<": lambda a, b: a << b,
    "&": lambda a, b: a & b,
    "|": lambda a, b: a | b,
    "^": lambda a, b: a ^ b
}

FLOAT_BIN_OP_TABLE = INT_BIN_OP_TABLE.copy()
FLOAT_BIN_OP_TABLE["/"] = lambda a, b: a / b

INT_UNA_OP_TABLE = {
    "neg": lambda v: -v,
    "!": lambda v: 1 if v == 0 else 0
}

FLOAT_UNA_OP_TABLE = {
    "neg": lambda v: -v
}


class OptimizerException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


class AstOptimizer:
    def __init__(self, root: ast.Node, parser: psr.Parser, level: int):
        self.root = root
        self.parser = parser
        self.level = level

    def optimize(self):
        if self.level > 0:
            self.optimize_node(self.root)

    def get_literal(self, pos, lit_type):
        if lit_type == 0:  # int
            return typ.bytes_to_int(self.parser.literal_bytes[pos:pos + INT_LEN])
        elif lit_type == 1:  # float:
            return typ.bytes_to_float(self.parser.literal_bytes[pos:pos + FLOAT_LEN])
        elif lit_type == 4:  # char
            return self.parser.literal_bytes[pos:pos + CHAR_LEN]
        else:
            return None  # not optimize-able type

    def optimize_node(self, node: ast.Node):
        if isinstance(node, ast.Node):
            attr_names = dir(node)
            for attr_name in attr_names:
                attr = getattr(node, attr_name)
                if isinstance(attr, ast.Node):
                    modified = self.optimize_node(attr)
                    setattr(node, attr_name, modified)
                elif isinstance(attr, list):
                    for i in range(len(attr)):
                        attr[i] = self.optimize_node(attr[i])

        if isinstance(node, ast.BinaryOperator):  # constant binary op pre-calculation
            if isinstance(node.left, ast.Literal) and isinstance(node.right, ast.Literal):
                lv = self.get_literal(node.left.lit_pos, node.left.lit_type)
                rv = self.get_literal(node.right.lit_pos, node.right.lit_type)
                if lv is not None and rv is not None:
                    res_v = binary_op_pre_calculate(node.operation, lv, node.left.lit_type, rv, node.right.lit_type)
                    new_lit = self.parser.make_literal_node(LF, res_v, False)
                    return new_lit

        if isinstance(node, ast.UnaryOperator):  # constant unary op pre-calculation
            if isinstance(node.value, ast.Literal):
                v = self.get_literal(node.value.lit_pos, node.value.lit_type)
                if v is not None:
                    res_v = unary_op_pre_calculate(node.operation, v, node.value.lit_type)
                    new_lit = self.parser.make_literal_node(LF, res_v, False)
                    return new_lit

        return node


def binary_op_pre_calculate(op, lv, lt, rv, rt):
    if lt == 0 or lt == 4:  # int or char
        rrv = int(rv)
        fn = INT_BIN_OP_TABLE[op]
        return fn(lv, rrv)
    elif lt == 1:
        rrv = float(rv)
        fn = FLOAT_BIN_OP_TABLE[op]
        return fn(lv, rrv)
    else:
        raise OptimizerException()


def unary_op_pre_calculate(op, v, t):
    if t == 0 or t == 4:
        fn = INT_UNA_OP_TABLE[op]
        return fn(v)
    elif t == 1:
        fn = FLOAT_UNA_OP_TABLE[op]
        return fn(v)
    else:
        raise OptimizerException()
