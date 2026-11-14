#!/usr/bin/env python3
"""Create the English publication PDF from verified paceval result data.
Every chart image comes from results/ via make_figures.py; source is reproducible.
"""
from pathlib import Path
import json,csv,math,re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.utils import ImageReader
ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'paceval_Chemical_Reactor_Thermal_Stability_Whitepaper_EN.pdf'
fig=ROOT/'figures'
fonts='/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('DV',fonts+'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVB',fonts+'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DVM',fonts+'DejaVuSansMono.ttf'))
W,H=A4;MAR=46;CONT=W-2*MAR
NAVY=HexColor('#153249'); TEAL=HexColor('#08738b'); GOLD=HexColor('#e59546'); SLATE=HexColor('#384a57');GREY=HexColor('#667b88');PALE=HexColor('#edf5f7')
styles={
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.15,leading=15.2,textColor=SLATE,spaceAfter=0),
 'small':ParagraphStyle('small',fontName='DV',fontSize=8.0,leading=12.1,textColor=SLATE),
 'caption':ParagraphStyle('caption',fontName='DV',fontSize=7.7,leading=11,textColor=GREY),
 'head':ParagraphStyle('head',fontName='DVB',fontSize=12.0,leading=18,textColor=TEAL),
 'formula':ParagraphStyle('formula',fontName='DVM',fontSize=8.1,leading=13.7,textColor=NAVY),
 'table':ParagraphStyle('table',fontName='DV',fontSize=7.7,leading=11.2,textColor=SLATE),
}
C=canvas.Canvas(str(PDF),pagesize=A4,pageCompression=1)
C.setTitle('Chemical Reactor Thermal Stability Screening | paceval Research Whitepaper')
C.setAuthor('paceval Research Demonstrator')

class Page:
 def __init__(self,num,title,eyebrow='WP 04 | CHEMICAL PROCESS ENGINEERING'):
  self.num=num;self.y=H-92
  C.setFillColor(NAVY);C.rect(0,H-18,W,18,fill=1,stroke=0)
  C.setFillColor(TEAL);C.setFont('DVB',9);C.drawString(MAR,H-48,eyebrow)
  C.setFillColor(NAVY);C.setFont('DVB',17);C.drawString(MAR,H-76,title)
  C.setStrokeColor(HexColor('#c5dae1'));C.setLineWidth(.7);C.line(MAR,H-84,W-MAR,H-84)
  self.footer()
 def footer(self):
  C.setStrokeColor(HexColor('#c8dae1'));C.line(MAR,52,W-MAR,52)
  C.setFillColor(GREY);C.setFont('DV',7.5)
  C.drawString(MAR,36,'paceval. | Industrial research | Synthetic mathematical screening | 14 November 2026')
  C.drawRightString(W-MAR,36,f'WP 04  /  {self.num}')
 def block(self,text,kind='body',after=10):
  P=Paragraph(text,styles[kind]);w,h=P.wrap(CONT,1000)
  if self.y-h < 67:raise RuntimeError(f'Page {self.num} overflow while placing text: y={self.y}, h={h}')
  P.drawOn(C,MAR,self.y-h);self.y-=h+after
 def h(self,s,after=5):self.block(s,'head',after)
 def formula(self,s):
  text=s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
  P=Paragraph(text,styles['formula']);_,h=P.wrap(CONT-24,1000);boxh=h+22
  if self.y-boxh<67:raise RuntimeError(f'Page {self.num} formula overflow')
  C.setFillColor(PALE);C.roundRect(MAR,self.y-boxh,CONT,boxh,5,stroke=0,fill=1)
  P.drawOn(C,MAR+12,self.y-12-h);self.y-=boxh+11
 def table(self,data,widths=None,fs=7.65,after=12):
  rows=[[Paragraph(str(cell),styles['table']) for cell in row] for row in data]
  t=Table(rows,colWidths=widths or [CONT/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,0),.8,TEAL),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#ffffff'),HexColor('#f8fafb')]),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5)]))
  _,height=t.wrap(CONT,1000)
  if self.y-height<67:raise RuntimeError(f'Page {self.num} table overflow: need {height}, have {self.y}')
  t.drawOn(C,MAR,self.y-height);self.y-=height+after
 def image(self,file,caption,height=240):
  im=ImageReader(str(fig/file));iw,ih=im.getSize();w=min(CONT,height*iw/ih);h=w*ih/iw
  if h>height:h=height;w=h*iw/ih
  cp=Paragraph(caption,styles['caption']);_,ch=cp.wrap(CONT,500)
  if self.y-h-ch-12<67:raise RuntimeError(f'Page {self.num} image overflow {file}: at {self.y}, height {h}')
  C.drawImage(im,(W-w)/2,self.y-h,width=w,height=h,mask='auto')
  self.y-=h+5;cp.drawOn(C,MAR,self.y-ch);self.y-=ch+15
 def end(self):C.showPage()

