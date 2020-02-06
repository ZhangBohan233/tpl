# TPL Known Issues

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

## Virtual Machine

* Printf and stringf float options
