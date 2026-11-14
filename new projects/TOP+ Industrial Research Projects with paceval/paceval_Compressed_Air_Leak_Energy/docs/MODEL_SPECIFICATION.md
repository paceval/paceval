# Mathematical specification and assumptions

## Physical boundary and convention

Single upstream receiver pressure $P_u$ and ambient pressure $P_a$ are both **absolute** in pascal. $T_u$ is the assumed constant absolute upstream temperature in kelvin. The effective leak discharges directly to atmospheric pressure. $A$ is a notional effective leak orifice in $\mathrm{mm}^2$ and is converted by a factor of $10^{-6}$ to $\mathrm{m}^2$ inside the real paceval graph. The reference pressure $P_{\mathrm{ref}}$ is an absolute pressure. The model does not solve transient receiver pressure or multi-node airflow networks.

## Version V1: empirical pressure law

```math
\dot m_1=\dot m_\mathrm{ref}\left(\frac{P_u-P_a}{P_\mathrm{ref}-P_a}\right)^n.
```

The reference flow is generated from a chosen *synthetic* orifice parameter set at a common pressure. The exponent $n$ is a calibrated-form assumption. It is not asserted to represent every real leak geometry or component type. The analytic derivative is

```math
\frac{\partial\dot m_1}{\partial P_u}=\frac{n\dot m_\mathrm{ref}}{P_\mathrm{ref}-P_a}\left(\frac{P_u-P_a}{P_\mathrm{ref}-P_a}\right)^{n-1}.
```

## Version V2: compressible ideal-gas orifice

The critical pressure ratio for an ideal-gas isentropic nozzle is

```math
r_c=\left(\frac{2}{\gamma+1}\right)^{\gamma/(\gamma-1)}.
```

For downstream-to-upstream ratio $r\le r_c$ the mass flow is choked:

```math
\dot m_\mathrm{choked}=C_d A\frac{P_u}{\sqrt{R T_u}}\sqrt{\gamma}\left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{2(\gamma-1)}}.
```

For $r>r_c$ the subcritical branch is

```math
\dot m_\mathrm{sub}=C_d A P_u\sqrt{\frac{2\gamma}{R T_u(\gamma-1)}\left[r^{2/\gamma}-r^{(\gamma+1)/\gamma}\right]}.
```

In the production graph, $A$ is first converted from $\mathrm{mm}^2$ to $\mathrm{m}^2$. The `AND` and relational operators of the actual paceval expression language select regimes. The host validates $P_u>P_a>0$, $T_u>0$, $1<\gamma$, $R>0$, $C_d>0$ and positive effective area before invoking the graph. **No lazy conditional evaluation is assumed.** The same domain permits both branch expressions to be evaluated safely. Near-atmosphere cases are included solely to test the subcritical formula; such pressures do not meet the sample plant minimum-pressure policy.

## Compression and operational model

The study assumes one steady-state compressor with constant overall isentropic efficiency $\eta$ and heat capacity $c_p$:

```math
\dot m_\mathrm{total}=\dot m_\mathrm{demand}+\dot m_\mathrm{leak},\quad
w=\frac{c_p T_u}{\eta}\left[\left(\frac{P_u}{P_a}\right)^{(\gamma-1)/\gamma}-1\right].
```

Electrical input is estimated as $P_\mathrm{el}=\dot m_\mathrm{total}w/1000$ in kW. The corresponding leak-allocated input is $P_\mathrm{leak}=\dot m_\mathrm{leak}w/1000$. Multiplication by assumed annual operating hours produces energy indicators, with hypothetical electricity price producing an illustrative expenditure. These indicators are **not empirical energy-saving measurements**. No variable-speed drive, staging, unloaded losses or inlet-condition changes are solved.

The downstream pressure proxy is $P_\mathrm{use}=P_u-k_d\dot m_\mathrm{total}^2$, where $k_d$ is a synthetic lumped loss coefficient with units $\mathrm{Pa}/(\mathrm{kg/s})^2$.

Four signed guard margins, each positive or zero when the modeled condition is satisfied, are

```math
M_P=P_\mathrm{use}-P_\mathrm{min},\quad
M_\mathrm{cap}=\dot m_\mathrm{capacity}-\dot m_\mathrm{total},
```

```math
M_\mathrm{leak}=f_\mathrm{max}-\frac{\dot m_\mathrm{leak}}{\dot m_\mathrm{total}},\quad
M_\mathrm{high}=P_\mathrm{max}-P_u.
```

A composite `AND` guard (0/1) combines four comparisons. It is a **mathematical screening rule**, not a safety certification. The score includes a scaled indicative leak-cost term and penalty weights on negative margins; weights are illustrative.

## Verification and traceability

`results/formula_manifest.csv` is the unedited formula register. `results/math_execution_inventory.csv` records every implemented mathematical function and its engine ownership. `src/compressed_air_main.cpp` contains a mathematically separate native C++ reference and the main graph evaluation paths. `scripts/verify_high_precision.py` contains separately derived 85-digit mpmath formulas. All public result numbers are traced to `results/execution_evidence.json` and generated CSV data.
