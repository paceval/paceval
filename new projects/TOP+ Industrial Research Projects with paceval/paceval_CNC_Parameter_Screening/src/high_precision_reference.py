"""Independent 80-digit check of exported paceval CNC screening computations.
The precision check is internal: no claim of field validation or machine accuracy.
"""
import csv, json
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
root=Path(__file__).resolve().parents[1]
path=root/'examples'/'screening_candidates.csv'
rows=list(csv.DictReader(path.open()))
selected=[rows[i] for i in range(0,8000,19)] + [rows[-1]]
maxerr=mp.mpf('0'); count=0
for row in selected:
    # All input decimal fields are full-precision serialized binary64 numbers.
    vc,fz,ap,ae=[mp.mpf(row[k]) for k in ('vc_m_min','fz_mm_tooth','ap_mm','ae_mm')]
    n=mp.mpf('1000')*vc/(mp.pi*12)
    feed=n*fz*4
    Q=ap*ae*feed/1000
    power=Q*1850/(60000*mp.mpf('.86'))
    life=40*(180/vc)**4*(mp.mpf('.12')/fz)**mp.mpf('.25')
    ra=fz**2/(32*mp.mpf('.8'))
    force=Q*1850/vc
    truth={'rpm':n,'feed_mm_min':feed,'mrr_cm3_min':Q,'motor_kW':power,'life_proxy_min':life,'roughness_proxy_mm':ra,'force_proxy_N':force}
    k=int(row['rule_id']);a=mp.mpf('.28')+mp.mpf('.018')*(k%10);b=mp.mpf('.35')+mp.mpf('.012')*(k%10);c=mp.mpf('.20')+mp.mpf('.008')*(k%10)
    q=Q/20;p=power/5;r=ra/mp.mpf('.001');t=40/life;f=force/1000
    if k//10==0:cost=a*p**2+b*r**2-c*q
    elif k//10==1:cost=a*f**2+b*t**2-c*mp.log(1+q)
    elif k//10==2:cost=a*p+b*r**2+c*t-mp.mpf('.45')*q
    elif k//10==3:cost=a*mp.sqrt(p*p+f*f)+b*r-c*q
    else:cost=a*p*p+b*t*t+c*r*r-mp.mpf('.4')*mp.log(1+q)
    truth['cost']=cost
    for key,val in truth.items():
        error=abs(val-mp.mpf(row[key]))
        maxerr=max(maxerr,error)
        if error>mp.mpf('2e-9')*(1+abs(val)):
            raise AssertionError(f'{row["candidate_id"]} {key} discrepancy {error}')
        count+=1
out={'status':'PASS','precision_digits':80,'selected_candidates':len(selected),'values_checked':count,'max_abs_difference_exported_decimal':str(maxerr),'scope':'Internal independent formula reference; NOT measurement or material calibration'}
(root/'results'/'high_precision_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS independent high-precision check',len(selected),'candidates;',count,'values')
