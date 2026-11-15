# Mathematical model specification

The two-state test plant is intentionally synthetic and fixed by the candidate input file. Model V1 uses linear state feedback; V2 adds a bounded smooth term in $\tanh(x)$. The variables $a,b,c,d,k_1,k_2,k_3,p_1,p_2,R,\varepsilon,u_{max}$ are positive or nonnegative in the documented CSV domains, except $k_1,k_2$ which can be negative. All states and actuator units are **normalized simulation units** and **not** physical robot-axis torque or length measurements.

The exact definitions, analytic proof and invariant ellipsoid are given in [the README](../README.md). The implementation uses no hidden automatic differentiation. All explicitly coded gain sensitivities are hand-derived formula strings in the original paceval engine. The host performs fourth-order Runge-Kutta integration using the actual paceval flow graph at every derivative stage.

**Certifier guarantees:** within the stated continuous-time model class, $M_x\ge0$, $M_y\ge0$ and $R\le1$ establish a sufficient negative Lyapunov inequality on a disk and a consequent invariant ellipsoid. A separate global actuator bound makes the input command admissible there. The proof is not a solver for arbitrary nonlinear expressions, and failing the sufficient test does not prove instability.

The product's C API is not a certification body. Any extension to uncertain plants would require a new mathematical derivation with measured uncertainty ranges, matching formal verification tools, calibrated actuator limits and safety review.
