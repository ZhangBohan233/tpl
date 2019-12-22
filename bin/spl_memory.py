class MemoryException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


class Heap:
    """ Heap.

    This is a max heap

    ===== Attributes =====
    """
    def __init__(self):
        self.heap = []

    def __len__(self):
        return len(self.heap)

    def __str__(self):
        return str(self.heap)

    def copy(self):
        h = Heap()
        h.heap = self.heap.copy()
        return h

    @staticmethod
    def _compare_node(node, other):
        return node < other

    def _heapify(self, index):
        left = (index + 1) * 2 - 1
        right = (index + 1) * 2

        extreme = self.heap[index]
        is_left = True
        if left < len(self.heap):
            if self._compare_node(extreme, self.heap[left]):
                extreme = self.heap[left]
        if right < len(self.heap):
            if self._compare_node(extreme, self.heap[right]):
                extreme = self.heap[right]
                is_left = False
        if self._compare_node(self.heap[index], extreme):
            if is_left:
                self._swap(index, left)
                self._heapify(left)
            else:
                self._swap(index, right)
                self._heapify(right)

    def _rise_node(self, index):
        parent_index = (index + 1) // 2 - 1
        if parent_index >= 0:
            parent_value = self.heap[parent_index]
            if self._compare_node(parent_value, self.heap[index]):
                self._swap(index, parent_index)
                self._rise_node(parent_index)

    def _swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def build_heap(self, lst: list):
        self.heap = lst.copy()
        mid = len(self.heap) // 2 - 1
        for i in range(mid, -1, -1):
            self._heapify(i)

    def insert(self, value):
        """ Insert a new value into this heap, while keeping the heap property. """
        self.heap.append(value)
        self._rise_node(len(self.heap) - 1)

    def get(self):
        """ Returns the minimum element in this heap. """
        return self.heap[0]

    def extract(self):
        """ Extracts the minimum element in this heap. """
        self._swap(0, -1)
        minimum = self.heap.pop()
        if len(self.heap) > 0:
            self._heapify(0)
        return minimum

    def print_sorted(self):
        h = self.copy()
        lst = []
        while len(h) > 0:
            lst.append(h.extract())
        lst.reverse()
        print(lst)

    # def print_heap(self):
    #     import math
    #     height = math.ceil(math.log2(self.__len__()))
    #     width = 2 ** height
    #     index = 0
    #     lst = []
    #     for level in range(height):
    #         exp = 2 ** level
    #         interval = round(width / exp)
    #         lst.append((height - level - 1) * height * '  ')
    #         for _ in range(exp):
    #             if index == self.__len__():
    #                 break
    #             string = '(' + str(self.heap[index]) + ')'
    #             lst.append(string)
    #             lst.append((interval + 4 - len(string)) * ' ')
    #             index += 1
    #         print(''.join(lst))
    #         lst.clear()


