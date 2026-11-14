# Results: provenance and status

All `dispatch_timeseries.csv`, `schedule_summary.csv`, `model_comparison.csv`, `native_audit.csv`, `formula_manifest.csv`, `math_execution_inventory.csv` and `execution_evidence.json` are generated from **actual execution of the compiled C++ application with the original paceval 4.25 SDK and supplied Linux shared runtime**. They are not fabricated test fixtures. They are deterministic synthetic mathematical screening outcomes, not measured site or operational grid data.

Command: `./build/microgrid_dispatch --run input/dispatch_candidates.csv input/parameters.csv results`.

`high_precision_audit.json` is generated independently with Python: `python3 scripts/verify_high_precision.py results input`.

The external runtime `.so` must be provided outside the published ZIP. The high-precision verifier uses independent equations, not graph expression strings or copied reference values.
