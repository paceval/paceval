cmake_minimum_required(VERSION 3.16)
project(JOSHUA_chess_research LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
# The supervisor can always be built and tested without the proprietary paceval
# shared object. It only orchestrates the real paceval-linked JOSHUA executable.
add_executable(joshua_selfplay joshua_selfplay.cpp zip_log_archive.cpp)
if(UNIX AND NOT APPLE AND CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
  target_link_options(joshua_selfplay PRIVATE -static-libstdc++ -static-libgcc)
endif()
# Write compressed ZIP files inside the C++ supervisor without depending on
# an external zip CLI or Python. Prefer static zlib for the distributed binary.
find_package(ZLIB REQUIRED)
find_library(JOSHUA_ZLIB_STATIC NAMES libz.a)
if(JOSHUA_ZLIB_STATIC)
  target_link_libraries(joshua_selfplay PRIVATE "${JOSHUA_ZLIB_STATIC}")
else()
  target_link_libraries(joshua_selfplay PRIVATE ZLIB::ZLIB)
endif()
# Only chess move helpers from chess_rules.h are needed; discard the unrelated
# SDK CSV conversion functions from this SDK-independent supervisor.
if(UNIX AND NOT APPLE)
 target_compile_options(joshua_selfplay PRIVATE -ffunction-sections -fdata-sections)
 target_link_options(joshua_selfplay PRIVATE -Wl,--gc-sections)
endif()
if(UNIX AND NOT APPLE)
 target_link_libraries(joshua_selfplay PRIVATE pthread)
endif()
option(JOSHUA_SELFPLAY_MANAGER_ONLY "Build only the subprocess supervisor without the paceval runtime" OFF)
if(JOSHUA_SELFPLAY_MANAGER_ONLY)
 find_package(Python3 COMPONENTS Interpreter REQUIRED)
 enable_testing()
 add_test(NAME joshua_selfplay_supervisor_parser COMMAND joshua_selfplay --selftest)
 add_test(NAME joshua_selfplay_zip_retention COMMAND "${Python3_EXECUTABLE}"
  "${CMAKE_CURRENT_LIST_DIR}/../scripts/test_v7_zip_retention.py"
  "$<TARGET_FILE:joshua_selfplay>" "${CMAKE_CURRENT_LIST_DIR}/../results/v3_ab_depth4_q1_10ply")
 add_test(NAME joshua_v8_progress_mock COMMAND "${Python3_EXECUTABLE}"
  "${CMAKE_CURRENT_LIST_DIR}/../scripts/test_v8_live_progress.py"
  "$<TARGET_FILE:joshua_selfplay>" "${CMAKE_CURRENT_LIST_DIR}/../results/v3_ab_depth4_q1_10ply")
 return()
endif()
# Official SDK adapter exposes many optional FFI entry points. Keep only those
# referenced by each executable when linking the optional forwarding loader.
if(UNIX AND NOT APPLE)
 set_source_files_properties(paceval_main.cpp PROPERTIES COMPILE_OPTIONS "-ffunction-sections;-fdata-sections")
 add_link_options(-Wl,--gc-sections)
 # Bundle the redistributable GNU C++ runtime into the executable instead of
 # requiring the target machine to have the same GCC 14 libstdc++ version.
 if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
   add_link_options(-static-libstdc++ -static-libgcc)
 endif()
endif()
option(JOSHUA_RUNTIME_DELAY_LOAD "Forward the original SDK FFI dynamically at program startup" ON)
if(JOSHUA_RUNTIME_DELAY_LOAD)
 # Produce runnable x86-64 ELF executables even if the external proprietary
 # runtime is not present on the BUILD machine. Evaluation still REQUIRES it.
 add_library(paceval_runtime STATIC paceval_runtime_loader.cpp)
 target_include_directories(paceval_runtime PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
 if(UNIX AND NOT APPLE)
   target_link_libraries(paceval_runtime PUBLIC dl)
 endif()
else()
 if(NOT PACEVAL_RUNTIME OR NOT EXISTS "${PACEVAL_RUNTIME}")
  message(FATAL_ERROR "Set -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so")
 endif()
 add_library(paceval_runtime SHARED IMPORTED)
 set_target_properties(paceval_runtime PROPERTIES IMPORTED_LOCATION "${PACEVAL_RUNTIME}")
endif()
add_test(NAME joshua_selfplay_supervisor_parser COMMAND joshua_selfplay --selftest)
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
add_test(NAME joshua_v7_offline_supervisor COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/test_v6_supervisor.py"
 "$<TARGET_FILE:joshua_selfplay>" "${CMAKE_CURRENT_LIST_DIR}/../results/v3_ab_depth4_q1_10ply")
add_test(NAME joshua_v7_zip_retention COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/test_v7_zip_retention.py"
 "$<TARGET_FILE:joshua_selfplay>" "${CMAKE_CURRENT_LIST_DIR}/../results/v3_ab_depth4_q1_10ply")
add_test(NAME joshua_v7_longgraph_offline_replay COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/test_v6_longgraph_supervisor.py"
 "$<TARGET_FILE:joshua_selfplay>" "${CMAKE_CURRENT_LIST_DIR}/../results/v5_graph_rebuilt_selfplay_8ply")
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

# JOSHUA V5 experiment: complete bounded legal tree compiled to one paceval decision graph.
add_executable(joshua_long_graph joshua_long_graph.cpp paceval_main.cpp)
target_include_directories(joshua_long_graph PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
target_link_libraries(joshua_long_graph PRIVATE paceval_runtime)
if(UNIX AND NOT APPLE)
 target_link_libraries(joshua_long_graph PRIVATE dl pthread)
endif()
add_test(NAME joshua_v5_compiled_depth2_minimax COMMAND joshua_long_graph --depth 2 --model 3
 --output "${CMAKE_CURRENT_BINARY_DIR}/v5_long_graph_depth2")

add_executable(joshua_game_audit joshua_game_audit.cpp paceval_main.cpp)
target_include_directories(joshua_game_audit PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
target_link_libraries(joshua_game_audit PRIVATE paceval_runtime)
if(UNIX AND NOT APPLE)
 target_link_libraries(joshua_game_audit PRIVATE dl pthread)
endif()
add_test(NAME joshua_v5_historical_game_legal_audit COMMAND joshua_game_audit
 "${CMAKE_CURRENT_LIST_DIR}/../input/chatgpt_vs_joshua_94_halfmoves.csv"
 "${CMAKE_CURRENT_BINARY_DIR}/v5_history_audit.json")
add_test(NAME joshua_v5_compiled_depth3_minimax COMMAND joshua_long_graph --depth 3 --model 3
 --max-nodes 25000 --output "${CMAKE_CURRENT_BINARY_DIR}/v5_long_graph_depth3")
add_test(NAME joshua_v5_compiled_v4_depth3_minimax COMMAND joshua_long_graph --depth 3 --model 4
 --max-nodes 25000 --output "${CMAKE_CURRENT_BINARY_DIR}/v5_long_graph_v4_depth3")

add_test(NAME joshua_v5_graph_rebuilt_before_each_move COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/run_long_graph_selfplay.py"
 --binary "$<TARGET_FILE:joshua_long_graph>" --depth 2 --model 4 --plies 3
 --output "${CMAKE_CURRENT_BINARY_DIR}/v5_graph_rebuild_selfplay")

add_test(NAME joshua_v5_huge_depth4_graph COMMAND bash "${CMAKE_CURRENT_LIST_DIR}/../scripts/run_graph_with_memory_limit.sh" "$<TARGET_FILE:joshua_long_graph>" --depth 4 --model 3
 --max-nodes 250000 --max-chars 2500000 --output "${CMAKE_CURRENT_BINARY_DIR}/v5_full_depth4")
add_test(NAME joshua_v5_huge_v4_neural_graph COMMAND bash "${CMAKE_CURRENT_LIST_DIR}/../scripts/run_graph_with_memory_limit.sh" "$<TARGET_FILE:joshua_long_graph>" --depth 4 --model 4
 --max-nodes 250000 --max-chars 2500000 --output "${CMAKE_CURRENT_BINARY_DIR}/v5_full_depth4_v4")
add_test(NAME joshua_v5_huge_v4_graph_independent_evidence COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_v5_graph.py" "${CMAKE_CURRENT_BINARY_DIR}/v5_full_depth4_v4")
set_tests_properties(joshua_v5_huge_v4_graph_independent_evidence PROPERTIES DEPENDS joshua_v5_huge_v4_neural_graph)
add_test(NAME joshua_v5_prior_blunder_no_extension COMMAND joshua --mode alphabeta --model 4
 --depth 2 --quiescence 0 --plies 1 --no-board
 --fen "r1bqkb1r/pp1p1pp1/n1p1p3/4P2p/1PnPBB2/PQN2N2/5PPP/R4RK1 b kq - 1 15"
 --output "${CMAKE_CURRENT_BINARY_DIR}/v5_blunder_q0")
add_test(NAME joshua_v5_prior_blunder_tactical_extension COMMAND joshua --mode alphabeta --model 4
 --depth 2 --quiescence 2 --plies 1 --no-board
 --fen "r1bqkb1r/pp1p1pp1/n1p1p3/4P2p/1PnPBB2/PQN2N2/5PPP/R4RK1 b kq - 1 15"
 --output "${CMAKE_CURRENT_BINARY_DIR}/v5_blunder_q2")

# Large formula compilation uses substantial memory. Never overlap these tests
# with other compute-heavy local paceval processes on a memory-limited CI host.
set_tests_properties(joshua_v5_huge_depth4_graph PROPERTIES RUN_SERIAL TRUE TIMEOUT 75)
set_tests_properties(joshua_v5_huge_v4_neural_graph PROPERTIES RUN_SERIAL TRUE TIMEOUT 85)

# Verified long-graph self-play release fixture: legal FEN chain and graph sizes.
add_executable(joshua_v5_selfplay_audit joshua_v5_selfplay_audit.cpp paceval_main.cpp)
target_link_libraries(joshua_v5_selfplay_audit PRIVATE paceval_runtime)
if(UNIX AND NOT APPLE)
 target_link_libraries(joshua_v5_selfplay_audit PRIVATE dl pthread)
endif()
target_include_directories(joshua_v5_selfplay_audit PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
add_test(NAME joshua_v5_eight_ply_graph_selfplay_replay COMMAND joshua_v5_selfplay_audit
 "${CMAKE_CURRENT_LIST_DIR}/../results/v5_graph_rebuilt_selfplay_8ply/selfplay_timeline.csv")
add_test(NAME joshua_v5_eight_ply_graph_evidence COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/check_v5_selfplay_evidence.py"
 "${CMAKE_CURRENT_LIST_DIR}/../results/v5_graph_rebuilt_selfplay_8ply")

# SDK-independent exploration policy. It does not claim a genuine paceval game.
add_executable(joshua_v8_exploration_policy_test "${CMAKE_CURRENT_LIST_DIR}/../tests/explore_policy_test.cpp")
target_include_directories(joshua_v8_exploration_policy_test PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
add_test(NAME joshua_v8_exploration_policy COMMAND joshua_v8_exploration_policy_test)
add_test(NAME joshua_v8_progress_mock COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/test_v8_live_progress.py"
 "$<TARGET_FILE:joshua_selfplay>" "${CMAKE_CURRENT_LIST_DIR}/../results/v3_ab_depth4_q1_10ply")
add_test(NAME joshua_v8_longgraph_diversity_replay COMMAND "${Python3_EXECUTABLE}"
 "${CMAKE_CURRENT_LIST_DIR}/../scripts/test_v8_longgraph_diversity.py"
 "$<TARGET_FILE:joshua_selfplay>" "${CMAKE_CURRENT_LIST_DIR}/../results/v5_graph_rebuilt_selfplay_8ply")

# V9 referee uses original legal-move logic but no mathematics runtime.
add_executable(joshua_referee joshua_referee.cpp)
# Discard unreferenced SDK CSV utility functions from chess_rules.h.
# The actual referee never evaluates paceval mathematics.
target_compile_options(joshua_referee PRIVATE -ffunction-sections -fdata-sections)
target_link_options(joshua_referee PRIVATE -Wl,--gc-sections)
if(UNIX AND NOT APPLE AND CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
 target_link_options(joshua_referee PRIVATE -static-libstdc++ -static-libgcc)
endif()

# Explicitly labelled offline UCI/paceval mocks. They verify the match
# coordinator and rejection/promote policy only, not engine chess quality.
add_test(NAME joshua_v9_stockfish_protocol_offline_mock
 COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../tests/test_v9_stockfish_mock.py")
