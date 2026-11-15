# Research sources and evidence separation

Read on November 15, 2026. Source WP 28 is an unexecuted proposal and specifies only preliminary feedback, quadratic Lyapunov and sampled residual kernels. The nonlinear plant dynamics, sufficient Lyapunov coefficient derivation and experimental dataset are new assumptions in this repository.

- Yang, Dai, Shi, Hsieh, Tedrake, Zhang, ICML 2024: https://proceedings.mlr.press/v235/yang24f.html. Modern Lyapunov-stable learned feedback and region of attraction reasoning.
- Debauche et al., NeSy 2025: https://proceedings.mlr.press/v288/debauche25a.html. CEGIS and formal verifier separate from candidate learning.
- Devadze, Magron and Streif, 2025: https://link.springer.com/article/10.1007/s10817-024-09717-2. Formal sums-of-squares and constructive analysis for discrete-time polynomial systems.
- Wei et al., November 2025: https://doi.org/10.1002/rnc.70279. Research on robust Lyapunov neural control and bounded disturbances. Those robustness results are not assumed in this simplified model.
- dReal: https://dreal.github.io/. Nonlinear SMT with precise `unsat` and `delta-sat` semantics; not executed in this project.
- Original paceval SDK docs: https://paceval.com/api/ and https://paceval.com/product-brief/.

The project is not an implementation of dReal, SOSTOOLS or hardware-in-the-loop control. Its certified inequality follows from explicitly derived analytic sufficient bounds and checked domain assumptions for this restricted mathematical model.
