# TPL Known Issues

## Tokenizer

* Variable names ended by numbers combined with double dots
```
var s1: *S;
s1..a = 0;
```

## Parser-Compiler

* ~~Nested function types~~
```
var f: fn(fn()->void)->int;    FIXED
```

* ~~Attributes op-assign~~
```
this..count += 1;    FIXED
```

* Attributes increment/decrement
```
this..count++;
```

* Indexing in multi-layer pointers
```
var arr: **S = {...};
arr[1] = {...};
```

* Instantiate struct before all method defined
```
struct S {
    var func: fn;
    ...
}

fn main() int {
    new(S);
    ...
}

fn S::func() void {...}
```

## Virtual Machine

* Printf and stringf float options

* Malloc memory usage
