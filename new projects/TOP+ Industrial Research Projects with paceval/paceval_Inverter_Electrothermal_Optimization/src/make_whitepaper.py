#!/usr/bin/env python3
"""Build the published English PDF from independently validated recorded paceval data.
Uses ReportLab for pagination and preserved-aspect hero / print-sized graphics.
"""
from pathlib import Path
import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor,white
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,Table,TableStyle,KeepTogether,HRFlowable
from PIL import Image as PILImage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
base=Path(__file__).resolve().parents[1];F=base/'figures';R=base/'results'
OUT=base/'paceval_Inverter_Electrothermal_Optimization_Whitepaper_EN.pdf'
e=json.loads((R/'execution_evidence.json').read_text());a=json.loads((R/'independent_reference_audit.json').read_text())
font='/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('DejaVu',font+'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold',font+'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Oblique',font+'DejaVuSans-Oblique.ttf'))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVu-Bold',italic='DejaVu-Oblique',boldItalic='DejaVu-Bold')
NAVY=HexColor('#12334D');TEAL=HexColor('#088A95');SLATE=HexColor('#536473');MUTED=HexColor('#EAF3F5');ORANGE=HexColor('#DB7E36')
styles={
 'title':ParagraphStyle('title',fontName='DejaVu-Bold',fontSize=23,leading=29,textColor=NAVY,spaceAfter=10),
 'subtitle':ParagraphStyle('subtitle',fontName='DejaVu',fontSize=11.0,leading=17,textColor=SLATE,spaceAfter=14),
 'chapter':ParagraphStyle('chapter',fontName='DejaVu-Bold',fontSize=16.0,leading=22,textColor=NAVY,spaceBefore=0,spaceAfter=10),
 'section':ParagraphStyle('section',fontName='DejaVu-Bold',fontSize=10.8,leading=16,textColor=TEAL,spaceBefore=10,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='DejaVu',fontSize=9.05,leading=14.3,textColor=NAVY,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='DejaVu',fontSize=8.15,leading=12.4,textColor=NAVY,spaceAfter=6),
 'caption':ParagraphStyle('caption',fontName='DejaVu-Oblique',fontSize=7.6,leading=11,textColor=SLATE,spaceAfter=10),
 'tiny':ParagraphStyle('tiny',fontName='DejaVu',fontSize=7.3,leading=10,textColor=SLATE,spaceAfter=4),
 'cover':ParagraphStyle('cover',fontName='DejaVu-Bold',fontSize=10,leading=14,textColor=TEAL,spaceAfter=10),
}
doc=SimpleDocTemplate(str(OUT),pagesize=A4,topMargin=17*mm,bottomMargin=18*mm,leftMargin=19*mm,rightMargin=19*mm,title='Industrial Inverter Electrothermal Mathematical Execution with paceval',author='paceval Research Demonstrator',subject='Verified synthetic inverter thermal research, reusable paceval execution graphs, no performance benchmarks')
W=A4[0]-38*mm
story=[]
def para(t,style='body'):story.append(Paragraph(t,styles[style]))
def title(t):para(t,'chapter')
def section(t):para(t,'section')
def spacer(n=4):story.append(Spacer(1,n*mm))
def pb():story.append(PageBreak())
def img(p,width_mm=152,max_h_mm=90):
    p=Path(p);im=PILImage.open(p);iw,ih=im.size;w=width_mm*mm;h=w*ih/iw
    if h>max_h_mm*mm:h=max_h_mm*mm;w=h*iw/ih
    story.append(Image(str(p),width=w,height=h,hAlign='CENTER'))
def fig(key,caption,width_mm=156,maxh=82):img(F/f'{key}.png',width_mm,maxh);para(caption,'caption')
def tbl(header,rows,widths=None):
  data=[[Paragraph(str(x),styles['small']) for x in header]]+[[Paragraph(str(x),styles['small']) for x in row] for row in rows]
  t=Table(data,colWidths=widths or [W/len(header)]*len(header),repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),MUTED),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,HexColor('#F8FAFB')]),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7)]))
  story.append(t)
def equ(name,mathstr):
    plt.rcParams['font.family']='DejaVu Sans'
    f=plt.figure(figsize=(10,1.05));f.text(.02,.42,'$'+mathstr+'$',fontsize=17,ha='left',va='center',color='#12334D');f.savefig(F/(name+'.png'),dpi=180,bbox_inches='tight',transparent=True,pad_inches=.13);plt.close(f)
    img(F/(name+'.png'),width_mm=159,max_h_mm=24)

