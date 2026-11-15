# paceval. | Industrial Research Portfolio

**101 research demonstrators across 15 industrial and scientific application clusters.**

This directory is a technical catalogue of research applications built around the [paceval. Mathematical Engine](https://paceval.com/). The projects illustrate how explicit mathematical expressions can be prepared as reusable computation objects and evaluated repeatedly within industrial workflows, scientific computing, AI tools, simulation pipelines and decision-support systems.

Each of the 100+ projects has an English README, a main scientific whitepaper in PDF form and at least one C++ source file. The examples range from synthetic feasibility studies to projects reporting execution evidence and independent numerical checks. 

**Portfolio inventory (15 November 2026):** 100+ distinct project directories, project READMEs, main English research PDFs comprising **1,223 pages**, and C++ source programs. 

## How paceval is used

```text
Industrial model, engineering experiment or agent tool request
                          |
                 Validate input and units
                          |
          Define approved, versioned mathematical formulas
                          |
                Create paceval computation objects
                          |
                  Reuse computation handles
                          |
           Evaluate changed inputs, optionally in batches
                          |
              Scores, constraints and numerical results
                          |
              Independent checks and host decisions
```

The paceval SDK accepts mathematical expressions and creates reusable computation objects that can be evaluated with different input values. The precise functions and calculation granularity depend on the project and SDK version. Some studies also document calculations through the paceval MCP service. A documented MCP execution is not the same evidence as a successfully linked and run local C++ executable.

The mathematical engine is an execution layer, not a replacement for the full application. C++ or other host software remains responsible for tasks such as data acquisition, numerical solver iteration, event management, model training, physical simulation state, sensor interfaces, authentication and I/O where these are not implemented as paceval expressions. Projects may encode objectives, piecewise rules, nonlinear physical submodels, sensitivities, calibration functions and mathematical constraint margins in persistent graphs. **The presence of paceval API calls is not evidence that every part of an application executes within paceval.**

For engine details, see the [official paceval API](https://paceval.com/api/), [developer documentation](https://paceval.com/developers/) and [MCP Server project](https://github.com/paceval/paceval/tree/main/examples_sources/MCP_server).

## Explore the 15 research clusters

| Cluster | Projects | Main research focus |
|---|---:|---|
| [1. AI agents, mathematical tools and MCP integration](#cluster-1) | 10 | Explicit mathematical tools, agent contracts, reusable computations, versioned formulas and controlled tool execution. |
| [2. Edge AI, neural expression execution and monitoring](#cluster-2) | 6 | Mathematical inference expressions, sensor analytics, anomaly scoring and edge deployment. |
| [3. Manufacturing, production quality and operations](#cluster-3) | 10 | Mathematical decision support for machining, scheduling, quality, inventory and production workflows. |
| [4. Industrial mathematics, calibration and metrology](#cluster-4) | 4 | Numerical kernels, covariance, calibration, sensitivities, uncertainty and tolerance assessment. |
| [5. Semiconductors, electronic packaging and photonics](#cluster-5) | 5 | Wafer overlay, etch processing, chip packaging, circuit corners and optical thin-film metrology. |
| [6. Chemical engineering, advanced materials and thermal processes](#cluster-6) | 8 | Reaction kinetics, separations, manufacturing process windows, cure models and thermal balances. |
| [7. Digital twins and equipment models](#cluster-7) | 9 | Reusable mathematical submodels embedded in equipment, factory, energy and building simulations. |
| [8. Robotics, grasping and geometric motion verification](#cluster-8) | 5 | Forward kinematics, calibration, trajectory costs, contact constraints and geometric safety margins. |
| [9. Power grids, electrification and storage](#cluster-9) | 6 | Network and microgrid constraints, electrical machine maps, converter losses and asset temperatures. |
| [10. Energy, environmental engineering and meteorological risks](#cluster-10) | 8 | Energy infrastructure and environmental process screening, including forecasts and protective decisions. |
| [11. Industrial control, stability and functional safety](#cluster-11) | 3 | Explicit control objectives, Lyapunov candidate screening and safety instrumented function reliability. |
| [12. Financial services, insurance and quantitative risk](#cluster-12) | 9 | Risk, valuation, pricing and balance-sheet scenario mathematics. |
| [13. Space engineering, astrodynamics and astronomical catalog research](#cluster-13) | 7 | Spacecraft hardware envelopes, orbital models and reproducible astronomical calculations. |
| [14. Fundamental physics and mathematical exploration](#cluster-14) | 5 | Exploratory scientific equations, numerical surfaces and explicitly scoped physical computations. |
| [15. Biomedical engineering, pharmaceutical and biomanufacturing processes](#cluster-15) | 6 | Physiological features, pharmacokinetics, bioreactors, pharmaceutical unit operations and microfluidics. |
| **Total** | **101** | **Unique projects, each assigned to one primary cluster.** |

## All research projects

The project title links to its local README. Adjacent links lead directly to its main English whitepaper and primary C++ source. All **303 catalogue file links** have been checked against the provided project archives. The paths are relative to this directory and are intended for a `README.md` placed in `new projects/TOP+ Industrial Research Projects with paceval/`.

<a id="cluster-1"></a>
### 1. AI agents, mathematical tools and MCP integration (10)

Explicit mathematical tools, agent contracts, reusable computations, versioned formulas and controlled tool execution.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Agent Constraint Verification](paceval_Agent_Constraint_Verification_Research/README.md) | Execute versioned mathematical guards on proposed industrial setpoints. | [PDF](paceval_Agent_Constraint_Verification_Research/paceval_Agent_Constraint_Verification_Whitepaper_EN.pdf) | [C++](paceval_Agent_Constraint_Verification_Research/src/agent_constraints.cpp) |
| [Agent Financial Arithmetic](paceval_Agent_Financial_Arithmetic/README.md) | Serve controlled, versioned financial computations to structured agent requests. | [PDF](paceval_Agent_Financial_Arithmetic/paceval_Agent_Financial_Arithmetic_Whitepaper_EN.pdf) | [C++](paceval_Agent_Financial_Arithmetic/src/financial_agent.cpp) |
| [Agent Simulations](paceval_Agent_Simulations_Research/README.md) | Coordinate selected simulation families with reusable formulas and logged retries. | [PDF](paceval_Agent_Simulations_Research/paceval_Agent_Orchestrated_Mathematical_Simulations_Whitepaper_EN.pdf) | [C++](paceval_Agent_Simulations_Research/src/agent_simulations.cpp) |
| [Auditable AI Chains](paceval_Auditable_AI_Chains/README.md) | Compose reusable mathematical steps with traceable intermediate values. | [PDF](paceval_Auditable_AI_Chains/paceval_Auditable_AI_Chains_Whitepaper_EN.pdf) | [C++](paceval_Auditable_AI_Chains/src/auditable_chains.cpp) |
| [Hypothesis Testing](paceval_Hypothesis_Testing/README.md) | Screen explicitly generated mathematical hypotheses against numerical data. | [PDF](paceval_Hypothesis_Testing/paceval_Hypothesis_Testing_Whitepaper_EN.pdf) | [C++](paceval_Hypothesis_Testing/src/hypothesis_test.cpp) |
| [Industrial Mathematical Models via MCP](paceval_Industrial_MCP_Mathematical_Models/README.md) | Compares remote MCP and local SDK evaluation paths for versioned synthetic volumetric calibration fields. | [PDF](paceval_Industrial_MCP_Mathematical_Models/paceval_Industrial_MCP_Mathematical_Models_Whitepaper_EN.pdf) | [C++](paceval_Industrial_MCP_Mathematical_Models/src/industrial_mcp_paceval.cpp) |
| [Large Quantitative Model Tools](paceval_Large_Quantitative_Model_Tools_Research/README.md) | Provide reusable quantitative formula tools for higher-level assistants. | [PDF](paceval_Large_Quantitative_Model_Tools_Research/paceval_Large_Quantitative_Model_Tools_Whitepaper_EN.pdf) | [C++](paceval_Large_Quantitative_Model_Tools_Research/src/quantitative_tools.cpp) |
| [LLM Generated Mathematics](paceval_LLM_Generated_Mathematics/README.md) | Validate and evaluate generated mathematical expressions under explicit model contracts. | [PDF](paceval_LLM_Generated_Mathematics/paceval_LLM_Math_Expressions_Whitepaper_EN.pdf) | [C++](paceval_LLM_Generated_Mathematics/src/llm_math.cpp) |
| [Low Code Automation](paceval_Low_Code_Automation/README.md) | Reuse approved mathematical models in an automation-style integration workflow. | [PDF](paceval_Low_Code_Automation/paceval_Low_Code_Automation_Whitepaper_EN.pdf) | [C++](paceval_Low_Code_Automation/src/lowcode_math.cpp) |
| [Technical AI Agents](paceval_Technical_AI_Agents/README.md) | Engineering formulas exposed through a typed, unit-checked tool boundary. | [PDF](paceval_Technical_AI_Agents/paceval_Technical_AI_Agents_Whitepaper_EN.pdf) | [C++](paceval_Technical_AI_Agents/src/technical_agent.cpp) |

<a id="cluster-2"></a>
### 2. Edge AI, neural expression execution and monitoring (6)

Mathematical inference expressions, sensor analytics, anomaly scoring and edge deployment.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Edge AI Postprocessing](paceval_Edge_AI_Postprocessing/README.md) | Apply deterministic mathematical scoring to precomputed AI outputs. | [PDF](paceval_Edge_AI_Postprocessing/paceval_Edge_AI_Postprocessing_Whitepaper_EN.pdf) | [C++](paceval_Edge_AI_Postprocessing/src/edge_ai.cpp) |
| [Explainable Anomaly Detection](paceval_Explainable_Anomaly_Detection/README.md) | Evaluate versioned anomaly-scoring formulas on synthetic sensor streams. | [PDF](paceval_Explainable_Anomaly_Detection/paceval_Explainable_Anomaly_Detection_Whitepaper_EN.pdf) | [C++](paceval_Explainable_Anomaly_Detection/src/anomaly_detection.cpp) |
| [Industrial Edge Neural Formula Execution](paceval_Industrial_Edge_Neural_Formula_Research_Expanded/README.md) | Executes two frozen synthetic neural networks as layered and expanded paceval expressions with sensitivities. | [PDF](paceval_Industrial_Edge_Neural_Formula_Research_Expanded/paceval_Industrial_Edge_Neural_Formula_Research_Expanded_EN.pdf) | [C++](paceval_Industrial_Edge_Neural_Formula_Research_Expanded/src/edge_neural_formula.cpp) |
| [Industrial Gateway](paceval_Industrial_Gateway/README.md) | Execute versioned telemetry rules in an offline industrial gateway replay. | [PDF](paceval_Industrial_Gateway/paceval_Industrial_Gateway_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Gateway/src/gateway_rules.cpp) |
| [On Device Expression Runtime](paceval_On_Device_Expression_Runtime/README.md) | Prepare reusable expressions for bounded-input device-side evaluation. | [PDF](paceval_On_Device_Expression_Runtime/paceval_On_Device_Expression_Runtime_Whitepaper_EN.pdf) | [C++](paceval_On_Device_Expression_Runtime/src/on_device_runtime.cpp) |
| [Predictive Maintenance](paceval_Predictive_Maintenance/README.md) | Calculate mathematical vibration-condition features and health scores. | [PDF](paceval_Predictive_Maintenance/paceval_Predictive_Maintenance_Whitepaper_EN.pdf) | [C++](paceval_Predictive_Maintenance/src/predictive_maintenance.cpp) |

<a id="cluster-3"></a>
### 3. Manufacturing, production quality and operations (10)

Mathematical decision support for machining, scheduling, quality, inventory and production workflows.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Agent-Controlled Production Planning Scores](paceval_Agent_Controlled_Production_Planning_Scores/README.md) | Uses persistent scheduling scores and constraint margins for a synthetic job-shop problem. A host scheduler handles combinatorial selection and controlled policy requests. | [PDF](paceval_Agent_Controlled_Production_Planning_Scores/paceval_Agent_Controlled_Production_Planning_Scores_Whitepaper_EN.pdf) | [C++](paceval_Agent_Controlled_Production_Planning_Scores/src/production_planning.cpp) |
| [Auction Bid Formulas](paceval_Auction_Bid_Formulas_Research/README.md) | Evaluate versioned mathematical supplier-bid formulas. | [PDF](paceval_Auction_Bid_Formulas_Research/paceval_Auction_Bid_Formulas_Whitepaper_EN.pdf) | [C++](paceval_Auction_Bid_Formulas_Research/src/auction_bids.cpp) |
| [CNC Parameter Screening](paceval_CNC_Parameter_Screening/README.md) | Screens machining parameters with reusable milling-related formulas, constraint checks and configurable scoring variants. | [PDF](paceval_CNC_Parameter_Screening/paceval_CNC_Parameter_Screening_Whitepaper_EN.pdf) | [C++](paceval_CNC_Parameter_Screening/src/cnc_screening.cpp) |
| [Industrial 3D](paceval_Industrial_3D_Research/README.md) | Generate scientific 3D surfaces from computed industrial mathematical models. | [PDF](paceval_Industrial_3D_Research/paceval_Industrial_3D_Diagrams_Whitepaper_EN.pdf) | [C++](paceval_Industrial_3D_Research/src/industrial_3d.cpp) |
| [Industrial Decision Tree Mathematical Execution](paceval_Decision_Tree_Mathematical_Execution/README.md) | Executes authored decision-tree indicators, mathematical guards, quality scores and evaluation of a deep-tree stress example. | [PDF](paceval_Decision_Tree_Mathematical_Execution/paceval_Decision_Tree_Mathematical_Execution_Whitepaper_EN.pdf) | [C++](paceval_Decision_Tree_Mathematical_Execution/src/decision_tree.cpp) |
| [Inventory Replenishment](paceval_Inventory_Replenishment_Research/README.md) | Compare parameterized inventory replenishment decision rules. | [PDF](paceval_Inventory_Replenishment_Research/paceval_Inventory_Replenishment_Whitepaper_EN.pdf) | [C++](paceval_Inventory_Replenishment_Research/src/inventory_replenishment.cpp) |
| [Machine Tool Chatter Stability Screening](paceval_Machine_Tool_Chatter/README.md) | Evaluates simplified milling stability, chatter-related margins and parameter sensitivity maps. | [PDF](paceval_Machine_Tool_Chatter/paceval_Machine_Tool_Chatter_Whitepaper_EN.pdf) | [C++](paceval_Machine_Tool_Chatter/src/chatter_stability_paceval.cpp) |
| [Material Symbolic Regression](paceval_Material_Symbolic_Regression_Research/README.md) | Evaluate predefined synthetic material-property candidate formulas. | [PDF](paceval_Material_Symbolic_Regression_Research/paceval_Material_Symbolic_Regression_Whitepaper_EN.pdf) | [C++](paceval_Material_Symbolic_Regression_Research/src/material_candidate.cpp) |
| [Quality Scrap Scores](paceval_Quality_Scrap_Scores_Research/README.md) | Apply mathematical quality-risk and inspection-routing scores. | [PDF](paceval_Quality_Scrap_Scores_Research/paceval_Quality_Scrap_Scores_Whitepaper_EN.pdf) | [C++](paceval_Quality_Scrap_Scores_Research/src/quality_scores.cpp) |
| [Symbolic System Identification](paceval_Symbolic_System_Identification/README.md) | Screen candidate nonlinear dynamical-system expressions against trajectories. | [PDF](paceval_Symbolic_System_Identification/paceval_Symbolic_System_Identification_Whitepaper_EN.pdf) | [C++](paceval_Symbolic_System_Identification/src/system_identification.cpp) |

<a id="cluster-4"></a>
### 4. Industrial mathematics, calibration and metrology (4)

Numerical kernels, covariance, calibration, sensitivities, uncertainty and tolerance assessment.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Industrial Matrix Sensor Fusion](paceval_Industrial_Matrix_Sensor_Fusion/README.md) | Executes synthetic SPD matrix factorization, inversion and multichannel sensor-fusion quality scores. | [PDF](paceval_Industrial_Matrix_Sensor_Fusion/paceval_Industrial_Matrix_Sensor_Fusion_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Matrix_Sensor_Fusion/src/matrix_sensor_fusion.cpp) |
| [Industrial Piecewise Calibration](paceval_Industrial_Piecewise_Calibration/README.md) | Executes versioned piecewise calibration expressions, correction terms, derivatives and inspection margins. | [PDF](paceval_Industrial_Piecewise_Calibration/paceval_Industrial_Piecewise_Calibration_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Piecewise_Calibration/src/industrial_calibration.cpp) |
| [Matrix Precision and Quality Monitoring](paceval_Matrix_Precision_Quality/README.md) | Explores matrix precision, covariance-weighted quality mathematics and separately documented MCP and C++ evidence. | [PDF](paceval_Matrix_Precision_Quality/paceval_Matrix_Precision_Quality_Whitepaper_EN.pdf) | [C++](paceval_Matrix_Precision_Quality/src/matrix_precision_paceval.cpp) |
| [Uncertainty-Aware Industrial Metrology](paceval_Uncertainty_Aware_Industrial_Metrology/README.md) | Calculates correlated measurement uncertainty, calibration corrections and guard-banded tolerance decisions. | [PDF](paceval_Uncertainty_Aware_Industrial_Metrology/paceval_Uncertainty_Aware_Industrial_Metrology_Whitepaper_EN.pdf) | [C++](paceval_Uncertainty_Aware_Industrial_Metrology/src/metrology.cpp) |

<a id="cluster-5"></a>
### 5. Semiconductors, electronic packaging and photonics (5)

Wafer overlay, etch processing, chip packaging, circuit corners and optical thin-film metrology.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Advanced Chip Packaging Warpage and Cure](paceval_Advanced_Chip_Packaging_Warpage_Cure/README.md) | Screens idealized cure kinetics, thermal expansion mismatch, warpage and stress sensitivities. | [PDF](paceval_Advanced_Chip_Packaging_Warpage_Cure/paceval_Advanced_Chip_Packaging_Warpage_Cure_Whitepaper_EN.pdf) | [C++](paceval_Advanced_Chip_Packaging_Warpage_Cure/src/warpage_main.cpp) |
| [Integrated Circuit Timing and Leakage Corners](paceval_IC_Timing_Leakage_Corner/README.md) | Screens synthetic timing, leakage power and operating corners using reusable circuit-level formulas. | [PDF](paceval_IC_Timing_Leakage_Corner/paceval_IC_Timing_Leakage_Corner_Whitepaper_EN.pdf) | [C++](paceval_IC_Timing_Leakage_Corner/src/ic_corner_paceval.cpp) |
| [Optical Thin-Film Metrology](paceval_Optical_Thin_Film/README.md) | Evaluates spectral optical thin-film forward models, inverse thickness calculations and uncertainty indicators. | [PDF](paceval_Optical_Thin_Film/paceval_Optical_Thin_Film_Whitepaper_EN.pdf) | [C++](paceval_Optical_Thin_Film/src/optical_film_main.cpp) |
| [Plasma Etch Uniformity and Selectivity](paceval_Plasma_Etch_Uniformity_Selectivity/README.md) | Screens idealized wafer-scale etch-rate fields, selectivity, thickness loss and uniformity margins. | [PDF](paceval_Plasma_Etch_Uniformity_Selectivity/paceval_Plasma_Etch_Uniformity_Selectivity_Whitepaper_EN.pdf) | [C++](paceval_Plasma_Etch_Uniformity_Selectivity/src/plasma_etch.cpp) |
| [Semiconductor Wafer Overlay and Distortion Correction](paceval_Semiconductor_Wafer_Overlay/README.md) | Evaluates synthetic wafer overlay fields, correction models, analytical sensitivities and precision margins. | [PDF](paceval_Semiconductor_Wafer_Overlay/paceval_Semiconductor_Wafer_Overlay_Whitepaper_EN.pdf) | [C++](paceval_Semiconductor_Wafer_Overlay/src/wafer_overlay.cpp) |

<a id="cluster-6"></a>
### 6. Chemical engineering, advanced materials and thermal processes (8)

Reaction kinetics, separations, manufacturing process windows, cure models and thermal balances.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Additive Manufacturing Thermal Process Windows](paceval_Additive_Manufacturing_Thermal_Window/README.md) | Evaluates simplified laser powder bed fusion thermal surrogates, process margins and alternative formula versions. | [PDF](paceval_Additive_Manufacturing_Thermal_Window/paceval_Additive_Manufacturing_Thermal_Window_Whitepaper_EN.pdf) | [C++](paceval_Additive_Manufacturing_Thermal_Window/src/am_thermal_paceval.cpp) |
| [Automatic Discovery of Chemical Kinetic Equations](paceval_Automatic_Discovery_Chemical_Kinetics/README.md) | Evaluates a fixed library of 1,000 chemically constrained kinetic candidates with host-side model selection. | [PDF](paceval_Automatic_Discovery_Chemical_Kinetics/paceval_Automatic_Discovery_Chemical_Kinetics_Whitepaper_EN.pdf) | [C++](paceval_Automatic_Discovery_Chemical_Kinetics/src/kinetic_discovery.cpp) |
| [Chemical Reactor Thermal Stability](paceval_Chemical_Reactor_Thermal_Stability/README.md) | Evaluates non-isothermal reactor heat balances, steady-state candidates and local Jacobian stability conditions. | [PDF](paceval_Chemical_Reactor_Thermal_Stability/paceval_Chemical_Reactor_Thermal_Stability_Whitepaper_EN.pdf) | [C++](paceval_Chemical_Reactor_Thermal_Stability/src/reactor_main.cpp) |
| [Composite Autoclave Cure Windows](paceval_Composite_Cure_Autoclave/README.md) | Models idealized composite cure kinetics, heat-history variables and autoclave process-window constraints. | [PDF](paceval_Composite_Cure_Autoclave/paceval_Composite_Cure_Autoclave_Whitepaper_EN.pdf) | [C++](paceval_Composite_Cure_Autoclave/src/composite_cure_main.cpp) |
| [Distillation Vapor Liquid Equilibrium Kernels](paceval_Distillation_VLE_Kernels/README.md) | Executes binary vapor-liquid equilibrium, reflux, mass-balance, heat-duty and sensitivity expressions. | [PDF](paceval_Distillation_VLE_Kernels/paceval_Distillation_VLE_Kernels_Whitepaper_EN.pdf) | [C++](paceval_Distillation_VLE_Kernels/src/distillation_kernels.cpp) |
| [Heat Exchanger Fouling and Thermal Performance](paceval_Heat_Exchanger_Fouling/README.md) | Screens simplified heat-transfer, fouling-resistance and thermal-performance models over operating scenarios. | [PDF](paceval_Heat_Exchanger_Fouling/paceval_Heat_Exchanger_Fouling_Whitepaper_EN.pdf) | [C++](paceval_Heat_Exchanger_Fouling/src/heat_exchanger_paceval.cpp) |
| [Industrial Furnace Energy and Emission Balances](paceval_Industrial_Furnace_Energy/README.md) | Evaluates fuel input, useful heat, furnace losses, waste-heat recovery and modeled emissions margins. | [PDF](paceval_Industrial_Furnace_Energy/paceval_Industrial_Furnace_Energy_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Furnace_Energy/src/industrial_furnace_paceval.cpp) |
| [Injection Molding Rheology and Process Windows](paceval_Injection_Molding_Rheology/README.md) | Evaluates simplified temperature-dependent polymer viscosity, pressure and shear process constraints. | [PDF](paceval_Injection_Molding_Rheology/paceval_Injection_Molding_Rheology_Whitepaper_EN.pdf) | [C++](paceval_Injection_Molding_Rheology/src/injection_molding_paceval.cpp) |

<a id="cluster-7"></a>
### 7. Digital twins and equipment models (9)

Reusable mathematical submodels embedded in equipment, factory, energy and building simulations.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Battery Charging and Aging Terms](paceval_Battery_Charging_Aging/README.md) | Screens tariff-aware charging schedules using state-of-charge transitions, versioned cost expressions and explicitly uncalibrated aging surrogates. | [PDF](paceval_Battery_Charging_Aging/paceval_Battery_Charging_Aging_Whitepaper_EN.pdf) | [C++](paceval_Battery_Charging_Aging/src/battery_charging_aging.cpp) |
| [Battery Equivalent Circuit Twin](paceval_Battery_Twin_Equivalent_Circuit_Functions/README.md) | Evaluates synthetic 1RC and 2RC circuit equations for voltage, state of charge, energy and thermal behavior. | [PDF](paceval_Battery_Twin_Equivalent_Circuit_Functions/paceval_Battery_Twin_Equivalent_Circuit_Functions_Whitepaper_EN.pdf) | [C++](paceval_Battery_Twin_Equivalent_Circuit_Functions/src/battery_twin.cpp) |
| [Building Thermal Twin](paceval_Building_Thermal_Twin/README.md) | Evaluates synthetic building heat balances, forecast functions, calibration losses and analytical sensitivities. | [PDF](paceval_Building_Thermal_Twin/paceval_Building_Thermal_Twin_Whitepaper_EN.pdf) | [C++](paceval_Building_Thermal_Twin/src/thermal_twin.cpp) |
| [Digital Twins Simulation](paceval_Digital_Twins_Simulation/README.md) | Evaluate reusable mathematical submodels in a synthetic thermal digital twin. | [PDF](paceval_Digital_Twins_Simulation/paceval_Digital_Twins_Whitepaper_EN.pdf) | [C++](paceval_Digital_Twins_Simulation/src/digital_twin.cpp) |
| [Electrolyser Efficiency Surrogates](paceval_Electrolyser_Efficiency_Surrogate_Functions/README.md) | Screens synthetic PEM electrolyser stack voltage, hydrogen production, system efficiency and operating constraints with explicit formula versions. | [PDF](paceval_Electrolyser_Efficiency_Surrogate_Functions/paceval_Electrolyser_Efficiency_Surrogate_Functions_Whitepaper_EN.pdf) | [C++](paceval_Electrolyser_Efficiency_Surrogate_Functions/src/electrolyser_twin.cpp) |
| [Factory Line Digital Twin](paceval_Factory_Line_Digital_Twin/README.md) | Couples a synthetic discrete-event line simulation to reusable station-time formulas, quality, energy and KPI computations. | [PDF](paceval_Factory_Line_Digital_Twin/paceval_Factory_Line_Digital_Twin_Whitepaper_EN.pdf) | [C++](paceval_Factory_Line_Digital_Twin/src/factory_line_twin.cpp) |
| [Heat Pump Twin](paceval_Heat_Pump_Twin/README.md) | Evaluates synthetic coefficient-of-performance maps, heating power, electricity use, sensitivities and cost expressions. | [PDF](paceval_Heat_Pump_Twin/paceval_Heat_Pump_Twin_Whitepaper_EN.pdf) | [C++](paceval_Heat_Pump_Twin/src/heat_pump_twin.cpp) |
| [Hydraulic Pump Twin](paceval_Hydraulic_Pump_Twin/README.md) | Evaluates synthetic pump, efficiency, power and piping-system functions across operating conditions. | [PDF](paceval_Hydraulic_Pump_Twin/paceval_Hydraulic_Pump_Twin_Whitepaper_EN.pdf) | [C++](paceval_Hydraulic_Pump_Twin/src/hydraulic_pump_twin.cpp) |
| [Wind Turbine Digital Twin](paceval_Wind_Turbine_Digital_Twin/README.md) | Evaluates rotor coefficient maps, aerodynamic power, torque, thrust, sensitivities and model state updates on synthetic inputs. | [PDF](paceval_Wind_Turbine_Digital_Twin/paceval_Wind_Turbine_Digital_Twin_Whitepaper_EN.pdf) | [C++](paceval_Wind_Turbine_Digital_Twin/src/wind_turbine_twin.cpp) |

<a id="cluster-8"></a>
### 8. Robotics, grasping and geometric motion verification (5)

Forward kinematics, calibration, trajectory costs, contact constraints and geometric safety margins.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Reconfigurable Robotic Trajectory Costs](paceval_Reconfigurable_Robotic_Trajectory_Costs/README.md) | Compare complete candidate trajectories under changeable cost formulas. | [PDF](paceval_Reconfigurable_Robotic_Trajectory_Costs/paceval_Reconfigurable_Robotic_Trajectory_Costs_Whitepaper_EN.pdf) | [C++](paceval_Reconfigurable_Robotic_Trajectory_Costs/src/trajectory_costs.cpp) |
| [Robot Calibration](paceval_Robot_Calibration/README.md) | Evaluates 3D robot kinematic calibration residuals and analytical model variations. | [PDF](paceval_Robot_Calibration/paceval_Robot_Calibration_Whitepaper_EN.pdf) | [C++](paceval_Robot_Calibration/src/robot_calibration.cpp) |
| [Robot Swept Volume and Collision Verification](paceval_Robot_Swept_Volume_Collision_Verification/README.md) | Screens simplified swept-volume geometry, distance constraints and candidate trajectory collision margins. | [PDF](paceval_Robot_Swept_Volume_Collision_Verification/paceval_Robot_Swept_Volume_Collision_Verification_Whitepaper_EN.pdf) | [C++](paceval_Robot_Swept_Volume_Collision_Verification/src/robot_continuous_main.cpp) |
| [Robotic Grasp Contact and Wrench Mathematics](paceval_Robotic_Grasp_Wrench/README.md) | Evaluates modeled contact forces, wrench balance, friction-cone margins and grasp feasibility indicators. | [PDF](paceval_Robotic_Grasp_Wrench/paceval_Robotic_Grasp_Wrench_Whitepaper_EN.pdf) | [C++](paceval_Robotic_Grasp_Wrench/src/robot_grasp_wrench_paceval.cpp) |
| [Robotics Trajectory Planning](paceval_Robotics_Trajectory_Planning/README.md) | Evaluate planar robot kinematics, trajectory scores and simplified constraints. | [PDF](paceval_Robotics_Trajectory_Planning/paceval_Robotic_Trajectories_Whitepaper_EN.pdf) | [C++](paceval_Robotics_Trajectory_Planning/src/robotics.cpp) |

<a id="cluster-9"></a>
### 9. Power grids, electrification and storage (6)

Network and microgrid constraints, electrical machine maps, converter losses and asset temperatures.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Demand Response](paceval_Demand_Response/README.md) | Evaluate versioned demand-response incentive and scheduling formulas. | [PDF](paceval_Demand_Response/paceval_Demand_Response_Whitepaper_EN.pdf) | [C++](paceval_Demand_Response/src/demand_response.cpp) |
| [Distribution Grid Hosting Capacity](paceval_Distribution_Grid_Hosting_Capacity/README.md) | Evaluates balanced feeder power-flow equations and operating margins around a host-controlled AC solver. | [PDF](paceval_Distribution_Grid_Hosting_Capacity/paceval_Distribution_Grid_Hosting_Capacity_Whitepaper_EN.pdf) | [C++](paceval_Distribution_Grid_Hosting_Capacity/src/grid_hosting.cpp) |
| [Electric Motor Efficiency and Field Weakening](paceval_Electric_Motor_Efficiency_Field_Weakening/README.md) | Evaluates steady-state IPMSM torque, electrical limits, efficiency and flux-weakening operating maps. | [PDF](paceval_Electric_Motor_Efficiency_Field_Weakening/paceval_Electric_Motor_Efficiency_Field_Weakening_Whitepaper_EN.pdf) | [C++](paceval_Electric_Motor_Efficiency_Field_Weakening/src/motor_main.cpp) |
| [Microgrid and Storage Dispatch](paceval_Microgrid_Storage_Dispatch/README.md) | Evaluates multi-period storage state, microgrid energy-balance, reserve and cost functions. | [PDF](paceval_Microgrid_Storage_Dispatch/paceval_Microgrid_Storage_Dispatch_Whitepaper_EN.pdf) | [C++](paceval_Microgrid_Storage_Dispatch/src/microgrid_main.cpp) |
| [Power Electronics Inverter Electrothermal Optimization](paceval_Inverter_Electrothermal_Optimization/README.md) | Couples synthetic SiC switch conduction and switching losses to junction-temperature screening. | [PDF](paceval_Inverter_Electrothermal_Optimization/paceval_Inverter_Electrothermal_Optimization_Whitepaper_EN.pdf) | [C++](paceval_Inverter_Electrothermal_Optimization/src/inverter_twin.cpp) |
| [Transformer Hotspot and Insulation Aging](paceval_Transformer_Hotspot_Insulation_Aging/README.md) | Evaluates synthetic transformer thermal transients, winding hotspot, relative aging and overload margins. | [PDF](paceval_Transformer_Hotspot_Insulation_Aging/paceval_Transformer_Hotspot_Insulation_Aging_Whitepaper_EN.pdf) | [C++](paceval_Transformer_Hotspot_Insulation_Aging/src/transformer_main.cpp) |

<a id="cluster-10"></a>
### 10. Energy, environmental engineering and meteorological risks (8)

Energy infrastructure and environmental process screening, including forecasts and protective decisions.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Carbon Capture Absorber and Regenerator Windows](paceval_Carbon_Capture_Process_Windows/README.md) | Screens simplified CO2 absorption and solvent-regeneration operating balances, energy duties and margins. | [PDF](paceval_Carbon_Capture_Process_Windows/paceval_Carbon_Capture_Process_Windows_Whitepaper_EN.pdf) | [C++](paceval_Carbon_Capture_Process_Windows/src/carbon_capture_main.cpp) |
| [Compressed Air Leakage and Energy](paceval_Compressed_Air_Leak_Energy/README.md) | Calculates pressure-dependent air leakage, compressor energy impacts and simplified remediation economics. | [PDF](paceval_Compressed_Air_Leak_Energy/paceval_Compressed_Air_Leak_Energy_Whitepaper_EN.pdf) | [C++](paceval_Compressed_Air_Leak_Energy/src/compressed_air_main.cpp) |
| [District Heating Thermal Dispatch](paceval_District_Heating_Thermal_Dispatch/README.md) | Screens pipeline and heating-network temperature, heat-flow and operating constraint functions. | [PDF](paceval_District_Heating_Thermal_Dispatch/paceval_District_Heating_Thermal_Dispatch_Whitepaper_EN.pdf) | [C++](paceval_District_Heating_Thermal_Dispatch/src/district_heating_paceval.cpp) |
| [Fusion Plasma Control](paceval_Fusion_Plasma_Control/README.md) | Evaluate explicitly defined plasma diagnostic and control-related functions. | [PDF](paceval_Fusion_Plasma_Control/paceval_Fusion_Diagnostics_Whitepaper_EN.pdf) | [C++](paceval_Fusion_Plasma_Control/src/fusion.cpp) |
| [Hydrogen Compression and Storage Thermal Envelopes](paceval_Hydrogen_Compression_Storage/README.md) | Evaluates idealized hydrogen compression, storage thermodynamics and temperature or pressure constraints. | [PDF](paceval_Hydrogen_Compression_Storage/paceval_Hydrogen_Compression_Storage_Whitepaper_EN.pdf) | [C++](paceval_Hydrogen_Compression_Storage/src/hydrogen_kernels.cpp) |
| [Meteorological Ensemble Decision Kernels](paceval_Meteorological_Ensemble_Decision_Kernels/README.md) | Evaluates synthetic site-level rainfall, wind and frost risk probabilities and economic action thresholds. | [PDF](paceval_Meteorological_Ensemble_Decision_Kernels/paceval_Meteorological_Ensemble_Decision_Kernels_Whitepaper_EN.pdf) | [C++](paceval_Meteorological_Ensemble_Decision_Kernels/src/weather_kernels.cpp) |
| [Wastewater Nitrification and Aeration Energy](paceval_Wastewater_Nitrification_Aeration/README.md) | Evaluates ammonium-conversion, oxygen-transfer and aeration-energy expressions under synthetic loads. | [PDF](paceval_Wastewater_Nitrification_Aeration/paceval_Wastewater_Nitrification_Aeration_Whitepaper_EN.pdf) | [C++](paceval_Wastewater_Nitrification_Aeration/src/wastewater_paceval.cpp) |
| [Wind Farm Loss Functions](paceval_Wind_Farm_Loss_Functions/README.md) | Evaluate simplified wake-loss and turbine-power functions. | [PDF](paceval_Wind_Farm_Loss_Functions/paceval_Wind_Farm_Loss_Functions_Whitepaper_EN.pdf) | [C++](paceval_Wind_Farm_Loss_Functions/src/wind_farm.cpp) |

<a id="cluster-11"></a>
### 11. Industrial control, stability and functional safety (3)

Explicit control objectives, Lyapunov candidate screening and safety instrumented function reliability.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Industrial Control](paceval_Industrial_Control/README.md) | Evaluates mathematical objective terms, state constraints and margins in an offline industrial control study. | [PDF](paceval_Industrial_Control/paceval_Industrial_Control_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Control/src/industrial_control.cpp) |
| [Nonlinear Control and Lyapunov Screening](paceval_Nonlinear_Control_Lyapunov_Screening/README.md) | Tests candidate Lyapunov functions, derivative conditions and sampled stability margins for chosen models. | [PDF](paceval_Nonlinear_Control_Lyapunov_Screening/paceval_Nonlinear_Control_Lyapunov_Screening_Whitepaper_EN.pdf) | [C++](paceval_Nonlinear_Control_Lyapunov_Screening/src/nonlinear_control_main.cpp) |
| [Safety Instrumented System Proof Test Reliability](paceval_SIS_Proof_Test_Reliability/README.md) | Screens synthetic failure-rate and proof-test assumptions to calculate safety-function reliability indicators. | [PDF](paceval_SIS_Proof_Test_Reliability/paceval_SIS_Proof_Test_Reliability_Whitepaper_EN.pdf) | [C++](paceval_SIS_Proof_Test_Reliability/src/sis_reliability.cpp) |

<a id="cluster-12"></a>
### 12. Financial services, insurance and quantitative risk (9)

Risk, valuation, pricing and balance-sheet scenario mathematics.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Asset Liability Management and Interest Rate Stress](paceval_ALM_Interest_Rate_Stress/README.md) | Reprices synthetic asset and liability cash flows under interest-rate scenarios and examines duration, convexity and mismatch. | [PDF](paceval_ALM_Interest_Rate_Stress/paceval_ALM_Interest_Rate_Stress_Whitepaper_EN.pdf) | [C++](paceval_ALM_Interest_Rate_Stress/src/alm_stress.cpp) |
| [Counterparty Exposure](paceval_Counterparty_Exposure_Research/README.md) | Evaluate pointwise counterparty-exposure calculation functions. | [PDF](paceval_Counterparty_Exposure_Research/paceval_Counterparty_Exposure_Whitepaper_EN.pdf) | [C++](paceval_Counterparty_Exposure_Research/src/counterparty_exposure.cpp) |
| [Credit Risk Scorecard](paceval_Credit_Risk_Scorecard_Research/README.md) | Evaluate transparent synthetic credit-scorecard formulas. | [PDF](paceval_Credit_Risk_Scorecard_Research/paceval_Credit_Risk_Scorecard_Whitepaper_EN.pdf) | [C++](paceval_Credit_Risk_Scorecard_Research/src/credit_scorecard.cpp) |
| [Insurance Tariffs](paceval_Insurance_Tariffs/README.md) | Demonstrate versioned synthetic insurance tariff calculations. | [PDF](paceval_Insurance_Tariffs/paceval_Insurance_Tariffs_Whitepaper_EN.pdf) | [C++](paceval_Insurance_Tariffs/src/insurance_tariffs.cpp) |
| [Intraday Risk](paceval_Intraday_Risk_Research/README.md) | Replay versioned intraday market-risk functions. | [PDF](paceval_Intraday_Risk_Research/paceval_Intraday_Risk_Whitepaper_EN.pdf) | [C++](paceval_Intraday_Risk_Research/src/intraday_risk.cpp) |
| [Monte Carlo Pricing](paceval_Monte_Carlo_Pricing/README.md) | Reuse option payoff formulas inside a host-driven Monte Carlo workload. | [PDF](paceval_Monte_Carlo_Pricing/paceval_Monte_Carlo_Pricing_Whitepaper_EN.pdf) | [C++](paceval_Monte_Carlo_Pricing/src/monte_carlo_pricing.cpp) |
| [Portfolio Stress](paceval_Portfolio_Stress/README.md) | Evaluate synthetic factor stress scenarios and portfolio P&L expressions. | [PDF](paceval_Portfolio_Stress/paceval_Portfolio_Stress_Whitepaper_EN.pdf) | [C++](paceval_Portfolio_Stress/src/portfolio_stress.cpp) |
| [Pricing Sensitivities](paceval_Pricing_Sensitivities_Research/README.md) | Evaluate option pricing and analytical sensitivity formulas. | [PDF](paceval_Pricing_Sensitivities_Research/paceval_Pricing_Formula_Sensitivities_Whitepaper_EN.pdf) | [C++](paceval_Pricing_Sensitivities_Research/src/pricing_sensitivities.cpp) |
| [Trading Indicators](paceval_Trading_Indicators_Research/README.md) | Evaluate mathematical quantitative indicator composites on price-bar data. | [PDF](paceval_Trading_Indicators_Research/paceval_Interchangeable_Trading_Indicators_Whitepaper_EN.pdf) | [C++](paceval_Trading_Indicators_Research/src/trading_indicators.cpp) |

<a id="cluster-13"></a>
### 13. Space engineering, astrodynamics and astronomical catalog research (7)

Spacecraft hardware envelopes, orbital models and reproducible astronomical calculations.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Electric Propulsion](paceval_Electric_Propulsion_Research/README.md) | Evaluate parameterized analytical electric-thruster performance maps. | [PDF](paceval_Electric_Propulsion_Research/paceval_Electric_Propulsion_Whitepaper_EN.pdf) | [C++](paceval_Electric_Propulsion_Research/src/electric_propulsion.cpp) |
| [Fermi 2FLE Real Catalog Spectral Mathematics](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/README.md) | Re-evaluates published spectral fit parameters for 450 NASA 2FLE catalog sources. It does not reprocess LAT photon events or establish new source classes. | [PDF](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/paceval_Fermi_2FLE_Real_Catalog_Whitepaper_EN.pdf) | [C++](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/src/fermi_real_catalog.cpp) |
| [Fermi 2FLE Spectral Screening Methods](paceval_Fermi_2FLE_Spectral_Screening/README.md) | Combines transcribed 2FLE source metadata with distinctly synthetic spectral and likelihood inputs to test reusable screening mathematics. | [PDF](paceval_Fermi_2FLE_Spectral_Screening/paceval_Fermi_2FLE_Spectral_Screening_Whitepaper_EN.pdf) | [C++](paceval_Fermi_2FLE_Spectral_Screening/src/fermi_2fle_demo.cpp) |
| [Gravitational Inversion](paceval_Gravitational_Inversion_Research/README.md) | Evaluate gravitational-field functions and inversion sensitivities. | [PDF](paceval_Gravitational_Inversion_Research/paceval_Gravitational_Inversion_Whitepaper_EN.pdf) | [C++](paceval_Gravitational_Inversion_Research/src/gravity_inversion.cpp) |
| [Orbit Parameter Sweeps](paceval_Orbit_Parameter_Sweeps_Research/README.md) | Calculate orbital acceleration components in host-driven orbit propagation. | [PDF](paceval_Orbit_Parameter_Sweeps_Research/paceval_Orbit_Parameter_Sweeps_Whitepaper_EN.pdf) | [C++](paceval_Orbit_Parameter_Sweeps_Research/src/orbit_sweeps.cpp) |
| [Satellite Attitude Actuator Torque and Momentum](paceval_Satellite_Attitude_Actuator/README.md) | Evaluates synthetic three-axis reaction-wheel torque, momentum, disturbance and maneuver margins. | [PDF](paceval_Satellite_Attitude_Actuator/paceval_Satellite_Attitude_Actuator_Whitepaper_EN.pdf) | [C++](paceval_Satellite_Attitude_Actuator/src/satellite_attitude_paceval.cpp) |
| [Space Transfer Screening](paceval_Space_Transfer_Screening/README.md) | Screens idealized two-body orbital transfers, impulsive velocity budgets, transfer times and rocket-equation propellant requirements. | [PDF](paceval_Space_Transfer_Screening/paceval_Space_Transfer_Screening_Whitepaper_EN.pdf) | [C++](paceval_Space_Transfer_Screening/src/space_transfer.cpp) |

<a id="cluster-14"></a>
### 14. Fundamental physics and mathematical exploration (5)

Exploratory scientific equations, numerical surfaces and explicitly scoped physical computations.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Collider](paceval_Collider_Research/README.md) | Execute selected collider-inspired mathematical analysis kernels. | [PDF](paceval_Collider_Research/paceval_Collider_Research_Whitepaper_EN.pdf) | [C++](paceval_Collider_Research/src/collider.cpp) |
| [Conservation Law Candidates](paceval_Conservation_Law_Candidates/README.md) | Checks proposed mathematical invariants and time-derivative residuals for specified dynamical models. Candidate screening is not a proof of a universal physical law. | [PDF](paceval_Conservation_Law_Candidates/paceval_Conservation_Law_Candidates_Whitepaper_EN.pdf) | [C++](paceval_Conservation_Law_Candidates/src/conservation_law_candidates.cpp) |
| [Extreme-Length Analytic Terrain](paceval_Extreme_Analytic_Terrain/README.md) | Creates and samples exceptionally long analytical terrain expressions to investigate reusable expression execution and numerical surfaces. | [PDF](paceval_Extreme_Analytic_Terrain/paceval_Extreme_Analytic_Terrain_Whitepaper_EN.pdf) | [C++](paceval_Extreme_Analytic_Terrain/src/extreme_terrain.cpp) |
| [Parameterized Bulk-Wave Kernels](paceval_Bulk_Wave_Kernels/README.md) | Executes parameterized wave operators, manufactured forcing, diagnostic functions and sensitivities in a host-integrated one-dimensional model. | [PDF](paceval_Bulk_Wave_Kernels/paceval_Bulk_Wave_Kernels_Whitepaper_EN.pdf) | [C++](paceval_Bulk_Wave_Kernels/src/bulk_wave_kernels.cpp) |
| [Quantum](paceval_Quantum_Research/README.md) | Evaluate classical calibration and circuit-expectation mathematics. | [PDF](paceval_Quantum_Research/paceval_Quantum_Research_Whitepaper_EN.pdf) | [C++](paceval_Quantum_Research/src/quantum.cpp) |

<a id="cluster-15"></a>
### 15. Biomedical engineering, pharmaceutical and biomanufacturing processes (6)

Physiological features, pharmacokinetics, bioreactors, pharmaceutical unit operations and microfluidics.

| Research project | Mathematical scope | Whitepaper | C++ source |
|---|---|---|---|
| [Biomanufacturing Process Analytical Technology](paceval_Biomanufacturing_PAT/README.md) | Evaluates synthetic fed-batch growth, oxygen uptake, transfer capacity and advisory monitoring functions. | [PDF](paceval_Biomanufacturing_PAT/paceval_Biomanufacturing_PAT_Whitepaper_EN.pdf) | [C++](paceval_Biomanufacturing_PAT/src/biomanufacturing_pat.cpp) |
| [Continuous Pharmaceutical Granulation and Drying](paceval_Continuous_Pharma_Granulation_Drying/README.md) | Evaluates simplified wet-granulation and drying mass, moisture and operating-window functions. | [PDF](paceval_Continuous_Pharma_Granulation_Drying/paceval_Continuous_Pharma_Granulation_Drying_Whitepaper_EN.pdf) | [C++](paceval_Continuous_Pharma_Granulation_Drying/src/granulation_drying_main.cpp) |
| [ECG Feature Rules](paceval_ECG_Feature_Rules_Research/README.md) | Evaluate synthetic ECG-feature-to-score mathematical rules. | [PDF](paceval_ECG_Feature_Rules_Research/paceval_ECG_Feature_Rule_Evaluation_Whitepaper_EN.pdf) | [C++](paceval_ECG_Feature_Rules_Research/src/ecg_rules.cpp) |
| [Microfluidic Reaction and Transport](paceval_Microfluidic_Reaction_Rate_Expressions/README.md) | Evaluates reversible reaction rates and conservative transport updates in a synthetic continuous-flow microreactor. | [PDF](paceval_Microfluidic_Reaction_Rate_Expressions/paceval_Microfluidic_Reaction_Rate_Expressions_Whitepaper_EN.pdf) | [C++](paceval_Microfluidic_Reaction_Rate_Expressions/src/microfluidic_reactor.cpp) |
| [Pharmacokinetic Rate Kernels](paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels/README.md) | Evaluates synthetic one-compartment drug exposure, concentration transitions, clearance variants and sensitivity functions. It is not prescribing software. | [PDF](paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels/paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels_Whitepaper_EN.pdf) | [C++](paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels/src/pharmacokinetic_kernels.cpp) |
| [Wearable Signal Scoring](paceval_Wearable_Signal_Scoring/README.md) | Executes configurable non-clinical scores on synthetic photoplethysmography and motion-sensor feature windows. | [PDF](paceval_Wearable_Signal_Scoring/paceval_Wearable_Signal_Scoring_Whitepaper_EN.pdf) | [C++](paceval_Wearable_Signal_Scoring/src/wearable_scoring.cpp) |

## Choose a research starting point

| Research objective | Suggested starting projects |
|---|---|
| Use AI agents for approved, auditable mathematical operations | [Technical AI Agents](paceval_Technical_AI_Agents/README.md), [Industrial Mathematical Models via MCP](paceval_Industrial_MCP_Mathematical_Models/README.md), [Agent Constraint Verification](paceval_Agent_Constraint_Verification_Research/README.md) |
| Reuse frozen neural networks or decision rules as expressions | [Industrial Edge Neural Formula Execution](paceval_Industrial_Edge_Neural_Formula_Research_Expanded/README.md), [Industrial Decision Tree Mathematical Execution](paceval_Decision_Tree_Mathematical_Execution/README.md) |
| Evaluate full matrix mathematics, calibration and tolerances | [Industrial Matrix Sensor Fusion](paceval_Industrial_Matrix_Sensor_Fusion/README.md), [Industrial Piecewise Calibration](paceval_Industrial_Piecewise_Calibration/README.md), [Uncertainty-Aware Industrial Metrology](paceval_Uncertainty_Aware_Industrial_Metrology/README.md) |
| Study semiconductor fab and chip packaging mathematics | [Semiconductor Wafer Overlay and Distortion Correction](paceval_Semiconductor_Wafer_Overlay/README.md), [Plasma Etch Uniformity and Selectivity](paceval_Plasma_Etch_Uniformity_Selectivity/README.md), [Advanced Chip Packaging Warpage and Cure](paceval_Advanced_Chip_Packaging_Warpage_Cure/README.md) |
| Screen industrial thermal, kinetic and manufacturing processes | [Additive Manufacturing Thermal Process Windows](paceval_Additive_Manufacturing_Thermal_Window/README.md), [Chemical Reactor Thermal Stability](paceval_Chemical_Reactor_Thermal_Stability/README.md), [Automatic Discovery of Chemical Kinetic Equations](paceval_Automatic_Discovery_Chemical_Kinetics/README.md) |
| Model electrical power equipment and network constraints | [Power Electronics Inverter Electrothermal Optimization](paceval_Inverter_Electrothermal_Optimization/README.md), [Distribution Grid Hosting Capacity](paceval_Distribution_Grid_Hosting_Capacity/README.md), [Transformer Hotspot and Insulation Aging](paceval_Transformer_Hotspot_Insulation_Aging/README.md) |
| Assess robotic geometry, calibration and grasp forces | [Robot Calibration](paceval_Robot_Calibration/README.md), [Robot Swept Volume and Collision Verification](paceval_Robot_Swept_Volume_Collision_Verification/README.md), [Robotic Grasp Contact and Wrench Mathematics](paceval_Robotic_Grasp_Wrench/README.md) |
| Evaluate weather-risk and environmental process decisions | [Meteorological Ensemble Decision Kernels](paceval_Meteorological_Ensemble_Decision_Kernels/README.md), [Wastewater Nitrification and Aeration Energy](paceval_Wastewater_Nitrification_Aeration/README.md), [Carbon Capture Absorber and Regenerator Windows](paceval_Carbon_Capture_Process_Windows/README.md) |
| Investigate safety and nonlinear controller margins | [Safety Instrumented System Proof Test Reliability](paceval_SIS_Proof_Test_Reliability/README.md), [Nonlinear Control and Lyapunov Screening](paceval_Nonlinear_Control_Lyapunov_Screening/README.md) |
| Run financial cash-flow and risk scenario mathematics | [Asset Liability Management and Interest Rate Stress](paceval_ALM_Interest_Rate_Stress/README.md), [Monte Carlo Pricing](paceval_Monte_Carlo_Pricing/README.md), [Portfolio Stress](paceval_Portfolio_Stress/README.md) |
| Use reusable mathematics for spacecraft actuators or astronomical catalogs | [Satellite Attitude Actuator Torque and Momentum](paceval_Satellite_Attitude_Actuator/README.md), [Orbit Parameter Sweeps](paceval_Orbit_Parameter_Sweeps_Research/README.md), [Fermi 2FLE Real Catalog Spectral Mathematics](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/README.md) |
| Explore life-science and pharmaceutical process mathematics | [Biomanufacturing Process Analytical Technology](paceval_Biomanufacturing_PAT/README.md), [Continuous Pharmaceutical Granulation and Drying](paceval_Continuous_Pharma_Granulation_Drying/README.md), [Microfluidic Reaction and Transport](paceval_Microfluidic_Reaction_Rate_Expressions/README.md) |

## Scientific evidence and limits

**Mathematical execution evidence.** The principal C++ sources were inspected for paceval computation-creation and evaluation integration. Individual projects provide different levels of evidence, ranging from source-only research implementations to successful local SDK executions, remote MCP evaluations, synthetic test results and independently checked numeric references. Read the corresponding project README and whitepaper to determine what has actually been executed. This portfolio index does not establish that all applications have been compiled, run and independently replicated.

**Scope of the models.** Most studies use synthetic parameters or deliberately simplified physical models. A verified formula value is not the same as validated field performance, a qualified manufacturing process, a certified controller or measured commercial benefit. Results from catalog astrophysics studies do not imply reprocessing of raw detector events, and sampled stability checks do not prove global dynamical stability.

**Precision and uncertainty.** Trusted Interval Computation can support numerical reliability for specified computations. It is not automatically an enclosure of physical measurement uncertainty or a mathematical proof over all inputs. Metrology, numerical linear algebra, nonlinear optimization and physical modeling require their own uncertainty and validation assumptions.

**Benchmark rigor.** Any comparison of paceval with optimized native C++, scientific numerical libraries or alternative runtimes must specify matched algorithms, comparable numerical precision, compiler options, hardware, complete pipeline timing, graph-creation cost, reuse frequency, memory use and repeated trials. There are no portfolio-wide claims of measured acceleration or energy savings in this index.

**Sector responsibilities.** Industrial safety studies are not IEC 61511 certification. Medical and pharmaceutical studies are not validated clinical or GMP systems. Finance and insurance examples are not regulatory compliance assessments. Space and robotics demonstrations are not flight-qualified software or validated safety interlocks. Decision tools require domain-specific authorization, calibration, field data and independent assessment.

## Reproduce or extend a project

1. Begin with the linked project README and whitepaper to identify mathematical assumptions, variable units, input provenance, and the documented status of executions and numerical checks.
2. Review the C++ source and any local manifests, build files, test vectors, generated formulas and independent validation scripts. Some supplementary folders are absent from these reduced ZIP exports and may exist only in the complete project repository.
3. Provide the compatible original paceval SDK and runtime when required. Some projects use remote paceval MCP; follow their own execution requirements. A bundled C/C++ header is not necessarily a replacement for a required runtime library.
4. Run the project in its specified environment. Distinguish a source-code inspection, compilation, linking, execution and independent numerical verification. Record all relevant versions and assumptions.
5. For benchmarks, compare the same mathematical work with suitable reference implementations on the same hardware. Report end-to-end cost alongside isolated formula-evaluation cost and numerical differences.

## Research priorities across the portfolio

A useful next phase is a common, automated verification harness for repeated mathematical graphs. It should compare native and paceval results at the same inputs and precision, include boundary and ill-conditioned cases, and record SDK versions and execution status. Selected projects should also be tested on representative real data when the corresponding datasets, licenses and industrial permissions are available.

The new semiconductor, power-system, process-engineering, metrology and meteorology studies provide suitable candidates for such cross-project comparisons. Their case studies should remain independent: a successful synthetic computation or good theoretical fit is a reason to benchmark, not a substitute for an experimentally established advantage.

## External scientific and engineering context

These external references describe the underlying industry problems and established verification principles. They do not validate or endorse the paceval results in this repository.

- [paceval. Mathematical Engine](https://paceval.com/) and [official API documentation](https://paceval.com/api/). These describe reusable expression execution and local SDK interfaces.
- [NIST Additive Manufacturing Benchmark Test Series](https://www.nist.gov/ambench). This provides experimental reference data and model-comparison challenges for additive manufacturing.
- [NIST Semiconductor Overlay Metrology](https://www.nist.gov/programs-projects/overlay-metrology-using-physics-and-ai-based-scanning-electron-microscopy). This describes measurement challenges in advanced semiconductor manufacturing.
- [NIST Digital Twins Workshops Summary Report (2026)](https://www.nist.gov/publications/digital-twins-workshops-summary-report). This discusses verification, validation, uncertainty and interoperability concerns for industrial digital twins.
- [BIPM Joint Committee for Guides in Metrology](https://www.bipm.org/en/web/guest/publications/guides). This covers measurement uncertainty and conformity assessment, including JCGM 100 and JCGM 106.
- [Lawrence Berkeley National Laboratory: Distribution System Planning](https://eta.lbl.gov/publications/bridging-gap-data-and-analysis). This discusses grid hosting-capacity analysis and utility planning data.
- [ECMWF Forecast Verification](https://www.ecmwf.int/en/forecasts/quality-our-forecasts). This provides meteorological forecast verification context and skill measures.
- [ISA Functional Safety Standards](https://www.isa.org/standards-and-publications/isa-standards/isa-84-standards). This defines relevant safety-instrumented-system lifecycle requirements.
- [FDA Process Analytical Technology Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/pat-framework-innovative-pharmaceutical-development-manufacturing-and-quality-assurance). This describes PAT in pharmaceutical manufacturing and quality assurance.

## Repository, coverage and maintenance

**Repository:** [paceval/paceval](https://github.com/paceval/paceval) | **Research directory:** [TOP+ Industrial Research Projects with paceval](https://github.com/paceval/paceval/tree/main/new%20projects/TOP%2B%20Industrial%20Research%20Projects%20with%20paceval) | **Technology:** [paceval. Mathematical Engine](https://paceval.com/)

**Catalogue date:** 15 November 2026. 
