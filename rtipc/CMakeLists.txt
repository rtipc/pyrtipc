message("SKBUILD_SABI_VERSION=${SKBUILD_SABI_VERSION}")
if (NOT "${SKBUILD_SABI_VERSION}" STREQUAL "")
  set(USE_SABI USE_SABI ${SKBUILD_SABI_VERSION})
endif()


cython_transpile(${CMAKE_CURRENT_SOURCE_DIR}/rtipc_wrapper.py LANGUAGE C CYTHON_ARGS  -I ${CMAKE_CURRENT_SOURCE_DIR} OUTPUT_VARIABLE RTIPC_WRAPPER_SRC)

python_add_library(rtipc_wrapper  ${RTIPC_WRAPPER_SRC})
#python_add_library(pyrtipc2 MODULE WITH_SOABI   ${RTIPC_WRAPPER_SRC})

target_include_directories(rtipc_wrapper PRIVATE ${RTIC_INCLUDE_DIR})

target_link_libraries(rtipc_wrapper PRIVATE ${RTIPC_LIBRARY})


install(
  TARGETS rtipc_wrapper
  RUNTIME DESTINATION pyrtipc
  ARCHIVE DESTINATION pyrtipc
  LIBRARY DESTINATION pyrtipc
)



install(
  FILES
    __init__.py
    config.py
    rtipc.pxd
  DESTINATION
    pyrtipc
)
