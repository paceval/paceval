#!/usr/bin/env python3
"""Render genuine paceval height-grid CSVs, export GLB/OBJ meshes and scientific charts."""
from pathlib import Path
import csv, json, os, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
import trimesh
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
FIG=ROOT/'figures'; FIG.mkdir(exist_ok=True)
NAMES=['alpine_lake','volcanic_caldera','canyon_ridges']
LABELS=['Alpine lake and mountains','Volcanic caldera','Canyon and ridge systems']
COLORS=['terrain','magma','copper']

def load(name):
 rows=list(csv.DictReader((ROOT/'examples'/f'{name}_height_grid.csv').open())); size=round(len(rows)**.5)
 assert size*size==len(rows)
 x=np.array([float(q['x']) for q in rows]).reshape(size,size); y=np.array([float(q['y']) for q in rows]).reshape(size,size)
 z=np.array([float(q['height']) for q in rows]).reshape(size,size)
 return x,y,z,float(rows[0]['water_level'])

def plotfig(fig,stem):
 fig.savefig(FIG/(stem+'.png'),dpi=200,bbox_inches='tight',facecolor='white')
 fig.savefig(FIG/(stem+'.pdf'),bbox_inches='tight',facecolor='white')
 plt.close(fig)

def mesh(x,y,z,w,name):
 n=len(x); vs=np.stack([x.ravel(),y.ravel(),z.ravel()],axis=-1); fs=[];waterfaces=[];waterverts=np.stack([x.ravel(),y.ravel(),np.full(n*n,w)],axis=-1)
 for iy in range(n-1):
  for ix in range(n-1):
   a=iy*n+ix;b=a+1;c=a+n;d=c+1
   fs.extend(((a,b,c),(b,d,c)))
   if np.all(z[iy:iy+2,ix:ix+2]<w):
    waterfaces.extend(((a,b,c),(b,d,c)))
 terrain=trimesh.Trimesh(vertices=vs,faces=fs,process=False)
 terrain.visual.vertex_colors=trimesh.visual.color.interpolate(z.ravel(),color_map=plt.get_cmap(COLORS[NAMES.index(name)]))
 scene=trimesh.Scene();scene.add_geometry(terrain,geom_name='paceval_height_field')
 terrain.export(ROOT/'examples'/f'{name}_terrain.obj')
 if waterfaces:
  lake=trimesh.Trimesh(vertices=np.array(waterverts),faces=np.array(waterfaces),process=False)
  lake.visual.face_colors=[30,150,225,190]
  lake.export(ROOT/'examples'/f'{name}_water.obj')
  scene.add_geometry(lake,geom_name='separate_constant_height_water_geometry')
 scene.export(ROOT/'examples'/f'{name}_terrain.glb')
 return dict(terrain_vertices=len(terrain.vertices),terrain_triangles=len(terrain.faces),water_triangles=len(waterfaces),glb=scene.geometry.keys().__len__(),surface_figure_stride=4)

meta=json.loads((ROOT/'results'/'mesh_validation.json').read_text()) if (ROOT/'results'/'mesh_validation.json').exists() else {}
selector=os.environ.get('PACEVAL_FIG_SCENE','all')
for k,name in enumerate(NAMES):
 if selector not in ('all',name):continue
 x,y,z,water=load(name);meta[name]=mesh(x,y,z,water,name)
 fig=plt.figure(figsize=(8.5,6.2));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(x[::4,::4],y[::4,::4],z[::4,::4],cmap=COLORS[k],linewidth=0,antialiased=True,rstride=1,cstride=1)
 ax.set_title(LABELS[k]+' - evaluated analytic height field (512 x 512)',fontsize=12,pad=13)
 ax.set(xlabel='normalized x',ylabel='normalized y',zlabel='synthetic height');ax.view_init(elev=32,azim=-61)
 fig.subplots_adjust(left=.02,right=.95,bottom=.08,top=.9)
 plotfig(fig,f'{2*k+1:02d}_{name}_surface')
 fig,ax=plt.subplots(figsize=(8.5,6.2));con=ax.contourf(x,y,z,levels=22,cmap=COLORS[k]);ax.contour(x,y,z,levels=[water],colors='#0c77b0',linewidths=1.5)
 ax.set_title(LABELS[k]+' • paceval height contours and declared water level',fontsize=11);ax.set(xlabel='normalized x',ylabel='normalized y');ax.set_aspect('equal');fig.colorbar(con,ax=ax,label='synthetic height')
 plotfig(fig,f'{2*k+2:02d}_{name}_contours')

rows=list(csv.DictReader((ROOT/'results'/'execution_summary.csv').open()))
fig,ax=plt.subplots(figsize=(9,4.2));labels=[x['scene'].replace('_',' ') for x in rows]; nums=[int(x['formula_characters']) for x in rows]
bars=ax.barh(labels,[n/1000 for n in nums],color=['#258d88','#b86e37','#7d8cab']);ax.set_xlabel('Explicit mathematical expression length (thousand characters)');ax.set_title('Verified complete paceval mathematical expressions');ax.invert_yaxis()
for b,n in zip(bars,nums):ax.text(b.get_width()+7,b.get_y()+b.get_height()/2,f'{n:,} chars',va='center',fontsize=9)
ax.set_xlim(0,max(nums)/1000*1.28);fig.tight_layout();plotfig(fig,'07_verified_formula_lengths')
(ROOT/'results'/'mesh_validation.json').write_text(json.dumps(meta,indent=2)+'\n')
for name in NAMES:
 m=trimesh.load(ROOT/'examples'/f'{name}_terrain.glb',force='scene');assert len(m.geometry)>=1 and sum(len(g.faces) for g in m.geometry.values())>0
print('PASS: generated charts and GLB/OBJ mesh sets for '+selector)
