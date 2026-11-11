cmake_minimum_required(VERSION 3.16)
project(paceval_edge_ai_postprocessing LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# The *API layer* paceval_main.cpp belongs to this project. It forwards to
# the actual, separately supplied paceval Linux shared library. It is not the
# mathematical engine itself; this is a verified Linux target configuration.
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "The tested reference build currently targets Linux")
endif()
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()
if(NOT PACEVAL_RUNTIME OR NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}" OR NOT EXISTS "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Provide an absolute path via -DPACEVAL_RUNTIME=/path/libpaceval_linux_sharedLIB.so or PACEVAL_LIB")
endif()
add_library(paceval_vendor SHARED IMPORTED GLOBAL)
set_target_properties(paceval_vendor PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")
add_executable(edge_ai edge_ai.cpp paceval_main.cpp)
target_include_directories(edge_ai PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(edge_ai PRIVATE paceval_vendor)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(edge_ai PRIVATE -Wall -Wextra -Wpedantic)
  if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(edge_ai PRIVATE -O3)
  endif()
endif()

enable_testing()
add_test(NAME native_self_test COMMAND edge_ai --self-test)
add_test(NAME real_paceval_smoke_test COMMAND edge_ai
   --catalog "${CMAKE_CURRENT_SOURCE_DIR}/../examples/formulas.csv"
   --traces "${CMAKE_CURRENT_SOURCE_DIR}/../examples"
   --limit 16 --batch 17
   --output "${CMAKE_CURRENT_BINARY_DIR}/ctest_scores.csv"
   --tinc "${CMAKE_CURRENT_BINARY_DIR}/ctest_tinc.csv")
message(STATUS "External paceval library: ${PACEVAL_RUNTIME}")
