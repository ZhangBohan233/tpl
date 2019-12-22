struct A {
    var x: int;
    var y: int;
    var z: int[2];
}

fn main() int {
    var arr: int[3][2];
    var a: int = 1;
    var b: int = 2;
    printf("%d %d", b, &b);
    b = 3;
    printf("%d %d", b, &b);

    var d: A;
    d.x = 5;
    d.y = 4;

    var e: int = 10;
    var f: int = &d;
    printf("%d", d.x);

    arr[0][0] = 11;
    arr[1][0] = 12;

    var g: int = add(7, 8);

    printf("%d", arr[1][0]);
    printf("%d", g);

    return 0;
}

fn add(x: int, y: int) int {
    return x + y;
}
