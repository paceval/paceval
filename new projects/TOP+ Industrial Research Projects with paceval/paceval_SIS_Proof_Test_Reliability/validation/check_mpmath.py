"""Independent 85-decimal-digit reliability reference (not a safety qualification).
Reads the published CSVs, uses separately written survival/integral calculations,
and verifies actual paceval outputs instead of using any graph formula strings.
"""
import csv, json, sys
from pathlib import Path
import mpmath as mp
mp.mp.dps = 85
root = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'results'
evidence = json.loads((root/'execution_evidence.json').read_text())
n = evidence['scenario_count']
ids = set(range(min(16,n))) | {n-1} | {int(i*(n-1)/255) for i in range(256)}
rows={}
with (root/'synthetic_input.csv').open(newline='') as f:
    for k,r in enumerate(csv.DictReader(f)):
        if k in ids: rows[k]={key:mp.mpf(value) for key,value in r.items()}
assert len(rows)==len(ids), (len(rows),len(ids))

def survival(z):
    return -mp.expm1(-z)/z if z else mp.mpf(1)

def quantities(r,v):
    ld,dc,pc,T,H,mttr,beta,target,age,ref=(r[k] for k in ('ld','dc','ptc','interval','horizon','mttr','beta','target','age','ref'))
    u=ld*(1-dc); detected=ld*dc; c=u*pc; unrevealed=u*(1-pc)
    availability=1/(1+detected*mttr); z=c*T; k=2-beta
    survival1=availability*mp.exp(-unrevealed*H)*survival(z)
    pfd=1-survival1 if v==1 else 1-2*survival1+availability**2*mp.exp(-k*unrevealed*H)*survival(k*z)
    x=unrevealed*H+c*age
    inst=1-availability*mp.exp(-x) if v==1 else 1-2*availability*mp.exp(-x)+availability**2*mp.exp(-k*x)
    return pfd,inst

def midpoint_quadrature(r,v):
    rr=r.copy();T=rr['interval']
    def instant(t):
        rr['age']=t
        return quantities(rr,v)[1]
    return mp.quad(instant,[mp.mpf(0),T])/T

checks=0;integral_checks=0;max_err=mp.mpf(0);derivative_checks=0
with (root/'scenario_results.csv').open(newline='') as f:
    for rec in csv.DictReader(f):
        i=int(rec['scenario']);v=int(rec['model'])
        if i not in rows:continue
        r=rows[i]; pfd,inst=quantities(r,v)
        for key,expected,abs_tol in [('pfd_average',pfd,mp.mpf('2e-9')),
                                      ('instant_pfd',inst,mp.mpf('2e-9')),
                                      ('margin',r['target']-pfd,mp.mpf('2e-9')),
                                      ('score',pfd/r['target']+mp.mpf('.03')*(1-r['ptc'])+mp.mpf('.05')*r['beta'],mp.mpf('2e-6')),
                                      ('expected_loss_proxy',pfd*r['ref'],mp.mpf('2e-5'))]:
            delta=abs(mp.mpf(rec[key])-expected)
            if delta>abs_tol:raise AssertionError(f'{key} scenario={i} model={v} delta={mp.nstr(delta,12)}')
            max_err=max(delta,max_err);checks+=1
        if i in {0,1,2,3,4,5,6,7,8,9,10,11}:
            integrate=midpoint_quadrature(r,v)
            if abs(integrate-pfd)>mp.mpf('1e-60'):raise AssertionError('Analytic average differs from 85-digit integral')
            integral_checks+=1
        if i in {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}:
            dt=mp.diff(lambda t: quantities({**r,'interval':t},v)[0],r['interval'])
            dc=mp.diff(lambda c: quantities({**r,'ptc':c},v)[0],r['ptc'])
            for key,val in [('interval_sensitivity',dt),('coverage_sensitivity',dc)]:
                gap=abs(mp.mpf(rec[key])-val)
                if gap>mp.mpf('1e-7'):
                    raise AssertionError(f'{key} discrepancy scenario={i} model={v}: {mp.nstr(gap,12)}')
                derivative_checks+=1

assert checks>1000 and integral_checks>=24
report={'reference':'independent 85-digit mpmath with direct numerical quadrature',
        'sampled_rows_per_model':len(rows), 'verified_quantities':checks,
        'independent_numerical_integrals':integral_checks,
        'analytic_sensitivity_checks':derivative_checks,
        'maximum_tested_absolute_deviation':mp.nstr(max_err,15),
        'result':'PASS', 'scope':'synthetic mathematical equations only; NOT SIL verification'}
(root/'high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS',json.dumps({k:v for k,v in report.items() if k not in {'maximum_tested_absolute_deviation'}},ensure_ascii=False))
