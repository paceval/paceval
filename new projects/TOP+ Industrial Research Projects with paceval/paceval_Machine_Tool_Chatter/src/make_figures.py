#!/usr/bin/env python3
"""Scientific figures drawn ONLY from archived actual remote paceval MCP outputs."""
from pathlib import Path
import csv,json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from mpl_toolkits.mplot3d import Axes3D  # noqa
R=Path(__file__).resolve().parents[1]
F=R/'figures';F.mkdir(exist_ok=True)
D=list(csv.DictReader((R/'results'/'mcp_boundary_observed.csv').open()))
col=lambda k:np.array([float(x[k]) for x in D]);w=col('w');freq=w/(2*np.pi)
COLORS={'single':'#087F8C','dual':'#E4743E','dark':'#17344E','pale':'#B8D8DB'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.3,'axes.titlesize':13,'axes.titleweight':'bold','axes.labelsize':10,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight'})
def done(fig,key):
 fig.savefig(F/(key+'.png'),dpi=230,facecolor='white');fig.savefig(F/(key+'.pdf'),facecolor='white');plt.close(fig)
fig,ax=plt.subplots(figsize=(9,5));
for name,k,s in [('Single-mode real','re1',COLORS['single']),('Two-mode real','re2',COLORS['dual']),('Single-mode imag','im1','#399FB1'),('Two-mode imag','im2','#EAA175')]:ax.plot(freq,col(k)*1e8,label=name,color=s,lw=2.25,linestyle='--' if 'imag' in name else '-')
ax.axhline(0,color='gray',lw=.8);ax.set(xlabel='Candidate chatter frequency (Hz)',ylabel='Oriented receptance (10⁻⁸ m/N)',title='Two simultaneously available structural receptance models');ax.grid(alpha=.15);ax.legend(ncol=2,fontsize=8);done(fig,'01_modal_receptance_actual_mcp')
fig,ax=plt.subplots(figsize=(9,5));ax.plot(freq,col('b1_m')*1e3,'o-',ms=3.2,lw=2.5,c=COLORS['single'],label='Version 1: one mode');ax.plot(freq,col('b2_m')*1e3,'o-',ms=3.2,lw=2.5,c=COLORS['dual'],label='Version 2: weighted two modes');ax.axhline(6.5,color='#59606C',linestyle=':',lw=1.7,label='Selected cutting depth: 6.5 mm');ax.set(xlabel='Candidate chatter frequency (Hz)',ylabel='Critical axial depth proxy (mm)',title='Candidate-boundary depth changes with the modal model');ax.grid(alpha=.15);ax.legend();done(fig,'02_critical_depth_actual_mcp')
fig,ax=plt.subplots(figsize=(10,5.8));
for lobe in range(4):
 for name,model,color in [('v1','1',COLORS['single']),('v2','2',COLORS['dual'])]:
  xx=col(f'rpm{model}_l{lobe}');yy=col('b1_m' if model=='1' else 'b2_m')*1000
  ax.plot(xx,yy,lw=2,marker='.',markersize=3.0,color=color,alpha=.82 if lobe==2 else .65,linestyle='-' if model=='1' else '--',label=f'{name}, branch {lobe}' if lobe in (0,2) else None)
ax.axhline(6.5,color='#64748B',lw=1.0,linestyle=':',label='Selected depth 6.5 mm');ax.set_xlim(1200,30000);ax.set_ylim(0,22);ax.set(xlabel='Candidate spindle speed (rev/min)',ylabel='Critical axial depth (mm)',title='Analytical regenerative boundary branches (not full milling SLD)');ax.grid(alpha=.15);ax.legend(ncol=3,fontsize=8);done(fig,'03_regenerative_lobe_branches_actual_mcp')
fig,ax=plt.subplots(figsize=(9,4.9));ax.plot(freq,(col('b1_m')-.0065)*1000,color=COLORS['single'],lw=2.5,label='v1 depth margin');ax.plot(freq,(col('b2_m')-.0065)*1000,color=COLORS['dual'],lw=2.5,label='v2 depth margin');ax.axhline(0,color='#343D49',lw=1.2);ax.fill_between(freq,0,(col('b2_m')-.0065)*1e3,where=((col('b2_m')-.0065)<0),color='#F5BFB0',alpha=.65);ax.set(xlabel='Candidate chatter frequency (Hz)',ylabel='Critical depth minus selected depth (mm)',title='Signed margins and version-specific boundary crossings');ax.grid(alpha=.15);ax.legend();done(fig,'04_cutting_depth_margins_actual_mcp')
fig,ax=plt.subplots(figsize=(9,5.0));ax.plot(freq,col('delta_depth_m')*1000,color='#88569F',lw=2.5,marker='o',ms=3);ax.axhline(0,c='#3A4655',lw=1);ax.set(xlabel='Candidate chatter frequency (Hz)',ylabel='Critical-depth delta: two-mode minus single-mode (mm)',title='Second mode can raise or lower the local candidate limit');ax.grid(alpha=.15);done(fig,'05_model_version_depth_difference_actual_mcp')
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(111,projection='3d');
for l in range(4):
 for mod,color,style in [('1',COLORS['single'],'-'),('2',COLORS['dual'],'--')]:
  x=col(f'rpm{mod}_l{l}')/1000;y=freq;z=col('b1_m' if mod=='1' else 'b2_m')*1e3
  ax.plot(x,y,z,color=color,lw=2.2,linestyle=style,alpha=.95)
ax.set(xlabel='Boundary RPM (×1000)',ylabel='Candidate frequency (Hz)',zlabel='Critical depth (mm)',title='3D parameterized branch geometry for both model versions');ax.view_init(elev=24,azim=-64);done(fig,'06_boundary_branches_3d_actual_mcp')
T=json.loads((R/'results'/'tinc_samples.json').read_text())['scenarios'];tx=np.array([float(x['omega'])/(2*np.pi) for x in T]);dd=np.array([float(x['critical_depth_v2']['hi'])-float(x['critical_depth_v2']['lo']) for x in T]);mm=np.array([float(x['depth_margin_v2']['hi'])-float(x['depth_margin_v2']['lo']) for x in T]);fig,ax=plt.subplots(figsize=(9,4.5));ax.plot(tx,dd,marker='o',label='TINC depth output width',c=COLORS['single']);ax.plot(tx,mm,marker='s',label='TINC depth-margin width',c=COLORS['dual']);ax.set_yscale('log');ax.set(xlabel='Candidate chatter frequency (Hz)',ylabel='Printed interval width (m, logarithmic)',title='Actual paceval TINC point-output intervals (not input uncertainty)');ax.grid(alpha=.2);ax.legend();done(fig,'07_tinc_point_bounds_actual_mcp')
print('Scientific figures generated: 7 PNG and 7 vector PDF files, all sourced from recorded paceval MCP data')
