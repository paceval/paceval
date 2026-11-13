# Independent mathematical validation notes

- The scientific study executes 31 persistent mathematical formulas through the original paceval C++ SDK using the Multi-Graph-Batch API.
- The native C++ oracle is implemented independently and checks 22,841 selected values; the native code is not used to fabricate graph outputs.
- `src/verify_results.py` independently recomputes 1,760 selected values at 80 decimal digits with mpmath and checks 80 finite differences for analytical coefficients.
- The Python audit also checks 7,200 rotor dynamics equations from the saved time-series, exact next-state chaining, and electrical-to-mechanical torque consistency.
- The 61x61 coefficient table is independently interpolated at 576 off-grid points, producing an approximation error only with respect to the declared synthetic analytical formula.
- All stochastic processes and exogenous input are deterministic; no production sensor inputs are used.
- The smooth electrical rating applies in the shaft torque as well as the electric power formula; this is essential to the model's energy balance.
- The report is evidence for reusable mathematical expression execution, not certified turbine performance.
