# Trash Programming Language Standard

###### **_TrashSoftwareStudio_**

## Introduction

**Trash Programming Language (TPL)** is a middle level programming language.

## General syntax

* Every code line must be terminated with line terminator `;`
* Code block is surrounded by `{` and `}`

## Native types:

There are 3 native primitive types which are directly stored in local memory. Each one has a fixed byte length.

* `char` stores 8 bit unsigned integer
* `int`: stores 64 bit signed integer
* `float`: stores 64 bit floating point values, compatible with IEEE 754 double precision floating point number

Note that the byteorder of `int` is depend on the platform.

## Pointers:

Pointers stores an address of a variable. A pointer of any type occupies the length of `int`.

## Literals:

There are 4 types of literals.

* `char` literal, quoted by `'`
* `float` literal, specified by a `.` between numbers
* `int` literal, integer numbers
* String literal, stored in `char[]`, quoted by `"`

## Variable declaration:

There are 2 main types of variables: 

* `var` which can be modified after declaration
* `const` which is read only after declaration

Variable should have its type specified while declaration. The type cannot be changed after
declaration. A typical example:
```
var x: int;
```

The initial value of a variable is undefined. For more information see part **_Undefined Behaviors_**

## Variable assignment:

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

Another modifier `register` can be used in declaring 8 byte native primitive types. The modifier `register`
tells the compiler to store this variable in a register. Example: 
```
register r: int = 2;
```
The register variable has the same characteristic as variables declared with `var` except for: 

* `register` variable cannot be used as the returning value of functions
* `register` variable does not support the address operations since it has no memory address

## Function declaration:

Functions are declared with the keyword `fn`. A complete function declaration should have at least a name, 
parameters, and a return type. A typical example:
```
fn add(x: int, y: int) int {
    return x + y;
}
```
Parameters should be separated by comma. 

There are two types of function declaration: virtual function, and real function.

Virtual function is declared to tell the compiler the function is ready to call, but not yet implemented.

A virtual function must eventually be implemented.

An example of the use of virtual function:
```
fn foo(n: int) int;

fn bar() void {
    return foo(1);
}

fn foo(n: int) int {
    return n + 1;
}
```

The implementation should have the same name, return type, and parameter types.

## Function call:

## Binary operators:

There are binary operators in TPL

#### Binary operators table:

Operator  | Left type  | Right type | Return type | Description
--------- | ---------- | ---------- | ----------- | -----
+         | int, float | int, float | int, float  | Addition
-         | int, float | int, float | int, float  | Subtraction
*         | int, float | int, float | int, float  | Multiplication
/         | int, float | int, float | int, float  | Division
%         | int, float | int, float | int, float  | Modulo
&&        | int        | int        | int         | Logical and
&#124;&#124;| int      | int        | int         | Logical or
==        | int, float | int, float | int         | Equivalent
!=        |
\>>       | int        | int        | int         | Arithmetic right shift
\>>>      | int        | int        | int         | Logical right shift
<<        | 

## Unary operators:

## Conditional statements:

There are 3 types of conditional statements: `if` statement, `for` statement, and `while` statement.

* #### If statement:
  If statement has 2 mandatory parts (condition block and then block), 1 optional part (else block).
   
  Condition block must be an expression with `int` output. If the result value of conditional block is not `0`,
  the program goes to the then block. Otherwise the program goes to the else block if there is an else block.
   
  Code example:
  ```
  a := 1;
  if a {
      printf("This line should be printed\n");
  } else {
      printf("This line should not be printed\n");
  }
  ```
  
  Notice that the braces `{` `}` surround if block is mandatory, but the braces surround else block is optional for 
  single line codes.
 
  
* #### For statement:


## Structs


## Compile time functions


## Native invoke functions


## Label and goto

A label can be defined as
```
label lab;
```
Where the `lab` is the name of label. Labels must be unique in the same function.

The syntax of goto statement is
```
goto lab;
```
Which directs the program to the defined label `lab`. Note that the label `lab` must be in the same function scope 
with the `goto` statement.

Example:
```
i := 0;
label begin;
printf("%d ", i);
i++;
if i < 10 {
    goto begin;
}
```


## Table of all native primitive types:

| Type name  | Byte length | Signed | Min value | Max value |
| ---------- | ----------- | -------| --------- | --------- |
| char       | 1           | False  | 0         | 255       |
| float      | 8           | True   | -2^1023   | 2^1023    |
| int        | 8           | True   | -2^63     | 2^63      |

## Table of operator precedences:

|
|
|
|
|

## List of all keywords:

* `break`
* `const`
* `continue`
* `else`
* `float`
* `fn`
* `for`
* `goto`
* `int`
* `if`
* `include`
* `label`
* `register`
* `return`
* `sizeof`
* `struct`
* `var`
* `while`

## Undefined Behaviors 

There are several operations in TPL is undefined.

1. Accessing an undefined variable
   ```
   var a: int;
   printf("%d", b);
   ```
   
2. Implicit casting between types
   ```
   var a: int = 'a';
   ```
   
3. 
