# Mathematical scope, units and physical assumptions

## Absorption channel: `BEER`

The effective wavelength-dependent absorption is $\alpha_{\mathrm{eff}}=\alpha_0(550\,\mathrm{nm}/\lambda)$ and the normalized output is $I=I_0\exp(-\alpha_{\mathrm{eff}}d)+I_{\mathrm{offset}}$. The analytical inverse requires $\alpha_{\mathrm{eff}}>0$, $I_0>0$ and $I>I_{\mathrm{offset}}$. The experiment sets $I_0=1$. Its thickness sensitivity is $\partial d/\partial I=-1/[\alpha_{\mathrm{eff}}(I-I_{\mathrm{offset}})]$. The inverse is unsuitable if the optical intensity approaches the offset or other unmodeled effects dominate.

## Interference channel: `FILM`

Assume one homogeneous, planar, lossless, isotropic layer at **normal incidence**, air incident medium $n_0=1$, constant real refractive index $n_f$ across wavelengths for each site, and a semi-infinite dielectric substrate with positive real $n_s$. The reflectance is formed from the real Fresnel amplitudes and $\cos(4\pi n_fd/\lambda)$, including the coherent multiple-reflection denominator. There are no polarization or angle differences at normal incidence. The unit of $d$ and $\lambda$ is nm. No substrate absorption, scattering, roughness, finite coherence, Fresnel film absorption, backside reflection or multiple finite layers is included.

Define $A=r_{01}^2+r_{12}^2$, $B=2r_{01}r_{12}$, $C=1+(r_{01}r_{12})^2$ and $\phi=4\pi n_fd/\lambda$. The analytical derivative actually implemented by a paceval graph is

```math
\frac{\partial R}{\partial d}=\frac{4\pi n_f}{\lambda}\,
\frac{B\sin\phi\,(A-C)}{(C+B\cos\phi)^2}.
```

A finite stack with unknown dispersive $n(\lambda)+i\kappa(\lambda)$ would need further material models and complex-number algebra. The present model deliberately avoids those unverified capabilities.

## Inversion and identifiability

The host uses a global thickness grid from **88 to 460 nm** and a local golden-section refinement of the best grid minimum, with the objective sum formed from the original paceval residuals. A numerical global grid is not a formal proof of the global optimum. A separate independent SciPy search reproduces the result for the tested cases. A single wavelength has exact aliases at $d+k\lambda/(2n_f)$ for integral $k$; this counterexample invalidates any universal uniqueness assertion.

Local Fisher information is $\sum_j[(\partial R_j/\partial d)/\sigma_R]^2$ under independently weighted normal-noise assumptions, and the local uncertainty proxy is $1/\sqrt{\mathrm{information}}$. It is **not** a calibrated 95% interval and does not include uncertain refractive indices or correlated sensor errors.

## Workflow and acceptance limits

The illustrative screen tests a film target of **235 ± 35 nm** and an inverse-recovery tolerance of 3 nm relative to known synthetic truth. A score cap of 45 on the normalized nine-band objective is a chosen experiment condition. Neither threshold originates from an instrument specification, wafer manufacturing acceptance plan or process qualification.

Zero/negative wavelength, non-positive absorption, non-finite or non-literal numeric inputs, $I\le I_{\mathrm{offset}}$, and unrealistic material-index combinations are refused before evaluation. A guard multiplying an undefined expression by a false boolean is not treated as a safe short circuit.
