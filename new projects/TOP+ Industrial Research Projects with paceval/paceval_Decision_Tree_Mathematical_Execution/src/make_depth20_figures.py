#!/usr/bin/env python3
"""Plot only recorded outputs from the actual original paceval exhaustive test."""
import csv,sys
from pathlib import Path
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent.parent
figs=root/'figures';figs.mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader((root/'results/depth20_path_cardinality.csv').open()))
x=[int(r['true_conditions']) for r in rows];y=[int(r['verified_paths']) for r in rows]
fig,ax=plt.subplots(figsize=(9.5,4.8))
ax.bar(x,y,color='#8e6ac8',width=.8)
ax.set(xlabel='Number of true binary decisions in a 20-level path',ylabel='Verified reachable terminal paths',title='Exhaustive coverage of 1,048,576 terminal paths')
ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True);fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(figs/('12_depth20_verified_coverage.'+ext),dpi=200)
plt.close(fig)
rows=list(csv.DictReader((root/'results/depth20_score_samples.csv').open()))
x=[int(r['leaf_id']) for r in rows];y1=[float(r['score_v1']) for r in rows];y2=[float(r['score_v2']) for r in rows]
fig,ax=plt.subplots(figsize=(9.5,4.8))
ax.plot(x,y1,label='Structured leaf score, model v1',lw=1.1,color='#245f80')
ax.plot(x,y2,label='Structured leaf score, model v2',lw=1.1,alpha=.9,color='#ca7047')
ax.set(xlabel='Leaf identifier (out of 1,048,576)',ylabel='Synthetic score (dimensionless)',title='Recorded paceval scores across the complete tree domain')
ax.xaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
ax.grid(alpha=.2);ax.legend(loc='upper left',fontsize=9);fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(figs/('13_depth20_versioned_scores.'+ext),dpi=200)
plt.close(fig)
print('Generated two depth20 figures from paceval result CSVs')
