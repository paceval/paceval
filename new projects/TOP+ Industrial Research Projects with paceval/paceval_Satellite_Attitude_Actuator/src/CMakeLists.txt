cmake_minimum_required(VERSION 3.16)
project(paceval_satellite_attitude LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT DEFINED PACEVAL_SHARED_LIB OR NOT EXISTS "${PACEVAL_SHARED_LIB}")
 message(FATAL_ERROR "Set -DPACEVAL_SHARED_LIB=/absolute/path/to/original/compatible/libpaceval.so (or import library). It is not redistributed.")
endif()
add_executable(satellite_attitude_paceval satellite_attitude_paceval.cpp paceval_main.cpp)
target_include_directories(satellite_attitude_paceval PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(satellite_attitude_paceval PRIVATE "${PACEVAL_SHARED_LIB}")
if(UNIX AND NOT APPLE)
 target_link_libraries(satellite_attitude_paceval PRIVATE dl)
endif()
enable_testing()
add_test(NAME local_sdk_axis_quat_and_profile
 COMMAND satellite_attitude_paceval
 "${CMAKE_CURRENT_SOURCE_DIR}/../examples/axis_snapshots.csv"
 "${CMAKE_CURRENT_SOURCE_DIR}/../examples/quaternion_snapshots.csv"
 "${CMAKE_CURRENT_BINARY_DIR}/local_axis.csv"
 "${CMAKE_CURRENT_BINARY_DIR}/local")
