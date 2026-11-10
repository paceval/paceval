cmake_minimum_required(VERSION 3.12)
project(paceval_collider_research LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(collider collider.cpp)
if(UNIX AND NOT APPLE)
  target_link_libraries(collider PRIVATE ${CMAKE_DL_LIBS})
endif()
if(MSVC)
  target_compile_options(collider PRIVATE /W4 /O2)
else()
  target_compile_options(collider PRIVATE -O3 -Wall -Wextra -Wpedantic)
endif()

enable_testing()
add_test(NAME native_self_test COMMAND collider --self-test)

# The vendor runtime is provided by the developer, not committed to GitHub.
# Supply an absolute filename with -DPACEVAL_RUNTIME=/path/to/libpaceval_linux_sharedLIB.so
# or export PACEVAL_LIB=/path/to/libpaceval_linux_sharedLIB.so before configuring.
if(NOT PACEVAL_RUNTIME AND DEFINED ENV{PACEVAL_LIB})
  set(PACEVAL_RUNTIME "$ENV{PACEVAL_LIB}")
endif()

if(PACEVAL_RUNTIME)
  if(NOT EXISTS "${PACEVAL_RUNTIME}" OR IS_DIRECTORY "${PACEVAL_RUNTIME}")
    message(FATAL_ERROR "PACEVAL_RUNTIME must identify an existing shared-library file: ${PACEVAL_RUNTIME}")
  endif()
  if(NOT IS_ABSOLUTE "${PACEVAL_RUNTIME}")
    message(FATAL_ERROR "PACEVAL_RUNTIME must be an absolute path")
  endif()
  add_test(NAME real_paceval_sample
    COMMAND collider --library "${PACEVAL_RUNTIME}" --require-paceval
    --input-csv "${CMAKE_CURRENT_SOURCE_DIR}/../examples/example_events.csv"
    --events 100 --batch 16 --csv "${CMAKE_CURRENT_BINARY_DIR}/example_measurement.csv")
  message(STATUS "Actual paceval runtime test enabled: ${PACEVAL_RUNTIME}")
else()
  message(STATUS "paceval runtime was not specified; only the native self-test is registered")
endif()