def add_page(title):
 global count
 count+=1;return Page(count,title)

# COVER
count=1
C.setFillColor(NAVY);C.rect(0,0,W,H,fill=1,stroke=0)
C.setFillColor(TEAL);C.rect(0,H-26,W,26,fill=1,stroke=0)
C.setFillColor(HexColor('#84d8e5'));C.setFont('DVB',18);C.drawString(MAR,H-82,'paceval.  /  INDUSTRIAL RESEARCH')
C.setFillColor(HexColor('#ffffff'));C.setFont('DVB',27);C.drawString(MAR,H-145,'CHEMICAL REACTOR')
C.drawString(MAR,H-182,'THERMAL STABILITY')
C.drawString(MAR,H-219,'SCREENING')
C.setFillColor(HexColor('#cfe9f0'));C.setFont('DV',12);C.drawString(MAR,H-255,'Coupled kinetics, steady states and independent verification')
C.drawImage(ImageReader(str(fig/'00_chemical_reactor_hero.png')),MAR,H-570,width=CONT,height=CONT/2,mask='auto')
C.setFillColor(HexColor('#d4e8ef'));C.setFont('DV',8.5);C.drawString(MAR,H-592,'Concept illustration; not a computed research result.')
C.setStrokeColor(HexColor('#32798f'));C.line(MAR,155,W-MAR,155)
C.setFillColor(HexColor('#e6f3f6'));C.setFont('DV',10);C.drawString(MAR,121,'Reproducible Linux C++ demonstrator | Original paceval SDK 4.25')
C.drawString(MAR,100,'Two cooling models | Coupled Jacobian | Synthetic scenario study')
C.setFillColor(HexColor('#97bbc9'));C.setFont('DV',9);C.drawString(MAR,56,'Research report | 14 November 2026 | WP 04')
C.showPage()

# 02
p=add_page('Industrial use case and motivation')
p.h('Why thermal stability screening matters')
p.block('Exothermic chemical reactions produce heat. If chemical conversion accelerates with temperature, a jacketed reactor must remove heat while feed flow and reaction consume or replenish material. Engineers often assess candidate process conditions by combining kinetic laws with material and enthalpy balances. A zero heat-balance residual locates a mathematical operating point; it does not establish whether perturbations decay or grow.')
p.block('The continuous stirred-tank reactor (CSTR) used here is deliberately simple: one well-mixed liquid phase, one irreversible first-order reaction, a constant volume and fixed bulk density and heat capacity. This compact system nevertheless exhibits nonlinear steady states, distinct equilibrium branches and coupled concentration-temperature stability behavior. These established phenomena motivate a functionally comprehensive mathematical-engine demonstrator.')
p.h('Engineering context and current technologies')
p.block('Plant engineers use commercial process simulation and dynamic modeling tools such as Aspen Plus Dynamics and Siemens gPROMS Process, alongside open systems such as Cantera and DWSIM. These platforms span thermodynamic property estimation, transient simulation, process-model configuration and flowsheet integration. The present work is not a replacement for a flowsheet simulator. It focuses on executing reusable explicit mathematical kernels inside an independent C++ screening workflow.')
p.block('Recent thermal-stability literature places greater emphasis on experimental calorimetry, complex reaction networks and model-informed runaway assessment. A 2024 review discusses thermal stability and runaway mechanisms. A 2026 study combines experiments, mechanistic modeling and data-driven analysis for other reactor types; a separate 2026 paper considers tubular-reactor runaway detection. Neither makes this simplified CSTR a validated industrial safety model. Sources are listed on the final page.')
p.h('Concrete hypothetical workflow')
p.block('A process-design team enters a reaction parameter set, feed concentration, residence time, coolant temperature and effective heat-transfer parameter. A library of verified paceval graphs evaluates the differential-equation right-hand sides and Jacobian elements. The C++ host finds candidate equilibria; paceval computes trace, determinant, sensitivities and a mathematical screening score. The engineer uses those outputs to select additional experiments, physics-rich simulations and hazard-review cases, never to bypass required process safety evaluations.')
p.h('Research question')
p.block('<b>Can interdependent reactor mathematics, including nonlinear rates, model versions, explicit sensitivities and logical screening criteria, be evaluated on a real, repeatable paceval graph path while maintaining independent scientific verification?</b> The response is supported by actual recorded test outputs, not prospective performance claims.')
p.end()

