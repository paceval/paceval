cmake_minimum_required(VERSION 3.16)
project(paceval_quantum_research LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# This example is validated on Linux with the original paceval v4.25 SDK.
# paceval_main.cpp is the API FORWARDING SOURCE, not the mathematical engine.
# The external binary libpaceval_linux_sharedLIB.so supplies the computation.
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "This release is verified for Linux and its original paceval .so")
endif()

# Supply a real, absolute .so path at configure time. The licensed binary is
# intentionally NOT stored in this GitHub project or built from the SDK source.
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()
if(NOT PACEVAL_RUNTIME OR NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}" OR
   NOT EXISTS "${PACEVAL_RUNTIME}" OR IS_DIRECTORY "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Set PACEVAL_RUNTIME or absolute environment variable PACEVAL_LIB to the original Linux shared library")
endif()

# Use an imported target to enforce real vendor symbol resolution at link-time
# and allow CMake to generate the appropriate build-tree library search path.
add_library(paceval_vendor SHARED IMPORTED GLOBAL)
set_target_properties(paceval_vendor PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")

# Include the user-supplied SDK's original header; compile its original .cpp
# along with the quantum demonstrator. Do not compile the header directly.
add_executable(quantum quantum.cpp paceval_main.cpp)
target_include_directories(quantum PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(quantum PRIVATE paceval_vendor)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(quantum PRIVATE -O3 -Wall -Wextra -Wpedantic)
endif()

enable_testing()
# The native test checks circuit identities and analytical derivative, but the
# second test actually instantiates SDK computation graphs in the original .so.
add_test(NAME native_formula_self_test COMMAND quantum --self-test)
add_test(NAME real_paceval_quantum_integration COMMAND quantum
  --events 120 --batch 32
  --input-csv "${CMAKE_CURRENT_SOURCE_DIR}/../examples/ramsey_circuit_sample.csv"
  --csv "${CMAKE_CURRENT_BINARY_DIR}/quantum_integration_output.csv")
message(STATUS "Real paceval SDK/runtime integration enabled: ${PACEVAL_RUNTIME}")
