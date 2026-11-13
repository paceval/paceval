# Industrial Calibration at Formula Scale with paceval

![Industrial mathematical calibration](figures/00_calibration_hero.png)

**Scientific functionality demonstrator | 13 November 2026 | Original paceval SDK 4.25**

This project examines the practical feasibility of using real, persistent **paceval mathematical execution graphs** for long piecewise calibration functions in industrial measurement and digital-twin preprocessing. It extends the earlier study, *Industrial Calibration at Formula Scale*, from very large one-version expressions to **two live formula versions**, temperature and drift compensation, sensitivity analysis, first-order uncertainty functions, synthetic quality-decision margins and formula governance scores. **No computational performance or hardware speedup comparison is made.**

The C++ host validates input, groups measurements by their piecewise interval blocks, selects model versions and interprets mathematical decision margins. **paceval actually executes the interpolation, local slopes, corrected output, analytical sensitivities, uncertainty propagation, residuals, limits and 16 different governance scores for each version.** All source expressions are recorded verbatim in the execution registry.

## Demonstrated functionality

| Research feature | Executed evidence |
|---|---|
| Two independently retained mathematical calibration models | `v1` and `v2` are simultaneously instantiated; no change to host logic when the formula changes |
| Piecewise model, default | **4,096 intervals per model**, 256 terms per routed graph |
| Large-capacity validation | **65,536 intervals per model**, 512 terms per routed graph |
| Original paceval computation objects | **121** graphs in default execution; **569** in capacity run |
| Actual mathematical graph outputs | **193,265** in each standard/capacity run (including real 3-D surface inputs) |
| Mathematical independent controls | **15,840** native C++ checks of sample quantities per run |
| Independent high precision | **15,840** 80-decimal-digit comparisons per run with a separately implemented `mpmath` oracle |
| Execution APIs | persistent creation, scalar, single-graph batch and multi-graph batch |
| Quality policies | synthetic `ACCEPT`, `REVIEW`, `REJECT` derived from paceval-computed margins |
| Model governance | preserved graph formulas, versions, source input CSV, hashes and auditable decisions |

These counts are from the included execution records and are checked by `verify_inventory.py`. Additional 2,501 real output values per model were calculated for an `(x,T)` surface (61 x-values by 41 temperatures); the surface is **not** a plotted approximation produced outside paceval.

## Primary application

A **non-safety-critical machine-axis correction / precision sensor calibration module** receives normalized raw signal `x`, temperature `T` and normalized drift input `d`. It retrieves a versioned piecewise-linear sensor function `S_v(x)` and executes a corrected measurement function. The research study uses deterministic synthetic knot values; it does not characterize any real sensor or establish metrological traceability.

The existing industrial research identifies additional applications including production quality scoring, flow and load measurement, digital-twin preprocessing and mathematical model fleet management. This package explicitly develops the machine-axis, precision-sensor, synthetic quality-gate and temperature-cycle scenarios.

### Complete mathematical model

For 4,096 intervals (default) or 65,536 intervals (capacity validation), `x_i=i/n`. With interval index `i`,

\[
S_v(x)=y_{i,v}+(y_{i+1,v}-y_{i,v})\frac{x-x_i}{x_{i+1}-x_i},\qquad x_i\le x<x_{i+1}.
\]

The final interval includes `x=1`. The synthetic knot generator is

\[
y_{i,1}=0.12+0.75x_i+0.09\sin(9x_i)+0.035\sin(37x_i)+0.04\exp[-((x_i-0.72)/0.06)^2],
\]

\[
y_{i,2}=y_{i,1}+0.002\sin(5x_i)+0.001x_i.
\]

The full correction executed by paceval is

\[
G_v(x,T,d)=S_v(x)[1+0.00035(T-20)]+0.0005(T-20)+0.000075\sin(7x)(T-20)+d(0.001+0.0015x).
\]

The default domains are `x in [0,1]`, `T in [0,60] degrees Celsius`, and `d in [-1,1]`. The C++ host **rejects** any out-of-domain, missing or nonfinite input. All outputs are normalized synthetic model units, not SI-calibrated quantities.

Local analytical derivatives `dG/dx`, `dG/dT` and `dG/dd` are paceval graphs. At interior interpolation knots, `dG/dx` follows the right-hand interval convention; at `x=1` the leftmost (final) segment is used. No classical derivative of a piecewise-linear interpolant exists at knots with unequal adjacent slopes; the value is therefore a declared one-sided sensitivity convention, not a proof of differentiability.

An *illustrative* first-order standard-uncertainty graph assumes uncorrelated inputs:

\[
u=\sqrt{(\partial_xG\,u_x)^2+(\partial_TG\,u_T)^2+(\partial_dG\,u_d)^2+u_{model}^2}.
\]

The inclusion of a model term does not demonstrate its actual statistical or metrological validity. For a synthetic reference `r` and tolerance `t`, the paceval decision margins are `m_accept=t-|G-r|-2u` and `m_reject=t-|G-r|+2u`. The host returns `ACCEPT` when `m_accept>=0`, `REJECT` when `m_reject<0`, and `REVIEW` otherwise. This is a **hypothetical decision-support test**, not an industrial release rule.