def footer(canvas,d):
 canvas.saveState();w,h=A4;canvas.setStrokeColor(HexColor('#CFDDE2'));canvas.line(19*mm,15.0*mm,w-19*mm,15.0*mm)
 canvas.setFont('DejaVu',7);canvas.setFillColor(SLATE);canvas.drawString(19*mm,10.8*mm,'paceval | Industrial Power Electronics Research | 14 November 2026')
 canvas.drawRightString(w-19*mm,10.8*mm,str(d.page));canvas.restoreState()

# 1 cover.
para('paceval.  |  INDUSTRIAL RESEARCH', 'cover')
para('Programmable Electrothermal Mathematics for SiC Inverter Power Modules','title')
para('Reusable paceval execution graphs for conduction and switching losses, coupled junction temperature, sensitivity analysis and controlled engineering margins','subtitle')
img(F/'00_inverter_electrothermal_hero.png',width_mm=170,max_h_mm=85)
para('Concept illustration; not an image computed by paceval.','caption')
spacer(2)
section('Research outcome')
para('A genuine C++ program using the original paceval API 4.25 executed <b>35 distinct mathematical graphs</b> across two model versions, a sweep of <b>100,000 synthetic operating points</b>, controlled two-dimensional operating maps and 12 first-order transient cases. The resulting computations passed independently coded analytic and high-precision checks. The work establishes functional mathematical execution for this specific, deliberately synthetic model; it does not validate a commercial inverter design.','body')
para('Scientific scope: synthetic per-switch equivalent current and energy surrogates; lumped effective junction-to-ambient thermal resistance; engineering analysis only. No hardware measurements, industrial certification or performance comparison.','small')
pb()
# 2 background.
title('1. Industrial use case and current state of the art')
para('Power electronic inverters continuously redirect electrical energy between a DC source and an AC load. Each semiconductor switch dissipates heat while conducting current and during turn-on and turn-off commutation. Because junction temperature can modify electrical losses, the engineer must assess switching frequency, current, bus voltage and the effective cooling path together. The problem is especially relevant in high-power converters where local device limits matter even if total system power is large.')
para('A typical design workflow combines data-sheet characterization, measured turn-on and turn-off energy, on-state resistance as a function of temperature, thermal-network models and circuit simulation. Manufacturers characterize energy across particular current, voltage, temperature and gate conditions. A simplified equation cannot replace those device-specific tests.')
section('Research context')
para('Bianchini et al. (2025) describe a switching-loss model for virtual SiC MOSFET junction-temperature estimation [1]. Infineon provides practical guidance for translating switching energy across application conditions [2, 3]. A 2026 paper studies junction-temperature measurements in SiC inverters with surge-avoidance techniques [4], while Drummond and colleagues examine application-representative SiC module power cycling [5]. These studies motivate the chosen electrothermal workflow, but their published results are not represented as paceval measurements.')
section('Research question')
para('<b>Can a stable, versioned collection of mathematically meaningful loss, electrothermal balance, sensitivity and quality expressions be executed by actual reusable paceval graphs, with C++ managing only state and root-solving decisions?</b> This study evaluates that question through reproducible synthetic data. It does not claim a new semiconductor device model or an end-to-end inverter efficiency estimate.')
section('Proposed industrial role')
para('In a future calibration-controlled workflow, an engineer could approve model coefficients from measured device curves and then reuse persistent formula versions across inverter operating points. A host application would manage device identities, applicability ranges, thermal solver brackets and result provenance. Safety-related actuation and qualified hardware limits must remain the responsibility of independently validated systems.')
pb()
# 3 architecture.
title('2. Experimental architecture and responsibilities')
fig('01_architecture_concept','Figure 1. Conceptual division of responsibilities: C++ generates and validates inputs, paceval owns the mathematical kernels, C++ orchestrates state/root steps, and paceval evaluates engineering margins.',width_mm=163,maxh=65)
para('The original SDK source files <b>paceval_main.h</b> and <b>paceval_main.cpp</b> are compiled directly, and their calls reach the independently supplied Linux shared library. Distinct persistent graph handles represent v1 and v2 without overwriting prior formulas. The engine uses the actual <b>paceval_dGetMultipleComputationsResultsExt</b> function for the principal calculations, including multiple independent input vectors. A separate scalar API test proves the expected graph-major layout of multi-graph results.')
section('Mathematics routed through paceval')
tbl(['Graph function family','Execution implementation'],[
 ('Two versions of conduction / switching / total loss','Six real graphs, three per version'),
 ('Thermal residual and analytic residual derivative','Four graphs used inside the C++ root solver'),
 ('Temperature, loss and feedback margins','Six verified mathematical guard graphs'),
 ('Loss/temperature sensitivities, switching share, stress score, Boolean conditions','Twelve real graphs across both versions'),
 ('Transient thermal step and loss-energy step','Four graphs reused for every time step'),
 ('Inter-version differences','Three distinct follow-on graphs')],widths=[W*.56,W*.44])
