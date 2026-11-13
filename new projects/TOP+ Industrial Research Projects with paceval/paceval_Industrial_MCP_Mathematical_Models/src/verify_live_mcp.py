#!/usr/bin/env python3
"""Validate newly recorded live MCP responses, without making remote network calls."""
from pathlib import Path
import sys,json,math
from independent_reference import fields
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
main=json.loads((root/'results/live_mcp_main_batch.json').read_text())
mod=json.loads((root/'results/live_mcp_modular_batch.json').read_text())
post=json.loads((root/'results/live_mcp_scoring_batch.json').read_text())
assert len(main['data'])==16
for r in main['data']:
 for v in (0,1):
  result=fields(r,v)[0]
  assert abs(float(result)-r[f'v{v+1}'])<5e-12
assert mod['number_of_module_outputs']==32
for s,expected in zip(mod['inputs'],mod['recombined_graph_major_outputs']):
    inp=dict(zip(['x','y','z','temp'],s))
    assert abs(float(fields(inp,1)[0])-expected)<5e-12
assert max(abs(a-b) for a,b in zip(mod['direct_monolithic'],mod['recombined_graph_major_outputs']))<2e-12
assert post['number_of_graph_outputs']==128 and post['all_mcp_errors_zero']
for ix,vals in [(0,post['first_row_results']),(15,post['last_row_results'])]:
 r=main['data'][ix];a,b=r['v1'],r['v2'];T=r['temp'];target=.16;tol=.03;raw=.15+.16*r['x']+.03*r['y']+.007*(T-25)
 ref=[b-a,b-target,((b-target)/tol)**2+.08*((T-25)/25)**2+.20*abs(b-a)/tol]
 ref += [1-ref[2],.024-abs(b-a),.55*abs(b-target)/tol+.25*abs(b-a)/tol+.20*abs(T-25)/25,50-T,raw-b]
 for p,q in zip(ref,vals):assert abs(p-q)<2e-12,(ix,p,q)
print('PASS live MCP v4.26 archived results: two 256-component models, eight modules, eight downstream graphs')
