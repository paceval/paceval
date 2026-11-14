#!/usr/bin/env python3
"""Generate standalone English scientific PDF from verified original paceval data.
The eleven figure files were produced by scripts/make_figures.py from original
C++/paceval outputs. Publication never substitutes high-precision reference data.
"""
import json,csv
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether,HRFlowable
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from PIL import Image as PILImage
ROOT=Path(__file__).resolve().parents[1]
FIG=ROOT/'figures';OUT=ROOT/'paceval_Electric_Motor_Efficiency_Field_Weakening_Whitepaper_EN.pdf'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
for n,f in [('DejaVu',font),('DejaVuBold',bold)]:pdfmetrics.registerFont(TTFont(n,f))
NAVY=colors.HexColor('#152C40');BLUE=colors.HexColor('#22708A');MUTED=colors.HexColor('#52606B');PALE=colors.HexColor('#F0F5F7')
styles={
 'title':ParagraphStyle('title',fontName='DejaVuBold',fontSize=22,leading=28,textColor=NAVY,spaceAfter=16),
 'subtitle':ParagraphStyle('subtitle',fontName='DejaVu',fontSize=12,leading=18,textColor=BLUE,spaceAfter=18),
 'h':ParagraphStyle('h',fontName='DejaVuBold',fontSize=15.5,leading=21,textColor=NAVY,spaceBefore=8,spaceAfter=12),
 'h2':ParagraphStyle('h2',fontName='DejaVuBold',fontSize=11.2,leading=16,textColor=BLUE,spaceBefore=12,spaceAfter=8),
 'body':ParagraphStyle('body',fontName='DejaVu',fontSize=9.1,leading=15.1,textColor=NAVY,spaceAfter=10),
 'small':ParagraphStyle('small',fontName='DejaVu',fontSize=8.1,leading=13,textColor=MUTED,spaceAfter=8),
 'caption':ParagraphStyle('caption',fontName='DejaVu',fontSize=8.6,leading=13,textColor=MUTED,spaceAfter=12),
 'equation':ParagraphStyle('equation',fontName='DejaVu',fontSize=10,leading=19,textColor=NAVY,leftIndent=14,spaceAfter=12),
 'tabh':ParagraphStyle('tabh',fontName='DejaVuBold',fontSize=8.4,leading=12,textColor=colors.white),
 'tab':ParagraphStyle('tab',fontName='DejaVu',fontSize=8.0,leading=12,textColor=NAVY),
}
W,H=A4
DOC=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=62,bottomMargin=51,title='Electric Motor Efficiency and Field-Weakening Maps with paceval',author='paceval industrial mathematical research',subject='IPMSM synthetic mathematical functionality with original paceval engine')
ST=[]
def p(t,style='body'):ST.append(Paragraph(t,styles[style]))
def heading(t):p(t,'h')
def sub(t):p(t,'h2')
def page():ST.append(PageBreak())
def tbl(rows,widths=None):
  data=[[Paragraph(str(cell),styles['tabh'] if r==0 else styles['tab']) for cell in row] for r,row in enumerate(rows)]
  t=Table(data,colWidths=widths or [DOC.width/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#D7E1E4'))]))
  ST.append(t);ST.append(Spacer(1,14))
def fig(number,name,title,caption):
  path=FIG/name
  with PILImage.open(path) as im: w,h=im.size
  img=Image(str(path),width=DOC.width,height=DOC.width*h/w)
  desc=Paragraph(f'<b>Figure {number}.</b> {caption}',styles['caption'])
  ST.append(KeepTogether([Paragraph(title,styles['h2']),Spacer(1,2),img,Spacer(1,8),desc]))
def frame(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#DDE6E8'));canvas.line(50,47,W-50,47)
 canvas.setFont('DejaVu',7.5);canvas.setFillColor(MUTED)
 canvas.drawString(50,34,'paceval · Independent mathematical research · 14 November 2026')
 canvas.drawRightString(W-50,34,str(doc.page))
 canvas.restoreState()
exec_info=json.loads((ROOT/'results/execution_evidence.json').read_text())
audit=json.loads((ROOT/'results/scientific_audit.json').read_text())
with (ROOT/'results/torque_speed_envelope.csv').open(newline='') as f:envelopes=list(csv.DictReader(f))
def lookup(v,t,r):
 return next(float(x['max_feasible_torque_Nm']) for x in envelopes if (x['model'],x['temperature_C'],x['speed_rpm'])==(str(v),str(t),str(r)))
# COVER
ST.append(Spacer(1,21));p('PACEVAL · INDUSTRIAL RESEARCH / WP 10','subtitle')
p('Electric Motor Efficiency and<br/>Field-Weakening Maps','title')
p('A verified, reproducible IPMSM mathematical execution-graph demonstrator','subtitle')
img=Image(str(FIG/'00_electric_motor_hero.png'),width=DOC.width,height=DOC.width/2);ST.append(img)
p('Concept illustration; not a computed research result.','caption')
ST.append(Spacer(1,10))
p('<b>Research scope.</b> Temperature-aware stationary synchronous-motor torque, loss, voltage and efficiency maps, computed with the original paceval SDK 4.25 and checked by independently implemented numerical references.')
p('<b>Evidence.</b> '+str(exec_info['unique_domain_graphs_executed'])+' genuine research graphs executed; '+str(exec_info['scenario_count'])+' distinct synthetic operating inputs; two simultaneously available model versions; '+str(audit['independent_numeric_checks'])+' independent high-precision numerical checks.')
p('<b>Publication status.</b> Original Linux C++ execution and technical audit completed. Synthetic mathematical screening only, not an industrial performance rating, FEA model, inverter controller or motor certification.','small')
page()
# INTRO
heading('1. Industrial problem and research objective')
p('An electric-traction or industrial-drive engineering team needs to determine the available torque and the motor operating range across speed, stator current, inverter voltage and temperature. The current vector may be optimal at low speed but violate the voltage limit at high speed. Motor losses and winding/magnet temperature also alter the operating map. This research isolates the explicit mathematical functions needed for these decisions and executes them as reusable paceval computation graphs.')
p('The industrial workflow normally links electromagnetic geometry and material identification, flux/inductance characterization, current reference generation, inverter constraints, thermal analysis and motor-inverter measurements. The present study is an intentionally bounded analytical screening stage that can precede, but not replace, field characterization and dynamometer validation.')
sub('Operational example')
p('Consider a hypothetical IPMSM driven from a 600 V DC link. For each speed, the engineering program explores negative d-axis and nonnegative q-axis peak currents, calculates torque, voltage and losses, and excludes operating points that violate either physical limit. It then reports the highest sampled feasible torque and a separate torque-qualified efficiency selection. At elevated assumed temperature it compares the baseline motor parameters with modified stator resistance and permanent-magnet flux linkage.')
sub('MTPA, field weakening, and the upper-speed region')
p('MTPA maximizes torque for a current magnitude or minimizes current for a torque request, depending on its formulation. As the electrical frequency rises, the voltage ellipse shrinks; negative d-axis current reduces net d-flux and may permit additional speed. At very high speed, maximum torque per voltage and other constraints may become relevant. In this study, the solver is deliberately a finite-grid selector. It does not claim continuous MTPA/MTPV optimality or real-time controller performance. The terminology and constraints are established in references [1], [2], [7] and [8].')
sub('Current research and established tooling')
p('MathWorks Motor Control Blockset provides documented field-weakening/MTPA operating examples and synchronous-frame current and voltage constraints [1–2]. FEM-parameterized motor modeling explicitly separates resistive, iron and mechanical losses [6]. Recent 2026 multiphysics work combines magnetic saturation, thermal field information and driving-cycle analysis [3–4]. The 2024 NHTSA analysis adopts characterized speed–torque machine efficiency maps [5]. This study instead demonstrates the analytical mathematical subfunctions with independent numerical scrutiny.')
page()
# MODEL
heading('2. Mathematical models, units and physical limits')
p('Both versions are balanced three-phase, sinusoidal, quasi-steady IPMSM models. Currents and voltages use <b>peak-value rotor synchronous-frame</b> conventions, p denotes pole pairs, inductances are fixed in the demonstrated domain, and the DC-to-AC voltage limit uses linear-SVPWM conventions.')
sub('Flux, terminal voltage and electromagnetic torque')
p('ω<sub>m</sub> = 2πn/60;  ω<sub>e</sub> = pω<sub>m</sub>;  ψ<sub>d</sub> = ψ<sub>PM</sub> + L<sub>d</sub>i<sub>d</sub>;  ψ<sub>q</sub> = L<sub>q</sub>i<sub>q</sub>.','equation')
p('v<sub>d</sub> = R<sub>s</sub>i<sub>d</sub> − ω<sub>e</sub>ψ<sub>q</sub>;  v<sub>q</sub> = R<sub>s</sub>i<sub>q</sub> + ω<sub>e</sub>ψ<sub>d</sub>.','equation')
p('T<sub>e</sub> = (3/2)p(ψ<sub>d</sub>i<sub>q</sub> − ψ<sub>q</sub>i<sub>d</sub>) = (3/2)p[ψ<sub>PM</sub>+(L<sub>d</sub>−L<sub>q</sub>)i<sub>d</sub>]i<sub>q</sub>.','equation')
sub('Voltage and current feasibility')
p('g<sub>I</sub> = I<sub>max</sub>² − i<sub>d</sub>² − i<sub>q</sub>² ≥ 0,  in A².','equation')
p('g<sub>V</sub> = (V<sub>dc</sub>/√3)² − v<sub>d</sub>² − v<sub>q</sub>² ≥ 0,  in V².','equation')
p('The code obtains g<sub>I</sub>, g<sub>V</sub>, and their compound logical AND directly from persistent paceval graphs. The host checks finite inputs and verifies the result-array error codes before determining which vectors are eligible for ranking.')
sub('Two simultaneously accessible formula versions')
p('<b>V1:</b> Constant R<sub>s</sub> = R<sub>s,25</sub> and ψ<sub>PM</sub> = ψ<sub>25</sub>, irrespective of the temperature column. <b>V2:</b> R<sub>s</sub>(T) = R<sub>s,25</sub>[1+α<sub>R</sub>(T−T<sub>ref</sub>)] and ψ<sub>PM</sub>(T) = ψ<sub>25</sub>[1+β<sub>ψ</sub>(T−T<sub>ref</sub>)]. These are separate actual formula handles. They use the same 25°C reference values.')
page()
heading('3. Losses, efficiencies and sensitivities')
p('The loss submodel is explicitly a synthetic functional proxy. It does not reproduce iron-lamination hysteresis, PWM harmonic loss, bearing measurements or real machine loss coefficients without external parameter identification.')
p('Copper: P<sub>Cu</sub> = 1.5 R<sub>s</sub>(i<sub>d</sub>²+i<sub>q</sub>²). Illustrative iron: P<sub>Fe</sub> = k<sub>Fe</sub>ω<sub>e</sub>²(ψ<sub>d</sub>²+ψ<sub>q</sub>²). Mechanical: P<sub>mech,loss</sub> = k<sub>mech</sub>ω<sub>m</sub>².','equation')
p('The estimated electromagnetic power is P<sub>em</sub> = T<sub>e</sub>ω<sub>m</sub>; shaft power is P<sub>shaft</sub> = P<sub>em</sub>−P<sub>mech,loss</sub>; and electrical input is P<sub>in</sub> = P<sub>em</sub>+P<sub>Cu</sub>+P<sub>Fe</sub>. The displayed motoring efficiency uses max(P<sub>shaft</sub>,0)/max(P<sub>in</sub>,10<super>−9</super> W). The idle and non-motoring convention avoids undefined ratios but must not be mistaken for measured efficiency.')
sub('Analytical sensitivity graphs')
p('The demonstrated partial derivatives include ∂T<sub>e</sub>/∂i<sub>d</sub> = (3/2)p(L<sub>d</sub>−L<sub>q</sub>)i<sub>q</sub> and ∂T<sub>e</sub>/∂i<sub>q</sub> = (3/2)p[ψ<sub>PM</sub>+(L<sub>d</sub>−L<sub>q</sub>)i<sub>d</sub>]. Both partial derivatives of squared voltage with respect to current are explicitly represented as paceval graph expressions. Temperature derivatives of torque and copper loss are version-specific.')
sub('Where paceval ends and the C++ host begins')
p('The 64 model expressions include flux, torque, voltage, losses, margins, composite logical feasibility, score and sensitivities. Five more graphs compare temperature-model results. C++ is responsible only for CSV schema checks, persistent handle management, batch grouping, selection over a finite candidate set, audit orchestration and file output. An independent native C++ implementation and a 90-digit Python reference are used only to verify the original paceval results.')
page()
heading('4. Complete execution evidence and study design')
p('The research first registers each exact mathematical expression with the original SDK. The registered graph handles are reused for all independent operating vectors. Multi-graph batch input/output arrangements were checked against a known-answer layout test; item-level error codes and finite values were checked on every graph result. This is a verified local C++ SDK execution and not a remote MCP experiment.')
tbl([['Evidence field','Actual verified value'],['Domain graphs created and executed',str(exec_info['unique_domain_graphs_executed'])+' / '+str(exec_info['unique_domain_graphs_created'])],['Distinct synthetic operating inputs',str(exec_info['scenario_count'])],['Motor version–scenario combinations',str(exec_info['model_scenario_count'])],['Independent native scalar endvalue checks',str(exec_info['independent_native_reference_checks'])],['Independently high-precision-checked rows',str(audit['high_precision_sampled_scenario_versions'])],['Independent high-precision numeric checks',str(audit['independent_numeric_checks'])]],widths=[DOC.width*.65,DOC.width*.35])
p('Research input covers 25°C and 110°C, speeds from 0 to 10,500 rpm in steps of 500 rpm, d-axis currents from −240 A to 0 A in steps of 12 A and q-axis currents from 0 A to 240 A in steps of 12 A. A fixed, documented table of phase resistance, magnet flux linkage, machine inductances, pole pairs, voltage limit and loss coefficients is shipped with the repository. Units and input schema constraints are defined in <b>input/SCHEMA.md</b>.')
p('The discrete output quantities are the maximum available torque for each speed/temperature/version group and the highest evaluated motoring shaft efficiency among feasible current vectors satisfying 120 N m. These maxima are <b>within the enumerated grid only</b>; they cannot be promoted to a global continuous optimizer guarantee.')
page()
heading('5. Reproduced functional motor-map results')
p('At the 110°C synthetic condition, changing the resistance and magnet-flux correlations alters both the electromagnetic torque and the voltage-constrained feasible currents. The following figures are from executed original paceval outputs, with host selection from those same outputs.')
tbl([['Speed','V1 constant parameter','V2 temperature-aware'],['3,000 rpm',f'{lookup(1,110,3000):.2f} N m',f'{lookup(2,110,3000):.2f} N m'],['5,000 rpm',f'{lookup(1,110,5000):.2f} N m',f'{lookup(2,110,5000):.2f} N m'],['9,000 rpm',f'{lookup(1,110,9000):.2f} N m',f'{lookup(2,110,9000):.2f} N m'],['10,000 rpm',f'{lookup(1,110,10000):.2f} N m',f'{lookup(2,110,10000):.2f} N m']],widths=[DOC.width*.25,DOC.width*.375,DOC.width*.375])
p('At low speed, the temperature-aware synthetic model has reduced permanent-magnet torque. At high speed, the reduced magnet flux can change the voltage-constraint geometry and therefore sometimes admit a different larger q-axis current. This can cause the two curves to cross, even though a stronger magnet was beneficial at low speed. The pattern is conditional on the numerical parameter set, fixed inductances, finite current grid and assumed temperature correlations.')
p('At 25°C, both models recover the same reference parameters and their graphs give coincident operating envelopes. The independent high-precision verification explicitly checks the 25°C baseline and model deltas. Research figures 01–11 illustrate the current-limited and voltage-limited regions, losses, sensitivity, and model-dependent behavior. The term “efficiency” in this document always refers to the declared <b>motor-only surrogate</b>, not an inverter-inclusive measured system efficiency.')
page()
# Figures: paired on six pages
names=[
 ('fig01_torque_speed_envelope.png','Constrained torque–speed operating envelopes','V1/V2 comparisons at 25°C and 110°C; torque values are selected from feasible paceval-evaluated current vectors.'),
 ('fig02_field_weakening_current.png','Field-weakening d-axis current commands','Selected d-axis current grows more negative as speed approaches voltage limits; selection is grid-limited.'),
 ('fig03_efficiency_map.png','Motor-only efficiency over the torque–speed plane','Highest observed shaft-efficiency value per sampled torque–speed bin in the hot V2 model; blank bins have no admissible motor point.'),
 ('fig04_current_plane_feasibility.png','Current and voltage feasible operating regions','The actual paceval logical guard identifies current vectors satisfying both limits at two mechanical speeds.'),
 ('fig05_loss_decomposition.png','Copper, iron and mechanical loss components','True evaluated paceval loss results along the V2 110°C maximum-torque finite-grid trajectory; loss coefficients remain synthetic.'),
 ('fig06_voltage_limit_utilization.png','Voltage utilization through the operating range','Voltage requirement divided by the assumed available peak vector; unity is the boundary.'),
 ('fig07_temperature_model_delta.png','Temperature-dependent torque model difference','At fixed currents, compare V2 minus V1 torque at two specified temperatures; this is a physical model change, not a software-engine discrepancy.'),
 ('fig08_envelope_torque_and_power.png','Torque and electromagnetic power at high temperature','Both torque and electromagnetic power are actual paceval graph results; the latter is not shaft output after mechanical losses.'),
 ('fig09_target_torque_optimal_efficiency.png','Torque-qualified efficiency choice','Among finite-grid feasible points producing at least 120 N m, the best synthetic shaft-efficiency candidate is selected.'),
 ('fig10_3d_torque_current_surface.png','Three-dimensional torque function over d/q currents','The full computed mathematical surface is shown without excluding infeasible points; physical admissibility must be checked with separate guard graphs.'),
 ('fig11_torque_sensitivities.png','Analytical current sensitivities','Explicit, separately registered paceval analytical derivatives at selected temperature-aware operating states.'),
]
for k in range(0,10,2):
 heading('6. Scientific result visualizations' if k==0 else 'Scientific result visualizations · continued')
 for j in (k,k+1):fig(j+1,*names[j]);
 page()
heading('7. 3D surface, analytical gradients and scientific audit')
fig(11,*names[10])
p('An independent Python mpmath implementation at 90 decimal digits checks the declared physical balances and derived end values. It reads recorded original paceval output CSV files; it never replaces them with freshly generated reference results. The technical verification also independently checks the discrete envelope and torque-qualified efficiency selection.')
page()
heading('8. Verification status and scientific limitations')
p('The shipped C++ source was compiled with the original supplied paceval 4.25 SDK and a compatible Linux shared library. A self-test checks real scalar and multi-graph execution, the numeric string converter, the exact logic/relational operators, signed modulo semantics, zeros, reference model values and the temperature correlations. The main input pipeline checks strict decimal-literal CSV grammar before any numeric parsing. Exact output byte-reproduction is verified separately using output file hashes, if rerun in the same environment.')
tbl([['Validation component','Observed result'],['Original SDK mathematical graphs',f'{exec_info["unique_domain_graphs_executed"]} of {exec_info["unique_domain_graphs_created"]} executed'],['Native C++ independent evaluations',str(exec_info['independent_native_reference_checks'])+' numeric checks'],['90-digit mpmath reference',str(audit['independent_numeric_checks'])+' checks, all passed'],['Temperature baseline / model deltas','Passed against the predefined reference'],['Finite-grid maxima and torque-qualified efficiency','Verified independently from output CSV']],widths=[DOC.width*.56,DOC.width*.44])
sub('Limits of scientific interpretation')
p('Neither constant Ld/Lq IPMSM equations nor a simple quadratic iron-loss proxy represent magnetic saturation, cross-saturation, harmonic losses or demagnetization protection. Thermal fields, inverter semiconductor losses, regeneration and transient dynamics are not modeled. The 2026 specialist literature combines finite-element, empirical and dynamometer data to overcome these limitations [3–4,6]. Therefore the verified result is <b>mathematical-function execution and reproducibility</b>, not a proof that the predicted efficiency/field-weakening curves match any production motor.')
sub('Proposed next experiment')
p('Replace the symbolic fixed parameters with identified flux surfaces ψd(id,iq,T), ψq(id,iq,T), temperature-dependent phase resistance and measured motor/inverter loss data. Compare operating points against an independent finite-element/machine-characterization reference under a documented uncertainty budget. Extend the host search to smooth continuous optimization only after validating convergence and the physical constraint surface. A separate project would be required to validate real-time controls or hardware acceleration.')
page()
heading('9. Selected references and provenance')
refs=[
('1','MathWorks, Field-Weakening Control (with MTPA) of PMSM. R2026b documentation.','https://www.mathworks.com/help/mcb/gs/field-weakening-control-mtpa-pmsm.html'),
('2','MathWorks, PMSM Constraint Curves and Their Application.','https://www.mathworks.com/help/mcb/gs/pmsm-constraint-curves-and-their-application.html'),
('3','Applied Sciences (2026), Integrated Multiphysics and WLTP-Based Evaluation of a 130 kW IPMSM.','https://www.mdpi.com/2076-3417/16/11/5589'),
('4','Scientific Reports (2026), Evaluation of electric vehicle performance using motor-inverter losses and efficiency.','https://www.nature.com/articles/s41598-026-36663-3'),
('5','NHTSA (2024), CAFE Final Technical Support Document, electric motor efficiency map sources.','https://www.nhtsa.gov/sites/nhtsa.gov/files/2024-06/CAFE-2027-2031-HDPUV-2030-2035_Final-Technical-Support-Document.pdf'),
('6','MathWorks, FEM-Parameterized PMSM reference documentation.','https://www.mathworks.com/help/simscape-electrical/ref/femparameterizedpmsm.html'),
('7','Energies (2022), A Review about Flux-Weakening Operating Limits and Control Techniques.','https://www.mdpi.com/1996-1073/15/5/1930'),
('8','Electronics (2025), Flux-Weakening Control Methods for PMSM Machines at High Speed.','https://www.mdpi.com/2079-9292/14/19/3779'),
('9','paceval API reference and Product Brief.','https://paceval.com/api/'),
]
for n,t,u in refs:p(f'<b>[{n}]</b> {t}<br/><link href="{u}" color="#22708A">{u}</link>','small')
ST.append(HRFlowable(width='100%',thickness=0.4,color=colors.HexColor('#CFDADE'),spaceBefore=14,spaceAfter=14))
p('<b>Original data and reproducibility.</b> The code, source citations, real paceval CSV outputs, full formula inventory, scalar/batch API checks, native and high-precision audit traces, input schemas, all plotted figures, and independent rebuild procedures are contained in the companion ZIP. The original runtime library is not redistributed in the archive.')
p('<b>Publication and figure provenance.</b> All input parameters are synthetic and were chosen to illustrate a bounded analytical research demonstrator. The hero image is a concept illustration. Figures 1–11 were produced from genuine executed paceval C++ outputs using the shipped Python plotting script. No external photographs or downloaded images are represented as scientific calculations. Prepared 14 November 2026.','small')
DOC.build(ST,onFirstPage=frame,onLaterPages=frame)
print('GENERATED',OUT,'bytes',OUT.stat().st_size)