spacer(2)
para('A registered but unused formula is not counted as executed. The complete 35-formula inventory contains the exact parser expressions, graph version, evaluation owner and reference test. Input data flow, scalar numerical checks and actual graph-point counts are archived as machine-readable evidence.','small')
pb()
# 4 maths.
title('3. Defined loss and temperature models')
para('The modeled quantities refer to a single <b>equivalent power switch</b>. The equivalent RMS conduction current is I (A), bus voltage V (V), switching frequency f (Hz), junction temperature Tj (°C), ambient temperature Ta (°C), and effective thermal resistance Rth (K/W). The model reference temperature is 25 °C. All electrical-energy and device coefficients in this study are synthetic research parameters.')
section('Version v1: original WP 03 model family')
equ('math_v1_conduction',r'P_{cond,1}=I^2R_0\left[1+\alpha_1(T_j-25)\right]')
equ('math_v1_switch',r'P_{sw,1}=f_{sw}E_0\left(\frac{V}{800}\right)\left(\frac{I}{100}\right)')
equ('math_residual',r'F_v(T_j)=T_j-T_a-R_{th}\left[P_{cond,v}(T_j)+P_{sw,v}(T_j)\right]')
para('The specified synthetic values are R0 = 0.018 ohm, alpha1 = 0.0038 1/K and E0 = 0.0026 J. Their purpose is reproducibility, not datasheet characterization. The host solves F(Tj)=0 using a safeguarded iterative method; each residual and analytic derivative is supplied by a persistent paceval graph.')
section('Version v2: extended nonlinear synthetic loss model')
para('The second, concurrently stored formula version adds a peak-to-peak triangular current ripple correction to the RMS conduction term, a quadratic temperature coefficient and temperature-dependent switching loss. Fractional current and voltage powers describe a chosen synthetic surrogate, not experimentally fitted scaling.')
equ('math_v2_conduction',r'P_{cond,2}=(I^2+I_{rip}^2/12)R_0(1+\alpha_2\Delta T+\beta_R\Delta T^2)')
para('Here alpha2 = 0.0036 1/K, betaR = 0.0000012 1/K² and ΔT = Tj − 25 °C. Switching loss includes E0(V/800)^1.04(I/100)^1.06(1 + 0.0009ΔT) and an additional 0.00030 J term proportional to voltage and current, with temperature factor (1 + 0.0013ΔT). All power is computed in W and all temperatures are in °C with differences in K.')
pb()
# 5 experiment.
title('4. Deterministic research design')
para('The C++ generator creates 100,000 distinct input records, with a fixed integer mapping to 0–180 A equivalent RMS current, 450–900 V DC bus voltage, 0–26 kHz switching frequency, synthetic ambient conditions and six effective cooling resistances. The actual CSV input is then parsed again using <b>paceval_dConvertStringToFloat</b> following strict literal-only validation. No numeric CSV expressions are evaluated from untrusted text. Output values use <b>paceval_dConvertFloatToString</b>; their text precision is not misrepresented as bitwise lossless binary64.')
fig('02_synthetic_operating_coverage','Figure 2. Sampling of the original, executed v2 scenario outputs. A point is colored only when a root is present in the declared thermal model interval.',width_mm=152,maxh=90)
section('Controlled surfaces and time-dependent cases')
para('A separate 41 × 41 parameter grid was evaluated for each model version at 750 V, 35 °C and 0.16 K/W, allowing exact two-dimensional plots of the computed response rather than interpolation from unrelated input settings. The time-domain experiment uses 12 synthetic model/drive/cooling combinations with 480 explicit state updates per case, a 0.25 s step and a declared thermal capacity of 60 J/K. This is a one-node lumped thermal model, not a measured power-module thermal impedance.')
pb()
# 6 audited counts and examples.
title('5. Executed numerical results')
tbl(['Recorded activity / result','Value'],[
 ('Different paceval graphs created and actually executed',f'{e["executed_graphs"]:,}'),
 ('Independent synthetic stationary inputs',f'{e["synthetic_scenarios"]:,}'),
 ('Distinct model-specific input evaluations','200,000'),
 ('Actual multi-graph batch calls',f'{e["multi_graph_batch_calls"]:,}'),
 ('Actual graph-point outputs (all calculation stages)',f'{e["graph_point_evaluations"]:,}'),
 ('Successful stationary v1 / v2 steady roots',f'{e["model_counts"]["v1"]["successfully_solved"]:,} / {e["model_counts"]["v2"]["successfully_solved"]:,}'),
 ('Identical scenario IDs with both valid roots',f'{e["complete_model_pairs"]:,}'),
 ('Independent full-model mathematical result checks',f'{a["native_scalar_checks"]:,}'),
 ('Independent time-domain checks',f'{a["full_trajectory_checks"]:,}'),
 ('Independent high-precision checks (80 decimal digits)',f'{a["high_precision_checks_80digit"]:,}')],widths=[W*.70,W*.30])
