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

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        return self.type_name == other.type_name and self.array_lengths == other.array_lengths

    def __ne__(self, other):
        return not self == other

    def total_len(self, mm):
        arr_len = 1
        for x in self.array_lengths:
            arr_len *= x
        return mm.get_type_size(self.type_name) * arr_len

    def unit_len(self, mm):
        if self.type_name[0] == "*":
            return mm.get_type_size(self.type_name[self.type_name.rfind("*") + 1:])
        return mm.get_type_size(self.type_name)


class AbstractFuncType(Type):
    def __init__(self):
        Type.__init__(self, "*")

    def __str__(self):
        return "fn"

    def __repr__(self):
        return self.__str__()


class FuncType(AbstractFuncType):
    def __init__(self, param_types: list, rtype: Type, func_type="f"):
        AbstractFuncType.__init__(self)

        self.param_types = param_types
        self.rtype = rtype
        self.func_type = func_type  # 'f' for function, 'n' for native function, 'c' for compile time function

    def __str__(self):
        return "fn(" + str(self.param_types) + ") -> " + str(self.rtype)

    def __eq__(self, other):
        if not isinstance(other, FuncType):
            return False
        return self.func_type == other.func_type and self.param_types == other.param_types and self.rtype == other.rtype

    def __ne__(self, other):
        return not self == other

    def total_len(self, mm):
        return mm.get_type_size("*")


def type_to_readable(t: Type) -> str:
    if isinstance(t, FuncType):
        s = "fn(" + ",".join([type_to_readable(p) for p in t.param_types]) + ")->"
        s += type_to_readable(t.rtype)
        return s
    else:
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
        self.constants: dict[str: int] = {}
        self.var_types: dict[str: Type] = {}  # name: (type name, arr len)

    def add_register(self, reg_id_neg):
        raise EnvironmentException("Cannot assign register outside of function")

    def is_global(self):
        return False

    def add_struct(self, name: str, struct):
        raise VariableException("Struct can only be defined under global environment")

    def get_struct(self, name: str):
        return self.outer.get_struct(name)

    def is_struct(self, name: str):
        return self.outer.is_struct(name)

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
        self.constants[name] = ptr
        self.var_types[name] = type_

    def get(self, name: str, lf, assign_const: bool):
        if name in self.constants:
            if assign_const:
                raise EnvironmentException("Cannot assign constant '{}', in file '{}', at line {}"
                                           .format(name, lf[1], lf[0]))
            else:
                return self.constants[name]
        if name in self.variables:
            return self.variables[name]
        return self.outer.get(name, lf, assign_const)

    def get_type_arr_len(self, name: str, lf) -> (str, int):
        if name in self.var_types:
            return self.var_types[name]
        return self.outer.get_type_arr_len(name, lf)

    def contains_ptr(self, name: str):
        if name in self.var_types:
            return True
        if not self.is_global():
            return self.outer.contains_ptr(name)
        return False

    def get_step_label(self):
        raise EnvironmentException("Continue outside loop")

    def get_end_label(self):
        raise EnvironmentException("Break outside loop")


class MainAbstractEnvironment(Environment):
    def __init__(self, outer):
        Environment.__init__(self, outer)


class SubAbstractEnvironment(Environment):
    def __init__(self, outer):
        Environment.__init__(self, outer)

    def add_register(self, reg_id_neg):
        self.outer.add_register(reg_id_neg)


class GlobalEnvironment(MainAbstractEnvironment):
    def __init__(self):
        MainAbstractEnvironment.__init__(self, None)

        self.structs = {}

    def get_type_arr_len(self, name: str, lf) -> (str, int):
        if name in self.var_types:
            return self.var_types[name]
        raise VariableException("Variable or constant '{}' is not defined, in file '{}', at line {}"
                                .format(name, lf[1], lf[0]))

    def is_global(self):
        return True

    def add_struct(self, name: str, struct):
        self.structs[name] = struct
        self.var_types[name] = Type(name)

    def get_struct(self, name: str):
        return self.structs[name]

    def is_struct(self, name: str):
        return name in self.structs

    def get(self, name: str, lf, assign_const: bool):
        if name in self.constants:
            if assign_const:
                raise EnvironmentException("Cannot assign constant '{}', in file '{}', at line {}"
                                           .format(name, lf[1], lf[0]))
            else:
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

        self.registers = []

    def add_register(self, reg_id_neg):
        self.registers.append(reg_id_neg)


class StructEnvironment(MainAbstractEnvironment):
    def __init__(self, outer):
        MainAbstractEnvironment.__init__(self, outer)


class LoopEnvironment(SubAbstractEnvironment):
    def __init__(self, outer, step_label, end_label):
        SubAbstractEnvironment.__init__(self, outer)

        self.step_label = step_label
        self.end_label = end_label

    def get_step_label(self):
        return self.step_label

    def get_end_label(self):
        return self.end_label


class BlockEnvironment(SubAbstractEnvironment):
    def __init__(self, outer):
        SubAbstractEnvironment.__init__(self, outer)

    def get_step_label(self):
        return self.outer.get_step_label()

    def get_end_label(self):
        return self.outer.get_end_label()
