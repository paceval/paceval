# paceval Research Hypothesis Testing

![paceval hypothesis-testing research overview](figures/00_hypothesis_testing_hero.png)

**Generate · Evaluate · Validate** — a reproducible C++ research demonstrator for batch evaluation of generated mathematical hypotheses with [paceval](https://paceval.com/). Its emphasis is **scientific feasibility, reusable mathematical execution graphs and independent numerical validation**, not execution-speed claims.

[**Read the full scientific whitepaper (PDF)**](paceval_Hypothesis_Testing_Whitepaper_EN.pdf)

## Verified research result

The tested program generated **10,000 distinct coefficient-bound hypotheses** drawn from **eight mathematical structural families**. It constructed **eight reusable paceval execution graphs** (plus one interval-enabled graph), evaluated candidate predictions against a frozen synthetic training dataset, shortlisted the 100 lowest-training-error candidates, selected one candidate using separate validation data, then evaluated it on untouched held-out and extrapolation partitions. The deliberately planted reference hypothesis was recovered (`candidate_id=0`). This is a controlled proof of the hypothesis-evaluation workflow, **not a claim of novel scientific-law discovery**.

| Measured output / check | Reproduced result |
|---|---:|
| Candidate hypotheses evaluated | **10,000** |
| Reused paceval mathematical graph families | **8** |
| Training / validation / test / extrapolation observations | **120 / 60 / 60 / 48** |
| Training-based shortlist | **100** |
| Native C++ numerical spot checks | **10,818 / 10,818** within tolerance |
| Independently checked 110-digit hypothesis samples | **144 / 144** within tolerance |
| Independently checked selected-model predictions | **288 / 288** within tolerance |
| Pointwise TINC reference containment samples | **24 / 24** |
| Compiler / integration tests | **GCC 14.2 and Clang (3/3 CTest cases each)** |
| Sanitizer testing | **AddressSanitizer / UndefinedBehaviorSanitizer (3/3)** |

These counts are linked to [the experiment summary](examples/validation.json), [the independent audit](examples/high_precision_audit.json), [the candidate records](examples/hypotheses.csv) and [the sampled mathematical reference values](examples/audit_samples.csv). The numerical tolerances are documented in [the C++ implementation](src/hypothesis_test.cpp).

## Why this is useful in research

A symbolic-regression, AI-agent or hypothesis-generation method may propose thousands of explicit mathematical functions. paceval provides an execution layer for repeated numerical evaluation of **approved expression structures and new parameter values**. In this experiment the reusable graphs are prepared once, and the C++ program is responsible for candidate generation, scoring, statistical separation of data, selection and reporting.

The candidate generator is **deterministic, not an LLM or an autonomous discovery system**. This strict separation makes the mathematical kernel independently reproducible and leaves an integration boundary for future PySR, SINDy, or LLM-generated candidates. See the [architecture diagram](figures/01_execution_architecture.png).

### Exact model families evaluated

The engine is initialized with the variable declaration `x a b c d` for every mathematical family. The same graph is reused for many different coefficient values; **10,000 generated hypotheses are not 10,000 separate paceval computation objects**.

| Family | Formula |
|---:|---|
| 0 | `a*sin(b*x)+c*x*x+d` |
| 1 | `a*cos(b*x)+c*x*x+d` |
| 2 | `a*tanh(b*x)+c*x*x+d` |
| 3 | `a*exp(-b*x*x)+c*x*x+d` |
| 4 | `a*sin(b*x)+c*x+d` |
| 5 | `a*cos(b*x)+c*x+d` |
| 6 | `a*sin(b*x)+c*x*x+d*cos(x)` |
| 7 | `a*ln(1+b*x*x)+c*x*x+d` |

The planted synthetic truth is `1.4*sin(1.8*x)+0.3*x*x+0.12`, with deterministic additive pseudo-noise. All variables are dimensionless in this synthetic experiment. Other actual scientific models require domain-appropriate units, data provenance, uncertainty models and independent external validation.

### Correct model-selection procedure

1. **Training only:** compute mean squared error for all 10,000 candidates, using batched paceval evaluations; keep the best 100.
2. **Validation only:** evaluate those 100 candidates on a separate dataset; select the minimum validation-MSE candidate (deterministic tie-break rules).
3. **Held-out test:** after selection is frozen, evaluate the single winner on the unseen test set.
4. **Extrapolation:** separately evaluate the same winner outside the training domain, without using those samples to choose it.
5. **Independent auditing:** compare stored numerical results with native C++ and an external 110-digit `mpmath` implementation. Check the TINC outputs against the high-precision reference point by point.

See the [candidate landscape](figures/03_candidate_screening.png), [train–validation selection](figures/04_training_validation_selection.png), [selected fitted curve](figures/02_selected_hypothesis_fit.png) and [partition metrics](figures/05_heldout_and_extrapolation.png).

## Repository contents

```text
paceval_Hypothesis_Testing/
├── README.md
├── paceval_Hypothesis_Testing_Whitepaper_EN.pdf
├── .gitignore
├── src/
│   ├── CMakeLists.txt
│   ├── hypothesis_test.cpp
│   ├── paceval_main.h
│   ├── paceval_main.cpp
│   ├── high_precision_reference.py
│   └── make_figures.py
├── examples/
│   ├── dataset.csv
│   ├── hypotheses.csv
│   ├── shortlist.csv
│   ├── selected_predictions.csv
│   ├── audit_samples.csv
│   ├── tinc_samples.csv
│   ├── validation.json
│   └── high_precision_audit.json
└── figures/
    ├── 00_hypothesis_testing_hero.png
    ├── 01_execution_architecture.png
    ├── 02_selected_hypothesis_fit.png
    ├── 03_candidate_screening.png
    ├── 04_training_validation_selection.png
    ├── 05_heldout_and_extrapolation.png
    ├── 06_high_precision_audit.png
    ├── 07_tinc_sample_intervals.png
    └── matching SVG sources for Figures 01–07
```

## Build and run on Linux

The official [paceval C/C++ API](https://paceval.com/api/) forwarding sources `paceval_main.h` and `paceval_main.cpp` are included in `src/`. The **original compatible Linux runtime library is an external build dependency**; it is not redistributed in this repository. The following command assumes a valid path on your own machine.

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \
  -DPACEVAL_RUNTIME=/absolute/path/libpaceval_linux_sharedLIB.so
cmake --build build -j
ctest --test-dir build --output-on-failure

# Reproduce the full published study:
./build/hypothesis_test --candidates 10000 --batch 256 --output reproduced
python3 src/high_precision_reference.py reproduced
```

Python dependency for independent high precision: `python3 -m pip install mpmath`. To regenerate the research charts additionally install `numpy matplotlib` and run:

```bash
python3 src/make_figures.py --examples reproduced --out regenerated_figures
```

Change the batch size without changing the hypothesis definitions or selections:

```bash
./build/hypothesis_test --candidates 10000 --batch 37 --output reproduced_batch37
```

The demonstrated CLI bounds (`--candidates` up to 100,000 and `--batch` up to 4,096) are **application-level resource rules in this reference program**, not fixed capabilities or limitations of the paceval engine.

This reference configuration was tested with **Debian GNU/Linux 13 (x86_64)**, **GCC 14.2**, **Clang**, an **Intel Xeon Platinum 8573C environment exposing five logical CPUs**, the official paceval 4.25 C/C++ API forwarding files, and the supplied original Linux library. These are reproducibility details, **not timing claims**. The tests were also run with AddressSanitizer/UndefinedBehaviorSanitizer.

## Numerical audit and TINC

- Every 113th prediction is sampled for comparison against the independently coded C++ formula evaluator, yielding 10,818 numerical spot checks in the full run.
- The high-precision script checks [144 separately sampled graph outputs](examples/audit_samples.csv), [all 288 selected-model predictions](examples/selected_predictions.csv), and the integrity of the training shortlist / validation decision.
- [The TINC figure](figures/07_tinc_sample_intervals.png) shows the 24 evaluated output intervals. The independent audit checks actual inclusion of the high-precision value for each sample. This is a finite-sample observation, not a universal interval guarantee.

[View the numerical accuracy chart](figures/06_high_precision_audit.png).

## Research scope and interpretation

This is a **completed local feasibility experiment** on a disclosed synthetic family of one-dimensional analytic expressions. A known target hypothesis is intentionally injected into the candidate set. The experiment establishes the tested software integration, reproducibility, separation of data partitions and numerical agreement, but does not infer a new physical law, benchmark a real LLM, run a SINDy or PySR search, or establish real-world predictive validity.

A future extension can consume approved expressions from existing symbolic-regression packages, evaluate independent scientific datasets with fixed data splits, and study more varied candidate structures. Graph reuse is particularly relevant when many candidate hypotheses share a mathematical form but differ in numerical coefficients.

## Background literature and official interfaces

- [Brunton, Proctor & Kutz (2016), *Discovering governing equations from data by sparse identification of nonlinear dynamical systems*](https://doi.org/10.1073/pnas.1517384113).
- [PySR / SymbolicRegression.jl documentation](https://pysr.ai/) — independent hypothesis generation and symbolic-regression context.
- [COCO benchmark methodology](https://coco-platform.org/) — fixed experimental setups and reproducibility principles.
- [paceval Mathematical Engine C/C++ API](https://paceval.com/api/) — computation objects and batch evaluation.

The [whitepaper](paceval_Hypothesis_Testing_Whitepaper_EN.pdf) describes the tested scope, formula families, selection protocol and independent checks in detail. No execution-speed comparison or performance advantage is asserted.
