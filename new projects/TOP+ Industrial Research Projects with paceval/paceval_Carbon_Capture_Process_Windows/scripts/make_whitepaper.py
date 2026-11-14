#!/usr/bin/env python3
"""Professional English PDF, all scientific figures from executed paceval CSVs."""
from pathlib import Path
import csv,json
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle,KeepTogether,HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'paceval_Carbon_Capture_Process_Windows_Whitepaper_EN.pdf'
FONTS=Path('/usr/share/fonts/truetype/dejavu')
pdfmetrics.registerFont(TTFont('DejaVu',str(FONTS/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuBold',str(FONTS/'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVuBold')
BLUE=colors.HexColor('#112C42');TEAL=colors.HexColor('#008B8D');MUTED=colors.HexColor('#48616F');PALE=colors.HexColor('#E6F3F2')
P=ParagraphStyle('body',fontName='DejaVu',fontSize=9.0,leading=14.7,textColor=BLUE,spaceAfter=8)
H1=ParagraphStyle('h1',parent=P,fontName='DejaVuBold',fontSize=15.2,leading=20,textColor=BLUE,spaceBefore=13,spaceAfter=10,keepWithNext=True)
H2=ParagraphStyle('h2',parent=P,fontName='DejaVuBold',fontSize=10.8,leading=15,spaceBefore=9,spaceAfter=7,keepWithNext=True)
LEAD=ParagraphStyle('lead',parent=P,fontSize=11,leading=17.5,spaceAfter=15)
SMALL=ParagraphStyle('small',parent=P,fontSize=7.8,leading=12.7)
CAP=ParagraphStyle('cap',parent=P,fontSize=7.9,leading=12.5,textColor=MUTED,spaceAfter=7)
EQ=ParagraphStyle('eq',parent=P,fontName='DejaVu',fontSize=9.2,leading=15,textColor=BLUE,leftIndent=10,rightIndent=10,spaceBefore=5,spaceAfter=9)
CELL=ParagraphStyle('cell',parent=P,fontSize=7.5,leading=10.4,spaceAfter=0)
CELLB=ParagraphStyle('cellb',parent=CELL,fontName='DejaVuBold')
TITLE=ParagraphStyle('title',fontName='DejaVuBold',fontSize=25,leading=31,textColor=BLUE,spaceAfter=11)
SUB=ParagraphStyle('subtitle',parent=P,fontSize=12.5,leading=19,textColor=TEAL,spaceAfter=15)
A4W,A4H=A4
PAGE_W=A4W-44*mm; IMAGE_W=PAGE_W
figpaths=sorted((ROOT/'figures').glob('fig*.png'))
assert len(figpaths)==10
rows=pd.read_csv(ROOT/'results/screening.csv');compare=pd.read_csv(ROOT/'results/model_comparison.csv');ev=json.loads((ROOT/'results/execution_evidence.json').read_text());audit=json.loads((ROOT/'results/high_precision_audit.json').read_text())
summary=rows.groupby('model').agg({'recovery':'mean','specific_duty_GJ_tCO2':'mean','composite_guard':'sum','reboiler_kW':'mean'}).round(4)
story=[]
def para(text,style=P):story.append(Paragraph(text,style))
def head(text):para(text,H1)
def sub(text):para(text,H2)
def pg():story.append(PageBreak())
def gap(n=6):story.append(Spacer(1,n))
def eq(s):para(escape(s),EQ)
def img(path,w=IMAGE_W):
 from PIL import Image as PILImage
 with PILImage.open(path) as im:iw,ih=im.size
 return Image(str(path),width=w,height=w*ih/iw)
def fig(i,caption,w=IMAGE_W):
 path=figpaths[i-1]
 story.append(KeepTogether([img(path,w),Spacer(1,4),Paragraph(f'<b>Figure {i}.</b> {caption}',CAP)]))
def table(headers,records,widths=None):
 data=[[Paragraph(str(x),CELLB) for x in headers]]+[[Paragraph(str(x),CELL) for x in r] for r in records]
 t=Table(data,colWidths=widths if widths else [PAGE_W/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('TEXTCOLOR',(0,0),(-1,-1),BLUE),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.75,TEAL),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#D6E0E5'))]))
 story.append(t);gap(12)

def footer(canvas,doc):
 canvas.saveState();w,h=A4
 canvas.setStrokeColor(colors.HexColor('#D6E3E7'));canvas.line(22*mm,19*mm,w-22*mm,19*mm)
 canvas.setFont('DejaVu',7);canvas.setFillColor(MUTED)
 canvas.drawString(22*mm,14.3*mm,'paceval.  |  Carbon Capture Process Windows  |  Research 2026')
 canvas.drawRightString(w-22*mm,14.3*mm,f'Page {doc.page}')
 if doc.page>1:
  canvas.setFont('DejaVuBold',7.2);canvas.setFillColor(TEAL)
  canvas.drawString(22*mm,h-17*mm,'PACEVAL  /  INDUSTRIAL RESEARCH  /  WP 16')
 canvas.restoreState()

# Cover page
story.append(Spacer(1,23*mm))
para('CARBON CAPTURE',TITLE)
para('Absorber-Regenerator Process Windows',ParagraphStyle('t2',parent=TITLE,fontSize=20,leading=26,spaceAfter=15))
para('A reproducible mathematical feasibility and regeneration-energy research demonstrator using original paceval computation graphs',SUB)
story.append(img(ROOT/'figures/00_carbon_capture_hero.png',PAGE_W));gap(16)
para('<b>Research outcome</b>  |  Original paceval SDK 4.25 executed 56 of 56 reusable mathematical graphs over 3,072 deterministic synthetic operating points and two simultaneously accessible model variants.',LEAD)
para('<b>Verification:</b> independent C++ end-value checks and a separate 90-digit mpmath reference passed. <b>Scope:</b> reduced-order mass-transfer, solvent-loading and heat-duty screening. No plant calibration, industrial deployment or solvent product-purity claim.',P)
para('14 November 2026  |  English scientific report  |  WP 16',SMALL)
pg()

head('1. Introduction: industrial use case and current state of the art')
para('Post-combustion carbon capture with aqueous amines typically combines a packed-gas absorber, a lean/rich solvent heat exchanger and a heated stripping column. Flue-gas CO2 transfers into a circulating lean solution, while the rich solution returns to a stripper where thermal energy releases CO2 and restores the solvent. Plant operators must meet a capture target while respecting practical bounds on solvent circulation, CO2 loading and thermal regeneration duty.')
para('An industrial operating-point study requires repeated evaluation of inlet-gas conditions, transfer capacity, solvent loading, lean/rich temperatures, regeneration energy and interdependent constraints. The engineering questions are therefore not limited to whether CO2 can be absorbed. They include which settings remain mathematically admissible and how changing one assumption shifts the feasible operating window.')
sub('Established research and software')
para('Conventional 30 wt% MEA is widely used as a post-combustion benchmark; the widely cited reboiler range around 3.6 to 4.0 GJ/tCO2 pertains to particular reference plant arrangements [1]. Rigorous models generally use electrolyte thermodynamics, rate-based column equations, calibrated transport and reaction data, and process flowsheet calculations. Examples include Aspen Plus models and modern solvent-blend studies [3-6].')
para('A 2025 experimental/modeling study of aqueous AMP/PZ reported thermodynamic calibration and validation against two pilot-plant campaigns [3]. A 2026 CESAR1 study described a rigorously validated rate-based model [4]. Separate 2024 and 2026 work examines amine mixtures, integrated heat recovery and overall process operation [5,6]. These are substantially richer physical models than the present mathematical screening experiment.')
sub('The demonstrator contribution')
para('The proposed study isolates a coherent mathematical kernel inside the wider carbon-capture workflow: CO2 transfer, solvent capacity, recovery, heat-demand decomposition, signed constraint margins, local derivatives and two versioned composite calculations. The engine provides transparent reusable expressions while C++ orchestrates candidate inputs and validation.')
pg()

head('2. Research question and executable architecture')
para('<b>Research question:</b> Can the original paceval Mathematical Engine correctly execute full, coupled carbon-capture process-window calculations for multiple formula versions, retain graph handles and return independently validated end results from real multi-graph batch evaluation?')
para('The experiment uses deterministic synthetic operating points. The main C++ application parses a controlled numeric CSV schema, checks domains, creates persistent paceval expressions, evaluates the candidate set in bounded multi-graph batches and writes machine-readable result files. Both model versions remain independently addressable during the same process invocation.')
sub('Executable chain')
table(['Stage','Responsibility','Actual output'],[
 ['1. Input and parameter domains','C++ host and original SDK decimal conversion','Validated binary64 vectors and rejected malformed inputs'],
 ['2. Core process mathematics','Actual paceval reusable graphs','Capture, loading, heat duty, recovery, off-gas CO2'],
 ['3. Composite conditions and local derivatives','Actual paceval reusable graphs','Signed margins, 0/1 feasibility gate, score, sensitivities'],
 ['4. Cross-model comparison','Additional actual paceval graphs','Delta recovery, delta capture, delta duty, joint guard'],
 ['5. Verification and publication','Separate native C++ and 90-digit Python; C++ I/O','Audited results, figures and independently verified status'],
 ],[36*mm,62*mm,PAGE_W-98*mm])
para('Graph handles are created once and reused. The SDK batch layout and per-item error behavior are checked explicitly rather than assumed. No multi-step process simulator, chemical equilibrium solver or optimization algorithm is attributed to paceval.')
pg()

head('3. Mathematical model and assumptions')
para('The two model versions use the same input vector and constrained steady-state control-volume assumptions. Transfer parameters are proxies, not calibrated chemistry. All input columns, units and admissible ranges are specified in the input schema.')
sub('Absorber material-balance kernel')
eq('N_transfer = kLa * Vol * (Cstar - Cbulk)    [mol/s]')
eq('N_capacity = S * (alpha_max - alpha_lean)    [mol/s]')
eq('V1: N_capture = min(Fin, N_capacity, N_transfer)')
eq('V2: N_capture = min(Fin, N_capacity * (1 - exp(-N_transfer/N_capacity)))')
para('Recovery is N_capture/Fin; the rich loading is alpha_lean + N_capture/S. The capture rate is always bounded by the inlet CO2 and the available cyclic solvent capacity. Treated-gas CO2 mole fraction follows a simplified binary-gas mass balance; it is not a captured-product purity estimate.')
sub('Regenerator energy kernel')
eq('Q_sensible = (S * 0.06108 / wt) * cp * (Tstrip - Tfeed) * (1 - HX_eff)    [kW]')
eq('Q_total = Q_sensible + N_capture * dh + Q_vapor    [kW]')
eq('q_specific = Q_total / (1000 * 0.04401 * N_capture)    [GJ/tCO2]')
para('The amine and CO2 molecular masses are model constants in kg/mol. Sensible heat is based on circulating solution mass flow and specified heat recovery. V2 raises the illustrative bounded recovery parameter and varies the overhead vapor heat term with stripping temperature. Both are explicitly research hypotheses, not a physical claim about real absorber and stripper hardware.')
sub('Constraints, score and differentiation')
para('The engine evaluates four signed margins for minimum capture, maximum thermal duty, maximum rich loading and upper stripper temperature. Positive margins denote admissibility. The four conditions are combined in a real 0/1 paceval graph and a multi-term score. Local sensitivities to kLa and Tstrip are analytically specified and checked only away from nondifferentiable model-switch points.')
pg()

head('4. paceval execution architecture and verified scope')
para('The exact SDK version is 4.25 with the original local C/C++ API and the separately provided Linux shared library. Graph creation and execution are backed by persistent handles. The production path invokes the real SDK multi-graph batch interface, complemented by a scalar API smoke test and a version comparison pass.')
table(['Mathematical function / industrial purpose','Actual owner','Graph IDs or host rationale'],[
 ['Mass-transfer driving force, solvent capacity and capture','paceval','V1_TRANSFER_POTENTIAL; V2_CAPTURE'],
 ['Rich loading, off-gas and fraction removed','paceval','V1_RICH_LOADING; V2_CAPTURE_FRACTION'],
 ['Sensible heat, desorption and vapor contributions','paceval','V1_REBOILER_SENSIBLE; V2_REBOILER_VAPOR'],
 ['Composite thermal duty and duty per captured mass','paceval','V1_REBOILER_TOTAL; V2_SPECIFIC_DUTY'],
 ['Capture, duty, loading and temperature margins','paceval','V1_MARGIN_CAPTURE; V2_MARGIN_LOADING'],
 ['Composite guard, score and local derivatives','paceval','V1_COMPOSITE_GUARD; V2_D_ETA_D_KLA'],
 ['Cross-model deltas and joint guard','paceval','DELTA_CAPTURE; DELTA_SPECIFIC_DUTY; COMBINED_GUARD'],
 ['I/O, batch grouping, domain validation and test selection','C++ host','Nonmathematical orchestration and dataset provenance'],
 ['Independent numerical checks','C++ / Python reference','Separate audited verification, not production outputs'],
 ],[69*mm,25*mm,PAGE_W-94*mm])
para('The manifest and execution inventory show real graph IDs, expressions and the execution owner. The actual scalar tests, SDK number/string conversions, operator checks and batch layout controls are recorded in test outputs. All production research graph groups were exercised with real numeric results.')
pg()

head('5. Deterministic research workload')
para('A deterministic generator provides 3,072 distinct synthetic operating inputs spanning four operating groups. For every input, both models are evaluated with identical gas, solvent and screening thresholds. The primary variables include inlet CO2 and bulk-gas flows, absorber transfer coefficient and contact volume, solution loading, amine circulation, regeneration temperature, heat-exchanger fraction, sensible heat capacity and reaction/vapor enthalpy parameters.')
table(['Property','Actual scope'],[
 ['Synthetic candidate inputs',str(ev['scenario_count'])],
 ['Model versions','V1 and V2, both retained and individually addressable'],
 ['Model-case evaluations',str(ev['model_case_combinations'])],
 ['Executed / created research graphs',f"{ev['unique_graphs_executed']} / {ev['unique_graphs_created']}"],
 ['Actual scalar API calls',str(ev['scalar_calls_including_operator_tests'])+' (including operator self-tests)'],
 ['Actual batch API calls',str(ev['batch_calls_including_layout_probe'])+' (including layout probe)'],
 ['Graph-point evaluations',str(ev['graph_point_evaluations_including_layout_probe'])+' (including layout probe)'],
 ],[67*mm,PAGE_W-67*mm])
para('All values in the output CSV are produced with the real paceval runtime. The generator seed-free deterministic loops and literal schema are retained. Physically inadmissible and potentially singular inputs are rejected before graph evaluation; Boolean masks are never treated as lazy execution guards.')
para('The sample does not claim to represent a statistically sampled industrial plant fleet, any particular proprietary solvent, measured energy savings or process-plant optimization optimality.')
pg()

head('6. Executed results and scientific interpretation')
para('Both versions were independently checked against their mathematical specifications. For the illustrative limits in this experiment, the number of model-case combinations with all four margins nonnegative differs because the two versions encode different transfer saturation and energy recovery hypotheses.')
table(['Executed indicator','V1','V2'],[
 ['Operating inputs evaluated','3,072','3,072'],
 ['Mean capture fraction',f"{summary.loc['V1','recovery']:.3f}",f"{summary.loc['V2','recovery']:.3f}"],
 ['Mean thermal specific duty (GJ/tCO2)',f"{summary.loc['V1','specific_duty_GJ_tCO2']:.3f}",f"{summary.loc['V2','specific_duty_GJ_tCO2']:.3f}"],
 ['Candidates meeting illustrative limits',f"{ev['feasible_V1']:,}",f"{ev['feasible_V2']:,}"],
 ['Independent native full-endvalue assertions',str(ev['native_assertions']),'Shared versioned audit'],
 ['High precision checks passed',str(audit['checks_passed']),'Both versions'],
 ],[78*mm,(PAGE_W-78*mm)/2,(PAGE_W-78*mm)/2])
para('The mean recovery and screening pass counts are model outputs, not measured capture efficiencies. A capture fraction below the illustrative target may coexist with a seemingly attractive thermal duty. Conversely, satisfying one criterion cannot compensate for a violation of another: feasibility requires all four signed margins.')
sub('Representative baseline operating input')
example=rows[rows.case_id=='CC00000'].set_index('model')
table(['paceval end result','V1','V2'],[
 ['CO2 capture (mol/s)',f"{example.loc['V1','capture_mol_s']:.3f}",f"{example.loc['V2','capture_mol_s']:.3f}"],
 ['CO2 recovery',f"{example.loc['V1','recovery']:.3f}",f"{example.loc['V2','recovery']:.3f}"],
 ['Specific reboiler duty (GJ/tCO2)',f"{example.loc['V1','specific_duty_GJ_tCO2']:.3f}",f"{example.loc['V2','specific_duty_GJ_tCO2']:.3f}"],
 ['All constraints satisfied','Yes' if example.loc['V1','composite_guard'] else 'No','Yes' if example.loc['V2','composite_guard'] else 'No'],
 ],[78*mm,(PAGE_W-78*mm)/2,(PAGE_W-78*mm)/2])
pg()

head('7. CO2 capture and process-energy landscapes')
fig(1,'Four operating groups reveal the dependence of synthetic recovery on the mathematical transfer model.',IMAGE_W)
fig(2,'Specific regeneration energy versus CO2 capture fraction. The marked recovery threshold is an illustrative input criterion.',IMAGE_W)
pg()

head('8. Thermal balance and solvent capacity')
fig(3,'Component-resolved reboiler demand, decomposed into sensible heat, CO2 desorption and a simplified vapor contribution.',IMAGE_W)
fig(4,'Calculated rich solvent loading versus captured CO2 fraction. This is not a calibrated chemical equilibrium curve.',IMAGE_W)
pg()

head('9. Multi-constraint process-window evidence')
fig(5,'Actual mathematical 0/1 guard acceptance fractions for each synthetic scenario and both formula versions.',IMAGE_W)
fig(6,'Model V2 specific duty compared to V1 at unchanged input vectors. The diagonal is equality, not an engine benchmark.',IMAGE_W)
pg()

head('10. Analytical sensitivity and treated-gas composition')
fig(7,'Local derivative of captured CO2 flow with respect to the transfer coefficient; values depend on the active branch.',IMAGE_W)
fig(8,'Modelled treated-gas CO2 fraction versus capture fraction under the binary gas assumption.',IMAGE_W)
pg()

head('11. Three-dimensional operating window')
fig(9,'The V2 output surface projected into solvent-flow, transfer-coefficient and captured-fraction axes. Point color encodes actual calculated heat demand.',IMAGE_W)
para('The projection illustrates the interaction between circulation, absorption driving force and thermal duty. Individual dots are computed candidates, not continuous plant operating trajectories or interpolated experimental measurements.')
sub('Why a three-dimensional figure?')
para('Two-dimensional charts can obscure that the same CO2 recovery may correspond to different solvent circulation and regeneration duties. This view preserves the joint variation of multiple driving parameters while keeping the operating-point representation directly traceable to actual CSV rows.')
pg()

head('12. Screening boundaries and independent verification')
fig(10,'Illustrative rejection causes grouped by signed limit. A single candidate may violate multiple limits.',IMAGE_W*0.93)
para('Independent native C++ tests covered complete coupled end values, not only elementary expressions. A distinct Python 90-decimal-digit reference checked model outputs and cross-version differences using the exact intended binary64 input values. Its detailed tolerance and difference records are retained exclusively in technical audits.')
para(f'The verified test set contains <b>{ev["native_assertions"]:,} native end-value assertions</b> and <b>{audit["checks_passed"]:,} high-precision checks</b>. These are independent verification events, not additional paceval graph executions. The actual number of unique research graphs is {ev["unique_graphs_created"]}.')
pg()

head('13. Applicability, limitations and next scientific steps')
para('These results establish a mathematically auditable reduced-order functional demonstration: the selected formulas are compiled into actual persistent paceval expressions, exercised over deterministic cases and checked independently. They do not establish full absorber or stripper physics, predicted CO2 product purity, realistic hydrodynamics, amine vapor loss, property correlations, equipment design compliance or plant safety.')
para('A production-grade digital engineering study would next import measured solvent equilibrium, kinetic and transport properties, validate against rate-based rigorous models or pilot data, include heat and liquid-vapor phase coupling and quantify parameter uncertainty. The engine could then be assessed as a mathematical submodule of those validated workflows. Hardware acceleration would remain a separate future engineering hypothesis.')
sub('Literature and technical sources')
refs=[
 '[1] Royal Society of Chemistry (2018), Carbon capture and storage: the way forward, Energy & Environmental Science. pubs.rsc.org/en/content/articlehtml/2018/ee/c7ee02342a',
 '[2] NETL (2024), Carbon Capture Program R&D Compendium. netl.doe.gov/sites/default/files/2025-01/Carbon-Capture-Compendium-2024.pdf',
 '[3] ACS (2025), Development of a Validated Rate-Based Model for CO2 Absorption in Aqueous AMP/PZ Blends. pmc.ncbi.nlm.nih.gov/articles/PMC12519493/',
 '[4] Separation and Purification Technology (2026), CESAR1 Unlocked: A validated rate-based model enabling next-generation carbon capture design. doi.org/10.1016/j.seppur.2026.137422',
 '[5] Chemical Engineering Research and Design (2026), Process integration and energy optimization of an MDEA/PZ-based CO2 capture system. doi.org/10.1016/j.cherd.2026.02.062',
 '[6] Separation and Purification Technology (2024), Process simulation and optimization for post-combustion CO2 capture pilot plant. doi.org/10.1016/j.seppur.2024.127873',
 '[7] paceval API documentation and product brief (2026). paceval.com/api/ and paceval.com/product-brief/'
]
for r in refs:para(escape(r),SMALL)
para('Source code, input schemas, individual graph formulas, results and independent audit files accompany this standalone research paper in the GitHub-compatible ZIP package.',SMALL)

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=22*mm,leftMargin=22*mm,topMargin=25*mm,bottomMargin=25*mm,title='paceval Carbon Capture Absorber-Regenerator Process Windows',author='paceval. Industrial Research',subject='Independent functional demonstration of mathematical carbon capture operating-window screening')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('WHITEPAPER CREATED',OUT,OUT.stat().st_size)
