#!/usr/bin/env python3
"""Independent 80-digit Decimal check of selected synthetic formula outputs.

Input CSV contains *native* C++ outputs; the separate application has already
checked every paceval scalar/batch result against its native C++ evaluator.
This script supplies a third, differently implemented numerical audit, and
explicitly does not claim 80-digit paceval computations.
"""
import csv
import json
import sys
from decimal import Decimal, localcontext
from pathlib import Path


def run(input_path: Path, output_path: Path):
    max_diff = Decimal(0)
    count = 0
    errors = []
    with localcontext() as ctx:
        ctx.prec = 80
        for row in csv.DictReader(input_path.open(newline='', encoding='utf8')):
            D = Decimal
            x, temp = D(row['x_dimensionless']), D(row['T_kelvin'])
            a, b, c = D(row['a_GPa']), D(row['b_GPa']), D(row['c_GPa'])
            d, e = D(row['d_kelvin']), D(row['e_GPa'])
            family = int(row['family'])
            if family in (0, 2, 3):
                v = a+b*x+c*(-d/temp).exp()
                if family == 2:
                    v += e*x*x
                elif family == 3:
                    v += e*x*(temp/D(300))
            elif family == 1:
                v = a+b*x+c/(D(1)+temp/d)
            else:
                raise AssertionError(f'Unapproved family: {family}')
            diff = abs(v-D(row['native_prediction_GPa']))
            max_diff = max(max_diff, diff)
            count += 1
            if diff > D('2e-10'):
                errors.append({'sample_id': row['sample_id'], 'difference_GPa': str(diff)})
    audit = {
        'oracle': 'independently coded Python Decimal',
        'decimal_precision': 80,
        'checked_selected_prediction_rows': count,
        'passed': count - len(errors),
        'max_absolute_difference_GPa': str(max_diff),
        'absolute_tolerance_GPa': '2e-10',
        'scope': 'selected candidate only; SDK/native comparisons are separate',
        'errors': errors,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(audit, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k:v for k,v in audit.items() if k!='errors'}, indent=2))
    if count!=60 or errors:
        raise SystemExit(1)

if __name__ == '__main__':
    if len(sys.argv) not in (2, 3):
        raise SystemExit('usage: python3 src/high_precision_reference.py examples/wp019_selected.csv [results/decimal_audit.json]')
    run(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv)==3 else Path('decimal_audit.json'))
