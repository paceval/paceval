# Collider Research with paceval

![paceval Collider Research: mathematically defined collider-analysis kernels, reusable graphs and validation](figures/00_collider_research_hero.png)

*Conceptual illustration of high-energy physics analysis; it does not depict an actual measured CERN collision event.*

**A validated C++ feasibility demonstrator for reusable mathematical execution in collider-inspired analysis.**  
**Executed with the original paceval Linux library | 10 November 2026**

This repository demonstrates that selected **classical mathematical kernels relevant to collider analysis can be implemented, repeatedly executed and independently checked using paceval**. It contains the real C++ integration, input fixtures, independent numerical checks, four technical figures and one scientific white paper. The demonstrator uses **synthetic events**, not CERN collision measurements or detector calibrations.

**[Scientific white paper (PDF)](paceval_Collider_Research_Whitepaper_EN.pdf)**

## Successfully implemented with paceval

The C++ program creates **four persistent calculation graphs and two additional TINC-enabled graphs** using the original paceval shared runtime.

| Graph | Implemented computation | Verification |
|:--|:--|:--|
| G1 | Direct squared invariant mass for two massless particles | Native C++ reference and numerical edge cases |
| G2 | Algebraically equivalent, numerically stable squared invariant mass | Native and independent high-precision reference |
| G3 | Synthetic parametrized event weight | Native C++ reference and five parameter variations |
| G4 | Fused stable mass squared multiplied by the event weight | Native result and direct graph agreement |
| T1, T2 | TINC-enabled graphs for both mass formulations | Independently checked interval samples |

The evaluated massless-particle expressions, with transverse momenta in GeV, are:

```text
m²_direct = 2 * pt1 * pt2 * (cosh(deta) - cos(dphi))
m²_stable = 4 * pt1 * pt2 * (sinh(deta/2)^2 + sin(dphi/2)^2)
```

The synthetic parameterized weight, **not an experimentally calibrated correction**, is:

```text
W = (1 + a*exp(-abs(deta))*cos(dphi)
       + b*ln(1+pt1/100)
       + c*sin(pt2/30)^2)
    * (1 + d*tanh((pt1+pt2-100)/60))
```

The same graph G3 is reused for five parameter settings. The program also exercises single-graph batch evaluation, **simultaneous evaluation of three distinct graphs**, and the combined formula G4. The natural logarithm is written `ln(...)` in the paceval expression syntax.

![Real paceval calculation paths: reusable graphs, batched events, parameter variations and TINC](figures/02_graph_reuse.png)

### Actual paceval interfaces exercised

The implementation calls `pacevalLibrary_Initialize`, `pacevalLibrary_CreateComputation`, `pacevalLibrary_dGetComputationResultExt`, `pacevalLibrary_dGetMultipleComputationsResultsExt`, `pacevalLibrary_dGetComputationResult` (for TINC), error/status interfaces, `pacevalLibrary_DeleteComputation`, and `pacevalLibrary_Free`. All calls are made through the supplied real shared library, loaded with `dlopen` on Linux. The [complete implementation](src/collider.cpp) contains the function signatures and input packing.

## Scientific validation

The test program independently evaluates the same mathematics in native C++ and checks the paceval results. For near-collinear particle directions, the direct mass formula can lose meaningful digits through subtraction. The alternative form avoids that particular cancellation. This is a mathematical property of the expression; paceval allows **both** forms to be managed and evaluated consistently as reusable graphs.

![Kinematic setting for the two-particle invariant mass](figures/01_kinematics.png)

![Independent 110-digit numerical reference: direct and stable mass expressions](figures/03_precision.png)

The [high-precision reference script](src/high_precision_reference.py) uses `mpmath` at **110 decimal digits** and checks 14 angle cases from `10^-2` to `10^-15`. It also tests interval containment for the 24 sample outputs in [examples/tinc_samples.csv](examples/tinc_samples.csv). All **24 of 24** sampled TINC intervals enclosed the independently computed reference values in the recorded real-runtime test.

