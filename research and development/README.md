# SPRIN-D validation summary (English)

## paceval in the SPRIN-D New Computing context

paceval was validated through a SPRIN-D project focused on **faster mathematics with lower energy consumption** implemented as a **mathematical engine in hardware and software**.

The project explored whether the paceval runtime can evolve beyond a software library into a **new kind of mathematical coprocessor architecture** for efficient execution of mathematical models and selected artificial intelligence workloads.

---

## Project objective

The central objective of the SPRIN-D validation project was to assess whether the **paceval mathematical engine** can be implemented in hardware, initially on **FPGA** and later potentially as an **ASIC-based mathematical coprocessor**.

The project specifically examined:

- which parts of the paceval engine can be implemented in hardware
- how hardware and software components can interact efficiently
- how memory and execution interfaces should be designed
- how the system behaves under multi-user and multi-function workloads
- which energy savings can be expected compared to pure software execution
- which follow-up activities are required for further development

---

## Core idea

paceval executes mathematical models as **closed mathematical expressions** and internally transforms them into an efficient execution structure made of atomic operations.

This execution model enables:

- deterministic runtime behavior
- repeated evaluation with caching
- parallel execution across available processors
- transparent and auditable mathematical computation
- a path toward hardware acceleration

In the project this execution principle was studied both in **software** and as a basis for **hardware realization**.

---

## Main results

The SPRIN-D validation project produced several important outcomes.

### 1. FPGA-based reference design

A first reference design was created using an **AMD Xilinx Zynq-7000 SoC** with:

- ARM processors
- FPGA programmable logic
- PetaLinux
- paceval-service as a mathematical engine exposed via REST API

This showed that paceval can be deployed in an embedded hardware context and used as a practical computation engine for mathematical models and AI-related workloads.

### 2. Hardware feasibility study by OFFIS

The project included an external feasibility study by **OFFIS** on how the paceval execution model can be implemented in FPGA hardware.

This study confirmed that the paceval architecture is well suited for hardware realization and offers strong potential for:

- energy-efficient execution
- deterministic behavior
- scalable acceleration of mathematical and AI workloads

### 3. Conversion of neural networks into mathematical expressions

A dedicated expert paper documented a method for converting selected neural networks into **closed mathematical expressions**.

This is strategically important because it enables:

- more transparent and auditable model execution
- deterministic inference
- improved explainability
- stronger certification and regulatory pathways

### 4. Strong energy-efficiency pathway

The project documented a clear path from software execution toward highly energy-efficient hardware execution.

The reported comparison for a neural network benchmark showed:

- conventional CPU + GPU systems at much higher power consumption
- Apple Silicon software execution with strong efficiency
- FPGA-based paceval execution with very low power usage
- a projected ASIC path with even further efficiency potential

This supports the broader thesis that paceval can serve as the basis for **energy-efficient AI and mathematical computing architectures**.

---

## Why this matters

The SPRIN-D project is important because it validates paceval not only as a software library, but as a **broader computing concept**.

It shows that paceval can become:

- a deterministic mathematical runtime
- a transparent execution layer for explainable AI
- a hardware-accelerated mathematical engine
- a foundation for energy-efficient edge and industrial computing

This makes paceval relevant for:

- edge AI
- embedded systems
- industrial automation
- robotics
- scientific computing
- finance
- regulated and safety-critical systems

---

## Strategic significance

The project strengthened paceval in three dimensions.

### Explainability
Mathematical expressions and exported neural models can be executed in a way that is more transparent and easier to audit than conventional black-box inference pipelines.
paceval does not depend on the assumption that every complex neural network automatically becomes fully human-readable. Its practical contribution to explainable AI is more specific: it enables explicit mathematical control layers around model behavior, including readable guardrails, thresholds, correction functions and constraints.

These layers are versionable, auditable and deterministic at runtime, which makes decision-relevant logic easier to inspect, validate and certify even when the underlying model remains complex.

### Energy efficiency
The hardware pathway shows strong potential to reduce power consumption significantly for selected workloads.

### Hardware sovereignty
The architecture is compatible with CPU, FPGA and future ASIC realizations and can also be adapted to open hardware ecosystems such as RISC-V.

---

## Conclusion

The SPRIN-D validation project demonstrated that paceval is more than a fast mathematical library.

It established paceval as a promising foundation for:

- deterministic computation
- explainable AI execution
- energy-efficient runtime systems
- future mathematical coprocessor architectures

In short, the SPRIN-D work confirmed that paceval can evolve from a software engine into a **new execution architecture for trustworthy and efficient computation**.

---

## References

- [SPRIN-D](https://www.sprind.org/en): Federal Agency for Breakthrough Innovation  
- paceval [SPRIN-D validation report](https://github.com/paceval/paceval/blob/main/research%20and%20development/2023JUL%20Update%202e%20final%20SPRIN-D%20Validierungsauftrag%20-%20Abschlussbericht%20paceval.%20-%20Schnellere%20Mathematik%20mit%20noch%20geringerem%20Stromverbrauch.pdf)
- [OFFIS](https://www.offis.de/en/offis/about-us.html) feasibility study on FPGA implementation  
- Expert paper on [converting neural networks into closed mathematical expressions](https://github.com/paceval/paceval/tree/main/paceval%20and%20artificial%20intelligence)

Copyright © 2015-2026 paceval.® All rights reserved.<br>
mailto:info@paceval.com