# 03
p=add_page('Reactor model and physical units')
p.h('Reaction rate and coupled state equations')
p.block('Let C be reactant concentration (mol/m³), T be reactor temperature (K), tau be residence time (s), and Rg be the gas constant (J/mol/K). Positive H denotes exothermic heat release in J/mol. The temperature-dependent kinetic coefficient is specified at an explicit reference temperature, avoiding an unnecessarily large Arrhenius prefactor.')
p.formula('k(T) = kref × exp[(-Ea/Rg) × (1/T - 1/Tref)] ;  r(T,C) = k(T) × C')
p.formula('dC/dt = (Cin - C)/tau - k(T) × C')
p.formula('dT/dt = (Tin - T)/tau + (H/rhoCp) × k(T) × C - [UAeff(T)/(rhoCp × V)] × (T - Tc)')
p.block('Here rhoCp is volumetric heat capacity (J/m³/K), V is liquid volume (m³), and UA is heat-transfer conductance (W/K). Concentration and thermal dynamics share the same kinetic rate, making a one-dimensional fixed-concentration slope test insufficient for equilibrium stability.')
p.h('Two simultaneous model versions')
p.formula('V1 : UAeff(T) = UA     ;     V2 : UAeff(T) = UA × [1 + alpha × (T - Tref)]')
p.block('V1 assumes a constant effective heat-transfer coefficient. V2 introduces a hypothetical linear dependence as a sensitivity scenario, not a measured correlation. The tested domain restricts temperatures and alpha so that UAeff stays positive. Each version is represented by its own persistent paceval graph set.')
p.h('Reduced equilibrium construction')
p.formula('Ceq(T) = Cin / [1 + tau × k(T)]   ;   F(T) = (dT/dt) evaluated at (T, Ceq(T))')
p.block('The host searches for sign changes in F(T) over a finite predefined interval and refines each bracket using bisection. The resulting concentration comes from the separately evaluated paceval graph Ceq. Both original differential-equation residuals are then re-evaluated at the final candidate to check the coupled equilibrium.')
p.h('Idealizations that remain explicit')
p.block('This is a first-order, constant-property, single-phase liquid model. It excludes pressure coupling, multi-step chemistry, heat of mixing, transport gradients, vaporization, decomposition, jacket fluid dynamics, reactor wall inertia and relief systems. The illustrative temperature screening limit is not a measured or permitted operating limit.')
p.end()

# 04
p=add_page('Coupled stability, scores and sensitivities')
p.h('The full two-state Jacobian')
p.block('At each stationary candidate, the model is linearized in the two state variables C and T. The matrix J contains four partial derivatives evaluated analytically, including the kinetic temperature derivative dk/dT = k × Ea/(Rg × T²). The temperature Jacobian J22 accounts for the extra V2 cooling-coefficient derivative.')
p.formula('J = [[ ∂(dC/dt)/∂C,   ∂(dC/dt)/∂T ], [ ∂(dT/dt)/∂C,   ∂(dT/dt)/∂T ]]')
p.formula('trace(J) = J11 + J22     ;     det(J) = J11 × J22 - J12 × J21')
p.block('Strictly negative trace and strictly positive determinant are necessary and sufficient for local asymptotic stability of a continuous two-state linearized system. The leading real eigenvalue component is derived from trace and determinant, with a zero-clamped discriminant only for taking the real part of a complex-conjugate eigenvalue pair.')
p.h('Screening margins and decision separation')
p.formula('g = min[ (Tlim - T)/(Tlim - Tin),  -tau × trace(J),  tau² × det(J) ]')
p.block('The reported score g is dimensionless. Its sign indicates whether three mathematical conditions are simultaneously strict, not whether the physical reactor is safe. A separate paceval logical graph checks trace &lt; 0, determinant &gt; 0, T ≤ Tlim and 0 ≤ C ≤ Cin. The host labels the output as mathematical screening only. The direction and inclusivity of each inequality are explicit.')
p.h('What is actually evaluated in paceval?')
p.table([
 ['Function group','Execution engine','Graph IDs'],
 ['Kinetics, heat production and feed duty','paceval','K_RATE, REACTION_RATE, Q_GEN, Q_FLOW'],
 ['Species and energy differential equations','paceval','F_C, V1_F_T, V2_F_T'],
 ['Reduced stationary equation, temperature conversion','paceval','C_EQ, V1_F_RED, V2_F_RED'],
 ['Complete Jacobian and eigen diagnostics','paceval','J11/J12/J21, V1_J22/V2_J22, J_TRACE/J_DET/EIG_MAX_RE'],
 ['Model comparison, cooling sensitivities, guards','paceval','DELTA_REM/DELTA_FRED, V1/V2_D_T_D_*, SCREEN_SCORE/GUARD'],
 ['Root bracketing and time integration','C++ host','Bisection and RK4 use paceval RHS graphs']
 ],[CONT*.38,CONT*.15,CONT*.47]);
