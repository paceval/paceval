# Scientific scope and model assumptions

## Compressor thermodynamics

The stage equation $T_2=T_1(P_2/P_1)^a$ with $a=(\gamma-1)/(\gamma\eta_p)$ is a **screening approximation** of ideal-gas polytropic compression. A single fixed $\gamma=1.405$, $c_p=14300$ J/kg/K and $c_v=10176$ J/kg/K is assumed in the synthetic dataset. The V2 efficiency modification is hypothetical. No measured manufacturer characteristic is used. No compressor mechanical losses, pressure drops, leakage, variable $c_p$, dynamic efficiency maps or non-ideal gas properties are represented.

The same total pressure ratio is distributed over one, two, three or four stages. Each stage uses a synthetic intercooler effectiveness, and cumulative stage power and cooling loads are summed using genuine paceval expressions. All reported work is thermal/enthalpy-related screening work, not a certified installed electrical motor power requirement.

## Rigid storage model

The single-zone storage model uses $M c_v dT/dt=\dot{m}(c_pT_{fill}-c_v T)-UA(T-T_{amb})$ and $P=MRT/V$. It has an explicit-Euler four-second integration interval, ideal-gas pressure, constant properties and fixed-volume storage. It ignores spatial heat transfer, non-ideal hydrogen compressibility, orifice/valve effects, vessel material and polymer liner conductivity, stress analysis, fatigue, emergency venting and flow distribution. Reproducing this equation with 80-digit arithmetic does not make it a physically validated high-pressure vessel design model.

The synthetic storage trajectory continues mathematically after crossing a screening threshold to show the whole model envelope. A real plant controller or protective shutdown would need a separately assessed and certified design. This is an important distinction for interpretation of red screening bands.

## Current evidence and additional work

The DOE describes hydrogen compressor categories and industrial context. NIST's reference-state framework and experiments show that proper high-pressure calculations require a real-gas equation of state, so the ideal-gas pressure is an intentionally bounded research surrogate. Contemporary filling literature demonstrates non-uniform vessel temperatures and complex cooling behavior. ISO 19880-1:2020 is a relevant standard for gaseous hydrogen fueling stations, **not** evidence of compliance by this demonstration.

Next work should use independently licensed hydrogen property reference tables with realistic $c_p(T,p)$, $Z(T,p)$ and enthalpy, measured stage-efficiency data, and a spatially distributed storage model validated against real temperature and pressure traces. All new functions should be incorporated as actual paceval graph kernels where feasible, with host-owned physical solvers and safety governance documented separately.
