cmake_minimum_required(VERSION 3.16)
project(paceval_industrial_gateway_rules LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "The reproducible reference build targets Linux")
endif()
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()
if(NOT PACEVAL_RUNTIME OR NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}" OR NOT EXISTS "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Set -DPACEVAL_RUNTIME=/absolute/path/libpaceval_linux_sharedLIB.so or export PACEVAL_LIB")
endif()
add_library(paceval_external SHARED IMPORTED GLOBAL)
set_target_properties(paceval_external PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")
# Compile both vendor API source files directly into the executable;
# dynamically linking ONLY the external proprietary compute library.
add_executable(gateway_rules gateway_rules.cpp paceval_main.cpp)
target_include_directories(gateway_rules PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(gateway_rules PRIVATE paceval_external)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(gateway_rules PRIVATE -Wall -Wextra -Wpedantic)
endif()
enable_testing()
add_test(NAME native_model_and_data_validation COMMAND gateway_rules --self-test)
add_test(NAME original_paceval_runtime_replay COMMAND gateway_rules
  --replay "${CMAKE_CURRENT_SOURCE_DIR}/../examples/telemetry.csv"
  --out "${CMAKE_CURRENT_BINARY_DIR}/ctest_results.csv" --batch 37
  --tinc "${CMAKE_CURRENT_BINARY_DIR}/ctest_tinc.csv")
add_test(NAME versioned_rule_replacement COMMAND gateway_rules
  --replay "${CMAKE_CURRENT_SOURCE_DIR}/../examples/telemetry.csv"
  --out "${CMAKE_CURRENT_BINARY_DIR}/ctest_update.csv" --update-rule 17 --batch 37)
add_test(NAME reject_nonmonotonic_replay COMMAND gateway_rules
  --replay "${CMAKE_CURRENT_SOURCE_DIR}/../examples/invalid_timestamp.csv"
  --out "${CMAKE_CURRENT_BINARY_DIR}/ctest_invalid.csv")
set_tests_properties(reject_nonmonotonic_replay PROPERTIES WILL_FAIL TRUE)
