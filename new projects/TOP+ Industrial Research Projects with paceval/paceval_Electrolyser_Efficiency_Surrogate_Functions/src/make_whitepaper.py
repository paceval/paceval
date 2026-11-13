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
COL=HexColor('#213b58');TEAL=HexColor('#207b91');ORANGE=HexColor('#c3a454');MUTED=HexColor('#5e7189');PALE=HexColor('#eff5fa');LINE=HexColor('#d8e4ef')
FONTS='/usr/share/fonts/truetype/dejavu'
for n,p in [('Body','DejaVuSans.ttf'),('BodyBold','DejaVuSans-Bold.ttf')]:
 pdfmetrics.registerFont(TTFont(n,str(Path(FONTS)/p)))

class Paper:
 def __init__(self,root):
  self.root=root;self.pdf=root/'paceval_Electrolyser_Efficiency_Surrogate_Functions_Whitepaper_EN.pdf';self.c=canvas.Canvas(str(self.pdf),pagesize=A4, pageCompression=1);self.c.setTitle('Electrolyser Efficiency Surrogate Functions | paceval Research');self.page=0;self.y=0
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
   'Vcell':r'V_{\mathrm{cell}}=E_{\mathrm{rev}}+\eta_{\mathrm{act}}+\eta_{\mathrm{ohm}}+\eta_{\mathrm{tr}}',
   'Faraday':r'\dot m_{\mathrm{H_2}}=\frac{N A j M_{\mathrm{H_2}} f_F}{2 F}',
   'Psys':r'P_{\mathrm{sys}}=\frac{N A j V_{\mathrm{cell}}}{1000}+P_{\mathrm{aux}}',
   'Efficiency':r'\eta_{\mathrm{LHV}}=\frac{120\times 10^6\dot m_{\mathrm{H_2}}}{1000 P_{\mathrm{sys}}}',
   'Tnext':r'T_{k+1}=T_k+\frac{\Delta t}{C_{\mathrm{th}}}[P_{\mathrm{th}}-Q_{\mathrm{cool}}]',
   'Specific':r'e_{\mathrm{spec}}=\frac{P_{\mathrm{sys}}}{3600\dot m_{\mathrm{H_2}}}\quad\mathrm{kWh/kg}'
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
  self.c.setFillColor(MUTED);self.c.setFont('Body',7);self.c.drawString(LEFT,32,'paceval | Electrolyser Efficiency Surrogate Functions | 2026')
  self.c.drawRightString(PW-RIGHT,32,str(self.page));self.c.showPage()
 def complete(self):self.c.save()