class Memory:
    def __init__(self):
        self.vm_size = 32768
        self.memory = bytearray(self.vm_size)

        self.stack_start = 9
        self.literal_start = 1024
        self.global_start = 1024
        self.heap_start = 1024

        # self.available = []
        self.available2 = Heap()

        self.call_stack_begins = []

        self.type_sizes = {
            "int": 8,
            "float": 8,
            "boolean": 1,
            "char": 1,
            "void": 0
        }
        self.pointer_length = self.type_sizes["int"]

        self.sp = 1 + self.pointer_length
        self.gp = 0

    def initialize(self, literal_bytes: bytes):
        length = len(literal_bytes)
        self.global_start += length
        self.memory[self.literal_start: self.global_start] = literal_bytes
        self.gp = self.global_start
        # self._generate_available()

    def get_type_size(self, name: str):
        if name[0] == "*":  # is a pointer
            return self.pointer_length
        return self.type_sizes[name]

    def add_type(self, name: str, length: int):
        self.type_sizes[name] = length

    def allocate(self, byt: bytearray) -> int:
        length = len(byt)
        ptr = self.allocate_empty(length)
        self.set(ptr, byt)
        return ptr

    def allocate_empty(self, length: int) -> int:
        if len(self.call_stack_begins) == 0:
            ptr = self.gp
            self.gp += length
        else:
            ptr = self.sp
            self.sp += length
            if self.sp >= self.literal_start:
                raise MemoryException("Stack overflow")
        return ptr

    def push_stack(self):
        self.call_stack_begins.append(self.sp)

    def restore_stack(self):
        self.sp = self.call_stack_begins.pop()

    def get_last_call(self):
        return self.call_stack_begins[-1]

    def set(self, ptr: int, b: bytes):
        self._check_range(ptr)
        self.memory[ptr: ptr + len(b)] = b

    def get(self, ptr, length) -> bytes:
        self._check_range(ptr)
        return self.memory[ptr: ptr + length]

    def mem_copy(self, from_ptr, to_ptr, length):
        b = self.get(from_ptr, length)
        self.set(to_ptr, b)

    def get_literal_ptr(self, lit_loc) -> int:
        return self.literal_start + lit_loc

    def get_char_array(self, ptr) -> bytes:
        end = ptr
        while self.memory[end] != 0:
            end += 1
        return self.get(ptr, end - ptr)

    def malloc(self, length) -> int:
        """
        Allocate memory of length <length> in the heap space and returns the pointer this memory to the user.

        This method will store extra information in the heap.

        :param length:
        :return:
        """
        reserved_len = self.get_type_size("int")
        total_len = length + reserved_len
        # ind = self._find_available(total_len)
        # loc = self.available[ind]
        # self.available[ind - total_len + 1: ind + 1] = []
        loc = self._find_available2(total_len)
        b_len = int_to_bytes(length)
        self.set(loc, b_len)  # stores the allocated length before the returned position
        return loc + reserved_len

    def free(self, ptr):
        reserved_len = self.get_type_size("int")
        begin = ptr - reserved_len
        b_len = self.get(begin, reserved_len)
        allocated_len = bytes_to_int(b_len)
        length = allocated_len + reserved_len
        for i in range(length):
            ava = begin
            # self._check_in_heap(ava)
            self.available2.insert(ava)
            # self.available.append(ava)

    def print_memory(self):
        print("stack pointer: {}, heap available: {}".format(self.sp, len(self.available2)))
        print(self.memory[:self.literal_start])
        print(self.memory[self.literal_start:self.global_start])
        print(self.memory[self.global_start:self.heap_start])
        print(self.memory[self.heap_start:])

    def _check_range(self, ptr: int):
        if ptr == 0:
            raise MemoryException("Trying to access null pointer")
        if self.sp <= ptr < self.literal_start:
            raise MemoryException("Unreachable stack location {}. Current tp: {}".format(ptr, self.sp))
        if ptr < 0 or ptr >= self._total_length():
            raise MemoryException("Unreachable memory location {}.".format(ptr, self.sp))

    def _total_length(self):
        return self.vm_size

    # def _check_in_heap(self, ptr: int):
    #     if ptr < self._heap_starts() or ptr >= self._heap_ends():
    #         raise MemoryException("Pointer to {} is not in heap".format(ptr))

    def _find_available2(self, length):
        pool = []
        found = False
        while not found:
            if len(self.available2) < length:
                break
            i = 0
            while i < length:
                x = self.available2.extract()
                pool.append(x)
                y = self.available2.get()
                if x != y + 1:
                    break
                i += 1
            if i == length:
                found = True

        if found:
            for j in range(len(pool) - length):
                self.available2.insert(pool[j])
            return pool[-1]
        else:
            raise MemoryException("No space to malloc an object of length {}"
                                  .format(length - self.get_type_size("int")))

    # def _find_available(self, length) -> int:
    #     """
    #     Finds a consecutive heap address of length <length> and returns the first address.
    #
    #     :param length:
    #     :return:
    #     """
    #     i = len(self.available) - 1
    #     while i >= 0:
    #         j = 0
    #         while j < length - 1 and i - j > 0:
    #             if self.available[i - j - 1] != self.available[i - j] + 1:
    #                 break
    #             j += 1
    #         if j == length - 1:
    #             return i
    #         else:
    #             i -= j + 1
    #     raise MemoryException("No space to malloc an object of length {}".format(length - self.get_type_size("int")))

    # def _heap_starts(self):
    #     return self.stack_size + self.literal_size
    #
    # def _heap_ends(self):
    #     return self.vm_size
    #
    # def _literal_starts(self):
    #     return self.stack_size
    #
    # def _heap_size(self):
    #     return self.vm_size - self.stack_size - self.literal_size

    # def _generate_available(self):
    #     # self.available = [i for i in range(self._heap_ends() - 1, self._heap_starts() - 1, -1)]
    #     self.available2.build_heap([i + self._heap_starts() for i in range(self._heap_size())])


MEMORY = Memory()


def int_to_bytes(i: int) -> bytes:
    int_len = MEMORY.get_type_size("int")
    return i.to_bytes(int_len, "big", signed=True)


def bytes_to_int(b: bytes) -> int:
    return int.from_bytes(b, "big", signed=True)


if __name__ == "__main__":
    m = Memory()
    m.initialize(bytes(0))
    m.available2.heap = [32767, 32766, 32765, 32764, 32763, 32762, 32761, 32760, 32759]
    m.available2.print_sorted()
    ava2 = m._find_available2(4)
    print(ava2)
    m.available2.print_sorted()
