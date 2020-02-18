import tkinter
import tkinter.ttk
import argparse
import os
import script
from py import tpl_lexer, tpl_ast as ast, tpl_parser as psr, ast_preprocessor as prep


class Visualizer:
    def __init__(self):
        self.window = tkinter.Tk()

        self.tree_view = tkinter.ttk.Treeview(self.window, selectmode='browse')
        self.tree_view.configure(columns=("type", "literal", "note", "file", "line"), height=30)

        self.tree_view.column("#0", width=300)
        self.tree_view.column("file", width=150, minwidth=100)
        self.tree_view.column("line", width=100, minwidth=50)

        self.tree_view.heading("#0", text="Node")
        self.tree_view.heading("type", text="Type")
        self.tree_view.heading("note", text="Note")
        self.tree_view.heading("literal", text="Literal")
        self.tree_view.heading("file", text="File")
        self.tree_view.heading("line", text="Line")

        self.tree_view.grid(row=0, column=0, sticky="news")

        scroll_bar = tkinter.ttk.Scrollbar(self.window, orient="vertical", command=self.tree_view.yview)
        self.tree_view.configure(yscrollcommand=scroll_bar.set)

        scroll_bar.grid(row=0, column=1, sticky='ns')

        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)

    def add_item(self, node, parent: tkinter.ttk.Treeview, note_to_this=""):
        if node is None:
            return
        if isinstance(node, ast.Node):
            if isinstance(node, ast.BlockStmt):
                child = self.insert(parent, node, repr(node), note_to_this)
                for line in node.lines:
                    self.add_item(line, child)
            elif isinstance(node, ast.LeafNode):
                self.insert(parent, node, repr(node), note_to_this)
            elif isinstance(node, ast.Expr):
                if isinstance(node, ast.UnaryExpr):
                    child = self.insert(parent, node, repr(node), note_to_this)
                    self.add_item(node.value, child, "value")
                elif isinstance(node, ast.BinaryExpr):
                    if isinstance(node, ast.FuncCall):
                        lit = "Call"
                        l_note = "call_obj"
                        r_note = "args"
                    else:
                        lit = repr(node)
                        l_note = "left"
                        r_note = "right"
                    child = self.insert(parent, node, lit, note_to_this)
                    self.add_item(node.left, child, l_note)
                    self.add_item(node.right, child, r_note)
                elif isinstance(node, ast.TernaryOperator):
                    child = self.insert(parent, node, repr(node), note_to_this)
                    self.add_item(node.left, child, "left")
                    self.add_item(node.mid, child, "mid")
                    self.add_item(node.right, child, "right")
                elif isinstance(node, ast.InDecrementOperator):
                    child = self.insert(parent, node, repr(node), note_to_this)
                    self.add_item(node.value, child, "value")
                elif isinstance(node, ast.FuncObj):
                    child = self.insert(parent, node, repr(node), note_to_this)
                    self.add_item(node.expr, child, "params")
            elif isinstance(node, ast.CondStmt):
                t = node.node_type
                if t == ast.IF_STMT:
                    node: ast.IfStmt
                    child = self.insert(parent, node, repr(node), note_to_this)
                    self.add_item(node.condition, child, "condition block")
                    self.add_item(node.then_block, child, "block if true")
                    self.add_item(node.else_block, child, "block if false")
                elif t == ast.WHILE_STMT:
                    node: ast.WhileStmt
                    child = self.insert(parent, node, repr(node), note_to_this)
                    self.add_item(node.condition, child, "condition block")
                    self.add_item(node.body, child, "do block")
                elif t == ast.FOR_LOOP_STMT:
                    node: ast.ForLoopStmt
                    child = self.insert(parent, node, repr(node), note_to_this)
                    self.add_item(node.condition, child, "condition block")
                    self.add_item(node.body, child, "do block")
            elif isinstance(node, ast.ImportNode):
                child = self.insert(parent, node, repr(node), note_to_this)
                self.add_item(node.import_name, child, "from " + node.path)
                self.add_item(node.block, child, "import")
            elif isinstance(node, ast.ClassStmt):
                child = self.insert(parent, node, repr(node), note_to_this)
                for sc in node.superclass_nodes:
                    self.add_item(sc, child, "{} extends".format(node.class_name))
                self.add_item(node.block, child, "class body")
            elif isinstance(node, ast.DefStmt):
                child = self.insert(parent, node, repr(node), note_to_this)
                self.add_item(node.params, child, "params")
                self.add_item(node.body, child, "function body")
            elif isinstance(node, ast.Arguments):
                child = self.insert(parent, node, repr(node), note_to_this)
                self.add_item(node.block, child, "args")
            elif isinstance(node, ast.StructNode):
                child = self.insert(parent, node, repr(node), note_to_this)
                self.add_item(node.block, child, "struct body")
            else:
                self.tree_view.insert(parent, 'end', text="Unknown type " + type(node).__name__)
        else:
            self.insert(parent, node, "", note_to_this)

    def insert(self, parent, node, literal, note):
        if isinstance(node, ast.Node):
            file, line = (node.file, node.line_num) if node.line_num > 0 else ("", "")
            return self.tree_view.insert(parent, 'end', text=repr(node), values=(type(node).__name__, literal, note,
                                                                                 file, line))
        else:
            return self.tree_view.insert(parent, 'end', text=repr(node), values=(type(node).__name__, literal, note,
                                                                                 "", ""))

    def show(self, node: ast.Node, main_path: str):
        self.window.title(main_path + " - SPL Abstract Syntax Tree Visualizer")
        self.add_item(node, "", "root")
        self.window.mainloop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Visualize an SPL abstract syntax tree")
    ap.add_argument('file_name', type=str)
    ap.add_argument('-ni', help="Do not automatically import lib.lang.sp", action='store_true')
    args = ap.parse_args()

    file_name = args.file_name
    ni = args.ni

    lexer = tpl_lexer.Tokenizer()
    lexer.setup(script.get_spl_path(), file_name, tpl_lexer.get_dir(file_name),
                import_lang=not ni)
    f = open(file_name, "r")
    lexer.tokenize(f)
    f.close()
    parser = psr.Parser(lexer.get_tokens())
    block = parser.parse()

    preprocessor = prep.Preprocessor()
    block = preprocessor.preprocess(block)

    vsr = Visualizer()
    vsr.show(block, file_name)
