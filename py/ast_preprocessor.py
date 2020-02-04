import py.tpl_ast as ast


class Preprocessor:
    def __init__(self):
        pass

    def preprocess(self, node: ast.Node):
        if isinstance(node, ast.Node):
            attr_names = dir(node)
            for attr_name in attr_names:
                attr = getattr(node, attr_name)
                if isinstance(attr, ast.Node):
                    modified = self.preprocess(attr)
                    setattr(node, attr_name, modified)
                elif isinstance(attr, list):
                    for i in range(len(attr)):
                        attr[i] = self.preprocess(attr[i])

        if isinstance(node, ast.BinaryOperatorAssignment):
            left = node.left
            right = node.right
            op_root = ast.BinaryOperator(node.lf(), node.real_op())
            op_root.left = left
            op_root.right = right
            assignment_root = ast.AssignmentNode(node.lf(), ast.ASSIGN)
            assignment_root.left = left
            assignment_root.right = op_root
            return assignment_root
        elif isinstance(node, ast.InDecrementOperator):
            pass

        return node
