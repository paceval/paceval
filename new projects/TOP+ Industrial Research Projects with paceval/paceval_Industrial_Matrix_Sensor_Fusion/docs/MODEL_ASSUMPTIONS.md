# Synthetic SPD and sensor-fusion model definition

The matrix input contains a full lower triangular generating factor `L0` with diagonal

`L0[i,i] = 1.13 + 0.003*(i % 9) + 0.004*version`

and, for `j < i`,

`L0[i,j] = 0.0017*sin((i+1)*(j+1)*0.017) + 0.0012*cos((i+3)*(j+2)*0.021)`.

The synthetic SPD input is `A = L0 * L0.T`. This input generator is implemented in C++ as **input preparation**. The original paceval engine then receives the full dense `A` and computes a new factor and complete inverse through its reusable scalar mathematics graphs. The generator's known factor is not passed to paceval or used to substitute for the factorization.

The sensor-fusion stage is six-dimensional. For each model version `v` and scenario `s`, the two covariance inputs are generated from the full SPD model at version `v` and `1-v`, with illustration-only positive scaling. The observation means and anomaly shifts are fixed functions of `s`. The two covariances are treated as independent; their correlations with other sensors are not modeled.

The information-form fused covariance and state are

`P_f = inverse(inverse(P1)+inverse(P2))`

`m_f = P_f * (inverse(P1)*m1 + inverse(P2)*m2)`.

The squared Mahalanobis innovation is

`d2 = (m1-m2)^T * inverse(P1+P2) * (m1-m2)`.

The illustrative quality scores use a hypothetical threshold of `12.592`. Version 1 is

`q1 = d2 + 0.06*((T-25)/25)^2 + 0.12*r + 0.30*abs(b)`

and version 2 is

`q2 = d2 + 0.09*((T-25)/25)^2 + 0.18*r + 0.18*abs(b)`,

where `r = sqrt(trace(P_f))` and `b = ||m1-m2||_2`. The scores are **not** probabilities or validated engineering acceptance criteria. Continuous signed margins are `g_v = 12.592-q_v`; illustrative host policy assigns ACCEPT when `g_v >= 0`, REVIEW when `-8 <= g_v < 0`, otherwise REJECT.

Explicit analytical temperature sensitivities (holding all other score inputs fixed) are

`dq1/dT = 0.12*(T-25)/625`, `dq2/dT = 0.18*(T-25)/625`.

All matrix arithmetic used to obtain the final model values is executed through actual paceval graphs, except deterministic synthetic matrix preparation, control flow, validation and file serialization by C++.
