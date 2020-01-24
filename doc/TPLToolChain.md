# TPL Tool Chain

###### **_Product of TrashSoftwareStudio_**

## Introduction

**TPL Tool Chain** is the native parser-compiler-virtual machine set of **Trash Programming Language (TPL)**.

## Compiler Tool Set

The TPL compiler set is made up by a tokenizer, a parser, an abstract syntax tree optimizer, a compiler, and 
a code optimizer. The tool set is written in python, with the entry `tpc.py`

Usage of `tpc.py`:
```
python tpc.py [FLAGS] SRC_FILE DST_FILE
```

List of flags:

* `-ast` Prints the abstract syntax tree
* `-nl`, \
  `--no-lang` Do not include "lib/lang.tp" automatically
* `-o0` No optimization
* `-o1` Level 1 optimization
* `-o2` Level 2 optimization
* `-o3` Level 3 optimization
* `-tk`, \
  `--tokens` Prints the list of tokens
  
### Optimization levels:

`-o1`: Abstract syntax tree optimization:
* Constant pre-calculation

`-o2`: Redundancy clearance:
* Removes noneffective TPA instructions
* Removes empty assignment

`-o3`: CPU friendly optimizations:
* Substitute `*`, `/`, `%` with `<<`, `>>`, `&` if applicable
* Stores loop invariant in register if applicable

## Virtual Machine

The Trash Program Virtual Machine (TVM) is the virtual runtime environment of TPL program.
The TVM is written in C.

#### Under Windows:

Usage of `tpl.exe`:
```
tpl.exe [VM_FLAGS] FILE [PROGRAM_FLAGS]
```
