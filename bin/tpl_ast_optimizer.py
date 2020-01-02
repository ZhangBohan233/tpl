import bin.spl_ast as ast
import bin.spl_types as typ
import bin.spl_parser as psr

INT_LEN = 8
FLOAT_LEN = 8
PTR_LEN = 8
BOOLEAN_LEN = 1
CHAR_LEN = 1
VOID_LEN = 0

LF = 0, "TreeOptimizer"

INT_OP_TABLE = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a // b,
    "%": lambda a, b: a % b,
}

FLOAT_OP_TABLE = INT_OP_TABLE.copy()
FLOAT_OP_TABLE["/"] = lambda a, b: a / b


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
            return None

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

        if isinstance(node, ast.BinaryOperator):  # constant pre-calculation
            if isinstance(node.left, ast.Literal) and isinstance(node.right, ast.Literal):
                lv = self.get_literal(node.left.lit_pos, node.left.lit_type)
                rv = self.get_literal(node.right.lit_pos, node.right.lit_type)
                if lv is not None and rv is not None:
                    res_v = pre_calculate(node.operation, lv, node.left.lit_type, rv, node.right.lit_type)
                    new_lit = self.parser.make_literal_node(LF, res_v, False)
                    return new_lit

        return node


def pre_calculate(op, lv, lt, rv, rt):
    if lt == 0 or lt == 4:  # int or char
        rrv = int(rv)
        fn = INT_OP_TABLE[op]
        return fn(lv, rrv)
    elif lt == 1:
        rrv = float(rv)
        fn = FLOAT_OP_TABLE[op]
        return fn(lv, rrv)
    else:
        raise Exception
