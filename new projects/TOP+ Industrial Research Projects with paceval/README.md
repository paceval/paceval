# paceval. | Industrial Research Portfolio

**67 mathematical research demonstrators across 11 industrial and scientific application clusters.**

This directory collects concrete mathematical application research using the [paceval. Mathematical Engine](https://paceval.com/). The studies explore how explicitly specified expressions can be prepared as persistent computation graphs and evaluated repeatedly within engineering applications, AI tool workflows, embedded systems, digital twins, industrial analytics, financial models and scientific research.

Every project has its own English README, scientific whitepaper and primary C++ research source. The collection is a set of **mathematical functionality and engineering feasibility demonstrators**, not a catalogue of certified industrial products or independently confirmed performance gains. Individual methods, numerical observations and limits are documented in the project packages.

**Archive inventory, 13 November 2026:** 67 project directories, 67 local project READMEs, 67 English research PDFs comprising **722 pages**, and 67 primary C++ sources. The principal C++ files contain original paceval computation creation and result evaluation call sites. The archive provides selected key files rather than every auxiliary result or figure referenced by the local READMEs. The full portfolio was indexed and source-inspected, but its 67 applications were not independently compiled or executed in this catalogue update.

## Mathematical execution architecture

```text
Engineering model, agent tool request or scientific calculation
                             |
                  Host input and unit checks
                             |
              Explicit, approved mathematical formulas
                             |
          paceval computation creation and preparation
                             |
           Reusable calculation objects and graph handles
                             |
        Repeated evaluation with changed numerical inputs
                             |
             Numerical outputs, scores and sensitivities
                             |
              Host interpretation and independent audits
```

The [paceval SDK](https://paceval.com/api/) constructs computation objects from mathematical expressions and reuses them for repeated scalar or batch evaluation. The exact API calls depend on the SDK version and project. Where a project uses the [paceval MCP service](https://github.com/paceval/paceval/tree/main/examples_sources/MCP_server), remote formula creation and evaluation are distinguished from execution through the local C++ SDK. Source code, actual execution records and independently implemented numerical checks have different evidentiary roles.

The research emphasizes reusable mathematical graphs for model formulas, scoring and quality functions, analytical derivatives, decision margins, conditional expressions and other suitable numerical kernels. Host C++ remains responsible for orchestration, datasets, memory layout, dependency order, training, physical simulation state, solver control, application policies and I/O wherever those steps are outside a paceval computation. **An application that calls paceval does not necessarily execute all its algorithms inside paceval.**

Trusted Interval Computation, when used by an individual experiment, concerns the documented numerical computations and tested inputs. It does not automatically establish physical measurement uncertainty, a global proof, safety certification or correct interpretation of an AI-generated model.

## Research clusters

The primary classification below is designed for both engineering readers and automated repository discovery. Some projects are relevant to several application domains, but each appears in exactly one cluster.

| Cluster | Projects | Research focus |
|---|---:|---|
| [1. AI agents, mathematical tools and MCP integration](#cluster-1) | 10 | Explicit mathematical contracts for AI agents, approved tool operations, versioned formulas and traceable calculations. MCP integration and local SDK execution are distinguished. |
| [2. Edge AI, neural formulas and monitoring](#cluster-2) | 6 | Sensor-derived mathematics, frozen neural inference represented as expressions, anomaly scores and industrial monitoring rules. |
| [3. Manufacturing, quality and industrial decisions](#cluster-3) | 10 | Decision trees, inspection and production scores, industrial planning, CNC screening, inventory and system identification. |
| [4. Industrial numerical kernels, calibration and matrix analytics](#cluster-4) | 3 | Long calibration expressions, full matrix arithmetic, covariance-based sensor fusion and configurable inspection mathematics. |
| [5. Digital twins and equipment models](#cluster-5) | 9 | Reusable mathematical submodels for buildings, factories, pumps, battery systems, heat pumps, wind turbines and equipment processes. |
| [6. Robotics, trajectories and geometric calibration](#cluster-6) | 3 | Kinematic expressions, residual models, trajectory scores and configurable motion constraints. |
| [7. Energy systems and fusion engineering](#cluster-7) | 3 | Demand response, wind-farm loss functions and selected plasma engineering calculations. |
| [8. Financial services, insurance and quantitative risk](#cluster-8) | 8 | Quantitative pricing, stress scenarios, exposure functions, risk indicators, scorecards and insurance calculations. |
| [9. Space engineering, astronomy and catalog analysis](#cluster-9) | 6 | Orbital mechanics, propulsion, gravity and mathematical spectral screening on documented astrophysical inputs. |
| [10. Fundamental physics and mathematical exploration](#cluster-10) | 5 | Classical physics kernels, symbolic candidate equations, analytic surfaces, collider-inspired functions and quantum-related classical expressions. |
| [11. Biomedical engineering and microfluidics](#cluster-11) | 4 | Research-only signal features, pharmacokinetic mathematical kernels and microfluidic reaction/transport expressions. |
| **Total** | **67** | **Research demonstrators with project-specific scope and validation.** |

## Project catalogue

Each project title opens its own README. The adjacent links open the primary English research PDF and C++ source. All three targets for every project were verified as paths in the supplied archive. These relative links work when this file is installed as `README.md` in the `TOP+ Industrial Research Projects with paceval/` directory.

<a id="cluster-1"></a>
### 1. AI agents, mathematical tools and MCP integration (10)

Explicit mathematical contracts for AI agents, approved tool operations, versioned formulas and traceable calculations. MCP integration and local SDK execution are distinguished.

| Project | Implemented mathematical research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Auditable AI Chains](paceval_Auditable_AI_Chains/README.md) | Compose reusable mathematical steps with traceable intermediate values. | [PDF](paceval_Auditable_AI_Chains/paceval_Auditable_AI_Chains_Whitepaper_EN.pdf) | [C++](paceval_Auditable_AI_Chains/src/auditable_chains.cpp) |
| [Agent Simulations](paceval_Agent_Simulations_Research/README.md) | Coordinate selected simulation families with reusable formulas and logged retries. | [PDF](paceval_Agent_Simulations_Research/paceval_Agent_Orchestrated_Mathematical_Simulations_Whitepaper_EN.pdf) | [C++](paceval_Agent_Simulations_Research/src/agent_simulations.cpp) |
| [Agent Financial Arithmetic](paceval_Agent_Financial_Arithmetic/README.md) | Serve controlled, versioned financial computations to structured agent requests. | [PDF](paceval_Agent_Financial_Arithmetic/paceval_Agent_Financial_Arithmetic_Whitepaper_EN.pdf) | [C++](paceval_Agent_Financial_Arithmetic/src/financial_agent.cpp) |
| [Large Quantitative Model Tools](paceval_Large_Quantitative_Model_Tools_Research/README.md) | Provide reusable quantitative formula tools for higher-level assistants. | [PDF](paceval_Large_Quantitative_Model_Tools_Research/paceval_Large_Quantitative_Model_Tools_Whitepaper_EN.pdf) | [C++](paceval_Large_Quantitative_Model_Tools_Research/src/quantitative_tools.cpp) |
| [Hypothesis Testing](paceval_Hypothesis_Testing/README.md) | Screen explicitly generated mathematical hypotheses against numerical data. | [PDF](paceval_Hypothesis_Testing/paceval_Hypothesis_Testing_Whitepaper_EN.pdf) | [C++](paceval_Hypothesis_Testing/src/hypothesis_test.cpp) |
| [Technical AI Agents](paceval_Technical_AI_Agents/README.md) | Engineering formulas exposed through a typed, unit-checked tool boundary. | [PDF](paceval_Technical_AI_Agents/paceval_Technical_AI_Agents_Whitepaper_EN.pdf) | [C++](paceval_Technical_AI_Agents/src/technical_agent.cpp) |
| [LLM Generated Mathematics](paceval_LLM_Generated_Mathematics/README.md) | Validate and evaluate generated mathematical expressions under explicit model contracts. | [PDF](paceval_LLM_Generated_Mathematics/paceval_LLM_Math_Expressions_Whitepaper_EN.pdf) | [C++](paceval_LLM_Generated_Mathematics/src/llm_math.cpp) |
| [Agent Constraint Verification](paceval_Agent_Constraint_Verification_Research/README.md) | Execute versioned mathematical guards on proposed industrial setpoints. | [PDF](paceval_Agent_Constraint_Verification_Research/paceval_Agent_Constraint_Verification_Whitepaper_EN.pdf) | [C++](paceval_Agent_Constraint_Verification_Research/src/agent_constraints.cpp) |
| [Low Code Automation](paceval_Low_Code_Automation/README.md) | Reuse approved mathematical models in an automation-style integration workflow. | [PDF](paceval_Low_Code_Automation/paceval_Low_Code_Automation_Whitepaper_EN.pdf) | [C++](paceval_Low_Code_Automation/src/lowcode_math.cpp) |
| [Industrial Mathematical Models via MCP](paceval_Industrial_MCP_Mathematical_Models/README.md) | Evaluate two versioned synthetic volumetric calibration fields through documented remote MCP operations and a separate local SDK C++ demonstrator. | [PDF](paceval_Industrial_MCP_Mathematical_Models/paceval_Industrial_MCP_Mathematical_Models_Whitepaper_EN.pdf) | [C++](paceval_Industrial_MCP_Mathematical_Models/src/industrial_mcp_paceval.cpp) |

<a id="cluster-2"></a>
### 2. Edge AI, neural formulas and monitoring (6)

Sensor-derived mathematics, frozen neural inference represented as expressions, anomaly scores and industrial monitoring rules.

| Project | Implemented mathematical research scope | Whitepaper | C++ source |
|---|---|---|---|
| [On Device Expression Runtime](paceval_On_Device_Expression_Runtime/README.md) | Prepare reusable expressions for bounded-input device-side evaluation. | [PDF](paceval_On_Device_Expression_Runtime/paceval_On_Device_Expression_Runtime_Whitepaper_EN.pdf) | [C++](paceval_On_Device_Expression_Runtime/src/on_device_runtime.cpp) |
| [Explainable Anomaly Detection](paceval_Explainable_Anomaly_Detection/README.md) | Evaluate versioned anomaly-scoring formulas on synthetic sensor streams. | [PDF](paceval_Explainable_Anomaly_Detection/paceval_Explainable_Anomaly_Detection_Whitepaper_EN.pdf) | [C++](paceval_Explainable_Anomaly_Detection/src/anomaly_detection.cpp) |
| [Edge AI Postprocessing](paceval_Edge_AI_Postprocessing/README.md) | Apply deterministic mathematical scoring to precomputed AI outputs. | [PDF](paceval_Edge_AI_Postprocessing/paceval_Edge_AI_Postprocessing_Whitepaper_EN.pdf) | [C++](paceval_Edge_AI_Postprocessing/src/edge_ai.cpp) |
| [Industrial Gateway](paceval_Industrial_Gateway/README.md) | Execute versioned telemetry rules in an offline industrial gateway replay. | [PDF](paceval_Industrial_Gateway/paceval_Industrial_Gateway_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Gateway/src/gateway_rules.cpp) |
| [Predictive Maintenance](paceval_Predictive_Maintenance/README.md) | Calculate mathematical vibration-condition features and health scores. | [PDF](paceval_Predictive_Maintenance/paceval_Predictive_Maintenance_Whitepaper_EN.pdf) | [C++](paceval_Predictive_Maintenance/src/predictive_maintenance.cpp) |
| [Industrial Edge Neural Formula Execution](paceval_Industrial_Edge_Neural_Formula_Research_Expanded/README.md) | Execute two frozen synthetic bearing-monitoring neural networks as layered and expanded paceval formulas, together with normalization, sensitivities and advisory scores. | [PDF](paceval_Industrial_Edge_Neural_Formula_Research_Expanded/paceval_Industrial_Edge_Neural_Formula_Research_Expanded_EN.pdf) | [C++](paceval_Industrial_Edge_Neural_Formula_Research_Expanded/src/edge_neural_formula.cpp) |

<a id="cluster-3"></a>
### 3. Manufacturing, quality and industrial decisions (10)

Decision trees, inspection and production scores, industrial planning, CNC screening, inventory and system identification.

| Project | Implemented mathematical research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Quality Scrap Scores](paceval_Quality_Scrap_Scores_Research/README.md) | Apply mathematical quality-risk and inspection-routing scores. | [PDF](paceval_Quality_Scrap_Scores_Research/paceval_Quality_Scrap_Scores_Whitepaper_EN.pdf) | [C++](paceval_Quality_Scrap_Scores_Research/src/quality_scores.cpp) |
| [Auction Bid Formulas](paceval_Auction_Bid_Formulas_Research/README.md) | Evaluate versioned mathematical supplier-bid formulas. | [PDF](paceval_Auction_Bid_Formulas_Research/paceval_Auction_Bid_Formulas_Whitepaper_EN.pdf) | [C++](paceval_Auction_Bid_Formulas_Research/src/auction_bids.cpp) |
| [Industrial 3D](paceval_Industrial_3D_Research/README.md) | Generate scientific 3D surfaces from computed industrial mathematical models. | [PDF](paceval_Industrial_3D_Research/paceval_Industrial_3D_Diagrams_Whitepaper_EN.pdf) | [C++](paceval_Industrial_3D_Research/src/industrial_3d.cpp) |
| [Material Symbolic Regression](paceval_Material_Symbolic_Regression_Research/README.md) | Evaluate predefined synthetic material-property candidate formulas. | [PDF](paceval_Material_Symbolic_Regression_Research/paceval_Material_Symbolic_Regression_Whitepaper_EN.pdf) | [C++](paceval_Material_Symbolic_Regression_Research/src/material_candidate.cpp) |
| [CNC Parameter Screening](paceval_CNC_Parameter_Screening/README.md) | Screens machining parameters with reusable milling-related formulas, constraint checks and configurable scoring variants. | [PDF](paceval_CNC_Parameter_Screening/paceval_CNC_Parameter_Screening_Whitepaper_EN.pdf) | [C++](paceval_CNC_Parameter_Screening/src/cnc_screening.cpp) |
| [Agent-Controlled Production Planning Scores](paceval_Agent_Controlled_Production_Planning_Scores/README.md) | Uses persistent scheduling scores and constraint margins for a synthetic job-shop problem. A host scheduler handles combinatorial selection and controlled policy requests. | [PDF](paceval_Agent_Controlled_Production_Planning_Scores/paceval_Agent_Controlled_Production_Planning_Scores_Whitepaper_EN.pdf) | [C++](paceval_Agent_Controlled_Production_Planning_Scores/src/production_planning.cpp) |
| [Industrial Control](paceval_Industrial_Control/README.md) | Evaluate objective and constraint terms in an offline MPC-style study. | [PDF](paceval_Industrial_Control/paceval_Industrial_Control_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Control/src/industrial_control.cpp) |
| [Inventory Replenishment](paceval_Inventory_Replenishment_Research/README.md) | Compare parameterized inventory replenishment decision rules. | [PDF](paceval_Inventory_Replenishment_Research/paceval_Inventory_Replenishment_Whitepaper_EN.pdf) | [C++](paceval_Inventory_Replenishment_Research/src/inventory_replenishment.cpp) |
| [Symbolic System Identification](paceval_Symbolic_System_Identification/README.md) | Screen candidate nonlinear dynamical-system expressions against trajectories. | [PDF](paceval_Symbolic_System_Identification/paceval_Symbolic_System_Identification_Whitepaper_EN.pdf) | [C++](paceval_Symbolic_System_Identification/src/system_identification.cpp) |
| [Industrial Decision Tree Mathematical Execution](paceval_Decision_Tree_Mathematical_Execution/README.md) | Execute explicitly authored decision-tree indicator expressions, two 64-leaf rule versions, score functions, guard margins and sensitivities. | [PDF](paceval_Decision_Tree_Mathematical_Execution/paceval_Decision_Tree_Mathematical_Execution_Whitepaper_EN.pdf) | [C++](paceval_Decision_Tree_Mathematical_Execution/src/decision_tree.cpp) |

<a id="cluster-4"></a>
### 4. Industrial numerical kernels, calibration and matrix analytics (3)

Long calibration expressions, full matrix arithmetic, covariance-based sensor fusion and configurable inspection mathematics.

| Project | Implemented mathematical research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Industrial Piecewise Calibration](paceval_Industrial_Piecewise_Calibration/README.md) | Evaluate large, versioned piecewise calibration functions with temperature corrections, drift terms, derivatives and synthetic quality margins. | [PDF](paceval_Industrial_Piecewise_Calibration/paceval_Industrial_Piecewise_Calibration_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Piecewise_Calibration/src/industrial_calibration.cpp) |
| [Industrial Matrix Sensor Fusion](paceval_Industrial_Matrix_Sensor_Fusion/README.md) | Build full symmetric positive-definite matrix factorizations and inverses for synthetic multichannel sensor fusion with versioned quality scores. | [PDF](paceval_Industrial_Matrix_Sensor_Fusion/paceval_Industrial_Matrix_Sensor_Fusion_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Matrix_Sensor_Fusion/src/matrix_sensor_fusion.cpp) |
| [Matrix Precision and Quality Monitoring](paceval_Matrix_Precision_Quality/README.md) | Connect archived dense SPD-matrix results with versioned covariance-weighted quality formulas, sensitivities and numerical enclosures. Newer MCP outputs and local C++ evidence are distinguished. | [PDF](paceval_Matrix_Precision_Quality/paceval_Matrix_Precision_Quality_Whitepaper_EN.pdf) | [C++](paceval_Matrix_Precision_Quality/src/matrix_precision_paceval.cpp) |

<a id="cluster-5"></a>
### 5. Digital twins and equipment models (9)

Reusable mathematical submodels for buildings, factories, pumps, battery systems, heat pumps, wind turbines and equipment processes.

| Project | Implemented mathematical research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Digital Twins Simulation](paceval_Digital_Twins_Simulation/README.md) | Evaluate reusable mathematical submodels in a synthetic thermal digital twin. | [PDF](paceval_Digital_Twins_Simulation/paceval_Digital_Twins_Whitepaper_EN.pdf) | [C++](paceval_Digital_Twins_Simulation/src/digital_twin.cpp) |
| [Factory Line Digital Twin](paceval_Factory_Line_Digital_Twin/README.md) | Couples a synthetic discrete-event line simulation to reusable station-time formulas, quality, energy and KPI computations. | [PDF](paceval_Factory_Line_Digital_Twin/paceval_Factory_Line_Digital_Twin_Whitepaper_EN.pdf) | [C++](paceval_Factory_Line_Digital_Twin/src/factory_line_twin.cpp) |
| [Building Thermal Twin](paceval_Building_Thermal_Twin/README.md) | Evaluates synthetic building heat balances, forecast functions, calibration losses and analytical sensitivities. | [PDF](paceval_Building_Thermal_Twin/paceval_Building_Thermal_Twin_Whitepaper_EN.pdf) | [C++](paceval_Building_Thermal_Twin/src/thermal_twin.cpp) |
| [Hydraulic Pump Twin](paceval_Hydraulic_Pump_Twin/README.md) | Uses synthetic pump curves and network models to calculate operating points, efficiency, power, energy cost and sensitivities. | [PDF](paceval_Hydraulic_Pump_Twin/paceval_Hydraulic_Pump_Twin_Whitepaper_EN.pdf) | [C++](paceval_Hydraulic_Pump_Twin/src/hydraulic_pump_twin.cpp) |
| [Battery Charging and Aging Terms](paceval_Battery_Charging_Aging/README.md) | Screens tariff-aware charging schedules using state-of-charge transitions, versioned cost expressions and explicitly uncalibrated aging surrogates. | [PDF](paceval_Battery_Charging_Aging/paceval_Battery_Charging_Aging_Whitepaper_EN.pdf) | [C++](paceval_Battery_Charging_Aging/src/battery_charging_aging.cpp) |
| [Battery Equivalent Circuit Twin](paceval_Battery_Twin_Equivalent_Circuit_Functions/README.md) | Evaluates synthetic 1RC and 2RC circuit equations for voltage, state of charge, energy and thermal behavior. | [PDF](paceval_Battery_Twin_Equivalent_Circuit_Functions/paceval_Battery_Twin_Equivalent_Circuit_Functions_Whitepaper_EN.pdf) | [C++](paceval_Battery_Twin_Equivalent_Circuit_Functions/src/battery_twin.cpp) |
| [Heat Pump Twin](paceval_Heat_Pump_Twin/README.md) | Evaluates synthetic coefficient-of-performance maps, heating power, electricity use, sensitivities and cost expressions. | [PDF](paceval_Heat_Pump_Twin/paceval_Heat_Pump_Twin_Whitepaper_EN.pdf) | [C++](paceval_Heat_Pump_Twin/src/heat_pump_twin.cpp) |
| [Electrolyser Efficiency Surrogates](paceval_Electrolyser_Efficiency_Surrogate_Functions/README.md) | Screens synthetic PEM electrolyser stack voltage, hydrogen production, system efficiency and operating constraints with explicit formula versions. | [PDF](paceval_Electrolyser_Efficiency_Surrogate_Functions/paceval_Electrolyser_Efficiency_Surrogate_Functions_Whitepaper_EN.pdf) | [C++](paceval_Electrolyser_Efficiency_Surrogate_Functions/src/electrolyser_twin.cpp) |
| [Wind Turbine Digital Twin](paceval_Wind_Turbine_Digital_Twin/README.md) | Evaluates rotor coefficient maps, aerodynamic power, torque, thrust, sensitivities and model state updates on synthetic inputs. | [PDF](paceval_Wind_Turbine_Digital_Twin/paceval_Wind_Turbine_Digital_Twin_Whitepaper_EN.pdf) | [C++](paceval_Wind_Turbine_Digital_Twin/src/wind_turbine_twin.cpp) |

<a id="cluster-6"></a>
### 6. Robotics, trajectories and geometric calibration (3)

Kinematic expressions, residual models, trajectory scores and configurable motion constraints.

| Project | Implemented mathematical research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Robotics Trajectory Planning](paceval_Robotics_Trajectory_Planning/README.md) | Evaluate planar robot kinematics, trajectory scores and simplified constraints. | [PDF](paceval_Robotics_Trajectory_Planning/paceval_Robotic_Trajectories_Whitepaper_EN.pdf) | [C++](paceval_Robotics_Trajectory_Planning/src/robotics.cpp) |
| [Reconfigurable Robotic Trajectory Costs](paceval_Reconfigurable_Robotic_Trajectory_Costs/README.md) | Compare complete candidate trajectories under changeable cost formulas. | [PDF](paceval_Reconfigurable_Robotic_Trajectory_Costs/paceval_Reconfigurable_Robotic_Trajectory_Costs_Whitepaper_EN.pdf) | [C++](paceval_Reconfigurable_Robotic_Trajectory_Costs/src/trajectory_costs.cpp) |
| [Robot Calibration](paceval_Robot_Calibration/README.md) | Evaluate 3D robot forward-kinematic residuals for position calibration. | [PDF](paceval_Robot_Calibration/paceval_Robot_Calibration_Whitepaper_EN.pdf) | [C++](paceval_Robot_Calibration/src/robot_calibration.cpp) |

<a id="cluster-7"></a>
### 7. Energy systems and fusion engineering (3)

Demand response, wind-farm loss functions and selected plasma engineering calculations.

| Project | Implemented mathematical research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Demand Response](paceval_Demand_Response/README.md) | Evaluate versioned demand-response incentive and scheduling formulas. | [PDF](paceval_Demand_Response/paceval_Demand_Response_Whitepaper_EN.pdf) | [C++](paceval_Demand_Response/src/demand_response.cpp) |
| [Wind Farm Loss Functions](paceval_Wind_Farm_Loss_Functions/README.md) | Evaluate simplified wake-loss and turbine-power functions. | [PDF](paceval_Wind_Farm_Loss_Functions/paceval_Wind_Farm_Loss_Functions_Whitepaper_EN.pdf) | [C++](paceval_Wind_Farm_Loss_Functions/src/wind_farm.cpp) |
| [Fusion Plasma Control](paceval_Fusion_Plasma_Control/README.md) | Evaluate explicitly defined plasma diagnostic and control-related functions. | [PDF](paceval_Fusion_Plasma_Control/paceval_Fusion_Diagnostics_Whitepaper_EN.pdf) | [C++](paceval_Fusion_Plasma_Control/src/fusion.cpp) |

<a id="cluster-8"></a>
### 8. Financial services, insurance and quantitative risk (8)

Quantitative pricing, stress scenarios, exposure functions, risk indicators, scorecards and insurance calculations.

| Project | Implemented mathematical research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Credit Risk Scorecard](paceval_Credit_Risk_Scorecard_Research/README.md) | Evaluate transparent synthetic credit-scorecard formulas. | [PDF](paceval_Credit_Risk_Scorecard_Research/paceval_Credit_Risk_Scorecard_Whitepaper_EN.pdf) | [C++](paceval_Credit_Risk_Scorecard_Research/src/credit_scorecard.cpp) |
| [Counterparty Exposure](paceval_Counterparty_Exposure_Research/README.md) | Evaluate pointwise counterparty-exposure calculation functions. | [PDF](paceval_Counterparty_Exposure_Research/paceval_Counterparty_Exposure_Whitepaper_EN.pdf) | [C++](paceval_Counterparty_Exposure_Research/src/counterparty_exposure.cpp) |
| [Intraday Risk](paceval_Intraday_Risk_Research/README.md) | Replay versioned intraday market-risk functions. | [PDF](paceval_Intraday_Risk_Research/paceval_Intraday_Risk_Whitepaper_EN.pdf) | [C++](paceval_Intraday_Risk_Research/src/intraday_risk.cpp) |
| [Insurance Tariffs](paceval_Insurance_Tariffs/README.md) | Demonstrate versioned synthetic insurance tariff calculations. | [PDF](paceval_Insurance_Tariffs/paceval_Insurance_Tariffs_Whitepaper_EN.pdf) | [C++](paceval_Insurance_Tariffs/src/insurance_tariffs.cpp) |
| [Trading Indicators](paceval_Trading_Indicators_Research/README.md) | Evaluate mathematical quantitative indicator composites on price-bar data. | [PDF](paceval_Trading_Indicators_Research/paceval_Interchangeable_Trading_Indicators_Whitepaper_EN.pdf) | [C++](paceval_Trading_Indicators_Research/src/trading_indicators.cpp) |
| [Monte Carlo Pricing](paceval_Monte_Carlo_Pricing/README.md) | Reuse option payoff formulas inside a host-driven Monte Carlo workload. | [PDF](paceval_Monte_Carlo_Pricing/paceval_Monte_Carlo_Pricing_Whitepaper_EN.pdf) | [C++](paceval_Monte_Carlo_Pricing/src/monte_carlo_pricing.cpp) |
| [Pricing Sensitivities](paceval_Pricing_Sensitivities_Research/README.md) | Evaluate option pricing and analytical sensitivity formulas. | [PDF](paceval_Pricing_Sensitivities_Research/paceval_Pricing_Formula_Sensitivities_Whitepaper_EN.pdf) | [C++](paceval_Pricing_Sensitivities_Research/src/pricing_sensitivities.cpp) |
| [Portfolio Stress](paceval_Portfolio_Stress/README.md) | Evaluate synthetic factor stress scenarios and portfolio P&L expressions. | [PDF](paceval_Portfolio_Stress/paceval_Portfolio_Stress_Whitepaper_EN.pdf) | [C++](paceval_Portfolio_Stress/src/portfolio_stress.cpp) |

<a id="cluster-9"></a>
### 9. Space engineering, astronomy and catalog analysis (6)

Orbital mechanics, propulsion, gravity and mathematical spectral screening on documented astrophysical inputs.

| Project | Implemented mathematical research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Electric Propulsion](paceval_Electric_Propulsion_Research/README.md) | Evaluate parameterized analytical electric-thruster performance maps. | [PDF](paceval_Electric_Propulsion_Research/paceval_Electric_Propulsion_Whitepaper_EN.pdf) | [C++](paceval_Electric_Propulsion_Research/src/electric_propulsion.cpp) |
| [Orbit Parameter Sweeps](paceval_Orbit_Parameter_Sweeps_Research/README.md) | Calculate orbital acceleration components in host-driven orbit propagation. | [PDF](paceval_Orbit_Parameter_Sweeps_Research/paceval_Orbit_Parameter_Sweeps_Whitepaper_EN.pdf) | [C++](paceval_Orbit_Parameter_Sweeps_Research/src/orbit_sweeps.cpp) |
| [Space Transfer Screening](paceval_Space_Transfer_Screening/README.md) | Screens idealized two-body orbital transfers, impulsive velocity budgets, transfer times and rocket-equation propellant requirements. | [PDF](paceval_Space_Transfer_Screening/paceval_Space_Transfer_Screening_Whitepaper_EN.pdf) | [C++](paceval_Space_Transfer_Screening/src/space_transfer.cpp) |
| [Gravitational Inversion](paceval_Gravitational_Inversion_Research/README.md) | Evaluate gravitational-field functions and inversion sensitivities. | [PDF](paceval_Gravitational_Inversion_Research/paceval_Gravitational_Inversion_Whitepaper_EN.pdf) | [C++](paceval_Gravitational_Inversion_Research/src/gravity_inversion.cpp) |
| [Fermi 2FLE Spectral Screening Methods](paceval_Fermi_2FLE_Spectral_Screening/README.md) | Combines transcribed 2FLE source metadata with distinctly synthetic spectral and likelihood inputs to test reusable screening mathematics. | [PDF](paceval_Fermi_2FLE_Spectral_Screening/paceval_Fermi_2FLE_Spectral_Screening_Whitepaper_EN.pdf) | [C++](paceval_Fermi_2FLE_Spectral_Screening/src/fermi_2fle_demo.cpp) |
| [Fermi 2FLE Real Catalog Spectral Mathematics](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/README.md) | Re-evaluates published spectral fit parameters for 450 NASA 2FLE catalog sources. It does not reprocess LAT photon events or establish new source classes. | [PDF](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/paceval_Fermi_2FLE_Real_Catalog_Whitepaper_EN.pdf) | [C++](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/src/fermi_real_catalog.cpp) |

<a id="cluster-10"></a>
### 10. Fundamental physics and mathematical exploration (5)

Classical physics kernels, symbolic candidate equations, analytic surfaces, collider-inspired functions and quantum-related classical expressions.

| Project | Implemented mathematical research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Conservation Law Candidates](paceval_Conservation_Law_Candidates/README.md) | Checks proposed mathematical invariants and time-derivative residuals for specified dynamical models. Candidate screening is not a proof of a universal physical law. | [PDF](paceval_Conservation_Law_Candidates/paceval_Conservation_Law_Candidates_Whitepaper_EN.pdf) | [C++](paceval_Conservation_Law_Candidates/src/conservation_law_candidates.cpp) |
| [Extreme-Length Analytic Terrain](paceval_Extreme_Analytic_Terrain/README.md) | Creates and samples exceptionally long analytical terrain expressions to investigate reusable expression execution and numerical surfaces. | [PDF](paceval_Extreme_Analytic_Terrain/paceval_Extreme_Analytic_Terrain_Whitepaper_EN.pdf) | [C++](paceval_Extreme_Analytic_Terrain/src/extreme_terrain.cpp) |
| [Collider](paceval_Collider_Research/README.md) | Execute selected collider-inspired mathematical analysis kernels. | [PDF](paceval_Collider_Research/paceval_Collider_Research_Whitepaper_EN.pdf) | [C++](paceval_Collider_Research/src/collider.cpp) |
| [Quantum](paceval_Quantum_Research/README.md) | Evaluate classical calibration and circuit-expectation mathematics. | [PDF](paceval_Quantum_Research/paceval_Quantum_Research_Whitepaper_EN.pdf) | [C++](paceval_Quantum_Research/src/quantum.cpp) |
| [Parameterized Bulk-Wave Kernels](paceval_Bulk_Wave_Kernels/README.md) | Executes parameterized wave operators, manufactured forcing, diagnostic functions and sensitivities in a host-integrated one-dimensional model. | [PDF](paceval_Bulk_Wave_Kernels/paceval_Bulk_Wave_Kernels_Whitepaper_EN.pdf) | [C++](paceval_Bulk_Wave_Kernels/src/bulk_wave_kernels.cpp) |

<a id="cluster-11"></a>
### 11. Biomedical engineering and microfluidics (4)

Research-only signal features, pharmacokinetic mathematical kernels and microfluidic reaction/transport expressions.

| Project | Implemented mathematical research scope | Whitepaper | C++ source |
|---|---|---|---|
| [ECG Feature Rules](paceval_ECG_Feature_Rules_Research/README.md) | Evaluate synthetic ECG-feature-to-score mathematical rules. | [PDF](paceval_ECG_Feature_Rules_Research/paceval_ECG_Feature_Rule_Evaluation_Whitepaper_EN.pdf) | [C++](paceval_ECG_Feature_Rules_Research/src/ecg_rules.cpp) |
| [Wearable Signal Scoring](paceval_Wearable_Signal_Scoring/README.md) | Executes configurable non-clinical scores on synthetic photoplethysmography and motion-sensor feature windows. | [PDF](paceval_Wearable_Signal_Scoring/paceval_Wearable_Signal_Scoring_Whitepaper_EN.pdf) | [C++](paceval_Wearable_Signal_Scoring/src/wearable_scoring.cpp) |
| [Pharmacokinetic Rate Kernels](paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels/README.md) | Evaluates synthetic one-compartment drug exposure, concentration transitions, clearance variants and sensitivity functions. It is not prescribing software. | [PDF](paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels/paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels_Whitepaper_EN.pdf) | [C++](paceval_Patient_Specific_Pharmacokinetic_Rate_Kernels/src/pharmacokinetic_kernels.cpp) |
| [Microfluidic Reaction and Transport](paceval_Microfluidic_Reaction_Rate_Expressions/README.md) | Evaluates reversible reaction rates and conservative transport updates in a synthetic continuous-flow microreactor. | [PDF](paceval_Microfluidic_Reaction_Rate_Expressions/paceval_Microfluidic_Reaction_Rate_Expressions_Whitepaper_EN.pdf) | [C++](paceval_Microfluidic_Reaction_Rate_Expressions/src/microfluidic_reactor.cpp) |

## Choose a starting point

| Engineering question | Suggested projects |
|---|---|
| How can AI agents perform approved, auditable calculations? | [Technical AI Agents](paceval_Technical_AI_Agents/README.md), [Industrial Mathematical Models via MCP](paceval_Industrial_MCP_Mathematical_Models/README.md), [Agent Constraint Verification](paceval_Agent_Constraint_Verification_Research/README.md) |
| Can frozen neural networks be expressed and executed mathematically at the edge? | [Industrial Edge Neural Formula Execution](paceval_Industrial_Edge_Neural_Formula_Research_Expanded/README.md), [Edge AI Postprocessing](paceval_Edge_AI_Postprocessing/README.md) |
| Can explicit decision trees and industrial quality rules be executed as formulas? | [Industrial Decision Tree Mathematical Execution](paceval_Decision_Tree_Mathematical_Execution/README.md), [Quality Scrap Scores](paceval_Quality_Scrap_Scores_Research/README.md) |
| How can large calibration models remain reusable and version-controlled? | [Industrial Piecewise Calibration](paceval_Industrial_Piecewise_Calibration/README.md), [Industrial Mathematical Models via MCP](paceval_Industrial_MCP_Mathematical_Models/README.md) |
| What is the role of paceval in matrix calculations and sensor fusion? | [Industrial Matrix Sensor Fusion](paceval_Industrial_Matrix_Sensor_Fusion/README.md), [Matrix Precision and Quality Monitoring](paceval_Matrix_Precision_Quality/README.md) |
| Which equipment models are suitable for digital-twin experiments? | [Digital Twins Simulation](paceval_Digital_Twins_Simulation/README.md), [Battery Twin Equivalent Circuit Functions](paceval_Battery_Twin_Equivalent_Circuit_Functions/README.md), [Factory Line Digital Twin](paceval_Factory_Line_Digital_Twin/README.md) |
| Which repetitive mathematics supports robotics and energy engineering? | [Robotics Trajectory Planning](paceval_Robotics_Trajectory_Planning/README.md), [Demand Response](paceval_Demand_Response/README.md), [Wind Turbine Digital Twin](paceval_Wind_Turbine_Digital_Twin/README.md) |
| Which financial and scientific computations can be represented as reusable expressions? | [Monte Carlo Pricing](paceval_Monte_Carlo_Pricing/README.md), [Portfolio Stress](paceval_Portfolio_Stress/README.md), [Fermi 2FLE Real Catalog Spectral Screening](paceval_Fermi_2FLE_Real_Catalog_Spectral_Screening/README.md) |

## Evidence and scientific interpretation

**Source code and execution evidence are not interchangeable.** All 67 principal programs contain paceval creation and evaluation call sites. The projects document their own mathematical models, runtime requirements, reported test results and independent checks. This portfolio index verifies the file inventory and inspects the source, but it does not independently rerun all experiments or certify the accuracy of every documented result.

**Original SDK and MCP execution must be distinguished.** The [Industrial Mathematical Models via MCP](paceval_Industrial_MCP_Mathematical_Models/README.md) project explicitly documents separate remote paceval MCP 4.26 activity and a local original SDK 4.25 C++ experiment. The [Matrix Precision and Quality Monitoring](paceval_Matrix_Precision_Quality/README.md) project distinguishes previously recorded full-matrix calculations, newer MCP output and a local C++ program for which the reported research package did not establish a completed local execution of the new application. Read the individual evidence sections before assigning an execution status to a result.

**Matrix mathematics and physical metrology must be distinguished.** [Industrial Matrix Sensor Fusion](paceval_Industrial_Matrix_Sensor_Fusion/README.md) evaluates complete synthetic symmetric positive-definite matrices, factorization, inversion, sensor-fusion formulas and two quality model versions. Its archived execution and numerical checks are not certification of real sensor accuracy. Matrix algorithms require attention to conditioning, numerical stability and independent residual checks. Libraries such as LAPACK provide established reference implementations.

**Neural and decision-rule mathematics have specific boundaries.** [Industrial Edge Neural Formula Execution](paceval_Industrial_Edge_Neural_Formula_Research_Expanded/README.md) uses trained synthetic networks with frozen coefficients and compares layered with fully expanded expression representations. It does not demonstrate hardware acceleration, a generic ONNX converter or field monitoring accuracy. [Industrial Decision Tree Mathematical Execution](paceval_Decision_Tree_Mathematical_Execution/README.md) evaluates explicitly specified rules. It does not train a decision tree or provide a certified industrial safety interlock. Algebraic branch indicators do not guarantee short-circuit handling of mathematically undefined expressions.

**Interpreting precision, performance and application claims.** Agreement on synthetic inputs does not alone demonstrate field validity. Reported numerical enclosures should be evaluated against the specified rounding model, and must not be confused with measurement uncertainty or proof over an untested input domain. Any performance claim should use matched mathematical definitions and inputs, optimized reference implementations, creation-cost amortization, full pipeline timing, repeated trials, hardware specifications and compiler options. Benchmarks for these 67 research applications are not established by this catalogue.

**Application responsibility remains with the implementer.** Agent systems must validate formulas, units, authorization and tool permissions. The biomedical projects are not clinical decision systems. Finance and insurance examples do not establish regulatory compliance. Robotics, machine control and fusion studies do not constitute certified controllers. The astronomy and physics exercises address their stated mathematical models and datasets, not automatic proof of new physical phenomena. Follow each project README for its specific assumptions.

## Reproduce or extend a demonstrator

1. Open the project's README and English whitepaper to establish its variables, assumptions, units, data provenance and claimed evidence.
2. Inspect its primary C++ source and, where supplied, `src/CMakeLists.txt`, project manifests, generated formula files and independent verification scripts.
3. Obtain the compatible original paceval runtime when required. The bundled C/C++ facade sources do not replace an external SDK library that the build expects. Projects using MCP have separate service execution requirements.
4. Compile and run in the environment documented by that project. Reuse the project's defined expressions, input datasets and precision settings.
5. Check numerical outputs using its independent Python or C++ references where provided. Distinguish source inspection, syntax compilation, successful linking, completed execution, external MCP operation and independent result verification.
6. Record SDK or MCP version, hardware, compiler options, input lineage and execution method when publishing a new experiment.

**Archive scope:** The supplied ZIP contains the 67 key project documents and sources. Some local READMEs refer to auxiliary `results/`, `figures/`, manifests or supplementary documents not present in this reduced export. Those missing auxiliary files were not evaluated as part of this index. Use the complete project directory when reproducing the work.

## Portfolio-wide development opportunities

The portfolio provides a common foundation for systematic research on reusable mathematical execution. The most useful next steps are to compare like-for-like expression evaluation against native C++ and established numerical libraries, verify more boundary cases with independent higher-precision references, use representative real-world inputs with appropriate permissions, and standardize formula registries and evidence metadata. Further work can evaluate long-form expression management, multi-graph batching, dimensional scaling and controlled revision of mathematical models. FPGA and ASIC research should report measured end-to-end results on implemented hardware rather than extrapolating from assumed speedups.

## External technical and scientific context

The following sources define relevant mathematical, industrial and interoperability context. Their inclusion is not external validation of the research outcomes in these folders.

- [paceval official website](https://paceval.com/), [SDK API](https://paceval.com/api/), [simple computation example](https://paceval.com/simple-code-example/) and [MCP server source](https://github.com/paceval/paceval/tree/main/examples_sources/MCP_server). These describe the expression preparation, reusable computation objects and service integration model.
- [Model Context Protocol specification, tools (2026-07-28)](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx). This defines the interaction model and tool-boundary obligations for MCP applications.
- [NIST Digital Twins Workshops Summary Report (2026)](https://www.nist.gov/publications/digital-twins-workshops-summary-report). This discusses industrial digital twins, validation, interoperability, uncertainty and trustworthiness.
- [scikit-learn documentation for decision trees](https://scikit-learn.org/stable/modules/tree.html). This gives background on piecewise rules and decision-tree models. These particular experiments use authored mathematical rules rather than independently trained classifiers.
- [LAPACK DPOTRF](https://www.netlib.org/lapack/explore-html/d2/d09/group__potrf_ga84e90859b02139934b166e579dd211d4.html) and [BIPM JCGM 102](https://www.bipm.org/documents/20126/2071204/JCGM_102_2011_E.pdf). These provide numerical linear algebra and multivariate measurement-uncertainty context for matrix and metrology projects.
- [BIPM JCGM 106](https://www.bipm.org/documents/20126/2071204/JCGM_106_2012_E.pdf) and [ISA/IEC 62443 standards](https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards). These provide context for measurement decision rules and industrial cybersecurity responsibilities.
- [NASA Fermi Science Support Center, 2FLE](https://fermi.gsfc.nasa.gov/ssc/data/access/lat/2FLE/). This provides catalog provenance for the astrophysical spectral-screening projects.

## Research status and ownership

**Collection status:** English research demonstrators and supporting scientific documents, indexed from the supplied archive as of 13 November 2026. Each individual project remains the primary source for its mathematical definition, scope, execution evidence, limitations and build instructions.

**Repository:** [paceval/paceval](https://github.com/paceval/paceval) | **Research folder:** [TOP+ Industrial Research Projects with paceval](https://github.com/paceval/paceval/tree/main/new%20projects/TOP%2B%20Industrial%20Research%20Projects%20with%20paceval) | **Mathematical Engine:** [paceval.](https://paceval.com/)
