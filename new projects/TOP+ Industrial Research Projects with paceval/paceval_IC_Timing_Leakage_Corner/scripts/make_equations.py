#!/usr/bin/env python3
"""Render mathematical specifications as typeset equation image; not an experimental plot."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parents[1]/'figures'
fig,ax=plt.subplots(figsize=(10.2,4.2));ax.axis('off')
texts=[
 r'$D_1=t_0+a_C C+a_S S+a_T(T-T_{ref})+a_V(V_{ref}/V)^p$',
 r'$D_2=D_1+a_C C[(V_{ref}/V)^q-1]+a_{CT}C(T-T_{ref})+a_{CS}CS$',
 r'$I_1=I_0\,e^{b_T(T-T_{ref})+b_V(V-V_{ref})}$',
 r'$I_2=I_0\,e^{b_T\Delta T+b_V\Delta V+b_{TT}\Delta T^2+b_{VT}\Delta T\Delta V}$',
 r'$s_i=T_{req}-T_{arr}-N D_i-D_{wire},\quad P_i=V I_i$',
 r'$g_i=\min(s_i,\;k(P_{cap}-P_i))$'
]
for j,txt in enumerate(texts):ax.text(.01,.88-.152*j,txt,fontsize=15.3,va='center',color='#142f48')
fig.savefig(p/'model_equations.png',dpi=220,bbox_inches='tight',pad_inches=.25)
fig.savefig(p/'model_equations.pdf',bbox_inches='tight',pad_inches=.25)
plt.close(fig)
