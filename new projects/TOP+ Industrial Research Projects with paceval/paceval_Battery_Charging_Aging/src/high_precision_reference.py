"""80-digit independent numerical audit of ACTUAL paceval per-transition outputs.
Uses formula strings recorded by the C++ program, re-evaluated by mpmath; the
scientific source of outputs is the original paceval runtime, not this script.
"""
import csv, json, random
from pathlib import Path
import mpmath as mp
ROOT=Path(__file__).resolve().parents[1]
mp.mp.dps=80
formulas=list(csv.DictReader((ROOT/'examples/formula_registry.csv').open()))
rows=list(csv.DictReader((ROOT/'examples/paceval_transition_audit.csv').open()))
assert len(formulas)==23 and len(rows)>1000
rng=random.Random(20261113)
selection=sorted(set([0,1,5,77,215,1799]+rng.sample(range(len(rows)),min(115,len(rows)))))
variables='p price soc temp dt eta cap cy cal alpha wAge wSmooth pMax socLo socHi co2 drive'.split()
worst_rel=mp.mpf('0');worst_abs=mp.mpf('0');worst_id='';worst_row=0;checks=0
for ix in selection:
    row=rows[ix]
    values={v:mp.mpf(row[v]) for v in variables}
    ctx={**values,'exp':mp.exp,'log':mp.log,'sqrt':mp.sqrt}
    for f in formulas:
        expr=f['expression'].replace('^','**')
        independently=eval(expr,{'__builtins__':{}},ctx)
        actual=mp.mpf(row[f['id']]);diff=abs(actual-independently)
        scaled=diff/(1+abs(independently))
        if scaled>worst_rel:worst_rel=scaled;worst_abs=diff;worst_id=f['id'];worst_row=ix
        assert scaled <mp.mpf('2e-12'),f"High-precision failure {f['id']} at row {ix}: {scaled}"
        checks+=1
result={'independent_precision_decimal_digits':80,'sampled_transition_rows':len(selection),
        'checked_paceval_graph_values':checks,'formula_graphs':len(formulas),
        'maximum_scaled_difference':str(worst_rel),'maximum_absolute_difference_at_worst':str(worst_abs),
        'worst_graph_id':worst_id,'worst_row_index':worst_row,
        'input_source':'ACTUAL executed paceval transition_audit.csv','status':'PASS'}
(ROOT/'results/high_precision_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
