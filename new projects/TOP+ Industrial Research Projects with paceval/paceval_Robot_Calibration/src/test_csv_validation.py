#!/usr/bin/env python3
"""Regression test for strict measurements and reproducible CSV import."""
import argparse,subprocess,csv,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--examples',type=Path,required=True)
a=p.parse_args()
with tempfile.TemporaryDirectory(prefix='robot-calibration-input-test-') as t:
    dst=Path(t)
    cmd=[str(a.binary),'--out',str(dst/'valid'),'--train-csv',str(a.examples/'training_observations.csv'),
         '--holdout-csv',str(a.examples/'holdout_observations.csv'),'--batch','37']
    proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    assert proc.returncode==0,(proc.stdout,proc.stderr)
    for fn in ['train_predictions.csv','holdout_predictions.csv','calibration_trace.csv']:
        assert (dst/'valid'/fn).read_bytes()==(a.examples/fn).read_bytes(),f'CSV roundtrip changed {fn}'
    # Critical validation negatives: nonfinite, invalid joint range and split.
    contents=(a.examples/'training_observations.csv').read_text().splitlines()
    for name,field,value in [('nonfinite',2,'nan'),('bad-range',3,'5.4'),('wrong-split',0,'holdout')]:
        lines=contents.copy();parts=lines[1].split(',');parts[field]=value;lines[1]=','.join(parts)
        source=dst/(name+'.csv');source.write_text('\n'.join(lines)+'\n')
        bad=[str(a.binary),'--out',str(dst/name),'--train-csv',str(source),
             '--holdout-csv',str(a.examples/'holdout_observations.csv')]
        result=subprocess.run(bad,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        assert result.returncode!=0,f'Accepted intentionally invalid data: {name}'
    print('PASS valid CSV replay + rejection of nonfinite input, joint-limit violation and wrong split')
