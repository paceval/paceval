cmake_minimum_required(VERSION 3.16)
project(JOSHUA_chess_research LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT PACEVAL_RUNTIME OR NOT EXISTS "${PACEVAL_RUNTIME}")
 message(FATAL_ERROR "Set -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so")
endif()
add_library(paceval_runtime SHARED IMPORTED)
set_target_properties(paceval_runtime PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")
add_executable(chess_decision chess_decision.cpp paceval_main.cpp)
target_include_directories(chess_decision PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
target_link_libraries(chess_decision PRIVATE paceval_runtime)
if(UNIX AND NOT APPLE)
 target_link_libraries(chess_decision PRIVATE dl pthread)
endif()
add_executable(chess_search chess_search.cpp paceval_main.cpp)
target_include_directories(chess_search PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
target_link_libraries(chess_search PRIVATE paceval_runtime)
if(UNIX AND NOT APPLE)
 target_link_libraries(chess_search PRIVATE dl pthread)
endif()
find_package(Python3 COMPONENTS Interpreter REQUIRED)
enable_testing()
add_test(NAME chess_perft_special_moves_and_sdk COMMAND chess_decision --selftest)
add_test(NAME chess_full_depth3_paceval_graph COMMAND chess_decision --depth 3 --output "${CMAKE_CURRENT_BINARY_DIR}/test_output")
add_test(NAME chess_independent_results COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_results.py" "${CMAKE_CURRENT_BINARY_DIR}/test_output")
set_tests_properties(chess_independent_results PROPERTIES DEPENDS chess_full_depth3_paceval_graph)
add_test(NAME github_markdown_math_links COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_markdown.py" "${CMAKE_CURRENT_LIST_DIR}/..")
add_test(NAME github_markdown_negative_tests COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_markdown.py" --selftest)

add_test(NAME chess_csv_numeric_sdk_path COMMAND chess_decision --csv-demo "${CMAKE_CURRENT_LIST_DIR}/../input/chess_features.csv" "${CMAKE_CURRENT_BINARY_DIR}/test_csv")
add_test(NAME chess_csv_independent_reference COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_csv.py" "${CMAKE_CURRENT_LIST_DIR}/../input/chess_features.csv" "${CMAKE_CURRENT_BINARY_DIR}/test_csv/features_scored.csv")
set_tests_properties(chess_csv_independent_reference PROPERTIES DEPENDS chess_csv_numeric_sdk_path)

add_test(NAME chess_search_selftest COMMAND chess_search --selftest)
add_test(NAME chess_search_e4_depth2 COMMAND chess_search --depth 2 --output "${CMAKE_CURRENT_BINARY_DIR}/search_results")

add_executable(joshua joshua.cpp paceval_main.cpp)
target_include_directories(joshua PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
target_link_libraries(joshua PRIVATE paceval_runtime)
if(UNIX AND NOT APPLE)
 target_link_libraries(joshua PRIVATE dl pthread)
endif()
add_test(NAME joshua_selftest COMMAND joshua --selftest)
add_test(NAME joshua_automatic_4plies_depth2 COMMAND joshua --depth 2 --plies 4 --no-board --output "${CMAKE_CURRENT_BINARY_DIR}/autoplay_test")

# JOSHUA public mode is self-play only. Stockfish/Lc0 are not dependencies.
add_test(NAME joshua_independent_selfplay_audit COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_autoplay.py" "${CMAKE_CURRENT_BINARY_DIR}/autoplay_test")
set_tests_properties(joshua_independent_selfplay_audit PROPERTIES DEPENDS joshua_automatic_4plies_depth2)
add_test(NAME joshua_forced_opening_depth2 COMMAND joshua --first-move e2e4 --depth 2 --plies 3 --no-board --output "${CMAKE_CURRENT_BINARY_DIR}/forced_opening_test")
add_test(NAME joshua_forced_opening_audit COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_autoplay.py" "${CMAKE_CURRENT_BINARY_DIR}/forced_opening_test")
set_tests_properties(joshua_forced_opening_audit PROPERTIES DEPENDS joshua_forced_opening_depth2)

# Optimized JOSHUA research full-width and optional exact-horizon alpha-beta.
add_test(NAME joshua_opt_research_4plies_depth3 COMMAND joshua --mode research --depth 3 --plies 4 --no-board --output "${CMAKE_CURRENT_BINARY_DIR}/optimized_research_test")
add_test(NAME joshua_opt_alphabeta_4plies_depth3 COMMAND joshua --mode alphabeta --depth 3 --plies 4 --no-board --output "${CMAKE_CURRENT_BINARY_DIR}/optimized_ab_test")
add_test(NAME joshua_opt_research_independent_audit COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_autoplay.py" "${CMAKE_CURRENT_BINARY_DIR}/optimized_research_test")
add_test(NAME joshua_opt_alphabeta_independent_audit COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_autoplay.py" "${CMAKE_CURRENT_BINARY_DIR}/optimized_ab_test")
set_tests_properties(joshua_opt_research_independent_audit PROPERTIES DEPENDS joshua_opt_research_4plies_depth3)
set_tests_properties(joshua_opt_alphabeta_independent_audit PROPERTIES DEPENDS joshua_opt_alphabeta_4plies_depth3)
add_test(NAME joshua_opt_exact_mode_equivalence COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_mode_equivalence.py" "${CMAKE_CURRENT_BINARY_DIR}/optimized_research_test" "${CMAKE_CURRENT_BINARY_DIR}/optimized_ab_test")
set_tests_properties(joshua_opt_exact_mode_equivalence PROPERTIES DEPENDS "joshua_opt_research_4plies_depth3;joshua_opt_alphabeta_4plies_depth3")

# V3 independent physical feature extraction and high-precision graph verification.
add_executable(joshua_v3_audit joshua_v3_audit.cpp paceval_main.cpp)
target_include_directories(joshua_v3_audit PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
target_link_libraries(joshua_v3_audit PRIVATE paceval_runtime)
if(UNIX AND NOT APPLE)
 target_link_libraries(joshua_v3_audit PRIVATE dl pthread)
endif()
add_test(NAME joshua_v3_graph_numeric_audit COMMAND joshua_v3_audit "${CMAKE_CURRENT_BINARY_DIR}/v3_audit.csv")
add_test(NAME joshua_v3_independent_decimal COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_v3_audit.py" "${CMAKE_CURRENT_BINARY_DIR}/v3_audit.csv")
set_tests_properties(joshua_v3_independent_decimal PROPERTIES DEPENDS joshua_v3_graph_numeric_audit)
add_test(NAME joshua_v3_research_3plies_depth3 COMMAND joshua --mode research --model 3 --depth 3 --plies 3 --no-board --output "${CMAKE_CURRENT_BINARY_DIR}/v3_research")
add_test(NAME joshua_v3_alphabeta_3plies_depth3 COMMAND joshua --mode alphabeta --model 3 --depth 3 --plies 3 --no-board --output "${CMAKE_CURRENT_BINARY_DIR}/v3_alphabeta")
add_test(NAME joshua_v3_cross_mode_scores COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_mode_equivalence.py" "${CMAKE_CURRENT_BINARY_DIR}/v3_research" "${CMAKE_CURRENT_BINARY_DIR}/v3_alphabeta")
set_tests_properties(joshua_v3_cross_mode_scores PROPERTIES DEPENDS "joshua_v3_research_3plies_depth3;joshua_v3_alphabeta_3plies_depth3")
add_test(NAME joshua_v3_depth10_endgame COMMAND joshua --mode alphabeta --model 3 --depth 10 --plies 1 --fen "8/8/8/8/8/7P/2k5/K7 w - - 0 1" --no-board --output "${CMAKE_CURRENT_BINARY_DIR}/v3_depth10")

# Validate the recorded English ten-halfmove release trace without spending
# an additional minute rerunning the full chess game during CTest.
add_test(NAME joshua_v3_english_10ply_recorded_audit COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_autoplay.py" "${CMAKE_CURRENT_LIST_DIR}/../results/v3_ab_depth4_q1_10ply")

# JOSHUA V4 model-specific tests (local paceval only)
add_executable(joshua_v4_teacher joshua_v4_teacher.cpp paceval_main.cpp)
target_include_directories(joshua_v4_teacher PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
target_link_libraries(joshua_v4_teacher PRIVATE paceval_runtime)
if(UNIX AND NOT APPLE)
 target_link_libraries(joshua_v4_teacher PRIVATE dl pthread)
endif()

add_executable(joshua_v4_audit joshua_v4_audit.cpp paceval_main.cpp)
target_include_directories(joshua_v4_audit PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
target_link_libraries(joshua_v4_audit PRIVATE paceval_runtime)
if(UNIX AND NOT APPLE)
 target_link_libraries(joshua_v4_audit PRIVATE dl pthread)
endif()
add_test(NAME joshua_v4_trained_graph_audit COMMAND joshua_v4_audit
 "${CMAKE_CURRENT_LIST_DIR}/../training/teacher_positions.csv"
 "${CMAKE_CURRENT_LIST_DIR}/../formulas/v4_training_example_predictions.csv"
 "${CMAKE_CURRENT_BINARY_DIR}/v4_audit.csv")
add_test(NAME joshua_v4_high_precision_reference COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_v4_high_precision.py"
 "${CMAKE_CURRENT_BINARY_DIR}/v4_audit.csv"
 "${CMAKE_CURRENT_LIST_DIR}/../formulas/v4_trained_weights.json")
set_tests_properties(joshua_v4_high_precision_reference PROPERTIES DEPENDS joshua_v4_trained_graph_audit)
add_test(NAME joshua_v4_research_depth2 COMMAND joshua --mode research --model 4 --depth 2 --plies 3 --no-board --output "${CMAKE_CURRENT_BINARY_DIR}/v4_research")
add_test(NAME joshua_v4_alphabeta_depth2 COMMAND joshua --mode alphabeta --model 4 --depth 2 --plies 3 --no-board --output "${CMAKE_CURRENT_BINARY_DIR}/v4_alphabeta")
add_test(NAME joshua_v4_search_equivalence COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_mode_equivalence.py"
 "${CMAKE_CURRENT_BINARY_DIR}/v4_research" "${CMAKE_CURRENT_BINARY_DIR}/v4_alphabeta")
set_tests_properties(joshua_v4_search_equivalence PROPERTIES DEPENDS "joshua_v4_research_depth2;joshua_v4_alphabeta_depth2")
add_test(NAME joshua_v4_research_chess_trace COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_autoplay.py" "${CMAKE_CURRENT_BINARY_DIR}/v4_research")
set_tests_properties(joshua_v4_research_chess_trace PROPERTIES DEPENDS joshua_v4_research_depth2)
add_test(NAME joshua_v4_alphabeta_chess_trace COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_autoplay.py" "${CMAKE_CURRENT_BINARY_DIR}/v4_alphabeta")
set_tests_properties(joshua_v4_alphabeta_chess_trace PROPERTIES DEPENDS joshua_v4_alphabeta_depth2)
