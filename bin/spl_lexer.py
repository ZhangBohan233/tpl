import _io
from bin import spl_token_lib as stl
import os

# SPL_PATH = os.getcwd()

OTHER_ARITHMETIC = {"*", "/", "%"}
SELF_CONCATENATE = {
    0, 1, 8, 9, 10, 11, 14, 17, 20, 21
}
CROSS_CONCATENATE = {
    (8, 9),  # >=
    (20, 9),  # <=
    (1, 0), (0, 12), (12, 0), (15, 9),
    (17, 9),  # +=
    (21, 9),  # -=
    (100, 9), (16, 9), (10, 9), (11, 9),
    (1, 14), (14, 1), (0, 14), (14, 0),
    (19, 9),  # :=
    (21, 8),  # ->
    (20, 21)  # <-
}
LINE_FILE = 0, "TOKENIZER"


class Tokenizer:
    """
    :type tokens: list of Token
    """

    def __init__(self):
        self.tokens = []
        # self.import_lang = True
        self.spl_path = ""
        self.script_dir = ""
        self.file_name = ""
        # self.link = False

    def setup(self, spl_path: str, file_name: str, script_dir: str):
        """
        Sets up the parameters of this lexer.

        The <file_name> will be recorded in tokens and ast nodes, which is used for properly displaying
        the error message, if any error occurs. This parameter does not contribute to the actual interpreting.

        The <script_dir> is used to find the importing files, which is important to run the script correctly.

        :param spl_path: the directory path of spl interpreter
        :param file_name: the name of the main script
        :param script_dir: the directory of the main script
        # :param imported: the set of imported file names
        # :param link: whether to write the result to file
        :return:
        """
        self.spl_path = spl_path
        self.file_name = file_name
        self.script_dir = script_dir
        # self.imported = imported
        # self.link = link
        # self.import_lang = import_lang

    def tokenize(self, source):
        """
        Tokenize the source spl source code into a list of tokens, stored in the memory of this Lexer.

        :param source: the source code, whether an opened file or a list of lines.
        :return: None
        """
        self.tokens.clear()
        # if self.import_lang and self.file_name[-7:] != "lang.tp":
        #     self.tokens += [stl.IdToken(LINE_FILE, "import"), stl.IdToken(LINE_FILE, "namespace"),
        #                     stl.LiteralToken(LINE_FILE, "lang")]
        #     self.find_import(0, 3)

        # if isinstance(source, list):
        #     self.tokenize_text(source)
        # else:
        self.tokenize_file(source)

    def tokenize_file(self, file: _io.TextIOWrapper):
        """
        :param file:
        :return:
        """
        line = file.readline()
        line_num = 1
        in_doc = False
        doc = ""
        while line:
            tup = (line_num, self.file_name)
            last_index = len(self.tokens)
            in_doc, doc = self.proceed_line(line, tup, in_doc, doc)
            self.find_include(last_index, len(self.tokens))
            line = file.readline()
            line_num += 1

        self.tokens.append(stl.Token((stl.EOF, None)))
        # if self.link:
        #     self._write_to_file()

    # def tokenize_text(self, lines):
    #     doc = ""
    #     in_doc = False
    #     for i in range(len(lines)):
    #         line_num = i + 1
    #         tup = (line_num, self.file_name)
    #         line = lines[i]
    #         last_index = len(self.tokens)
    #         in_doc, doc = self.proceed_line(line, tup, in_doc, doc)
    #         self.find_import(last_index, len(self.tokens))
    #
    #     self.tokens.append(stl.Token((stl.EOF, None)))

    # def restore_tokens(self, file: _io.BytesIO):
    #     self.tokens.clear()
    #     while True:
    #         flag = int.from_bytes(file.read(1), "big")
    #         if flag == 0:
    #             self.tokens.append(stl.Token((stl.EOF, None)))
    #             break
    #         else:
    #             line = int(stl.read_string(file))
    #             file_name = stl.read_string(file)
    #             lf = line, file_name
    #             if flag == 1:
    #                 token: stl.NumToken = stl.NumToken(lf, stl.read_string(file))
    #             elif flag == 2:
    #                 token: stl.LiteralToken = stl.LiteralToken(lf, stl.read_string(file), True)
    #             elif flag == 3:
    #                 token: stl.IdToken = stl.IdToken(lf, stl.read_string(file))
    #             elif flag == 4:
    #                 token: stl.DocToken = stl.DocToken(lf, stl.read_string(file))
    #             else:
    #                 raise stl.ParseException("Unknown flag: {}".format(flag))
    #             self.tokens.append(token)

    def proceed_line(self, line: str, line_num: (int, str), in_doc: bool, doc: str) -> (bool, str):
        """ Tokenize a line.

        :param line: line to be proceed
        :param line_num: the line number and the name of source file
        :param in_doc: whether it is currently in docstring, before proceed this line
        :param doc: the current doc
        :return: whether it is currently in docstring, after proceed this line
        """
        in_single = False
        in_double = False
        literal = ""
        non_literal = ""

        length = len(line)
        i = -1
        while i < length - 1:
            i += 1
            ch = line[i]
            if not in_double and not in_single:
                if in_doc:
                    if ch == "*" and i < length - 1 and line[i + 1] == "/":
                        in_doc = False
                        i += 2
                        continue
                else:
                    if ch == "/" and i < length - 1 and line[i + 1] == "*" and (i == 0 or line[i - 1] != "/"):
                        in_doc = True
                        i += 1

            if not in_doc:
                if len(doc) > 0:
                    self.tokens.append(stl.DocToken(line_num, doc[2:]))
                    doc = ""
                if in_double:
                    if ch == '"':
                        in_double = False
                        self.tokens.append(stl.LiteralToken(line_num, literal, True))
                        literal = ""
                        continue
                elif in_single:
                    if ch == "'":
                        in_single = False
                        self.tokens.append(stl.LiteralToken(line_num, literal, False))
                        literal = ""
                        continue
                else:
                    if ch == '"':
                        in_double = True
                        self.line_tokenize(non_literal, line_num)
                        non_literal = ""
                        continue
                    elif ch == "'":
                        in_single = True
                        self.line_tokenize(non_literal, line_num)
                        non_literal = ""
                        continue
                if in_single or in_double:
                    literal += ch
                else:
                    non_literal += ch
                    if len(non_literal) > 1 and non_literal[-2:] == "//":
                        self.line_tokenize(non_literal[:-2], line_num)
                        non_literal = ""
                        break
            else:
                doc += ch

        if len(non_literal) > 0:
            self.line_tokenize(non_literal, line_num)

        return in_doc, doc

    def line_tokenize(self, non_literal, line_num):
        """
        Tokenize a line, with string literals removed.

        :param non_literal: text to be tokenize, no string literal
        :param line_num: the line number
        :return: None
        """
        lst = normalize(non_literal)
        for part in lst:
            if part.isidentifier():
                self.tokens.append(stl.IdToken(line_num, part))
            elif is_float(part):
                self.tokens.append(stl.NumToken(line_num, part))
            elif is_integer(part):
                self.tokens.append(stl.NumToken(line_num, part))
            elif stl.is_in_all(part):
                self.tokens.append(stl.IdToken(line_num, part))
            elif part[:-1] in stl.OP_EQ:
                self.tokens.append(stl.IdToken(line_num, part))
            elif part == stl.EOL:
                self.tokens.append(stl.IdToken(line_num, stl.EOL))
            elif part in stl.OMITS:
                pass
            else:
                raise stl.ParseException("Unknown symbol: '{}', at line {}".format(part, line_num))

    def find_include(self, from_, to):
        for i in range(from_, to, 1):
            token = self.tokens[i]
            if isinstance(token, stl.IdToken) and token.symbol == "include":
                next_token: stl.LiteralToken = self.tokens[i + 1]
                name = next_token.text

                if name[-3:] == ".tp":  # user lib
                    if len(self.script_dir) == 0:
                        file_name = name[:-3] + ".tp"
                    else:
                        file_name = self.script_dir + "{}{}".format("/", name[:-3]) + ".tp"
                else:  # system lib
                    file_name = "{}{}lib{}{}.tp".format(self.spl_path, os.sep, os.sep, name)

                self.tokens.pop(i + 1)  # remove the import name token
                self.tokens.pop(i)  # remove the 'include' token

                self.include_file(file_name)
                break

    def include_file(self, file_name):
        with open(file_name, "r") as file:
            lexer = Tokenizer()
            lexer.setup(self.spl_path, file_name, get_dir(file_name))
            lexer.tokenize(file)
            self.tokens += lexer.tokens
            self.tokens.pop()  # remove the EOF token

    # def find_import(self, from_, to):
    #     """
    #     Looks for import statement between the given slice of the tokens list.
    #
    #     :param from_: the beginning position of search
    #     :param to: the end position of search
    #     :return: None
    #     """
    #     for i in range(from_, to, 1):
    #         token = self.tokens[i]
    #         if isinstance(token, stl.IdToken) and token.symbol == "import":
    #             next_token: stl.Token = self.tokens[i + 1]
    #             namespace_token = None
    #             if isinstance(next_token, stl.IdToken) and next_token.symbol == "namespace":
    #                 namespace_token = next_token
    #                 self.tokens.pop(i + 1)
    #                 path_token: stl.LiteralToken = self.tokens[i + 1]
    #             elif isinstance(next_token, stl.LiteralToken):
    #                 path_token: stl.LiteralToken = self.tokens[i + 1]
    #             else:
    #                 raise stl.ParseException("Unexpected token in file '{}', at line {}"
    #                                          .format(next_token.file, next_token.line))
    #             name = path_token.text
    #
    #             if name[-3:] == ".tp":  # user lib
    #                 if len(self.script_dir) == 0:
    #                     file_name = name[:-3] + ".tp"
    #                 else:
    #                     file_name = self.script_dir + "{}{}".format("/", name[:-3]) + ".tp"
    #                     # file_name = "{}{}{}".format(self.script_dir, os.sep, name[:-3]).replace(".", "/") + ".tp"
    #                 if "/" in name:
    #                     import_name = name[name.rfind("/") + 1:-3]
    #                 else:
    #                     import_name = name[:-3]
    #             else:  # system lib
    #                 file_name = "{}{}lib{}{}.tp".format(self.spl_path, os.sep, os.sep, name)
    #                 import_name = name
    #
    #             if len(self.tokens) > i + 2:
    #                 as_token: stl.IdToken = self.tokens[i + 2]
    #                 if as_token.symbol == "as":
    #                     if namespace_token is not None:
    #                         raise stl.ParseException("Unexpected combination 'import namespace ... as ...'")
    #                     name_token: stl.IdToken = self.tokens[i + 3]
    #                     import_name = name_token.symbol
    #                     self.tokens.pop(i + 1)
    #                     self.tokens.pop(i + 1)
    #
    #             self.tokens.pop(i + 1)  # remove the import name token
    #
    #             self.import_file(file_name, import_name)
    #             if namespace_token:
    #                 lf = namespace_token.line, namespace_token.file
    #                 self.tokens.append(namespace_token)
    #                 self.tokens.append(stl.IdToken(lf, import_name))
    #                 self.tokens.append(stl.IdToken(lf, stl.EOL))
    #             break
    #
    # def import_file(self, full_path, import_name):
    #     """
    #     Imports an external tp file.
    #
    #     This method tokenize the imported file, and inserts all tokens except the EOF token of the imported
    #     file into the current file.
    #
    #     :param full_path: the path of the file to be imported
    #     :param import_name: the name to be used
    #     """
    #     with open(full_path, "r") as file:
    #         lexer = Tokenizer()
    #         lexer.setup(self.spl_path, full_path, get_dir(full_path))
    #         # lexer.script_dir = get_dir(full_path)
    #         lexer.tokenize(file)
    #         # print(lexer.tokens)
    #         self.tokens.append(stl.IdToken(LINE_FILE, import_name))
    #         self.tokens.append(stl.IdToken(LINE_FILE, full_path))
    #         self.tokens.append(stl.IdToken(LINE_FILE, "{"))
    #         self.tokens += lexer.tokens
    #         self.tokens.pop()  # remove the EOF token
    #         self.tokens.append(stl.IdToken(LINE_FILE, "}"))

    def get_tokens(self):
        """
        Returns the tokens list.

        :return: the tokens list
        """
        return self.tokens

    def _write_to_file(self):
        name = stl.replace_extension(self.file_name, "lsp")
        with open(name, "wb") as wf:
            for token in self.tokens:
                wf.write(token.to_binary())


