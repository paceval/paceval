# paceval. | Industrial Research Portfolio

**61 C++ research demonstrators and scientific whitepapers across ten application clusters.**

This directory presents application-oriented research using the [paceval. Mathematical Engine](https://paceval.com/). The projects investigate how explicit mathematical expressions can be transformed into persistent computation graphs, evaluated repeatedly, and integrated with engineering software, AI agents, digital twins, industrial operations and scientific workflows. Each study has a dedicated README, an English research whitepaper and a main C++ source file.

The collection illustrates **executable mathematical research and feasibility studies**. Individual results must be interpreted within their declared models, test datasets and validation methods. The projects are not automatically commercial products, validated field deployments or certified safety systems.

**Portfolio inventory (13 November 2026):** 61 project directories, 61 project READMEs, 61 English research PDFs covering 643 pages, and 61 primary C++ demonstrators. All three direct links for each entry below have been verified against the supplied core-file archive. Each main C++ source contains paceval computation-creation and result-evaluation call sites. The source inventory does not establish that all programs were independently rebuilt or rerun during preparation of this index.

## How the paceval Mathematical Engine is used

```text
Engineering model, AI tool request, physical scenario or financial model
                              |
                 Host validates input and units
                              |
               Explicit mathematical expressions
                              |
             paceval CreateComputation once
                              |
             Reusable graph and computation handle
                              |
           Repeated scalar or multi-graph evaluation
                              |
             Numerical values and model decisions
                              |
           Host workflow and independent verification
```

The paceval SDK prepares explicit mathematical expressions for repeated evaluation. The research programs use the original paceval interfaces through the C/C++ facade and, where applicable, persistent graphs and multi-graph batch APIs. Application-level C++ remains responsible for tasks such as input handling, combinatorial scheduling, simulation state, data selection, I/O, algorithm orchestration and independent checks. **The use of paceval does not imply that every algorithm, optimizer or simulation step runs inside the mathematical engine.**

For language model workflows, this separation is particularly important. An agent can select an approved mathematical operation and pass validated parameters, while paceval executes the explicit calculation. Deterministic mathematical evaluation alone does not verify the semantic correctness of an agent-generated formula, authorization, units or policy.

Learn more: [paceval source repository](https://github.com/paceval/paceval), [developer documentation](https://paceval.com/developers/), [Trusted Interval Computation](https://paceval.com/tinc/) and [paceval MCP Server](https://github.com/paceval/paceval/tree/main/examples_sources/MCP_server).

## Browse research by application cluster

| Cluster | Projects | Main focus |
|---|---:|---|
| [1. AI agents, mathematical tools and verifiable computation](#cluster-1) | 9 | Tool-based mathematical evaluation, calculation handles, formula contracts and traceable steps. |
| [2. Edge computing, sensors and operational monitoring](#cluster-2) | 5 | Edge scoring, sensor telemetry, anomaly rules and condition assessment. |
| [3. Manufacturing, planning and industrial decision functions](#cluster-3) | 9 | Production planning, machining, industrial optimization, quality and inventory. |
| [4. Digital twins, equipment models and energy conversion](#cluster-4) | 9 | Simulation modules for factories, buildings, batteries, heat pumps, pumps and turbines. |
| [5. Robotics, trajectory scoring and calibration](#cluster-5) | 3 | Kinematics, calibration, trajectories and configurable objective functions. |
| [6. Energy systems, renewables and fusion engineering](#cluster-6) | 3 | Demand response, wind-farm losses and plasma control functions. |
| [7. Finance, insurance and quantitative risk](#cluster-7) | 8 | Financial valuation, portfolio stress, market risk, tariffs and scorecards. |
| [8. Space engineering, astronomy and catalog analysis](#cluster-8) | 6 | Electric propulsion, orbital transfers, gravity and Fermi 2FLE spectra. |
| [9. Fundamental physics and mathematical model exploration](#cluster-9) | 5 | PDE kernels, conservation candidates, mathematical surfaces, collider and quantum exercises. |
| [10. Biomedical engineering, pharmacokinetics and microfluidics](#cluster-10) | 4 | Non-clinical signals, pharmacokinetics and reaction transport. |
| **Total** | **61** | **Each project is assigned to one primary cluster. Several use cases span multiple domains.** |

## Project catalogue

Each project name opens its local README. The PDF and C++ columns link directly to the primary research whitepaper and executable source text. These are relative repository links, so this index can be uploaded as `README.md` at the root of `TOP+ Industrial Research Projects with paceval/`.

<a id="cluster-1"></a>
### 1. AI agents, mathematical tools and verifiable computation (9)

Deterministic mathematical tool boundaries, validated expressions and traceable computational workflows. The agent or host software remains responsible for the request, interpretation and authorization.

| Research project | Mathematical scope and demonstrated workflow | Whitepaper | C++ source |
|---|---|---|---|
| [Technical AI Agents](paceval_Technical_AI_Agents/README.md) | Engineering formulas exposed through a typed, unit-checked tool boundary. | [PDF](paceval_Technical_AI_Agents/paceval_Technical_AI_Agents_Whitepaper_EN.pdf) | [C++](paceval_Technical_AI_Agents/src/technical_agent.cpp) |
| [LLM Generated Mathematics](paceval_LLM_Generated_Mathematics/README.md) | Validate and evaluate generated mathematical expressions under explicit model contracts. | [PDF](paceval_LLM_Generated_Mathematics/paceval_LLM_Math_Expressions_Whitepaper_EN.pdf) | [C++](paceval_LLM_Generated_Mathematics/src/llm_math.cpp) |
| [Agent Constraint Verification](paceval_Agent_Constraint_Verification_Research/README.md) | Execute versioned mathematical guards on proposed industrial setpoints. | [PDF](paceval_Agent_Constraint_Verification_Research/paceval_Agent_Constraint_Verification_Whitepaper_EN.pdf) | [C++](paceval_Agent_Constraint_Verification_Research/src/agent_constraints.cpp) |
| [Auditable AI Chains](paceval_Auditable_AI_Chains/README.md) | Compose reusable mathematical steps with traceable intermediate values. | [PDF](paceval_Auditable_AI_Chains/paceval_Auditable_AI_Chains_Whitepaper_EN.pdf) | [C++](paceval_Auditable_AI_Chains/src/auditable_chains.cpp) |
| [Agent Simulations](paceval_Agent_Simulations_Research/README.md) | Coordinate selected simulation families with reusable formulas and logged retries. | [PDF](paceval_Agent_Simulations_Research/paceval_Agent_Orchestrated_Mathematical_Simulations_Whitepaper_EN.pdf) | [C++](paceval_Agent_Simulations_Research/src/agent_simulations.cpp) |
| [Agent Financial Arithmetic](paceval_Agent_Financial_Arithmetic/README.md) | Serve controlled, versioned financial computations to structured agent requests. | [PDF](paceval_Agent_Financial_Arithmetic/paceval_Agent_Financial_Arithmetic_Whitepaper_EN.pdf) | [C++](paceval_Agent_Financial_Arithmetic/src/financial_agent.cpp) |
| [Large Quantitative Model Tools](paceval_Large_Quantitative_Model_Tools_Research/README.md) | Provide reusable quantitative formula tools for higher-level assistants. | [PDF](paceval_Large_Quantitative_Model_Tools_Research/paceval_Large_Quantitative_Model_Tools_Whitepaper_EN.pdf) | [C++](paceval_Large_Quantitative_Model_Tools_Research/src/quantitative_tools.cpp) |
| [Hypothesis Testing](paceval_Hypothesis_Testing/README.md) | Screen explicitly generated mathematical hypotheses against numerical data. | [PDF](paceval_Hypothesis_Testing/paceval_Hypothesis_Testing_Whitepaper_EN.pdf) | [C++](paceval_Hypothesis_Testing/src/hypothesis_test.cpp) |
| [Low Code Automation](paceval_Low_Code_Automation/README.md) | Reuse approved mathematical models in an automation-style integration workflow. | [PDF](paceval_Low_Code_Automation/paceval_Low_Code_Automation_Whitepaper_EN.pdf) | [C++](paceval_Low_Code_Automation/src/lowcode_math.cpp) |

<a id="cluster-2"></a>
### 2. Edge computing, sensors and operational monitoring (5)

Expression execution close to devices and industrial data sources. The studies distinguish mathematical scoring from data acquisition, learned-model inference and hardware deployment.

| Research project | Mathematical scope and demonstrated workflow | Whitepaper | C++ source |
|---|---|---|---|
| [Edge AI Postprocessing](paceval_Edge_AI_Postprocessing/README.md) | Apply deterministic mathematical scoring to precomputed AI outputs. | [PDF](paceval_Edge_AI_Postprocessing/paceval_Edge_AI_Postprocessing_Whitepaper_EN.pdf) | [C++](paceval_Edge_AI_Postprocessing/src/edge_ai.cpp) |
| [Industrial Gateway](paceval_Industrial_Gateway/README.md) | Execute versioned telemetry rules in an offline industrial gateway replay. | [PDF](paceval_Industrial_Gateway/paceval_Industrial_Gateway_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Gateway/src/gateway_rules.cpp) |
| [On Device Expression Runtime](paceval_On_Device_Expression_Runtime/README.md) | Prepare reusable expressions for bounded-input device-side evaluation. | [PDF](paceval_On_Device_Expression_Runtime/paceval_On_Device_Expression_Runtime_Whitepaper_EN.pdf) | [C++](paceval_On_Device_Expression_Runtime/src/on_device_runtime.cpp) |
| [Explainable Anomaly Detection](paceval_Explainable_Anomaly_Detection/README.md) | Evaluate versioned anomaly-scoring formulas on synthetic sensor streams. | [PDF](paceval_Explainable_Anomaly_Detection/paceval_Explainable_Anomaly_Detection_Whitepaper_EN.pdf) | [C++](paceval_Explainable_Anomaly_Detection/src/anomaly_detection.cpp) |
| [Predictive Maintenance](paceval_Predictive_Maintenance/README.md) | Calculate mathematical vibration-condition features and health scores. | [PDF](paceval_Predictive_Maintenance/paceval_Predictive_Maintenance_Whitepaper_EN.pdf) | [C++](paceval_Predictive_Maintenance/src/predictive_maintenance.cpp) |

<a id="cluster-3"></a>
### 3. Manufacturing, planning and industrial decision functions (9)

Reusable mathematical objectives, feasibility margins, process formulas and cost scores inside offline manufacturing and operations studies.

| Research project | Mathematical scope and demonstrated workflow | Whitepaper | C++ source |
|---|---|---|---|
| [Agent-Controlled Production Planning Scores](paceval_Agent_Controlled_Production_Planning_Scores/README.md) | Uses persistent scheduling scores and constraint margins for a synthetic job-shop problem. A host scheduler handles combinatorial selection and controlled policy requests. | [PDF](paceval_Agent_Controlled_Production_Planning_Scores/paceval_Agent_Controlled_Production_Planning_Scores_Whitepaper_EN.pdf) | [C++](paceval_Agent_Controlled_Production_Planning_Scores/src/production_planning.cpp) |
| [CNC Parameter Screening](paceval_CNC_Parameter_Screening/README.md) | Screens machining parameters with reusable milling-related formulas, constraint checks and configurable scoring variants. | [PDF](paceval_CNC_Parameter_Screening/paceval_CNC_Parameter_Screening_Whitepaper_EN.pdf) | [C++](paceval_CNC_Parameter_Screening/src/cnc_screening.cpp) |
| [Industrial Control](paceval_Industrial_Control/README.md) | Evaluate objective and constraint terms in an offline MPC-style study. | [PDF](paceval_Industrial_Control/paceval_Industrial_Control_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Control/src/industrial_control.cpp) |
| [Quality Scrap Scores](paceval_Quality_Scrap_Scores_Research/README.md) | Apply mathematical quality-risk and inspection-routing scores. | [PDF](paceval_Quality_Scrap_Scores_Research/paceval_Quality_Scrap_Scores_Whitepaper_EN.pdf) | [C++](paceval_Quality_Scrap_Scores_Research/src/quality_scores.cpp) |
| [Inventory Replenishment](paceval_Inventory_Replenishment_Research/README.md) | Compare parameterized inventory replenishment decision rules. | [PDF](paceval_Inventory_Replenishment_Research/paceval_Inventory_Replenishment_Whitepaper_EN.pdf) | [C++](paceval_Inventory_Replenishment_Research/src/inventory_replenishment.cpp) |
| [Auction Bid Formulas](paceval_Auction_Bid_Formulas_Research/README.md) | Evaluate versioned mathematical supplier-bid formulas. | [PDF](paceval_Auction_Bid_Formulas_Research/paceval_Auction_Bid_Formulas_Whitepaper_EN.pdf) | [C++](paceval_Auction_Bid_Formulas_Research/src/auction_bids.cpp) |
| [Industrial 3D](paceval_Industrial_3D_Research/README.md) | Generate scientific 3D surfaces from computed industrial mathematical models. | [PDF](paceval_Industrial_3D_Research/paceval_Industrial_3D_Diagrams_Whitepaper_EN.pdf) | [C++](paceval_Industrial_3D_Research/src/industrial_3d.cpp) |
| [Material Symbolic Regression](paceval_Material_Symbolic_Regression_Research/README.md) | Evaluate predefined synthetic material-property candidate formulas. | [PDF](paceval_Material_Symbolic_Regression_Research/paceval_Material_Symbolic_Regression_Whitepaper_EN.pdf) | [C++](paceval_Material_Symbolic_Regression_Research/src/material_candidate.cpp) |
| [Symbolic System Identification](paceval_Symbolic_System_Identification/README.md) | Screen candidate nonlinear dynamical-system expressions against trajectories. | [PDF](paceval_Symbolic_System_Identification/paceval_Symbolic_System_Identification_Whitepaper_EN.pdf) | [C++](paceval_Symbolic_System_Identification/src/system_identification.cpp) |

<a id="cluster-4"></a>
### 4. Digital twins, equipment models and energy conversion (9)

Parameterized mathematical submodels for physical assets, simulation state updates and scenario comparisons. The examples use reduced-order or synthetic models rather than calibrated commercial twins.

| Research project | Mathematical scope and demonstrated workflow | Whitepaper | C++ source |
|---|---|---|---|
| [Digital Twins Simulation](paceval_Digital_Twins_Simulation/README.md) | Evaluate reusable mathematical submodels in a synthetic thermal digital twin. | [PDF](paceval_Digital_Twins_Simulation/paceval_Digital_Twins_Whitepaper_EN.pdf) | [C++](paceval_Digital_Twins_Simulation/src/digital_twin.cpp) |
| [Factory Line Digital Twin](paceval_Factory_Line_Digital_Twin/README.md) | Couples a synthetic discrete-event line simulation to reusable station-time formulas, quality, energy and KPI computations. | [PDF](paceval_Factory_Line_Digital_Twin/paceval_Factory_Line_Digital_Twin_Whitepaper_EN.pdf) | [C++](paceval_Factory_Line_Digital_Twin/src/factory_line_twin.cpp) |
| [Building Thermal Twin](paceval_Building_Thermal_Twin/README.md) | Evaluates synthetic building heat balances, forecast functions, calibration losses and analytical sensitivities. | [PDF](paceval_Building_Thermal_Twin/paceval_Building_Thermal_Twin_Whitepaper_EN.pdf) | [C++](paceval_Building_Thermal_Twin/src/thermal_twin.cpp) |
| [Heat Pump Twin](paceval_Heat_Pump_Twin/README.md) | Evaluates synthetic coefficient-of-performance maps, heating power, electricity use, sensitivities and cost expressions. | [PDF](paceval_Heat_Pump_Twin/paceval_Heat_Pump_Twin_Whitepaper_EN.pdf) | [C++](paceval_Heat_Pump_Twin/src/heat_pump_twin.cpp) |
| [Hydraulic Pump Twin](paceval_Hydraulic_Pump_Twin/README.md) | Uses synthetic pump curves and network models to calculate operating points, efficiency, power, energy cost and sensitivities. | [PDF](paceval_Hydraulic_Pump_Twin/paceval_Hydraulic_Pump_Twin_Whitepaper_EN.pdf) | [C++](paceval_Hydraulic_Pump_Twin/src/hydraulic_pump_twin.cpp) |
| [Battery Equivalent Circuit Twin](paceval_Battery_Twin_Equivalent_Circuit_Functions/README.md) | Evaluates synthetic 1RC and 2RC circuit equations for voltage, state of charge, energy and thermal behavior. | [PDF](paceval_Battery_Twin_Equivalent_Circuit_Functions/paceval_Battery_Twin_Equivalent_Circuit_Functions_Whitepaper_EN.pdf) | [C++](paceval_Battery_Twin_Equivalent_Circuit_Functions/src/battery_twin.cpp) |
| [Battery Charging and Aging Terms](paceval_Battery_Charging_Aging/README.md) | Screens tariff-aware charging schedules using state-of-charge transitions, versioned cost expressions and explicitly uncalibrated aging surrogates. | [PDF](paceval_Battery_Charging_Aging/paceval_Battery_Charging_Aging_Whitepaper_EN.pdf) | [C++](paceval_Battery_Charging_Aging/src/battery_charging_aging.cpp) |
| [Wind Turbine Digital Twin](paceval_Wind_Turbine_Digital_Twin/README.md) | Evaluates rotor coefficient maps, aerodynamic power, torque, thrust, sensitivities and model state updates on synthetic inputs. | [PDF](paceval_Wind_Turbine_Digital_Twin/paceval_Wind_Turbine_Digital_Twin_Whitepaper_EN.pdf) | [C++](paceval_Wind_Turbine_Digital_Twin/src/wind_turbine_twin.cpp) |
| [Electrolyser Efficiency Surrogates](paceval_Electrolyser_Efficiency_Surrogate_Functions/README.md) | Screens synthetic PEM electrolyser stack voltage, hydrogen production, system efficiency and operating constraints with explicit formula versions. | [PDF](paceval_Electrolyser_Efficiency_Surrogate_Functions/paceval_Electrolyser_Efficiency_Surrogate_Functions_Whitepaper_EN.pdf) | [C++](paceval_Electrolyser_Efficiency_Surrogate_Functions/src/electrolyser_twin.cpp) |

<a id="cluster-5"></a>
### 5. Robotics, trajectory scoring and calibration (3)

Parameterized kinematics, residuals, motion objectives and simplified constraints. The research does not constitute a safety-certified robotics stack.

| Research project | Mathematical scope and demonstrated workflow | Whitepaper | C++ source |
|---|---|---|---|
| [Robotics Trajectory Planning](paceval_Robotics_Trajectory_Planning/README.md) | Evaluate planar robot kinematics, trajectory scores and simplified constraints. | [PDF](paceval_Robotics_Trajectory_Planning/paceval_Robotic_Trajectories_Whitepaper_EN.pdf) | [C++](paceval_Robotics_Trajectory_Planning/src/robotics.cpp) |
| [Reconfigurable Robotic Trajectory Costs](paceval_Reconfigurable_Robotic_Trajectory_Costs/README.md) | Compare complete candidate trajectories under changeable cost formulas. | [PDF](paceval_Reconfigurable_Robotic_Trajectory_Costs/paceval_Reconfigurable_Robotic_Trajectory_Costs_Whitepaper_EN.pdf) | [C++](paceval_Reconfigurable_Robotic_Trajectory_Costs/src/trajectory_costs.cpp) |
| [Robot Calibration](paceval_Robot_Calibration/README.md) | Evaluate 3D robot forward-kinematic residuals for position calibration. | [PDF](paceval_Robot_Calibration/paceval_Robot_Calibration_Whitepaper_EN.pdf) | [C++](paceval_Robot_Calibration/src/robot_calibration.cpp) |

<a id="cluster-6"></a>
### 6. Energy systems, renewables and fusion engineering (3)

Reusable mathematical kernels for flexibility markets, simplified wind-farm interaction models and fusion-inspired diagnostic expressions.

| Research project | Mathematical scope and demonstrated workflow | Whitepaper | C++ source |
|---|---|---|---|
| [Demand Response](paceval_Demand_Response/README.md) | Evaluate versioned demand-response incentive and scheduling formulas. | [PDF](paceval_Demand_Response/paceval_Demand_Response_Whitepaper_EN.pdf) | [C++](paceval_Demand_Response/src/demand_response.cpp) |
| [Wind Farm Loss Functions](paceval_Wind_Farm_Loss_Functions/README.md) | Evaluate simplified wake-loss and turbine-power functions. | [PDF](paceval_Wind_Farm_Loss_Functions/paceval_Wind_Farm_Loss_Functions_Whitepaper_EN.pdf) | [C++](paceval_Wind_Farm_Loss_Functions/src/wind_farm.cpp) |
| [Fusion Plasma Control](paceval_Fusion_Plasma_Control/README.md) | Evaluate explicitly defined plasma diagnostic and control-related functions. | [PDF](paceval_Fusion_Plasma_Control/paceval_Fusion_Diagnostics_Whitepaper_EN.pdf) | [C++](paceval_Fusion_Plasma_Control/src/fusion.cpp) |

<a id="cluster-7"></a>
### 7. Finance, insurance and quantitative risk (8)

Explicit mathematical kernels for controlled scenario evaluation, valuation, exposure and scoring. These experiments are not complete trading, insurance or regulated banking products.

| Research project | Mathematical scope and demonstrated workflow | Whitepaper | C++ source |
|---|---|---|---|
| [Credit Risk Scorecard](paceval_Credit_Risk_Scorecard_Research/README.md) | Evaluate transparent synthetic credit-scorecard formulas. | [PDF](paceval_Credit_Risk_Scorecard_Research/paceval_Credit_Risk_Scorecard_Whitepaper_EN.pdf) | [C++](paceval_Credit_Risk_Scorecard_Research/src/credit_scorecard.cpp) |
| [Counterparty Exposure](paceval_Counterparty_Exposure_Research/README.md) | Evaluate pointwise counterparty-exposure calculation functions. | [PDF](paceval_Counterparty_Exposure_Research/paceval_Counterparty_Exposure_Whitepaper_EN.pdf) | [C++](paceval_Counterparty_Exposure_Research/src/counterparty_exposure.cpp) |
| [Intraday Risk](paceval_Intraday_Risk_Research/README.md) | Replay versioned intraday market-risk functions. | [PDF](paceval_Intraday_Risk_Research/paceval_Intraday_Risk_Whitepaper_EN.pdf) | [C++](paceval_Intraday_Risk_Research/src/intraday_risk.cpp) |
| [Portfolio Stress](paceval_Portfolio_Stress/README.md) | Evaluate synthetic factor stress scenarios and portfolio P&L expressions. | [PDF](paceval_Portfolio_Stress/paceval_Portfolio_Stress_Whitepaper_EN.pdf) | [C++](paceval_Portfolio_Stress/src/portfolio_stress.cpp) |
| [Monte Carlo Pricing](paceval_Monte_Carlo_Pricing/README.md) | Reuse option payoff formulas inside a host-driven Monte Carlo workload. | [PDF](paceval_Monte_Carlo_Pricing/paceval_Monte_Carlo_Pricing_Whitepaper_EN.pdf) | [C++](paceval_Monte_Carlo_Pricing/src/monte_carlo_pricing.cpp) |
| [Pricing Sensitivities](paceval_Pricing_Sensitivities_Research/README.md) | Evaluate option pricing and analytical sensitivity formulas. | [PDF](paceval_Pricing_Sensitivities_Research/paceval_Pricing_Formula_Sensitivities_Whitepaper_EN.pdf) | [C++](paceval_Pricing_Sensitivities_Research/src/pricing_sensitivities.cpp) |
| [Insurance Tariffs](paceval_Insurance_Tariffs/README.md) | Demonstrate versioned synthetic insurance tariff calculations. | [PDF](paceval_Insurance_Tariffs/paceval_Insurance_Tariffs_Whitepaper_EN.pdf) | [C++](paceval_Insurance_Tariffs/src/insurance_tariffs.cpp) |
| [Trading Indicators](paceval_Trading_Indicators_Research/README.md) | Evaluate mathematical quantitative indicator composites on price-bar data. | [PDF](paceval_Trading_Indicators_Research/paceval_Interchangeable_Trading_Indicators_Whitepaper_EN.pdf) | [C++](paceval_Trading_Indicators_Research/src/trading_indicators.cpp) |

<a id="cluster-8"></a>
### 8. Space engineering, astronomy and catalog analysis (6)

Spacecraft modeling, gravitational submodels and reusable astronomy spectral mathematics. The two Fermi 2FLE studies are distinct: one is a synthetic methods pilot, the other uses published NASA fit parameters.

| Research project | Mathematical scope and demonstrated workflow | Whitepaper | C++ source |
|---|---|---|---|
| [Electric Propulsion](paceval_Electric_Propulsion_Research/README.md) | Evaluate parameterized analytical electric-thruster performance maps. | [PDF](paceval_Electric_Propulsion_Research/paceval_Electric_Propulsion_Whitepaper_EN.pdf) | [C++](paceval_Electric_Propulsion_Research/src/electric_propulsion.cpp) |
| [Orbit Parameter Sweeps](paceval_Orbit_Parameter_Sweeps_Research/README.md) | Calculate orbital acceleration components in host-driven orbit propagation. | [PDF](paceval_Orbit_Parameter_Sweeps_Research/paceval_Orbit_Parameter_Sweeps_Whitepaper_EN.pdf) | [C++](paceval_Orbit_Parameter_Sweeps_Research/src/orbit_sweeps.cpp) |
| [Space Transfer Screening](paceval_Space_Transfer_Screening/README.md) | Screens idealized two-body orbital transfers, impulsive velocity budgets, transfer times and rocket-equation propellant requirements. | [PDF](paceval_Space_Transfer_Screening/paceval_Space_Transfer_Screening_Whitepaper_EN.pdf) | [C++](paceval_Space_Transfer_Screening/src/space_transfer.cpp) |
| [Gravitational Inversion](paceval_Gravitational_Inversion_Research/README.md) | Evaluate gravitational-field functions and inversion sensitivities. | [PDF](paceval_Gravitational_Inversion_Research/paceval_Gravitational_Inversion_Whitepaper_EN.pdf) | [C++](paceval_Gravitational_Inversion_Research/src/gravity_inversion.cpp) |
| [Fermi 2FLE Spectral Screening Methods](paceval_Fermi_2FLE_Spectral_Screening/README.md) | Combines transcribed 2FLE source metadata with distinctly synthetic spectral and likelihood inputs to test reusable screening mathematics. | [PDF](paceval_Fermi_2FLE_Spectral_Screening/paceval_Fermi_2FLE_Spectral_Screening_Whitepaper_EN.pdf) | [C++](paceval_Fermi_2FLE_Spectral_Screening/src/fermi_2fle_demo.cpp) |
| [Fermi 2FLE Real Catalog Spectral Mathematics](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/README.md) | Re-evaluates published spectral fit parameters for 450 NASA 2FLE catalog sources. It does not reprocess LAT photon events or establish new source classes. | [PDF](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/paceval_Fermi_2FLE_Real_Catalog_Whitepaper_EN.pdf) | [C++](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/src/fermi_real_catalog.cpp) |

<a id="cluster-9"></a>
### 9. Fundamental physics and mathematical model exploration (5)

Mathematical kernels for specified physics and geometry models, including analytical waves, invariants and large expressions. Numerical experiments are not independent evidence for new physical phenomena.

| Research project | Mathematical scope and demonstrated workflow | Whitepaper | C++ source |
|---|---|---|---|
| [Parameterized Bulk-Wave Kernels](paceval_Bulk_Wave_Kernels/README.md) | Executes parameterized wave operators, manufactured forcing, diagnostic functions and sensitivities in a host-integrated one-dimensional model. | [PDF](paceval_Bulk_Wave_Kernels/paceval_Bulk_Wave_Kernels_Whitepaper_EN.pdf) | [C++](paceval_Bulk_Wave_Kernels/src/bulk_wave_kernels.cpp) |
| [Conservation Law Candidates](paceval_Conservation_Law_Candidates/README.md) | Checks proposed mathematical invariants and time-derivative residuals for specified dynamical models. Candidate screening is not a proof of a universal physical law. | [PDF](paceval_Conservation_Law_Candidates/paceval_Conservation_Law_Candidates_Whitepaper_EN.pdf) | [C++](paceval_Conservation_Law_Candidates/src/conservation_law_candidates.cpp) |
| [Extreme-Length Analytic Terrain](paceval_Extreme_Analytic_Terrain/README.md) | Creates and samples exceptionally long analytical terrain expressions to investigate reusable expression execution and numerical surfaces. | [PDF](paceval_Extreme_Analytic_Terrain/paceval_Extreme_Analytic_Terrain_Whitepaper_EN.pdf) | [C++](paceval_Extreme_Analytic_Terrain/src/extreme_terrain.cpp) |
| [Collider](paceval_Collider_Research/README.md) | Execute selected collider-inspired mathematical analysis kernels. | [PDF](paceval_Collider_Research/paceval_Collider_Research_Whitepaper_EN.pdf) | [C++](paceval_Collider_Research/src/collider.cpp) |
| [Quantum](paceval_Quantum_Research/README.md) | Evaluate classical calibration and circuit-expectation mathematics. | [PDF](paceval_Quantum_Research/paceval_Quantum_Research_Whitepaper_EN.pdf) | [C++](paceval_Quantum_Research/src/quantum.cpp) |

<a id="cluster-10"></a>
### 10. Biomedical engineering, pharmacokinetics and microfluidics (4)

Configurable non-clinical signal rules, fictional pharmacokinetic models and synthetic reaction transport. No clinical efficacy, therapeutic dosing or medical-device validation is claimed.

| Research project | Mathematical scope and demonstrated workflow | Whitepaper | C++ source |
|---|---|---|---|
| [ECG Feature Rules](paceval_ECG_Feature_Rules_Research/README.md) | Evaluate synthetic ECG-feature-to-score mathematical rules. | [PDF](paceval_ECG_Feature_Rules_Research/paceval_ECG_Feature_Rule_Evaluation_Whitepaper_EN.pdf) | [C++](paceval_ECG_Feature_Rules_Research/src/ecg_rules.cpp) |
| [Wearable Signal Scoring](paceval_Wearable_Signal_Scoring/README.md) | Executes configurable non-clinical scores on synthetic photoplethysmography and motion-sensor feature windows. | [PDF](paceval_Wearable_Signal_Scoring/paceval_Wearable_Signal_Scoring_Whitepaper_EN.pdf) | [C++](paceval_Wearable_Signal_Scoring/src/wearable_scoring.cpp) |
| [Pharmacokinetic Rate Kernels](paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels/README.md) | Evaluates synthetic one-compartment drug exposure, concentration transitions, clearance variants and sensitivity functions. It is not prescribing software. | [PDF](paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels/paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels_Whitepaper_EN.pdf) | [C++](paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels/src/pharmacokinetic_kernels.cpp) |
| [Microfluidic Reaction and Transport](paceval_Microfluidic_Reaction_Rate_Expressions/README.md) | Evaluates reversible reaction rates and conservative transport updates in a synthetic continuous-flow microreactor. | [PDF](paceval_Microfluidic_Reaction_Rate_Expressions/paceval_Microfluidic_Reaction_Rate_Expressions_Whitepaper_EN.pdf) | [C++](paceval_Microfluidic_Reaction_Rate_Expressions/src/microfluidic_reactor.cpp) |

## Select a project by technical requirement

| Engineering or research question | Suggested starting points |
|---|---|
| How can an AI agent call a deterministic mathematical tool? | [Technical AI Agents](paceval_Technical_AI_Agents/README.md), [LLM Generated Mathematics](paceval_LLM_Generated_Mathematics/README.md), [Agent Constraint Verification](paceval_Agent_Constraint_Verification_Research/README.md) |
| How can calculations be changed without rewriting application logic? | [Low Code Automation](paceval_Low_Code_Automation/README.md), [CNC Parameter Screening](paceval_CNC_Parameter_Screening/README.md), [Agent-Controlled Production Planning Scores](paceval_Agent_Controlled_Production_Planning_Scores/README.md) |
| How do reusable expressions support physical asset digital twins? | [Battery Equivalent Circuit Twin](paceval_Battery_Twin_Equivalent_Circuit_Functions/README.md), [Heat Pump Twin](paceval_Heat_Pump_Twin/README.md), [Electrolyser Efficiency Surrogates](paceval_Electrolyser_Efficiency_Surrogate_Functions/README.md) |
| What can be scored continuously on an industrial edge device? | [Edge AI Postprocessing](paceval_Edge_AI_Postprocessing/README.md), [Industrial Gateway](paceval_Industrial_Gateway/README.md), [Predictive Maintenance](paceval_Predictive_Maintenance/README.md) |
| Where can mathematical cost functions support industrial scheduling? | [Agent-Controlled Production Planning Scores](paceval_Agent_Controlled_Production_Planning_Scores/README.md), [Industrial Control](paceval_Industrial_Control/README.md), [Inventory Replenishment](paceval_Inventory_Replenishment_Research/README.md) |
| How can a research program compare formula versions and sensitivities? | [Wind Turbine Digital Twin](paceval_Wind_Turbine_Digital_Twin/README.md), [Symbolic System Identification](paceval_Symbolic_System_Identification/README.md), [Parameterized Bulk-Wave Kernels](paceval_Bulk_Wave_Kernels/README.md) |
| How can mathematical kernels be used in scientific catalog studies? | [Fermi 2FLE Spectral Screening Methods](paceval_Fermi_2FLE_Spectral_Screening/README.md), [Fermi 2FLE Real Catalog Spectral Mathematics](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/README.md) |
| How can analytical functions serve quantitative risk and pricing? | [Monte Carlo Pricing](paceval_Monte_Carlo_Pricing/README.md), [Pricing Sensitivities](paceval_Pricing_Sensitivities_Research/README.md), [Portfolio Stress](paceval_Portfolio_Stress/README.md) |
| How can physiology or chemistry formulas be evaluated reproducibly? | [Wearable Signal Scoring](paceval_Wearable_Signal_Scoring/README.md), [Pharmacokinetic Rate Kernels](paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels/README.md), [Microfluidic Reaction and Transport](paceval_Microfluidic_Reaction_Rate_Expressions/README.md) |

## Evidence, reproducibility and interpretation

**What this portfolio inventory verifies.** The core-file export includes one project README, one primary English PDF and one project-specific C++ program for each of the 61 research folders. Source inspection confirms explicit paceval computation creation and result-evaluation calls in each main program. All 61 PDF files were successfully opened for text inspection. The project READMEs describe varying levels of reference calculations, audit scripts, test procedures and numerical outputs.

**What it does not verify.** This catalogue does not itself independently rebuild every project, rerun all 61 scientific workloads, benchmark their performance or revalidate each reported numerical result. The supplied core-file export omits some auxiliary files referenced by project READMEs, including generated figures, numerical results, original datasets or historical proposals. Their availability and integrity should be confirmed in each full project package before claiming end-to-end reproducibility.

**Model and performance boundaries.** Most projects use synthetic, controlled or reduced-order test cases. Successful execution demonstrates a defined computation workflow but does not by itself prove industrial accuracy, generalization, speedup over optimized alternatives, safety certification, energy savings or commercial performance. Independent benchmarking should include the full host pipeline, graph creation and reuse, input preparation, numerical agreement, compiler settings, hardware configuration and repeated measurements.

**Trusted Interval Computation.** TINC is an available paceval feature and appears in selected studies. The presence of an interval check, especially a pointwise check, must not be equated with a global proof over an entire physical or parameter domain. The stated mathematical assumptions and tested ranges remain essential.

**Domain boundaries.** The biomedical projects are not validated diagnostics or prescribing tools. The financial studies do not establish regulatory suitability or fairness. Robotic and industrial control examples are not safety-certified systems. The astronomy and physics studies evaluate specified mathematical models and published data products where declared. They are not evidence for new physical phenomena unless independently supported by the relevant scientific methods.

**Fermi 2FLE provenance.** The [methods pilot](paceval_Fermi_2FLE_Spectral_Screening/README.md) uses transcribed source metadata and synthetic likelihood data. The separate [real-catalog study](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/README.md) states that it evaluates published spectral parameters from the original NASA 2FLE FITS catalog. Neither is presented here as an independent reanalysis of LAT photon events or as a source classification study.

## Reproduce and extend a research demonstrator

1. Read its project README and whitepaper to identify the exact mathematical domain, assumptions, variable units and evidence boundaries.
2. Open the main C++ source and its `src/CMakeLists.txt` where supplied. Examine how expressions are registered and executed by paceval, and what remains in the host implementation.
3. Obtain a compatible original paceval runtime and follow the project-specific build instructions. The source facade files alone may not provide the linked runtime library.
4. Run the example using its declared test data and verify intermediate quantities, constraints, sensitivities and reported outputs with independent references where supplied.
5. Document the platform, SDK version, input provenance, timing methodology and comparison baseline. Validate domain limits before adapting a synthetic example to real equipment or regulated workflows.

## Research development priorities

The greatest value of a cross-industry portfolio is systematic comparison across use cases. Useful follow-up work includes matched native C++ reference benchmarks, common graph-creation and repeated-evaluation measurements, stress testing of formula validity, independent higher-precision references, consistent audit records and practical integration pilots. Strong deployment candidates should also be checked on representative hardware using permitted real datasets. FPGA or other hardware studies should report measured system-level performance and energy rather than extrapolating from assumed graph speedups.

## External research context

These sources provide application context and definitions. They do **not** independently validate any paceval performance claim or numerical result in this portfolio.

- [Model Context Protocol (2026 specification), tool interfaces](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx). Provides the interface context for agent-controlled calculation tools.
- [NIST AI Risk Management Framework and Generative AI Profile](https://www.nist.gov/itl/ai-risk-management-framework). Provides AI governance and verification context.
- [NIST Manufacturing Digital Twin Standards (2024)](https://www.nist.gov/publications/manufacturing-digital-twin-standards) and [NIST Digital Twins Workshops Summary Report (2026)](https://www.nist.gov/publications/digital-twins-workshops-summary-report). Discusses standards, validation, interoperability and uncertainty in manufacturing twins.
- [U.S. Department of Energy, PEM electrolysis technical targets](https://www.energy.gov/cmei/fuels/technical-targets-proton-exchange-membrane-electrolysis). Provides industrial context for electrolyser stack and system efficiency measures.
- [NASA Fermi Science Support Center, Second Fermi-LAT Low Energy Catalog (2FLE)](https://fermi.gsfc.nasa.gov/ssc/data/access/lat/2FLE/) and [2026 2FLE catalog publication](https://doi.org/10.3847/1538-4365/aeb54d). Provide original astrophysical catalog context and source provenance.

## Portfolio status and repository links

**Status:** Research collection inventoried from the supplied November 2026 core-file export. Each study has its own model limitations, independent reference methods and reported results. Consult the project README and scientific paper for any claim more specific than this index.

**Repository:** [paceval/paceval](https://github.com/paceval/paceval) | **Mathematical engine:** [paceval.](https://paceval.com/) | **SDK and developer resources:** [paceval documentation](https://paceval.com/developers/)
