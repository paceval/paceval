# Industrial Edge Neural Formula Execution with paceval

**An executed C++ research demonstrator for converting trained neural networks into reusable mathematical execution graphs.**

![Industrial edge neural formula execution](figures/00_edge_neural_formula_hero.png)

This project investigates a practical software architecture for non-safety-critical industrial condition monitoring. A small neural network is trained on synthetic bearing-related sensor features, its frozen weights are converted into mathematical expressions, and the original **paceval Mathematical Engine** executes these expressions together with feature normalization, operating-point corrections, decision margins and advisory scores.

The primary question is **functional feasibility and mathematical equivalence**, not CPU inference speed. An eventual FPGA or ASIC implementation is a separate hardware development path and has not been evaluated in this demonstrator.

[**Read the complete scientific whitepaper (PDF)**](paceval_Industrial_Edge_Neural_Formula_Research_Expanded_EN.pdf)

## What is actually implemented

The reproducible project trains two versions of an **8-8-4-1** fully connected sigmoid network using a controlled synthetic data generator. All network parameters are frozen, exported with sufficient decimal precision to round-trip binary64 values, and tracked in a model manifest. The data comprise 48 independent virtual bearing identities and 1,536 feature vectors. Training, validation, held-out testing and shifted-operating-condition groups do not share virtual bearing identities.

Two complementary representations of each trained network run through the real paceval API. In the *layered* representation, each neuron is an independent persistent computation object and intermediate values are passed between layers. In the *fully expanded* representation, the complete network output is exported as one mathematical expression. The latter is useful as a correctness and representation experiment, but not assumed to be the generally preferable export strategy.

The project also implements a small executable `RecordFormula`-style operator tracer inspired by the original Julia/Flux research. It records scalar operators and constructs intermediate-variable expressions at layer boundaries. This Python experiment is **not** a general Julia/Flux converter and not an ONNX importer.

The application includes eight shared feature-normalization graphs, 28 neural-network graphs across two versions (including two flattened alternatives), and 24 versioned downstream mathematical graphs. The C++ host is responsible for input validation, lifecycle and graph selection, output recording and discrete `MONITOR`, `REVIEW` or `ADVISE_INSPECTION` decisions. It does not train the network or replace industrial signal acquisition, safety logic or established maintenance workflows.

## Verified mathematical execution

The execution evidence below comes from running the compiled C++ application with the original Linux paceval shared library supplied separately for the experiment.

| Functional evidence | Verified value |
| --- | ---: |
| Persistent paceval computation graphs | **60** |
| Frozen trained network versions | **2** |
| Synthetic feature vectors | **1,536** |
| Virtual bearing groups | **48** |
| paceval multi-graph batch calls | **148** |
| Actual graph outputs | **117,897** |
| Independent 80-decimal-digit result checks | **2,286** |
| Maximum observed network error vs 80-digit reference | **1.45 × 10^-15** |
| Threshold disagreements in independently audited samples | **0** |
| Operator-trace test for both network revisions | **PASS** |

The original SDK performs computation creation and actual numerical evaluation. Both layer-wise and flattened network representations agree with an independently implemented C++ forward pass within documented numerical tolerances. Additional independent Python checks use 80-decimal-digit arithmetic. These finite-sample comparisons **do not establish a global numerical error bound** or a certified Trusted Interval Computation result.

The network classification plots use only synthetic labels. They establish no capability to identify real bearing defects or to provide calibrated failure probabilities.

## Scientific figures

The figures are generated from the C++ result files and independent mathematical checks. The conceptual hero image and pipeline schematic are illustrations; their roles are stated in the whitepaper.

