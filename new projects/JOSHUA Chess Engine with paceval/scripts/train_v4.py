#!/usr/bin/env python3
"""Train a small deterministic residual MLP on JOSHUA's depth-two V3 teacher.
No Stockfish or Leela targets are used. Outputs are reproducible artifacts.
The teacher, positions, and model limitations are stated in the report.
"""
import csv, json, math, random, hashlib
from pathlib import Path
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'training/teacher_positions.csv'
FORM=ROOT/'formulas'
FORM.mkdir(parents=True,exist_ok=True)
with INPUT.open(newline='') as f:
    rows=list(csv.DictReader(f))
cols=list(rows[0].keys())[6:]
assert len(cols)==48, cols
X=np.array([[float(r[x]) for x in cols] for r in rows],float)
y=np.array([float(r['residual_cp']) for r in rows],float)
gid=np.array([int(r['game_id']) for r in rows]);rng=random.Random(20261115)
groups=sorted(set(gid));rng.shuffle(groups)
ng=len(groups);tr=set(groups[:int(ng*0.72)]);va=set(groups[int(ng*0.72):int(ng*0.86)]);te=set(groups[int(ng*0.86):]);assert not tr&va and not tr&te and not va&te
idxTr=np.array([g in tr for g in gid]);idxVa=np.array([g in va for g in gid]);idxTe=np.array([g in te for g in gid]);
scale=StandardScaler().fit(X[idxTr]);tx=scale.transform(X)
# Preserve unaltered zero-scale variables as zero signals; scaler handles them.
res={}
for h in (12,16):
  for alpha in (0.1,2.0):
    nn=MLPRegressor(hidden_layer_sizes=(h,),activation='logistic',solver='lbfgs',alpha=alpha,
      random_state=20261115,max_iter=280,max_fun=400,tol=1e-8)
    nn.fit(tx[idxTr],y[idxTr]/100.0)
    v=(nn.predict(tx[idxVa])*100)
    mae=mean_absolute_error(y[idxVa],np.clip(v,-150,150))
    res[(h,alpha)]=(mae,nn)
choice=min(res,key=lambda key:res[key][0]); net=res[choice][1];h=choice[0]
W=net.coefs_[0].T.copy();b=net.intercepts_[0].copy();ow=net.coefs_[1].reshape(-1).copy();ob=float(net.intercepts_[1][0]);
assert W.shape==(h,48) and len(b)==len(ow)==h

def predict(x):
  z=(x-scale.mean_)/scale.scale_
  hidden=1/(1+np.exp(-(z@W.T+b)))
  return np.clip(100*(hidden@ow+ob),-150,150)
