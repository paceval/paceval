#!/usr/bin/env python3
"""Generate reproducible, wholly synthetic acceleration windows, not real bearing data.

Asset isolation prevents overlap / label leakage between train, validation and test.
Feature extraction is performed by C++; this script only creates raw waveforms.
"""
import csv, random, math, argparse

def build(path):
    rng=random.Random(20261111)
    with open(path,'w',newline='',encoding='utf8') as fp:
        writer=csv.writer(fp,lineterminator='\n')
        writer.writerow(['asset_id','window_id','split','label','temp_C','sample_index','accel_g'])
        for asset in range(48):
            split='train' if asset<24 else ('validation' if asset<36 else 'test')
            label=asset%2
            for window in range(12):
                temp=60.0+6.0*label+0.25*(asset%5)+0.4*window
                amplitude=0.18+0.025*(asset%4)+0.09*label
                for idx in range(512):
                    x=amplitude*(0.8*math.sin(2*math.pi*idx/27+0.03*asset)+0.3*math.sin(2*math.pi*idx/7))
                    x+=amplitude*0.24*rng.gauss(0,1)
                    if label and (idx+asset*3+window*7)%89 in (0,1):
                        x+=amplitude*3.5 * (-1 if idx%2 else 1)
                    writer.writerow([asset,window,split,label,f'{temp:.12g}',idx,f'{x:.17g}'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True)
    args=ap.parse_args();build(args.output)
