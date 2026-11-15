# SI data schema

All inputs are synthetic, not actual measurements. The CSV header has `case_id` followed by the 25 variables in `src/formula_manifest.json`, in precisely that order. `mf` and `mp` are kg/s, `LHV` J/kg, `eta` 0..1, `cp`,`cpe` J/(kg*K), `Tin`,`Tout`,`Tw`,`Tamb`,`Tex`,`Tmax` K, `beta` 1/K, external convection `U` W/(m^2*K), `A` m^2, `eps`,`rec` 0..1, `sigma` W/(m^2*K^4), `mex` kg/s, `efco2` kg CO2/kg fuel, `cNOx` mg/Nm^3 on a consistent dry/reference basis, `qflue` Nm^3/s on that same basis, `capco2`,`capnox` kg/s, `fuelcap` kg/s. Host enforces positive temperatures and denominators. Caps are hypothetical, not legal requirements.

The 49-grid variation is fuel mass flow 0.025..0.055 kg/s x external wall skin 350..410 K; assumed NOx concentration covaries with wall test index for sampling coverage only and is NOT a generated physical NOx prediction. Twelve snapshots vary recovery fraction at three values and fuel at four values.
