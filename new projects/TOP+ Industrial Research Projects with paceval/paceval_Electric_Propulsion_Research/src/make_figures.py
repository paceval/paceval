#!/usr/bin/env python3
"""Produce reproducible industry-facing scientific figures from exported paceval CSVs."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
ROOT=Path(__file__).resolve().parents[1];F=ROOT/'figures';F.mkdir(exist_ok=True);E=ROOT/'examples'
plt.rcParams.update({'font.family':'DejaVu Sans','axes.titlesize':12,'axes.labelsize':10,'font.size':9,'figure.facecolor':'white','savefig.facecolor':'white'})
def save(name,fig):
 fig.savefig(F/(name+'.png'),dpi=180,bbox_inches='tight',pad_inches=.24)
 fig.savefig(F/(name+'.pdf'),bbox_inches='tight',pad_inches=.24)
 plt.close(fig)
def surface(name,title,zlabel,scale=1,cmap='viridis',azim=-57):
 df=pd.read_csv(E/(name+'_surface.csv'));P=df['power_w'].to_numpy().reshape(61,61)/1000
 M=df['flow_mg_s'].to_numpy().reshape(61,61);Z=df['value'].to_numpy().reshape(61,61)*scale
 fig=plt.figure(figsize=(9.2,6.3));ax=fig.add_subplot(111,projection='3d')
 plot=ax.plot_surface(P,M,Z,cmap=cmap,linewidth=0,antialiased=True,alpha=.97,rstride=1,cstride=1)
 ax.set_xlabel('Input electrical power [kW]',labelpad=9);ax.set_ylabel('Total propellant flow [mg/s]',labelpad=9);ax.set_zlabel(zlabel,labelpad=12)
 ax.view_init(elev=26,azim=azim);ax.set_title(title,pad=13)
 fig.colorbar(plot,ax=ax,shrink=.55,pad=.14,label=zlabel)
 fig.subplots_adjust(left=.04,right=.90,top=.90,bottom=.06)
 return fig
def main():
 # Graph (1): directly computed efficiency surface.
 save('01_efficiency_surface',surface('efficiency','Synthetic total efficiency map','Efficiency [-]',cmap='viridis'))
 save('02_thrust_surface',surface('thrust','Analytical thrust map','Thrust [mN]',cmap='plasma'))
 save('03_specific_impulse_surface',surface('specific_impulse','Specific impulse from thrust / mass flow','Specific impulse [s]',cmap='cividis'))
 # Map contour: user can see a constrained operating point independent of 3D perspective.
 df=pd.read_csv(E/'efficiency_surface.csv');P=df.power_w.to_numpy().reshape(61,61)/1000;M=df.flow_mg_s.to_numpy().reshape(61,61);Z=df.value.to_numpy().reshape(61,61)
 fig,ax=plt.subplots(figsize=(8.8,5.4));co=ax.contourf(P,M,Z,levels=18,cmap='viridis');ax.contour(P,M,Z,levels=9,colors='#d5e6f1',linewidths=.6)
 fig.colorbar(co,ax=ax,label='Total efficiency [-]');ax.set(xlabel='Input electrical power [kW]',ylabel='Total propellant flow [mg/s]',title='Efficiency operating-region contours');save('04_efficiency_contours',fig)
 save('05_thrust_to_power_surface',surface('thrust_to_power','Thrust per unit input electrical power','Thrust / power [mN/kW]',cmap='magma'))
 save('06_nonjet_power_surface',surface('waste_power','Electrical power not represented in jet power','Non-jet power [W]',cmap='inferno'))
 # A cross-sectional trade-off using same 3D grids, at fixed mass flow ~4.5 mg/s
 f1=pd.read_csv(E/'specific_impulse_surface.csv');f2=pd.read_csv(E/'thrust_to_power_surface.csv')
 sel=np.isclose(f1.flow_mg_s,4.5,atol=.051)
 a=f1[sel].sort_values('power_w');b=f2[sel].sort_values('power_w')
 fig,ax=plt.subplots(figsize=(8.8,5.0));ax.plot(a.power_w/1000,a.value,lw=2.4,color='#007F88',label='Specific impulse')
 ax.set(xlabel='Electrical power [kW]',ylabel='Specific impulse [s]',title='Operating-point trade-off at 4.5 mg/s')
 ay=ax.twinx();ay.plot(b.power_w/1000,b.value,lw=2,color='#D67A2F',label='Thrust / power');ay.set_ylabel('Thrust / power [mN/kW]')
 ax.grid(alpha=.18);save('07_tradeoff_cross_section',fig)
 df=pd.read_csv(E/'formula_revision.csv')
 fig,ax=plt.subplots(figsize=(8.8,4.8));ax.plot(df.power_w/1000,df.thrust_original_mn,label='Original graph',lw=2.4,color='#007f88')
 ax.plot(df.power_w/1000,df.thrust_revised_mn,label='Immutable revision',lw=2,color='#D67A2F',ls='--')
 ax.set(xlabel='Electrical power [kW]',ylabel='Thrust [mN]',title='Controlled mathematical model revision at 4.5 mg/s')
 ax.legend();ax.grid(alpha=.2);save('08_formula_revision',fig)
 # Show architecture via native vector graphics, not misrepresenting numerical results.
 fig,ax=plt.subplots(figsize=(10.2,2.2));ax.set_xlim(0,10);ax.set_ylim(0,2);ax.axis('off')
 for i,(label,sub) in enumerate([('Defined P and mdot','Host input contract'),('Persistent math','51 paceval graphs'),('Derived metrics','Five surface families'),('Engineering review','Host decisions')]):
  x=.25+i*2.48;ax.text(x+.94,1.1,label,ha='center',va='center',fontweight='bold',fontsize=10,bbox=dict(boxstyle='round,pad=.65',facecolor='#DDEFF1' if i==1 else '#F0F3F6',edgecolor='#1D8293'))
  ax.text(x+.94,.34,sub,ha='center',fontsize=8,color='#4D6475')
  if i<3:ax.annotate('',(x+2.39,1.1),(x+1.78,1.1),arrowprops=dict(arrowstyle='->',lw=1.5,color='#1D8293'))
 save('09_execution_architecture',fig)
 # Two supplementary vector-quality typeset equation panels for the report.
 for name,lines in [
  ('10_physics_equations',[r'$\eta=\frac{T^2}{2\dot{m}P}$',r'$T=\sqrt{2\eta P\dot{m}}$',r'$I_{\mathrm{sp}}=\frac{T}{\dot{m}g_0}$']),
  ('11_synthetic_equation',[r'$\eta_j(P,m)=b_j+a_j\exp\left[-\left(\frac{P-1700}{900}\right)^2-\left(\frac{m-4.5}{2}\right)^2\right]$'])]:
  fig,ax=plt.subplots(figsize=(9,1.05 if len(lines)==1 else 3.25));ax.set_axis_off()
  for idx,line in enumerate(lines):ax.text(.5,1-(idx+1)/(len(lines)+1),line,ha='center',va='center',fontsize=17 if len(lines)==1 else 18,color='#153450',transform=ax.transAxes)
  save(name,fig)
 print('PASS generated 9 scientific/architecture graphics and 2 typeset formula panels')
if __name__=='__main__':main()
