#!/usr/bin/env python3
"""Produce the fixed-layout English report from actual saved paceval figures."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

R=Path(__file__).resolve().parent.parent
OUT=R/'paceval_Industrial_3D_Diagrams_Whitepaper_EN.pdf'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DVS',FONT));pdfmetrics.registerFont(TTFont('DVS-Bold',BOLD))
NAVY=colors.HexColor('#12283c');TEAL=colors.HexColor('#147e92');MUTED=colors.HexColor('#586c79')
ss=getSampleStyleSheet()
ss.add(ParagraphStyle(name='MainTitleX',fontName='DVS-Bold',fontSize=20,leading=27,textColor=NAVY,spaceAfter=12))
ss.add(ParagraphStyle(name='HeadX',fontName='DVS-Bold',fontSize=13.5,leading=18,textColor=NAVY,spaceBefore=11,spaceAfter=8))
ss.add(ParagraphStyle(name='BodyX',fontName='DVS',fontSize=9.0,leading=14.5,textColor=NAVY,spaceAfter=8))
ss.add(ParagraphStyle(name='TinyX',fontName='DVS',fontSize=7.0,leading=10.5,textColor=MUTED,spaceAfter=8))
ss.add(ParagraphStyle(name='CellX',fontName='DVS',fontSize=8,leading=11,textColor=NAVY))
ss.add(ParagraphStyle(name='CellBoldX',fontName='DVS-Bold',fontSize=8,leading=11,textColor=NAVY))
P=lambda x,style='BodyX':Paragraph(x,ss[style])
doc=SimpleDocTemplate(str(OUT),pagesize=(595.28,841.89),leftMargin=42,rightMargin=42,topMargin=45,bottomMargin=52)
W=doc.width
story=[]
def add(x,sty='BodyX'):story.append(P(x,sty))
def figure(name,scale=1):
 from PIL import Image as PILImage
 im=PILImage.open(R/'figures'/name);w,h=im.size
 width=W*scale;height=width*h/w
 story.append(Image(str(R/'figures'/name),width=width,height=height))
def footer(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#a7cbd1'));canvas.line(42,43,553,43)
 canvas.setFont('DVS',7);canvas.setFillColor(MUTED)
 canvas.drawString(42,31,'paceval. | Scientific Mathematical 3D Industrial Diagrams | Research demonstrator | 2026')
 canvas.drawRightString(553,31,str(doc.page));canvas.restoreState()

def table(rows,widths=None):
 t=Table([[P(str(c),'CellBoldX' if i==0 else 'CellX') for c in row] for i,row in enumerate(rows)],colWidths=widths or [W/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5f2f4')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f8f9')]),('LINEBELOW',(0,0),(-1,0),.7,TEAL),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
 story.append(t)

add('Scientific Mathematical 3D Industrial Diagrams','MainTitleX')
add('Six industrial numerical response surfaces generated with the original paceval C/C++ SDK','HeadX')
figure('01_heat_transfer.png')
add('Cover: a real 81 × 81 paceval-evaluated heat-response field and its corresponding contours. Unlike illustrative concept art, every displayed pixel is grounded in saved numerical outputs.','TinyX')
add('<b>Research outcome.</b> Six independently defined industrial analytic functions were compiled into reusable paceval expression graphs. The program generated 39,366 scalar values and separately checked 192 SDK batch results. All were checked against distinct native C++ formula implementations within an explicitly defined numeric tolerance.','BodyX')
add('<b>Scope.</b> These are analytically specified synthetic industrial models for mathematical visualization. The project does not solve governing 3D PDEs, calibrate digital twins, reproduce plant sensor observations or establish physical predictive accuracy. No runtime or speedup claims are made.','BodyX')
story.append(PageBreak())
add('1. Research question and execution architecture','HeadX')
add('Can a single reusable mathematical expression engine produce technically interpretable 3D industrial response surfaces, with explicit units, repeatable input sweeps, checked scalar/batch outputs and independently traceable renderings?')
add('A scientific 3D surface in this study is a map z=f(x,y), where two parameter axes and the numerical result are plotted in three Cartesian dimensions. The numerical values are computed by paceval, while Matplotlib renders the mesh. No AI image generation enters the data-to-figure pipeline.')
table([['Responsibility','Implementation'],['Formula parsing and reusable graph evaluation','Original paceval SDK 4.25 public C++ facade and compatible external runtime'],['Grid construction, declared units and domain checks','C++ research host'],['Independent arithmetic for each coordinate pair','Separate native C++ expression implementations'],['Plotting 3D surfaces and contours','Python Matplotlib from exported paceval CSV values']],[180,W-180])
add('The complete project consists of src/industrial_3d.cpp, original SDK facade files, src/CMakeLists.txt, six generated CSV grids, a CSV manifest, the figure-generation script, images and this report.')
add('2. Verified execution','HeadX')
table([['Audited component','Observed result'],['Original paceval computation graphs','6'],['Independent scalar comparison samples','39,366 / 39,366 accepted'],['Batch output comparisons','192 / 192 accepted'],['Samples per industrial model','6,561 (81 × 81)'],['Maximum absolute difference to native C++','2.84217 × 10⁻¹⁴ in the differing temperature model'],['CMake / CTest integration','1 / 1 passed']],[300,W-300])
add('The reported maximum difference combines distinct units across cases and is provided solely as a floating-point agreement diagnostic. Per-model error columns retain the physically relevant output units. No universal rigorous error enclosure or all-domain guarantee follows from this finite mesh.')
story.append(PageBreak())
CASES=[
 ('heat_transfer','3. Heat-transfer hotspot','Position x, y (normalized)','Temperature (K)','The registered smooth field combines a localized Gaussian hotspot with sinusoidal spatial variation. It is an analytic temperature surrogate; Fourier conduction and boundary conditions are not solved.','Possible validation: compare against measured thermocouple arrays or an independently solved steady heat equation with prescribed material properties and geometry.'),
 ('motor_resonance','4. Rotating-machinery resonance','Frequency (Hz); speed (rpm)','Vibration response (mm/s)','A rational resonance peak shifts with rotational speed and is augmented by a localized exponential peak. It models only a stylized response surface, not a measured motor fault signature.','Possible validation: use controlled run-up vibration spectra and machine-specific resonance observations, with harmonic and sensor calibration checks.'),
 ('robot_clearance','5. Robot workcell clearance','End-effector x and y (m)','Clearance (m)','The analytic field forms safe-looking and low-clearance regions using signed Gaussian terms. It is not a signed-distance field computed from collision geometry.','Possible validation: calculate true minimum distances against CAD collision objects and verify robot-joint constraints and tool trajectories.'),
 ('transformer_hotspot','6. Transformer hotspot response','Current (p.u.); ambient (°C)','Hotspot temperature (°C)','The field combines ambient temperature, a squared-current rise and a smooth localized load effect. Parameters are illustrative and are not a thermal qualification curve.','Possible validation: apply instrumented transformer temperature histories and recognized loading-guide thermal models before engineering use.'),
 ('reactor_conversion','7. Chemical reactor conversion','Temperature (K); residence time (s)','Conversion fraction (0–1)','An explicit first-order Arrhenius-like saturating response is evaluated. No velocity field, pressure, composition transport or heat balance is solved.','Possible validation: use kinetic experiments, reaction enthalpy, flow and mixing records and domain-specific mass/energy balance checks.'),
 ('pressure_loss','8. Pipeline pressure loss','Flow (m³/s); roughness (mm)','Pressure drop (kPa)','The declared nonlinear surface includes a squared-flow component, a logarithmic roughness dependence and a cubic-flow term. It is not a Darcy–Weisbach or network hydraulic solver.','Possible validation: compare with physically parameterized pipe diameters, fluids, Reynolds-dependent friction factors and pressure-sensor records.'),
]
for i,(stem,title,inputs,output,meaning,validation) in enumerate(CASES,1):
 add(title,'HeadX')
 add(f'<b>Declared axes:</b> {inputs}. <b>Output:</b> {output}.')
 figure(f'{i:02d}_{stem}.png')
 add('Figure '+str(i)+'. Three-dimensional paceval-calculated numerical surface (left) and an independently rendered contour projection of the same 6,561 CSV numbers (right).','TinyX')
 add('<b>Mathematical interpretation.</b> '+meaning)
 add('<b>Industrial verification path.</b> '+validation)
 add('The complete numeric grid is distributed as <font color="#147e92">examples/'+stem+'.csv</font>. The formula is fixed in the C++ model registry and exported verbatim into examples/manifest.csv.','TinyX')
 story.append(PageBreak())
add('9. Reproducibility, boundaries and external context','HeadX')
add('Build and evaluation (Linux x86-64 tested with a provided external ABI-compatible shared library):')
for ln in ['cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so','cmake --build build -j','ctest --test-dir build --output-on-failure','./build/industrial_3d --out examples','python3 src/make_figures.py --data examples --figures figures']:
 add(ln.replace('&','&amp;'),'TinyX')
add('The original paceval_main.h and paceval_main.cpp are compiled as sources alongside the research host; only the facade include location was adjusted. The external Linux runtime is not redistributed. Original upstream license headers remain intact. No separate LICENSE_NOTICE.md is part of the publication.')
add('All six source data files and all six pairs of PNG/PDF scientific figures are included. The plotting script refuses to run if CSVs are missing or contain a wrong grid size; there is no default alternate image-generation fallback.')
add('The 3D case studies demonstrate reusable deterministic mathematical visualization; they are NOT validated industrial twins, FEM/CFD simulation results, safety certifications or real sensor predictions. More extensive industrial deployment requires independently specified governing models, measured datasets, uncertainty estimates and fit-for-purpose domain validation.')
add('Selected external sources','HeadX')
for source in ['paceval C/C++ public API: https://paceval.com/api/','High-temperature heat-upgrade digital-twin architecture: https://www.mdpi.com/2076-3417/15/5/2350','Digital twin prognostics and health management review: https://www.nature.com/articles/s41598-024-63990-0','Robotics manufacturing digital twin study: https://arxiv.org/abs/2410.14934','Substation digital-twin research: https://www.mdpi.com/1424-8220/25/18/5689','NIST-JARVIS materials informatics: https://jarvis.nist.gov/']:
 add(source,'TinyX')
add('Conclusion. The real SDK run successfully evaluated six reusable nontrivial industrial mathematical graphs and generated independently checked 3D numerical scientific figures. Further claims about physical models require application-specific evidence.')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
