# Mathematical model, units, limits and responsibilities

## Research model

The study covers two idealized moving balls or conservative spherical bounds represented in a common Cartesian coordinate system. Their center difference has quadratic polynomial components in normalized motion time $u\in[0,1]$. All coefficients are deterministic multiples of 1/256 metre. The demonstrator uses a one-second time horizon, so dimensionless $u=t/(1\mathrm{s})$ is also numerically equal to seconds elapsed. Radius components $r_1,r_2$ and optional buffer $b$ are nonnegative constants. Input values are not actual measurements from a robot plant.

```math
x(u)=x_0+x_1u+x_2u^2,\quad y(u)=y_0+y_1u+y_2u^2,\quad z(u)=z_0+z_1u+z_2u^2.
```

```math
F_v(u)=x(u)^2+y(u)^2+z(u)^2-R_v^2,
\quad R_1=r_1+r_2,\quad R_2=r_1+r_2+b.
```

The squared distance margin has units m² and is **not** interchangeable with physical surface clearance in metres. Physical signed clearance is $c_v=\sqrt{D}-R_v$ with $D=x^2+y^2+z^2$. The sign is identical for valid radii. The time derivative is $F_v'=2(xx'+yy'+zz')$. The second derivative is $F_v''=2(x'^2+y'^2+z'^2+xx''+yy''+zz'')$. The explicit sensitivity to $x_0$ is $2x$; to $x_1$ is $2ux$; to $b$ is $0$ for V1 and $-2R_2$ for V2.

## Proof status

The C++ host generates all candidates at stationary points and endpoints via numerical polynomial root isolation; it retrieves candidate margins through original paceval graphs. This is validated numerically but is not an interval certificate by itself. The separate Python verifier builds the quartic polynomial with arbitrary-precision `fractions.Fraction` coefficients **from exact dyadic input values**, maps power coefficients to degree-four Bernstein coefficients, recursively subdivides at exact dyadic endpoints, and uses their convex-hull bounds. All Bernstein coefficients strictly greater than zero prove strict separation throughout the subinterval. If a rational evaluation is negative, an overlap has been witnessed. A rational zero proves contact at that exact instant. The verifier records an explicit `UNRESOLVED` status if the interval bound is inconclusive at maximum depth. It does not use pointwise paceval TINC as a range proof.

The word *certified* in this package refers only to these exact rational statements about this mathematical quartic on $[0,1]$, not ISO 10218 certification, robot-arm safety, controller timing, correct calibration of bounding spheres, missing obstacles, human presence, network delay or end-effector tracking error. The proof would not automatically extend to splines of higher degree, arbitrary meshes, joint-space models or uncertain coefficients.

## Model-version semantics

V1: sum of two nominal geometric spheres. V2: sum of the same spheres plus a fixed illustrative conservative spatial buffer. Both graph families are loaded concurrently and evaluated independently. More V2 overlaps are therefore expected by construction; this is not evidence that a software engine is inaccurate or that V2 physically models actual measured uncertainties.

## Computational ownership

* `paceval`: position, relative velocities, distance, squared margin, physical clearance, first/second derivatives, speed, score, math guards, sensitivity and difference functions.
* `C++ host`: input schema validation, exact input boundary checks, graph handle lifetime, root-isolation control, selection of minimum among original paceval values, CSV and metadata output.
* `Python reference`: exact rational interval algebra and independent mpmath numerical reference. Both are validation workflows, not the source of the published paceval output values.

Every coefficient is finite with absolute value at most 8. The individual radii must be positive, the optional buffer nonnegative and total inflated radius below two metres. Piecewise trajectory segments, tracking uncertainty envelopes, rigid-body kinematics, compliance, rotation and dynamic collision response are outside scope.
