"""Independent pointwise 80-digit reference check for exported paceval surfaces."""
import csv, json, sys
from pathlib import Path
import mpmath as mp
mp.mp.dps = 80
root = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((root/'examples/gravity_surface.csv').open()))
sel = rows[::37][:101]
refmu=mp.mpf('398600.4418')*mp.mpf('1.0007')
refj=mp.mpf('0.00108262668')*mp.mpf('1.035')
R=mp.mpf('6378.137')
results=[]
for r in sel:
    radius=mp.mpf(r['r_km']); c=mp.mpf(r['cos_colatitude']);p2=(3*c*c-1)/2
    potential=refmu/radius*(1-refj*(R/radius)**2*p2)
    field=refmu/radius**2*(1-3*refj*(R/radius)**2*p2)
    # Exported decimal strings represent double outputs, not exact mathematical inputs.
    for column,reference in [('potential_km2_s2',potential),('radial_km_s2',field)]:
        actual=mp.mpf(r[column]); deviation=abs(actual-reference)
        assert deviation < mp.mpf('3e-12')*(1+abs(reference)),(column,deviation)
        results.append(float(deviation))
report={'precision_decimal_digits':80,'samples':len(sel),'checked_outputs':len(results),'all_pass':True,'maximum_absolute_difference':max(results),'caveat':'Reference uses exported decimal inputs; this is a finite pointwise test, not a global error certificate.'}
(root/'results/high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
