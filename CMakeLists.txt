cmake_minimum_required(VERSION 3.15)
project(tpl3 C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_FLAGS_DEBUG -O2)

add_executable(tpl3 lib.c lib.h vm.c vm.h)