# paceval Quantum Research

![paceval Quantum Research: reliable classical mathematics for quantum experiments](figures/00_quantum_research_hero.png)

**Reliable Mathematics for Quantum Research — a successfully implemented and independently verified C++ demonstrator using the original paceval mathematical engine.**

This project demonstrates the **technical feasibility** of using reusable paceval execution graphs for explicit classical mathematics in quantum research: a synthetic **Ramsey calibration model**, its binomial likelihood and frequency derivative, and the **exact expectation value of a two-qubit quantum circuit**. The computations use the actual paceval Linux runtime and are checked against independently implemented mathematical references. The project does not claim real quantum-device measurements, a complete calibration fit, or classical simulation of arbitrary quantum circuits.

**[Scientific whitepaper: implemented and verified use cases (PDF)](paceval_Quantum_Research_Whitepaper_EN.pdf)**

## Verified implementation

| Implemented capability | Verified result |
| --- | --- |
| Reusable paceval mathematical execution | **Five graphs** created and evaluated with the original runtime |
| Combined Ramsey computation | Probability, likelihood contribution and frequency derivative evaluated using the **multi-graph API** |
| Parameter exploration | The same likelihood graph reused for **five detuning-frequency hypotheses**, in separate and flattened batches |
| Explicit quantum circuit | Two mathematically equivalent expressions validated using an independent **four-amplitude statevector** calculation |
| Numerical cross-checks | Native C++ reference calculations and derivative finite-difference tests completed successfully |
| Trusted Interval Computing (TINC) | **24 of 24 sampled point intervals** contained independently computed **110-decimal-digit reference values** |

The TINC result is a **pointwise test** for the stated inputs, not a general mathematical proof that every interval encloses the exact answer for arbitrary inputs. The conclusion is limited to implementation and validation of these selected mathematical workloads.

![Implemented paceval computation layer](figures/03_execution_graph_architecture.png)

## Use case A: Ramsey calibration mathematics

A commonly used phenomenological model for a Ramsey measurement is

$$
P(t) = \frac{1}{2}\left[1 + C e^{-t/\tau}\cos(2\pi\Delta f\,t+\phi)\right],
$$

where $t$ is delay, $C$ is contrast, $\tau$ is an effective dephasing time, $\Delta f$ is detuning frequency and $\phi$ is phase. For $k_i$ observed positive outcomes among $N_i$ trials, the implementation evaluates each binomial negative log-likelihood contribution without its parameter-independent combinatorial constant:

$$
\ell_i=-\left[k_i\ln P(t_i) + (N_i-k_i)\ln(1-P(t_i))\right].
$$

The derivative with respect to detuning frequency is also implemented and independently checked:

$$
\frac{\partial P}{\partial \Delta f}=-\pi C t e^{-t/\tau}\sin(2\pi\Delta f\,t+\phi).
$$

The demonstrator uses deterministic synthetic data (512 Bernoulli trials at each sampled delay), evaluates all three Ramsey expressions with paceval, and reuses the likelihood graph for five frequency hypotheses. **It evaluates the building blocks of a fit, but it does not perform a complete parameter-estimation fit.**

![Ramsey model and synthetic observations](figures/01_ramsey_calibration.png)

## Use case B: explicit quantum-circuit expectation value

Starting from $|00\rangle$, the specified circuit applies $R_y(\theta_1)$ and $R_y(\theta_2)$, followed by CNOT with the first qubit as control and the second as target. For the observable $I\otimes Z$, the exact result is

$$
\langle I\otimes Z\rangle = \cos\theta_1\cos\theta_2
=\frac{\cos(\theta_1-\theta_2)+\cos(\theta_1+\theta_2)}{2}.
$$

paceval evaluates **both equivalent formulas as persistent execution graphs**. A separate native C++ implementation computes the four real state amplitudes after the rotations and CNOT, then evaluates the observable independently. This shows that a **known, compact formula** arising from a quantum circuit can be reused as classical mathematical software. It does not imply that arbitrary circuits have efficient classical closed-form representations.

![Exact two-qubit expectation map](figures/02_quantum_circuit_fourier.png)

## Direct integration of the original paceval C++ SDK

The [research application](src/quantum.cpp) includes the supplied [paceval API header](src/paceval_main.h). The paired, supplied [SDK forwarding implementation](src/paceval_main.cpp) is compiled alongside the C++ research application through [src/CMakeLists.txt](src/CMakeLists.txt). That implementation links to the **actual, externally provided** `libpaceval_linux_sharedLIB.so` at build time. The SDK source files are **not** the numerical engine and the compiled `.so` is **not** included in this repository.

No handwritten `dlopen`/`dlsym` function-pointer declarations, substitute implementation, or runtime-only library CLI argument are needed. The build checks the original vendor symbols. The application calls these **typed, declared API functions**:

