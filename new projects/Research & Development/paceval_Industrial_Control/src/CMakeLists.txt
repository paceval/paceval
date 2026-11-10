cmake_minimum_required(VERSION 3.16)
project(paceval_industrial_control LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# The portable vendor C/C++ API sources are compiled into this executable.
# They FORWARD to the separately supplied original paceval Linux shared library.
# They do not replace or contain the mathematics runtime itself.
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "The validated sample build targets Linux with the original paceval .so")
endif()
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()
if(NOT PACEVAL_RUNTIME OR NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}" OR NOT EXISTS "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Set -DPACEVAL_RUNTIME=/absolute/path/libpaceval_linux_sharedLIB.so or environment PACEVAL_LIB")
endif()
add_library(paceval_vendor SHARED IMPORTED GLOBAL)
set_target_properties(paceval_vendor PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")
add_executable(industrial_control industrial_control.cpp paceval_main.cpp)
target_include_directories(industrial_control PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(industrial_control PRIVATE paceval_vendor)
target_compile_definitions(industrial_control PRIVATE EXAMPLE_SCENARIOS="${CMAKE_CURRENT_SOURCE_DIR}/../examples/scenarios.csv")
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(industrial_control PRIVATE -O3 -Wall -Wextra -Wpedantic)
endif()
enable_testing()
add_test(NAME analytic_self_test COMMAND industrial_control --self-test)
add_test(NAME offline_mpc_original_paceval_test COMMAND industrial_control
  --scenarios-csv "${CMAKE_CURRENT_SOURCE_DIR}/../examples/scenarios.csv"
  --steps 8 --horizon 4 --beam 12 --batch 128
  --out-csv "${CMAKE_CURRENT_BINARY_DIR}/ctest_trajectory.csv"
  --tinc-csv "${CMAKE_CURRENT_BINARY_DIR}/ctest_tinc.csv")
add_test(NAME exhaustive_native_oracle COMMAND industrial_control --oracle-test)
message(STATUS "Linking original external paceval runtime: ${PACEVAL_RUNTIME}")
