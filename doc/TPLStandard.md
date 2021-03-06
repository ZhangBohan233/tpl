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

* `register` variables cannot be used as the returning value of functions
* `register` variables cannot be used as the function call arguments
* `register` variables do not support the address operations since they have no memory address

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

Implementation of function with declared return type other than `void` must terminate by `return` statement(s).

## Function call:

## Unary operators:

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
<<        | int        | int        | int         | Left shift

Note that the operator `&&` and `||` uses short-circuiting evaluation. For the operator `&&`, if the left side is
false (evaluates as 0), then the right side would never be executed. For `||`, if the left side is true, then the 
right side is not executed.

## Ternary operators

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


## Functional programming

### Passing function pointer as variable:


## Object oriented programming:

TPL supports simple object oriented programming. A method of a struct must be declared in the struct body.

```
struct Foo {
    ...
    var bar: fn;
}
```
Which declared a member function of struct `Foo` which takes an `int` and returns nothing.

The declared member function may be implemented by
```
fn Foo::bar(x: int) void {
    ...
}
```
Notice that the compiler should add a parameter to the struct pointer named `this` as the first parameter. So the 
actual parameters of the example method is `this: *Foo, x: int`.

Use the keyword function `new` to create structs that has member functions. Otherwise, the member functions may remain
unimplemented. Example:
```
var foo: *Foo = new(Foo);
```
The member functions are called via struct attributes. For example:
```
foo..bar(5);
```
Which calls the member function `bar` of `Foo` instance 'foo'.
Notice that the actual first argument is a copy of the left side of the dot `..`. So when the code segment above is 
executed, the actual calling is `foo..bar(foo, 5)`. If the left side of the dot is a function call, then the execution
result might be undefined (see Undefined Behaviors #3).

Inheritance is not supported.

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
Will output
```
0 1 2 3 4 5 6 7 8 9 
```
Which is equivalent to
```
i := 0
while i < 10 {
    printf("%d ", i);
    i++;
}
```

**Warning:** do not use `label` or `goto` in any situation other than breaking loops.

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
* `char`
* `const`
* `continue`
* `else`
* `exit`
* `float`
* `fn`
* `for`
* `goto`
* `int`
* `if`
* `include`
* `label`
* `new`
* `register`
* `return`
* `sizeof`
* `struct`
* `this`
* `var`
* `while`

## Undefined Behaviors 

There are several operations in TPL is undefined.

1.  Accessing an undefined variable
    ```
    var a: int;
    printf("%d", b);
    ```
   
2.  Implicit casting between types
    ```
    var a: int = 'a';
    ```

3.  Calling a member function of struct returned by another function
    ```
    struct S {
        var foo: fn;
        var bar: fn;
    }
    
    fn S::foo(x: int) void {
        printf("%d\n", x);
    }
    
    fn S::bar() fn(int)->void {
        return this..foo;
    }
    
    fn main() int {
        var s: *S = new(S);
        s..bar()(1);   // would cause runtime error or undefined behavior
        return 0;
    }
    ```
    
4.  Referencing pointers that are already released
    ```
    var a: *int = malloc(8);
    *a = 2;
    free(a);
    printf("%d\n", *a);
    ```
