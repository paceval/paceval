#!/usr/bin/env python3
"""Independent decimal-precision (80 dps) evaluation of all saved decision outcomes.
The source algorithm is a numerical decision traversal, not the paceval path-mask code.
All comparisons use recorded decimal strings of the binary64 program output.
"""
import csv, json, sys, collections
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
D=mp.mpf
CENT=[53.0,5.4,7.5,49.0,14.2,0.43]
STEP=[1.25,0.17,0.26,1.4,0.48,0.012]

def threshold(ver,depth,node):
    k=(node*5+depth*3)%7-3
    return CENT[depth]+(STEP[depth]*1.4 if ver==2 else 0.0)+STEP[depth]*k

def leaf_value(ver,leaf):
    base=0.13+0.011*(leaf%23)+0.021*(leaf//23)
    if ver==2: base+=(0.065 if leaf%5==0 else 0.017)
    return base

def close(name,reference,recorded,atol=D('3e-11')):
    error=abs(reference-D(recorded))
    if error>atol:
        raise AssertionError(f'{name}: predicted={mp.nstr(reference,22)} recorded={recorded}, error={mp.nstr(error,8)}')
    return error

def check(path):
    root=Path(path);r=root/'results'/'decision_results.csv';counts=collections.Counter();maxerr=D('0');number=0
    with r.open(newline='') as f:
      for row in csv.DictReader(f):
        ver=int(row['version'][1:]);x=[D(row[k]) for k in ['t_raw','v_raw','p_raw','load','current','drift']]
        temp,vraw,praw,load,current,drift=x
        vc=vraw*(1+D('0.002')*(temp-25))
        pc=praw-D('0.006')*(temp-25)
        xx=[temp,vc,pc,load,current,drift]
        values={'v_corrected':vc,'p_corrected':pc}
        # Branching uses the same binary64 threshold values as generated source,
        # but no path-mask algebra or paceval formula is used in the oracle.
        node=0;leaf=0
        for depth in range(6):
            right=float(xx[depth])>=threshold(ver,depth,node)
            leaf=2*leaf+int(right)
            node=2*node+2 if right else 2*node+1
        base=D(repr(leaf_value(ver,leaf)))
        risk=(base +D('0.11')*(vc/12)**2 +D('0.035')*((temp-45)/55)**2
             +D('0.04')*(current/30)**2 +D('0.03')*drift)
        if ver==2:risk+=D('0.012')*((pc-7)/8)**2
        values.update({'base_score':base,'nested_score':base,'leaf_index':leaf,
                       'path_coverage':1,'final_score':risk,
                       'accept_margin':D('.30')-risk,'reject_margin':D('.43')-risk,
                       'guard_t':87-temp,'guard_v':10-vc,'guard_p':D('12.5')-pc,
                       'guard_l':90-load,'guard_i':26-current,'guard_d':D('0.8')-drift,
                       'dscore_dt':D('0.07')*(temp-45)/55**2,
                       'dscore_dv':D('0.22')*vc/12**2,
                       'dscore_dp':D('0.024')*(pc-7)/8**2 if ver==2 else D('0')})
        for name,expected in values.items():
            err=close(name,expected,row[name]);number+=1;maxerr=max(maxerr,err)
        # This is a policy mapping rather than a paceval-supported continuous formula.
        guards=[values[k] for k in ['guard_t','guard_v','guard_p','guard_l','guard_i','guard_d']]
        status='REJECT' if any(g<0 for g in guards) or risk>=D('0.43') else 'ACCEPT' if risk<D('0.30') else 'REVIEW'
        if status!=row['status']:
            # Rounding at exact boundary is a documented review case, but never silently ignored.
            raise AssertionError(f'status mismatch row {row["sample_id"]}/{ver}: {status} != {row["status"]}')
        counts[(row['version'],status)]+=1
    with (root/'results'/'original_tree_example.csv').open() as f:
        for row in csv.DictReader(f):
            a=float(row['a']);b=float(row['b']);expected=8 if a<0 and b<30 else 11 if a<0 else 7 if b<10 else 9
            assert float(row['paceval_cost'])==float(expected)
    output={'reference':'independent Python / mpmath decimal 80 dps; threshold traversal in binary64 semantic domain',
            'checked_scalar_values':number,'checked_complete_decisions':sum(counts.values()),
            'maximum_abs_difference_audit_only':mp.nstr(maxerr,10),
            'verdict':'PASS',
            'counts':{f'{version}_{status}':count for (version,status),count in sorted(counts.items())}}
    (root/'results'/'independent_80digit_audit.json').write_text(json.dumps(output,indent=2)+'\n')
    print(f'PASS: {number} independent high-precision scalar comparisons, {sum(counts.values())} complete decisions; audit saved')

if __name__=='__main__':check(sys.argv[1])
