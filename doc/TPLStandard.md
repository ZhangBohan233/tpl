# Trash Programming Language Standard

###### **_TrashSoftwareStudio_**

## Introduction

**Trash Programming Language (TPL)** is a middle level programming language.

## Syntax Guide

### General syntax

* Every code line must be terminated with line terminator `;`

### Variable declaration

There are 2 main types of variables: 

* `var` which can be modified after declaration
* `const` which is read only after declaration

Variable should have its type specified while declaration. The type cannot be changed after
declaration. A typical example:
```
var x: int;
```

The initial value of a variable is undefined. For more information see part **_Undefined Behaviors_**

### Variable assignment:

The symbol `=` is used for variable assignment. \
The assignment symbol `=` assigns the value right of it to the variable at its left. Example:
```
x = 1;
```

Simple variable can be assigned with an initial value while declaration. Example:
```
var x: int = 1;
```
or a shortcut syntax:
```
x := 1;
```
which declares the variable `x` and assigns it with integer `1`.
These two ways are equivalent.

Notice that the constant declaration must have an initial value. Example:
```
const c: int = 5;
```

### Function declaration:

### Function call:

### List of all native primitive types:

* `char`
* `int`
* `float`

### List of all keywords:

* `break`
* `const`
* `continue`
* `else`
* `float`
* `fn`
* `for`
* `int`
* `if`
* `include`
* `register`
* `return`
* `sizeof`
* `struct`
* `var`
* `while`

## Style Guide

## Undefined Behaviors 
