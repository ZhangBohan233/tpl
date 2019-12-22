from bin import spl_ast as ast, spl_token_lib as stl
import bin.spl_types as typ

ABSTRACT_IDENTIFIER = {"fn", "class"}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens

        self.literal_bytes = bytearray((0, 1))
        self.string_lengths = {}  # ptr: length
        self.literals = {}  # lit: position
        self.bool_literals = {}

    def parse(self):
        """
        Parses the list of tokens stored in this Lexer, and returns the root node of the parsed abstract syntax
        tree.

        :return: the parsed block
        """
        parser = ast.AbstractSyntaxTree()
        i = 0
        func_count = 0
        par_count = 0  # count of parenthesis
        square_count = 0  # count of square bracket
        cond_nest_list = []
        call_nest_list = []
        param_nest_list = []
        square_nest_list = []
        is_abstract = False
        is_extending = False
        is_conditional = False
        is_type_param = False
        var_level = ast.ASSIGN
        brace_count = 0
        struct_braces = []
        # import_braces = []

        while True:
            try:
                token = self.tokens[i]
                line = (token.line_number(), token.file_name())
                if isinstance(token, stl.IdToken):
                    sym = token.symbol
                    if sym == "if":
                        parser.add_if(line)
                        is_conditional = True
                    elif sym == "else":
                        parser.add_else()
                    elif sym == "while":
                        parser.add_while(line)
                        is_conditional = True
                    elif sym == "for":
                        parser.add_for_loop(line)
                        is_conditional = True
                    elif sym == "return":
                        # parser.add_unary(line, "return")
                        parser.add_return(line)
                    elif sym == "break":
                        parser.add_break(line)
                    elif sym == "continue":
                        parser.add_continue(line)
                    elif sym == "true" or sym == "false":
                        lit_node = self.make_literal_node(line, True if sym == "true" else False, False)
                        parser.add_bool(line, lit_node)
                    elif sym == "null":
                        parser.add_null(line)
                    elif sym == "const":
                        var_level = ast.CONST
                    elif sym == "var":
                        var_level = ast.VAR
                    # elif sym == "@":
                    #     i += 1
                    #     next_token: stl.IdToken = self.tokens[i]
                    #     # titles.append(next_token.symbol)
                    #     parser.add_annotation(line, next_token.symbol)
                    elif sym == "{":
                        brace_count += 1
                        if is_conditional:
                            is_conditional = False
                            parser.build_expr()
                            parser.build_condition()
                            parser.new_block()
                        elif is_extending:
                            is_extending = False
                            parser.build_extends()
                            parser.new_block()
                        elif is_type_param:
                            parser.build_type_param()
                            typ = parser.pop_last()
                            func_node: ast.DefStmt = parser.get_last()
                            func_node.r_type = typ
                            parser.new_block()
                            is_type_param = False
                        else:
                            last_token = self.tokens[i - 1]
                            if isinstance(last_token, stl.IdToken) and \
                                    (last_token.symbol == ")" or  # is a function
                                     is_identifier_before_block(last_token.symbol)):  # is a class or a dotted import
                                parser.new_block()
                            else:
                                parser.add_dict()
                    elif sym == "}":
                        brace_count -= 1
                        parser.build_block()
                        parser.try_build_func()
                        # if is_this_list(import_braces, brace_count):
                        #     parser.build_import()
                        #     import_braces.pop()
                        if is_this_list(struct_braces, brace_count):
                            # parser.build_class()
                            parser.build_struct()
                            struct_braces.pop()
                        next_token = self.tokens[i + 1]
                        if not (isinstance(next_token, stl.IdToken) and next_token.symbol in stl.NO_BUILD_LINE):
                            parser.build_line()
                    elif sym == "(":
                        if i > 0 and is_call(self.tokens[i - 1]):
                            parser.add_call(line)
                            call_nest_list.append(par_count)
                        else:
                            parser.add_parenthesis()
                        par_count += 1
                    elif sym == ")":
                        par_count -= 1
                        next_sig_token = self.find_next_significant_token(i)
                        if is_this_list(call_nest_list, par_count):
                            parser.build_line()
                            parser.build_call()
                            call_nest_list.pop()
                        elif is_this_list(param_nest_list, par_count):
                            parser.build_func_params()
                            param_nest_list.pop()
                            parser.begin_type_param(line)
                            is_type_param = True
                            # i += 1  # omit the next ':' symbol
                        elif next_sig_token.is_identifier() and next_sig_token.symbol == "->":
                            parser.build_lambda_parameters()
                        else:
                            parser.build_parenthesis()
                    elif sym == "[":
                        if i > 0 and is_call(self.tokens[i - 1]):
                            parser.add_getitem(line)
                        else:
                            print(123123)
                        # else:
                        #     square_nest_list.append(square_count)
                        #     func_name = "list"
                        #     if i > 0:
                        #         last_token = self.tokens[i - 1]
                        #         if isinstance(last_token, stl.IdToken) and last_token.symbol == "~":
                        #             func_name = "array"
                        #     parser.add_name(line, func_name)
                        #     parser.add_call(line)
                        square_count += 1
                    elif sym == "]":
                        square_count -= 1
                        if is_this_list(square_nest_list, square_count):  # end of list creation
                            square_nest_list.pop()
                            parser.build_call()
                        else:
                            parser.build_getitem()
                    elif sym == "=":
                        # parser.build_expr()
                        # print(parser.get_last())
                        parser.add_assignment(line, var_level)
                        var_level = ast.ASSIGN
                    elif sym == ":=":
                        parser.build_expr()
                        parser.add_assignment(line, ast.VAR)
                    elif sym == ",":
                        if var_level == ast.ASSIGN:  # the normal level
                            parser.build_line()
                    elif sym == ".":
                        parser.add_dot(line)
                    elif sym == "~":  # a special mark
                        pass
                    elif sym == "fn":
                        # func_doc = self.get_doc(i)
                        i += 1
                        f_token: stl.IdToken = self.tokens[i]
                        f_name = f_token.symbol
                        push_back = 1
                        # if f_name == "(":
                        #     func_count += 1
                        #     push_back = 0
                        # elif f_name.isidentifier():
                        #     parser.add_name(line, f_name)
                        #     parser.add_assignment(line, ast.FUNC_DEFINE)
                        # else:
                        #     raise stl.ParseException("Illegal function name '{}', in file '{}', at line {}"
                        #                              .format(f_name, line[1], line[0]))
                        parser.add_function(line, f_name)
                        i += push_back
                        param_nest_list.append(par_count)
                        par_count += 1
                        # is_abstract = False
                    elif sym == "struct":
                        i += 1
                        name_token: stl.IdToken = self.tokens[i]
                        parser.add_struct(line, name_token.symbol)
                        struct_braces.append(brace_count)
                    # elif sym == "->":
                    #     parser.add_lambda(line)
                    # elif sym == "<-":
                    #     parser.add_anonymous_class(line)
                    # elif sym == "operator":
                    #     func_doc = self.get_doc(i)
                    #     i += 1
                    #     op_token = self.tokens[i]
                    #     group = stl.BINARY_OPERATORS
                    #     if isinstance(op_token, stl.NumToken):
                    #         v = int(op_token.value)
                    #         if v == 1:
                    #             group = stl.UNARY_OPERATORS
                    #         elif v == 2:
                    #             group = stl.BINARY_OPERATORS
                    #         elif v == 3:
                    #             group = stl.TERNARY_OPERATORS
                    #         else:
                    #             raise stl.ParseException("Unsupported operator kind")
                    #         i += 1
                    #         op_token = self.tokens[i]
                    #     op_name = "__" + group[op_token.symbol] + "__"
                    #     parser.add_name(line, op_name)
                    #     parser.add_assignment(line, ast.FUNC_DEFINE)
                    #     parser.add_function(line, False, func_doc)
                    #     param_nest_list.append(par_count)
                    #     par_count += 1
                    #     i += 1
                    # elif sym == "class":
                    #     class_doc = self.get_doc(i)
                    #     i += 1
                    #     c_token: stl.IdToken = self.tokens[i]
                    #     class_name = c_token.symbol
                    #     if class_name in stl.NO_CLASS_NAME:
                    #         raise stl.ParseException("Name '{}' is forbidden for class name".format(class_name))
                    #     parser.add_class(
                    #         (c_token.line_number(), c_token.file_name()),
                    #         class_name,
                    #         is_abstract,
                    #         class_doc
                    #     )
                    #     class_braces.append(brace_count)
                    #     is_abstract = False
                    # elif sym == "extends":
                    #     parser.add_extends()
                    #     is_extending = True
                    # elif sym == "abstract":
                    #     next_token = self.tokens[i + 1]
                    #     if isinstance(next_token, stl.IdToken) and next_token.symbol in ABSTRACT_IDENTIFIER:
                    #         is_abstract = True
                    #     else:
                    #         raise stl.ParseException("Unexpected token 'abstract', in file '{}', at line {}"
                    #                                  .format(line[1], line[0]))
                    #         # parser.add_abstract(line)
                    # elif sym == "new":
                    #     parser.add_unary(line, "new")
                    # elif sym == "throw":
                    #     parser.add_unary(line, "throw")
                    # elif sym == "try":
                    #     parser.add_try(line)
                    # elif sym == "catch":
                    #     parser.add_catch(line)
                    #     is_conditional = True
                    # elif sym == "finally":
                    #     parser.add_finally(line)
                    elif sym == "assert":
                        parser.add_unary(line, "assert")
                    elif sym == "++" or sym == "--":
                        parser.add_increment_decrement(line, sym)
                    elif sym in stl.TERNARY_OPERATORS and \
                            (parser.is_in_ternary() or stl.TERNARY_OPERATORS[sym]):
                        # This check should go strictly before the check of binary ops
                        if parser.is_in_ternary():
                            parser.finish_ternary(line, sym)
                        else:
                            parser.add_ternary(line, sym)
                    elif sym in stl.BINARY_OPERATORS:
                        if sym == "-" and (i == 0 or is_unary(self.tokens[i - 1])):
                            parser.add_unary(line, "neg")
                        elif sym == "*" and (i == 0 or is_unary(self.tokens[i - 1]) or is_type_param):
                            parser.add_unary(line, "unpack")
                        elif sym == "&" and (i == 0 or is_unary(self.tokens[i - 1])):  # the command-line notation
                            parser.add_unary(line, "pack")
                        elif sym == ":":
                            parser.add_type_node(line)
                        else:
                            parser.add_operator(line, sym)
                    elif sym in stl.UNARY_OPERATORS:
                        if sym == "!":
                            parser.add_unary(line, "!")
                        else:
                            parser.add_unary(line, sym)
                    elif sym[:-1] in stl.OP_EQ:
                        parser.add_operator(line, sym, True)
                    # elif sym == "import":
                    #     i += 2
                    #     name_token: stl.IdToken = self.tokens[i - 1]
                    #     path_token: stl.IdToken = self.tokens[i]
                    #     # print(name_token)
                    #     import_name = name_token.symbol
                    #     parser.add_import(line, import_name, path_token.symbol)
                    #     import_braces.append(brace_count)
                    elif token.is_eol():
                        if var_level != ast.ASSIGN:
                            # active = parser.get_active()
                            # # active.build_line()
                            # active.build_expr()
                            # parser.add
                            parser.add_assignment(line, var_level)
                            parser.add_undefined(line)
                            parser.build_line()
                            # print(parser.get_last())

                            var_level = ast.ASSIGN
                        parser.build_line()
                    else:
                        parser.add_name(line, sym)
                        # auth = stl.PUBLIC

                elif isinstance(token, stl.NumToken):
                    value = token.value
                    num = get_number(line, value)
                    num_lit = self.make_literal_node(line, num, False)
                    parser.add_number(line, num_lit)
                elif isinstance(token, stl.LiteralToken):
                    value = token.text
                    lit = self.make_literal_node(line, value, token.is_string)
                    if token.is_string:
                        str_len = self.string_lengths[lit.lit_pos]
                        parser.add_string_literal(line, lit, str_len)
                    else:
                        parser.add_char(line, lit)
                elif isinstance(token, stl.DocToken):
                    pass
                elif token.is_eof():
                    parser.build_line()
                    break
                else:
                    stl.unexpected_token(token)
                i += 1
            except stl.ParseException as e:
                raise e
            except Exception:
                raise stl.ParseException("Parse error in '{}', at line {}".format(self.tokens[i].file_name(),
                                                                                  self.tokens[i].line_number()))

        if par_count != 0 or len(call_nest_list) != 0 or len(cond_nest_list) != 0 or len(param_nest_list) or \
                len(square_nest_list) != 0 or brace_count != 0:
            raise stl.ParseEOFException(
                "Reach the end while parsing, {},{},{},{}".format(par_count, call_nest_list,
                                                                  cond_nest_list, param_nest_list))
        return parser.get_as_block()

    def get_doc(self, index):
        if index > 0:
            doc_token = self.tokens[index - 1]
            if isinstance(doc_token, stl.DocToken):
                return doc_token.text
        return ""

    def find_next_significant_token(self, index: int):
        index += 1
        while index < len(self.tokens):
            token = self.tokens[index]
            if not token.is_eol():
                return token
            index += 1

    def make_literal_node(self, lf, lit, make_string) -> ast.Literal:
        """
        Produce the literal node which does not contain any literal, but pointer to the stored literal bytes.

        :param self:
        :param lf: line, file
        :param lit: the literal, could be int, float, bool, or str
        :param make_string: True if make string, False if make char
        """
        # print(lit, type(lit))
        if isinstance(lit, bool):  # in python, bool is int but int is not bool
            b = typ.boolean_to_bytes(lit)
            lit_type = 2
        elif isinstance(lit, int):
            b = typ.int_to_bytes(lit)
            lit_type = 0
        elif isinstance(lit, float):
            b = typ.float_to_bytes(lit)
            lit_type = 1
        elif isinstance(lit, str):
            b = typ.string_to_bytes(lit)
            if make_string:
                lit_type = 3
                b += bytes(1)  # add the string terminator
            else:
                if len(b) != 1:
                    raise stl.ParseException("Only ascii characters can be char")
                lit_type = 4
        else:
            raise stl.ParseException("Unexpected literal type")

        if lit_type == 2:  # special case for boolean, since in python, bool and int has the same hash
            if lit:
                return ast.Literal(lf, 1, 2)
            else:
                return ast.Literal(lf, 0, 2)
        elif lit in self.literals:
            pos = self.literals[lit]
            node = ast.Literal(lf, pos, lit_type)
            return node
        else:
            ptr = len(self.literal_bytes)
            self.literals[lit] = ptr
            self.literal_bytes.extend(b)
            node = ast.Literal(lf, ptr, lit_type)
            if lit_type == 3:
                self.string_lengths[ptr] = len(b)
            return node


