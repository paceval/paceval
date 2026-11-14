# Electric Motor Efficiency and Field-Weakening Maps with paceval

![Concept illustration of a disassembled electric traction motor with flux and efficiency visualization](figures/00_electric_motor_hero.png)

*Concept illustration; not a computed research result.*

An independently verified, executable **C++ research demonstrator** for steady-state interior permanent-magnet synchronous motor (IPMSM) operating maps. It uses the **original paceval Mathematical Engine SDK 4.25** to evaluate genuine reusable mathematical execution graphs. This release is a **synthetic mathematical study**, not a calibrated motor model, inverter software, certified efficiency measurement, or drive controller.

## 1. Industrial use case and current state of the art

Traction-drive and industrial-motor teams must determine how much torque a motor can deliver as its speed rises, whether a given current command fits inverter limits, how stator winding and magnet temperatures modify these boundaries, and how much power is lost at each operating point. A typical workflow starts with electromagnetic characterization and measured material parameters, constructs flux and loss maps, calculates current commands for required torque and speed, and checks thermal, current, and voltage constraints. Dynamometer tests and electromagnetic finite-element analysis are required to substantiate an industrial machine model.

At low speed, an interior PMSM often uses **maximum torque per ampere (MTPA)** current references. At higher speed, the back electromotive force requires negative d-axis current to reduce net flux and meet the available voltage vector constraint. **Field weakening** trades available torque against extended speed capability, and deep field-weakening operation may require maximum torque per voltage (MTPV). These are current-selection strategies; they must not be confused with a single measured or theoretically globally optimal trajectory. MathWorks documents the corresponding current and voltage constraint loci, MTPA and field-weakening control for PMSMs. [1](https://www.mathworks.com/help/mcb/gs/field-weakening-control-mtpa-pmsm.html) [2](https://www.mathworks.com/help/mcb/gs/pmsm-constraint-curves-and-their-application.html)

Industry increasingly combines electromagnetic FEA flux maps, saturation-aware loss models and motor-inverter simulation. Work published in **2026** explicitly integrates electromagnetic, thermal and driving-cycle operating maps; other 2026 work describes flux-map-based modeling of speed/torque envelopes. [3](https://www.mdpi.com/2076-3417/16/11/5589) [4](https://www.nature.com/articles/s41598-026-36663-3) The 2024 NHTSA technical support documentation also uses electric-machine torque-speed efficiency maps from measured or characterized traction systems. [5](https://www.nhtsa.gov/sites/nhtsa.gov/files/2024-06/CAFE-2027-2031-HDPUV-2030-2035_Final-Technical-Support-Document.pdf)

**Research question.** Can the important analytical motor functions, including the *resistive* dq voltage model, torque and reluctance contribution, copper/iron/mechanical loss proxies, current/voltage margins, composite feasibility guards, sensitivities and temperature-model comparisons, be executed as real reusable paceval graphs and independently verified across a meaningful grid of operating states? This is a functionality question, not a claim of speed or energy savings.

## 2. Mathematical model and explicit conventions

The model assumes a balanced, sinusoidal three-phase IPMSM, constant d/q inductances, constant rotor speed per operating point, and quasisteady current commands. Currents and synchronous-frame voltages are **peak quantities**, $p$ is the number of **pole pairs**, and the inverter uses a **linear-SVPWM peak voltage-vector limit** $V_{\mathrm{dc}}/\sqrt{3}$. The temperature input is an illustrative common winding/magnet temperature, not a solved thermal field. V1 intentionally ignores its influence, while V2 incorporates two explicit temperature correlations.

```math
\begin{aligned}
\omega_m &= 2\pi n/60,\quad \omega_e=p\omega_m,\\
\psi_d &= \psi_{\mathrm{PM}}+L_di_d,\qquad \psi_q=L_qi_q,\\
v_d &= R_si_d-\omega_e\psi_q,\\
v_q &= R_si_q+\omega_e\psi_d,\\
T_e &= \tfrac32 p(\psi_d i_q-\psi_q i_d),\\
I_s^2 &= i_d^2+i_q^2\le I_{\max}^2,\\
v_d^2+v_q^2 &\le (V_{\mathrm{dc}}/\sqrt3)^2.
\end{aligned}
```

V1 fixes $R_s=R_{s,25}$ and $\psi_{\mathrm{PM}}=\psi_{25}$; V2 uses the separately registered expressions below:

```math
\begin{aligned}
R_s(T)&=R_{s,25}\left[1+\alpha_R(T-T_{\mathrm{ref}})\right],\\
\psi_{\mathrm{PM}}(T)&=\psi_{25}\left[1+\beta_\psi(T-T_{\mathrm{ref}})\right].
\end{aligned}
```

Losses are **uncalibrated functional surrogates**. Copper loss is $1.5R_s(i_d^2+i_q^2)$ with peak dq currents. The illustrative iron-loss term scales with $\omega_e^2(\psi_d^2+\psi_q^2)$ and its empirical coefficient; viscous mechanical loss scales with $\omega_m^2$. For motoring operation, estimated shaft efficiency is calculated from positive shaft power divided by electrical input. Zero-speed or non-motoring points receive a zero-valued displayed efficiency, not a physical zero-speed efficiency measurement. Inverter semiconductor, switching and control-system losses are excluded. The real software performs all these calculations through paceval graphs; C++ only selects among the evaluated finite candidates.

The positive **current margin** is $I_{\max}^2-i_d^2-i_q^2$ in A². The positive **voltage margin** is $(V_{\mathrm{dc}}/\sqrt3)^2-v_d^2-v_q^2$ in V². An AND expression combines these guards into a 0/1 feasibility flag. The host still checks finite inputs, schema validity and output conditions. A flagged point is not an industrial safety permission.

## 3. Two simultaneous formula versions and actual computation ownership

Both sets of graph handles remain independently accessible during the same program execution. The **69 executed mathematical graphs** consist of **32 V1 graphs, 32 V2 graphs and 5 inter-model comparison graphs**. The table groups actual graph IDs; none of the following functions is a merely descriptive or placeholder registration.

| Mathematical function / industrial purpose | Actual implementation | Graphs / version |
|---|---|---|
| Stator resistance, PM flux, d/q flux linkages | paceval | `V1_RS`, `V2_RS`, `V1_PM_FLUX`, `V2_PM_FLUX`, `V1_FLUX_D/Q`, `V2_FLUX_D/Q` |
| Resistive d/q terminal voltage and required vector | paceval | `V1_VOLTAGE_D/Q/MAG`, `V2_VOLTAGE_D/Q/MAG` |
| Electromagnetic torque, PM and reluctance components | paceval | `V1_TORQUE`, `V2_TORQUE`, `*_TORQUE_PM`, `*_TORQUE_RELUCTANCE` |
| Copper, iron, mechanical and total losses | paceval | `*_COPPER_LOSS`, `*_IRON_LOSS`, `*_MECH_LOSS`, `*_TOTAL_LOSS` |
| Electromagnetic power, shaft power, electrical input, efficiency | paceval | `*_EM_POWER`, `*_SHAFT_POWER`, `*_ELEC_INPUT`, `*_EFFICIENCY` |
| Current/voltage margins and utilization | paceval | `*_CURRENT_MARGIN`, `*_VOLTAGE_MARGIN`, `*_CURRENT_UTIL`, `*_VOLTAGE_UTIL` |
| Torque/efficiency target margins, combined constraint and score | paceval | `*_TARGET_TORQUE_MARGIN`, `*_EFFICIENCY_MARGIN`, `*_FEASIBILITY_GUARD`, `*_SCREENING_SCORE` |
| Analytical torque, voltage and thermal sensitivities | paceval | `*_DTORQUE_DID/DIQ/DT`, `*_DVOLTAGE2_DID/DIQ`, `*_DCOPPER_DT` |
| Temperature-model deltas and conservative voltage margin | paceval | `DELTA_TORQUE`, `DELTA_VOLTAGE`, `DELTA_EFFICIENCY`, `DELTA_TOTAL_LOSS`, `WORST_VOLT_MARGIN` |
| Finite-grid maximum-torque and torque-qualified efficiency selection | C++ host | Discrete selection; no native replacement for motor formulas |
| CSV validation, loop control, scalar and batch orchestration | C++ host | Original paceval SDK called for numerical field conversions and mathematics |
| Independent numerical checking | Native C++ and mpmath | Verification only, not published paceval data generation |

The program genuinely invokes `paceval_CreateComputation`, `paceval_dGetMultipleComputationsResultsExt`, `paceval_dGetComputationResult` in its self-test, `paceval_dConvertStringToFloat`, `paceval_dConvertFloatToString`, and handle release. Multi-graph layout and error-array semantics are checked with a small known-answer test. The CSV validator refuses arbitrary formulas in numeric fields even though the SDK number parser can interpret mathematical expressions. The graph registry, actual expressions, units and execution flags are in [`results/formula_manifest.csv`](results/formula_manifest.csv), [`results/math_execution_inventory.csv`](results/math_execution_inventory.csv), and [`results/execution_evidence.json`](results/execution_evidence.json).

## 4. Reproducible operating-map experiment

The supplied CSV evaluates **19,404 distinct synthetic `(temperature, speed, id, iq)` input combinations** and **38,808 motor-model cases**. Parameters are deliberately transparent in [`input/motor_parameters.csv`](input/motor_parameters.csv). The test uses 25°C and 110°C, 0 to 10,500 rpm, negative d-current and nonnegative q-current on a rectangular finite grid. Infeasible vectors are **not selected** as valid operating points. A sample is reported below; these numbers are from the executed original paceval engine, not from the independent mathematical reference.

| At 110°C, constrained maximum torque | V1 constant parameter model | V2 temperature-aware model |
|---|---:|---:|
| 3,000 rpm | 228.46 N m | 214.35 N m |
| 5,000 rpm | 218.25 N m | 205.85 N m |
| 9,000 rpm | 114.85 N m | 124.65 N m |
| 10,000 rpm | 100.67 N m | 95.72 N m |

The reversal at 9,000 rpm is interpretable: V2 loses low-speed PM torque from weakened magnet flux, but the altered flux changes the voltage-constrained feasible region at high speed. Because the grid is finite and the inductances and loss coefficients are assumed, this should **not** be read as a universal improvement or a certified motor result. The 25°C results coincide between the two models because their parameter definitions coincide at the reference temperature.

The model emphasizes *feasible evaluated points*. Its maximum-torque path is the best point **on the declared grid**, not a mathematical proof of a globally optimal MTPA or MTPV trajectory. The additional efficiency output chooses the highest observed shaft efficiency **subject to a 120 N m torque threshold**, and is undefined when no feasible candidate satisfies that threshold. At zero speed, the computed torque may be nonzero while the shaft efficiency readout is deliberately zero.

## 5. Build and reproduce

On Linux x86-64, supply the **compatible original paceval runtime** separately; no `.so` library is packaged or published with this repository. The original SDK 4.25 files `src/paceval_main.h` and `src/paceval_main.cpp` are included with their copyright/license notices and a minimal local-include adaptation. No substitute paceval engine is used.

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \
  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/motor_maps --run input/candidates.csv input/motor_parameters.csv results
python3 scripts/verify_high_precision.py results input/motor_parameters.csv
python3 scripts/make_figures.py
```

The result CSVs and `execution_evidence.json` come from the C++/paceval execution, while detailed numerical audit data come from the independent verification path. Before CSV-to-number conversion, the application validates decimal-literal grammar; internal scientific CSV files use decimal dots and UTF-8. All published CSV floating values are formatted with the official paceval SDK and are not asserted to roundtrip bit-for-bit. The independent checking script uses exact binary64 rational input interpretation and 90-digit mpmath calculations.

## 6. Visual results

The eleven scientific plots below come **only from actual paceval-generated result data**. Each is available as vector PDF and PNG and is recreated using [`scripts/make_figures.py`](scripts/make_figures.py).

| Figure | Research interpretation |
|---|---|
| [01 Torque–speed envelopes](figures/fig01_torque_speed_envelope.png) | Voltage/current-constrained torque capability |
| [02 Field-weakening d current](figures/fig02_field_weakening_current.png) | Negative d-current movement at increasing speed |
| [03 Shaft efficiency map](figures/fig03_efficiency_map.png) | Highest sampled efficiency in speed–torque bins |
| [04 Current-plane feasibility](figures/fig04_current_plane_feasibility.png) | Intersection of both constraints at two speeds |
| [05 Loss breakdown](figures/fig05_loss_decomposition.png) | Copper, illustrative iron and mechanical losses |
| [06 Voltage-limit proximity](figures/fig06_voltage_limit_utilization.png) | Constraint utilization on selected envelope |
| [07 Thermal-model torque difference](figures/fig07_temperature_model_delta.png) | Same-current V2−V1 torque effect |
| [08 Torque and power envelopes](figures/fig08_envelope_torque_and_power.png) | Explicit paceval torque and EM power |
| [09 Torque-qualified efficiency](figures/fig09_target_torque_optimal_efficiency.png) | Conditional finite-grid efficiency selection |
| [10 3D torque surface](figures/fig10_3d_torque_current_surface.png) | Full evaluated torque surface, including infeasible input vectors |
| [11 Analytical sensitivities](figures/fig11_torque_sensitivities.png) | Partial derivatives at selected operating points |

## 7. Real validation and scientific limits

The original Linux SDK was compiled and executed with the associated shared library. All **69/69** research graphs were used in the main path. The accompanying `results/scientific_audit.json` documents **1,133 scenario/version rows** evaluated by an independent **90-digit** model and **25,002 successful checks**. The application separately performed **2,316 native C++ numerical end-value checks**. The exact validation errors and tolerances are archived in `results/` and are not presented as competitive precision claims.

**Important limitations:** no measured inductance or flux map; no saturation, cross-saturation or magnet demagnetization threshold modeling; no loss identification or temperature-dependent iron coefficients; no inverter switching/conduction losses; no regeneration; no transient motor/thermal dynamics; no battery-voltage droop, voltage overmodulation, acoustic effects or real-time controller validation. Voltage/current limits and surrogate efficiency are mathematical screening results, not machine safety or certification evidence. More mature workflows calibrate a loss/flux-map model against FEA and dynamometer data, as shown in the specialist methods cited above. [3](https://www.mdpi.com/2076-3417/16/11/5589) [6](https://www.mathworks.com/help/simscape-electrical/ref/femparameterizedpmsm.html)

A next technical stage could supply measured $\psi_d(i_d,i_q,T)$, $\psi_q(i_d,i_q,T)$, resistance, mechanical and iron-loss maps and validate them against motor dynamometer runs. That would allow physically grounded current-reference lookup and trajectory studies. No FPGA or ASIC acceleration is claimed by this CPU software study.

## 8. Documentation and sources

[`RESEARCH_VALIDATION.md`](RESEARCH_VALIDATION.md) lists the actual numerical audit scope; [`docs/SDK_COMPATIBILITY.md`](docs/SDK_COMPATIBILITY.md) details original library linking and API contracts; [`input/SCHEMA.md`](input/SCHEMA.md) fixes the data schema; the [English PDF whitepaper](paceval_Electric_Motor_Efficiency_Field_Weakening_Whitepaper_EN.pdf) is a standalone scientific report.

1. MathWorks. [Field-Weakening Control (with MTPA) of PMSM](https://www.mathworks.com/help/mcb/gs/field-weakening-control-mtpa-pmsm.html), R2026b documentation.
2. MathWorks. [PMSM Constraint Curves and Their Application](https://www.mathworks.com/help/mcb/gs/pmsm-constraint-curves-and-their-application.html).
3. *Applied Sciences* (2026). [Integrated Multiphysics and WLTP-Based System-Level Evaluation of a 130 kW IPMSM](https://www.mdpi.com/2076-3417/16/11/5589).
4. *Scientific Reports* (2026). [Evaluation of electric vehicle performance using driving-cycle clustering based on motor-inverter losses and efficiency](https://www.nature.com/articles/s41598-026-36663-3).
5. NHTSA (2024). [CAFE Final Technical Support Document, electric machine efficiency maps](https://www.nhtsa.gov/sites/nhtsa.gov/files/2024-06/CAFE-2027-2031-HDPUV-2030-2035_Final-Technical-Support-Document.pdf).
6. MathWorks. [FEM-Parameterized PMSM loss and flux models](https://www.mathworks.com/help/simscape-electrical/ref/femparameterizedpmsm.html).
7. *Energies* (2022). [Review of flux-weakening operating limits and controls](https://www.mdpi.com/1996-1073/15/5/1930).
8. *Electronics* (2025). [Flux-weakening control at high speed](https://www.mdpi.com/2079-9292/14/19/3779).
9. [paceval API documentation](https://paceval.com/api/) and [product brief](https://paceval.com/product-brief/).

**Provenance:** All input data are synthetic, all scientific result figures originate in the actual paceval output files, and the hero image is a concept illustration. Research date: **14 November 2026**. Original SDK source notices indicate AGPL licensing; review all SDK and application distribution obligations before third-party redistribution.
