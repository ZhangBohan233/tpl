import py.tpl_token_lib as ttl


# operator: (precedence, left-first)
PRECEDENCE = {"+": (50, True), "-": (50, True), "*": (100, True), "/": (100, True), "%": (100, True),
              "==": 20, ">": (25, True), "<": (25, True), ">=": 25, "<=": 25,
              "!=": 20, "&&": (5, True), "||": (5, True), "&": 12, "^": 11, "|": 10,
              "<<": 40, ">>": 40, ">>>": 40, "unpack": 200, "kw_unpack": 200, "pack": 200, "new": 150,
              ".": 500, "!": 200, "neg": 200, "return": 0, "throw": 0, "namespace": 150,
              "=": (1, False), "+=": 3, "-=": 3, "*=": 3, "/=": 3, "%=": 3,
              "&=": 3, "^=": 3, "|=": 3, "<<=": 3, ">>=": 3, ">>>=": 3,
              "===": 20, "!==": 20, "instanceof": 25, "subclassof": 25, "assert": 0,
              "?": 4, "++": 300, "--": 300, ":": 3, "->": 4, "<-": 2, ":=": 1, "::": 500}


class Node:
    def __init__(self, lf: tuple):
        self.lf = lf


class Stmt(Node):
    def __init__(self, lf):
        Node.__init__(self, lf)


class Expr(Stmt):
    def __init__(self, lf):
        Stmt.__init__(self, lf)


class Line(Stmt):
    def __init__(self, lf, sections):
        Stmt.__init__(self, lf)

        self.sections = sections

    def __str__(self):
        return "Line " + str(self.sections) + ";\n"

    def __repr__(self):
        return self.__str__()


class Section(Stmt):
    def __init__(self, lf, nodes):
        Stmt.__init__(self, lf)

        self.nodes = nodes

    def __str__(self):
        return "Sec " + str(self.nodes)

    def __repr__(self):
        return self.__str__()


class BlockStmt(Stmt):
    def __init__(self, lf, contents):
        Stmt.__init__(self, lf)

        self.contents = contents

    def __str__(self):
        lst = ["Block{"]
        for line in self.contents:
            lst.append(str(line))
        return "\n".join(lst) + "}"

    def __repr__(self):
        return self.__str__()


class LeafNode(Node):
    def __init__(self, lf):
        Node.__init__(self, lf)


class LiteralNode(LeafNode):
    def __init__(self, lf, lit_pos, lit_type):
        LeafNode.__init__(self, lf)

        self.lit_pos = lit_pos
        self.lit_type = lit_type

    def __str__(self):
        return "Lit #" + self.lit_pos

    def __repr__(self):
        return self.__str__()


class NameNode(LeafNode):
    def __init__(self, lf, name):
        LeafNode.__init__(self, lf)

        self.name = name

    def __str__(self):
        return "Name({})".format(self.name)

    def __repr__(self):
        return self.__str__()


class BinaryExpr(Expr):
    def __init__(self, lf, op):
        Expr.__init__(self, lf)

        self.op = op
        self.left = None
        self.right = None
        self.pre, self.left_first = PRECEDENCE[op]

    def not_built(self):
        return self.left is None or self.right is None

    def __str__(self):
        return "BE({}{}{})".format(self.left, self.op, self.right)

    def __repr__(self):
        return self.__str__()


class UnaryExpr(Expr):
    def __init__(self, lf, op):
        Expr.__init__(self, lf)

        self.op = op
        self.value = None
        self.pre, self.left_first = PRECEDENCE[op]

    def not_built(self):
        return self.value is None


class CondStmt(Stmt):
    def __init__(self, lf):
        Stmt.__init__(self, lf)


class ForLoopStmt(CondStmt):
    def __init__(self, lf):
        CondStmt.__init__(self, lf)

        self.condition: list = None
        self.body = None

    def __str__(self):
        print(len(self.condition))
        return "for {} do {}".format(self.condition, self.body)

    def __repr__(self):
        return self.__str__()


class SectionBuilder:
    def __init__(self, parent=None):
        self.nodes = []
        self.parent = parent

    def add_name(self, name: str, lf):
        self.nodes.append(NameNode(lf, name))

    def add_binary_expr(self, op, lf):
        self.nodes.append(BinaryExpr(lf, op))

    def add_num_literal(self, num, lf):
        self.nodes.append(LiteralNode(lf, num, 0))

    def build(self, lf) -> Node:
        expr = False
        for node in self.nodes:
            if isinstance(node, Expr):
                expr = True

        if expr:
            self.build_expr()

        return Section(lf, self.nodes)

    def build_expr(self):
        while True:
            max_pre = 0
            index = 0
            for i in range(len(self.nodes)):
                node = self.nodes[i]
                if isinstance(node, BinaryExpr) and node.not_built():
                    if node.pre >= max_pre:
                        max_pre = node.pre
                        index = i
                elif isinstance(node, UnaryExpr) and node.not_built():
                    if node.pre >= max_pre:
                        max_pre = node.pre
                        index = i

            if max_pre == 0:  # build finished
                break

            expr = self.nodes[index]
            if isinstance(expr, BinaryExpr):
                expr.left = self.nodes[index - 1]
                expr.right = self.nodes[index + 1]
                self.nodes.pop(index + 1)
                self.nodes.pop(index - 1)
            elif isinstance(expr, UnaryExpr):
                if expr.left_first:
                    expr.value = self.nodes[index - 1]
                    self.nodes.pop(index - 1)
                else:
                    expr.value = self.nodes[index + 1]
                    self.nodes.pop(index + 1)


class LineBuilder:
    def __init__(self):
        self.sections = []

    def add_section(self, section: SectionBuilder, lf):
        self.sections.append(section.build(lf))

    def build(self, lf):
        return Line(lf, self.sections)


class BraceBuilder:
    def __init__(self, parent):
        self.lines = []
        self.parent: BraceBuilder = parent

    def add_line(self, line: LineBuilder, lf):
        self.lines.append(line.build(lf))

    def build_as_block(self, lf):
        return BlockStmt(lf, self.lines)

    def add_self_to_parent(self, lf):
        block = self.build_as_block(lf)
        self.parent.lines.append(block)


class ForLoopBuilder(BraceBuilder):
    def __init__(self, parent):
        BraceBuilder.__init__(self, parent)

        self.in_body = False
        self.cond_lines = []

    def add_line(self, line: LineBuilder, lf):
        if self.in_body:
            self.lines.append(line.build(lf))
        else:
            self.cond_lines.append(line.build(lf))

    def add_self_to_parent(self, lf):
        body = self.build_as_block(lf)
        for_loop = ForLoopStmt(lf)
        for_loop.condition = self.cond_lines
        for_loop.body = body
        self.parent.lines.append(for_loop)


class BracketBuilder:
    def __init__(self):
        self.inner_builder = SectionBuilder()
