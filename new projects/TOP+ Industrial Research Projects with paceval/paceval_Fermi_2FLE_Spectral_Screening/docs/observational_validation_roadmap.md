# Roadmap from the 2FLE metadata and synthetic model pilot to astrophysical inference

**None of P2-P7 is performed by the accompanying C++ demonstrator.** This is an actionable plan, not a claim that any source has been classified.

## P0-P1: Reacquire and audit observations

1. Download NASA FSSC October 2026 revision `2FLE_psc_v8.fit(s)` from https://fermi.gsfc.nasa.gov/ssc/data/access/lat/2FLE/ . SHA-256 and preserve catalog revision. This environment did not have this binary file.
2. Confirm 450 total, 377 associated, 73 unassociated, 13 4FGL-related and 60 new sources from original FITS, validating column types, null flags and sky positions. Reconcile Appendix A source metadata and any renamed/updated revisions.
3. Reacquire original `fermi_filter.cpp`, `all_60_screening.csv`, `all_450_reference.csv` and historical `SHA256SUMS.txt` to reproduce the user V4 paper's 110,700 previous paceval evaluations. This package does not contain or reverify those historical artifacts.

## P2: Cross-survey catalog associations

For each source, compare 4FGL DR4, SIMBAD/VizieR, VLASS/NVSS, WISE, Gaia, relevant X-ray, TeV and pulsar catalogs. Preserve localization error ellipses, local counterpart density, chance-association and color/timing consistency. The PDF `ASSOC3` column is an unconfirmed potential hint only.

## P3-P4: Calibrated Fermi spectral, temporal and spatial analyses

Obtain original Pass-8 photon files, spacecraft/pointing histories, GTIs, matching IRFs, diffuse Galactic/isotropic backgrounds and source templates. Recreate instrument-calibrated ROIs with current Fermitools/Fermipy. Use a forward-folded expected count model and Poisson likelihood over space, energy and time bins. Refit after reasonable background variation, PSF/energy cuts, time splits and null-control regions. A simple catalog-flux score is insufficient. Select 5–10 pilot ROIs, then all 60 if pilot reproducibility gates pass.

## P5: Physically-constrained spectral expression search

Candidate families should include power law, log parabola, exponential cutoff, and physically motivated extensions. paceval can evaluate candidate analytic functions and likelihood kernels after a separate calibrated detector response maps physical source flux to expected counts. State-dependent optimization, response integration, uncertainty propagation and model selection remain external unless independently verified. Penalize complexity and use out-of-sample time/ROI partitions.

## P6: Falsifiable technosignature hypothesis testing

Test T01-T07 only after defining a concrete instrument-band prediction, natural controls, statistical test, trial correction and calibrated injection-recovery sensitivity. The 511 keV annihilation line is below the 20–200 MeV 2FLE band and cannot be directly tested from the 2FLE catalog. Require multi-instrument confirmation and astrophysical source-model separation.

## P7: Scientific status of all 60 sources

Maintain an audit trail of evidence for categories A (natural identification), B (natural compatible), C (artifact), D (inconclusive), E (robust anomaly), F (technosignature hypothesis deserving dedicated test). Report a source-specific status only when its evidence gate has been met. A lack of alternative counterparts or the failure of an incomplete model library is not evidence of technological origin.

References: NASA FSSC https://fermi.gsfc.nasa.gov/ssc/data/access/lat/2FLE/ ; 2026 Fermi LAT collaboration https://arxiv.org/abs/2610.18972 ; Fermipy https://fermipy.readthedocs.io/en/latest/ .
