#!/usr/bin/env python3
"""Make all scientific plots exclusively from exported paceval CSV results."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'figures'
rows=list(csv.DictReader((ROOT/'examples/pricing_grid.csv').open()))
V=lambda key:np.array([float(r[key]) for r in rows]).reshape(41,61)
S=V('S');SIG=V('sigma')
cm=LinearSegmentedColormap.from_list('paceval',['#176e9a','#41c5ce','#eac68a','#bb603f'])
navy='#0d1c2c'; cyan='#30bfd0'; gold='#e3ab62'
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','axes.titleweight':'bold',
                     'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})
def save(fig,stem):
 fig.savefig(OUT/(stem+'.png'),dpi=185,bbox_inches='tight')
 fig.savefig(OUT/(stem+'.pdf'),bbox_inches='tight')
 plt.close(fig)
def surface(key,label,stem):
 fig=plt.figure(figsize=(10.2,5.4));ax=fig.add_subplot(111,projection='3d')
 surf=ax.plot_surface(S,SIG,V(key),cmap=cm,linewidth=0,antialiased=True,rstride=2,cstride=2)
 ax.set_xlabel('Spot S (currency units)',labelpad=9);ax.set_ylabel('Volatility σ (year⁻¹/²)',labelpad=9)
 ax.set_zlabel(label,labelpad=9);ax.view_init(24,-129);ax.set_title(label+' | 2,501 paceval-evaluated points',pad=14)
 fig.colorbar(surf,ax=ax,pad=.10,shrink=.72,label=label);fig.subplots_adjust(left=.04,right=.95)
 save(fig,stem)
def contour(key,label,stem):
 fig,ax=plt.subplots(figsize=(10,4.7)); m=ax.contourf(S,SIG,V(key),levels=28,cmap=cm)
 cs=ax.contour(S,SIG,V(key),levels=10,colors=navy,linewidths=.35,alpha=.65);ax.clabel(cs,inline=True,fontsize=7)
 fig.colorbar(m,ax=ax,label=label);ax.set_xlabel('Spot S (currency units)');ax.set_ylabel('Volatility σ (year⁻¹/²)');ax.set_title(label+' | paceval response map')
 save(fig,stem)
surface('call_price','European call price','01_call_price_surface')
surface('put_price','European put price','02_put_price_surface')
contour('call_delta','Call delta (per currency unit)','03_call_delta_map')
surface('gamma','Gamma (per currency unit²)','04_gamma_surface')
surface('vega','Vega (per 1.00 volatility)','05_vega_surface')
contour('call_theta','Call theta (currency units per year)','06_theta_map')
# Corresponding put/call curves on the fixed sigma slice for transparent comparison.
fig,ax=plt.subplots(figsize=(10,4.7)); j=10
ax.plot(S[j],V('call_price')[j],lw=2.3,color=cyan,label='Call price')
ax.plot(S[j],V('put_price')[j],lw=2.3,color=gold,label='Put price')
ax.set_xlabel('Spot S (currency units)');ax.set_ylabel('Option price (currency units)');ax.set_title(f'Call and put prices | σ={SIG[j,0]:.3f}, K=100, T=1.25 years')
ax.grid(alpha=.25);ax.legend();save(fig,'07_call_put_slice')
# Max error shown as summary from actually saved audit; no timing benchmarks.
print('Generated seven mathematical figures, each as PNG and vector PDF')
