#!/usr/bin/env python3
"""Rebuild the illustrated 12-page English paceval battery-twin whitepaper from recorded results.
ReportLab fixed-page layout avoids unplanned overlaps and preserves figure aspect ratios.
All result diagrams are directly sourced from original paceval run CSVs.
"""
import argparse,csv,math,os,io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

PW,PH=A4;LEFT=48;RIGHT=48;W=PW-LEFT-RIGHT
COL=HexColor('#233e51');TEAL=HexColor('#216e70');ORANGE=HexColor('#c67d44');MUTED=HexColor('#5b6e73');PALE=HexColor('#edf5f2');LINE=HexColor('#d7e2e2')
FONTS='/usr/share/fonts/truetype/dejavu'
for n,p in [('Body','DejaVuSans.ttf'),('BodyBold','DejaVuSans-Bold.ttf')]:
 pdfmetrics.registerFont(TTFont(n,str(Path(FONTS)/p)))

class Paper:
 def __init__(self,root):
  self.root=root;self.pdf=root/'paceval_Battery_Twin_Equivalent_Circuit_Functions_Whitepaper_EN.pdf';self.c=canvas.Canvas(str(self.pdf),pagesize=A4, pageCompression=1);self.c.setTitle('Battery Twin Equivalent-Circuit Functions | paceval Research');self.page=0;self.y=0
  self.style=ParagraphStyle('p',fontName='Body',fontSize=9.35,leading=14.8,textColor=COL,spaceAfter=0)
  self.small=ParagraphStyle('s',parent=self.style,fontSize=8.45,leading=12.6)
  self.table=ParagraphStyle('t',parent=self.style,fontSize=7.7,leading=11)
 def begin(self,heading,eyebrow='SCIENTIFIC RESEARCH DEMONSTRATOR'):
  self.page+=1;self.c.setFillColor(TEAL);self.c.rect(0,PH-14,PW,14,fill=1,stroke=0)
  self.c.setFont('BodyBold',7.5);self.c.setFillColor(MUTED);self.c.drawString(LEFT,PH-36,'paceval | RESEARCH | 2026');self.c.drawRightString(PW-RIGHT,PH-36,eyebrow)
  self.c.setStrokeColor(LINE);self.c.line(LEFT,PH-44,PW-RIGHT,PH-44)
  self.y=PH-70
  if heading:
   self.title(heading)
 def title(self,s):
  self.c.setFont('BodyBold',16);self.c.setFillColor(COL);self.c.drawString(LEFT,self.y,s);self.y-=31
 def sub(self,s):
  self.space(7);self.c.setFont('BodyBold',10.3);self.c.setFillColor(TEAL);self.c.drawString(LEFT,self.y,s);self.y-=20
 def space(self,dy):self.y-=dy
 def p(self,s,small=False,width=W,x=LEFT):
  style=self.small if small else self.style
  para=Paragraph(s,style);ow,oh=para.wrap(width,1400)
  self.must(oh+4);para.drawOn(self.c,x,self.y-oh);self.y-=oh+9
 def must(self,height):
  if self.y-height<60:raise RuntimeError(f'page {self.page}: content overflow: y={self.y:.1f}, height={height:.1f}')
 def note(self,s):
  self.c.setFillColor(PALE);h=44;self.must(h+5);self.c.roundRect(LEFT,self.y-h,W,h,7,stroke=0,fill=1)
  p=Paragraph(s,self.small);_,ph=p.wrap(W-22,h);p.drawOn(self.c,LEFT+12,self.y-ph-9);self.y-=h+11
 def fig(self,name,caption,maxh=220):
  src=self.root/'figures'/(name+'.png');img=ImageReader(str(src));wi,hi=img.getSize();ratio=wi/hi
  width=min(W,maxh*ratio);height=width/ratio;self.must(height+48)
  self.c.drawImage(img,LEFT+(W-width)/2,self.y-height,width=width,height=height,mask='auto',preserveAspectRatio=True)
  self.y-=height+5
  self.p(caption,small=True);self.space(4)
 def tab(self,headers,rows,widths=None):
  data=[[Paragraph(f'<b>{str(x)}</b>',self.table) for x in headers]]
  for row in rows:data.append([Paragraph(str(x),self.table) for x in row])
  t=Table(data,colWidths=widths or [W/len(headers)]*len(headers),hAlign='LEFT',repeatRows=1)
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#ffffff'),HexColor('#f8faf9')]),('LINEBELOW',(0,0),(-1,0),.65,TEAL),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
  _,th=t.wrap(W,1200);self.must(th);t.drawOn(self.c,LEFT,self.y-th);self.y-=th+13
 def eq(self,text):
  eqs={
   'Vterm':r'V_{\mathrm{term}}=V_{\mathrm{OCV}}(z,T)-I R_0(z,T)-\sum_{i=1}^{n}V_{p,i}',
   'dVpi':r'\frac{dV_{p,i}}{dt}=-\frac{V_{p,i}}{\tau_i}+\frac{I R_i}{\tau_i},\quad \tau_i=R_i C_i',
   'Vpi,next':r'V_{p,i}^{k+1}=e^{-\Delta t/\tau_i}V_{p,i}^k+I R_i(1-e^{-\Delta t/\tau_i})',
   'znext':r'z_{k+1}=z_k-\frac{I_k\Delta t\,a}{3600Q},\quad Q=3.2\,\mathrm{Ah}',
   'Tnext':r'T_{k+1}=T_k+\frac{\Delta t}{C_{\mathrm{th}}}[P_{\mathrm{heat}}-h(T_k-T_a)]',
   'I OCV':r'I V_{\mathrm{OCV}}=I V_{\mathrm{term}}+I^2 R_0+\sum_i I V_{p,i}'
  }
  tex=next((v for k,v in eqs.items() if text.startswith(k)),None)
  if tex is None:raise ValueError('No matching mathematical equation '+text)
  self.must(44)
  fig=plt.figure(figsize=(8.4,.5),dpi=220)
  fig.patch.set_alpha(0)
  fig.text(.5,.5,'$'+tex+'$',ha='center',va='center',fontsize=15,color='#233e51')
  out=io.BytesIO();fig.savefig(out,format='png',dpi=220,transparent=True,bbox_inches='tight',pad_inches=.03)
  plt.close(fig);out.seek(0)
  img=ImageReader(out);iw,ih=img.getSize();h=min(36, W*ih/iw);w=h*iw/ih
  self.c.drawImage(img,LEFT+(W-w)/2,self.y-h,width=w,height=h,mask='auto')
  self.y-=h+10
 def end(self):
  self.c.setStrokeColor(LINE);self.c.line(LEFT,48,PW-RIGHT,48)
  self.c.setFillColor(MUTED);self.c.setFont('Body',7);self.c.drawString(LEFT,32,'paceval | Battery Twin Equivalent-Circuit Functions | 2026')
  self.c.drawRightString(PW-RIGHT,32,str(self.page));self.c.showPage()
 def complete(self):self.c.save()

