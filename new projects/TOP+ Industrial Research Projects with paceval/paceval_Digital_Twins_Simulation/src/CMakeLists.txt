cmake_minimum_required(VERSION 3.16)
project(paceval_digital_twins LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Linux vendor SDK layout: paceval_main.cpp is the supplied API forwarding
# layer. It is compiled together with this research application and includes
# paceval_main.h. It DOES NOT implement the mathematical runtime itself.
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "This tested project requires Linux and its paceval shared library")
endif()

# The runtime is intentionally external, not committed to a public GitHub ZIP.
# Configure, for example: cmake -S src -B build -DPACEVAL_RUNTIME=/path/libpaceval_linux_sharedLIB.so
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()
if(NOT PACEVAL_RUNTIME OR NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}" OR NOT EXISTS "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Set PACEVAL_RUNTIME or absolute env PACEVAL_LIB to an existing original paceval Linux .so")
endif()

# Imported binary is linked by CMake, so the ABI is checked by the compiler
# and linker rather than manually reproduced with function-pointer typedefs.
add_library(paceval_vendor SHARED IMPORTED GLOBAL)
set_target_properties(paceval_vendor PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")
add_executable(digital_twin digital_twin.cpp paceval_main.cpp)
target_include_directories(digital_twin PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(digital_twin PRIVATE paceval_vendor)

# The freshly built executable can locate the explicitly linked runtime without
# requiring LD_LIBRARY_PATH when CMake generates a build-tree RUNPATH.
set_target_properties(digital_twin PROPERTIES BUILD_RPATH_USE_ORIGIN FALSE)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(digital_twin PRIVATE -O3 -Wall -Wextra -Wpedantic)
endif()

enable_testing()
add_test(NAME native_self_test COMMAND digital_twin --self-test)
add_test(NAME real_paceval_digital_twin COMMAND digital_twin
  --input-csv "${CMAKE_CURRENT_SOURCE_DIR}/../examples/scenarios.csv"
  --scenarios 12 --steps 60 --dt 2
  --output-csv "${CMAKE_CURRENT_BINARY_DIR}/trajectories_test.csv"
  --tinc-csv "${CMAKE_CURRENT_BINARY_DIR}/tinc_test.csv")
message(STATUS "Compiling original paceval_main.cpp and linking original vendor runtime: ${PACEVAL_RUNTIME}")
