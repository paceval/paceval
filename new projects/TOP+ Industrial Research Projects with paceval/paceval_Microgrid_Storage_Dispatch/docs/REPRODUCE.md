# Exact experiment replay

Run from repository root using a compatible original Linux runtime external to this repository:

```bash
python3 scripts/generate_input.py
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/microgrid_dispatch --run input/dispatch_candidates.csv input/parameters.csv results
python3 scripts/verify_high_precision.py results input
python3 scripts/make_figures.py
python3 scripts/make_whitepaper.py
```

The generation script makes the same synthetic source rows using deterministic fixed seeds; replacing any input, numerical library, platform, compiler or model version requires revalidating the result files. Only the original paceval executable produces the recorded primary mathematical results. The independent Python reference does not regenerate or replace the production outputs.

For an archival data-integrity check, compare SHA-256 hashes of the eight generated files after rerun. Their paths and provenance are listed in `results/README.md`. Floating-number text formatting is performed by the original paceval SDK, so byte-identical output is guaranteed only for the actually tested binary/host combination and should not be generalized across arbitrary platforms.