section('Representative actual operating point')
para('At I = 80 A, V = 750 V, f = 16 kHz, Ta = 35 °C and Rth = 0.16 K/W, both versions were directly evaluated on the controlled surface:')
tbl(['Per-switch result','Model v1','Model v2'],[
 ('Steady junction temperature','60.94 °C','61.60 °C'),('Conduction loss','130.93 W','130.73 W'),
 ('Switching loss','31.20 W','35.49 W'),('Total device loss','162.13 W','166.22 W'),
 ('Remaining allowable loss relative to 220 W','57.87 W','53.78 W')],widths=[W*.52,W*.24,W*.24])
para('The differences above are model-revision effects within synthetic assumptions, not experimental validation of one model over the other.','caption')
pb()
# 7 losses.
title('6. Physical components of the computed loss')
fig('03_conduction_and_switching_loss','Figure 3. Actual paceval-computed electrical conduction, switching and total losses at 16 kHz; the purple line is a deliberately hypothetical loss allowance.',maxh=102)
fig('10_switching_fraction_versioned','Figure 4. Fraction of modeled device loss associated with switching, computed by both retained graph versions.',maxh=89)
pb()
# 8 3d.
title('7. Three-dimensional electrothermal solutions')
fig('04_junction_temperature_surface_v1','Figure 5. V1 stationarity surface: the temperature root comes from the host-controlled balance and paceval graph evaluation, not a native independent substitute.',maxh=91)
fig('05_junction_temperature_surface_v2','Figure 6. V2 stationarity surface: versioned temperature feedback is included in every executed loss expression.',maxh=91)
pb()
# 9 margins.
title('8. Thermal and electrical constraints')
fig('06_temperature_margin','Figure 7. Remaining junction-temperature margin T_limit − Tj for the hypothetical v2 reference configuration.',maxh=88)
fig('07_loss_margin','Figure 8. Remaining power-loss margin P_limit − P_loss; the dark contour marks a zero-margin boundary.',maxh=88)
pb()
# 10 deltas.
title('9. Model revisions and analytic sensitivities')
fig('08_temperature_model_revision','Figure 9. Actual difference between the concurrently stored v1 and v2 junction-temperature solutions on exactly the same synthetic input grid.',maxh=88)
fig('09_thermal_sensitivity','Figure 10. V2 implicit junction-temperature sensitivity with respect to equivalent RMS current, calculated as a paceval expression using analytic loss derivatives and thermal-feedback margin.',maxh=88)
pb()
# 11 regions.
title('10. Guard expressions and engineering interpretation')
fig('11_model_decision_distributions','Figure 11. Counts of three research labels calculated by C++ from paceval-computed continuous margins and scores. They do not constitute equipment qualification.',maxh=88)
fig('14_operating_margin_regions','Figure 12. Synthetic two-dimensional margin classifications derived from stored paceval temperature and total-loss limits.',maxh=88)
pb()
# 12 transients.
title('11. Time-dependent thermal analysis')
fig('12_transient_junction_temperature','Figure 13. Independently validated first-order junction-temperature trajectories of three deterministic load waveforms for the same cooling setting. Both graph versions are displayed.',maxh=88)
fig('13_transient_energy','Figure 14. Actual paceval-computed cumulative per-switch electrical-loss energy along the second controlled drive waveform.',maxh=88)
pb()
# 13 proofs.
title('12. Independent verification and reproducibility')
para('The production C++ binary uses persistent graphs and both multigraph and scalar paceval APIs. A separate Python program independently derives the stationary electrothermal reference by solving the polynomial balance in terms of ΔT = Tj − 25. The v1 model is linear in ΔT; v2 is quadratic. The reference also reconstructs all reported losses, margins, sensitivities, 0/1 guards and host classifications, and independently propagates every recorded transient trajectory.')
section('Completed tests')
tbl(['Validation stage','Recorded result'],[
 ('Independent complete stationary results',f'{a["native_scalar_checks"]:,} scalar fields passed'),
 ('Independent transient evolution',f'{a["full_trajectory_checks"]:,} state/power/energy checks passed'),
 ('Independent 80-decimal high-precision sub-study',f'{a["high_precision_checks_80digit"]:,} checks passed'),
 ('Both model versions / domain exclusions','Independently checked against explicit root domains'),
 ('Engineering graph-chain trace','One complete per-version calculation from unchanged CSV input'),
 ('Input / API failure paths','Strict CSV schema, operator semantics and bad-input tests'),
 ('Complete graph registry',f'{e["created_graphs"]:,} actual parser expressions and graph IDs')],widths=[W*.53,W*.47])
