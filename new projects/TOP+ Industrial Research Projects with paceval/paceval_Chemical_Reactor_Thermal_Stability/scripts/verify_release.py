#!/usr/bin/env python3
"""No speed claims. Artifact/internal consistency and link checks only."""
import csv,json,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def readcsv(path):
 with (ROOT/path).open(newline='') as f:return list(csv.DictReader(f))
assert Image.open(ROOT/'figures/00_chemical_reactor_hero.png').size==(2400,1200)
ev=json.loads((ROOT/'results/execution_evidence.json').read_text())['main_run']
inventory=readcsv('results/math_execution_inventory.csv')
formulas=readcsv('results/formula_manifest.csv')
assert len(formulas)==ev['unique_domain_graphs_created']==ev['unique_domain_graphs_executed']==35
assert len([r for r in inventory if r['execution_owner']=='paceval' and r['status']=='executed'])==35
assert len(readcsv('input/scenarios.csv'))==ev['scenario_count']==81
assert len(readcsv('results/equilibria.csv'))==ev['equilibrium_roots']==418
assert len(readcsv('results/profile.csv'))==542
assert len(list((ROOT/'figures').glob('fig*.png')))==10
assert len(list((ROOT/'figures').glob('fig*.pdf')))==10
assert json.loads((ROOT/'results/scientific_audit.json').read_text())['failure_count']==0
import subprocess
output=subprocess.check_output(['pdfinfo',str(ROOT/'paceval_Chemical_Reactor_Thermal_Stability_Whitepaper_EN.pdf')],text=True)
assert any(line.strip()=='Pages:           12' for line in output.splitlines())
checks=[]
for path in sorted(ROOT.rglob('*')):
 if not path.is_file() or path.name in ('checksums.sha256',) or 'build' in path.parts:continue
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 checks.append(f'{digest}  {path.relative_to(ROOT).as_posix()}')
(ROOT/'results/checksums.sha256').write_text('\n'.join(checks)+'\n')
print(f'RELEASE QA PASS: {ev["unique_domain_graphs_executed"]} executed graphs, 10 PNG/PDF chart pairs, 12-page report, {len(checks)} checksums')
