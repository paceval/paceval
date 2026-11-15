cmake_minimum_required(VERSION 3.16)
project(paceval_industrial_furnace LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT DEFINED PACEVAL_SHARED_LIB)
  message(FATAL_ERROR "Set -DPACEVAL_SHARED_LIB=<absolute path to compatible original libpaceval.so or .dll/.lib import library>. Runtime library is intentionally NOT shipped.")
endif()
add_executable(industrial_furnace_paceval industrial_furnace_paceval.cpp paceval_main.cpp)
target_include_directories(industrial_furnace_paceval PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(industrial_furnace_paceval PRIVATE "${PACEVAL_SHARED_LIB}")
if(UNIX AND NOT APPLE)
  target_link_libraries(industrial_furnace_paceval PRIVATE dl)
endif()
enable_testing()
add_test(NAME original_sdk_full_csv
  COMMAND industrial_furnace_paceval
    "${CMAKE_CURRENT_SOURCE_DIR}/../examples/synthetic_operating_points.csv"
    "${CMAKE_CURRENT_BINARY_DIR}/local_sdk_results.csv")
