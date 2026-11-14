# Meteorological Ensemble Postprocessing and Site-Level Extreme Weather Decision Kernels with paceval

![Concept illustration of site-level rain, wind and air-frost hazards with the paceval Mathematical Engine](figures/00_weather_risk_hero.png)

*Concept illustration; not a computed research result or an operational forecast map.*

This C++ research demonstrator uses **real reusable paceval computation graphs** to evaluate probabilistic weather-risk expressions and hypothetical site-level action decisions. The project includes a 10,000-site, three-hazard synthetic experiment, independent numerical verification, a PDF research paper and reproducible graphics. It does not run a numerical weather prediction model and does not issue operational weather warnings.

[Read the English scientific whitepaper](paceval_Meteorological_Ensemble_Decision_Kernels_Whitepaper_EN.pdf) | [C++ source](src/weather_kernels.cpp) | [Reproducible results](results/execution_evidence.json) | [Original research proposal](docs/Original_Meteorological_Research_Proposal_2026-11-14.pdf)

## 1. Industrial use case and current state of the art

Utilities, logistics networks and industrial infrastructure operators need to translate numerical weather model ensembles into site-specific, auditable preparations. A regional ensemble probability alone is not a measurement of possible damage at a particular site. A realistic workflow first checks the forecast issue, valid-time interval, ensemble member count, physical units, observation matching and site representativeness. It then evaluates a defined weather event, may statistically postprocess its probability using historically fitted coefficients and finally combines that probability with *asset-dependent* loss, mitigation effectiveness and action cost.

This research deliberately separates three events: (1) at least **20 mm of 24-hour precipitation**, (2) at least **25 m/s of 6-hour peak wind gust**, and (3) an **overnight minimum 2-metre air-temperature event below 0 °C**. These are illustrative event specifications, not universal industrial thresholds. The last event is **not** a prediction of surface icing; precipitation is **not** a flood-depth model and wind gust is **not** a structural-damage calculation. The frost synthetic input is expressed as a *hazard-oriented* variable `-temperature_C`, so all three events can use a common threshold-exceedance contract.

ECMWF's free open IFS data includes a 0.1-degree tier from 20 October 2026, but the open portal is a short rolling archive of recent forecast cycles. NOAA GEFSv12 reforecasts provide a possible historical path with different member coverage and available variables. DWD ICON-EPS and DWD CDC station data are other potential integration sources. Appropriate **forecast-skill** evaluation requires actual time-aligned historical forecasts, verifying observations, training/holdout segregation, and meaningful event counts. This synthetic study makes no claim about observed meteorological skill. See the sources near the end of this README.

## 2. Verified research scope

The main experiment uses **10,000 synthetic sites**, four nominal lead horizons (24/48/72/96 h), three distinct event windows, and **51 synthetic ensemble members** for each feature record. Each of the 120,000 feature records is processed with two separate mathematical model versions, yielding 240,000 model-case evaluations. The model coefficients are **fixed illustrative parameters**, not coefficients fitted to historical station observations. The independently generated binary outcomes are **synthetic**, not weather observations.

The executable creates **60 distinct, executed paceval graphs**, makes **7,460,172 actual graph-point evaluations**, and checks their mathematical results with a separately implemented native C++ model. The independent Python audit verifies 1,890 selected rows (20,790 individual results) with 80 decimal digits, plus sampled compound-event bounds. The source of counts is [execution_evidence.json](results/execution_evidence.json), with separate [validation evidence](results/validation_evidence.json). Repeated verification runs are not added to the main execution count.

## 3. Mathematical model and actual execution ownership

For `k` threshold-exceeding ensemble members among `n` valid members, the smoothed exceedance and its logit are:

$$q=(k+0.5)/(n+1),\qquad u=\ln\left((k+0.5)/(n-k+0.5)\right).$$

A version-specific fixed coefficient vector determines a model logit `z` from `u`, standardized ensemble-mean anomaly, normalized spread, site-to-grid height difference, day-of-year harmonic predictors and lead time. Model **v2** additionally includes a bounded squared-anomaly term. The candidate postprocessed probability is computed as $p=\operatorname{sig}(z)$. Both coefficient sets remain accessible without modifying or replacing the other version's handles. No claims of historical calibration or automatic differentiation are made.

The Brier contribution for an observed synthetic label `y` is $B=(p-y)^2$. The synthetic expected net benefit of an optional protective action is $M=p e L-C$, where `e` is mitigation fraction, `L` is avoidable event loss and `C` is action cost. The probability boundary $p_*=C/(eL)$ is meaningful only for validated `eL>0`. An affirmative `M` value alone does not authorize a physical action. The C++ policy classifies **ACTION_CANDIDATE**, **REVIEW** or **NO_ACTION**, according to a disclosed illustrative probability review threshold of 0.25 and the paceval-computed margin.

For two weather events with model probabilities `pA` and `pB`, paceval computes the Fréchet bounds $\max(0,p_A+p_B-1)\le P(A\cap B)\le\min(p_A,p_B)$. The code **does not** multiply marginals under an unsupported independence assumption.

