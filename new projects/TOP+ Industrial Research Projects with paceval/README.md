# paceval. | Industrial Research Portfolio

**42 reproducible research-project packages across eight industrial and scientific application clusters**

> **Purpose.** This directory presents concrete feasibility studies of the [paceval. Mathematical Engine](https://paceval.com/): an expression-based, reusable mathematical execution layer for technical software, AI toolchains, edge systems, industrial analytics, financial models and scientific research. Each project supplies its own source code, English README, research whitepaper and experimental artifacts. The projects are research demonstrators, not automatically validated commercial products or certified applications.

**Portfolio snapshot:** 42 project directories · 42 project READMEs · 42 main English research whitepapers · 42 principal C++ demonstrators · supporting Python validation and plotting utilities, numeric outputs and figures. Inventory based on the supplied project archive (November 2026).

## The common paceval architecture

```text
Application / engineering model / agent request
                  |
       Input validation and model selection (host)
                  |
      Explicit mathematical expression / version
                  |
      paceval CreateComputation (prepare once)
                  |
         Reusable computation graph / handle
                  |
     paceval GetComputationResult* (evaluate repeatedly)
                  |
      Numerical outputs, optional TINC information
                  |
       Host workflow / independent verification
```

paceval converts explicit mathematical expressions into reusable computation structures, separating mathematical execution from orchestration and application logic. In these projects, C++ typically constructs formulas and calls the original paceval SDK facade (`paceval_main.h` / `paceval_main.cpp`), while the host retains responsibility for data generation, numerical solvers, simulations, model selection, scoring workflows, validation, and integration as appropriate. **The presence of paceval calls does not mean that every algorithm in the application executes inside paceval.** [Official repository](https://github.com/paceval/paceval) · [Developer overview](https://paceval.com/developers/) · [TINC overview](https://paceval.com/tinc/).

## Explore by research cluster

| Cluster | Projects | Core research focus |
|---|---:|---|
| [1. AI agents, mathematical tool use and verifiable computation](#cluster-1) | 9 | Deterministic mathematical tool boundaries, validation of generated formulas, reusable calculations and auditable computational workflows. |
| [2. Edge computing, inference post-processing and operational monitoring](#cluster-2) | 5 | Reusable mathematical rules at the edge, including sensor and inference-derived scoring, with clear separation from data collection and learned-model inference. |
| [3. Manufacturing, industrial operations and digital twins](#cluster-3) | 8 | Explicit mathematical models for industrial simulation, planning, quality, inventory and formula discovery. |
| [4. Robotics and motion mathematics](#cluster-4) | 3 | Kinematic expressions, robot calibration residuals, trajectory costs and simplified collision-related scores. |
| [5. Energy systems and plasma-related engineering](#cluster-5) | 3 | Mathematical kernels for grid flexibility, wind-farm energy estimation and fusion-inspired diagnostic/control studies. |
| [6. Financial services, insurance and quantitative risk](#cluster-6) | 8 | Reusable mathematical kernels for valuation, risk measurement, scenarios and scoring; not complete regulated production platforms. |
| [7. Space, physical sciences and frontier research](#cluster-7) | 5 | Explicit classical mathematical submodels used in controlled physics and aerospace research demonstrators. |
| [8. Biomedical signal feature rules](#cluster-8) | 1 | Non-clinical mathematical scoring of extracted physiological signal features. |

## Project catalogue

Each entry opens the project’s local README and directly links its scientific whitepaper and main C++ source. Relative links are designed to work when this file is placed at the root of **`TOP+ Industrial Research Projects with paceval/`**. Projects appear in one primary cluster even where their use cases overlap.

<a id="cluster-1"></a>
### 1. AI agents, mathematical tool use and verifiable computation (9)

Deterministic mathematical tool boundaries, validation of generated formulas, reusable calculations and auditable computational workflows.

| Project | Demonstrated research scope | Whitepaper | C++ source |
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
### 2. Edge computing, inference post-processing and operational monitoring (5)

Reusable mathematical rules at the edge, including sensor and inference-derived scoring, with clear separation from data collection and learned-model inference.

| Project | Demonstrated research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Edge AI Postprocessing](paceval_Edge_AI_Postprocessing/README.md) | Apply deterministic mathematical scoring to precomputed AI outputs. | [PDF](paceval_Edge_AI_Postprocessing/paceval_Edge_AI_Postprocessing_Whitepaper_EN.pdf) | [C++](paceval_Edge_AI_Postprocessing/src/edge_ai.cpp) |
| [Industrial Gateway](paceval_Industrial_Gateway/README.md) | Execute versioned telemetry rules in an offline industrial gateway replay. | [PDF](paceval_Industrial_Gateway/paceval_Industrial_Gateway_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Gateway/src/gateway_rules.cpp) |
| [On Device Expression Runtime](paceval_On_Device_Expression_Runtime/README.md) | Prepare reusable expressions for bounded-input device-side evaluation. | [PDF](paceval_On_Device_Expression_Runtime/paceval_On_Device_Expression_Runtime_Whitepaper_EN.pdf) | [C++](paceval_On_Device_Expression_Runtime/src/on_device_runtime.cpp) |
| [Explainable Anomaly Detection](paceval_Explainable_Anomaly_Detection/README.md) | Evaluate versioned anomaly-scoring formulas on synthetic sensor streams. | [PDF](paceval_Explainable_Anomaly_Detection/paceval_Explainable_Anomaly_Detection_Whitepaper_EN.pdf) | [C++](paceval_Explainable_Anomaly_Detection/src/anomaly_detection.cpp) |
| [Predictive Maintenance](paceval_Predictive_Maintenance/README.md) | Calculate mathematical vibration-condition features and health scores. | [PDF](paceval_Predictive_Maintenance/paceval_Predictive_Maintenance_Whitepaper_EN.pdf) | [C++](paceval_Predictive_Maintenance/src/predictive_maintenance.cpp) |

<a id="cluster-3"></a>
### 3. Manufacturing, industrial operations and digital twins (8)

Explicit mathematical models for industrial simulation, planning, quality, inventory and formula discovery.

| Project | Demonstrated research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Digital Twins Simulation](paceval_Digital_Twins_Simulation/README.md) | Evaluate reusable mathematical submodels in a synthetic thermal digital twin. | [PDF](paceval_Digital_Twins_Simulation/paceval_Digital_Twins_Whitepaper_EN.pdf) | [C++](paceval_Digital_Twins_Simulation/src/digital_twin.cpp) |
| [Industrial Control](paceval_Industrial_Control/README.md) | Evaluate objective and constraint terms in an offline MPC-style study. | [PDF](paceval_Industrial_Control/paceval_Industrial_Control_Whitepaper_EN.pdf) | [C++](paceval_Industrial_Control/src/industrial_control.cpp) |
| [Quality Scrap Scores](paceval_Quality_Scrap_Scores_Research/README.md) | Apply mathematical quality-risk and inspection-routing scores. | [PDF](paceval_Quality_Scrap_Scores_Research/paceval_Quality_Scrap_Scores_Whitepaper_EN.pdf) | [C++](paceval_Quality_Scrap_Scores_Research/src/quality_scores.cpp) |
| [Inventory Replenishment](paceval_Inventory_Replenishment_Research/README.md) | Compare parameterized inventory replenishment decision rules. | [PDF](paceval_Inventory_Replenishment_Research/paceval_Inventory_Replenishment_Whitepaper_EN.pdf) | [C++](paceval_Inventory_Replenishment_Research/src/inventory_replenishment.cpp) |
| [Auction Bid Formulas](paceval_Auction_Bid_Formulas_Research/README.md) | Evaluate versioned mathematical supplier-bid formulas. | [PDF](paceval_Auction_Bid_Formulas_Research/paceval_Auction_Bid_Formulas_Whitepaper_EN.pdf) | [C++](paceval_Auction_Bid_Formulas_Research/src/auction_bids.cpp) |
| [Industrial 3D](paceval_Industrial_3D_Research/README.md) | Generate scientific 3D surfaces from computed industrial mathematical models. | [PDF](paceval_Industrial_3D_Research/paceval_Industrial_3D_Diagrams_Whitepaper_EN.pdf) | [C++](paceval_Industrial_3D_Research/src/industrial_3d.cpp) |
| [Material Symbolic Regression](paceval_Material_Symbolic_Regression_Research/README.md) | Evaluate predefined synthetic material-property candidate formulas. | [PDF](paceval_Material_Symbolic_Regression_Research/paceval_Material_Symbolic_Regression_Whitepaper_EN.pdf) | [C++](paceval_Material_Symbolic_Regression_Research/src/material_candidate.cpp) |
| [Symbolic System Identification](paceval_Symbolic_System_Identification/README.md) | Screen candidate nonlinear dynamical-system expressions against trajectories. | [PDF](paceval_Symbolic_System_Identification/paceval_Symbolic_System_Identification_Whitepaper_EN.pdf) | [C++](paceval_Symbolic_System_Identification/src/system_identification.cpp) |

<a id="cluster-4"></a>
### 4. Robotics and motion mathematics (3)

Kinematic expressions, robot calibration residuals, trajectory costs and simplified collision-related scores.

| Project | Demonstrated research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Robotics Trajectory Planning](paceval_Robotics_Trajectory_Planning/README.md) | Evaluate planar robot kinematics, trajectory scores and simplified constraints. | [PDF](paceval_Robotics_Trajectory_Planning/paceval_Robotic_Trajectories_Whitepaper_EN.pdf) | [C++](paceval_Robotics_Trajectory_Planning/src/robotics.cpp) |
| [Reconfigurable Robotic Trajectory Costs](paceval_Reconfigurable_Robotic_Trajectory_Costs/README.md) | Compare complete candidate trajectories under changeable cost formulas. | [PDF](paceval_Reconfigurable_Robotic_Trajectory_Costs/paceval_Reconfigurable_Robotic_Trajectory_Costs_Whitepaper_EN.pdf) | [C++](paceval_Reconfigurable_Robotic_Trajectory_Costs/src/trajectory_costs.cpp) |
| [Robot Calibration](paceval_Robot_Calibration/README.md) | Evaluate 3D robot forward-kinematic residuals for position calibration. | [PDF](paceval_Robot_Calibration/paceval_Robot_Calibration_Whitepaper_EN.pdf) | [C++](paceval_Robot_Calibration/src/robot_calibration.cpp) |

<a id="cluster-5"></a>
### 5. Energy systems and plasma-related engineering (3)

Mathematical kernels for grid flexibility, wind-farm energy estimation and fusion-inspired diagnostic/control studies.

| Project | Demonstrated research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Demand Response](paceval_Demand_Response/README.md) | Evaluate versioned demand-response incentive and scheduling formulas. | [PDF](paceval_Demand_Response/paceval_Demand_Response_Whitepaper_EN.pdf) | [C++](paceval_Demand_Response/src/demand_response.cpp) |
| [Wind Farm Loss Functions](paceval_Wind_Farm_Loss_Functions/README.md) | Evaluate simplified wake-loss and turbine-power functions. | [PDF](paceval_Wind_Farm_Loss_Functions/paceval_Wind_Farm_Loss_Functions_Whitepaper_EN.pdf) | [C++](paceval_Wind_Farm_Loss_Functions/src/wind_farm.cpp) |
| [Fusion Plasma Control](paceval_Fusion_Plasma_Control/README.md) | Evaluate explicitly defined plasma diagnostic and control-related functions. | [PDF](paceval_Fusion_Plasma_Control/paceval_Fusion_Diagnostics_Whitepaper_EN.pdf) | [C++](paceval_Fusion_Plasma_Control/src/fusion.cpp) |

<a id="cluster-6"></a>
### 6. Financial services, insurance and quantitative risk (8)

Reusable mathematical kernels for valuation, risk measurement, scenarios and scoring; not complete regulated production platforms.

| Project | Demonstrated research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Credit Risk Scorecard](paceval_Credit_Risk_Scorecard_Research/README.md) | Evaluate transparent synthetic credit-scorecard formulas. | [PDF](paceval_Credit_Risk_Scorecard_Research/paceval_Credit_Risk_Scorecard_Whitepaper_EN.pdf) | [C++](paceval_Credit_Risk_Scorecard_Research/src/credit_scorecard.cpp) |
| [Counterparty Exposure](paceval_Counterparty_Exposure_Research/README.md) | Evaluate pointwise counterparty-exposure calculation functions. | [PDF](paceval_Counterparty_Exposure_Research/paceval_Counterparty_Exposure_Whitepaper_EN.pdf) | [C++](paceval_Counterparty_Exposure_Research/src/counterparty_exposure.cpp) |
| [Intraday Risk](paceval_Intraday_Risk_Research/README.md) | Replay versioned intraday market-risk functions. | [PDF](paceval_Intraday_Risk_Research/paceval_Intraday_Risk_Whitepaper_EN.pdf) | [C++](paceval_Intraday_Risk_Research/src/intraday_risk.cpp) |
| [Portfolio Stress](paceval_Portfolio_Stress/README.md) | Evaluate synthetic factor stress scenarios and portfolio P&L expressions. | [PDF](paceval_Portfolio_Stress/paceval_Portfolio_Stress_Whitepaper_EN.pdf) | [C++](paceval_Portfolio_Stress/src/portfolio_stress.cpp) |
| [Monte Carlo Pricing](paceval_Monte_Carlo_Pricing/README.md) | Reuse option payoff formulas inside a host-driven Monte Carlo workload. | [PDF](paceval_Monte_Carlo_Pricing/paceval_Monte_Carlo_Pricing_Whitepaper_EN.pdf) | [C++](paceval_Monte_Carlo_Pricing/src/monte_carlo_pricing.cpp) |
| [Pricing Sensitivities](paceval_Pricing_Sensitivities_Research/README.md) | Evaluate option pricing and analytical sensitivity formulas. | [PDF](paceval_Pricing_Sensitivities_Research/paceval_Pricing_Formula_Sensitivities_Whitepaper_EN.pdf) | [C++](paceval_Pricing_Sensitivities_Research/src/pricing_sensitivities.cpp) |
| [Insurance Tariffs](paceval_Insurance_Tariffs/README.md) | Demonstrate versioned synthetic insurance tariff calculations. | [PDF](paceval_Insurance_Tariffs/paceval_Insurance_Tariffs_Whitepaper_EN.pdf) | [C++](paceval_Insurance_Tariffs/src/insurance_tariffs.cpp) |
| [Trading Indicators](paceval_Trading_Indicators_Research/README.md) | Evaluate mathematical quantitative indicator composites on price-bar data. | [PDF](paceval_Trading_Indicators_Research/paceval_Interchangeable_Trading_Indicators_Whitepaper_EN.pdf) | [C++](paceval_Trading_Indicators_Research/src/trading_indicators.cpp) |

<a id="cluster-7"></a>
### 7. Space, physical sciences and frontier research (5)

Explicit classical mathematical submodels used in controlled physics and aerospace research demonstrators.

| Project | Demonstrated research scope | Whitepaper | C++ source |
|---|---|---|---|
| [Electric Propulsion](paceval_Electric_Propulsion_Research/README.md) | Evaluate parameterized analytical electric-thruster performance maps. | [PDF](paceval_Electric_Propulsion_Research/paceval_Electric_Propulsion_Whitepaper_EN.pdf) | [C++](paceval_Electric_Propulsion_Research/src/electric_propulsion.cpp) |
| [Orbit Parameter Sweeps](paceval_Orbit_Parameter_Sweeps_Research/README.md) | Calculate orbital acceleration components in host-driven orbit propagation. | [PDF](paceval_Orbit_Parameter_Sweeps_Research/paceval_Orbit_Parameter_Sweeps_Whitepaper_EN.pdf) | [C++](paceval_Orbit_Parameter_Sweeps_Research/src/orbit_sweeps.cpp) |
| [Gravitational Inversion](paceval_Gravitational_Inversion_Research/README.md) | Evaluate gravitational-field functions and inversion sensitivities. | [PDF](paceval_Gravitational_Inversion_Research/paceval_Gravitational_Inversion_Whitepaper_EN.pdf) | [C++](paceval_Gravitational_Inversion_Research/src/gravity_inversion.cpp) |
| [Collider](paceval_Collider_Research/README.md) | Execute selected collider-inspired mathematical analysis kernels. | [PDF](paceval_Collider_Research/paceval_Collider_Research_Whitepaper_EN.pdf) | [C++](paceval_Collider_Research/src/collider.cpp) |
| [Quantum](paceval_Quantum_Research/README.md) | Evaluate classical calibration and circuit-expectation mathematics. | [PDF](paceval_Quantum_Research/paceval_Quantum_Research_Whitepaper_EN.pdf) | [C++](paceval_Quantum_Research/src/quantum.cpp) |

<a id="cluster-8"></a>
### 8. Biomedical signal feature rules (1)

Non-clinical mathematical scoring of extracted physiological signal features.

| Project | Demonstrated research scope | Whitepaper | C++ source |
|---|---|---|---|
| [ECG Feature Rules](paceval_ECG_Feature_Rules_Research/README.md) | Evaluate synthetic ECG-feature-to-score mathematical rules. | [PDF](paceval_ECG_Feature_Rules_Research/paceval_ECG_Feature_Rule_Evaluation_Whitepaper_EN.pdf) | [C++](paceval_ECG_Feature_Rules_Research/src/ecg_rules.cpp) |

## How to choose a project

| If you need to investigate… | Start with… |
|---|---|
| Formula execution behind AI agents, mathematical trust boundaries, typed tool calls | Technical AI Agents, LLM Generated Mathematics, Agent Constraint Verification |
| Edge AI output corrections and continuously evaluated industrial rules | Edge AI Postprocessing, Industrial Gateway, On Device Expression Runtime |
| Mathematical scoring, condition monitoring and interpretable alarms | Explainable Anomaly Detection, Predictive Maintenance, Quality Scrap Scores |
| Reusable kinematics and parameterized motion objectives | Robotics Trajectory Planning, Reconfigurable Robotic Trajectory Costs, Robot Calibration |
| Computational finance and versioned scenario models | Monte Carlo Pricing, Portfolio Stress, Credit Risk Scorecard, Pricing Sensitivities |
| Explicit mathematical kernels in scientific computation | Orbit Parameter Sweeps, Collider Research, Quantum Research, Fusion Plasma Control |

## What the research establishes — and what it does not

**Established at the repository level:** Each of the 42 principal C++ research applications contains explicit `paceval_CreateComputation` and `paceval_*GetComputationResult*` calls; each project includes a local README, a main research whitepaper, source code, and numerical or visual supporting material. The individual project READMEs document their stated execution environments, model definitions, outputs and checks. The portfolio itself has been inventoried and source-inspected, but **the 42 programs have not been independently compiled and rerun as part of this portfolio overview**.

**Interpret results narrowly:** Nearly all project workloads are synthetic, illustrative, offline or deliberately scoped to mathematical kernels. Numerical agreement on a fixed test set does not by itself establish general validity, field accuracy, real-time latency, regulatory suitability, safety certification or superiority over optimized alternatives. Benchmark conclusions require matched hardware, compiler options, amortized graph-creation costs, complete pipeline timing, repeated trials and documented baselines.

**Precision and TINC:** Trusted Interval Computation is a paceval capability used or discussed in selected projects, but its presence varies by implementation. A reported pointwise interval check is not automatically a formal enclosure or global proof over a multidimensional input domain. Inspect the individual mathematical assumptions and reference checks before making such claims.

**AI and agent scope:** A deterministic mathematical evaluator does not independently validate an LLM’s intentions, generated model semantics, unit interpretation, security policy or authorization. Offline tool-adapter demonstrations do not amount to an operational LLM or MCP integration unless separately implemented and tested.

**Domain boundaries:** Credit and insurance examples do not establish regulatory compliance or fairness; ECG rules are non-clinical; robot and control exercises do not constitute safety-certified controllers; physics and quantum experiments evaluate selected numerical expressions rather than demonstrating new physical discoveries.

## Reproduce an individual demonstrator

1. Open a project README and read its prerequisites, model scope and numerical validation section.
2. Inspect its `src/` folder, normally including the project-specific C++ main program, `CMakeLists.txt`, and the paceval C/C++ SDK facade files.
3. Supply the compatible original paceval runtime/library as required by that project. Library names and build instructions differ across packages; follow the project-specific instructions rather than assuming one universal command.
4. Build and run the local experiment. Where supplied, compare generated outputs with the committed CSV/JSON/TXT examples and independent Python references.
5. Record the exact platform and library version, rerun numerical tests and distinguish wall-clock runtime from graph construction, host-side preprocessing and I/O.

The supplied SDK facade source files are not a substitute for the external original paceval runtime where the project build requires it. See the official [paceval GitHub repository](https://github.com/paceval/paceval) and [paceval website](https://paceval.com/) for SDK and runtime background.

## Portfolio-wide development opportunities

The strongest follow-up work is comparative and reproducible rather than merely expanding the number of formula families:

1. **Unified benchmarks:** Establish identical native C++ and paceval mathematical semantics, inputs, precision, warm-up, timing and statistical reporting, including graph-creation amortization and full application latency.
2. **Validated numerical envelopes:** Add tolerance policies, independent high-precision references, boundary / pathological cases and interval checks appropriate to the mathematics; state precisely what was covered.
3. **Real data and integration:** Replace selected synthetic replays with permissible industrial, financial or scientific datasets, with data lineage and reproducibility metadata.
4. **Meaningful integration pilots:** Connect the strongest calculation kernels to realistic agent, gateway, simulation or embedded workflows with traceable contracts and controlled formula updates.
5. **Hardware research:** Investigate FPGA or dedicated hardware execution for stable, repeatedly evaluated mathematical graphs, and measure system-level performance and energy on real implementations rather than extrapolating from assumed speedups.
6. **Research governance:** Standardize project metadata (domain, formula ownership, test data, validation reference, runtime version, limitations, evidence tier and licensing) and collect cross-project regression results.

## External context and technical references

The following sources provide industrial or scientific context. They are **not** independent endorsements of the numerical results in this repository.

- [paceval. official website](https://paceval.com/) and [official GitHub repository](https://github.com/paceval/paceval): mathematical expression runtime, execution-graph model and integrations.
- [paceval. developer documentation](https://paceval.com/developers/) and [TINC explanation](https://paceval.com/tinc/): create/evaluate pattern and numerical-precision positioning.
- [Model Context Protocol, tools specification (2026-07-28)](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx): structured tool invocation and integration boundaries for agent-related work.
- [NIST AI RMF Generative AI Profile (2024)](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence): risk framing for generative AI systems and tool-based applications.
- [NIST, Manufacturing Digital Twin Standards (2024)](https://www.nist.gov/publications/manufacturing-digital-twin-standards): digital-twin interoperability and standards context.
- [NIST, Digital Twins Workshops Summary Report (2026)](https://www.nist.gov/publications/digital-twins-workshops-summary-report): verification, validation, uncertainty quantification and integration challenges.

## Scope, status and authorship

**Status:** Collection of published research demonstrators and their supporting artifacts, assembled from the supplied project directory, November 2026. The catalogue is an editorial navigation and synthesis layer; it does not replace project-specific scientific qualifications.

**Repository:** [paceval/paceval](https://github.com/paceval/paceval) · **Software and mathematical engine:** [paceval.](https://paceval.com/) · **Individual research scope and references:** linked project READMEs and whitepapers.