| Focus | Figure |
| --- | --- |
| Complete functional pipeline | [01 Pipeline architecture](figures/01_pipeline_architecture.png) |
| Synthetic held-out and shifted operating groups | [02 Synthetic model behavior](figures/02_generalization_and_false_alerts.png) |
| Score distributions | [03 Score distributions](figures/03_synthetic_score_distributions.png) |
| Revision and frozen-weight comparison | [04 Model revision](figures/04_version_revision_scatter.png) |
| Input-shift mathematical descriptor | [05 Shift descriptor](figures/05_normalized_feature_shift.png) |
| Executed mathematical functionality | [06 paceval graph inventory](figures/06_paceval_graph_coverage.png) |
| Fully expanded vs intermediate-variable formulas | [07 Formula representation](figures/07_formula_export_size.png) |
| Versioned advisory categories | [08 Advisory outcomes](figures/08_advisory_outcomes.png) |
| Signed decision margins | [09 Threshold-margin surface](figures/09_threshold_margin_surface_3d.png) |
| Reference agreement | [10 Neural output parity](figures/10_executed_reference_overlay.png) |
| Composite mathematical rule | [11 Advisory index](figures/11_paceval_composite_advisory_score.png) |
| Operating-point correction | [12 3D rule surface](figures/12_operating_point_surface_3d.png) |

## Build and reproduce

Prerequisites are Linux x86-64, a C++17 compiler, CMake, and a locally available compatible `libpaceval_linux_sharedLIB.so`. The paceval runtime is **not** included in this public package. The provided `paceval_main.cpp` and `paceval_main.h` preserve the original paceval copyright and license notices. Set the path of the separately obtained shared library when configuring the build:

```bash
cmake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j
./build/edge_neural_formula . 128
ctest --test-dir build --output-on-failure
```

The two C++ test cases check the SDK implementation with different batch sizes. Where Python 3 is installed, the CTest suite additionally checks high-precision numerical parity and the `RecordFormula` operator trace. The independent audit scripts rely only on Python's standard library:

```bash
python3 src/verify_independent.py
python3 src/trace_neural_formulas.py
```

To regenerate the plots and the PDF report, install Python 3 with `numpy`, `pandas`, `matplotlib`, `Pillow` and `reportlab`, then run:

```bash
python3 src/make_figures.py
python3 src/make_whitepaper.py
```

To regenerate the synthetic training data and both frozen model revisions from the fixed seed, use `python3 src/train_and_export.py` before rebuilding and rerunning the SDK test. Do not regenerate the dataset after the C++ run without rerunning the application and the audits.

## Key files and provenance

The `examples/` folder contains the synthetic feature vectors, training-fold normalization, frozen model weights and a manifest with hashes and source details. `results/` contains the executed graph registry, mathematical execution inventory, feature-level inference results, model revision data, decision surfaces and independent numerical audit. `src/` includes the training exporter, the C++ application and original SDK bindings, the scalar operator tracer, the independent high-precision reference, and reproduction scripts.

This demonstration is grounded in two user-provided research papers: *Conversion of neural networks to closed-form expressions as human-readable mathematical functions* and *From Neural Networks to Reusable Mathematical Execution Graphs*. The original formula extraction work and examples are available in the [paceval artificial intelligence repository](https://github.com/paceval/paceval/tree/main/paceval%20and%20artificial%20intelligence). For the underlying execution API, see the [paceval documentation](https://paceval.com/api/).

The industrial application context is motivated by the [Paderborn Bearing DataCenter](https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter), whose physical-bearing recordings are **not** contained in this project. The published dataset has non-commercial usage restrictions that require separate review before any commercial application.

## Research status and extensions

**Demonstrated:** training and freezing compact synthetic neural models; explicit and traced formula generation; original paceval graph construction, scalar evaluation and multi-graph batch evaluation; two parallel model versions; independent numerical equivalence; separate mathematical postprocessing; recorded results and reproduction instructions.

**Still to validate:** real-bearing condition-monitoring quality; a production-grade generic converter for additional trained-network operators; real sensor and gateway integration; an engineering-approved model-update workflow; and any hardware implementation. Mathematical representation alone does not make a neural model causally interpretable, calibrated or safe for automated machinery control.

A useful follow-up is to train a similarly compact model on appropriately licensed real industrial data, independently verify the resulting mathematical export and validate the complete monitoring logic on bearing-disjoint and operating-condition-disjoint test sets. A dedicated FPGA or ASIC execution graph implementation is a plausible future path, but its benefits are **not measured or asserted here**.

This is a scientific feasibility demonstrator, **not a certified industrial fault detector or a production safety system**.
