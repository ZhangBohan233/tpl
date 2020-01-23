cmake_minimum_required(VERSION 3.15)
project(tpl C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_FLAGS_DEBUG -O2)

add_executable(tpl src/lib.c src/lib.h src/vm.c src/vm.h src/heap.c src/heap.h)