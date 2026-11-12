"""Cross-check exported paceval data against manifest and deterministic policy."""
from pathlib import Path
import csv,json,sys
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'examples'
read=lambda name:list(csv.DictReader((p/name).open()))
r=read('feature_replay.csv');f=read('formula_registry.csv');surf=read('ecg_score_surface.csv');rev=read('formula_version_surface.csv')
assert len(r)==10000, len(r)
assert len(f)==51 and len({x['expression'] for x in f})==51
assert len(surf)==3721 and len(rev)==101
assert all((float(x['score'])>=.65)==(int(x['review_flag'])==1) for x in r)
assert sum(int(x['review_flag']) for x in r)==1658
assert all(0<float(x['score'])<1 for x in r)
assert all(0<float(x['score'])<1 for x in surf)
assert any(abs(float(x['score_v1'])-float(x['score_v2']))>1e-5 for x in rev)
summary=dict(line.strip().split('=',1) for line in (p/'execution_summary.txt').read_text().splitlines() if '=' in line)
assert int(summary['graphs'])==51 and int(summary['records'])==10000
assert int(summary['scalar_evaluations'])==13923 and int(summary['batch_results'])==1600
print('PASS exported replay, unique formulas, immutable revision, flag policy, surface size, summary counts')
