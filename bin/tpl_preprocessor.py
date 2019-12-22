import bin.spl_ast as ast


class Preprocessor:
    def __init__(self):
        pass

    def preprocess(self, node: ast.Node):
        if isinstance(node, ast.TypeNode):  # do not modify any node inside
            return node
        elif isinstance(node, ast.IndexingNode):
            return node
        elif isinstance(node, ast.Node):
            attr_names = dir(node)
            for attr_name in attr_names:
                if len(attr_name) < 5 or (attr_name[:2] != "__" and attr_name[-2:] != "__"):
                    setattr(node, attr_name, self.preprocess(getattr(node, attr_name)))
        return node
