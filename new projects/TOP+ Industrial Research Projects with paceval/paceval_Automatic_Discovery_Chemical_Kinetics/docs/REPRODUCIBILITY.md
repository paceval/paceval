# WP 27 | Reproducibility and data contracts

This file extends the [main project README](../README.md) and is itself subject to the archive-wide mathematics/link gate.

## Execution environment

Linux x86-64, C++17 (GCC or Clang), CMake 3.16+, Python 3 with NumPy, matplotlib, mpmath, Mistune 3 with its math plugin, PIL, ReportLab. Link the original public `src/paceval_main.h` and `src/paceval_main.cpp` to a separately provided compatible original `libpaceval_linux_sharedLIB.so`, paceval SDK 4.25. No substitute paceval implementation is permitted. Production data have no dependency on real reactor observations.

## Exact commands

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \
  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/kinetic_discovery --run 512 256 256 results
python3 validation/check_high_precision.py results
python3 src/make_figures.py
python3 src/make_whitepaper.py
python3 src/check_archive_markdown.py
python3 src/check_publication.py
python3 src/check_manifest.py
```

## CSV contracts

All CSV files are UTF-8, comma separated, use decimal dots, single header row and stable line endings. Numeric text conversion in the compiled C++ program uses real paceval SDK `double`-to-string and string-to-`double` routines. The strict numeric parser accepts only finite numerical literals and rejects equations in data fields. Text-based CSV serialization may round compared with binary IEEE-754 output; no bitwise reversibility is asserted.

- `results/synthetic_kinetics_observations.csv`: row ID, `TRAIN`/`VALIDATION`/`HOLDOUT`, concentrations (mol/L), temperature (kelvin) and synthetic observed rate (mol L^-1 h^-1).
- `results/candidate_search.csv`: 1,000 unique fixed search formula parameterizations, fitted constants and train/validation scores.
- `results/selected_models.csv`: two frozen selected versions and corresponding held-out scores.
- `results/holdout_predictions.csv`: recorded paceval rates, residual-derived loss, analytical sensitivities and logical rate indicators.
- `results/integrated_reaction_profiles.csv`: two selected models, eight isothermal initial-condition scenarios, 81 time samples per scenario.
- `results/model_response_surface.csv`: real batch output on concentration grids at 300 K and 340 K.
- `results/model_temperature_and_saturation_curves.csv`: two scan types using genuine paceval rate handles.
- `results/formula_registry.csv`: exact graph formula text, including 1,000 candidate basis expressions.
- `results/math_execution_inventory.csv`: actual function-ownership and mathematical execution table.
- `results/execution_evidence.json`: successful graph handles, graph-point outputs, scalar calls, batches and tested end values.
- `results/independent_validation.json`: independent Python candidate scoring, 80-digit audit and numerical status.

## Candidate identification

The 1,000 candidates comprise five model families, five A concentration exponents, five B exponents, four activation energies and two family-specific coefficient variants. Candidate prefactors are fitted only from training data. Model ranking uses validation scores and complexity; held-out data are not read during ranking. Test temperatures are intentionally shifted from the training range.

The synthetic data generator embeds the correct family and parameter combination in the original C++ source. A correct reconstruction is evidence that the fixed constrained library and mathematical execution layer work under these chosen synthetic conditions, **not** proof that genuinely unknown chemical mechanisms have been discovered.

## Independent controls

`validation/check_high_precision.py` independently reconstructs all 1,000 candidate factors, k-prefactor fits and selection scores. It also tests selected recorded holdout rates with 80-digit mpmath formulas and verifies all trajectory concentration invariants. The C++ implementation independently evaluates every holdout output and both selected ODE trajectories. The public report does not display engine-by-engine numerical deviation tables; these are preserved in technical audit outputs.

## Limitations

- All data, loss thresholds and reaction states are synthetic.
- The source search grammar contains the synthetic truth by design.
- The rate observations are provided directly, not inferred from noisy concentration derivatives.
- Only a single conceptual isothermal $A+B\rightarrow P$ stoichiometry is implemented.
- The calibration coefficient $k_{ref}$ has candidate-dependent dimensions.
- Species conservation does not verify activation pathways or reaction mechanism.
- The rate-envelope constraint is an illustrative scalar check rather than an industrial safety criterion.
- No CPU/GPU/FPGA or native engine performance comparison is performed or reported.