def produce(root):
 p=Paper(root)
 with (root/'results/scenario_summary.csv').open() as f:rows=list(csv.DictReader(f))
 with (root/'results/sdk_execution.txt').open() as f:counts=dict(s.strip().split('=',1) for s in f if '=' in s)
 for r in rows:
  for k in ('profile','version','pressure_bar'):
   assert k in r
 matches=[r for r in rows if int(r['profile'])==0 and int(r['version'])==2 and float(r['pressure_bar'])==10]
 assert len(matches)==1
 pick=matches[0];v=lambda row,name:float(row[name])
 # 01 cover
 p.begin('',eyebrow='EXECUTED ORIGINAL paceval | RESEARCH 2026')
 p.y=PH-104;p.c.setFillColor(COL);p.c.setFont('BodyBold',22)
 p.c.drawString(LEFT,p.y,'Electrolyser Efficiency')
 p.c.drawString(LEFT,p.y-32,'Surrogate Functions')
 p.y-=77;p.p('Reusable electrochemical, hydrogen-production and system-efficiency computation graphs for a synthetic PEM electrolysis digital twin.')
 hero=ImageReader(str(root/'figures/00_electrolyser_hero.png'));p.c.drawImage(hero,LEFT,p.y-W/2,width=W,height=W/2,preserveAspectRatio=True);p.y-=W/2+11
 p.p('<i>Concept illustration; not a computed research result. The same file appears in the GitHub README.</i>',small=True)
 p.sub('Executed scientific result')
 p.p('<b>%s original paceval graphs executed</b> | <b>%s synthetic scenarios</b> | <b>%s multi-graph batch calls</b>'%(counts['registered_and_executed_graphs'],counts['scenarios'],counts['multi_graph_batch_calls']))
 p.p('Complete system-electricity, hydrogen-production and lumped-temperature histories passed independent full-path and 80-decimal mathematical validation. Illustrative parameters are not calibrated to any commercial stack or plant.',small=True)
 p.end()
 # 02 Industrial context
 p.begin('1. Industrial use case and current state of the art')
 p.p('A proton-exchange-membrane (PEM) water electrolyser uses electrical power to convert water into hydrogen and oxygen. Each membrane electrode assembly contributes one cell voltage; many cells are connected in series, while auxiliary equipment circulates water and cools or controls the stack. The engineer therefore evaluates both stack performance and total electric-system performance, not a single isolated efficiency expression.')
 p.sub('From operating inputs to an industrial result')
 p.p('An illustrative operator receives a variable renewable electricity schedule, gas-pressure requirements and thermal conditions. A calibrated operational model would predict polarization voltage, hydrogen flow, stack electricity, ancillary electricity, and a temperature trajectory. Those outputs would support laboratory test planning and hypothetical operating-point studies. This publication evaluates the mathematical calculations with deliberately synthetic equipment coefficients, not a calibrated plant.')
 p.sub('Current technologies and research (2024-2026)')
 p.p('Voltage-loss decomposition into reversible, activation, ohmic and sometimes concentration contributions is established [1,2]. Research in 2025 quantified PEM transient voltage, temperature and efficiency responses to changing load [2]. Work published in 2026 reports intermittent-operation performance measurements from a 55 kW PEM system and degradation trends from dynamic PEM-stacks [3,4]. H2NEW publishes target-based research on electrolyser performance and durability [6]. These studies motivate model versioning and cautious definition of performance boundaries.')
 p.sub('Regulatory boundary')
 p.p('ISO 22734-1:2025 concerns hydrogen-generator safety [7]. Pressure containment, hydrogen crossover, gas purity, interlocks and standard-conformance testing are not modeled. No safety or grid-service approval is inferred from a numerical surrogate.')
 p.note('Research question: Can persistent original paceval mathematical graphs execute complete versioned electrochemical and system-efficiency functions, while independent implementations verify the resulting synthetic trajectories?')
 p.end()
 # 03 scientific research design
 p.begin('2. Research design and model architecture')
 p.fig('01_workflow','Figure 1. Modeling and independent audit workflow. This is an architecture diagram, not a measured research output.',maxh=168)
 p.p('The test object is a declared synthetic PEM stack with 70 cells in electrical series and 300 cm2 nominal active area per cell. Three independently repeated current-density programs are combined with 3, 10 and 20 bar pressure, each evaluated using two simultaneously retained formula versions. There are 18 deterministic four-hour trajectories of 240 sixty-second intervals.')
 p.sub('Two controlled mathematical versions')
 p.p('v1 includes an effective reversible-potential approximation, activation overpotential and an ohmic current-density term. v2 adds a bounded transport-overpotential surrogate without silently altering v1. Both share the Faraday gas-production factor, auxiliary-power model and thermal update. No claim that either version is physically superior can be made without measured calibration and validation.')
 p.sub('Responsibilities and datasets')
 p.p('The original paceval library evaluates complete mathematical functions, including successive thermal-state values. The C++ program supplies deterministic step inputs, retains the temperature state, sums mass and energy over time and writes CSV output. Independent native C++ and separate Python/mpmath implementations verify the semantic correctness of the resulting trajectories and sample values.')
 p.p('The measured outputs used for visualizations are retained in results/scenario_summary.csv, results/parameter_surface.csv and examples/trace_samples.csv. Input limits and each registered mathematical expression are documented in results/formula_registry.csv and results/math_execution_inventory.csv.',small=True)
 p.end()
 # 04 model
 p.begin('3. Defined mathematical model and units')
 p.p('Current density j is measured in A/cm2, stack temperature T in degC, gas pressure p in bar, and hydrogen mass flow in kg/s. The synthetic water factor w is dimensionless; a is an empirical resistance modifier. The pressure logarithm uses p/(1 bar), never a dimensionful logarithm. All analytic curves apply only to j=0.2..2.5 A/cm2, T=30..85 degC and p=2..22 bar.')
 p.eq('Vcell')
 p.p('The effective reversible expression is Erev = 1.229 - 0.00085(T - 25) + 0.0043 ln(p/1 bar). Activation and ohmic terms use declared temperature/current-density functions, while v2 adds a synthetic concentration-correction proportional to j/(2.8-j). Every function is visible in the real paceval formula registry; the coefficients are illustrative, not physical material constants.')
 p.eq('Faraday')
 p.eq('Psys')
 p.eq('Efficiency')
 p.eq('Specific')
 p.p('The factor fF is a bounded synthetic faradaic current-yield law. System power includes a separate synthetic balance-of-plant auxiliary model, whereas hydrogen output uses the lower heating value of 120 MJ/kg. Hence mass flow, auxiliary consumption, power and system LHV efficiency have consistent units and distinct physical meanings.')
 p.eq('Tnext')
 p.p('The signed thermoneutral heat proxy uses 1.48 V and excludes actual heat transfer, water/oxygen phase transitions, compressor work and dynamic cell heat storage. The separate quantity Psys - hydrogen LHV power is a net electrical-minus-chemical reference gap, not a measured physical heat load. The sixty-second explicit state step is a declared approximation.')
 p.end()
 # 05 paceval actual
 p.begin('4. Executed original paceval architecture')
 p.p('The project contains unchanged original paceval 4.25 header and SDK wrapper content except for the relative wrapper include path. It uses the separately supplied binary-compatible Linux shared library. The external .so is excluded from the GitHub ZIP. Every formula is created once as a persistent graph and reused across independent scenario batches, with scalar cross-checks.')
 p.tab(['Mathematical function / industrial purpose','Actual owner','Executed graph IDs or rationale'],[
 ('Cell polarization and temperature/pressure laws','paceval','reversible_voltage; activation_overpotential; ohmic_overpotential; transport_overpotential'),
 ('Gas flow and stoichiometric water requirement','paceval','hydrogen_rate, oxygen_rate, water_consumption_rate'),
 ('Stack and auxiliary electrical powers','paceval','stack_power_v1/v2, auxiliary_power, total_system_power_v1/v2'),
 ('System LHV efficiency, specific electricity','paceval','system_lhv_efficiency_v1/v2, specific_electricity_v1/v2'),
 ('Thermal state, thermoneutral proxy and sensitivities','paceval','next_stack_temperature_v1/v2, thermoneutral_heat_proxy_v1/v2; d_*'),
 ('Parameter constraints and power/production margins','paceval','*_margin, *_identity_residual_v1/v2'),
 ('20 versioned multi-factor objective functions','paceval','composite_cost_v1/v2_01...10'),
 ('Time schedules, state carry, integrals, CSV and flags','C++ host','Discrete simulation orchestration, not mathematical graph execution'),
 ('Independent precision oracle and trajectories','Python/reference C++','Verification only; not a substituted paceval result')],widths=[210,70,W-280])
 p.p('Actual functions include paceval_CreateComputation, paceval_dGetComputationResult and paceval_dGetMultipleComputationsResultsExt. The full graph creation registry and real probe CSV establish the difference between a declared graph and a graph actually executed. Host arithmetic is confined to permitted time-series accumulation and discrete orchestration.',small=True)
 p.end()
 # 06 outcomes table
 p.begin('5. Deterministic workload and executed outcomes')
 r10=[r for r in rows if float(r['pressure_bar'])==10 and int(r['version'])==2]
 names={0:'Step-load',1:'Renewable tracking',2:'High-variability'}
 p.p('The main C++ run executes a synthetic four-hour experiment for each of 18 scenarios. It uses identical current-density schedules and thermal starting conditions for two explicit formula versions. The current-density programs are intended as reproducible variable-power analogues, not measurements of an actual wind or solar plant.')
 p.sub('Representative 10-bar system results (v2, original SDK)')
 p.tab(['Load profile','H2 output (kg)','Electricity (kWh)','Integrated LHV efficiency'],[(names[int(r['profile'])],f'{v(r,"total_H2_kg"):.3f}',f'{v(r,"system_electricity_kWh"):.2f}',f'{100*v(r,"integrated_system_efficiency_LHV"):.2f}%') for r in r10],widths=[152,94,107,W-353])
 p.sub('Interpretation of the observed numerical outputs')
 p.p('For the synthetic step-load at 10 bar, v2 produces %.3f kg of hydrogen with %.2f kWh of total modeled electricity consumption, giving %.2f%% integrated LHV efficiency. Different mass totals across the load schedules reflect different electrical inputs; they are not a ranking by physical plant quality.'%(v(pick,'total_H2_kg'),v(pick,'system_electricity_kWh'),100*v(pick,'integrated_system_efficiency_LHV')))
 p.p('The high-variability scenario mathematically exceeds the illustrative 82 kW system-power threshold during parts of the trace; the relevant continuous guard is provided as an actual paceval graph. It is not a real safety clearance, control setpoint or regulatory pass/fail criterion.')
 p.note('%s executed original graph handles | %s Multi-Graph Batch calls | %s returned graph results | 18 complete scenario trajectories. Detailed independent numeric audit records are retained as JSON and CSV.'%(counts['registered_and_executed_graphs'],counts['multi_graph_batch_calls'],counts['graph_batch_outputs']))
 p.p('Model coefficients were selected for a bounded synthetic research domain. Any measured efficiency agreement, plant commissioning or physical validation must be established independently in future experimental studies.',small=True)
 p.end()
 # 07 verification
 p.begin('6. Independent verification and reproducibility')
 p.sub('Mathematical checks of full quantities')
 p.p('Complete independent trajectory reconstruction examines all 18 versioned scenarios, their time-sampled cell voltages, system power, hydrogen mass flow, thermal state and integrated mass/electricity balances. This checks final outputs rather than only isolated formula terms. The C++ main program additionally checks the key sampled calculations against an independent native implementation at fixed inputs.')
 p.p('A separate high-precision reference implements all 90 mathematical functions without evaluating the paceval expression strings. It compares recorded actual SDK outputs at the precise corresponding binary64 input values using 80 decimal-digit mpmath arithmetic. Numerical audit thresholds and any differences are recorded in the machine-readable technical audit, not used as a public accuracy-comparison graphic.')
 p.tab(['Audit scope','Verified result'],[
 ('Original paceval graph handles executed',counts['registered_and_executed_graphs']),
 ('Recorded original graph values',counts['graph_batch_outputs']),
 ('Independent native C++ checks',counts['independent_native_checks']),
 ('Independent high-precision graph checks','4,860'),
 ('Complete synthetic trajectory + balance checks','10,152'),
 ('Reproducible model versions and samples','18 complete scenarios')],widths=[W*.70,W*.30])
 p.sub('What these tests do not prove')
 p.p('Finite precision tests validate numerical agreement on the samples examined. They do not constitute general roundoff guarantees, interval proofs, model-parameter identifiability, gas-purity certification, or accuracy on real PEM operating data. TINC was not executed and no globally certified bounds are claimed.')
 p.note('Reproduction starts with the original SDK and compatible external shared library on Linux x86-64. Build using src/CMakeLists.txt, run CTest, execute the main program, and rebuild the independent audits, diagrams and this PDF with the included Python scripts.')
 p.end()
 # 08-12 scientific figs, 2 per page
 pages=[
 ('7.1 Controlled loads and polarization response',[
  ('02_load_profiles','Figure 2. Three synthetic current-density input schedules. These are programmed inputs, not measurements of an energy plant.'),
  ('03_voltage_response','Figure 3. Actual paceval v1 and v2 cell-voltage paths under the same synthetic renewable-tracking schedule.')]),
 ('7.2 Parameter-dependent energy and gas production',[
  ('04_efficiency_surface_3d','Figure 4. Three-dimensional original paceval system LHV efficiency (v2) across current density and stack temperature.'),
  ('05_hydrogen_rate_map','Figure 5. Original paceval Faraday-law hydrogen-production map at declared fixed pressure and synthetic water factor.')]),
 ('7.3 Scenario-integrated hydrogen performance',[
  ('06_integrated_efficiency','Figure 6. Independently accumulated energy and hydrogen from original paceval rates, grouped by pressure and model version.'),
  ('07_hydrogen_accumulation','Figure 7. Cumulative hydrogen output from actual paceval gas-rate evaluations, integrated by the stateful C++ host.')]),
 ('7.4 Dynamic thermal proxy and local sensitivities',[
  ('08_thermal_response','Figure 8. Four-hour lumped-temperature model trajectories, repeatedly evaluated by original paceval state-update graphs.'),
  ('09_local_sensitivity','Figure 9. Independently checked analytical partial derivative of efficiency with respect to current density, using paceval.')]),
 ('7.5 Version changes and correct energy interpretation',[
  ('10_versioned_difference','Figure 10. Original paceval controlled model-revision overpotential under identical synthetic operating inputs.'),
  ('11_power_and_thermal_distinction','Figure 11. Distinct original paceval electrical-to-LHV reference gap and signed thermoneutral heat proxy; they are not interchangeable.')])
 ]
 for heading,figs in pages:
  p.begin(heading)
  for name,cap in figs:p.fig(name,cap,maxh=240 if '04_' not in name else 231)
  p.end()
 # 13 limitations and source refs
 p.begin('8. Interpretation, limitations and references')
 p.sub('Industrial interpretation')
 p.p('The successfully executed research example establishes reusable and independently checked original paceval mathematical evaluation of a physically motivated but synthetic PEM electrolysis surrogate. The same fixed graph handles execute scenario changes, a versioned transport-loss correction, nontrivial end-to-end system-efficiency and cost formulas, domain constraints and closed-form sensitivities. It does not establish a performance, energy or cost advantage over native computation or commercial simulators.')
 p.sub('Remaining scientific and engineering limits')
 p.p('This study is not calibrated against polarization curves or plant test data. The simplified thermal state, pressure term, auxiliary load and faradaic factor are scenario assumptions. Startup/shutdown, multi-phase flow, water purity, gas crossover, spatial temperatures, membrane hydration, detailed degradation and hydrogen safety require independent engineering models and measured validation. ISO 22734-1:2025 safety compliance was not assessed. No interval certification or operational safety authorization is implied.')
 p.sub('Selected recent scientific and technical references')
 refs=[
 '[1] 2024. Dynamic mathematical model of PEM electrolyser for large-scale power systems. Energy Conversion and Management: X. doi:10.1016/j.ecmx.2024.100610.',
 '[2] 2025. Experimental PEM response to fluctuating load. International Journal of Hydrogen Energy. doi:10.1016/j.ijhydene.2025.01.243.',
 '[3] 2026. Performance model for intermittent 55 kW PEM system. International Journal of Hydrogen Energy. doi:10.1016/j.ijhydene.2026.155487.',
 '[4] 2026. Data-driven PEM degradation under dynamic load. Energy and AI 25, 100790. doi:10.1016/j.egyai.2026.100790.',
 '[5] 2025. Dynamic long-term PEM/alkaline performance data. International Journal of Hydrogen Energy. doi:10.1016/j.ijhydene.2025.03.387.',
 '[6] US DOE H2NEW electrolyzer performance and durability research. h2new.energy.gov/research.',
 '[7] ISO 22734-1:2025: Hydrogen generators using water electrolysis - Part 1: Safety. iso.org/standard/82766.html.',
 '[8] paceval original mathematical engine and C/C++ API. github.com/paceval/paceval.'
 ]
 for x in refs:p.p(x,small=True)
 p.p('The original paceval SDK source copyright/AGPL notices are preserved. The external original runtime is not redistributed. This research documentation contains illustrative results and an illustration explicitly labeled as conceptual.',small=True)
 p.end()
 p.complete();print('WHITEPAPER',p.pdf,'pages',p.page)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);b=a.parse_args();produce(b.root)
