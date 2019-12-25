import sys
import bin.tpl_compiler as cmp
import bin.spl_parser as psr
import bin.spl_lexer as lex
import bin.tpl_preprocessor as pre
import bin.tpc_decompiler as decompiler
import script


def parse_args():
    args_dict = {"py": sys.argv[0], "src_file": None, "tar_file": None, "tpa_file": None, "optimize": 0,
                 "tokens": False, "ast": False}
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg[0] == "-":
            if len(arg) == 1:
                print("Illegal syntax")
            elif arg[1:].lower() == "a":
                i += 1
                args_dict["tpa_file"] = sys.argv[i]
            elif arg[1].lower() == "o":
                try:
                    op_level = int(arg[2:])
                    args_dict["optimize"] = op_level
                except ValueError:
                    print("Illegal optimize level")
            elif arg[1:].lower() == "tk":
                args_dict["tokens"] = True
            elif arg[1:].lower() == "ast":
                args_dict["ast"] = True
            else:
                print("Unknown flag '{}'".format(arg))
        elif args_dict["src_file"] is None:
            args_dict["src_file"] = arg
        elif args_dict["tar_file"] is None:
            args_dict["tar_file"] = arg
        else:
            print("Unexpected argument")
        i += 1
    return args_dict


if __name__ == '__main__':
    args = parse_args()
    if not args["src_file"] or not args["tar_file"]:
        print("Usage: python tpc.py -[FLAGS] source target")

    with open(args["src_file"], "r") as rf:
        lexer = lex.Tokenizer()
        lexer.setup(script.get_spl_path(), args["src_file"], lex.get_dir(args["py"]))
        lexer.tokenize(rf)

        tokens = lexer.get_tokens()

        if args["tokens"]:
            print(tokens)

        parser = psr.Parser(tokens)
        root = parser.parse()

        preprocessor = pre.Preprocessor()
        preprocessor.preprocess(root)

        if args["ast"]:
            print(root)
            print("========== End of AST ==========")

        compiler = cmp.Compiler(parser.literal_bytes)
        compiler.set_optimize(args["optimize"])
        byt = compiler.compile_all(root)

        with open(args["tar_file"], "wb") as wf:
            wf.write(byt)

        if args["tpa_file"]:
            with open(args["tpa_file"], "w") as wf:
                dec = decompiler.Decompiler(byt)
                dec.decompile(wf)
