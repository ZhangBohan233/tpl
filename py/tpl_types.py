import struct
import sys


INT_LEN = 8
FLOAT_LEN = 8
PTR_LEN = 8
# BOOLEAN_LEN = 1
CHAR_LEN = 1
VOID_LEN = 0
CLASS_INFO_LEN = 24
OBJECT_HEADER_LEN = 8
CLASS_INFO_INTS = 3


class Type:
    def __init__(self, name, length):
        self.name = name
        self.length = length

    def __eq__(self, other):
        return isinstance(other, Type) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


def int_to_bytes(i: int) -> bytes:
    int_len = INT_LEN
    return i.to_bytes(int_len, sys.byteorder, signed=True)


def bytes_to_int(b: bytes) -> int:
    return int.from_bytes(b, sys.byteorder, signed=True)


def float_to_bytes(f: float) -> bytes:
    return bytes(struct.pack("d", f))


def bytes_to_float(b: bytes) -> float:
    return struct.unpack("d", b)[0]


def boolean_to_bytes(b: bool) -> bytes:
    return bytes((1,)) if b else bytes((0,))


def bytes_to_bool(by: bytes) -> bool:
    return bool(by[0])


def string_to_bytes(s: str) -> bytes:
    return s.encode("utf-8")


def bytes_to_string(b: bytes) -> str:
    return b.decode("utf8")


def char_to_bytes(c: str) -> bytes:
    return bytes((ord(c),))


def bytes_to_char(b: bytes) -> str:
    return chr(b[0])


def int_neg(v: bytes) -> bytes:
    i = bytes_to_int(v)
    return int_to_bytes(-i)


def int_add_int(v1: bytes, v2: bytes) -> bytes:
    li = bytes_to_int(v1)
    ri = bytes_to_int(v2)
    return int_to_bytes(li + ri)


def int_sub_int(v1: bytes, v2: bytes) -> bytes:
    li = bytes_to_int(v1)
    ri = bytes_to_int(v2)
    return int_to_bytes(li - ri)


def int_mul_int(v1: bytes, v2: bytes) -> bytes:
    li = bytes_to_int(v1)
    ri = bytes_to_int(v2)
    return int_to_bytes(li * ri)


def int_div_int(v1: bytes, v2: bytes) -> bytes:
    li = bytes_to_int(v1)
    ri = bytes_to_int(v2)
    return int_to_bytes(li // ri)


def int_add_float(v1: bytes, v2: bytes) -> bytes:
    li = bytes_to_int(v1)
    ri = int(bytes_to_float(v2))
    return int_to_bytes(li + ri)


def int_sub_float(v1: bytes, v2: bytes) -> bytes:
    li = bytes_to_int(v1)
    ri = int(bytes_to_float(v2))
    return int_to_bytes(li - ri)


def int_cmp_int(v1: bytes, v2: bytes) -> int:
    """
    :param v1:
    :param v2:
    :return: negative value if v1 < v2, 0 if v1 == v2, positive value if v1 > v2
    """
    i1 = bytes_to_int(v1)
    i2 = bytes_to_int(v2)
    return i1 - i2


def char_cmp_char(v1: bytes, v2: bytes) -> int:
    """
    :param v1:
    :param v2:
    :return: negative value if v1 < v2, 0 if v1 == v2, positive value if v1 > v2
    """
    i1 = v1[0]
    i2 = v2[0]
    return i1 - i2


def float_add_int(v1: bytes, v2: bytes) -> bytes:
    f = bytes_to_float(v1)
    i = bytes_to_int(v2)
    return float_to_bytes(f + i)


if __name__ == "__main__":
    f1 = float_to_bytes(7.5)
    b11 = bytes_to_float(f1)
    print(b11)
