#!/usr/bin/env python3
"""Independent 110-decimal reference and separation-policy regression.

The approved-model expression is read only as published test data. Its actual
mathematics is independently implemented here using Python decimal arithmetic;
we do not invoke the C++ evaluator's parsing or reference functions.
"""
import argparse
import csv
from decimal import Decimal, localcontext
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', required=True)
    parser.add_argument('--manifest', required=True)
    args = parser.parse_args()
    lines=Path(args.manifest).read_text(encoding='utf-8').splitlines()
    assert len(lines)==3 and lines[0]=='model_id=weighted_features_v1'
    variable_names=lines[1].removeprefix('variables=').split(' ')
    expression=lines[2].removeprefix('expression=')
    assert len(variable_names)==48 and len(expression)>180
    assert variable_names==['v'+str(i) for i in range(48)]
    # This expected structure is independently regenerated and compared to the
    # versioned data file; changing the formula requires review and a new ID.
    expected_formula='+'.join(
        f'(({i%7+1}*v{i}/1000)+(v{i}*v{i}/10))' for i in range(48))
    assert expression==expected_formula
    with tempfile.TemporaryDirectory() as temp:
        output=Path(temp)/'model_results.csv'
        result=subprocess.run([args.binary,'--approved-model',args.manifest,
               '--approved-output',str(output)],capture_output=True,text=True,check=True)
        assert 'variables=48' in result.stdout and 'input_samples=16' in result.stdout
        rows=list(csv.DictReader(output.open(newline='',encoding='utf-8')))
        assert len(rows)==16
        max_abs=Decimal(0)
        with localcontext() as ctx:
            ctx.prec=110
            for j,row in enumerate(rows):
                assert int(row['sample'])==j
                reference=Decimal(0)
                for i in range(48):
                    x=Decimal(j+1)/Decimal(64)+Decimal(i%7)/Decimal(256)
                    reference+=Decimal(i%7+1)*x/Decimal(1000)+x*x/Decimal(10)
                actual=Decimal(row['paceval_result'])
                difference=abs(actual-reference)
                max_abs=max(max_abs,difference)
                assert difference<=Decimal('3e-11')*(1+abs(reference)),(j,difference)
        # An altered owner-approval manifest must be rejected before paceval
        # graph creation. It is not enough to label arbitrary input 'trusted'.
        modified=Path(temp)/'tampered_model.txt'
        modified.write_text(Path(args.manifest).read_text().replace('v47/1000','v47/999'),encoding='utf-8')
        reject=subprocess.run([args.binary,'--approved-model',str(modified),
            '--approved-output',str(output)],capture_output=True,text=True)
        assert reject.returncode!=0 and 'does not match owner-approved' in reject.stderr
        untrusted=subprocess.run([args.binary,'--formula',expression,
           '--values','0.2,-0.1,0.5,0.3,1.2,0.1'],capture_output=True,text=True,check=True)
        assert '"status":"RESOURCE_LIMIT"' in untrusted.stdout
        print('PASS: 48 variables,',len(expression),'expression chars, 16 samples,',
              'independent 110-digit audit, tamper rejection and untrusted policy preserved;',
              'max absolute error',max_abs)


if __name__=='__main__':
    main()
