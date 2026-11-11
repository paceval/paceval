cmake_minimum_required(VERSION 3.16)
project(paceval_fusion_diagnostics LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# This project is tested with the supplied Linux paceval SDK 4.25. The two
# vendor source files are compiled directly; the proprietary mathematical
# runtime must be obtained separately and is not included in the repository.
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "This verified build targets Linux with the paceval shared runtime")
endif()
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()
if(NOT PACEVAL_RUNTIME OR NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}" OR NOT EXISTS "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Set -DPACEVAL_RUNTIME=/absolute/path/libpaceval_linux_sharedLIB.so or env PACEVAL_LIB")
endif()
add_library(paceval_vendor SHARED IMPORTED GLOBAL)
set_target_properties(paceval_vendor PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")
add_executable(fusion fusion.cpp paceval_main.cpp)
target_include_directories(fusion PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(fusion PRIVATE paceval_vendor)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(fusion PRIVATE -O3 -Wall -Wextra -Wpedantic)
endif()

enable_testing()
add_test(NAME native_self_test COMMAND fusion --self-test)
add_test(NAME paceval_real_runtime_test COMMAND fusion
  --input-csv "${CMAKE_CURRENT_SOURCE_DIR}/../examples/sensors.csv"
  --samples 64 --batch 16
  --output-csv "${CMAKE_CURRENT_BINARY_DIR}/test_outputs.csv"
  --tinc-csv "${CMAKE_CURRENT_BINARY_DIR}/test_tinc.csv")
message(STATUS "Linked paceval Linux runtime: ${PACEVAL_RUNTIME}")
