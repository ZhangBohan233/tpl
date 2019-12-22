import bin.spl_memory as mem


class EnvironmentException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


class VariableException(EnvironmentException):
    def __init__(self, msg=""):
        EnvironmentException.__init__(self, msg)


class Undefined:
    def __init__(self):
        pass


class Type:
    def __init__(self, type_name: str, *arr_len):
        self.type_name = type_name
        self.array_lengths = arr_len

    def __str__(self):
        return "({}, {})".format(self.type_name, self.array_lengths)

    def total_len(self, mm):
        arr_len = 1
        for x in self.array_lengths:
            arr_len *= x
        return mm.get_type_size(self.type_name) * arr_len

    def unit_len(self, mm):
        if self.type_name[0] == "*":
            return mm.get_type_size(self.type_name[self.type_name.rfind("*") + 1:])
        return mm.get_type_size(self.type_name)


def type_total_len(t: Type) -> int:
    arr_len = 1
    for x in t.array_lengths:
        arr_len *= x
    return mem.MEMORY.get_type_size(t.type_name) * arr_len


def type_to_readable(t: Type) -> str:
    if len(t.array_lengths) == 0:
        return t.type_name
    else:
        r = t.type_name
        for ar in t.array_lengths:
            r += "[" + str(ar) + "]"
        return r


def is_array(t: Type) -> bool:
    return len(t.array_lengths) > 0


def is_pointer(t: Type) -> bool:
    return t.type_name[0] == "*"


UNDEFINED = Undefined()


class Environment:
    def __init__(self, outer):
        self.outer: Environment = outer
        # self.var_count = 0

        self.variables: dict[str: int] = {}
        self.constants = {}
        self.var_types: dict[str: Type] = {}  # name: (type name, arr len)

    def invalidate(self):
        raise EnvironmentException("Cannot invalidate a main environment")

    def is_global(self):
        return False

    def add_struct(self, name: str, struct):
        raise VariableException("Struct can only be defined under global environment")

    def get_struct(self, name: str):
        return self.outer.get_struct(name)

    def define_var(self, name: str, type_: Type, ptr: int):
        # check if already defined
        if self.contains_ptr(name):
            raise VariableException("Name '{}' already defined in this scope".format(name))

        # self.variables[name] = Variable(type_name, mem.MEMORY.type_sizes[type_name], ptr, array_length)
        self.variables[name] = ptr
        self.var_types[name] = type_

    def define_const(self, name: str, type_: Type, ptr: int):
        # check if already defined
        if self.contains_ptr(name):
            raise VariableException("Name '{}' already defined in this scope".format(name))

        # self.constants[name] = Variable(type_name, mem.MEMORY.type_sizes[type_name], ptr, array_length)
        self.variables[name] = ptr
        self.var_types[name] = type_

    def assign(self, name: str, ptr: int, lf):
        if name in self.variables:
            self.variables[name] = ptr
        elif not self.is_global():
            self.outer.assign(name, ptr, lf)
        else:
            raise VariableException("Variable or constant '{}' is not defined, in file '{}', at line {}"
                                    .format(name, lf[1], lf[0]))

    def define_function(self, name: str, func):
        raise EnvironmentException("Function must be declared in global scope")
        # self.functions[name] = func

    def get_function(self, name: str, lf):
        return self.outer.get_function(name, lf)

    def get(self, name: str, lf):
        if name in self.constants:
            return self.constants[name]
        if name in self.variables:
            return self.variables[name]
        return self.outer.get(name, lf)
        # raise VariableException("Variable or constant '{}' is not defined, in file '{}', at line {}"
        #                         .format(name, lf[1], lf[0]))

    def get_type_arr_len(self, name: str, lf) -> (str, int):
        if name in self.var_types:
            return self.var_types[name]
        if not self.is_global():
            return self.outer.get_type_arr_len(name, lf)
        raise VariableException("Variable or constant '{}' is not defined, in file '{}', at line {}"
                                .format(name, lf[1], lf[0]))

    def contains_ptr(self, name: str):
        if name in self.var_types:
            return True
        if not self.is_global():
            return self.outer.contains_ptr(name)
        return False

    def terminate(self, ptr):
        raise EnvironmentException("Return outside function")

    def is_terminated(self):
        return False

    def returned_ptr(self):
        raise EnvironmentException("Return outside function")

    def break_loop(self):
        raise EnvironmentException("Break outside loop")

    def pause_loop(self):
        raise EnvironmentException("Continue outside loop")

    def resume_loop(self):
        raise EnvironmentException("Continue outside loop")

    def is_stopped(self):
        return False


class MainAbstractEnvironment(Environment):
    def __init__(self, outer):
        Environment.__init__(self, outer)


class SubAbstractEnvironment(Environment):
    def __init__(self, outer):
        Environment.__init__(self, outer)

    def terminate(self, ptr):
        self.outer.terminate(ptr)

    def is_terminated(self):
        return self.outer.is_terminated()

    def returned_ptr(self):
        return self.outer.returned_ptr()

    def break_loop(self):
        self.outer.break_loop()

    def pause_loop(self):
        self.outer.pause_loop()

    def is_stopped(self):
        return self.outer.is_stopped()

    def invalidate(self):
        self.variables = {}
        self.constants = {}
        self.var_types = {}


class GlobalEnvironment(MainAbstractEnvironment):
    def __init__(self):
        MainAbstractEnvironment.__init__(self, None)

        self.structs = {}
        self.functions: dict = {}

    def define_function(self, name: str, func):
        self.functions[name] = func

    def get_function(self, name: str, lf):
        if name in self.functions:
            return self.functions[name]
        else:
            raise EnvironmentException("Function '{}' not defined".format(name))

    def is_global(self):
        return True

    def add_struct(self, name: str, struct):
        self.structs[name] = struct
        self.var_types[name] = Type(name)

    def get_struct(self, name: str):
        return self.structs[name]

    def get(self, name: str, lf):
        if name in self.constants:
            return self.constants[name]
        if name in self.variables:
            return self.variables[name]
        if name in self.structs:
            return self.structs[name]
        raise VariableException("Variable or constant '{}' is not defined, in file '{}', at line {}"
                                .format(name, lf[1], lf[0]))


class FunctionEnvironment(MainAbstractEnvironment):
    def __init__(self, outer):
        MainAbstractEnvironment.__init__(self, outer)

        self.terminated = False
        self.return_ptr = 0

    def terminate(self, ptr):
        self.terminated = True
        self.return_ptr = ptr

    def is_terminated(self):
        return self.terminated

    def returned_ptr(self):
        return self.return_ptr


class LoopEnvironment(SubAbstractEnvironment):
    def __init__(self, outer):
        SubAbstractEnvironment.__init__(self, outer)

        self.broken = False
        self.paused = False

    def break_loop(self):
        self.broken = True

    def pause_loop(self):
        self.paused = True

    def resume_loop(self):
        self.paused = False

    def is_stopped(self):
        return self.broken or self.paused


class BlockEnvironment(SubAbstractEnvironment):
    def __init__(self, outer):
        SubAbstractEnvironment.__init__(self, outer)
