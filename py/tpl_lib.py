class InvalidArgument:
    def __init__(self):
        pass

    def __str__(self):
        return "INVALID"


class CompileTimeException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


class TplException(CompileTimeException):
    def __init__(self, msg=""):
        CompileTimeException.__init__(self, msg)


class UnexpectedSyntaxException(TplException):
    def __init__(self, msg=""):
        TplException.__init__(self, msg)


class TypeException(TplException):
    def __init__(self, msg=""):
        TplException.__init__(self, msg)
