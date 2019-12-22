import io

EOF = -1
EOL = ";"
SYMBOLS = {"{", "}", ".", ",", "~"}
MIDDLE = {"(", ")", "[", "]"}
TERNARY_OPERATORS = {"?": True, ":": False}  # the bool value indicate whether this operator can begin a ternary
# operator
BINARY_OPERATORS = {"+": "add", "-": "sub", "*": "mul", "/": "truediv", "%": "mod",
                    "<": "lt", ">": "gt", "==": "eq", ">=": "ge", "<=": "le", "!=": "neq",
                    "&&": "and", "||": "or", "&": "band", "^": "xor", "|": "bor",
                    "<<": "lshift", ">>": "rshift", "===": "", "!==": "", "instanceof": "",
                    "subclassof": "", ":": "", "->": "lambda", "<-": "extendedby"}
UNARY_OPERATORS = {"!": "not"}
OTHERS = {"=", "@", ":", ":="}
ALL = [SYMBOLS, UNARY_OPERATORS, BINARY_OPERATORS, TERNARY_OPERATORS, OTHERS, MIDDLE]
# ALL = set().union(SYMBOLS) \
#     .union(BINARY_OPERATORS) \
#     .union(OTHERS) \
#     .union(MIDDLE) \
#     .union(UNARY_OPERATORS) \
#     .union(TERNARY_OPERATORS)
# RESERVED = {"class", "fn", "if", "else", "new", "extends", "return", "break", "continue",
#             "true", "false", "null", "operator", "while", "for", "import", "namespace", "throw", "try", "catch",
#             "finally", "abstract", "const", "var", "assert", "as", "struct"}
RESERVED = {"fn", "if", "else", "return", "break", "continue", "true", "false", "null", "while", "for",
            "const", "var", "assert", "struct", "include"}
RESERVED_FOR_BRACE = {"return"}
LAZY = {"&&", "||"}
OMITS = {"\n", "\r", "\t", " "}
OP_EQ = {"+", "-", "*", "/", "%", "&", "^", "|", "<<", ">>"}
ESCAPES = {"n": "\n", "t": "\t", "0": "\0", "a": "\a", "r": "\r", "f": "\f", "v": "\v", "b": "\b", "\\": "\\"}
NO_BUILD_LINE = {"catch", "finally"}

NO_CLASS_NAME = {"Object"}


# PUBLIC = 0
# PRIVATE = 1


def is_in_all(keyword):
    for s in ALL:
        if keyword in s:
            return True
    return False


def replace_escapes(text: str):
    lst = []
    in_slash = False
    for i in range(len(text)):
        ch = text[i]
        if in_slash:
            in_slash = False
            if ch in ESCAPES:
                lst.append(ESCAPES[ch])
            else:
                lst.append("\\" + ch)
        else:
            if ch == "\\":
                in_slash = True
            else:
                lst.append(ch)
    return "".join(lst)


def unexpected_token(token):
    if isinstance(token, IdToken):
        raise ParseException("Unexpected token: '{}', in {}, at line {}".format(token.symbol,
                                                                                token.file_name(),
                                                                                token.line_number()))
    else:
        raise ParseException("Unexpected token in '{}', at line {}".format(token.file_name(),
                                                                           token.line_number()))


def replace_extension(name: str, new_extension: str) -> str:
    """
    Replaces the content after the last '.' with the <new_extension>

    :param name:
    :param new_extension:
    :return:
    """
    dot_index = name.rfind(".")
    return name[:dot_index + 1] + new_extension


def string_to_bytes(s: str) -> bytes:
    b_value = s.encode("utf-8")
    return len(b_value).to_bytes(4, "big") + b_value


def read_string(f: io.BytesIO) -> str:
    b = f.read(4)
    length = int.from_bytes(b, "big")
    byte_str = f.read(length)
    return byte_str.decode("utf-8")


class Token:

    def __init__(self, line):
        self.line: int = line[0]
        self.file: str = line[1]

    def __str__(self):
        if self.is_eof():
            return "EOF"
        else:
            raise LexerException("Not Implemented")

    def __repr__(self):
        return self.__str__()

    def line_file_bytes(self) -> bytes:
        return string_to_bytes(str(self.line)) + string_to_bytes(self.file)

    def to_binary(self) -> bytes:
        if self.is_eof():
            return bytes([0])
        else:
            raise LexerException("Not Implemented")

    def is_eof(self):
        return self.line == EOF

    def is_eol(self):
        return False

    def is_number(self):
        return False

    def is_literal(self):
        return False

    def is_identifier(self):
        return False

    def is_doc(self):
        return False

    def file_name(self):
        return self.file

    def line_number(self):
        return self.line


class NumToken(Token):
    def __init__(self, line, v):
        Token.__init__(self, line)

        self.value: str = v

    def to_binary(self) -> bytes:
        return bytes([1]) + self.line_file_bytes() + string_to_bytes(self.value)

    def is_number(self):
        return True

    def __str__(self):
        return "NumToken({})".format(self.value)

    def __repr__(self):
        return self.__str__()


class LiteralToken(Token):
    def __init__(self, line, t: str, is_string):
        Token.__init__(self, line)

        self.text: str = replace_escapes(t)
        self.is_string = is_string

    def to_binary(self) -> bytes:
        return bytes([2]) + self.line_file_bytes() + string_to_bytes(self.text)

    def is_literal(self):
        return True

    def __str__(self):
        return "LIT({})".format(self.text)

    def __repr__(self):
        return self.__str__()


class DocToken(Token):
    def __init__(self, line, t: str):
        Token.__init__(self, line)

        self.text: str = t

    def to_binary(self) -> bytes:
        return bytes([4]) + self.line_file_bytes() + string_to_bytes(self.text)

    def is_doc(self):
        return True

    def __str__(self):
        return "DOC({})".format(self.text)

    def __repr__(self):
        return self.__str__()


class IdToken(Token):
    def __init__(self, line, s):
        Token.__init__(self, line)

        self.symbol: str = s

    def __eq__(self, other):
        return isinstance(other, IdToken) and other.symbol == self.symbol

    def to_binary(self) -> bytes:
        return bytes([3]) + self.line_file_bytes() + string_to_bytes(self.symbol)

    def is_identifier(self):
        return True

    def is_eol(self):
        return self.symbol == ";"

    def __str__(self):
        if self.is_eol():
            return "Id(EOL)"
        else:
            return "Id({})".format(self.symbol)

    def __repr__(self):
        return self.__str__()


class LexerException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


class ParseException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


class ParseEOFException(ParseException):
    def __init__(self, msg=""):
        ParseException.__init__(self, msg)
