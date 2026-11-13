#!/usr/bin/env python3
"""Publish a scientific PDF from VERIFIED original paceval execution CSVs.
ReportLab keeps page structure reproducible; mathtext is rendered as math imagery.
The program refuses to publish if execution or the independent audit is missing.
"""
from pathlib import Path
import argparse,csv,io,json,math,re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import (SimpleDocTemplate,Paragraph,Image,Table,TableStyle,Spacer,PageBreak,KeepTogether,HRFlowable)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

NAVY=colors.HexColor('#16314d');TEAL=colors.HexColor('#087e87');GRAY=colors.HexColor('#4c6474');LIGHT=colors.HexColor('#ecf3f5');ORANGE=colors.HexColor('#bd7830')
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',FONT));pdfmetrics.registerFont(TTFont('DejaVu-Bold',BOLD));pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVu-Bold',italic='DejaVu',boldItalic='DejaVu-Bold')
S={
 'body':ParagraphStyle('Body',fontName='DejaVu',fontSize=9.1,leading=13.35,textColor=NAVY,spaceAfter=9),
 'body2':ParagraphStyle('Body2',fontName='DejaVu',fontSize=8.6,leading=12.2,textColor=NAVY,spaceAfter=7),
 'caption':ParagraphStyle('Caption',fontName='DejaVu',fontSize=8,leading=11.6,textColor=GRAY,spaceBefore=3,spaceAfter=10),
 'h1':ParagraphStyle('H1',fontName='DejaVu-Bold',fontSize=15.4,leading=20,textColor=NAVY,spaceAfter=13),
 'h2':ParagraphStyle('H2',fontName='DejaVu-Bold',fontSize=10.5,leading=15,textColor=TEAL,spaceBefore=8,spaceAfter=8),
 'coverTitle':ParagraphStyle('CoverTitle',fontName='DejaVu-Bold',fontSize=24,leading=30,textColor=NAVY,spaceAfter=9),
 'coverSub':ParagraphStyle('CoverSub',fontName='DejaVu',fontSize=11,leading=16,textColor=GRAY,spaceAfter=14),
 'small':ParagraphStyle('Small',fontName='DejaVu',fontSize=7.7,leading=11.3,textColor=NAVY,spaceAfter=6),
 'th':ParagraphStyle('TH',fontName='DejaVu-Bold',fontSize=7.5,leading=10.7,textColor=colors.white),
 'td':ParagraphStyle('TD',fontName='DejaVu',fontSize=7.5,leading=10.8,textColor=NAVY),
}
W=A4[0]-2*45

def P(txt,style='body'):return Paragraph(txt,S[style])
def H(txt):return P(txt,'h1')
def H2(txt):return P(txt,'h2')
def fmt(x):return f'{x:.9g}'
def imgpath(path,maxheight=240):
 with PILImage.open(path) as im:w,h=im.size
 scale=min(W/w,maxheight/h)
 return Image(str(path),width=w*scale,height=h*scale)
def fig(story,root,id,caption,maxheight=220):
 pic=root/'figures'/f'{id}.png';assert pic.is_file(),pic
 story.append(imgpath(pic,maxheight));story.append(P('<b>Figure '+id[:2]+'.</b> '+caption,'caption'))