p.end()

# 05
p=add_page('Deterministic numerical study')
p.h('Inputs and calculation domain')
p.block('The experiment varies two axes, coolant temperature and the nominal jacket heat-transfer conductance, over a deterministic 9 × 9 grid. Every scenario is evaluated under both model versions. One fixed reference scenario (S04_04) is used for detailed profiles, state-plane visualization and transient initial-value demonstrations. All input quantities and parameter values are synthetic research assumptions.')
p.table([
 ['Parameter','Synthetic baseline','Units'],
 ['Reactor volume V; volumetric heat capacity rhoCp','2; 4,000,000','m³; J/(m³ K)'],
 ['Feed temperature Tin; reference Tref','300; 340','K'],
 ['Feed concentration Cin; residence time tau','3,000; 150','mol/m³; s'],
 ['Exothermic heat H; activation energy Ea','100,000; 80,000','J/mol; J/mol'],
 ['Rate kref; base coolant temperature Tc','0.02; 295','1/s; K'],
 ['Base UA; temperature cooling slope alpha','16,000; 0.002','W/K; 1/K'],
 ['Illustrative temperature screening threshold','345','K'],
 ['Bounded root search','276 through 410','K'],
 ],[CONT*.47,CONT*.30,CONT*.23])
p.h('Numerical execution sequence')
p.block('The application validates input schemas and finite domains before passing values to paceval. Numeric CSV fields use the official paceval string-to-double converter only after strict literal validation. Persistent graphs are created once for each formula version; multi-graph batches evaluate independent temperature scans and phase-plane grids. A C++ bisection solver refines sign-change brackets. paceval then evaluates the complete concentration-temperature equilibrium and Jacobian. Additional profiles and RK4 transients reuse the same handles.')
p.h('Independent validation design')
p.block('The program contains an independently written native C++ model for a bounded suite of reference checks. A separate Python implementation uses mpmath at 85-decimal-digit precision for the recorded equilibrium and profile quantities. Scalar and multi-graph input/output layout, SDK operator semantics, CSV parse/rejection rules, and three-equilibrium regression behavior are each checked separately. Exact technical audit data are provided in the ZIP, not displayed as engine comparison tables in this publication.')
p.end()

# 06
p=add_page('Thermal balance and stationary states')
p.block('The recorded baseline graph outputs show multiple sign changes in the reduced energy residual. The horizontal zero is the stationary-energy condition. Every marked crossing has also been checked against the full two-state balance, rather than accepted from a heat-only curve.',after=12)
p.image('fig01_thermal_residual.png','Figure 1. Actual paceval-reported energy residuals for the same synthetic operating case under V1 and V2. Markers identify bracketed stationary candidates.',height=227)
p.image('fig02_energy_components.png','Figure 2. Reaction heat generation, cooling-jacket duty and net reaction plus incoming sensible enthalpy contribution. Values are derived from actual executed paceval output fields.',height=227)
p.end()

