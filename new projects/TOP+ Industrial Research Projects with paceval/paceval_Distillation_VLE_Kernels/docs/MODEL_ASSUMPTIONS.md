# Thermodynamic models, domains and scientific scope

The research question is whether the original paceval API can repeatedly evaluate explicit binary vapor-liquid equilibrium and associated distillation screening mathematics, not whether paceval replaces a complete commercial process simulator.

## Model v1: constant relative volatility

The binary equilibrium approximation is $y=\alpha x/(1+(\alpha-1)x)$, with $\alpha=2.6$. The composition $x$ and $y$ are **dimensionless benzene mole fractions**. This model has no temperature dependence and no independent pressure closure; it is not a rigorous vapor-liquid phase equilibrium equation at fixed operating pressure. Its sensitivity is $dy/dx=\alpha/(1+(\alpha-1)x)^2$.

## Model v2: temperature and composition dependent

The pure-component vapor pressures use the original Antoine equation from the NIST Chemistry WebBook, with pressure in bar and temperature in kelvin:

```math
\log_{10} P_i^{sat}(T)=A_i-\frac{B_i}{T+C_i}.
```

| Component | A | B | C | Range |
|---|---:|---:|---:|---|
| Benzene | 4.72583 | 1660.652 | -1.461 | 333.4 to 373.5 K |
| Toluene | 4.07827 | 1343.943 | -53.773 | 308.52 to 384.66 K |

The **common supported range** is 333.4 to 373.5 K. Activity coefficients are hypothetical Margules functions, using $A=0.18$ and mole fraction $x$:

```math
\gamma_A=\exp(A(1-x)^2),\qquad\gamma_B=\exp(Ax^2).
```

The equilibrium numerator $N=x\gamma_A P_A^{sat}$ and complement $M=(1-x)\gamma_B P_B^{sat}$ give $y=N/(N+M)$ and bubble pressure $N+M$. This is a low-pressure ideal-vapor model with non-ideal-liquid correction. The hypothetical activity parameter is not fitted to physical liquid-mixture measurements. It is not a validated benzene/toluene property model.

The analytic derivative at fixed temperature is determined independently and evaluated by paceval, while the host only validates the input domain and transports graph outputs. Along the isobaric bubble curve, derivatives with respect to composition must additionally account for $dT/dx$. The separately reported $dy/dx$ holds temperature fixed.

## Stagewise column screening and heat duty

The demonstration uses an isobaric pressure of 0.60 bar, 100 kmol/h feed and a deliberately simplified material-balanced binary split. The selected feed and product fractions satisfy $x_B<z_F<x_D$. With reflux ratio $R$, the liquid reflux flow is $L=RD$ and the constant-molar-overflow vapor flow proxy is $V=(R+1)D$. Material balances are:

```math
F=D+B,\qquad Fz_F=Dx_D+Bx_B.
```

The condenser is total, the feed is assumed saturated liquid, and the rectifying line is $y_R(x)=(Rx+x_D)/(R+1)$. The stripping line intersects $y_R$ at feed composition $x=z_F$ and passes through $(x_B,x_B)$. Idealized equilibrium-stage stepping is a *McCabe-Thiele-style* host algorithm with a precomputed monotone isobaric paceval VLE table. No explicit tray enthalpy model is solved.

The latent heat is a **synthetic fixed** 31 MJ/kmol. The heat-duty proxy expressed in kW is $Q_{reb}=V(31)/3.6$, with an equal and opposite simplified condenser duty. This is **not a complete column energy balance**. No vapor-liquid hydraulics, feed enthalpy, non-equilibrium mass transfer, azeotrope detection, dynamic startup, or equipment design is included.

## Numerical quality, handling and nonclaims

The host rejects nonfinite and out-of-domain data before graph execution. `min` and `max`, comparisons, Boolean logic, and the distinct `%` and `mod` syntaxes are tested using the original SDK. Guarding a singular expression with a Boolean multiplier does not imply short-circuit execution.

Both models represent separate, immutable computation handles. Each quantitative result is attributed to the SDK's actual executed graph and the downstream host function. Independent native C++ reference formulas and a separate Python 80-digit reference are included. Those checks establish numerical equivalence within the stated model domain, not validity of industrial physical interaction parameters or regulatory approval.