val=predict(X[idxVa]);test=predict(X[idxTe]);
metrics={
 'data_source':'JOSHUA-generated legal positions, V3 depth-two minimax teacher (no external engine)',
 'label':'clipped teacher-minus-V3 residual in centipawns, not WDL probabilities',
 'train_game_count':len(tr),'validation_game_count':len(va),'test_game_count':len(te),
 'train_rows':int(idxTr.sum()),'validation_rows':int(idxVa.sum()),'test_rows':int(idxTe.sum()),
 'model_hidden_units':h,'alpha':choice[1],'validation_mae_residual_cp':float(mean_absolute_error(y[idxVa],val)),
 'test_mae_residual_cp':float(mean_absolute_error(y[idxTe],test)),
 'test_zero_residual_mae_cp':float(np.mean(np.abs(y[idxTe]))),
 'train_mae_residual_cp':float(mean_absolute_error(y[idxTr],predict(X[idxTr]))),
 'input_features':cols,
 'trained':True,'seed':20261115,
 'full_test_teacher_mae_from_v3_cp':float(np.mean(np.abs(y[idxTe]))),
 'full_test_teacher_mae_from_v4_cp':float(np.mean(np.abs(y[idxTe]-test))),
 'loss_limitation':'Teacher is a low-depth hand-crafted V3 search, not a validated stronger chess opponent.'
}
for (H,a),(mae,nn2) in res.items():metrics[f'candidate_val_mae_h{H}_alpha{a}']=float(mae)
(FORM/'training_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
model={'input_features':cols,'feature_mean':scale.mean_.tolist(),'feature_scale':scale.scale_.tolist(),
    'hidden_weights':W.tolist(),'hidden_bias':b.tolist(),'output_weights':ow.tolist(),
    'output_bias':ob,'output_scale':100.0,'residual_cap_cp':150.0,'activation':'sigmoid','trained':True,
    'seed':20261115,'training_provenance':'JOSHUA synthetic legal positions; classical V3 minimax depth-two targets',
    'group_split':{'training':[int(x) for x in sorted(tr)],'validation':[int(x) for x in sorted(va)],'test':[int(x) for x in sorted(te)]}}
(FORM/'v4_trained_weights.json').write_text(json.dumps(model,indent=2)+'\n')
# Always format all coefficients to shortest roundtrippable decimal, preserving native parity.
fmt=lambda x:format(float(x),'.17g')
formulas=[]
for i in range(h):
    s='('+fmt(b[i])
    for k,name in enumerate(cols):
      w=W[i,k]
      if abs(w)>0:
        term='('+fmt(w)+'*(('+name+'-('+fmt(scale.mean_[k])+'))/'+fmt(scale.scale_[k])+'))'
        s+='+'+term if w>=0 else '+'+term # signed coefficient handled inside term
    s+=')'
    formulas.append((f'H{i}','(1/(1+exp(-'+s+')))'))
outer='('+fmt(ob)+''.join('+('+fmt(ow[i])+'*h'+str(i)+')' for i in range(h))+')'
# Output graph combines the original paceval V3 value and a capped neural residual.
# Number of input variables H+1; base is the original paceval V3 SCORE result.
z='(100*'+outer+')'
last='(base+0.5*(abs('+z+'+150)-abs('+z+'-150)))'
formulas.append(('V4_FUSED_SCORE',last))
with (FORM/'v4_graph_expressions.tsv').open('w') as f:
  f.write(''.join(n+'\t'+expr+'\n' for n,expr in formulas))
with (FORM/'v4_graph_manifest.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['graph','input_variables','formula_characters','trained','purpose'])
 for n,expr in formulas:w.writerow([n,48 if n!='V4_FUSED_SCORE' else h+1,len(expr),'yes','hidden activation' if n.startswith('H') else 'V3 plus bounded learned residual'])
# Generated header stores exact source coefficients used by the C++ independent reference.
def cc(v):return '{'+','.join(fmt(x) for x in v)+'}'
with (ROOT/'src/v4_trained_model.h').open('w') as f:
 f.write('// AUTOMATICALLY GENERATED by scripts/train_v4.py from split synthetic data.\n#pragma once\n')
 f.write('constexpr int V4_INPUTS=48, V4_HIDDEN='+str(h)+';\n')
 f.write('static const double V4_MEAN[V4_INPUTS]='+cc(scale.mean_)+';\n')
 f.write('static const double V4_SCALE[V4_INPUTS]='+cc(scale.scale_)+';\n')
 f.write('static const double V4_W[V4_HIDDEN][V4_INPUTS]={'+','.join(cc(row) for row in W)+'};\n')
 f.write('static const double V4_B[V4_HIDDEN]='+cc(b)+';\n')
 f.write('static const double V4_OUT[V4_HIDDEN]='+cc(ow)+';\n')
 f.write('static constexpr double V4_BIAS='+fmt(ob)+';\n')
 f.write('static constexpr double V4_CLIP=150.0;\n')
 f.write('static const char* V4_VARIABLE_NAMES[V4_INPUTS]={'+','.join('"'+s+'"' for s in cols)+'};\n')
with (ROOT/'src/v4_graph_formulas.h').open('w') as f:
 f.write('// Exact, trained, exported paceval formula literals.\n#pragma once\n')
 f.write('static const char* V4_GRAPH_NAMES[V4_HIDDEN+1]={'+','.join('"'+name+'"' for name,_ in formulas)+'};\n')
 f.write('static const char* V4_GRAPH_EXPRESSIONS[V4_HIDDEN+1]={'+','.join(json.dumps(formula) for _,formula in formulas)+'};\n')
with (FORM/'v4_training_example_predictions.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['game_id','split','fen','teacher_cp','v3_cp','true_residual_cp','v4_predicted_residual_cp','v4_cp'])
  preds=predict(X)
  for i,r in enumerate(rows):
    spl='train' if idxTr[i] else ('validation' if idxVa[i] else 'test')
    w.writerow([r['game_id'],spl,r['fen'],r['teacher_cp'],r['v3_cp'],r['residual_cp'],f'{preds[i]:.12g}',f'{float(r["v3_cp"])+preds[i]:.12g}'])
print('trained V4',h,'hidden neurons, train/val/test',int(idxTr.sum()),int(idxVa.sum()),int(idxTe.sum()),
 'baseline test MAE',round(metrics['test_zero_residual_mae_cp'],3),'V4 test MAE',round(metrics['test_mae_residual_cp'],3),
 'graphs',len(formulas),'characters',sum(len(s) for _,s in formulas))
