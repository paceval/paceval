"""Render publication-only typeset mathematical definitions, not simulated research data."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
F=Path(__file__).resolve().parents[1]/'figures'
forms={
'01_base_rates':r'$\lambda_{DU}=\lambda_D(1-DC),\quad \lambda_c=c\lambda_{DU},\quad \lambda_u=(1-c)\lambda_{DU}$',
'02_baseline':r'$\mathrm{PFD}_{avg}\approx\frac{\lambda_{DU}T}{2},\qquad \frac{\partial\mathrm{PFD}_{avg}}{\partial T}=\frac{\lambda_{DU}}{2}$',
'03_target':r'$m=\mathrm{PFD}_{target}-\mathrm{PFD}_{avg}$',
'04_survival':r'$A(z)=\frac{1-e^{-z}}{z},\quad B=\frac{1}{1+\lambda_D\,DC\,MTTR},\quad z=\lambda_cT$',
'05_pfd_1oo1':r'$\mathrm{PFD}_{avg,1}=1-B\,e^{-\lambda_uH}\,A(z)$',
'06_pfd_1oo2':r'$\mathrm{PFD}_{avg,2}=1-2B\,e^{-\lambda_uH}A(z)+B^2e^{-(2-\beta)\lambda_uH}A((2-\beta)z)$'
}
for name,tex in forms.items():
    fig,ax=plt.subplots(figsize=(10.6,1.03));fig.patch.set_facecolor('#F1F6F8');ax.set_facecolor('#F1F6F8');ax.axis('off');ax.text(.025,.5,tex,fontsize=18,color='#07314F',va='center',ha='left',transform=ax.transAxes)
    fig.savefig(F/f'equation_{name}.png',dpi=190,bbox_inches='tight',pad_inches=.12,facecolor=fig.get_facecolor());plt.close(fig)
print('6 typeset mathematical equation panels')
