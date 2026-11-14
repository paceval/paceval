# WP 21 mathematical model specification

**Scientific status:** deterministic, synthetic, non-validated material. All formulas are in the original paceval graphs listed in `results/formula_manifest.csv`, except the stateful implicit heat solve and spatial extrema/aggregation in the C++ host. Every registered domain graph is actually evaluated in the main run.

## Definitions and units

- `T`, `L`, `R`, `Tair`, `TgZero`, `TgFull`, `Tlimit`: kelvin, always >0, and in the case of the input material values bounded by physically plausible synthetic ranges.
- `alpha`: irreversible degree of cure, dimensionless 0 <= alpha <= 1. Initial value 0.015.
- `Aone`, `Atwo`: inverse seconds; `Eone`, `Etwo`: J/mol; `Rg`: J/(mol K).
- `mExp`, `nExp`, `lambda`: dimensionless, with `lambda` positive to avoid a singular DiBenedetto denominator at alpha=1.
- `width`: kelvin, strictly positive logistic broadening for diffusion limiting.
- `rhoRes`: resin mass per bulk laminate volume, kg/m3; `Hc`: heat per resin mass, J/kg; `rhoCp`: effective laminate volumetric heat capacity, J/(m3 K).
- `kCond`: effective through-thickness conductivity W/(m K); `hConv`: surface thermal transfer coefficient W/(m2 K); `dz`: one tenth laminate thickness, m.
- `boundary`: 1 on either exposed face; 0 inside; missing outer finite-volume neighbors set equal to boundary node temperature.
- `pressure`, `pressureReq`: illustrative absolute-independent pressure magnitudes in bar. Their use is limited to comparison and does not model fluid or porosity mechanics.

## Kinetics

The original WP 21 defines Arrhenius coefficients `k1` and `k2`, a Kamal-Sourour autocatalytic rate, a volumetric heat source, and a conversion margin. Both V1 and V2 preserve those expressions and add mathematically useful intermediate, sensitivity and guard quantities.

V1: `rate = (k1 + k2 alpha^m) (1-alpha)^n`.

V2: `rate = V1_rate / (1+exp((Tg(alpha)-T)/width))`, where `Tg(alpha) = Tg0 + (TgFull-Tg0)*lambda*alpha/(1-(1-lambda)*alpha)`.

This is an intentionally simplified physically motivated diffusion correction. It must not be interpreted as a fitted law for an identified resin. The implemented analytical `dRate/dT` includes the logistic derivative in V2; no automatic differentiation feature of the SDK is claimed.

## One-dimensional energy balance

For each node, paceval calculates local conduction, surface convection, reaction heat, effective thermal coefficients and an explicit temperature-rate diagnostic. The host advances the 10 thermal states using an implicit Euler tridiagonal linear system constructed from *paceval-returned* coefficients and heat forcing. The host advances alpha explicitly with the paceval rate and projects the state into [0,1] for numeric safety.

The discretized heat equation is not a validated 3D anisotropic laminate model. In particular, the tooling, porosity, tool contact resistance and nonuniform autoclave air velocity are not represented.

## Synthetic material constants

| Property | Synthetic value |
|---|---:|
| Effective transverse conductivity | 0.48 W/(m K) |
| Laminate volumetric heat capacity | 1.64e6 J/(m3 K) |
| Resin mass per bulk volume | 610 kg/m3 |
| Specific resin reaction heat | 250,000 J/kg |
| A1, A2 | 10,000 and 45,000 1/s |
| E1, E2 | 65,000 and 63,500 J/mol |
| Reaction exponents m and n | 1.0 and 1.35 |
| Uncured and final glass transition | 260.15 and 455.15 K |
| DiBenedetto lambda | 0.68 |
| Diffusion transition width | 9.5 K |
| Initial temperature | 298.15 K |
| Initial degree of cure | 0.015 |
| Time step / duration | 15 s / 210 min |
| Temperature cooling slope | 2.3 °C/min |

All properties are experimental **assumptions**, not sourced numerical measurements. The input domain is validated before numerical processing. Temperature and conversion are checked after every update. No parameter fitting, measured time series, or actual commercial solvent/resin datasets are claimed.

## Sign and threshold conventions

For end-of-cycle evaluation, a nonnegative margin indicates that the designated constraint is met:

- `alpha_min - alphaReq >= 0`
- `Tlimit - peak_temperature >= 0`
- `gradientLimit - peak_gradient >= 0`
- `pressure - pressureReq >= 0`

The illustrative cutoffs are 0.88 conversion, 196 °C peak, 32 K spread, and 3.5 bar. An equality at the threshold is accepted. The C++ host selects spatial minima/maxima, paceval calculates signed margins and the composite Boolean gate, and C++ emits the final screen. These are not manufacturing release criteria.

## Numerical method limitations

The heat step uses first-order implicit Euler; chemical conversion uses first-order explicit forward Euler with projection. No time-step or spatial-grid convergence proof is claimed. The independent tests verify kinetics, sensitivity, enthalpy, thermal coefficients, reference endpoints and recorded monotonicity. The high-precision formula verifier evaluates 90-digit mpmath expressions from printed inputs with matching decimal representations; the complete state trajectory is not independently integrated with 90-digit precision.
