# Scientific model specification, units, and limits

## Scope and model versions

Synthetic dry-solid flow `solid` (kg/h) and liquid-feed flow `water` (kg/h) mix with initially wet powder whose baseline moisture is `baseMoist` (kg/kg dry solids). The uniform inlet dry-basis moisture is $M_0=\mathrm{baseMoist}+\mathrm{water}/\mathrm{solid}$. The output quality quantity is the **wet-basis** fraction $W=M/(1+M)$, with unit kg water per kg moist granules. Do not confuse this with dry-basis water content $M$.

An illustrative equilibrium moisture combines relative humidity `RH`, air temperature `Tair`, reference temperature `Tref`, and fitted coefficient parameters. The Arrhenius-normalized apparent rate is $k=k_{ref}\exp[-(E_a/R)(1/T_a-1/T_{ref})]$, with `Ea` in joules per mole and temperature in kelvin. Version V1 uses $M_1=M_{eq}+(M_0-M_{eq})\exp(-kt)$. Version V2 uses a weighted pair of exponentials with rates $k(1+s)$ and $k(1-s)$ and fixed fraction $f$. Both are mathematical research surrogates, not measured chemistry- or equipment-specific process models.

## Residence uncertainty and quality margins

A nominal residence time `time` is expanded to a symmetric illustrative interval `[time*(1-rtdWidth), time*(1+rtdWidth)]`. Under the explicitly required domain $M_0>M_{eq}$, $k>0$, $t>0$, and $0<s<1$, moisture decreases monotonically and the shorter interval endpoint is wettest. The long endpoint must remain above `Mmin`, and the short endpoint below `Mmax`; both limits are wet-basis mass fractions. No claim about distribution tails or actual material genealogy is implied.

Product temperature is approximated as `Tin + (Tair-Tin)*(1-exp(-hcoef*time)) - latentCool*(M0-Mout)`. `latentCool` is an illustrative coefficient, not a resolved material-specific heat/mass-balance calculation. Evaporated water is `solid*(M0-Mout)`, and latent-duty indicator is `evaporation*2257/3600` kW. The factor 2257 kJ/kg is a nominal water vaporization heat, not a full dryer energy model. The quality score and all continuous and boolean margins are computed by actual paceval graphs.

The synthetic PAT observation is generated using the V1 model plus noise; this test can verify parser, algebra, model-version mismatch and decision semantics, but cannot validate a real PAT method. The median granule-size proxy is a deliberately uncalibrated straight line with liquid/solid ratio. It cannot predict particle-size distributions or downstream tablet quality.

## Mathematical function owner and clinical/GMP separation

All explicit intermediate functions, compound scores, version deltas, and guards operate in the persisted original paceval graphs as identified in `results/math_execution_inventory.csv`. The C++ host is responsible for unit/domain checks, loop/batch orchestration, output and final label. Native C++ and mpmath are independent reference-only implementations.

The work is *research screening only*. No formula result is a GMP batch-release specification, Process Analytical Technology calibration, real-world quality assurance decision, certification of a design space, diversion-control actuator or regulatory clearance. An eventual pilot must use formulation-specific experimental drying parameters, traced instrument measurements, validated time-residence distributions, uncertainty bounds, appropriate model risk management and a separate change-control/quality-system process.
