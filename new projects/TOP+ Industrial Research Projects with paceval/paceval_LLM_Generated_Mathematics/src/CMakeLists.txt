cmake_minimum_required(VERSION 3.16)
project(paceval_llm_expression_validation LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "This independently tested demonstrator targets Linux")
endif()
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()
if(NOT PACEVAL_RUNTIME OR NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}" OR NOT EXISTS "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Supply -DPACEVAL_RUNTIME=/absolute/path/libpaceval_linux_sharedLIB.so (or PACEVAL_LIB)")
endif()
add_library(paceval_vendor SHARED IMPORTED GLOBAL)
set_target_properties(paceval_vendor PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")
# IMPORTANT: compile original SDK interface CPP in the application and link external runtime.
add_executable(llm_math llm_math.cpp paceval_main.cpp)
target_include_directories(llm_math PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(llm_math PRIVATE paceval_vendor)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(llm_math PRIVATE -Wall -Wextra -Wpedantic)
  if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(llm_math PRIVATE -O3)
  endif()
endif()
enable_testing()
add_test(NAME parser_unit_tests COMMAND llm_math --self-test)
add_test(NAME actual_paceval_200_cases COMMAND llm_math
  --cases "${CMAKE_CURRENT_SOURCE_DIR}/../examples/expressions.csv"
  --sweep "${CMAKE_CURRENT_SOURCE_DIR}/../examples/sweep.csv"
  --output "${CMAKE_CURRENT_BINARY_DIR}/evaluation.csv" --batch 7)
add_test(NAME simple_formula_cli COMMAND llm_math --formula "exp(-k*t)*sin(w*t)+c" --values "0.2,-0.1,0.5,0.3,1.2,0.1")
add_test(NAME rejected_formula_cli COMMAND llm_math --formula "1/(t-t)" --values "0.2,-0.1,0.5,0.3,1.2,0.1")

# Offline semantic-contract workflow; Python stdlib only (not an LLM or MCP server).
find_package(Python3 COMPONENTS Interpreter)
if(Python3_Interpreter_FOUND)
  add_test(NAME llm_contract_reuse
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/validate_llm_workflow.py"
      --binary "$<TARGET_FILE:llm_math>"
      --input "${CMAKE_CURRENT_SOURCE_DIR}/../examples/llm_proposals.jsonl")
endif()

# Separate owner-approved model demonstration. This uses 48 input variables
# and a long reviewed formula; it never relaxes the untrusted input parser.
add_test(NAME approved_large_formula_48_variables COMMAND llm_math
  --approved-model "${CMAKE_CURRENT_SOURCE_DIR}/../examples/approved_48_variable_model.txt"
  --approved-output "${CMAKE_CURRENT_BINARY_DIR}/approved_large_model_results.csv")

if(Python3_Interpreter_FOUND)
  add_test(NAME approved_model_110_digit_and_policy_audit
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/validate_approved_model.py"
      --binary "$<TARGET_FILE:llm_math>"
      --manifest "${CMAKE_CURRENT_SOURCE_DIR}/../examples/approved_48_variable_model.txt")
endif()
