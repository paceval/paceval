cmake_minimum_required(VERSION 3.16)
project(paceval_technical_ai_agents LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# The original SDK C++ facade is compiled into our executable. The proprietary
# mathematical engine itself is supplied as an external Linux shared library.
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "This validated reference build targets Linux")
endif()
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()
if(NOT PACEVAL_RUNTIME OR NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}" OR NOT EXISTS "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Supply absolute -DPACEVAL_RUNTIME=/path/libpaceval_linux_sharedLIB.so or PACEVAL_LIB")
endif()
add_library(paceval_vendor SHARED IMPORTED GLOBAL)
set_target_properties(paceval_vendor PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")
add_executable(technical_agent technical_agent.cpp paceval_main.cpp)
target_include_directories(technical_agent PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(technical_agent PRIVATE paceval_vendor)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(technical_agent PRIVATE -Wall -Wextra -Wpedantic)
  if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(technical_agent PRIVATE -O3)
  endif()
endif()
enable_testing()
add_test(NAME native_self_tests COMMAND technical_agent --self-test)
add_test(NAME real_paceval_agent_casebook COMMAND technical_agent
  --cases "${CMAKE_CURRENT_SOURCE_DIR}/../examples/requests.csv"
  --output "${CMAKE_CURRENT_BINARY_DIR}/agent_results.csv"
  --tinc "${CMAKE_CURRENT_BINARY_DIR}/tinc_samples.csv"
  --batch 29)
message(STATUS "Using external paceval runtime: ${PACEVAL_RUNTIME}")
