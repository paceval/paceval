#!/usr/bin/env python3
"""Independent scientific data/integrity checks, including negative controls."""
from pathlib import Path
import csv,json,hashlib,statistics
ROOT=Path(__file__).resolve().parent.parent
read=lambda filename:list(csv.DictReader((ROOT/filename).open()))
reg=read('results/formula_registry.csv'); metrics=read('results/candidate_metrics.csv'); summary=read('results/precision_recall.csv');ref=read('examples/high_precision_reference_samples.csv');surface=read('examples/oscillator_lie_surface.csv')
assert len(reg)==36 and len({r['id'] for r in reg})==36
assert len(metrics)==36*4*2 and len(summary)==24
assert len(ref)==36*16 and len(surface)==65*65
assert sum(int(r['known_invariant']) for r in reg)==12
assert sum(int(r['known_invariant'])==0 for r in reg)==24
assert len({r['model'] for r in reg})==3
for r in summary:
    assert int(r['true_positive'])+int(r['false_negative'])==({'oscillator':4,'kepler':6,'damped':2}[r['model']])
    assert int(r['true_negative'])+int(r['false_positive'])==({'oscillator':8,'kepler':6,'damped':10}[r['model']])
    assert abs(float(r['precision'])-1.0)<1e-12 and abs(float(r['recall'])-1.0)<1e-12
for r in surface:
    assert abs(float(r['energy_lie_abs']))<1e-9
# Perturbed trajectories have a noisier invariant-drift observation metric.
drift=lambda m, noise:[float(r['trajectory_drift_rms']) for r in metrics if r['model']==m and r['known_invariant']=='1' and float(r['noise_sigma'])==noise and r['split']=='heldout']
noise0=drift('oscillator',0.0)
noise2=drift('oscillator',0.02)
assert statistics.mean(noise2)>statistics.mean(noise0)+0.001
report={'catalog':'36 version-pinned candidates, 144 real graphs','true_candidate_count':12,
        'known_false_candidate_count':24,'model_families':3,'classification_test_rows':len(metrics),
        'independent_training_test_splits':2,'noise_sigma_levels':[0,0.005,0.02,0.05],
        'heldout_precision_recall':'All predeclared selected benchmark cases correctly classified; conditional on known exact vector fields and deliberately fixed candidate library',
        'observational_noise_caveat':'The Lie derivative is evaluated against the exact known dynamical vector field at noisy states, not reconstructed from noisy finite differences. Noise enters trajectory drift metrics.',
        'not_a_discovery':'False negatives/positives on this closed library cannot estimate real-world discovery performance.'}
(ROOT/'results'/'scientific_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('scientific data audit passed:',len(metrics),'candidate / noise / split results')
