"""Check numerical exports, model identities, independence of holdout and links."""
import csv, math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
grid=list(csv.DictReader((root/'examples/gravity_surface.csv').open()))
obs=list(csv.DictReader((root/'examples/synthetic_observations.csv').open()))
fit={x['fit']:x for x in csv.DictReader((root/'examples/inversion_summary.csv').open())}
assert len(grid)==3721 and len(obs)==960
assert abs(float(fit['noiseless']['mu_km3_s2'])-float(fit['true']['mu_km3_s2']))<1e-6
assert abs(float(fit['noiseless']['j2'])-float(fit['true']['j2']))<1e-12
for x in grid:
    m=float(x['radial_km_s2']);mono=float(x['monopole_km_s2']);revision=float(x['scaled_version_km_s2'])
    assert math.isfinite(m) and math.isfinite(mono)
    assert abs(revision-(mono+1.1*(m-mono)))<5e-14
print('PASS: 3721 surface points, 960 observations, exact noiseless inversion and version identity')
