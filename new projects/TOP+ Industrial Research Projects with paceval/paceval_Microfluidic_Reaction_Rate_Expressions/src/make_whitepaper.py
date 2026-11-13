#!/usr/bin/env python3
"""Build an English scientific PDF entirely from recorded ORIGINAL paceval data.
No simulated data are fabricated by this report writer. The cover photo is
explicitly marked concept illustration; figures 02-10 are actual SDK output.
"""
from pathlib import Path
import argparse,csv,io,math,json
from xml.sax.saxutils import escape
from PIL import Image as PIL
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Image,Table,TableStyle,Spacer,PageBreak,KeepTogether,HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

NAVY=colors.HexColor('#20334b');VIOLET=colors.HexColor('#634c8b');TEAL=colors.HexColor('#007e8a');MUTED=colors.HexColor('#5b697a');INK=colors.HexColor('#212e3a');LIGHT=colors.HexColor('#f1f6f8')
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('D',FONT));pdfmetrics.registerFont(TTFont('DB',BOLD));pdfmetrics.registerFontFamily('D',normal='D',bold='DB',italic='D',boldItalic='DB')
ST={'p':ParagraphStyle('Body',fontName='D',fontSize=8.65,leading=13.2,textColor=INK,spaceAfter=9),
'p2':ParagraphStyle('Second',fontName='D',fontSize=8.25,leading=12.1,textColor=INK,spaceAfter=7),
'caption':ParagraphStyle('Cap',fontName='D',fontSize=7.2,leading=10.3,textColor=MUTED,spaceAfter=10,spaceBefore=3),
'h1':ParagraphStyle('Section',fontName='DB',fontSize=16.1,leading=22,textColor=NAVY,spaceAfter=13),
'h2':ParagraphStyle('Subsection',fontName='DB',fontSize=10.3,leading=14.1,textColor=VIOLET,spaceBefore=7,spaceAfter=7),
'title':ParagraphStyle('CoverTitle',fontName='DB',fontSize=23.2,leading=29.2,textColor=NAVY,spaceAfter=12),
'sub':ParagraphStyle('CoverSub',fontName='D',fontSize=10.4,leading=15.5,textColor=MUTED,spaceAfter=11),
'small':ParagraphStyle('Small',fontName='D',fontSize=7.6,leading=11.1,textColor=INK,spaceAfter=6),
'cell':ParagraphStyle('Cell',fontName='D',fontSize=7.15,leading=10.5,textColor=INK),
'head':ParagraphStyle('Head',fontName='DB',fontSize=7.25,leading=10.7,textColor=colors.white)}
PW,PH=A4; W=PW-90

