"""Run N repetitions, check reproducibility, report median and min/max times.

Accepts the actual paceval shared library via --library (not the mock fixture).
No speed claims are made for the fake ABI integration fixture.
"""
import argparse
import csv
from pathlib import Path
import statistics
import subprocess


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--exe',type=Path,default=Path('build/collider'))
    ap.add_argument('--library',type=Path)
    ap.add_argument('--events',type=int,default=120000)
    ap.add_argument('--batch',type=int,default=16384)
    ap.add_argument('--repeats',type=int,default=7)
    ap.add_argument('--out',type=Path,default=Path('results/repeats'))
    a=ap.parse_args()
    if a.repeats<2:ap.error('--repeats >= 2')
    a.out.mkdir(parents=True,exist_ok=True)
    exe=str(a.exe.resolve())
    storage={}
    checksums={}
    for i in range(a.repeats):
        report=a.out/f'run_{i+1:02}.csv'
        command=[exe,'--events',str(a.events),'--batch',str(a.batch),'--csv',str(report)]
        if a.library:command.extend(['--library',str(a.library.resolve()),'--require-paceval'])
        output=subprocess.run(command,check=True,capture_output=True,text=True)
        (a.out/f'run_{i+1:02}.txt').write_text(output.stdout,encoding='utf-8')
        with report.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
        for r in rows:
            if r['backend']=='mock_fixture':raise RuntimeError('Never benchmark mock fixture')
            name=(r['backend'],r['method'])
            storage.setdefault(name,[]).append(float(r['eval_ms']))
            check=checksums.setdefault(name,float(r['checksum']))
            if abs(float(r['checksum'])-check)>1e-8*max(abs(check),1):
                raise RuntimeError(f'Non-reproducible checksum for {name}: {r["checksum"]} vs {check}')
        print(f'Run {i+1}/{a.repeats} OK')
    out=a.out/'summary.csv'
    with out.open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f)
        writer.writerow(['backend','method','repetitions','median_ms','min_ms','max_ms','checksums_consistent'])
        for (backend,method),sample in sorted(storage.items()):
            writer.writerow([backend,method,len(sample),statistics.median(sample),min(sample),max(sample),'yes'])
            print(f'{backend:14} {method:24} median {statistics.median(sample):.4f} ms, min {min(sample):.4f}, max {max(sample):.4f}')
    print('Saved:',out)


if __name__=='__main__':main()