def produce(root):
 p=Paper(root)
 with (root/'results/scenario_summary.csv').open() as f: rows=list(csv.DictReader(f))
 with (root/'results/sdk_execution.txt').open() as f:counts=dict(x.strip().split('=',1) for x in f if '=' in x)
 vals=lambda r,k:float(r[k])
 urban=next(r for r in rows if int(r['profile'])==0 and int(r['version'])==2 and float(r['ambient_C'])==25)
 # 1 cover with broad exact-ratio image
 p.begin('',eyebrow='ORIGINAL paceval | SCIENTIFIC NUMERICAL VALIDATION')
 p.y=PH-110;p.c.setFillColor(COL);p.c.setFont('BodyBold',23)
 p.c.drawString(LEFT,p.y,'Battery Twin')
 p.c.drawString(LEFT,p.y-34,'Equivalent-Circuit Functions')
 p.y-=78;p.p('Parameterized 1RC/2RC execution graphs for a reproducible electro-thermal battery-model demonstrator.',small=False)
 img=ImageReader(str(root/'figures/00_battery_twin_hero.png'));p.c.drawImage(img,LEFT,p.y-245,width=W,height=245,preserveAspectRatio=True);p.y-=254
 p.p('<i>Concept illustration; not a computed research result. Reused in the project README.</i>',small=True)
 p.sub('Executed research outcome')
 p.p(f'<b>{counts["registered_and_executed_graphs"]} executed original paceval graphs</b>  |  <b>{counts["scenarios"]} synthetic scenarios</b>  |  <b>{counts["multi_graph_batch_calls"]} multi-graph batches</b>')
 p.p('Independently verified complete electrical and thermal traces; all graph definitions and technical audits are included in the GitHub package. Scope: synthetic single-cell surrogate, not validated BMS or electrochemical aging prediction.',small=True)
 p.end()
 # 2 introduction
 p.begin('1. Industrial use case and current state of the art')
 p.p('A battery management system (BMS) interprets electrical measurements to track a rechargeable cell through dynamic loads. A battery digital twin is a mathematical model repeatedly evaluated under current, ambient-temperature and operating-condition changes. Its practical outputs include terminal voltage, an estimated charge state, polarization states and an approximate thermal response. These outputs may guide algorithm research and laboratory test planning; this report does not implement an operational safety controller.')
 p.sub('Why reusable mathematics matters')
 p.p('Equivalent-circuit models represent cell behavior using an open-circuit voltage (OCV) map, series resistance and one or more RC polarization branches. The current schedule changes quickly, while parameters depend on SOC, temperature and possibly aging. Repeated recalculation of the same expressions across many scenarios is therefore a natural setting for persistent computation graphs.')
 p.sub('Established and recent research')
 p.p('Reviews published in 2025 and 2026 examine 1RC/2RC battery parameter estimation, state observers and the trade-off between model complexity and identifiability [1-3]. A 2026 practical guide emphasizes designed pulse experiments, relaxation intervals, use of time constants and validation over actual measured temperature and SOC domains [2]. An open battery model such as PyBaMM offers Thevenin-style RC models; MathWorks Simscape Battery documents comparable electro-thermal models with tabulated SOC- and temperature-dependent parameters [4-5].')
 p.sub('A concrete illustrative workflow')
 p.p('A hypothetical laboratory engineer programs current steps for a nominal 3.2 Ah cell. Measured current and temperature would normally be passed to the model, which evaluates electrical parameters, advances RC states and predicts a cell terminal voltage. This demonstrator uses deterministic synthetic schedules instead of measured data to make every numerical pathway reproducible.')
 p.note('Publication boundary: the demonstrated numbers characterize a declared synthetic model, not a commercially manufactured cell. No accuracy, speed or safety advantage over established BMS products is asserted.')
 p.end()
 # 3 architecture
 p.begin('2. Research question and experimental architecture')
 p.p('Can the original paceval SDK evaluate the complete mathematical kernel of a versioned, parameter-dependent 1RC/2RC battery equivalent-circuit model, rather than a trivial isolated expression, while C++ handles state orchestration and independent programs verify the complete results?')
 p.fig('01_workflow','Figure 1. Conceptual execution pipeline. Only the analytical battery graphs are assigned to paceval; time schedules, state administration and audits belong to the host/reference.',maxh=184)
 p.sub('Controlled comparison')
 p.p('Two immutable model versions coexist: v1 includes one RC polarization branch; v2 includes two. Both use identical current schedules, initial conditions and SOC/temperature-dependent parameter laws. The additional RC branch is a controlled model revision, not evidence that two branches are intrinsically better.')
 p.sub('Reproducible inputs and outputs')
 p.p('All 18 cases use 720 intervals of 2 seconds and identical signed-current conventions. The C++ host carries prior states across steps. The original paceval Multi-Graph Batch API returns next-state values, terminal voltage, electrical powers, heat proxy, voltage margins and domain scores. CSVs preserve the outputs; separate native and 80-decimal oracles inspect them.')
 p.end()
 # 4 equations
 p.begin('3. Defined mathematical model')
 p.p('Current I is positive during discharge and negative during charging. The dimensionless charge state is z; polarization voltages are Vp1 and Vp2, and T and Ta are cell and ambient temperatures in degrees Celsius. Resistances are in ohms and RC time constants are in seconds.')
 p.sub('Two-branch Thevenin topology')
 p.eq('Vterm = OCV(z,T) - I R0(z,T) - sum(Vpi),  i = 1..n')
 p.eq('dVpi/dt = -Vpi / taui + I Ri / taui,    taui = Ri Ci')
 p.p('For each fixed two-second interval, paceval evaluates the algebraically exact constant-coefficient RC update. Because R, tau and OCV vary with z and T between intervals, the whole nonlinear trajectory is not an exact global solution.')
 p.eq('Vpi,next = exp(-dt/taui) Vpi + I Ri [1-exp(-dt/taui)]')
 p.sub('Charge state, thermal proxy and power decomposition')
 p.eq('znext = z - I dt age / (3600 Q),      Q = 3.2 Ah')
 p.eq('Tnext = T + (dt/Cth) [Pheat - h(T-Ta)]')
 p.eq('I OCV = I Vterm + I^2 R0 + sum(I Vpi)')
 p.p('The last identity is an instantaneous algebraic decomposition of the declared circuit voltage, not proof of full thermodynamic energy conservation. The illustrative heat proxy includes positive series and polarization-resistance dissipation but omits reversible heat, structural heat flow and electrochemical losses.')
 p.note('Exact numeric parameter expressions and units are in results/formula_registry.csv; all relevant formulas are executed as original paceval graphs, not copied from the independent oracle.')
 p.end()
 # 5 table
 p.begin('4. Original paceval execution architecture')
 p.p('Version 4.25 C/C++ headers are supplied without replacing the original engine. One include path in the SDK translation unit is adapted to this project. The engine is initialized before graph creation and freed after handle deletion. Each handle is retained across all independent scenarios.')
 p.tab(['Mathematical function / purpose','Actual owner','Graph IDs or rationale'],[
 ('Open-circuit voltage; SOC/temperature parameter laws','paceval','ocv; ohmic_resistance; fast/slow_resistance; fast/slow_tau'),
 ('SOC and exact frozen-coefficient RC state transitions','paceval','next_soc; next_fast_polarization; next_slow_polarization_v1/v2'),
 ('Voltage and cell-temperature next states','paceval','terminal_voltage_v1/v2; next_cell_temperature_v1/v2'),
 ('Heat proxy, powers and electrical power identity','paceval','resistive_heat_proxy_v1/v2; *_power_v1/v2; power_identity_residual_v1/v2'),
 ('Signed SOC, voltage and temperature margins','paceval','soc_*_margin; voltage_*_margin_v1/v2; thermal_upper_margin'),
 ('Local analytical parametric sensitivities','paceval','d_ocv_d_soc; d_r0_d_soc; d_r0_d_temp; d_voltage_d_*'),
 ('20 composed load/voltage/temperature/capacity score variants','paceval','composite_cost_v1_01...10; composite_cost_v2_01...10'),
 ('Current program, external time loop, file operations','C++ host','Stateful orchestration; no substitute mathematical kernel'),
 ('Independent trajectories and decimal mathematical oracle','Python','Separate verification only; never presented as paceval execution')],widths=[205,67,W-272])
 p.p('The actual evaluation path calls paceval_dGetMultipleComputationsResultsExt, with graph-major results verified against an independent reference. Scalar paceval_dGetComputationResult is exercised independently. All 75 registered graphs appear in executed batch probes; numeric outputs are recorded without double-counting scenarios as graph creations.',small=True)
 p.end()
 # 6 workload
 p.begin('5. Deterministic workload and executed outcomes')
 p.p('Three synthetic input schedules (urban pulses, sustained highway load, and charge/rest), three fixed ambient temperatures (5, 25, 40 C) and two simultaneously active model versions produce 18 scenario trajectories. Every trajectory has 720 steps of 2 seconds. The nominal capacity is 3.2 Ah; the charge/rest profile uses a synthetic capacity/resistance modifier of 1.12 for sensitivity exploration, not an empirically established degradation law.')
 p.sub('Representative 25 C outcomes (executed paceval C++ run)')
 rr=[r for r in rows if r['ambient_C']=='25' and r['version']=='2']
 names={0:'Urban pulses',1:'Highway load',2:'Charge/rest'}
 p.tab(['Current schedule','Final SOC','Final T (C)','Min voltage (V)','Terminal energy (Wh)'],[
 (names[int(r['profile'])],f'{vals(r,"final_soc"):.4f}',f'{vals(r,"final_temperature_C"):.2f}',f'{vals(r,"min_voltage_V"):.3f}',f'{vals(r,"terminal_energy_Wh"):.3f}') for r in rr],widths=[129,70,90,105,W-394])
 p.sub('What the results demonstrate')
 p.p('The outputs are meaningful industrial-domain quantities: voltage response, charge depletion, thermal state, an electrical power split and model-revision differences. For the urban profile at 25 C, the 2RC example gives final SOC %.6f and a terminal-energy integral of %.5f Wh. Those are produced from actual repeated paceval evaluations, not from the reference implementation.'%(vals(urban,'final_soc'),vals(urban,'terminal_energy_Wh')))
 p.p('Voltage and temperature limits are synthetic mathematical test thresholds only. They are not cell-manufacturer specifications, experimentally verified hazards or certified BMS safe-operating-area boundaries.')
 p.note('Recorded execution: %s actual graph handles; %s batch calls; %s batch outputs; 18 complete scenarios. Detailed independent numerical checks remain in the package audit files.'%(counts['registered_and_executed_graphs'],counts['multi_graph_batch_calls'],counts['graph_batch_outputs']))
 p.end()
 # figs 2 to 9
 for title,figs in [
 ('6.1 Input schedules and terminal-voltage response',[
  ('02_current_profiles','Figure 2. Three deterministic synthetic current schedules. Positive current corresponds to discharge; negative values represent charging.'),
  ('03_terminal_voltage','Figure 3. Identical synthetic urban load; different 1RC and 2RC versions produce differing voltage trajectories.')]),
 ('6.2 Charge state and thermal behavior',[
  ('04_soc_profiles','Figure 4. Computed SOC history for the 2RC version across three programmed schedules, at 25 C ambient.'),
  ('05_thermal_response','Figure 5. Lumped thermal proxy response to sustained highway load for three external temperatures; synthetic cell coefficients.')]),
 ('6.3 State-dependent electrical parameter surfaces',[
  ('06_voltage_surface_3d','Figure 6. Three-dimensional original paceval-loaded voltage evaluations, at fixed current, polarization inputs and age modifier.'),
  ('07_ohmic_resistance_map','Figure 7. State-of-charge and cell-temperature dependence of the declared synthetic ohmic parameter.')]),
 ('7. Controlled model changes and RC dynamics',[
  ('08_relaxation_time_scales','Figure 8. Relative time-scale separation for two RC branches, recalculated with original paceval parameter graphs.'),
  ('09_formula_version_response','Figure 9. Voltage response difference between two complete independently advanced model versions; not merely a fixed-state voltage comparison.')])]:
  p.begin(title)
  for name,cap in figs:p.fig(name,cap,maxh=245 if '06_' not in name else 255)
  p.end()
 # 11 energy
 p.begin('8. Electrical energy accounting and numerical audit')
 p.fig('10_electrical_energy_terms','Figure 10. Signed 2RC electrical energy terms, obtained from original paceval-produced power samples integrated by the host. Negative values indicate net charging; terms do not represent complete thermodynamic heat loss.',maxh=240)
 p.sub('Independent validation results')
 p.p('The source package includes a second implementation that reconstructs all 18 state trajectories, terminal-voltage samples, electrical integrals, temperatures and extrema without calling paceval. An independent mpmath oracle, configured with 80 decimal places, checks the original binary64 numerical input values against all registered graph definitions on representative executed rows.')
 p.tab(['Audit dimension','Observed run'],[
 ('Registered and actually executed graphs',counts['registered_and_executed_graphs']),('Original SDK graph outputs',counts['graph_batch_outputs']),('Native C++ one-step comparisons',counts['independent_native_comparisons']),('Independent high-precision graph comparisons',counts['graph_inventory_probe_rows']),('Complete trajectory and energy reference','All 18 scenarios passed')],widths=[W*.7,W*.3])
 p.p('The detailed numeric differences, tolerances and exceptional conditions are retained in machine-readable results/high_precision_audit.json and results/independent_trajectory_audit.json rather than published as comparative precision charts.',small=True)
 p.end()
 # 12 limitations references
 p.begin('9. Interpretation, reproducibility and references')
 p.sub('Interpretation and limitations')
 p.p('This experiment confirms that the mathematical kernel of a nonlinear 1RC/2RC surrogate can be executed using original reusable paceval graphs and verified independently under a controlled synthetic workload. It does not show model accuracy against an actual cell, correctness of any temperature or ageing law, parameter identifiability, safe BMS integration, interval certification, runtime advantage or savings. State-dependent frozen-coefficient RC stepping and the lumped thermal proxy are explicit approximations.')
 p.sub('Reproduction')
 p.p('Build on Linux x86-64 using the CMakeLists.txt in src/, the packaged original paceval_main.h and paceval_main.cpp and a separately acquired compatible shared library passed using PACEVAL_RUNTIME. Run CTest, the 720-step binary, verify_results.py, high_precision_reference.py, make_figures.py and check_readme_math.py. All source and numeric results are included; the proprietary/external paceval shared library is omitted.')
 p.sub('Selected current research and engineering references')
 refs=[
 '[1] 2025. Advancements in parameter estimation techniques for 1RC and 2RC equivalent-circuit models. Journal of Energy Storage. doi:10.1016/j.est.2025.115581.',
 '[2] 2026. How to parameterise an equivalent-circuit empirical battery model from time-domain data. PMC13049963.',
 '[3] 2026. Comprehensive Review of Equivalent Circuit Models and Neural Network Models for Battery Management Systems. Batteries 12(1), 37. doi:10.3390/batteries12010037.',
 '[4] PyBaMM documentation: Thevenin Equivalent Circuit Model. docs.pybamm.org.',
 '[5] MathWorks Simscape Battery 2026: Battery Equivalent Circuit block. mathworks.com/help/simscape-battery/',
 '[6] CALCE battery experimental data library. University of Maryland, calce.umd.edu/data.',
 '[7] paceval Mathematical Engine and original C/C++ API. github.com/paceval/paceval.'
 ]
 for t in refs:p.p(t,small=True)
 p.p('Source and licensing: SDK copyright and AGPL notices have been preserved. The code author/reuser is responsible for applicable license compliance. The synthetic illustration on the cover does not represent measured laboratory equipment.',small=True)
 p.end()
 p.complete();print('whitepaper created',p.pdf,'pages',p.page)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p=a.parse_args();produce(p.root)