| Direct paceval C/C++ API | Demonstrated implementation |
| --- | --- |
| `paceval_InitializeLibrary`, `paceval_FreeLibrary` | Initialize and close the real runtime |
| `paceval_CreateComputation`, `paceval_DeleteComputation` | Prepare five reusable mathematical graphs and two additional TINC graphs; release handles with RAII |
| `paceval_dGetComputationResultExt` | Evaluate a graph for many Ramsey/circuit inputs and five frequency hypotheses |
| `paceval_dGetMultipleComputationsResultsExt` | Evaluate three Ramsey-related graphs for the same input batch |
| `paceval_dGetComputationResult` | Obtain point values and reported TINC lower/upper endpoints |
| `paceval_GetIsError`, `paceval_GetErrorInformation` | Inspect graph state and diagnostic error codes |

All seven graphs share the identical nine-variable declaration in a fixed order. Batch input data is arranged event-major and multi-graph results are graph-major. The application verifies both API status and per-element error codes, compares results to independent native expressions, and releases all computation handles before shutting down the engine. The independent [110-digit TINC checker](src/high_precision_reference.py) does **not** invoke paceval.

**Source provenance and licensing.** The `paceval_main.h` and `paceval_main.cpp` files were taken from the original supplied paceval API v4.25 sources, converted to UTF-8 while retaining copyright/AGPL notices, and adjusted only for a project-local header include (`"paceval_main.h"`). These SDK adapter files have not been reimplemented. Any public distribution must comply with the applicable **GNU AGPL** obligations, as well as any separate terms for the externally supplied runtime binary.

## Build and independently verify on Linux

Requirements: CMake **3.16+**, a Linux C++17 compiler (GCC or Clang), and an **original compatible paceval Linux shared library** supplied separately. Python 3 and third-party [`mpmath`](https://mpmath.org/) are needed only for the additional independent high-precision check.

```bash
# From the repository root; CMakeLists.txt lives in src/.
export PACEVAL_LIB=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build --output-on-failure

# Alternatively configure with the exact absolute path explicitly:
# cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \
#   -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so

# Exercise the real paceval engine with the included example data.
./build/quantum \
  --input-csv examples/ramsey_circuit_sample.csv \
  --events 120 --batch 32 --csv example_results.csv

# Validate new 24-point TINC output (written next to example_results.csv).
python3 -m pip install mpmath
python3 src/high_precision_reference.py tinc_samples.csv
```

Both tests in CTest require a real runtime at **build/link time**; there is no native-only fallback when it is missing. Test 1 verifies the native mathematical identities and test 2 exercises the original paceval SDK/library. Changing the library path requires a CMake reconfigure. The program writes CSV files with numerical results and internal timing diagnostics solely for reproducibility, **not as evidence of comparative performance**. Tests and figures in this research demonstrator use deterministic synthetic inputs, not quantum hardware measurements.

## Independently checked numerical results

The [high-precision verification script](src/high_precision_reference.py) evaluates the same mathematical expressions using 110-decimal-digit `mpmath` arithmetic. It promotes the **actual stored binary64 input values** and the graph's rounded numerical constants before comparison with the paceval interval endpoints. The independently verified real-runtime run produced **24 of 24 contained point references**, archived in [the supplied TINC sample CSV](examples/tinc_samples.csv). The script can rerun this independent check on the archived samples or new outputs generated by the C++ program.

![TINC pointwise interval examination](figures/04_tinc_validation.png)

This does not certify the general rigorous interval properties of TINC. Statistical measurement uncertainty, physical-model uncertainty and floating-point numerical uncertainty remain distinct.

## Reproducible project contents

```text
paceval_Quantum_Research/
├── README.md
├── paceval_Quantum_Research_Whitepaper_EN.pdf
├── .gitignore
├── src/
│   ├── CMakeLists.txt
│   ├── quantum.cpp
│   ├── paceval_main.h
│   ├── paceval_main.cpp
│   └── high_precision_reference.py
├── examples/
│   ├── ramsey_circuit_sample.csv
│   └── tinc_samples.csv
└── figures/
    ├── 00_quantum_research_hero.png
    ├── 01_ramsey_calibration.png
    ├── 02_quantum_circuit_fourier.png
    ├── 03_execution_graph_architecture.png
    └── 04_tinc_validation.png
```

The [CMake project](src/CMakeLists.txt), [source code](src/quantum.cpp), [original SDK header](src/paceval_main.h), [original SDK adapter source](src/paceval_main.cpp), [example input](examples/ramsey_circuit_sample.csv), [high-precision checker](src/high_precision_reference.py), [archived TINC results](examples/tinc_samples.csv), and all embedded figures are included. The original compiled paceval runtime is intentionally external; only the vendor API source adapter is included.

## Scope and scientific background

This is a **validated classical mathematical research demonstrator** for selected quantum-research workflows, not a quantum-processor or a full experimental reconstruction system. All measurements are **synthetic**. Scientific background includes [Qiskit Experiments Ramsey characterization](https://qiskit-community.github.io/qiskit-experiments/stable/0.8/manuals/characterization/t2ramsey.html) and [PennyLane's Fourier-analysis documentation](https://docs.pennylane.ai/en/stable/code/qp_fourier.html).

The demonstrated success is concrete: the original paceval library **constructed and evaluated the intended formulas**, the independent native references agreed within configured numerical tolerances, and all 24 high-precision point-containment checks passed. The implementation and numerical validation establish the stated feasibility result without relying on any claim about quantum hardware acceleration.
