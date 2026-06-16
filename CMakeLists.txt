cmake_minimum_required(VERSION 3.15)

include(ExternalProject)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(Cython MODULE REQUIRED VERSION 3.0)

include(UseCython)

set(RTIPC_INSTALL_DIR ${CMAKE_CURRENT_BINARY_DIR}/rtipc-install)
set(SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/src/pyrtipc) 

ExternalProject_Add(
  rtipc
  GIT_REPOSITORY    https://github.com/mausys/rtipc.git
  GIT_TAG           main
  INSTALL_DIR ${RTIPC_INSTALL_DIR}
  CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=<INSTALL_DIR>
)

set(RTIC_INCLUDE_DIR ${RTIPC_INSTALL_DIR}/include)

project(pyrtipc LANGUAGES C)


set(CMAKE_C_STANDARD 11)

option(RTIPC_BUILD_EXAMPLES "Build examples" OFF)

cython_transpile(${SRC_DIR}/rtipc.pyx LANGUAGE C CYTHON_ARGS -I ${SRC_DIR} OUTPUT_VARIABLE rtipc_c)

python_add_library(pyrtipc MODULE "${rtipc_c}" WITH_SOABI)

add_dependencies(pyrtipc rtipc)

target_include_directories(pyrtipc PRIVATE ${RTIC_INCLUDE_DIR})


install(TARGETS pyrtipc DESTINATION .)

