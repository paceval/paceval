# Independent validation and exact scope (technical audit)

The archived numerical results originate from C++17 compiled with the genuine paceval 4.25 SDK and the user-supplied compatible Linux shared library. No mock engine is used. The original 2-page research proposal is in `docs/Original_WP01_Proposal.pdf`, distinct from the new executed study.

- Ten synthetic wafer lots; each has 377 measured metrology sites, split deterministically into train and untouched held-out sites. Two fitted model families (9 and 15 basis terms) are stored side by side for each lot.
- 10,000 synthetic evaluated wafer coordinates per lot, per model version; 200,000 grid model evaluations plus 7,540 metrology-site model evaluations, each for 18 paceval graphs.
- Householder QR in C++ computes coefficients from train-only sites; an independent NumPy/LAPACK least-squares implementation verifies all archived fitted coefficients. The graph output is evaluated exclusively through original `paceval_dGetMultipleComputationsResultsExt`.
- The C++ scalar SDK API is separately checked and graph-major batch ordering is tested against known values. Every individual engine-reported cell error code is checked.
- Formula and CSV numeric conversion use `paceval_dConvertFloatToString` and `paceval_dConvertStringToFloat`, with strict lexical and range checks for imported data. The original conversion deliberately provides about fifteen significant digits; numerical audit tolerances incorporate the real serialization.
- Explicit `<= (2*sigma)` grouping is mandatory: the API's grammar may otherwise interpret multiplication differently than an unparenthesized Boolean right-hand side. Dedicated operator regression tests are part of CTest.
- Full numerical verification independently reconstructs 18 outputs per published measurement/sample row, including derivatives and Boolean policy, plus a deterministic 80-digit mpmath subset. **Archived precision differences are technical verification data, not a publication benchmark.**
- The identity of the generated synthetic truth does not confer physical calibration traceability or validity of a fab process model.
- The original source describes potential latency/economic comparisons. In accordance with the user's publication requirement, this new report focuses exclusively on functionality and feasibility; no performance comparisons appear in the public whitepaper/README.

Source assumptions: wafer diameter 300 mm, normalized radius 1, nm correction outputs, nominal temperature 25 °C, synthetic temperature variation, synthetic uncertainty and hypothetical 2σ/3.5σ quality thresholds. No real metrology data was used and no fabrication equipment was addressed.

Implementation responsibilities: paceval owns dx/dy maps, residuals, scores, guard functions, sensitivities, and Boolean decisions. The C++ host owns data generation, parsing/policies, QR, graph lifetime, aggregation and reporting; independent Python owns only the audit and graphics.
