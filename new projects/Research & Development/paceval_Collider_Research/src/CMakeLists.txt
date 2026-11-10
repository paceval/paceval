cmake_minimum_required(VERSION 3.16)
project(paceval_collider_research LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# This tested release builds for Linux with the original vendor shared object.
# paceval_main.cpp is ONLY the supplied C/C++ API forwarding layer, not the
# mathematical computation engine. It calls pacevalLibrary_* in the external .so.
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "This example is tested with Linux and its original paceval .so")
endif()

# A user-supplied absolute path is needed at CONFIGURE time. Do not copy the
# proprietary binary into this GitHub repository.
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()
if(NOT PACEVAL_RUNTIME OR NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}" OR NOT EXISTS "${PACEVAL_RUNTIME}" OR IS_DIRECTORY "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Set PACEVAL_RUNTIME or absolute env PACEVAL_LIB to an original Linux .so file")
endif()

# The imported target asks the linker to verify exported symbols and lets
# CMake generate a build-tree RUNPATH for the supplied shared library.
add_library(paceval_vendor SHARED IMPORTED GLOBAL)
set_target_properties(paceval_vendor PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")

# Compile BOTH the C++ research application and the original API adapter.
# paceval_main.h is included by each translation unit; never compile a header.
add_executable(collider collider.cpp paceval_main.cpp)
target_include_directories(collider PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(collider PRIVATE paceval_vendor)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(collider PRIVATE -O3 -Wall -Wextra -Wpedantic)
endif()

# There is no silent native-only fallback: the real runtime is a build dependency.
# The self-test only checks mathematical native reference values; the second
# test exercises the linked SDK and real paceval graph/batch/TINC paths.
enable_testing()
add_test(NAME native_formula_self_test COMMAND collider --self-test)
add_test(NAME real_paceval_collider_integration COMMAND collider
  --input-csv "${CMAKE_CURRENT_SOURCE_DIR}/../examples/example_events.csv"
  --events 100 --batch 16 --csv "${CMAKE_CURRENT_BINARY_DIR}/validation_test.csv")
message(STATUS "Original paceval SDK + real runtime configured: ${PACEVAL_RUNTIME}")
