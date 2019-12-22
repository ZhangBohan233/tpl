fn main() int {
    var t1: int = clock();
    var a: int = fib(20);
    //var a: int = ftn(5) + ftn(6) + ftn(7);
    //var a: int = 5;
    var t2: int = clock();
    printf("%d, time: %d", a, t2 - t1);
    return 0;
}

fn fib(n: int) int {
    //printf("%d", &n);
    if (n < 2) {
        return n;
    } else {
        return fib(n - 1) + fib(n - 2);
    }
}

fn ftn(n: int) int {
    return n + 1;
}
