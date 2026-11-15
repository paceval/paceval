# Deterministic three-contact candidate CSV specification

The file `synthetic_contact_candidates.csv` has exactly 81 rows, prefixed by a `case_id` field. The remaining fields are 41 numerical literals: three successive groups of `Fn Ft Fz nx ny R z mu Ncap`, followed by `mass g ex ey ez etx ety etz Ftol Ttol Lref wF wT wM`. The C++ parser requires the exact header and count and uses a dot decimal separator and comma field delimiter; mathematical expressions, `NaN`, `Inf`, unit suffixes, blanks, thousands separators and ambiguous locale formats are rejected.

Units: `Fn`, `Ft`, `Fz`, `Ncap`, `ex`, `ey`, `ez`, `Ftol` are newtons; `tx`, `ty`, `tz`, `etx`, `ety`, `etz`, `Ttol` are newton-metres; `R`, `z`, `Lref` are metres; `mass` is kilograms; `g` is m/s²; `mu` and weights are dimensionless. The unit outward radial normals `(nx,ny)` must satisfy `nx²+ny²=1` to within `1e-12` before graph evaluation. Contact normal `Fn` is compressive-positive, and the applied world force is `(-Fn*nx-Ft*ny,-Fn*ny+Ft*nx,Fz)`.

Geometry G1 has radial offset 40 mm and axial positions (0,0,0) mm. G2 has 55 mm radial offset and axial positions (3,-2,1) mm. G3 has 70 mm offset and axial positions (9,-4,5) mm. All have three fingertip outward radial directions at 0°, 120°, and 240°. These are synthetic geometry parameters, not real identified fingertip placements.

Friction coefficients are `0.25`, `0.40`, `0.60`. The shared normal loads per contact are 8, 11 and 14 N. Axial load perturbations are -0.25, 0 and +0.25 N distributed so the net vertical support still balances the nominal 9.81 N weight. Specified external wrench in v2 is `(0.13,-0.035,0)` N and `(0.01,-0.002,0.004)` N·m. Hard force and torque residual limits are 0.2 N and 0.06 N·m. The score uses `Lref=0.05` m, weights `(1,1,2)` and normal-force capacity 16 N per contact.

Candidate identifiers encode geometry, coefficient, normal-force tier and perturbation: `G1M2F2D1` indicates geometry 1, friction coefficient 0.40, Fn 11 N and the -0.25 N axial perturbation. These symbolic identifiers are not inferred from output values or ordered by score.
