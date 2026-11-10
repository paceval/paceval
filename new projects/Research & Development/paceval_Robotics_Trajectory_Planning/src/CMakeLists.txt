cmake_minimum_required(VERSION 3.16)
project(paceval_robotic_trajectories LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# The two original vendor SDK source files are source-level API *forwarders*.
# They do not implement the mathematical engine. A compatible original Linux
# shared runtime is separately supplied and linked into this application.
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "This validated research build targets the original Linux paceval runtime")
endif()
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()
if(NOT PACEVAL_RUNTIME OR NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}" OR NOT EXISTS "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Use -DPACEVAL_RUNTIME=/absolute/path/libpaceval_linux_sharedLIB.so or PACEVAL_LIB")
endif()
add_library(paceval_vendor SHARED IMPORTED GLOBAL)
set_target_properties(paceval_vendor PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")
add_executable(robotics robotics.cpp paceval_main.cpp)
target_include_directories(robotics PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(robotics PRIVATE paceval_vendor)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(robotics PRIVATE -O3 -Wall -Wextra -Wpedantic)
endif()
enable_testing()
add_test(NAME native_kinematics_geometry_and_derivatives COMMAND robotics --self-test)
add_test(NAME original_paceval_waypoint_plan COMMAND robotics
  --waypoints "${CMAKE_CURRENT_SOURCE_DIR}/../examples/waypoints.csv"
  --steps 8 --grid 19 --batch 128
  --out-csv "${CMAKE_CURRENT_BINARY_DIR}/ctest_trajectory.csv"
  --tinc-csv "${CMAKE_CURRENT_BINARY_DIR}/ctest_tinc.csv")
message(STATUS "Linking separately supplied original paceval Linux runtime: ${PACEVAL_RUNTIME}")