para('Detailed tolerances and numerical discrepancies are kept in the technical audit files, not reproduced as engine-comparison charts in this scientific report. A finite successful test campaign establishes correctness for its declared cases, not a general proof over all semiconductor operating regimes.')
section('Available reproducibility materials')
para('The ZIP includes the complete C++17 source, original SDK header and API wrapper source, a CMake project, generated CSV inputs and executed outputs, formula inventory, machine-readable execution manifest, two independent calculation traces, Python reference and scientific figure-generation scripts. A compatible Linux shared library must be supplied separately and is never redistributed. The included build instructions support both a small test run and the complete 100,000-point reproduction.')
spacer(4)
para('Source links and exact filenames are provided in README.md. The linked research articles establish relevance but are not represented as independent verification of this synthetic paceval study.','small')
pb()
# 14 limits and sources.
title('13. Scientific limitations and industrial next step')
para('This demonstrator computes <b>one switch-equivalent averaged model</b>. Its loss-energy coefficients, temperature dependences, voltage/current scalings, ambient conditions, effective thermal resistances and quality thresholds are synthetic. In particular, it does not simulate PWM current paths in individual MOSFETs, dead-time and diode conduction in a six-switch bridge, measured switching transients, gate-driver losses, module heat spreading, heatsink thermal dynamics, reliability, power-cycle lifetime or inverter-wide efficiency.')
para('The thermal root solver only searches the declared interval from ambient temperature to 250 °C. The separate illustrative engineering limit of 170 °C is a chosen model parameter, not a device rating or permission to operate a semiconductor at that value. A rejected root outside the search domain is not a proof of physical thermal runaway. The 1-node thermal transition is an explicit illustrative state model, not a calibrated impedance spectrum. No TINC interval guarantee, regulatory qualification, hard real-time safety function or external industrial deployment was tested.')
section('Next experimental step')
para('For an industrial pilot, characterize a named inverter semiconductor module with documented manufacturer permission, reconstruct its on-state resistance and Eon/Eoff surfaces over current, voltage, temperature and gate-drive conditions, incorporate a multi-node or measured transient thermal impedance, and validate predicted junction temperature and switching-energy changes on independently held-out measurements. The paceval execution-graph architecture can then preserve versioned formulas, margins and sensitivities while the host handles device provenance, safety logic and configuration control.')
section('External scientific and technical references')
references=[
 '[1] C. Bianchini et al. (2025). Switching Loss Model for SiC MOSFETs Based on Datasheet Parameters Enabling Virtual Junction Temperature Estimation. Sensors 25(12), 3605. https://doi.org/10.3390/s25123605',
 '[2] Infineon (2024). Estimating SiC MOSFET switching losses in applications. https://community.infineon.com/t5/Knowledge-Base-Articles/Estimating-SiC-MOSFET-switching-losses-in-applications/ta-p/709113',
 '[3] Infineon. CoolSiC 1200 V G2 application note, switching energy as function of temperature. https://www.infineon.com/assets/row/public/documents/24/42/infineon-coolsic-1200v-g2-mosfet-in-a-to263-7-package-applicationnotes-en.pdf',
 '[4] An Online Junction Temperature Estimation Method for SiC Inverter Considering Surge Avoidance (2026). https://doi.org/10.1049/pel2.70278',
 '[5] R. Drummond et al. (2026). Application-representative high-frequency power cycling of SiC power modules used in inverters and rectifiers. https://doi.org/10.1016/j.microrel.2026.115997',
 '[6] paceval mathematical engine official C/C++ API and product brief. https://paceval.com/api/; https://paceval.com/product-brief/'
]
for r in references:para(r,'tiny')
spacer(3)
para('Conclusion: actual reusable paceval execution graphs support the complete, defined synthetic electrothermal loss, balance, margin, sensitivity and state-update chain, and the resulting study is reproducible and independently checked. Commercial device applicability requires a different, externally characterized validation stage.','small')

doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('Wrote',OUT)
