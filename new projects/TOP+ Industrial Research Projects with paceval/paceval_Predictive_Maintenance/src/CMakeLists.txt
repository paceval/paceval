cmake_minimum_required(VERSION 3.16)
project(paceval_predictive_maintenance LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "Reproducible reference build targets Linux")
endif()
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()
if(NOT PACEVAL_RUNTIME OR NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}" OR NOT EXISTS "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Pass -DPACEVAL_RUNTIME=/absolute/path/libpaceval_linux_sharedLIB.so")
endif()
add_library(paceval_external SHARED IMPORTED GLOBAL)
set_target_properties(paceval_external PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")
# Direct official C/C++ API bridge: vendor wrapper compiled as part of the program.
add_executable(predictive_maintenance predictive_maintenance.cpp paceval_main.cpp)
target_include_directories(predictive_maintenance PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(predictive_maintenance PRIVATE paceval_external)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(predictive_maintenance PRIVATE -Wall -Wextra -Wpedantic)
endif()
enable_testing()
add_test(NAME native_self_test COMMAND predictive_maintenance --self-test)
add_test(NAME paceval_original_library_integration COMMAND predictive_maintenance
 --raw "${CMAKE_CURRENT_SOURCE_DIR}/../examples/raw_vibration.csv"
 --out "${CMAKE_CURRENT_BINARY_DIR}/ctest_evaluations.csv"
 --features "${CMAKE_CURRENT_BINARY_DIR}/ctest_features.csv"
 --metrics "${CMAKE_CURRENT_BINARY_DIR}/ctest_metrics.csv"
 --tinc "${CMAKE_CURRENT_BINARY_DIR}/ctest_tinc.csv" --batch 37)
add_test(NAME invalid_recordings_rejected COMMAND predictive_maintenance
 --raw "${CMAKE_CURRENT_SOURCE_DIR}/../examples/invalid_raw.csv"
 --out "${CMAKE_CURRENT_BINARY_DIR}/invalid.csv")
set_tests_properties(invalid_recordings_rejected PROPERTIES WILL_FAIL TRUE)
