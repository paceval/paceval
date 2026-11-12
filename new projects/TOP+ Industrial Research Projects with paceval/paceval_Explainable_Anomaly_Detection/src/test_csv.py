#!/usr/bin/env python3
"""Test strict input validation and reproducibility with the same SDK binary."""
import argparse,csv,hashlib,subprocess,tempfile
from pathlib import Path

def run(cmd,expect=0):
    r=subprocess.run(cmd,capture_output=True,text=True)
    assert (r.returncode==0)==(expect==0),(cmd,r.returncode,r.stderr[-1000:])
    return r

def hash_file(p):return hashlib.sha256(p.read_bytes()).hexdigest()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--examples',type=Path,required=True);p.add_argument('--batch',type=int,default=37)
    a=p.parse_args();source=a.examples/'signals.csv'
    assert source.is_file(),source
    with tempfile.TemporaryDirectory(prefix='paceval_anomaly_') as td:
        td=Path(td)
        out=td/'replay'
        run([str(a.binary),'--input',str(source),'--out',str(out),'--batch',str(a.batch)])
        for name in ['signals.csv','rules.csv','selected_scores.csv','selection.csv','model_diagnostics.csv',
                     'event_detection.csv','rule_update.csv','tinc_samples.csv','audit_samples.csv','validation.json']:
            assert hash_file(a.examples/name)==hash_file(out/name),name
        raw=source.read_text().splitlines(keepends=True)
        for label,index,field in [('duplicate_minute',5,1),('nonfinite',8,6),('invalid_sigma',9,8),('wrong_split',7,3)]:
            copy=raw[:];cols=copy[index].strip().split(',')
            if label=='duplicate_minute':cols[field]='0'
            if label=='nonfinite':cols[field]='nan'
            if label=='invalid_sigma':cols[field]='0'
            if label=='wrong_split':cols[field]='test'
            copy[index]=','.join(cols)+'\n'
            candidate=td/(label+'.csv');candidate.write_text(''.join(copy))
            run([str(a.binary),'--input',str(candidate),'--out',str(td/label)],expect=2)
        print('PASS: strict CSV validation, four corrupt records rejected; replay byte-identical.')
