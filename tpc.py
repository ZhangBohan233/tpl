import sys
import time
import bin.tpl_compiler as cmp
import bin.spl_parser as psr
import bin.tpl_lexer as lex
import bin.tpl_ast_optimizer as pre
import bin.tpa_generator as decompiler
import bin.tpa_optimizer as optimizer
import script


def parse_args():
    args_dict = {"py": sys.argv[0], "src_file": None, "tar_file": None, "optimize": 0, "no_lang": False,
                 "tokens": False, "ast": False}
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg[0] == "-":
            if len(arg) == 1:
                print("Illegal syntax")
            elif arg[1:].lower() == "nl" or arg[1:].lower() == "-no-lang":
                args_dict["no_lang"] = True
            elif arg[1].lower() == "o":
                try:
                    op_level = int(arg[2:])
                    args_dict["optimize"] = op_level
                except ValueError:
                    print("Illegal optimize level")
            elif arg[1:].lower() == "tk" or arg[1:].lower() == "-tokens":
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
    t0 = time.time()

    args = parse_args()
    if not args["src_file"] or not args["tar_file"]:
        print("Usage: python tpc.py -[FLAGS] source target")

    with open(args["src_file"], "r") as rf:
        lexer = lex.Tokenizer()
        lexer.setup(script.get_spl_path(), args["src_file"], lex.get_dir(args["py"]), not args["no_lang"])
        lexer.tokenize(rf)

        tokens = lexer.get_tokens()

        if args["tokens"]:
            print(tokens)

        parser = psr.Parser(tokens)
        root = parser.parse()

        tree_optimizer = pre.AstOptimizer(root, parser, args["optimize"])
        tree_optimizer.optimize()

        if args["ast"]:
            print(root)
            print("========== End of AST ==========")

        compiler = cmp.Compiler(parser.literal_bytes)
        # compiler.set_optimize(args["optimize"])
        byt = compiler.compile_all(root)

        tar_name = args["tar_file"]
        pure_name = tar_name[:tar_name.rfind(".")]
        tpa_name = pure_name + ".tpa"

        with open(tpa_name, "w") as wf:
            dec = decompiler.TPAssemblyCompiler(byt)
            dec.compile(wf)

        if args["optimize"] > 1:
            # print("Optimization currently unavailable")
            # exit(1)
            with open(tpa_name, "r") as tpa_f:
                tpa_text = tpa_f.read()
                opt_par = optimizer.TpaParser(tpa_text)
                opt = optimizer.Optimizer(opt_par)
                opt.optimize(args["optimize"])

                byt = opt_par.to_byte_code()
                opt_tpa_name = pure_name + ".o.tpa"
                with open(opt_tpa_name, "w") as wf2:
                    dec2 = decompiler.TPAssemblyCompiler(byt)
                    dec2.compile(wf2)

        with open(tar_name, "wb") as wf:
            wf.write(byt)

    t1 = time.time()
    print("Compilation finished in {} seconds.".format(t1 - t0))
