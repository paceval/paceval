# Research design and mathematical scope

## Hypothesis

A single explicitly defined mathematical model can be expressed as reusable native paceval graphs and evaluated over a complete synthetic corner map, including upstream conductance, coupled heat-duty, constraint margins, analytic sensitivities and illustrative cleaning scores. It must pass independent numerical checks. This is a functional claim, not a runtime-performance or industrial-savings claim.

## Original proposed kernels

The two-page original WP 15 specifies `Ueff`, terminal `LMTD`, a derived `Q` and cleaning cost. It is archived under `docs/Original_WP15_Proposal.pdf`. Its numerical experiment, economic thresholds and performance comparisons were proposals, not measurements. This project uses the Master-Prompt v3.0 priority of functionality rather than performance comparison.

## Model limits and decisions

The original LMTD kernel is preserved as `v1`. The important extension is a coupled counterflow `epsilon–NTU` model `v2`, with both capacity rates explicitly known. In contrast to an ad-hoc combination of `Q_LMTD` and independently selected outlet temperatures, this coupled version satisfies an internal hot/cold energy balance by construction. Both paths are *different experiment definitions*, so do not use their difference as a numerical accuracy metric.

The cleaning scoring model assumes a constant power deficit over the chosen horizon, no cleaning downtime except the entered lump sum, an externally specified residual fouling resistance, and no subsequent fouling recurrence. The `DeltaP` observation is only a guard input; flow-dependent hydraulic pressure change is **not** generated. Terminal temperature differences for LMTD are separate declared inputs, not derived from the NTU outputs.

## Test plan and falsifiers

- Main remote graph registration and batch execution: verify 24 graphs and 49 scenarios.
- Independent high-precision check: 147 numerical readings and 98 boolean flags.
- Thermal physical monotonicity: check `Q_NTU_v2` declines as Rf increases at fixed boundary conditions.
- Cross-domain validation: positive capacity rates, Uc, area, finite inputs, temperature directions and legal CSV literals.
- Critical removable singularities: exact/equal LMTD and equal-capacity epsilon with dedicated graphs.
- TINC scope: pointwise output intervals at exact binary input values, including explicit documentation of failures.
- Local C++ SDK execution: real runtime, scalar/one-graph/multi-graph API layout and conversion tests when separately supplied compatible shared library exists.
- Domain validation and field deployment: would need experimental process measurements, calibrated fouling law and separate pressure checks. Not achieved in this study.

## Evidence boundaries

The manually transcribed remote MCP observations have limited significant decimal digits, while the independent reference uses exact binary64 input values. This is documented in JSON. The full 24×49 remote response is not archived byte-for-byte; re-running the provided C++ program with a compatible SDK library will produce a fresh complete CSV, not a silent replacement of archived remote results.