| Function and industrial purpose | Actual implementation | Graph/version or host rationale |
|---|---|---|
| Raw count and feature preparation | C++ host | Member loops; categorical and temporal data |
| Smoothed exceedance, logit, normalized features | paceval | 12 primary graphs per model version |
| Candidate probability and analytic sensitivities | paceval | Separate persistent primary graphs, v1 and v2 |
| Per-case Brier loss and action-value functions | paceval | 17 secondary graphs per model version |
| Logical/relational probability guards and indicators | paceval | Actual secondary expression graphs |
| Fréchet bounds for matched pairs | paceval | 2 shared persistent graphs |
| Grouping, reliability bins, categorical policy decisions | C++ host | Stateful grouping and business-policy control |
| Native and 80-digit mathematical reference | Separate C++ and Python | Validation only; never substituted for production results |

[The complete mathematical execution inventory](results/math_execution_inventory.csv) assigns the true owner, formula and API path to every major function. [The formula registry](results/formula_registry.csv) captures the actual expressions. The C++ application supplies paceval results from the first stage as validated inputs to second-stage graphs, rather than replacing downstream domain calculations with native C++.

## 4. Reproduced numerical study

Results are stored as CSV generated **by the real C++ paceval execution path**. The input dataset is created deterministically, written as [synthetic_ensemble_features.csv](results/synthetic_ensemble_features.csv), then **read back through `paceval_dConvertStringToFloat`** before graph evaluation. Numerical outputs are written using **`paceval_dConvertFloatToString`**. Strict numeric-literal validation rejects unexpected expressions in CSV numeric fields. The roughly 15-digit text representation is not claimed to be an exact round-trip encoding of any arbitrary IEEE-754 `double`.

The [per-hazard and per-horizon summary](results/hazard_window_summary.csv) shows model probability, Brier contribution, mean expected loss and counts of each hypothetical policy status. [Reliability bins](results/reliability_bins.csv) show model probabilities and the frequency of the **synthetic** event labels. These are useful for numerical demonstrations but cannot establish forecast skill. The [probability response surfaces](results/paceval_probability_surfaces.csv) are generated by actual paceval graph calls. [Sampled matched-event bounds](results/compound_bounds_samples.csv) are evaluated without assuming independent weather events.

## 5. Scientific diagrams

All numbered scientific results except the explicitly marked concept architecture are plotted from original paceval output CSV using [make_figures.py](src/make_figures.py). PNG and vector PDF counterparts are included. Highlights are the [hazard probabilities](figures/02_event_probabilities.png), [synthetic Brier contributions](figures/04_synthetic_brier.png), [reliability diagrams](figures/07_synthetic_reliability.png), [two paceval probability surfaces](figures/08_probability_surface_v1.png), [analytical sensitivity](figures/10_sensitivity_surface.png), [decision margin examples](figures/11_asset_action_scatter.png) and [compound-event probability bounds](figures/12_compound_frechet_bounds.png).

## 6. Build with the original SDK

The project includes the original `paceval_main.h` and the minimally adapted `paceval_main.cpp` with the original notices intact. It **does not** redistribute the external binary `libpaceval_linux_sharedLIB.so`. Supply a compatible original library yourself. On Linux x86-64 with CMake and a C++17 compiler:

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \
  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/weather_kernels --run --sites 10000 --out results/reproduced
python validation/verify_weather_reference.py results/reproduced
python src/make_figures.py
```

`src/make_figures.py` generates the charts from `results/`, which are the archived main-run outputs. To regenerate plots from the reproduced run, copy the deliberately separate verified `results/reproduced/*.csv` into a new charting workspace rather than overwriting the original archive without checking the expected fingerprints.

The tests exercise numerical CSV conversion, operator semantics, scalar and multi-graph ordering, invalid inputs, an executable synthetic sample, 80-digit reference checks, reproducibility and archive integrity. Detailed numerical tolerances and individual reference comparisons are retained in machine-readable audit and verification scripts rather than presented as competitiveness metrics.

## 7. Scientific interpretation and limits

The successful demonstration is the repeated, versioned and independently checked execution of a defined industrial-meteorological **mathematical processing layer**. It is not an atmosphere model, weather-data ingestion service, historical calibration model, live early-warning platform, financial loss forecast or certified safety function. In particular, the 51-member synthetic ensemble is not downloaded from ECMWF; the binary labels are simulated and the hypothetical asset costs lack empirical calibration. Real external testing would first need a specific historical model version, exact event windows, station matching, lead-time stratification, train/held-out seasons and stable access rights.

TINC is not claimed as a meteorological probability interval or a certification of forecast correctness. Hardware acceleration remains a prospective engineering direction; no CPU/GPU/FPGA/ASIC performance comparison or speedup is included in this research publication.

## 8. Source material and external references

- ECMWF open forecast data, current availability, data licensing and rolling retention: https://www.ecmwf.int/en/forecasts/datasets/open-data
- ECMWF 2026 open data and 0.1-degree publication details: https://confluence.ecmwf.int/spaces/DAC/pages/272310539/ECMWF+open+data+real-time+forecasts+from+IFS+and+AIFS
- NOAA GEFSv12 reforecast archive (2000–2019, different ensemble sizes): https://registry.opendata.aws/noaa-gefs-reforecast/
- ECMWF Forecast User Guide, verification metrics including reliability and Brier: https://confluence.ecmwf.int/pages/viewpage.action?pageId=363864334
- Bonavita and Geer, *Forecast verification using information and noise*, **Quarterly Journal of the Royal Meteorological Society** (2026): https://doi.org/10.1002/qj.70109
- paceval official API and functions: https://paceval.com/api/
- Original research proposal: [PDF](docs/Original_Meteorological_Research_Proposal_2026-11-14.pdf)

*Research generated 14 November 2026. Synthetic numerical research only; not operational weather guidance.*
