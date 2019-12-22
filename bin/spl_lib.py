import bin.spl_memory as mem


class InvalidArgument:
    def __init__(self):
        pass

    def __str__(self):
        return "INVALID"


class CompileTimeException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


class SplException(CompileTimeException):
    def __init__(self, msg=""):
        CompileTimeException.__init__(self, msg)


class UnexpectedSyntaxException(SplException):
    def __init__(self, msg=""):
        SplException.__init__(self, msg)


class TypeException(SplException):
    def __init__(self, msg=""):
        SplException.__init__(self, msg)
