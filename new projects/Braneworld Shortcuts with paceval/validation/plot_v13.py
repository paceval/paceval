import csv,matplotlib.pyplot as plt,pathlib,numpy as np
root=pathlib.Path(__file__).resolve().parents[1]
def rows(f):return list(csv.DictReader(open(f,newline='')))
new=rows(root/'results'/'paceval_scan_v13.csv'); old=rows(root/'results'/'scan_refined_v12.csv')
a={(float(r['rho0']),float(r['w']),float(r['D'])):r for r in old}
pairs=[(a[(float(r['rho0']),float(r['w']),float(r['D']))],r) for r in new if (float(r['rho0']),float(r['w']),float(r['D'])) in a]
x=np.array([float(p[0]['relative_pct']) for p in pairs]);y=np.array([float(p[1]['relative_pct']) for p in pairs]);
fig,ax=plt.subplots(figsize=(7.5,4.8));ax.scatter(x,y,s=22);v=max(x.max(),y.max());ax.plot([0,v],[0,v],linestyle='--',linewidth=1)
ax.set(xlabel='Archived SciPy v1.2: advance (%)',ylabel='C++17 paceval v1.3: advance (%)',title='47-case cross-implementation agreement');ax.grid(alpha=.2);fig.tight_layout();fig.savefig(root/'figures'/'05_cpp_paceval_v12_comparison.png',dpi=180);plt.close(fig)
conv=rows(root/'validation'/'convergence_v13.csv');n=[int(r['steps']) for r in conv];err=[float(r['abs_error']) for r in conv];
fig,ax=plt.subplots(figsize=(7.5,4.8));ax.loglog(n,err,marker='o');ax.set(xlabel='RK4 steps in log(a) ∈ [0,4]',ylabel='Absolute error in dimensionless Δτ',title='Convergence toward 65-digit MPMath reference');ax.grid(True,which='both',alpha=.2);fig.tight_layout();fig.savefig(root/'figures'/'06_cpp_v13_convergence.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(7.5,4.7));
for rr in sorted(set(float(r['rho0']) for r in new)):
  subset=[r for r in new if float(r['rho0'])==rr and float(r['D'])==1.0]
  subset.sort(key=lambda r:float(r['w']))
  ax.plot([float(r['w']) for r in subset],[float(r['relative_pct']) for r in subset],marker='o',label=f'rho0={rr:g}')
ax.set(xlabel='Fluid equation-of-state w',ylabel='Conditional arrival-time advance (%)',title='Parameter dependence at receiver D=1 (where bracketed)');ax.grid(alpha=.2);ax.legend();fig.tight_layout();fig.savefig(root/'figures'/'07_cpp_v13_parameter_dependence.png',dpi=180);plt.close(fig)
