"""Validate CSV schema, counts, immutable formula versions, and application decisions."""
import csv,json,math
from pathlib import Path
r=Path(__file__).resolve().parents[1]
def rd(name):return list(csv.DictReader((r/'examples'/name).open()))
c=rd('screening_candidates.csv');surface=rd('cnc_response_surface.csv');rev=rd('formula_revision.csv');regs=rd('formula_registry.csv')
assert len(c)==8000 and len(surface)==3721 and len(rev)==101 and len(regs)==58
assert len(set(x['expression'] for x in regs))==58
assert [int(x['graph_id']) for x in regs]==list(range(1,59))
assert sum(int(x['feasible']) for x in c)==5388
assert len(set(int(x['rule_id']) for x in c))==50
for row in c:
    rpm=float(row['rpm']);p=float(row['motor_kW']);life=float(row['life_proxy_min']);ra=float(row['roughness_proxy_mm']);f=float(row['force_proxy_N'])
    expect=(rpm<=9000 and p<=7.5 and life>=18 and ra<=.0012 and f<=1800)
    assert expect==bool(int(row['feasible']))
for row in surface:
    assert all(math.isfinite(float(v)) for v in row.values())
assert all(float(r['cost_v1'])!=float(r['cost_v2']) for r in rev)
data={'status':'PASS','screening_candidates':len(c),'feasible_candidates':5388,'formula_graphs':len(regs),'surface_points':len(surface),'revision_points':len(rev),'checks':['counts','50 unique score formulas','independent screening decision reconstruction','finite surface','immutable distinct formula version']}
(r/'results'/'data_audit.json').write_text(json.dumps(data,indent=2)+'\n')
print('PASS csv, screening and mathematical model registry verification')
