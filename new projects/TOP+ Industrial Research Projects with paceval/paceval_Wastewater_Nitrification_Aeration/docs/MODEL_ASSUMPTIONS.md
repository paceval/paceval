# Scientific model, scope, and units

The original WP18 proposes four simple equations, and presents its million-case scale and benchmarks as **plans**, not measurements. This project keeps the Monod-type potential nitrification rate and adds a distinct temperature/substrate-inhibition variant for comparative study.

Version v1: potential nitrification rate is `muN/YN * Xn * NH4/(KN+NH4) * DO/(KO+DO)` [mg N/L/h]. Version v2 multiplies by `theta^(Temp-Tref)` and replaces the substrate saturation term with `NH4/(KN+NH4+NH4^2/KI)`. The inhibition term is an illustrative model assumption; its coefficients are synthetic. Both model versions evaluate concurrently as persistent paceval graphs.

The actual one-residence-time effective removal rate is `min(potential rate, NH4/tau)` so removal cannot exceed the available nitrogen in a fixed-input screening snapshot; this is *not* a dynamic reactor mass balance with inflows, effluent flows, recirculation, and time-varying biology. The estimated NH4 outlet is NH4 - tau * effective rate. Potential growth rate and effective capped rate must not be confused. The analytical partial derivative with respect to DO is valid for the **uncapped potential v2 rate** only, and is not an automatic derivative computed by paceval.

OUR = aN * effective_rate + bX * Xn [mg O2/L/h]. The chosen aN=4.57 is the theoretical full-oxidation O2/N ratio; the extra biomass respiration term is intentionally stylized. OTR = KL*(DOsat-DO) [mg O2/L/h]. The reported power is `OUR*Vol/(1000*alphaO2)` [kW], where 1 mg/L = 1 g/m3 and alphaO2 is **kg oxygen transferred per kWh electrical**. This represents a demand-based proxy rather than actual variable-frequency-drive blower power; it is not derived from the OTR or from measured electricity.

The mathematical guard requires all: NH4out <= Nlimit, OTR >= OUR, DO >= DOmin, Power <= Pmax. It is not a discharge permit. The two model versions can disagree. Negative oxygen margin flags a simplified transfer shortfall but does not mean negative actual DO; DO is treated as an exogenous snapshot value.

The 7 x 7 grid uses NH4 from 8 to 44 mg/L and DO from 0.5 to 4.5 mg/L. The additional 12 hourly states are synthetic snapshots, **not** an integrated transient simulation or 12 measured hours. The CPP main data flow reads these same input CSV files, uses paceval conversion, performs scalar and multi-graph batch evaluation, writes a separate SDK result, and carries out native consistency checks. The compatible original library was not available for executing that local path.

Missing physics include heterotrophic substrate oxidation, alkalinity/pH inhibition, denitrification and nitrate tracking, solids residence time (SRT), nitrite pathways, N2O, chemical equilibria, diffuser air transfer, DO gradients, sensor calibration, feed disturbances and full ASM1/BSM2 mass balances. Input coefficients were not calibrated.
