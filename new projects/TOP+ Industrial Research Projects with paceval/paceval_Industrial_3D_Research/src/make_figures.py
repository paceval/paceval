#!/usr/bin/env python3
"""Render *only* values exported by the paceval C++ executable.

Requires numpy and matplotlib. A missing CSV is fatal; no replacement/synthetic
figure data are generated here. PNG and vector PDF use the same input arrays.
"""
from pathlib import Path
import argparse, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors

ROOT = Path(__file__).resolve().parent.parent
CASES = [
 ('heat_transfer','Heat-transfer surrogate','Position x (normalized)','Position y (normalized)','Temperature (K)','inferno'),
 ('motor_resonance','Rotating-machine resonance response','Frequency (Hz)','Rotational speed (rpm)','Vibration response (mm/s)','viridis'),
 ('robot_clearance','Robot clearance response surface','End-effector x (m)','End-effector y (m)','Clearance (m)','cividis'),
 ('transformer_hotspot','Transformer hotspot surrogate','Current (p.u.)','Ambient temperature (°C)','Hotspot temperature (°C)','plasma'),
 ('reactor_conversion','Reactor conversion response','Temperature (K)','Residence time (s)','Conversion (0–1)','turbo'),
 ('pressure_loss','Pipeline pressure-loss surrogate','Flow (m³/s)','Roughness (mm)','Pressure drop (kPa)','magma'),
]

def make(data_dir, figures_dir):
 figures_dir.mkdir(parents=True,exist_ok=True)
 for k,(stem,title,xlab,ylab,zlab,cmap) in enumerate(CASES,1):
  path=data_dir/(stem+'.csv')
  if not path.exists(): raise FileNotFoundError('Missing paceval-generated data: '+str(path))
  rows=list(csv.DictReader(path.open()))
  if len(rows)!=81*81: raise ValueError('Unexpected grid length: '+str(path))
  xx=np.empty((81,81));yy=np.empty((81,81));zz=np.empty((81,81))
  for row in rows:
   i,j=int(row['i']),int(row['j'])
   xx[i,j]=float(row['x']); yy[i,j]=float(row['y']); zz[i,j]=float(row['paceval_z'])
  plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'savefig.facecolor':'#0b1725'})
  fig=plt.figure(figsize=(12,5.8),facecolor='#0b1725')
  ax=fig.add_axes([0.035,0.10,0.53,0.79],projection='3d',facecolor='#0b1725')
  surf=ax.plot_surface(xx,yy,zz, cmap=cmap,rstride=2,cstride=2,linewidth=0, antialiased=True)
  ax.view_init(elev=31,azim=-58)
  ax.set_xlabel(xlab,labelpad=8,color='white');ax.set_ylabel(ylab,labelpad=9,color='white');ax.set_zlabel(zlab,labelpad=7,color='white')
  ax.tick_params(colors='white',labelsize=7)
  for a in (ax.xaxis,ax.yaxis,ax.zaxis):
   a.pane.set_facecolor((.05,.12,.19,.6));a.line.set_color((.6,.7,.8,1))
  ax.set_box_aspect((1.2,1,.72))
  ax2=fig.add_axes([.66,.17,.29,.60],facecolor='#12243a')
  ax2.contourf(xx,yy,zz,levels=22,cmap=cmap)
  ax2.contour(xx,yy,zz,levels=9,colors='white',linewidths=.45,alpha=.6)
  ax2.set_xlabel(xlab,color='white',fontsize=8)
  ax2.set_ylabel(ylab,color='white',fontsize=8)
  ax2.tick_params(colors='white',labelsize=8)
  for spine in ax2.spines.values():spine.set_color('#5c7a90')
  fig.text(.035,.95,f'{k:02d}  |  {title}',color='white',size=17,weight='bold')
  fig.text(.035,.02,'Numerical values: paceval C++ SDK 4.25  •  81 × 81 mesh  •  deterministic analytic research model  •  not measured plant data',color='#a9c1d1',size=8)
  fig.savefig(figures_dir/(f'{k:02d}_{stem}.png'),dpi=170)
  fig.savefig(figures_dir/(f'{k:02d}_{stem}.pdf'))
  plt.close(fig)
  print('Rendered from paceval CSV:',stem)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,default=ROOT/'examples');p.add_argument('--figures',type=Path,default=ROOT/'figures');a=p.parse_args();make(a.data,a.figures)
