import sys
import bin.tpl_compiler as cmp
import bin.spl_parser as psr
import bin.spl_lexer as lex
import bin.tpl_preprocessor as pre
import bin.tpc_decompiler as decompiler
import script


def parse_args():
    args_dict = {"py": sys.argv[0], "spa": False, "src_file": None, "tar_file": None, "spa_file": None}
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg[0] == "-":
            if arg[1:] == "a":
                args_dict["spa"] = True
                i += 1
                args_dict["spa_file"] = sys.argv[i]
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

        parser = psr.Parser(tokens)
        root = parser.parse()

        preprocessor = pre.Preprocessor()
        preprocessor.preprocess(root)

        print(root)
        print("========== End of AST ==========")

        compiler = cmp.Compiler(parser.literal_bytes)
        # compiler.compile(root)
        byt = compiler.compile_all(root)

        with open(args["tar_file"], "wb") as wf:
            wf.write(byt)

        if args["spa_file"]:
            with open(args["spa_file"], "w") as wf:
                dec = decompiler.Decompiler(byt)
                dec.decompile(wf)
