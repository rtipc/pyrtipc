cmake_minimum_required(VERSION 2.8.12...4.0.0)

include(ExternalProject)

find_package(Python COMPONENTS Interpreter Development.Module  REQUIRED )
find_package(Cython REQUIRED)

include(UseCython)

set(RTIPC_INSTALL_DIR ${CMAKE_CURRENT_BINARY_DIR}/rtipc-install)
set(RTIPC_INCLUDE_DIR ${RTIPC_INSTALL_DIR}/include)
set(RTIPC_LIBRARY ${RTIPC_INSTALL_DIR}/lib/librtipc.a)


ExternalProject_Add(
  rtipc_project
  SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/rtipc
  BUILD_BYPRODUCTS ${RTIPC_LIBRARY}
  INSTALL_DIR ${RTIPC_INSTALL_DIR}
  CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=<INSTALL_DIR> -DCMAKE_INSTALL_LIBDIR=lib
)


add_library(rtipc_library STATIC IMPORTED GLOBAL)
set_property(TARGET rtipc_library PROPERTY IMPORTED_LOCATION ${RTIPC_LIBRARY})
add_dependencies(rtipc_library rtipc_project)


project(pyrtipc LANGUAGES C)

set(CMAKE_C_STANDARD 11)

option(RTIPC_BUILD_EXAMPLES "Build examples" OFF)


add_subdirectory(wrapper)