# 07
p=add_page('Multiplicity across operating conditions')
p.block('The synthetic scenario grid reveals regions with one or three equilibria within the prescribed temperature bracket. The branch classification is calculated using the coupled Jacobian, rather than a slope of the isolated heat-generation curve.',after=9)
p.image('fig03_equilibrium_branches.png','Figure 3. Stable and unstable candidate temperatures across coolant settings at fixed nominal UA. Both concurrently executed formula versions are shown.',height=231)
p.image('fig04_multiplicity_maps.png','Figure 4. Counts of bracketed steady states within the explicitly bounded temperature scan. The plotted values do not constitute a complete global bifurcation diagram.',height=227)
p.end()

# 08
p=add_page('Coupled dynamics and state trajectories')
p.block('A full two-state vector field is created by paceval multi-graph evaluation of concentration and temperature derivatives. The numerical time integrator remains an explicitly identified host component and invokes the original paceval RHS graphs for every RK4 stage.',after=9)
p.image('fig05_phase_plane.png','Figure 5. Coupled state-space directions for V1 from the genuine paceval right-hand-side field. Arrow magnitudes are normalized for visualization; the symbols mark the baseline equilibria.',height=234)
p.image('fig06_transients.png','Figure 6. Three illustrative state trajectories from synthetic initial conditions, with host RK4 stepping and genuine paceval evaluation of each species and energy derivative.',height=225)
p.end()

# 09
p=add_page('Sensitivities and versioned envelopes')
p.block('The two cooling law versions remain independently callable as persistent execution graphs. The sensitivity functions displayed below are explicit analytic formulas executed by paceval, not a claim of automatic differentiation of arbitrary program code.',after=9)
p.image('fig07_sensitivity.png','Figure 7. Graph-evaluated partial derivatives of the temperature RHS with respect to nominal UA and coolant temperature, sampled at common temperature points.',height=233)
p.image('fig08_stable_equilibrium_surface.png','Figure 8. Lowest locally stable equilibrium for each scenario in V1. The visible change in surface level illustrates selection between different available branches, not a continuously differentiable low branch everywhere.',height=225)
p.end()

# 10
p=add_page('Screening outcomes and Jacobian criteria')
p.block('An illustrative thermal cutoff and the two continuous-time Jacobian conditions are assembled into a domain score and an explicit relational/logical graph. Positive signs are interpretable only in the model and are not authorization to operate a chemical process.',after=11)
p.image('fig09_screening_score.png','Figure 9. Dimensionless screening margin at all found equilibrium candidates. Dashed red line marks an invented 345 K scenario threshold, not a site-approved operating limit.',height=228)
p.image('fig10_jacobian_stability.png','Figure 10. Trace and determinant classification across the recorded stationary solutions. These are the actual coupled two-state linear stability quantities.',height=230)
p.end()

# 11
p=add_page('Executed research findings and independent audit')
p.h('What was actually measured in the functional experiment?')
ev=json.loads((ROOT/'results/execution_evidence.json').read_text())['main_run']
sumrows=list(csv.DictReader((ROOT/'results/scenario_surface.csv').open()))
counts={}
for v in ('1','2'):
 entries=[z for z in sumrows if z['model']==v]
 counts[v]={'three':sum(int(x['root_count'])==3 for x in entries),'one':sum(int(x['root_count'])==1 for x in entries),'stable':sum(int(x['stable_count']) for x in entries),'below':sum(int(x['stable_below_limit_count']) for x in entries)}
p.table([
 ['Executed evidence item','Actually recorded result'],
 ['Independent synthetic scenarios and model-scenario combinations',f'{ev["scenario_count"]} and {ev["model_scenario_count"]}'],
 ['Unique domain execution graphs created and run',str(ev['unique_domain_graphs_executed'])],
 ['Distinct stationary-state records',str(ev['equilibrium_roots'])],
 ['One-root / three-root scenarios under V1',f'{counts["1"]["one"]} / {counts["1"]["three"]}'],
 ['One-root / three-root scenarios under V2',f'{counts["2"]["one"]} / {counts["2"]["three"]}'],
 ['Stable equilibrium records (V1 / V2)',f'{counts["1"]["stable"]} / {counts["2"]["stable"]}'],
 ['Stable and below hypothetical 345 K limit (V1 / V2)',f'{counts["1"]["below"]} / {counts["2"]["below"]}'],
 ['Separate native C++ analytic checks',str(ev['native_reference_checks'])],
 ],[CONT*.66,CONT*.34])
