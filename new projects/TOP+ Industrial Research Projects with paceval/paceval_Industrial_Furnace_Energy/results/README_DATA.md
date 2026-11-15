# Dataset provenance

* `mcp_observed_grid_transcription.csv`: all 49 grid cases actually evaluated through MCP 4.26; selected result columns transcribed at up to 14 significant digits from returned output and reconstructed using the observed linear fuel increment for each wall row. **Not a raw JSON payload.**
* `mcp_observed_snapshots.csv`: actual 12-case MCP batch selected values recorded to the displayed precision.
* `mcp_tinc_observed.csv`: 12 actual returned interval-enabled point outputs and bounds.
* `operator_mcp_selftest.json`: actual SDK-compatible operator semantics returned by the remote 4.26 engine.
* `independent_reference_all_61.csv`: independent 90-digit mpmath reference values, *not* remote paceval data.
* `high_precision_validation.json`: numerical comparisons/point inclusion, including recorded maximum error and failure log.
* `execution_evidence.json`: counts, version, scope, negative claims.
* `math_execution_inventory.csv`: all owned mathematical functions with execution status and units.