def normalize(string):
    """
    Splits a line to tokens.

    :type string: str
    :param string:
    :return:
    :type: list
    """
    if string.isidentifier():
        return [string]
    else:
        lst = []
        if len(string) > 0:
            s = string[0]
            last_type = char_type(s)

            for i in range(1, len(string), 1):
                char = string[i]
                t = char_type(char)
                if (t in SELF_CONCATENATE and t == last_type) or ((last_type, t) in CROSS_CONCATENATE):
                    s += char
                else:
                    put_string(lst, s)
                    s = char
                last_type = t
            put_string(lst, s)
        return lst


def put_string(lst: list, s: str):
    if len(s) > 1 and s[-1] == ".":  # Scenario of a name ended with a number.
        lst.append(s[:-1])
        lst.append(s[-1])
    else:
        lst.append(s)


def char_type(ch):
    """
    :type ch: string
    :param ch:
    :return:
    """
    if ch.isdigit():
        return 0
    elif ch.isalpha():
        return 1
    elif ch == "{":
        return 2
    elif ch == "}":
        return 3
    elif ch == "(":
        return 4
    elif ch == ")":
        return 5
    elif ch == ";":
        return 6
    elif ch == "\n":
        return 7
    elif ch == ">":
        return 8
    elif ch == "=":
        return 9
    elif ch == "&":
        return 10
    elif ch == "|":
        return 11
    elif ch == ".":
        return 12
    elif ch == ",":
        return 13
    elif ch == "_":
        return 14
    elif ch == "!":
        return 15
    elif ch == "^":
        return 16
    elif ch == "+":
        return 17
    elif ch == "@":
        return 18
    elif ch == ":":
        return 19
    elif ch == "<":
        return 20
    elif ch == "-":
        return 21
    elif ch in OTHER_ARITHMETIC:
        return 100
    else:
        return -1


def is_integer(num_str: str) -> bool:
    """

    :param num_str:
    :return:
    """
    if len(num_str) == 0:
        return False
    for ch in num_str:
        if not ch.isdigit() and ch != "_":
            return False
    return True


def is_float(num_str: str) -> bool:
    """
    :param num_str:
    :return:
    """
    if "." in num_str:
        index = num_str.index(".")
        front = num_str[:index]
        back = num_str[index + 1:]
        if len(front) > 0:
            if not is_integer(front):
                return False
        if is_integer(back):
            return True
    return False


def get_dir(f_name: str):
    if os.sep in f_name:
        return f_name[:f_name.rfind(os.sep)]
    elif "/" in f_name:
        return f_name[:f_name.rfind("/")]
    else:
        return ""