p.h('Baseline mathematical interpretation')
p.block('Scenario S04_04 admits three equilibria under each model version. For V1 the temperatures are approximately 304.713, 325.963 and 347.979 K; the low and high branches meet the coupled local linear-stability conditions, while the middle branch has an unstable Jacobian. The high-temperature stable root still violates the invented 345 K illustrative screening limit. These are mathematical model outputs, not measured physical behavior.')
p.h('Independent verification outcome')
audit=json.loads((ROOT/'results/scientific_audit.json').read_text())
p.block(f'The execution was evaluated against separately derived native C++ model functions and an 85-decimal-place mpmath implementation. The high-precision audit checked {audit["root_records_checked"]} recorded equilibrium rows and {audit["profile_rows_checked"]} profile rows and reported {audit["failure_count"]} failed criteria. Detailed differences and explicit tolerances remain in the machine-readable technical audit files; no comparative engine-accuracy table is published here.')
p.h('Scientific limits')
p.block('Finite root scanning can miss tangential or tightly clustered solutions; no global root-completeness proof is asserted. Local asymptotic stability cannot establish global attraction, transient upset safety, protective-system adequacy or safe operating limits. Parameter identification, calorimetry, uncertainty propagation, multimode physics and safety assessments are independent prerequisites for real reactor decisions.')
p.end()

# 12
p=add_page('Reproducibility, sources and conclusions')
p.h('Source files and reproduction')
p.block('The repository includes the original SDK 4.25 interface files, CMake build, complete C++ demonstrator, deterministic input generator, scenario CSV, genuine paceval result CSVs, separate mpmath reference and plotting/PDF scripts. Provide an appropriately licensed compatible libpaceval_linux_sharedLIB.so and build with cmake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/library.so, then run ctest --test-dir build --output-on-failure, followed by the main executable and the independent validation scripts.')
p.block('The external compiled runtime is deliberately excluded from the GitHub archive. The SDK source retains original license and copyright headers. Tests use Linux x86-64 and do not assert independent hardware, regulatory or industrial certification. No performance, energy or commercial speed comparison has been carried out as part of this functionality-oriented study.')
p.h('Selected scientific and industrial sources')
references=[
 ('Michigan Technological University, 2017','CSTR dynamic-model lecture notes','https://pages.mtu.edu/~tbco/cm416/lecture_22_2017.pdf'),
 ('Belfiore, Wiley, 2003','Multiple stationary states in continuous stirred tank reactors','ISBN 9780471202752'),
 ('Canadian Journal of Chemical Engineering, 2024','Evaluating thermal stability of chemicals and systems: a review','https://doi.org/10.1002/cjce.25422'),
 ('Industrial & Engineering Chemistry Research, 2026','Thermal Runaway of Chemical Reactors: experimental/modeling/data-driven study','https://pubs.acs.org/iecred/article/65/4/2057/5072740/'),
 ('Chemical Engineering Transactions, 2026','A refined divergence-based runaway detection criterion for tubular reactors','https://doi.org/10.3303/CET26126040'),
 ('Cantera official documentation','Reactors and reactor networks','https://cantera.org/stable/reference/reactors/index.html'),
 ('Siemens official documentation','gPROMS Process','https://www.siemens.com/de-de/products/gproms/process/'),
 ('AspenTech official documentation','Aspen Plus Dynamics','https://www.aspentech.com/en/products/engineering/aspen-plus-dynamics'),
 ('DWSIM official documentation','CSTR software reference','https://dwsim.org/help/api/reactors/cstr.html'),
 ('OSHA','Chemical reactivity hazards and process safety management','https://www.osha.gov/chemical-reactivity'),
 ('paceval official documentation','API version 4.25','https://paceval.com/api/')]
for who,what,url in references:
 p.block(f'<b>{who}</b>. {what}. <font color="#08738b">{url}</font>','small',after=3)
p.h('Concluding result')
p.block('The verified experiment demonstrates that reusable original paceval execution graphs can supply a coherent chemical-reactor screening kernel, including full coupled Jacobian tests, formula versioning, derivative and score functions, and repeated scalar and multi-graph evaluation. The model is independently checked, reproducible and mathematically useful as a research demonstration, while its industrial domain validity and process safety remain explicitly outside the evidence presented.')
p.end()

C.save()
print('Wrote whitepaper:',PDF)
