cmake_minimum_required(VERSION 3.16)
project(paceval_credit_scorecard_research LANGUAGES CXX)

# The official source facade in this repository is compiled into the executable.
# The matching binary math engine is an EXTERNAL dependency (not redistributed).
if(NOT PACEVAL_RUNTIME)
  message(FATAL_ERROR "Supply -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so")
endif()
if(NOT EXISTS "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "PACEVAL_RUNTIME does not exist: ${PACEVAL_RUNTIME}")
endif()

add_executable(credit_scorecard credit_scorecard.cpp paceval_main.cpp)
target_compile_features(credit_scorecard PRIVATE cxx_std_17)
target_include_directories(credit_scorecard PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(credit_scorecard PRIVATE "${PACEVAL_RUNTIME}")

if(MSVC)
  target_compile_options(credit_scorecard PRIVATE /W4)
else()
  target_compile_options(credit_scorecard PRIVATE -Wall -Wextra -Wpedantic)
endif()

# RUNPATH points to the external runtime directory on Linux, not a bundled .so.
if(UNIX AND NOT APPLE)
  get_filename_component(PACEVAL_RUNTIME_DIR "${PACEVAL_RUNTIME}" DIRECTORY)
  set_target_properties(credit_scorecard PROPERTIES BUILD_RPATH "${PACEVAL_RUNTIME_DIR}")
endif()

enable_testing()
add_test(NAME paceval_scalar_and_batch_sdk_check
         COMMAND credit_scorecard --test --out "${CMAKE_CURRENT_BINARY_DIR}/test_scorecards.csv")
