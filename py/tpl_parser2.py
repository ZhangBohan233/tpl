import py.tpl_token_lib as ttl
import py.tpl_ast2 as ast


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens

    def parse(self):
        i = 0
        tk_len = len(self.tokens)

        builder = ast.BraceBuilder(None)

        par_builder = ast.BracketBuilder()

        line_builder = ast.LineBuilder()
        section_builder = ast.SectionBuilder()

        while i < tk_len:
            token: ttl.Token = self.tokens[i]
            lf = token.line, token.file
            if token.is_identifier():
                token: ttl.IdToken
                sym = token.symbol
                if sym == "(":
                    section_builder = ast.SectionBuilder(section_builder)
                elif sym == ")":

                    section_builder = section_builder.parent
                elif sym == "{":
                    if isinstance(builder, ast.ForLoopBuilder):
                        line_builder.add_section(section_builder, lf)
                        builder.add_line(line_builder, lf)
                        line_builder = ast.LineBuilder()
                        section_builder = ast.SectionBuilder()
                        builder.in_body = True
                    else:
                        builder = ast.BraceBuilder(builder)
                elif sym == "}":
                    builder.add_self_to_parent(lf)
                    builder = builder.parent
                elif sym == "for":
                    builder = ast.ForLoopBuilder(builder)
                elif sym == ",":
                    line_builder.add_section(section_builder, lf)
                    section_builder = ast.SectionBuilder()
                elif sym == ";":
                    line_builder.add_section(section_builder, lf)
                    builder.add_line(line_builder, lf)

                    line_builder = ast.LineBuilder()
                    section_builder = ast.SectionBuilder()
                elif sym in ttl.BINARY_OPERATORS:
                    section_builder.add_binary_expr(sym, lf)
                else:
                    section_builder.add_name(sym, lf)
            elif token.is_number():
                token: ttl.NumToken
                section_builder.add_num_literal(token.value, lf)
            elif token.is_literal():
                pass
            elif token.is_eof():
                break
            else:
                raise ttl.ParseException("Unknown token: {}".format(type(token)))

            i += 1

        print(builder.lines)
