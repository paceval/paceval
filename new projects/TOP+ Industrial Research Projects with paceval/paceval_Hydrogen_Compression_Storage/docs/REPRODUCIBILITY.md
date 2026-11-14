# Reproducibility and versioned research outputs

The study uses synthetic, deterministic numerical inputs. Its purpose is to prove that the stated physical screening expressions can be **executed by original paceval graphs**, composed through repeated state transitions, and independently verified. It does not validate an actual compressor, pressure vessel or hydrogen distribution station.

## Numerical CSV contract

Each compressor row contains a stable integer `id`, a source and target pressure in bar, gas inlet temperature in K, an illustrative polytropic efficiency, $\gamma$, constant $c_p$ (J/kg/K), mass flow (kg/s), cooler setpoint, cooler effectiveness and per-stage screening limits. The application writes each numeric value using `paceval_dConvertFloatToString`, then **reopens** the CSV and parses validated decimal literals using `paceval_dConvertStringToFloat`. Regex literal checks prevent implicit evaluation of mathematics contained in a numeric CSV field. Separator is comma, decimal point is a period, no ambiguous localized decimal grouping is permitted.

The generated per-case output is `compression_scenarios.csv` for both model versions. Every result is produced by actual original paceval graph evaluation. `stage_trace_samples.csv` records selected stage data, pressure derivatives and mathematical guards. `storage_profiles.csv` contains actual graph-generated time trajectories.

The original compressed-data source has a user-uploaded provenance in `docs/original_WP24_proposal.pdf`. It is a **proposal**; it is not an independently executed study.

## Graph and state order

The host enumerates 1–4 stages and builds the input arrays; the pressure target is evaluated in a paceval graph. For each version and stage, 17 compressor graphs are evaluated as a real multi-graph batch. Their **actual outputs** update the next-stage inlet temperature, the current stage pressure and the cumulative compressor power and intercooler heat removal. The host does not replace these output values with a native calculation.

For each storage scenario, stage graphs first determine the filling-gas temperature. A separate paceval graph computes initial mass from the specified initial pressure. Fourteen storage graphs evaluate $dT/dt$, the next mass, next temperature and next pressure. The C++ host advances the state by passing these actual graph values back as the next step's inputs. Pressure/temperature margin graphs and Boolean guards are evaluated in the same call.

## Independent validation and counting

All productive compressor stages were independently checked against native C++ analytic expressions. A separate mpmath implementation with `mp.mp.dps = 80` validates recorded stage outputs and analytic derivatives, without evaluating the paceval expression source. An independent storage check examines the mass-temperature-pressure identity at every synthetic state point. Tests also cover extreme stage ratios, count alignment, constrained Boolean operators, `%` versus `mod`, numeric input grammar and actual batch ordering. Detailed numeric comparison differences remain in the technical audit, not in the public publication figures.

The number `graph_point_evaluations` counts one actual output of one graph for one independent input row (including scalar calls). It does not count independent reference calculations or repetitions, and it is not the number of unique graphs. `multi_graph_batch_calls` counts calls to the real API, not the number of points. `executed_unique_graphs` requires successful output from the actual SDK.

## Reproduction and validation

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \
  -DPACEVAL_RUNTIME=/your/compatible/original/paceval.so
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/hydrogen_thermal_kernels --run 100000 16 /tmp/wp24_replay
python3 validation/check_high_precision.py /tmp/wp24_replay
```

The full input and output CSV data are reproducible under the tested toolchain/SDK. A shell file comparison confirms byte-level reproducibility for explicitly listed primary result files, not universal cross-platform floating-point textual equivalence.

The archive-wide math checker in `src/check_archive_markdown.py` uses Mistune's Markdown math parser and nine intentionally broken mathematical Markdown snippets. Every Markdown file in the archive must pass. A byte-for-byte reproducibility check must operate on the **final** ZIP, not merely on its working folder.

## Source-level license and dependency note

`src/paceval_main.h` and `src/paceval_main.cpp` are the original redistributable public-facing SDK interface sources already available with the research inputs; their original copyright notices are preserved. The executable requires an external original runtime library, which is not part of this ZIP. Scientific plots and report generation require only the Python packages declared in `src/requirements.txt`. Do not interpret use of the original SDK adapter as evidence of any remote MCP call.
