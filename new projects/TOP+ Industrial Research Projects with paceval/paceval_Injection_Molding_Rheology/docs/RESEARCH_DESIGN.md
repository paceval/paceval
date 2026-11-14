# Scope, evidence and independently falsifiable criteria

Use case: programmable mathematical screening of injection molding gate/runner pressure loss, viscosity and operating constraints. The main graph chain is deterministic and calibrated only to declared synthetic inputs.

Primary criteria: both v1 and v2 graph paths execute; input/schema/operator checks pass; endpoint calculations agree independently with 90-digit reference within max(1e-8 absolute, 2e-11 relative); Newtonian n=1 limit agrees with the independent Hagen-Poiseuille expression; each logical result uses >=0 with boundary semantics; pressure reduces with T at fixed geometry and n when E>0; pressure increases monotonically with positive Q; cross-viscosity is finite; pointwise TINC inclusion should hold for displayed sample bounds; no local-ABI test claim without runtime.

Model differences: v1 is the original Newtonian pipe formula evaluated with apparent power-law viscosity at Newtonian nominal wall shear. v2 uses the corrected analytical constant-temperature power-law pipe pressure for circular laminar flow. Both models are mathematically different; neither solves the real cavity filling PDE. The Cross-Arrhenius diagnostic is separate from v1/v2 and not a real material-fitted Cross-WLF database record.

Scientific/engineering sources are in README and whitepaper; original WP20 (2026-11-13) is preserved as a proposal, not prior evidence of execution.
