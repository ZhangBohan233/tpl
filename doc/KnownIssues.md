# TPL Known Issues

## Parser-Compiler

* Nested function types
```
var f: fn(fn()->void)->int;
```

* Attributes op-assign
```
this..count += 1;
this..count++;
```

## Virtual Machine

* Printf and stringf float options
