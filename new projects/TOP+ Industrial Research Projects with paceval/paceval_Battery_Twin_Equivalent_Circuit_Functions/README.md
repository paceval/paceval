# Battery Twin Equivalent-Circuit Functions | paceval Research

![Concept illustration of a battery cell, equivalent circuit and parameter surfaces](figures/00_battery_twin_hero.png)

*Concept illustration; not a computed research result.*

**An independently verified, executable C++ research demonstrator using the original paceval Mathematical Engine** to evaluate parameter-dependent lithium-ion battery surrogate equations, simulate controlled 1RC/2RC model revisions, and inspect synthetic voltage, temperature and electrical-energy behavior.

**[English scientific whitepaper (PDF)](paceval_Battery_Twin_Equivalent_Circuit_Functions_Whitepaper_EN.pdf)** · **[C++ source](src/battery_twin.cpp)** · **[Mathematical execution inventory](results/math_execution_inventory.csv)** · **[Independent technical audit](results/high_precision_audit.json)**

## 1. Industrial use case and current state of the art

A battery management system (BMS) must interpret terminal voltage, current and temperature to estimate internal electrical states. A digital twin can repeatedly simulate the response of a cell during acceleration, sustained load, regenerative charging and rest. The input consists of a signed cell-current time series, ambient temperature, initial state of charge, model parameters and a declared equivalent-circuit topology. The output is a trace of predicted terminal voltage, polarization states, remaining charge and lumped cell temperature. Engineers may use these traces to assess model behavior, prepare state estimators, explore parameter sensitivities and plan experiments. This demonstrator performs **none of the safety-critical functions of a deployed BMS**.

