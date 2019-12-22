fn main() int {
    var x: int;
    var y: int[5];
    //var z: *int;
    x = 5;
    printf("%d", add(x, 3));
    var z: *int = &x;
    printf("%d", z);
    var r: int = *z;
    printf("%d", r);
    var t: int = add(3,4) + 1;
    printf("%d", t);

    var a : int = 66;
    var b : int = 44;
    var c : int = add_ptr(&a, &b);
    printf("%d", *c);
}

fn add(x: int, y: int) int {
    x + y + 1;
}

fn add_ptr(x: *int, y: *int) *int {
    &(*x + *y);
}
