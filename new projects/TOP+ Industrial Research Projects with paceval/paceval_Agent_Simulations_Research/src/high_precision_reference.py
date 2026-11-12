"""Independent 80-digit reference audit of exported paceval surface and model-version results."""
import csv,json
from pathlib import Path
from mpmath import mp
mp.dps=80
R=Path(__file__).resolve().parents[1]
a=list(csv.DictReader((R/'examples/residual_surface.csv').open()))
checks=0;worst=mp.mpf('0')
for k in range(0,len(a),13):
 r=a[k];x=mp.mpf(r['simulated']);y=mp.mpf(r['observed']);actual=mp.mpf(r['normalized_residual'])
 expected=abs(x-y)/(mp.mpf('0.12')+mp.mpf('0.000001'))
 error=abs(actual-expected);worst=max(worst,error)
 if error > mp.mpf('1e-12')*(1+abs(expected)):raise AssertionError((k,str(error)))
 checks+=1
# Independent reference for both retained versions.
for r in csv.DictReader((R/'examples/version_comparison.csv').open()):
 x=mp.mpf(r['x']);base=-mp.mpf('.4')*(x-mp.mpf('.7'))
 for key,ref in [('rhs_v1',base),('rhs_v2',base-mp.mpf('.02')*(x-mp.mpf('.7'))**3)]:
  v=mp.mpf(r[key]);err=abs(v-ref);worst=max(worst,err)
  if err>mp.mpf('1e-12')*(1+abs(ref)):raise AssertionError((key,str(err)))
  checks+=1
result={'status':'PASS','precision_decimal_digits':80,'reference_checks':checks,'max_abs_error_exported_decimal':str(worst),'scope':'selected residual grid points and full version-comparison CSV; no global error proof'}
(R/'results/high_precision_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(result)
