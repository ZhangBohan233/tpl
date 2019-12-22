fn main() int {
    var a: int = 5;
    var b: float = 7.5;

    var pa: *int = &a;
    printf("%d", pa);
    *pa = 7;

    var d: int;
    &d = 10;
    printf("%d", d);

    var c: float = b + a;
    typeof(c);
    printf("%f", c);

    return 0;
}