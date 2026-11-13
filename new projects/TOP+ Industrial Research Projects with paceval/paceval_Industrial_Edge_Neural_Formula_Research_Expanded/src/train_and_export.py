#!/usr/bin/env python3
"""Generate synthetic bearing features, train two frozen MLPs, export exact decimal weights.
This is NOT a real-bearing benchmark. No network connection or external dataset is used.
Requires numpy for model generation/training only, not for the C++ demonstrator.
"""
from pathlib import Path
import numpy as np, csv, json, hashlib, argparse
P=Path(__file__).resolve().parents[1]
RNG=np.random.default_rng(20261113)
NAMES=['vibration_rms_mm_s','crest_factor','kurtosis','vibration_band_energy','current_rms_A','current_harmonic_ratio','bearing_temperature_C','shaft_speed_rpm']
def sigmoid(z):
    z=np.clip(z,-60,60)
    return 1/(1+np.exp(-z))
def samples():
    records=[]
    # Disjoint synthetic bearing identities. All operating-condition holdouts are explicit.
    for bearing in range(48):
        split=['train']*24+['validation']*8+['test']*8+['shift_test']*8
        category=split[bearing]
        fault= int((bearing*7+3)%4 in (0,1))
        severity= (0.15+0.10*(bearing%6)) if fault else 0.
        offset=RNG.normal(0,.08,size=6)
        for w in range(32):
            condition = w%4 if category!='shift_test' else 4
            if condition==4:
                rpm=2500 + 230*RNG.random(); load=.8+.2*RNG.random()
            else:
                rpm=[1000,1300,1600,1900][condition] + RNG.normal(0,45)
                load=[.30,.52,.7,.86][condition]+RNG.normal(0,.04)
            noi=RNG.normal(0,1,6)
            a=.75+.00038*rpm+.30*load+0.85*severity+offset[0]+.10*noi[0]
            cf=2.5+.00016*rpm+1.25*severity+offset[1]+.15*noi[1]
            ku=3.0+1.6*severity+offset[2]+.25*noi[2]
            band=.06+.000043*rpm+.13*severity+offset[3]*.04+.025*noi[3]
            cur=2.5+1.5*load+.00022*rpm+.17*severity+offset[4]+.08*noi[4]
            harm=.055+.045*severity+.028*load+offset[5]*.03+.011*noi[5]
            temp=30+.006*rpm+5.7*load+5*severity+RNG.normal(0,.8)
            features=np.array([a,cf,ku,band,cur,harm,temp,rpm],dtype=float)
            records.append((category,bearing,condition,fault,features))
    return records
records=samples()
train=np.stack([r[4] for r in records if r[0]=='train']);mu=train.mean(0);sd=train.std(0)
assert (sd>0).all()
X=np.stack([(r[4]-mu)/sd for r in records]);y=np.array([r[3] for r in records],float)[:,None]
tr=np.array([i for i,r in enumerate(records) if r[0]=='train'])
val=np.array([i for i,r in enumerate(records) if r[0]=='validation'])
def init(seed):
    g=np.random.default_rng(seed)
    return [g.normal(0,.36,(8,8)),np.zeros(8),g.normal(0,.37,(8,4)),np.zeros(4),g.normal(0,.36,(4,1)),np.zeros(1)]
def predict(params,x):
    a=sigmoid(x@params[0]+params[1]);b=sigmoid(a@params[2]+params[3]);c=sigmoid(b@params[4]+params[5]);return c

def fit(seed,wd=0.):
    p=init(seed);m=[np.zeros_like(q) for q in p];v=[np.zeros_like(q) for q in p]
    for epoch in range(1,601):
        A=sigmoid(X[tr]@p[0]+p[1]);B=sigmoid(A@p[2]+p[3]);out=sigmoid(B@p[4]+p[5])
        d3=(out-y[tr])/len(tr)
        gr=[None]*6; gr[4]=B.T@d3+wd*p[4];gr[5]=d3.sum(0)
        d2=(d3@p[4].T)*B*(1-B)
        gr[2]=A.T@d2+wd*p[2];gr[3]=d2.sum(0)
        d1=(d2@p[2].T)*A*(1-A)
        gr[0]=X[tr].T@d1+wd*p[0];gr[1]=d1.sum(0)
        for i,g in enumerate(gr):
            m[i]=.9*m[i]+.1*g;v[i]=.999*v[i]+.001*(g*g)
            p[i]=p[i]-.028*(m[i]/(1-.9**epoch))/(np.sqrt(v[i]/(1-.999**epoch))+1e-8)
    return p
models={'v1':fit(19,.00003),'v2':fit(31,.00015)}
# Put exact binary64 round-tripping decimal repr in CSV and input files.
def fmt(v):return format(float(v),'.17g')
ex=P/'examples';ex.mkdir(exist_ok=True)
with (ex/'synthetic_bearing_features.csv').open('w',newline='') as fh:
    w=csv.writer(fh);w.writerow(['split','virtual_bearing_id','operating_condition','synthetic_fault_label']+NAMES)
    for r in records:w.writerow([r[0],r[1],r[2],r[3]]+[fmt(z) for z in r[4]])
with (ex/'normalization.csv').open('w',newline='') as fh:
    w=csv.writer(fh);w.writerow(['feature','mean','std']);[w.writerow([n,fmt(mu[i]),fmt(sd[i])]) for i,n in enumerate(NAMES)]
with (ex/'frozen_network_weights.csv').open('w',newline='') as fh:
    w=csv.writer(fh);w.writerow(['version','layer','neuron','input','weight'])
    for name,p in models.items():
        for l,(W,b) in enumerate([(p[0],p[1]),(p[2],p[3]),(p[4],p[5])],1):
            for j in range(W.shape[1]):
                for i in range(W.shape[0]):w.writerow([name,l,j,i,fmt(W[i,j])])
                w.writerow([name,l,j,-1,fmt(b[j])])
manifest={"dataset_kind":"synthetic feature vectors, no real measurements", "seed":20261113,"architecture":"8-8-4-1","activations":"logistic", "model_training":"batch Adam, 600 epochs, binary cross entropy; train virtual bearing groups only","version_seeds":{"v1":19,"v2":31},"normalization":"training-group only", "dataset_split":"disjoint virtual bearing identities, 32 records per bearing, shift_test at higher speed", "operating_decision":"illustrative advisory only; not a calibrated failure probability","threshold":0.5,"review_width":0.08,"source":"src/train_and_export.py"}
for name,p in models.items():
    manifest[name]={}
    for partition in ['train','validation','test','shift_test']:
        ix=np.array([i for i,r in enumerate(records) if r[0]==partition]);pred=predict(p,X[ix]).flatten();yy=y[ix].flatten()
        manifest[name][partition]={"count":len(ix),"accuracy_at_0.5":round(float(np.mean((pred>=.5)==yy)),6),"false_alarms":int(np.sum((pred>=.5)&(yy==0))),"missed_faults":int(np.sum((pred<.5)&(yy==1)))}
manifest['feature_dataset_sha256']=hashlib.sha256((ex/'synthetic_bearing_features.csv').read_bytes()).hexdigest()
manifest['frozen_weights_sha256']=hashlib.sha256((ex/'frozen_network_weights.csv').read_bytes()).hexdigest()
(ex/'model_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:manifest[k] for k in ['v1','v2']},indent=2))