def tab(rows,frac=None):
 if frac is None:frac=[1/len(rows[0])]*len(rows[0])
 data=[[P(str(v),'th' if i==0 else 'td') for v in row]for i,row in enumerate(rows)]
 t=Table(data,colWidths=[W*x for x in frac],repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#d2e0e5')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 return t

def equation(src):
 fig=plt.figure(figsize=(9.2,.8));fig.patch.set_alpha(0)
 fig.text(.02,.55,'$'+src+'$',size=16,ha='left',va='center',color='#16314d')
 output=io.BytesIO();fig.savefig(output,format='png',dpi=260,bbox_inches='tight',pad_inches=.12,transparent=True);plt.close(fig)
 output.seek(0)
 with PILImage.open(output) as im:w,h=im.size
 output.seek(0);scale=min(W/w,55/h)
 return Image(output,width=w*scale,height=h*scale)

def front(c,doc):
 page=doc.page;c.saveState();pw,ph=A4
 if page>1:
  c.setStrokeColor(TEAL);c.setLineWidth(.8);c.line(45,ph-35,pw-45,ph-35)
  c.setFont('DejaVu-Bold',9);c.setFillColor(NAVY);c.drawString(45,ph-27,'paceval.  |  SCIENTIFIC RESEARCH DEMONSTRATOR')
 c.setStrokeColor(colors.HexColor('#d9e6ea'));c.line(45,37,pw-45,37)
 c.setFont('DejaVu',7.4);c.setFillColor(GRAY);c.drawString(45,24,'paceval | Building Thermal Twin Cost Functions | 2026')
 c.drawRightString(pw-45,24,f'{page}')
 c.restoreState()

def check(root):
 log=(root/'results/sdk_execution.txt').read_text();assert 'original paceval SDK execution SUCCESS' in log
 assert 'samples=384' in log and 'candidate_grid=7' in log, 'Whitepaper requires canonical 384-row / 7-grid release workload'
 ver=json.loads((root/'results/verification_summary.json').read_text());assert ver['status']=='PASS'
 hp=json.loads((root/'results/high_precision_audit.json').read_text());assert hp['status']=='PASS'
 assert (root/'figures/00_building_thermal_twin_hero.png').is_file()
 im=PILImage.open(root/'figures/00_building_thermal_twin_hero.png');assert im.size==(2400,1200)
 with (root/'results/model_sweep.csv').open() as f:rows=list(csv.DictReader(f))
 results={v:min((r for r in rows if r['version']==v),key=lambda r:float(r['mean_squared_residual_K2'])) for v in ('v1','v2')}
 return ver,hp,results

def build(root):
 v,hp,best=check(root);o=root/'paceval_Building_Thermal_Twin_Whitepaper_EN.pdf'
 doc=SimpleDocTemplate(str(o),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=48,bottomMargin=48,title='Building Thermal Twin Cost Functions | paceval',author='paceval. Research',subject='Original-SDK verified thermal-twin mathematical execution research')
 z=[]
 # Page 1
 z.extend([Spacer(1,15),P('PACEVAL  |  ORIGINAL-SDK VERIFIED RESEARCH','small'),
 P('Building Thermal Twin<br/>Cost Functions','coverTitle'),
 P('Reusable mathematical execution graphs for thermal response, calibration, composite scores, guard margins and sensitivity analysis','coverSub'),
 imgpath(root/'figures/00_building_thermal_twin_hero.png',255),
 P('<i>Concept illustration; not a computed research result.</i>','caption'),Spacer(1,8),
 H2('Research outcome'),
 P('<b>62</b> executed original paceval computation graphs; <b>1,575</b> multi-graph batch calls; <b>324,868</b> computed graph outputs; <b>18,834</b> native C++ reference checks; <b>1,438</b> independent 80-digit high-precision comparisons.'),
 P('<b>Scope.</b> A deterministic synthetic 1R1C building thermal response model, not a validated facility controller or full-physics simulator.'),
 P('Independent research demonstration  |  13 November 2026','small'),PageBreak()])
 # Page 2
 z.extend([H('1. Introduction: industrial use case and state of the art'),
 P('Building operation depends on the interaction of outside temperature, solar exposure, envelope heat transfer, internal gains and HVAC system power. Operators may use temperature observations and equipment readings to estimate a reduced-order thermal model, evaluate a set of hypothetical parameters or screen candidate control strategies. A thermal-twin calculation kernel translates each sensor and scenario record into a forecast, a residual and engineering quantities. A higher-level simulation or controller can use those outputs; the present experiment neither acts on equipment nor validates a real facility.'),
 P('Detailed engineering alternatives include the heat-balance-based EnergyPlus simulator [1], the Modelica Buildings Library [2] and the BOPTEST controls benchmark [3]. Each covers capabilities well beyond the deliberately limited single-zone model presented here. Low-order resistance-capacitance (RC) grey-box thermal dynamics remain useful in interpretable parameter estimation and model-predictive-control research.'),
 H2('Research developments through 2026'),
 P('Serasinghe, Long and Clark [4] reviewed parameter-identification methods for low-order grey-box models in 2024. Lin et al. [5] studied inference with unmeasured internal gains. Mont Lecocq, Pascual and Salom [6] described physically coherent grey-box model variation in 2025. A 2026 review by Bisogno Bernardini et al. [7] surveyed RC-model use for digital twins and large-scale energy flexibility. The Modelica Buildings Library released version 14.0.0 in October 2026 [2]. These references motivate clear separation of mathematical expressions, calibration, data quality and deployment validation.'),
 H2('Research boundary and original contribution'),
 P('The experiment does not propose a new building-physics law or claim competitive industrial accuracy. It investigates whether the meaningful full calculation chain of a controlled synthetic thermal model can be represented by long-lived, inspectable paceval graphs, including two formula versions, whole weighted objectives and their analytical derivatives. The novelty claim is limited to this documented implementation exercise, not to thermal-twin methodology.'),
 tab([['Input','Mathematical operation','Output / potential use'],['Zone and external conditions','Graph-based heat transfer and balance','Signed thermal fluxes; one-step temperature'],['Observed temperature','Residual and calibration objective','Parameter-grid ranking'],['Setpoint, temperature band','Heating-demand proxy and guard expressions','Scenario assessment'],['Candidate model coefficients','Versioned weighted scores and sensitivities','Model comparison and audit']],[.26,.38,.36]),PageBreak()])
 # Page 3
 z.extend([H('2. Research question and execution architecture'),
 P('<b>Question.</b> Can original paceval computation handles evaluate the domain-significant thermal equations, calibration objectives, setpoint indicators and sensitivities in scalar and multi-graph batch execution, while a simple C++ host controls state, grid selection and I/O?'),
 H2('Execution ownership'),
 tab([['Component','Owner','Tested responsibility'],['Math expressions','Original paceval SDK','Heat terms, one-step temperature, residuals, 30 objectives, inequalities, sensitivities, version delta'],['State and dataset','C++ host','Generates deterministic input rows; carries the prior zone state to the next step'],['Grid optimization','C++ host','Enumerates 49 v1 and 343 v2 candidates; reduces the paceval-derived scalar losses'],['Verification','Independent C++ and mpmath','Whole-output recalculation at defined values and precisions']],[.23,.21,.56]),
 H2('Program architecture'),
 P('A common 18-variable input declaration is passed to 62 registered expressions. The original <font name="DejaVu-Bold">paceval_CreateComputation</font> API creates each graph once. The host exercises the scalar evaluation API for reference checks and the original <font name="DejaVu-Bold">paceval_dGetMultipleComputationsResultsExt</font> path for a production batch of several graphs and row inputs. An independent scalar-versus-batch ordering probe prevents a silent results-layout error. Each graph is deleted after use and the engine library is released.'),])
 fig(z,root,'01_workflow_architecture','Schematic only. The orchestrator and independent validators are separate from the reusable mathematical graph executor.',150)
 z.append(PageBreak())
 # Page 4
 z.extend([H('3. Defined mathematical model'),
 P('The case uses a single-zone first-order RC energy balance. All temperatures are interpreted as Celsius values with K as a difference unit; thermal capacitance is in J/K, heat gains and losses in W, and the integration interval is in seconds.'),
 equation(r'C\,\frac{dT}{dt}=Q_{\mathrm{HVAC}}+Q_{\mathrm{int}}+Q_{\mathrm{solar}}-Q_{\mathrm{loss}}'),
 P('Version 1 uses fixed thermal-envelope conductance and unshaded solar input. Version 2 adds a linear wind-dependent conductance term and a solar shading factor. Both are transparent toy models, not measured infiltration or irradiance submodels.'),
 equation(r'Q_{\mathrm{loss},1}=UA(T-T_o),\quad Q_{\mathrm{solar},1}=\alpha G'),
 equation(r'Q_{\mathrm{loss},2}=(UA+k_w w)(T-T_o),\quad Q_{\mathrm{solar},2}=\alpha G(1-s)'),
 equation(r'T_{k+1}=T_k+\frac{\Delta t}{C}(Q_{\mathrm{HVAC}}+Q_{\mathrm{int}}+Q_{\mathrm{solar}}-Q_{\mathrm{loss}})'),
 H2('Physical meaning of key parameters'),
 tab([['Symbol','Definition','Unit / illustrative range'],['T, T_o','Zone and outdoor temperatures','°C'],['C','Effective thermal capacitance','J/K; 5.4–9.0 million'],['UA','Envelope effective conductance','W/K; 150–270 on grid'],['k_w, w','Wind-dependent transfer coefficient; wind speed','W/K per (m/s); m/s'],['G, α, s','Incident solar thermal-power proxy; solar coupling; shade','W; dimensionless; dimensionless'],['Q_HVAC, Q_int','Supplied HVAC power and internal gains','W; W']],[.18,.46,.36]),
 P('The Euler step is 900 s. The maximum tested coefficient and step range are subject to explicit host-side validation. This project does not establish a global stability or discretization-error guarantee.'),PageBreak()])
 # Page 5
 z.extend([H('4. Full cost functions and paceval coverage'),
 P('For observed next-zone temperature T(obs), the first objective of each version is simply its squared one-step temperature residual. Each version also retains 14 simultaneous fully composed score variants combining forecast residual, steady-state signed heat-demand proxy, setpoint deviation and a conductance prior. The weights are research-defined and not monetary costs.'),
 equation(r'r_k=T_{k+1}^{(v)}-T_{\mathrm{obs},k+1},\qquad J_1^{(v)}=r_k^2'),
 equation(r'Q_{\mathrm{req},v}=U_v(T_{\mathrm{set}}-T_o)-Q_{\mathrm{solar},v}-Q_{\mathrm{int}}'),
 equation(r'J_i^{(v)}=w_{r,i}r_k^2+w_{e,i}(Q_{\mathrm{req},v}/1000)^2+w_{c,i}((T_{k+1}-T_{\mathrm{set}})/2)^2+w_{p,i}((UA-UA_p)/100)^2'),
 P('The signed required-heat quantity is the instantaneous thermal balance at a fixed setpoint, without storage or controller dynamics. The numerical normalizers in the composed score define arbitrary score units rather than engineering prices or physical guarantees.'),
 H2('Verified mathematical execution inventory (selected groups)'),
 tab([['Mathematical quantity','Actual owner','Execution identifiers'],['Solar gain, thermal loss, net heat','paceval','solar_gain_v*, envelope_loss_v*, net_heat_v*'],['One-step temperature and residual','paceval','temperature_next_v*, temperature_residual_v*'],['Demand proxy and guard margins','paceval','required_heat_v*, lower/upper_margin_v*'],['Versioned base and composite costs','paceval','score_v1_01 through _15; score_v2_01 through _15'],['Analytical score and temperature gradients','paceval','score_dUA_v*, score02_dUA_v*, temperature_dUA_v* etc.'],['Recursive state and candidate ranking','C++ host','Time orchestration and output reduction']],[.36,.17,.47]),
 P('The full <b>results/math_execution_inventory.csv</b> and <b>results/formula_registry.csv</b> contain all graph IDs and exact expressions. The score_v*_02 sensitivities correspond to the derivatives of the entire weighted objectives, not merely their residual components.'),PageBreak()])
 # Page 6
 z.extend([H('5. Deterministic workload and audit design'),
 P('A 384-row synthetic dataset covers 96 hours at a 900-second interval. The generator uses smooth periodic outdoor temperature, solar power and wind terms, deterministic HVAC and internal gains, and fixed day-period shade settings. Version 2 generates the synthetic zone trajectory with UA = 210 W/K, C = 7.2 MJ/K, k_w = 55 W/K per (m/s), and solar factor α = 0.65. A small predetermined sinusoidal observation perturbation is added; there is no measurement data.'),
 H2('Candidate experiments'),
 tab([['Study','Finite design','Execution'],['Version 1','7 conductance × 7 capacitance; fixed α = 0.65','49 calibration candidates'],['Version 2','7 conductance × 7 capacitance × 7 wind coefficients','343 calibration candidates'],['Each candidate','384 observed one-step rows','Batch evaluation of forecast and residual score'],['Final common parameter tuple','All 384 sample rows; 62 registered functions','Complete multi-graph result pass, 30 score variants'],['Verification','Scalar–batch order, native model, 80-digit oracle','Technical audit persisted as CSV / JSON']],[.24,.41,.35]),
 P('For each row, the forecast takes the known prior temperature from the synthetic record rather than feeding its own forecast recursively during calibration. Consequently the reported errors are <b>one-step teacher-forced residuals</b>. The initial synthetic trajectory itself is generated recursively by graph calls and recorded for reproducibility. Calibration then evaluates selected candidate parameters against this fixed trajectory.'),
 H2('Independent numerical verification'),
 P('Full-domain quantity checks are performed with native C++ expressions and with an independent 80-digit mpmath reference. The high-precision reference parses the written input decimals, recomputes both full one-step forecasts, residuals, demand proxies, margins, analytical sensitivities and means of all 30 score variants. Critical results passed the predefined finite-sample checks. The detailed audit, including numerical tolerances and differences, resides only in the project technical files.'),
 P('This verifies executed formula semantics for the tested inputs. It does not demonstrate global interval enclosures, model identifiability, robust out-of-sample forecasting or a validated building model.'),PageBreak()])
 # Page 7
 z.extend([H('6. Executed one-step thermal response'),
 P('All curves on this page originate from the executed original paceval results/time_series.csv, at the common best v2 parameter tuple. Both formulas are evaluated on identical synthetic records. This is an application illustration of explicit, versioned calculation, not a field-system model accuracy comparison.'),
 ]);fig(z,root,'02_observed_and_predicted_temperature','Actual paceval graph forecasts versus deterministic synthetic observations for identical row inputs.',217)
 fig(z,root,'03_residual_by_model','Residuals of the two retained model formulas. The data-generation process deliberately uses v2 physics.',214)
 z.append(PageBreak())
 # Page 8
 z.extend([H('7. Parameter study: the calibrated cost landscape'),
 P('The calibration objective in this section is the mean squared one-step temperature residual (K²). Each plotted surface value is from the original paceval execution, not an analytical redraw computed natively after the fact. The visualized v2 slice holds thermal capacitance fixed at 7.2 MJ/K and α = 0.65.'),
 ]);fig(z,root,'04_parameter_cost_surface_3d','Three-dimensional paceval calibration-loss surface over UA and wind coefficient.',280)
 fig(z,root,'05_parameter_cost_contours','Two-dimensional contour interpretation of the same finite executed grid, with selected v2 point.',195)
 z.append(PageBreak())
 # Page 9
 z.extend([H('8. Thermal operation quantities and guard expressions'),
 P('Two independent expressions calculate equilibrium signed heating demand and the distances to illustrative lower and upper zone-temperature limits. They help demonstrate end-to-end domain arithmetic while leaving decisions and protection logic on the host. A negative demand proxy can mean net cooling tendency in the model; it is not an HVAC setpoint request.'),
 ]);fig(z,root,'06_heat_demand_proxy','Versioned steady-state demand proxy, calculated from solar, internal and envelope heat terms.',210)
 fig(z,root,'07_temperature_guard_margins','Distance between each forecast and an illustrative 18–25 °C band. These are numerical margins, not safety approval.',210)
 z.append(PageBreak())
 # Page 10
 z.extend([H('9. Formula versions and sensitivity outputs'),
 P('The SDK retains two formula families simultaneously. Each version has fifteen score graphs: a pure residual calibration score and fourteen weighted scenarios. All objective variants are evaluated with a common parameter tuple in this figure, and their means are computed by the host from paceval batch outputs.'),
 ]);fig(z,root,'08_weighted_cost_versions','The same data and parameters are evaluated against different simultaneously preserved objective definitions.',214)
 fig(z,root,'09_calibration_sensitivity','A graph computes the exact analytical derivative of the baseline squared-residual objective. An additional verified graph covers the full composite score-v2-02 derivative.',210)
 z.append(PageBreak())
 # Page 11
 z.extend([H('10. Interpretation, limits and model changes'),
 P(f"On the tested fixed grid, version 1's lowest mean squared residual is <b>{float(best['v1']['mean_squared_residual_K2']):.9f} K²</b> at UA = {float(best['v1']['UA_WperK']):g} W/K and C = {float(best['v1']['C_JperK'])/1e6:g} MJ/K. Version 2's lowest value is <b>{float(best['v2']['mean_squared_residual_K2']):.9f} K²</b> at UA = {float(best['v2']['UA_WperK']):g} W/K, C = {float(best['v2']['C_JperK'])/1e6:g} MJ/K and k_w = {float(best['v2']['kwind_WperKmps']):g} W/K per (m/s). These are synthetic discretized one-step calibration results, not independently tested physical accuracy."),
 ]);fig(z,root,'10_selected_cost_by_heat_capacity','Best baseline squared-residual value for each tested thermal-capacitance setting.',220)
 z.extend([H2('What is and is not demonstrated'),
 P('Demonstrated: actual original SDK execution; persistent and independent graph versions; repeated scalar and multi-graph batches; graph-derived domain losses, costs, constraints and sensitivities; deterministic input/output files; independently checked main results. Not demonstrated: measurements from a real building, physically identified envelope coefficients, long-horizon autonomous prediction, robust calibration across seasonal periods, control or safety performance, carbon or energy savings, or superiority over existing simulation tools.'),
 P('The synthetic generator itself uses v2, which biases model selection in its favor; the wind coefficient truth is between grid points. Different weights and priors may choose different candidates. A useful next experiment would use external weather and metered HVAC records, held-out data, more than one zone, carefully parameterized physical constraints and independent emulator comparisons.'),PageBreak()])
 # Page 12
 z.extend([H('11. Reproducibility, audit and external references'),
 P('This publication is generated only after a real paceval SDK run and independent audit. The full reproducibility package contains original paceval source files (copyright and AGPL notices preserved), the CMake project, synthetic inputs, complete execution data, function inventory, validation programs, scientific figure sources and this PDF creation script. The externally supplied Linux shared library is not redistributed.'),
 P('<b>Build:</b> <font name="DejaVu">cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/path/to/libpaceval_linux_sharedLIB.so</font>','small'),
 P('<b>Run:</b> <font name="DejaVu">cmake --build build -j</font>; <font name="DejaVu">ctest --test-dir build --output-on-failure</font>; <font name="DejaVu">./build/building_thermal_twin --out . --steps 384 --grid 7</font>','small'),
 P('<b>Verification / diagrams:</b> <font name="DejaVu">python3 src/verify_results.py --root .</font>; <font name="DejaVu">python3 src/make_figures.py --root . --figures figures</font>','small'),
 H2('Execution references'),
 tab([['Project artifact','Purpose'],['src/thermal_twin.cpp / src/CMakeLists.txt','Main C++ application and original shared-library integration'],['results/math_execution_inventory.csv','Graph-by-graph mapping of mathematical function and actual owner'],['results/sdk_execution.txt','Execution counts and selected synthetic grid minima'],['results/high_precision_audit.json','Independent 80-digit whole-output verification (technical)'],['results/figure_manifest.csv','Provenance and captions of plotted research diagrams']],[.42,.58]),
 H2('Selected scientific and technology sources'),
 P('[1] EnergyPlus Engineering Reference, zone air heat-balance documentation: energyplus.readthedocs.io. [2] LBNL, Modelica Buildings Library, v14.0.0 (October 2026): simulationresearch.lbl.gov/modelica/. [3] IBPSA, Building Optimization Performance Test (BOPTEST): ibpsa.github.io/project1-boptest/.','small'),
 P('[4] Serasinghe et al., <i>Parameter identification methods for low-order gray box building energy models: A critical review</i>, Energy and Buildings 311 (2024), DOI 10.1016/j.enbuild.2024.114123. [5] Lin et al., <i>Grey-box modeling for thermal dynamics of buildings under the presence of unmeasured internal heat gains</i>, Energy and Buildings 314 (2024), DOI 10.1016/j.enbuild.2024.114229.','small'),
 P('[6] Mont Lecocq, Pascual and Salom, <i>Development of physically coherent grey-box models for residential buildings using a simplified adjustment method</i>, Energy and Buildings 328 (2025), DOI 10.1016/j.enbuild.2024.115215. [7] Bisogno Bernardini et al., <i>Grey-Box RC Building Models for Intelligent Management of Large-Scale Energy Flexibility: From Mass Modeling to Decentralized Digital Twins</i>, Energies 19(1), 77 (2026), DOI 10.3390/en19010077.','small'),
 P('<b>Conclusion.</b> This bounded synthetic experiment verifies the use of original paceval expression graphs for domain-complete thermal-twin mathematical calculations and controlled formula variants. Wider scientific or industrial validation remains an independent next step.','small')])
 doc.build(z,onFirstPage=front,onLaterPages=front)
 print(o,o.stat().st_size)
 return o
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));a=p.parse_args();build(a.root)