![Numerical TINC interval diagnostics from the original paceval library](figures/04_tinc.png)

These sampled inclusion checks demonstrate the behavior of the supplied runtime for the selected inputs. They do **not** constitute a universal mathematical proof of rigorous TINC enclosure. The [retained high-precision edge-case values](examples/high_precision_reference.csv) support the precision figure. For source-level reproducibility, the C++ application generates its own deterministic test events (seed `20261110`) or reads externally supplied event kinematics from CSV.

## Build and reproduce (Linux x86-64)

Prerequisites: CMake 3.12+, GCC or Clang with C++17, and a **separately supplied compatible original paceval Linux shared library**. The proprietary library is **not included** in this GitHub package. ROOT is not required for the enclosed examples. The source CMake file lives in [`src/CMakeLists.txt`](src/CMakeLists.txt).

From the repository root:

```bash
export PACEVAL_LIB=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$PACEVAL_LIB"
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

When an absolute `PACEVAL_RUNTIME` is provided, CTest includes a real-runtime integration test in addition to the native mathematical self-test. Without a library, the native self-test remains available, but paceval integration cannot be exercised.

**Run using supplied example events:**

```bash
mkdir -p out
./build/collider --library "$PACEVAL_LIB" --require-paceval \
  --input-csv examples/example_events.csv --batch 16 \
  --csv out/example_validation.csv
```

**Run a larger deterministic synthetic set:**

```bash
./build/collider --library "$PACEVAL_LIB" --require-paceval \
  --events 120000 --batch 16384 --csv out/synthetic_validation.csv
```

The event fixture uses `pt1,pt2,deta,dphi` plus optional parameters `a,b,c,d`. Both [four-column](examples/example_4col.csv) and [eight-column](examples/example_events.csv) formats are provided. Transverse momenta are expressed in GeV and the angular differences in radians. The command also writes `out/tinc_samples.csv`, which can be audited with:

```bash
python3 -m pip install mpmath
python3 src/high_precision_reference.py \
  --tinc-csv out/tinc_samples.csv --strict-tinc \
  --out out/high_precision_audit.csv
```

The application continues to emit internal diagnostic information in its CSV output; this public report is specifically about **implementation feasibility and numerical verification**.

## Reproducibility and boundaries

The supplied implementation was validated with the original paceval Linux library under Debian GNU/Linux 13 (x86-64, KVM-virtualized AMD EPYC 9V74) using GCC 14.2 and Clang 17. The verification exercise used a sequential C++ process and externally loaded library. Matching the original vendor library can be checked with SHA-256:

```text
acf63a87df0ee822b467edbca887393d31ec0ea03562e1abf802d2512a5bfb12
```

The C++ demonstrator is **not** a replacement for ROOT, CMS reconstruction, particle tracking or detector simulation. Its verified result is an optional mathematical execution component suitable for evaluating explicitly defined scalar formulas and validation probes. Incorporating a physics-approved correction function and real open collider data would be a separate follow-up study.

## Repository contents

```text
README.md                                    Project overview and documentation
paceval_Collider_Research_Whitepaper_EN.pdf  Scientific feasibility white paper
src/CMakeLists.txt                           CMake build and CTest integration
src/collider.cpp                             Full C++ source and real paceval API usage
src/high_precision_reference.py             Independent 110-digit numerical checks
examples/example_4col.csv                   Minimal external event input
examples/example_events.csv                 Parametrized external event input
examples/tinc_samples.csv                   Original paceval interval sample output
examples/high_precision_reference.csv       Independent reference values
figures/                                     One README hero and four scientific diagrams
.gitignore                                   Local build/output exclusions
```

Scientific context: [paceval API](https://paceval.com/api/) · [CERN Open Data](https://opendata.cern.ch/) · [ROOT](https://root.cern.ch/). This independent demonstrator does not imply a CERN or CMS collaboration.
