"""Verify deterministic formula bundle hashes and dataset checksum, no key material."""
from pathlib import Path
import csv,json,hashlib,sys
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
m=json.loads((R/'results/formula_version_manifest.json').read_text());data=list(csv.DictReader((R/'results/graph_registry.csv').open()))
sha=lambda x:hashlib.sha256(x.encode()).hexdigest()
for v in ['v1','v2']:
 r=[d for d in data if d['version']==v];assert len(r)==m['model_versions'][v]['registered_graph_count']
 assert sha('\n'.join(x['graph_id']+'|'+x['expression'] for x in r))==m['model_versions'][v]['formula_bundle_sha256']
assert hashlib.sha256((R/'examples/synthetic_sensor_inputs.csv').read_bytes()).hexdigest()==m['dataset_sha256']
print('PASS graph bundle checksums + synthetic input checksum; not signed')
