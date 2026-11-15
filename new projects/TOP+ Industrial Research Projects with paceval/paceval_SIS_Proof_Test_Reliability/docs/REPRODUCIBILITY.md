# Reproducibility contract

The shipped project contains original public paceval SDK integration files in `src/paceval_main.h` and `src/paceval_main.cpp`; users supply a compatible Linux x86-64 shared library externally with CMake `PACEVAL_RUNTIME`. Build with C++17, run self-tests, and run the deterministic 100,000-input-scenario dataset.

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/sis_reliability --run 100000 replay_results
python3 validation/check_mpmath.py replay_results
```

The C++ numeric input file `results/synthetic_input.csv` is generated deterministically and **re-read** through `paceval_dConvertStringToFloat` after strict validation against a numeric-literal grammar. Input and output files have comma-separated fields, dot decimal notation, UTF-8-compatible ASCII columns and LF newlines. Float output is formatted through `paceval_dConvertFloatToString`, whose precision is **not guaranteed to preserve every original double bit**. Do not conflate rounded text with a bit-identical physical measurement.

Each of the two architecture models creates 20 persistent mathematical graphs. The main program evaluates each group in `paceval_dGetMultipleComputationsResultsExt` batches. The global JSON `results/execution_evidence.json` counts 100,000 distinct synthetic inputs, 200,000 model cases and separate surface/cycle graph evaluations. A separate `validation/check_mpmath.py` numerically integrates selected instantaneous PFD curves at 85 decimal digits and independently checks sensitivities.

`src/check_archive_markdown.py` tests every `*.md` in all subdirectories and includes nine deliberately malformed Markdown cases that must fail. GitHub's remote web renderer is not claimed to have been visually inspected. The README uses `$...$` and `math` code fences, not raw LaTeX delimiters.

Run `python3 src/make_figures.py` to regenerate figures. The images are generated from logged paceval outputs, **not** from independent reference values. The external paceval shared binary is intentionally absent from the release archive. The archived SHA256SUMS manifest verifies all files apart from itself, and the full project is retested after freshly extracting the ZIP.
