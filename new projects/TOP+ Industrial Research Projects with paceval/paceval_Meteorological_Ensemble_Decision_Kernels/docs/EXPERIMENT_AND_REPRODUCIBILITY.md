# Executed experiment and scientific evidence

**Research status:** executed with the original paceval SDK 4.25 and the separately supplied compatible Linux shared library. This repository does **not** bundle the library.

This project is a reproducible mathematical demonstration using generated ensemble features and simulated binary event labels. No ECMWF, NOAA or DWD forecast grids or station observations were downloaded or included. Therefore no operational forecast-skill, warning or real industrial loss result is claimed.

## What was actually executed

- 10,000 synthetic site IDs; four nominal lead horizons; three separate event types per site-lead.
- 120,000 generated and CSV-reread feature records, each with 51 synthesized member values.
- 240,000 distinct versioned model-case rows, two immutable fixed illustrative coefficient sets.
- 60 unique created/executed paceval graphs: 12 primary and 17 secondary per version, plus two matched compound-event bounds.
- 10,086 additional response-surface points computed through the original graph handles.
- 7,460,172 individual graph-point results, with the official multi-graph batch API and per-output error checks.
- 6,960,000 native C++ independent model-value checks; 480,000 independent compound-bound checks; 20,172 independent response-surface checks.
- 1,890 independent 80-decimal-precision sample rows, representing 20,790 values; plus 1,219 sample compound-pair bound checks.
- Automated CTest suite: 12 of 12 tests passed in the publication build. The suite includes conversion semantics, operator semantics, batch layout, invalid domains, sample execution, 80-digit comparison, archive provenance, GitHub README check/negative test, PDF integrity, and SHA-256 manifest verification.

Numbers above are sourced from `results/execution_evidence.json` and `results/validation_evidence.json` and from the successful CTest output. Repeated fresh-extraction checks are **not** added to main-run totals.

## Mathematical and metrological limitations

The `paceval_dConvertFloatToString` route serializes numerical output with a finite decimal representation. Numerical values in the archival CSV therefore may not preserve the original binary64 value bit for bit. The verifier uses an independently coded 80-decimal mathematical expression and a documented tolerance suitable for decimal serialization. Byte-for-byte identical result files, where reproduced, show deterministic program output on the tested runtime; they are not a numerical certification for all hardware.

The sample data do not provide operational forecast timestamps or genuine matching station observations; the four synthetic lead horizons and hazard-specific validity windows are **not** a meteorological archive. The two mathematical versions are different parameterizations, not a claim about historical calibration improvements. Independently generated synthetic binary labels are not proof of forecasting accuracy on real events.

## Reproduction

From the repository root with a compatible original Linux paceval shared library at a separately configured absolute path:

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/weather_kernels --run --sites 10000 --out results/reproduced
python validation/verify_weather_reference.py results/reproduced
```

The last command writes a reference validation evidence JSON into `results/reproduced` and should not overwrite the previously recorded main run. Compare SHA-256 digests for the central result CSV and evidence files if required. No performance benchmark or speedup is part of the experiment.
