# Reproduce the WP17 paceval distillation experiment

Run the build and the mathematical tests on Linux x86-64 with a compatible original paceval shared library, supplied separately. No package in this repository contains the vendor runtime binary. All numerical source values are either published NIST Antoine coefficients or explicitly stated synthetic assumptions.

## Build and run

```bash
python3 -m pip install -r src/requirements.txt
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/distillation_kernels --run 250000 1500 ./results
python3 validation/validate_results.py ./results
python3 src/make_figures.py
python3 src/check_archive_markdown.py
```

The executable creates the CSV input file first and reads it back through `paceval_dConvertStringToFloat`, validates the scientific range, then calls actual paceval functions in a series of reusable multi-graph batches. The subsequent dependent streams are taken from previous graph outputs rather than precalculated C++ values. It writes its key execution counters to `results/execution_evidence.json`. Repetition of the full run should regenerate the same canonical output files with compatible runtime and numerics, although no cross-platform byte-identity guarantee is made.

A smaller reproducible mode is `./build/distillation_kernels --run 64 16 ./build/smoke_data`. The negative CSV cases are included in the C++ selftest; invalid numeric formulas are rejected by the schema before invoking the paceval numerical parser. A separate floating-point formatting audit distinguishes printed decimals from IEEE-754 binary representations.

## Data lineage and precise scope

- `synthetic_vle_inputs.csv`: synthetic composition and temperature samples and controlled process parameters.
- `formula_registry.csv`: exact formulas registered as persistent paceval graphs for both versions.
- `math_execution_inventory.csv`: execution owner and validation mapping for every important function.
- `vle_samples.csv`: sparse recorded results from graph-evaluated main workloads, including VLE sensitivities and energy/quality margins.
- `isobaric_equilibrium_curves.csv`: paceval equilibrium values on the 0.60 bar bubble-pressure constraint. Bubble temperatures are obtained by host bisection of an actual paceval pressure graph.
- `column_configurations.csv`: approximated stage counts for a predeclared synthetic set of column variants; flux and duty values are computed through chained paceval graph evaluations.
- `numerical_audit.csv`: selected independent native mathematical checks.
- `independent_validation.json`: independent high-precision and bubble-point verification evidence.

## Publication checklist

The repository has a source-level archive-wide GitHub math preflight based on Mistune; inspect its negative regressions to see what it rejects. All relative Markdown image and whitepaper links must resolve inside this archive. Every PDF page must be rendered and visually reviewed. For any new mathematical model version, update both the formula registry and the independent reference before publishing.
