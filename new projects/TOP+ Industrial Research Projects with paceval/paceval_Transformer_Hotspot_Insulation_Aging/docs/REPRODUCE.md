# Full Reproduction on Linux

1. Install CMake >=3.16, a C++17 compiler, Python3 with `mpmath`, `pandas`, `matplotlib`, `Pillow`, `reportlab`, `markdown-it-py` and a compatible original paceval Linux runtime.
2. Follow the exact commands in root `README.md` to generate deterministic input, build, run five CTests, produce results and create ten vector/PNG figures plus the PDF.
3. CMake takes `-DPACEVAL_RUNTIME=/absolute/path/to/...so`. The `src/paceval_main.cpp` file is original 4.25 interface with a minimal include-path fix. The `.so` is not shipped.
4. Compare `results/execution_evidence.json` with the run log. The CTest suite uses an independent temporary results directory; full reproduction in `results/` allows comparing SHA256 of eight CSVs, after accounting for possible version-specific decimal formatting. Byte-identical tests are only claimed for the platform on which actually run.
5. Inspect `results/high_precision_audit.json` for exact numeric tolerances, failed cases and numerical accuracy auditing. The 85-decimal-digit mpmath calculations are independent physical formulas, not restatements of paceval expression strings.
6. The README link validator also runs deliberately broken-link and broken-code-fence negative tests.

No external commercial license, reference measurement data, or sensor telemetry is embedded. The original graphic is a conceptual rendering, and the PDF scientific plots are directly built from the `hotspot_timeseries.csv` and `asset_summary.csv` files.
