# WP_043 technical validation report

The C++ program was built and run against the original, externally held paceval Linux shared library. The repository contains original SDK interface source files (`paceval_main.h`/`paceval_main.cpp`) but does not include the runtime binary.

- 86 registered expression graphs created without graph-compilation errors.
- 1,164,440 checked, finite Multi-Graph-Batch return values from the full work program.
- 23,520 native C++ oracle values independently compared during the original runtime execution.
- 3,559 independently recomputed values from actual exported CSV files checked using 80-decimal-digit mpmath.
- 57,164 complete-file physical and accounting checks passed (`result_verification.json`).
- CMake build and original runtime CTest integration test: passed (1/1).
- 7/7 tracked main outputs byte-identical in a separately executed original-SDK replay.
- 15/15 PDF pages rendered for final visual review.
- README GitHub-style local links and math block static validation passed.

**Interpretation:** all computations refer to the declared synthetic pump and parallel-pipe model. No EPANET solver, calibration against physical measurements, water-quality transport or pump certification has been performed.
