# Deterministic synthetic input schema

`synthetic_lobe_inputs.csv` contains 64 rows: 16 chatter angular-frequency samples from 3900 to 6900 rad/s, combined with four nonnegative integer lobe orders 0–3. Fields are `case_id,w,mone,kone,cone,mtwo,ktwo,ctwo,alpha,Ks,depth,teeth,lobe` in this exact order. Numeric CSV values are canonical period-decimal literals with comma delimiters and UTF-8, no expressions, units or missing values in numeric fields.

Units: w rad/s, masses kg, stiffness coefficients N/m, viscous damping Ns/m, alpha dimensionless, Ks effective orientation-adjusted N/m², depth m, teeth integer and lobe nonnegative integer. Synthetic settings: m1=1 kg, k1=14 MN/m, c1=1200 Ns/m; m2=1 kg, k2=42 MN/m, c2=1800 Ns/m and alpha=0.3. Cutting coefficient Ks=1 GN/m², selected depth 6.5 mm and four teeth. Values are **hypothetical** research parameters, not measured spindle FRFs or a fitted cutting-force model.

Host prechecks require a strictly negative oriented receptance real part for both versions before evaluating the -1/(2 Ks ReG) expressions. Positive damping and denominators must be nonzero. Do not infer global stability from a single candidate-frequency depth guard.
