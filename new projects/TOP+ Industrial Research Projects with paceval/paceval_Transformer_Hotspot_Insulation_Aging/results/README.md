# Research Results and Audits

All files in this directory except `high_precision_audit.json` and `release_qa.json` are emitted by the compiled C++ application using the original paceval 4.25 SDK. `high_precision_audit.json` is emitted by a separate mpmath reference after checking complete sampled time series. `release_qa.json` contains separately run packaging and reproduction checks. All input data is synthetic and deterministic.

- `hotspot_timeseries.csv`: 96,768 actual graph-derived model-hour results, including temperature, FAA, state memory, cumulative equivalent-aging hours, margins, logical guard and sensitivities.
- `asset_summary.csv`: 288 model-asset-scenario series summaries, aggregated from the paceval-produced state values.
- `model_comparison.csv`: 144 paired V1/V2 series results. Temperature differences and age ratios are obtained from actual paceval comparison graphs.
- `formula_manifest.csv`: exact registered original paceval formulas, graph IDs, versions and units.
- `math_execution_inventory.csv`: scientific calculation ownership and observed graph execution status.
- `native_audit.csv`: sampled main-path independent native C++ checks.
- `execution_evidence.json`: observed original SDK API call counters, graph counts and complete scenario counts.
- `high_precision_audit.json`: 85-digit reference assertions and internal numerical differences, with declared tolerances. These are technical audit values, not published accuracy comparisons.
- `release_qa.json`: integration tests, PDF inspection, archive and output reproduction status.

The term “equivalent aging” means integration of a **model-defined relative Arrhenius acceleration** using 110 °C as reference, not measured or estimated residual equipment lifetime. The model is not a faithful full implementation of IEEE C57.91-2025.
