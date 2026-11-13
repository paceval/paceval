"""Create a deterministic, unsigned checksum manifest for the executed graph versions."""
from pathlib import Path
import csv,hashlib,json
R=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((R/'results/graph_registry.csv').open()))
sha=lambda text:hashlib.sha256(text.encode('utf-8')).hexdigest()
versions={}
for v in ['v1','v2']:
    r=[a for a in rows if a['version']==v]
    stream='\n'.join(a['graph_id']+'|'+a['expression'] for a in r)
    versions[v]={'registered_graph_count':len(r),'formula_bundle_sha256':sha(stream),'status':'synthetic research version, not approved for metrology'}
path=R/'examples/synthetic_sensor_inputs.csv'
manifest={'model_name':'Industrial Mathematical Calibration at Formula Scale','sdk_version':'4.25',
  'formula_approval_status':'RESEARCH_ONLY_NOT_CERTIFIED','dataset_origin':'fully synthetic','model_versions':versions,
  'calibration_domain':{'x':[0,1],'temperature_C':[0,60],'normalized_drift':[-1,1]},
  'knot_ownership':'right interval at internal knots; last interval includes x=1',
  'uncertainty':'uncorrelated input linear propagation, illustrative standard uncertainties only',
  'policy':'ACCEPT if tol - abs(error) - 2*u >= 0; REJECT if tol - abs(error) + 2*u < 0; else REVIEW',
  'dataset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
  'traceability':'none: not a calibrated instrument or accredited laboratory result'}
(R/'results/formula_version_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Wrote versioned checksum manifest')
