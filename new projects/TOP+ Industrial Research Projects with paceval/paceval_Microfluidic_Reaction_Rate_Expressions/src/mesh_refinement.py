#!/usr/bin/env python3
"""Independent 32/64/128 cell mesh-refinement research evidence from ORIGINAL
paceval executable runs; output convergence table, not a performance benchmark.
Use after the main 64-cell run. Does not distribute external runtime.
"""
from pathlib import Path
import argparse,csv,subprocess,tempfile

def read(p):
 with open(p,newline='') as f:return {int(x['scenario_id']):x for x in csv.DictReader(f)}
def main(root,exe):
 full=read(root/'results/scenario_summary.csv');assert len(full)==12
 with tempfile.TemporaryDirectory() as temp:
  sample={64:full}
  for n in (32,128):
   folder=Path(temp)/str(n)
   subprocess.run([str(exe.resolve()),'--out',str(folder),'--cells',str(n),'--steps','1440'],check=True,capture_output=True,text=True)
   sample[n]=read(folder/'results/scenario_summary.csv')
  with (root/'results/mesh_refinement.csv').open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['scenario_id','model_version','C_out_N32','C_out_N64','C_out_N128','abs_difference_32_to_64','abs_difference_64_to_128','difference_ratio_64_128_over_32_64','decreasing_difference'])
   ratios=[]
   for i in sorted(full):
    y=[float(sample[n][i]['C_out_mmol_per_L']) for n in (32,64,128)]
    d1=abs(y[1]-y[0]);d2=abs(y[2]-y[1]);q=d2/d1 if d1 else 0.;ratios.append(q)
    w.writerow([i,full[i]['model_version'],*y,d1,d2,q,int(d2<d1)])
 assert all(x<1 for x in ratios),f'Decreasing grid-difference criterion failed: {ratios}'
 print(f'WP047 mesh refinement PASS for all 12 scenarios (N=32,64,128); observed ratio range [{min(ratios):.3f}, {max(ratios):.3f}] (technical method check, not a global PDE theorem).')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--executable',type=Path,required=True);args=p.parse_args();main(args.root,args.executable)