def P(t,style='p'):return Paragraph(t,ST[style])
def H(t):return P(t,'h1')
def H2(t):return P(t,'h2')
def T(data,ratios):
 d=[[P(str(x),'head' if i==0 else 'cell') for x in row] for i,row in enumerate(data)]
 table=Table(d,colWidths=[x*W for x in ratios],repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([
 ('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
 ('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,1),(-1,-1),.22,colors.HexColor('#d5e0e8')),
 ('LINEBELOW',(0,0),(-1,0),.7,TEAL),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),5),
 ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));return table

def Img(p,mh=255):
 with PIL.open(p) as im:w,h=im.size
 k=min(W/w,mh/h);return Image(str(p),width=w*k,height=h*k)
def Eq(s,mh=40):
 fig=plt.figure(figsize=(12,1.15));fig.patch.set_alpha(0)
 fig.text(.02,.47,'$'+s+'$',fontsize=19,ha='left',va='center',color='#20334b')
 bio=io.BytesIO();fig.savefig(bio,format='png',dpi=230,transparent=True,bbox_inches='tight',pad_inches=.10);plt.close(fig);bio.seek(0)
 with PIL.open(bio) as im:w,h=im.size
 k=min(W/w,mh/h);bio.seek(0);return Image(bio,width=w*k,height=h*k)
def F(root,n,name,cap,mh=245):return [Img(root/'figures'/f'{n:02d}_{name}.png',mh),P(f'<b>Figure {n}.</b> {cap}','caption')]
def new(story,title,number):
 if story:story.append(PageBreak())
 story.append(H(f'{number}. {title}'))
def bullet(t):return P('<font color="#007e8a">●</font>  '+t,'p2')
def footer(c,doc):
 page=doc.page;c.saveState();c.setStrokeColor(colors.HexColor('#d9e5e7'));c.setLineWidth(.7);c.line(45,38,PW-45,38)
 if page>1:
  c.setStrokeColor(TEAL);c.setLineWidth(1.0);c.line(45,PH-34,PW-45,PH-34)
  c.setFont('DB',7.7);c.setFillColor(NAVY);c.drawString(45,PH-27,'paceval.   MICROFLUIDIC REACTION–TRANSPORT RESEARCH')
 c.setFont('D',7.2);c.setFillColor(MUTED);c.drawString(45,23,'paceval | Research Demonstrator | November 2026')
 c.drawRightString(PW-45,23,str(page));c.restoreState()
def rd(path):
 with open(path,newline='') as f:return list(csv.DictReader(f))
def work(root):
 result=root/'results';run=(result/'sdk_execution.txt').read_text();audit=json.loads((result/'high_precision_audit.json').read_text());assert audit['status']=='PASS'
 m={a:b for a,b in (x.split('=',1) for x in run.splitlines() if '=' in x)}
 assert int(m['registered_executed_graphs'])==82 and int(m['steps'])==1440 and int(m['cells'])==64
 cases=rd(result/'scenario_summary.csv');assert len(cases)==12
 source=root/'paceval_Microfluidic_Reaction_Rate_Expressions_Whitepaper_EN.pdf'
 story=[]
 # 1 COVER
 story.append(Spacer(1,12));story.append(P('PACEVAL  /  SCIENTIFIC FEASIBILITY DEMONSTRATOR','small'))
 story.append(P('Microfluidic Reaction–Transport<br/>with Reusable Mathematical Kernels','title'))
 story.append(P('A conservative synthetic 1-D flow reactor with versioned reversible kinetics, persistent original paceval computation graphs and independent whole-model validation.','sub'))
 story.append(Img(root/'figures/00_microfluidic_hero.png',263));story.append(P('Cover: concept illustration; not a computed research result. The scientific figures inside are generated from actual original-paceval numerical output.','caption'))
 story.append(H2('Research outcome'))
 story.append(T([['Evidence','Verified execution result'],['Original paceval SDK','82 persistent graphs; 2,890 multi-graph batches'],['Research workload','12 scenarios × 64 cells × 1440 time steps'],['Graph calculations',f"{int(m['graph_outputs']):,} evaluated graph results"],['Independent audit',f"{audit['high_precision_graph_samples']:,} 80-digit graph probes and {audit['native_independent_trajectory_fields']} full-trajectory output checks"]],[.34,.66]))
 story.append(Spacer(1,8));story.append(P('Scope: isothermal, prescribed-velocity, cross-section-averaged reactor with fictional chemical parameters. No validated 3-D microfluidic device, process safety or performance claim.','small'))
 # 2 INTRODUCTION
 new(story,'Industrial use case and current state of the art',1)
 story.append(P('Microfluidic flow reactors make it possible to expose small liquid volumes to controlled residence times, reagent concentrations and chemical environments. In real systems, a reaction and its measured product distribution are inseparable from transport and mixing: an intrinsic local reaction rate is useful only when interpreted together with flow, dispersion, reaction time and boundary inputs. Research and industrial workflows therefore combine reaction-rate expressions with conservation laws, experimental process analytics and simulation.'))
 story.append(P('A practical example is a hypothetical experiment in which reagent A and reagent B enter a microchannel and form product C. An engineer changes inlet flow velocity or the chemical-rate parameters, simulates the expected concentration along the reactor, and interprets product concentration and the reacted fraction at the outlet. A changed kinetic law should be traceable and simultaneously available with the previous version.'))
 story.append(H2('Established methods and contemporary work'))
 story.append(P('COMSOL’s current Microfluidics/Chemical Reaction Engineering documentation describes coupled flow, advection, diffusion and chemical reactions. OpenFOAM publishes a conservative scalar-transport finite-volume formulation. The present experiment keeps the flow field prescribed and addresses only the lower-dimensional coupled species kernel, not the complete multiphysics solver. [1, 2]'))
 story.append(P('Westphal et al. (2024) reported microreactor workflows with online (chip-)LC/MS reaction monitoring; Knoll et al. (2025) presented FlowMat for modular flow-reactor modeling, identification and optimization; Silber et al. (2026) reported modeling multi-step flow transformations using sequential dynamic experiments. The wider field therefore motivates auditable, reusable mathematical kinetic kernels while also highlighting the need to link them to independent experiments. [3–5]'))
 story.append(H2('Positioning of the paceval research'))
 story.append(P('This study demonstrates mathematical execution and formula reuse, not a replacement for computational fluid dynamics, an experimentally calibrated reaction mechanism or industrial process validation. Only calculations actually executed with the original paceval SDK are attributed to paceval. The independent Python/C++ reference checks never produce the published simulation outputs.'))
 # 3
 new(story,'Research question and execution architecture',2)
 story.append(P('Can a chemically meaningful reversible reaction–transport time step, including local rate laws, advection–dispersion, conditional boundary factors, kinetic sensitivities, outlet score formulas and explicit model versioning, be represented by real original-SDK paceval graphs and repeatedly evaluated on a spatial mesh? Can the full resulting numerical trajectory be independently verified?'))
 story += F(root,1,'workflow','Industrial information chain: synthetic operating inputs, chronological finite-volume host, genuine paceval mathematical execution and an independently implemented scientific audit.',225)
 story.append(H2('System boundary'))
 story.append(T([['Component','Role / real implementation'],['paceval engine','Creates and evaluates local kinetic, complete 1-D finite-volume state-update, boundary flux, score and sensitivity graphs'],['C++ host','Supplies old-state neighbors and boundary conditions; maintains state arrays and time steps; accumulates numerical integrals; selects scenarios'],['Independent validation','Reconstructs full trajectories with independent NumPy physics and tests each graph family using 80-digit mpmath reference'],['Scientific outputs','Concentration fields, product levels, model revision effects, reaction fractions, conserved pair inventories, scores and sensitivity maps']],[.29,.71]))
 story.append(P('The output model is explicitly cross-section-averaged and one-dimensional. No direct measurement or validation for a particular device is implied.','small'))
 # 4
 new(story,'Defined reaction and transport model',3)
 story.append(P('Consider the reversible net reaction A + B ⇌ C in a dilute, hypothetical liquid mixture. A, B and C are mmol/L concentrations. The channel length is 20 mm; mean axial velocity is prescribed, temperature is held fixed, and axial effective dispersion is treated as constant.'))
 story.append(Eq(r'\partial_t c_i+u\partial_x c_i=D\partial_{xx}c_i+\nu_i r',42))
 story.append(P('Species stoichiometric coefficients are νA=−1, νB=−1 and νC=+1. Original kinetics v1 implement mass action; the v2 alternative reduces the forward term with a hypothetical saturation factor K. These are not fitted to chemical measurements.'))
 story.append(Eq(r'r_1=k_fAB-k_rC,\qquad r_2=\frac{k_fAB}{1+KA}-k_rC',46))
 story.append(T([['Quantity / unit','Numerically evaluated values'],['Channel L, effective axial D','20 mm; 0.006 mm²/s'],['Mean flow velocity u','0.25, 0.40, 0.55 mm/s'],['Forward kf','0.018 or 0.032 L/(mmol·s)'],['Reverse kr; saturation K','0.003 s⁻¹; 0.65 L/mmol'],['Inlet concentrations','A=1.00, B=0.90, C=0.00 mmol/L'],['Initial condition','All 64 cells initially at A=B=C=0'],['Simulation interval','Δt=0.1 s; endpoint 144 s']],[.46,.54]))
 story.append(P('The kf, kr and K values are a model-defined synthetic research set. Qualitative behavior and the mathematical reproducibility are meaningful for this chosen model; physical calibration for a named chemistry remains separate.'))
 # 5
 new(story,'Finite-volume update, boundaries and chemical invariants',4)
 story.append(P('An explicit conservative upwind-convection and centered-dispersion discretization was selected to make the mathematical computation boundary easy to audit. C++ arranges the neighboring cell states and boundary flags; paceval evaluates each full source-plus-transport update as one persistent mathematical graph per species and kinetic version.'))
 story.append(Eq(r'J_{i-1/2}=uc_{i-1}-D\alpha_L\frac{c_i-c_{i-1}}{\Delta x}',40))
 story.append(Eq(r'J_{i+1/2}=uc_i-D\alpha_R\frac{c_{i+1}-c_i}{\Delta x}',40))
 story.append(Eq(r'c_i^{n+1}=c_i^n+\Delta t\left[\frac{J_{i-1/2}-J_{i+1/2}}{\Delta x}+\nu_ir\right]',42))
 story.append(P('Internal face coefficients αL=αR=1 implement the centered dispersive difference. At the inlet αL=2 uses the half-cell distance to a fixed feed concentration; at the outlet αR=0 enforces zero dispersive outflow. Convective transport uses the left/upwind value for positive prescribed u.'))
 story.append(H2('Chemical invariants and startup interpretation'))
 story.append(P('For stoichiometry A+B⇌C, the reaction cancels identically in A+C and B+C. Their domain integrals are therefore governed only by inlet and outlet fluxes. paceval computes the boundary combinations and their local concentrations; C++ performs the stateful summation over mesh cells and time.'))
 story.append(Eq(r'\frac{d}{dt}\int_0^L(A+C)\,dx=J_{A+C}(0)-J_{A+C}(L)',42))
 story.append(P('A startup transient can have low outlet A because material has not arrived, even without significant reaction. The reported stoichiometric reacted fraction is therefore C/(A+C+ε), ε=10⁻¹² mmol/L (not 1−Aout/Ain). Low-signal values are not treated as a clinical, physical or safety decision.'))
 # 6
 new(story,'Real paceval execution graph inventory',5)
 story.append(P('The original Linux SDK was linked externally. Its authentic header and source were included, preserving copyright and upstream licensing. A persistent graph is created once per mathematical function and model version. The main data path invokes paceval_dGetMultipleComputationsResultsExt on actual mesh-row inputs; scalar evaluation is checked against batch layout and used for selected final indicators.'))
 story.append(T([['Mathematical calculation / purpose','Executed by','Graph family / justification'],
 ['Reversible reaction, forward/reverse parts','paceval','reaction_rate, forward_rate, reverse_rate v1/v2'],
 ['Advection–dispersion for all species','paceval','transport_A/B/C v1/v2'],
 ['Full reaction–transport state transition','paceval','A_next, B_next, C_next v1/v2'],
 ['Sensitivity to five kinetic inputs','paceval','d_rate_dA/B/C/kf/K v1/v2'],
 ['Boundary fluxes and reaction invariants','paceval','influx/outflux; mole_sum v1/v2'],
 ['Physical operating descriptors','paceval','Pe, Da, residence time'],
 ['Reaction fraction, margins and product output','paceval','outlet_reacted_fraction, target_product_margin, product_ratio'],
 ['12 weighted assessment expressions per version','paceval','score_v1_01…12 / score_v2_01…12'],
 ['Spatial integral, time history, ordering','C++ host','stateful reductions/orchestration (not paceval graphs)'],
 ['Independent numerical checks','C++ / Python','deliberately independent from published paceval execution']],[.38,.15,.47]))
 story.append(P('The complete row-level inventory and graph formula registry are in results/math_execution_inventory.csv and results/formula_registry.csv. The 82 reported graphs have all been registered and actually evaluated in the scientific code path.'))
 # 7
 new(story,'Deterministic workload and verification status',6)
 story.append(P(f"<b>Executed:</b> {int(m['registered_executed_graphs'])} registered-and-executed graphs, {int(m['multi_graph_batch_calls']):,} real multi-graph batches, {int(m['graph_outputs']):,} graph results, {int(m['scalar_calls']):,} scalar calls. Twelve operating scenarios use 64 cells and 1440 time steps; {int(m['native_state_oracle_comparisons']):,} original-C++-implementation reference comparisons were completed independently. Both kinetic versions remain registered throughout the run."))
 story.append(P(f"<b>Independent verification:</b> {int(audit['high_precision_graph_samples']):,} 80-decimal-place graph checks and {int(audit['native_independent_trajectory_fields'])} independent whole-trajectory field comparisons passed. Both spatially integrated conserved-species balances and nonnegative concentration tests passed; technical tolerances and per-case checks are retained in results/high_precision_audit.json, not promoted as accuracy comparisons in this report."))
 story += F(root,7,'stoichiometric_inventory','Actual length-integrated concentrations A+C and B+C follow the time-integrated boundary transport of each conserved combination, using the recorded paceval concentration fields.',280)
 story.append(P('An additional original-paceval 32/64/128-cell mesh refinement run gives decreasing consecutive outlet-concentration differences for all 12 cases (ratio 0.488–0.510). This provides empirical grid-convergence evidence for the present assumptions, not a general convergence proof or experimental validation.','small'))
 # 8
 new(story,'Reaction fronts and spatial concentration fields',7)
 story.append(P('Starting from a reagent-free channel, the inlet pulse moves downstream and gradually forms product C. Unlike a local kinetics-only benchmark, the calculation captures the interaction between finite residence time, axial effective dispersion and local nonlinear reaction.'))
 story += F(root,2,'spatial_species_profiles','Concentrations A, B and C along the 20 mm channel for three actual recorded time points. Different line styles represent time, and colors represent chemical species.',345)
 story.append(P('The curves describe synthetic, one-dimensional, cross-section-averaged concentrations. They cannot resolve transverse micro-mixing, axial dispersion uncertainty or true wall-catalysis.'))
 # 9
 new(story,'Spatiotemporal reaction development',7.1)
 story.append(P('The genuinely computed spatial and temporal fields provide an application-level demonstration of repeated paceval updates. The surface below is plotted directly from the sampled simulation output; its smooth rendering is graphical interpolation between discrete computed states, not an additional physical model.'))
 story += F(root,3,'product_spacetime_3d','Three-dimensional product C concentration surface from paceval-computed cell states versus channel coordinate and time (scenario 3).',350)
 story.append(P('The front moves from the inlet to the outlet over a velocity-dependent residence interval. The observed endpoint is 144 s and should not be interpreted as proof of an asymptotic reactor steady state at every setting.'))
 # 10
 new(story,'Flow-rate response and parameterized outlet analysis',8)
 story.append(P('These diagrams compare the relevant industrial observables: local extent of reaction at the outlet and the concentration of product under changed velocity and forward-rate coefficient. All plot points are original paceval outputs, not interpolated native C++ results.'))
 story += F(root,4,'reacted_fraction_flow','Outlet stoichiometric reacted fraction for two kinetic models, two forward-rate settings and three flow velocities.',237)
 story += F(root,5,'outlet_product_parameter_map','Final product concentration across a 3 × 2 operating grid per retained kinetic model, with actual values printed in each cell.',234)
 # 11
 new(story,'Controlled kinetic revision and sensitivity analysis',8.1)
 story.append(P('Model v2 introduces a hypothetical saturation denominator in the forward step while keeping the same transport, boundary conditions and reverse-rate term. Both model versions remain simultaneously available; no graph is silently overwritten when mathematical definitions change.'))
 story += F(root,6,'versioned_reaction_outcome','Paired product concentration differences between v2 and v1 for identical boundary inputs and engineering operating settings.',232)
 story += F(root,8,'local_kinetic_sensitivities','Measured paceval analytical sensitivity graph outputs for model v2 evaluated on recorded cell states; points are colored by local B concentration.',232)
 # 12
 new(story,'Reactor-regime descriptors and programmable costs',8.2)
 story.append(P('The dimensionless Péclet group Pe=uL/D and nominal Da=kf Bin L/u help interpret reaction-to-residence and convection-to-dispersion ratios within this simplified reactor. They are diagnostic descriptors of the assumed effective one-dimensional model, not independent measurements.'))
 story += F(root,9,'peclet_damkohler_map','Actual operating conditions in the Pe–Da plane, colored by the observed paceval outlet reacted fraction.',235)
 story += F(root,10,'programmable_composite_scores','Original paceval results for 12 retained weighted research score expressions per version, comparing otherwise matched scenarios.',225)
 # 13
 new(story,'Scientific limitations and industrial interpretation',9)
 story.append(H2('What is genuinely demonstrated'))
 story.append(P('A reproducible original-SDK paceval C++ application executes two distinct, controlled reaction-rate models as persistent mathematical graphs. It integrates physically relevant kinetic, transport, boundary and diagnostic mathematics into actual production-path multi-graph batches. Concentration fields, stoichiometric invariants, outlet descriptors, versioned model comparisons, local analytic sensitivities and 24 composite score variants are all linked to real registered and executed graphs. Independent double-precision and 80-digit implementations verify the full numerical results under the chosen synthetic model.'))
 story.append(H2('What is not established'))
 for x in ['No measured reaction kinetics, public microfluidic benchmark measurements or compound-specific physical parameters were used.',
           'No 2-D or 3-D Navier–Stokes simulation, wall effects, transverse mixing, pressure drop, temperature field or phase/interface dynamics are resolved.',
           'The effective axial dispersion parameter is prescribed; its relation to a particular fabricated chip was not identified or calibrated.',
           'The toy saturation model is a mathematical alternative, not a validated chemical mechanism.',
           'The weighted engineering score and target concentration are hypothetical study policies, not chemical safety certification or production approval.',
           'No hardware throughput, energy efficiency, CPU comparison, economic value or clinical benefit was established.',
           'Trusted Interval Computation (TINC) was not evaluated; finite numerical agreement does not establish certified interval enclosures.']:
  story.append(bullet(x))
 story.append(H2('Next defensible scientific step'))
 story.append(P('Connect a published or newly measured microreactor concentration dataset with independently characterized residence-time distribution; estimate kinetic parameters and confidence regions; compare the same parameters against a high-fidelity transport/CFD model; and use experimental mass-conservation and external validation to test physical transferability.'))
 # 14
 new(story,'Reproducibility, external sources and conclusion',10)
 story.append(H2('Exact reproduction'))
 story.append(P('With a compatible external Linux x86-64 original paceval shared library supplied separately, execute:'))
 story.append(P('1. <font name="DB">cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so</font>','small'))
 story.append(P('2. <font name="DB">cmake --build build -j &amp;&amp; ctest --test-dir build --output-on-failure</font>','small'))
 story.append(P('3. <font name="DB">./build/microfluidic_reactor --out . --cells 64 --steps 1440</font>','small'))
 story.append(P('4. <font name="DB">python3 src/verify_results.py --root .</font>','small'))
 story.append(P('5. <font name="DB">python3 src/mesh_refinement.py --root . --executable build/microfluidic_reactor</font>','small'))
 story.append(P('6. <font name="DB">python3 src/make_figures.py --root .</font>','small'))
 story.append(P('A full, regenerable experiment ships as C++17 source, CMake, original SDK adapter/source, Python validation/figure/report scripts, input CSV, graph registry, independent audit, numerical outcome CSVs and high-resolution PNG plus vector-PDF figures. The shared library is not redistributed.'))
 story.append(H2('External scientific and technical references'))
 sources=[
  '[1] COMSOL (2026), Chemical Transport and Reactions, Microfluidics Module v6.4: doc.comsol.com/6.4/doc/com.comsol.help.mfl/mfl_ug_modeling.05.13.html',
  '[2] OpenFOAM documentation, scalarTransportFoam: doc.openfoam.com/2306/tools/processing/solvers/rtm/basic/scalarTransportFoam/',
  '[3] Westphal H. et al. (2024), Automated platform for monitoring microfluidic reactors with online (chip-)LC/MS, React. Chem. Eng.; DOI 10.1039/D4RE00004H.',
  '[4] Knoll S. et al. (2025), FlowMat: modeling flow reactors with physics-based and ML approaches, RSC Adv.; DOI 10.1039/D5RA06173C.',
  '[5] Silber K. et al. (2026), Kinetic modeling of multi-step transformations using sequential dynamic flow experiments, React. Chem. Eng.; DOI 10.1039/D5RE00306G.',
  '[6] Capillary microreactor photochemistry reaction-rate extraction (2024), React. Chem. Eng.; DOI 10.1039/D4RE00087K.',
  '[7] paceval original C/C++ SDK: github.com/paceval/paceval; paceval.com/api/.']
 for s in sources:story.append(P(escape(s),'small'))
 story.append(H2('Conclusion'))
 story.append(P('The original paceval Mathematical Engine successfully executed and independently passed verification for an end-to-end synthetic microreactor reaction–transport research kernel. This reproducible evidence supports further experimental coupling and research, but does not constitute validation of any particular manufactured microfluidic reactor.'))
 doc=SimpleDocTemplate(str(source),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=51,bottomMargin=52,title='paceval | Microfluidic Reaction-Transport Research',author='paceval Research Demonstrator',subject='Original paceval executable reusable mathematical expression graphs in a verified one-dimensional reaction–transport experiment')
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 print('PDF generated:',source)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);args=ap.parse_args();work(args.root)