There are 16 additional versioned score formulas combining absolute residual, uncertainty, local sensitivity and operating drift. All 16 are persistently created and executed by paceval. The independent reference is only a validation oracle, not an alternative production inference engine.

## Reproduce with the original library

The SDK interface `paceval_main.cpp` and `paceval_main.h` is included, with only the Linux include location adapted in `paceval_main.cpp`. The binary shared library is **not** included. Use your compatible separately provided Linux runtime; this project was tested using that runtime.

```bash
cmake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j4
./build/industrial_calibration . 128
python3 src/independent_reference.py .
python3 src/make_figures.py
ctest --test-dir build --output-on-failure
```

For the separate large-capacity verification, which leaves the normal results intact:

```bash
python3 src/run_large_capacity.py ./build/industrial_calibration
```

The large run creates 569 original paceval graphs for two models with 65,536 intervals each, and independently verifies its outputs with 80-digit arithmetic. For graph evaluation the demonstration uses `paceval_dGetComputationResultExt()` and `paceval_dGetMultipleComputationsResultsExt()`. C++ operates only as input validator, dispatcher, CSV writer, independent checker and decision-state interpreter. `mpmath` is needed only by the independent audit, while `matplotlib` and `numpy` are used only to render figures. Productive C++ code needs no external numerical framework.

## Results and files

- [`src/industrial_calibration.cpp`](src/industrial_calibration.cpp): the functioning C++ research demonstrator.
- [`src/CMakeLists.txt`](src/CMakeLists.txt): CMake build and CTest suite.
- [`examples/synthetic_sensor_inputs.csv`](examples/synthetic_sensor_inputs.csv): four reproducible synthetic scenarios, 720 inputs.
- [`results/sdk_run_summary.json`](results/sdk_run_summary.json) and [`results/graph_registry.csv`](results/graph_registry.csv): actual original-SDK execution and complete formulas.
- [`results/calibrated_samples.csv`](results/calibrated_samples.csv): both models' corrected outputs, sensitivities, margins, uncertainty and decisions.
- [`results/calibration_surface.csv`](results/calibration_surface.csv): actual paceval calculations on the 2-D input grid.
- [`results/governance_scores.csv`](results/governance_scores.csv): 16 different executed score formulas for both versions.
- [`results/formula_version_manifest.json`](results/formula_version_manifest.json): documented, unsigned mathematical-version checksums and input provenance.
- [`results/independent_80digit_audit.json`](results/independent_80digit_audit.json): independent high-precision examination.
- [`results/large_capacity/`](results/large_capacity/): capacity execution, graph registry and independent audit.
- [`figures/`](figures/): new standalone title image and 12 reproducible research figures, each also available as vector PDF.
- [`paceval_Industrial_Piecewise_Calibration_Whitepaper_EN.pdf`](paceval_Industrial_Piecewise_Calibration_Whitepaper_EN.pdf): detailed English scientific report.

The measured graphical and numerical content comes from **real paceval outputs** recorded during the run. The title image is a conceptual, generated editorial illustration, not experimental apparatus.

## Scientific boundaries

This is a **software and mathematical feasibility study using only synthetic data**. It has no instrument uncertainty budget, traceable calibration chain, accredited calibration lab, independent metrology sign-off, real process transmitter data, safety validation or field deployment. Uncertainty is demonstrated symbolically and numerically under explicitly simplified assumptions, not certified. TINC was not invoked and no verified interval enclosures are claimed. Hardware execution and acceleration remain a future architecture direction; no speedup is assumed or reported.

In particular, NIST describes traceability as a documented unbroken calibration chain with associated uncertainties. IEC 61298-2:2026 applies to specified reference-condition performance tests for process instrumentation and excludes process measurement transmitters, which fall under the IEC 62828 family. The standards are relevant *context*, not a declaration of this project's compliance.

## Research sources

1. paceval Mathematical Engine API 4.25: https://paceval.com/api/
2. NIST metrological traceability: https://www.nist.gov/metrology/metrological-traceability
3. IEC 61298-2:2026 scope: https://webstore.iec.ch/en/publication/87417
4. ISO/IEC 17025 laboratory competence: https://www.iso.org/standard/66912.html
5. SciPy PCHIP shape-preserving interpolation (potential future model, not implemented in this demonstration): https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.PchipInterpolator.html
6. OPC UA Companion Specifications for industrial model interoperability: https://opcfoundation.org/about/opc-technologies/opc-ua/ua-companion-specifications/
7. NIST Technical Note 1297 (uncertainty framework): https://www.nist.gov/pml/nist-technical-note-1297

**Research conclusion:** formula-based piecewise calibration, explicit model revisions, combined domain-compensation mathematics and auditable synthetic-quality margins are executable with the original paceval C++ API. Industrial calibration suitability remains an open experimental question, not a result of this synthetic study.
