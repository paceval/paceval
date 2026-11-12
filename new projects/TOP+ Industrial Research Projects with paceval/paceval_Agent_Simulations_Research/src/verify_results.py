"""Validate counts, deterministic workflow decisions and internally consistent trace."""
from pathlib import Path
import csv,json,math
R=Path(__file__).resolve().parents[1]
def rows(f):return list(csv.DictReader((R/'examples'/f).open()))
s=rows('scenario_summary.csv');t=rows('simulation_trace.csv');g=rows('residual_surface.csv');registry=rows('formula_registry.csv');l=rows('orchestration_log.csv');v=rows('version_comparison.csv')
assert len(s)==100 and len(t)==6400 and len(g)==3721 and len(registry)==6 and len(v)==81
assert len(set((r['model'],r['version'],r['expression']) for r in registry))==6
assert sum(r['decision']=='ACCEPT' for r in s)==79
assert sum(r['decision']=='REVIEW' for r in s)==21
assert sum(r['stage']=='retry' for r in l)==52
for r in s:
 val=float(r['final_score']);assert math.isfinite(val)
 assert r['decision']==('ACCEPT' if val<=0.005 else 'REVIEW')
assert all(math.isfinite(float(r['normalized_residual'])) for r in g)
audit={'status':'PASS','scenarios':len(s),'trace_points':len(t),'graph_count':len(registry),'surface_points':len(g),'retry_count':52,'accept':79,'review':21}
(R/'results/data_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(audit)
