"""Structural provenance and decision audit of actual paceval outputs."""
import csv,json,sys,math
from pathlib import Path
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
load=lambda name:list(csv.DictReader((R/'results'/name).open()))
summary=json.loads((R/'results/sdk_run_summary.json').read_text())
rows=load('calibrated_samples.csv');registry=load('graph_registry.csv');scores=load('governance_scores.csv');surface=load('calibration_surface.csv')
assert summary['original_paceval_used'] and summary['model_versions']==2
assert summary['graph_count']==121 and summary['intervals_per_version']==4096
assert len(rows)==1440 and len(registry)==121 and len(scores)==1440*16 and len(surface)==2*61*41
assert all(r['status']=='executed' for r in registry)
assert any(r['decision']=='REJECT' for r in rows) and any(r['decision']=='REVIEW' for r in rows) and any(r['decision']=='ACCEPT' for r in rows)
assert len({r['version'] for r in rows})==2
assert all(math.isfinite(float(r['corrected_value'])) for r in rows)
large=R/'results/large_capacity/sdk_run_summary.json'
if large.is_file():
 a=json.loads(large.read_text())
 assert a['graph_count']==569 and a['intervals_per_version']==65536 and a['model_versions']==2
 print('PASS capacity stress evidence: 569 graphs, two models each with 65,536 intervals')
print('PASS paceval inventory, sample/version traces, scores, rejection paths, graph registry')
