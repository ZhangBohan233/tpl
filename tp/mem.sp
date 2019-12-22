struct A {
    var a: int;
    var b: int;
}

fn createA() *A {
    var x: *A = malloc(sizeof(A));
    (*x).a = 8;
    (*x).b = 15;
    //memory_view();
    return x;
}

fn sCreateA() *A {
    var x: A;
    x.a = 16;
    x.b = 30;
    return &x;
}

fn main() int {
    var a: A;
    a.a = 7;
    a.b = 14;
    var aa: *A = createA();

    //memory_view();
    printf("%d", aa);

    typeof(aa);
    memory_ava();
    free(aa);
    memory_ava();

    return 0;
}
