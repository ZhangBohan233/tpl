class A:
    def __init__(self):
        self.v = 1

    def get_mul(self, m):
        for i in range(m):
            self.v *= i
        return self.v


class B:
    def __init__(self):
        self.v = 1


def get_mul(b, m):
    for i in range(m):
        b.v *= i
    return b.v


count = 0


def fib(n):
    print(n, end=" ")
    global count
    count += 1
    if n < 2:
        return n
    else:
        return fib(n - 1) + fib(n - 2)


if __name__ == '__main__':
    import time

    # n = 5000

    t1 = time.time()

    print(fib(3))

    t2 = time.time()

    print(count)

    for i in range(1000000):
        pass

    t3 = time.time()

    print((t2 - t1) * 1000, (t3 - t2) * 1000)