def get_number(line, v: str):
    try:
        if "." in v:
            return float(v)
        else:
            return int(v)
    except TypeError:
        raise stl.ParseException("Unexpected syntax: '{}', at line {}".format(v, line))


def is_call(last_token: stl.Token) -> bool:
    if last_token.is_identifier():
        last_token: stl.IdToken
        if (last_token.symbol.isidentifier() and last_token.symbol not in stl.RESERVED) or \
                last_token.symbol == "." or \
                last_token.symbol == ")" or \
                last_token.symbol == "]":
            return True
    return False


def is_identifier_before_block(s: str) -> bool:
    """
    Returns False if the next brace is a dict or set initialization

    :param s:
    :return:
    """
    if s in stl.RESERVED_FOR_BRACE:
        return False
    elif s.isidentifier():
        return True
    else:
        if len(s) > 0 and s[0] != "." and s[-1] != ".":
            s2 = s.replace(".", "").replace("\\", "").replace("/", "")
            if s2.isidentifier():
                return True
            else:
                if len(s2) > 2 and s2[1] == ":":  # special case for windows path
                    return s2[0].isidentifier() and s2[2:].isidentifier()
        return False


def is_this_list(lst: list, count: int) -> bool:
    """
    Returns true iff the list is not empty and the last item of the list equals the 'count'

    :param lst:
    :param count:
    :return:
    """
    return len(lst) > 0 and lst[-1] == count


def is_unary(last_token):
    """
    Returns True iff this should be an unary operator.
    False if it should be a minus operator.

    :param last_token:
    :type last_token: Token
    :return:
    :rtype: bool
    """
    if isinstance(last_token, stl.IdToken):
        if last_token.is_eol():
            return True
        else:
            sym = last_token.symbol
            if sym in stl.BINARY_OPERATORS:
                return True
            elif sym in stl.SYMBOLS:
                return True
            elif sym == "(":
                return True
            elif sym == "=":
                return True
            elif sym in stl.RESERVED:
                return True
            else:
                return False
    elif isinstance(last_token, stl.NumToken):
        return False
    else:
        return True
