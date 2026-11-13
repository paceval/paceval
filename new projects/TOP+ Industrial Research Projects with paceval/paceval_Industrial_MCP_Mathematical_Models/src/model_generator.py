from pathlib import Path
import csv, json, hashlib
from decimal import Decimal, ROUND_HALF_UP
root=Path(__file__).resolve().parents[1]
for n in ['src','docs','figures','results','examples','generated','tests']:(root/n).mkdir(parents=True,exist_ok=True)

N=256
def jsfixed(v,places):
  quant=Decimal('1').scaleb(-places)
  return format(Decimal.from_float(float(v)).quantize(quant,rounding=ROUND_HALF_UP),f'.{places}f')
names=['x','y','z','temp']
def term(k,v=0):
 a=((k%11)-5)*0.00009*(1+0.06*v)
 mx=((k*37)%257)/256
 my=((k*53)%263)/262
 mz=((k*71)%269)/268
 s=0.08+0.014*(k%5)
 c=((k%7)-3)*0.012
 A=jsfixed(a,9);X=jsfixed(mx,6);Y=jsfixed(my,6);Z=jsfixed(mz,6);S=jsfixed(s,6);C=jsfixed(c,6)
 dist=f'((x-{X})*(x-{X})+(y-{Y})*(y-{Y})+(z-{Z})*(z-{Z}))'
 gauss=f'exp(-{dist}/{S})'
 T=f'(1{"+" if c>=0 else ""}{C}*(temp-20)/20)'
 return A,gauss,T,X,S,C

def make_expr(v,kind='field',begin=0,end=N):
 chunks=[]
 for k in range(begin,end):
  a,g,t,x,s,c=term(k,v)
  if kind=='field': chunks.append(f'({a}*{g}*{t})')
  elif kind=='temp_sensitivity':chunks.append(f'({a}*{g}*({c}/20))')
  elif kind=='x_sensitivity':chunks.append(f'({a}*{g}*{t}*(-2*(x-{x})/{s}))')
  else:raise ValueError(kind)
 base=(['(0.130000+0.002000*(temp-20)+0.014000*x-0.011000*y+0.009000*z)',
        '(0.135000+0.002200*(temp-20)+0.013000*x-0.009000*y+0.011000*z)'][v] if kind=='field' else
        (['0.002000','0.002200'][v] if kind=='temp_sensitivity' else ['0.014000','0.013000'][v]))
 if kind=='field' and begin>0: base='0'
 if kind!='field' and begin>0: base='0'
 return base + ('+'+'+'.join(chunks) if chunks else '')

for ver in (0,1):
 for kind in ['field','temp_sensitivity','x_sensitivity']:
  p=root/f'generated/{kind}_v{ver+1}.txt';p.write_text(make_expr(ver,kind)+'\n')
for k in range(8):
 (root/f'generated/modular_block_{k+1:02d}_v2.txt').write_text(make_expr(1,'field',k*32,(k+1)*32)+'\n')
post={
 'revision_delta':'v2-v1',
 'target_residual':'v2-target',
 'quality_score':'((v2-target)/tol)^2+0.08*((temp-25)/25)^2+0.20*abs(v2-v1)/tol',
 'quality_margin':'1-(((v2-target)/tol)^2+0.08*((temp-25)/25)^2+0.20*abs(v2-v1)/tol)',
 'version_margin':'0.024-abs(v2-v1)',
 'governance_score':'0.55*abs(v2-target)/tol+0.25*abs(v2-v1)/tol+0.20*abs(temp-25)/25',
 'temperature_guard':'50-temp',
 'corrected_measurement':'raw-v2'
}
for k,v in post.items():
 (root/f'generated/{k}.txt').write_text(v+'\n')
rows=[]
for it,T in enumerate([15,25,35,45]):
 for iy in range(11):
  for ix in range(11):
   x=ix/10;y=iy/10;z=0.20+0.60*(ix+iy)/20
   raw=0.15+0.16*x+0.03*y + .007*(T-25)
   rows.append(dict(case_id=f'grid_{it}_{iy}_{ix}',x=x,y=y,z=z,temp=T,target=0.16,tol=0.030,raw=raw,scenario=f'T{T}'))
for i in range(36):
 x=((i*37)%97)/96;y=((i*23)%89)/88;z=((i*11)%79)/78;T=10+i*40/35
 rows.append(dict(case_id=f'stress_{i}',x=x,y=y,z=z,temp=T,target=0.16,tol=0.030,raw=.15+.16*x+.03*y+.007*(T-25),scenario='stress'))
with open(root/'examples/synthetic_machine_cases.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with open(root/'examples/mcp_batch_cases.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows([dict(case_id=f'live_mcp_{yi}_{xi}',x=xi/3,y=yi/3,z=.25+.5*(xi+yi)/6,temp=25,target=.16,tol=.03,raw=.15+.16*(xi/3)+.03*(yi/3),scenario='live_mcp_grid') for yi in range(4) for xi in range(4)])
manifest={'project':'Industrial mathematical models via the paceval MCP server','experiment':'two versioned 256-component Gaussian RBF synthetic models','number_of_components_per_version':N,'variables':names,'model_is_synthetic':True,'runtime_mcp':'4.26 (live service)','runtime_local_sdk':'4.25 (independent reproduction)','generation_rule':'model_generator.py','formulas':{}}
for p in sorted((root/'generated').glob('*.txt')):
 manifest['formulas'][p.name]={'length':len(p.read_text().strip()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(root/'generated/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