Thevenin-style 1RC and 2RC models are established engineering surrogates. A 2025 review surveys analytical, filtering and optimization-based parameter identification for those models. A 2026 methodological paper stresses adequately designed pulses, relaxation experiments, and the use of time constants for robust parameterization. The officially documented **PyBaMM Thevenin model** supports configurable RC branches and thermal models; **MathWorks Simscape Battery** likewise provides electro-thermal equivalent-circuit blocks with temperature-, SOC- and aging-dependent parameters. These mature approaches are relevant alternatives rather than systems claimed to be replaced by paceval. Further reading: [2025 parameter-identification review](https://doi.org/10.1016/j.est.2025.115581), [2026 parameterization guide](https://pmc.ncbi.nlm.nih.gov/articles/PMC13049963/), [PyBaMM Thevenin documentation](https://docs.pybamm.org/en/latest/source/api/models/equivalent_circuit/thevenin.html), [MathWorks Simscape Battery documentation](https://www.mathworks.com/help/simscape-battery/ref/batteryequivalentcircuit.html).

A useful industry-style example is a **hypothetical 3.2 Ah cell** subjected to three scripted current schedules and three ambient temperatures. The original paceval engine evaluates reusable battery expressions for each time step; a C++ scheduler advances the states; the resulting recorded trajectories are independently reproduced. No real automotive cell chemistry or manufacturer specification is inferred from the illustrative coefficients.

## 2. Research question and verified scope

Can original paceval computation handles execute the meaningful mathematical components of a parameterized one- and two-branch battery equivalent circuit while preserving independently reproducible state transitions and explicitly versioned result semantics?

The executed experiment has **75 successfully created and exercised paceval graphs**, **18 synthetic scenarios**, **720 steps per scenario**, **724 multi-graph batch calls**, **307,949 batch graph results**, and **4,050 independently checked high-precision graph samples**. These are recorded execution counts, not claims of speed or efficiency advantages. The two versions coexist and are evaluated with unchanged graph handles. The independent reference recreates full trajectories, energy aggregates and voltage extrema.

## 3. Mathematical model and units

Discharge-positive cell current $I$ is measured in amperes, state of charge $z$ is dimensionless, temperature $T$ is in degrees Celsius, resistance in ohms, and voltage in volts. The original proposal's differential RC law is retained and extended using **frozen-coefficient exact exponential steps** over each two-second interval.

```math
\frac{dV_{p,i}}{dt}=-\frac{V_{p,i}}{\tau_i}+\frac{I R_i}{\tau_i},\quad
\tau_i=R_i C_i,
\qquad
V_{p,i}(t+\Delta t)=e^{-\Delta t/\tau_i}V_{p,i}(t)+I R_i(1-e^{-\Delta t/\tau_i}).
```

The terminal model is versioned without changing the sign convention:

```math
V_{\mathrm{term}}=V_{\mathrm{OCV}}(z,T)-I R_0(z,T)-\sum_{i=1}^{n} V_{p,i},\qquad n\in\{1,2\}.
```

The implementation uses a declared synthetic sigmoid-plus-linear open-circuit map and smooth resistance and time-constant parameter functions; see [the executable formula registry](results/formula_registry.csv) for the **exact** expressions, including all numerical constants. Capacity modification by a synthetic factor is illustrative, not an empirically fitted aging law. SOC advances by coulomb counting and a lumped temperature advances from a resistive heating **proxy** and ambient exchange.

```math
z_{k+1}=z_k-\frac{I_k\Delta t\,a}{3600 Q},\quad
T_{k+1}=T_k+\frac{\Delta t}{C_{\mathrm{th}}}\left(P_{\mathrm{heat}}-h(T_k-T_a)\right).
```

An instantaneous **algebraic electrical-power identity** is checked:

```math
I V_{\mathrm{OCV}}=I V_{\mathrm{term}}+I^2 R_0+\sum_i I V_{p,i}.
```

This identity does not prove a full electrochemical or thermal energy conservation law when parameter values vary over time. In particular, heat generated by the lumped resistance proxy does not account for all reversible entropy, electrode, pack, cooling, or aging phenomena.

## 4. Actual mathematical execution ownership

Every paceval item below is a **successfully created and executed original SDK graph**. Formula strings and version IDs are published in [formula_registry.csv](results/formula_registry.csv); the machine-readable full inventory is in [math_execution_inventory.csv](results/math_execution_inventory.csv).

| Mathematical function / industrial purpose | Actual implementation | Graphs or rationale |
|---|---|---|
| OCV, state-dependent $R_0$, $R_1$, $R_2$ and both time constants | **paceval** | `ocv`, `ohmic_resistance`, `fast_resistance`, `slow_resistance`, `fast_tau`, `slow_tau` |
| SOC, fast-RC and two distinct slow-RC state updates | **paceval** | `next_soc`, `next_fast_polarization`, `next_slow_polarization_v1/v2` |
| 1RC and 2RC terminal voltage | **paceval** | `terminal_voltage_v1/v2` |
| Lumped temperature and resistive-heat proxy | **paceval** | `next_cell_temperature_v1/v2`, `resistive_heat_proxy_v1/v2` |
| OCV, terminal, ohmic, polarization power and algebraic power residual | **paceval** | Versioned `*_power_v1/v2`, `power_identity_residual_v1/v2` |
| SOC, voltage, temperature signed feasibility margins | **paceval** | `soc_*_margin`, `voltage_*_margin_v1/v2`, `thermal_upper_margin` |
| Analytical local sensitivities of OCV, $R_0$, voltage and SOC transition | **paceval** | `d_ocv_d_soc`, `d_r0_d_soc`, `d_r0_d_temp`, `d_voltage_d_current_v1/v2`, etc. |
| Composed voltage / load / temperature / parameter / SOC cost functions | **paceval** | `composite_cost_v1_01...10`, `composite_cost_v2_01...10` |
| Time-scheduled current profiles, parameter validation, state control | **C++ host** | Deterministic scheduling and orchestration, not mathematical graph evaluation |
| Per-scenario accumulated energy and extrema | **C++ host** | Stateful summation and reporting of paceval-produced power samples |
| Independent complete trajectory and 80-decimal scientific checks | **Python reference** | [verify_results.py](src/verify_results.py), [high_precision_reference.py](src/high_precision_reference.py) |

The main production path batches voltage, SOC, polarization states, heat, electrical power and composite scores through the original `paceval_dGetMultipleComputationsResultsExt` function. For all graphs, periodic complete batch probes document real execution; a separate scalar call cross-checks an OCV evaluation. The original `paceval_main.cpp` and `paceval_main.h` are included in `src/` with only the relative source include adapted for this project layout.

## 5. Deterministic research workload and results

The demonstration uses **1RC and 2RC**, three synthetic cell-current schedules (urban pulses, highway load, charge/rest), ambient temperatures of **5, 25 and 40 C**, and a 1.12 synthetic capacity/resistance modifier in the charge/rest schedule. A 3.2 Ah hypothetical cell starts at SOC 0.74. Each 24-minute run has 720 two-second intervals. State-dependent parameters are held fixed within each integration interval but recomputed at the next step. The integration rule is not a global exact solution for varying coefficients.

Example: for the urban profile at 25 C, the **2RC version** produces final SOC **0.529896**, final cell temperature **26.52 C**, terminal-energy integral **2.48345 Wh** and a minimum terminal voltage **3.49579 V**. These are generated by the executed paceval C++ program, with complete raw precision in [scenario_summary.csv](results/scenario_summary.csv). A lower terminal voltage in the 2RC model does not establish which topology is more accurate without independent real-cell voltage data.

The **hypothetical** operating margins are solely illustrative mathematical checks, not validated manufacturer cell limits, and do not confer thermal safety certification or battery-management approval. Both charge and discharge occur with a consistently positive-discharge convention.

## 6. Scientific figures

All result plots are made from recorded original paceval outputs using [make_figures.py](src/make_figures.py); the architecture schematic is explicitly conceptual.

| Figure | Interpretation |
|---|---|
| [01: Workflow](figures/01_workflow.png) | Conceptual execution and verification workflow |
| [02: Current schedules](figures/02_current_profiles.png) | Synthetic, deterministic input currents |
| [03: Terminal voltage](figures/03_terminal_voltage.png) | Versioned 1RC/2RC voltage response |
| [04: State of charge](figures/04_soc_profiles.png) | Recorded SOC trajectories for three schedules |
| [05: Thermal response](figures/05_thermal_response.png) | Lumped model for three ambient temperatures |
| [06: 3D voltage surface](figures/06_voltage_surface_3d.png) | Original paceval voltage calculations over SOC and temperature |
| [07: Ohmic resistance](figures/07_ohmic_resistance_map.png) | Calibratable parameter surface, synthetic coefficients |
| [08: Time constants](figures/08_relaxation_time_scales.png) | Fast/slow relaxation scale ratio |
| [09: Formula-version response](figures/09_formula_version_response.png) | Same external current, different state-model topology |
| [10: Electrical terms](figures/10_electrical_energy_terms.png) | Signed OCV, terminal and ohmic integrals |

## 7. Build and reproduction

Requires Linux x86-64, C++17, CMake, Python 3 with NumPy, Matplotlib and mpmath, and a **separately obtained compatible original paceval shared library**. The shared library is **not redistributed** in this archive.

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \
  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/battery_twin --out . --steps 720
python3 src/verify_results.py --root .
python3 src/high_precision_reference.py --root .
python3 src/make_figures.py --root .
python3 src/check_readme_math.py
```

Use [reproduce.sh](src/reproduce.sh) for the full sequence. The original SDK is required; a native reference is **not** substituted for it. The `results/` folder contains actual engine logs, formula execution registers, independent technical checks and a parameter surface. See [sdk_execution.txt](results/sdk_execution.txt), [executed_graph_probes.csv](results/executed_graph_probes.csv), and [independent_trajectory_audit.json](results/independent_trajectory_audit.json).

## 8. Scientific interpretation and limitations

This is a software and numerical research demonstration of original paceval mathematical expression execution inside an accepted equivalent-circuit modeling family. It is **not** a fitted lithium-ion cell model, experimental battery-performance validation, state-estimator benchmark, aging predictor, tested pack, thermal-runaway predictor, clinical device or certified BMS. Resistance, capacity and thermal parameters are explicitly synthetic. Additional RC branches may increase expressivity but also introduce parameter identifiability and overfitting concerns; richer models need empirical justification.

An extension using carefully documented open cell-cycling measurements (for example [University of Maryland CALCE battery data](https://calce.umd.edu/data)) would require pulse/rest alignment, uncertainty treatment, true parameter identification and hold-out validation across SOC and temperature. Interval/TINC certification, real battery safety margins, hardware speedups and industrial operational benefits are **not claimed** here. All precise engine-versus-reference comparison statistics are retained in technical audits rather than promoted as competitive accuracy comparisons in this README or whitepaper.

## 9. Literature and technical references

1. [Advancements in parameter estimation for 1RC and 2RC models, *Journal of Energy Storage* (2025)](https://doi.org/10.1016/j.est.2025.115581).
2. [How to parameterise an equivalent-circuit empirical battery model from time-domain data (2026)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13049963/).
3. [Battery ECM and neural-network BMS review, *Batteries* (2026)](https://doi.org/10.3390/batteries12010037).
4. [PyBaMM: Thevenin equivalent circuit model](https://docs.pybamm.org/en/latest/source/api/models/equivalent_circuit/thevenin.html).
5. [MathWorks Simscape Battery: Battery Equivalent Circuit](https://www.mathworks.com/help/simscape-battery/ref/batteryequivalentcircuit.html).
6. [CALCE battery research data](https://calce.umd.edu/data).
7. [Original paceval source repository](https://github.com/paceval/paceval).

**Reproducibility note:** The library sources included in the project retain their upstream AGPL notices; anyone publishing modified or combined code should review their license obligations. The external proprietary/runtime binary is not included. A successful structural math/link check does not constitute a visual verification of GitHub's Markdown renderer.
