# Research validation record

**Date:** 13 November 2026  
**Project:** Programmable Matrix Mathematics for Industrial Sensor Fusion with paceval

## Genuine original library execution

The executable was built with the original `paceval_main.cpp` and `paceval_main.h` files and an externally supplied paceval 4.25 Linux runtime library. The only adjustment to the original SDK integration file was its relative header include path.

Two **new complete SPD inversion runs** were executed. The 128 × 128 case registered 17 persistent graphs and recorded 1,108,678 genuine graph outputs. The 512 × 512 case registered 17 graphs and recorded 67,538,758 graph outputs. Every complete input matrix, lower triangular Cholesky factor and inverse was written as little-endian IEEE-754 binary64 data.

| Independent matrix check | 128 × 128 | 512 × 512 |
|---|---:|---:|
| Complete inverse entries | 16,384 | 262,144 |
| Full Cholesky reconstruction residual, original code | 1.55e-15 | 4.66e-15 |
| Full inverse identity residual, original code | 2.00e-15 | 5.00e-15 |
| Independently checked full factor and inverse using NumPy/LAPACK | PASS | PASS |
| Independent log-determinant | PASS | PASS |

This record contains numerical error values intentionally omitted from the published whitepaper and README. They are audit data, not metrological accuracy guarantees.

## Industrial workflow validation

The demonstrator ran 16 synthetic sensor situations for two distinct versioned quality formulas, totaling 32 complete scenarios. Covariance matrices were SPD, generated from full lower-triangular factors, and independently inverted. Two six-dimensional observation vectors were combined using information-form fusion. The Mahalanobis innovation used the inverse of the **sum of the sensor covariances**.

For each of the two versions, the resulting synthetic status counts were **9 ACCEPT, 3 REVIEW, 4 REJECT**. Every complete fused state, covariance diagonal, first off-diagonal covariance, Mahalanobis statistic, score, signed margin, temperature sensitivity and outcome was independently checked by NumPy. Six genuine paceval mathematical graphs were evaluated on 625 additional shared score-surface records.

The independent `mpmath` reference used 80 decimal places to examine 56 scalar results across selected full sensor-fusion scenarios. This is an independent mathematical reference check, not a claim of physically traceable uncertainty.

## Important scope distinctions

The supplied source PDF previously documented fully executed 512- and 1024-dimensional results. This package **newly re-executes 128 and 512**; it does not claim to have newly run 1024. The source PDF is background and is not redistributed here because it contains older publication-format performance comparisons that do not belong in the current functionality-only release.

No real customer measurements, production machine configuration, safety certification, hardware acceleration benchmark, certified TINC enclosure or industrial acceptance standard has been established. Model coefficients and quality limits are illustrative and synthetic.

## Reproduction

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j
./build/matrix_sensor_fusion . --n 128
./build/matrix_sensor_fusion . --n 512
OPENBLAS_NUM_THREADS=1 python3 src/verify_results.py .
ctest --test-dir build --output-on-failure
```

The original binary Linux paceval runtime is required for execution but is not included in the GitHub ZIP. All original SDK source copyright information remains in `src/paceval_main.*`.
