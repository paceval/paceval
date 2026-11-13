"""Research-grade English PDF; figures are from recorded real paceval outputs.
Requires reportlab and matplotlib only for document publishing.
"""
from pathlib import Path
import os, math, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.platypus import (BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,Image,PageBreak,Table,TableStyle,KeepTogether,HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT,TA_CENTER,TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).resolve().parents[1];F=R/'figures';OUT=R/'paceval_Industrial_Piecewise_Calibration_Whitepaper_EN.pdf'
for name,fn in [('Lato','Lato-Regular.ttf'),('Lato-Bold','Lato-Bold.ttf'),('Lato-Italic','Lato-Italic.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/lato/'+fn))
W,H=A4;blue=colors.HexColor('#1C4769');orange=colors.HexColor('#E06A34');navy=colors.HexColor('#172D40');teal=colors.HexColor('#2A8C84');muted=colors.HexColor('#637584')
styles={
 'title':ParagraphStyle('title',fontName='Lato-Bold',fontSize=28,leading=31,textColor=navy,spaceAfter=10),
 'subtitle':ParagraphStyle('subtitle',fontName='Lato',fontSize=13.4,leading=19,textColor=blue,spaceAfter=18),
 'h1':ParagraphStyle('h1',fontName='Lato-Bold',fontSize=16.2,leading=20,textColor=navy,spaceBefore=0,spaceAfter=11),
 'h2':ParagraphStyle('h2',fontName='Lato-Bold',fontSize=12.4,leading=16,textColor=blue,spaceBefore=14,spaceAfter=8),
 'body':ParagraphStyle('body',fontName='Lato',fontSize=10.1,leading=15.1,textColor=navy,spaceAfter=9),
 'small':ParagraphStyle('small',fontName='Lato',fontSize=8.8,leading=12.3,textColor=navy,spaceAfter=7),
 'caption':ParagraphStyle('caption',fontName='Lato-Italic',fontSize=8.5,leading=11.5,textColor=muted,spaceBefore=7,spaceAfter=11),
 'call':ParagraphStyle('call',fontName='Lato-Bold',fontSize=9.6,leading=14,textColor=blue,spaceBefore=8,spaceAfter=8),
 'source':ParagraphStyle('source',fontName='Lato',fontSize=8.9,leading=13.8,textColor=navy,spaceAfter=10),
}
class PageDoc(BaseDocTemplate):pass
D=PageDoc(str(OUT),pagesize=A4,leftMargin=49,rightMargin=49,topMargin=66,bottomMargin=49,title='Industrial Calibration at Formula Scale with paceval',author='paceval scientific feasibility research',subject='Executed long piecewise mathematical calibration graphs and independent validation')
frame=Frame(49,48,W-98,H-113,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
def painter(c,d):
    c.saveState()
    if d.page>1:
        c.setFillColor(navy);c.setFont('Lato-Bold',10.5);c.drawString(49,H-36,'paceval.')
        c.setFillColor(muted);c.setFont('Lato',8.5);c.drawRightString(W-49,H-36,'Industrial Calibration at Formula Scale')
        c.setStrokeColor(colors.HexColor('#D5E2E9'));c.setLineWidth(.65);c.line(49,H-45,W-49,H-45)
    c.setStrokeColor(colors.HexColor('#D5E2E9'));c.line(49,42,W-49,42)
    c.setFont('Lato',8);c.setFillColor(muted)
    c.drawString(49,27,'Independent scientific functionality demonstrator  |  13 November 2026')
    c.drawRightString(W-49,27,str(d.page))
    c.restoreState()
D.addPageTemplates(PageTemplate(id='normal',frames=frame,onPage=painter))
def P(s,st='body'):return Paragraph(s,styles[st])
def Heading(n,s):return P(f'{n}  {s}','h1')
def line():return HRFlowable(width='100%',thickness=.7,color=colors.HexColor('#D7E4EB'),spaceBefore=10,spaceAfter=14)
def image(name,maxw=495,maxh=340):
    from PIL import Image as PIL
    p=F/name
    with PIL.open(p) as im:w,h=im.size
    f=min(maxw/w,maxh/h)
    return Image(str(p),width=w*f,height=h*f)
def fig(name,caption,maxh=320):return [image(name,maxh=maxh),P(caption,'caption')]
def table(items,widths=None,head=True):
    dat=[[P(str(v),'small') for v in row] for row in items]
    t=Table(dat,colWidths=widths if widths else [(W-98)/len(dat[0])]*len(dat[0]),hAlign='LEFT',repeatRows=1 if head else 0)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EDF4F7')) if head else ('BACKGROUND',(0,0),(-1,-1),colors.white),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F7F9FB')]),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('LINEBELOW',(0,0),(-1,0),.8,blue),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#E5ECEF')),
    ]))
    return t

def equation(name,latex):
    f=plt.figure(figsize=(10,1.36 if name=='math_corr.png' else 1.12),facecolor='white');ax=f.add_axes([0,0,1,1]);ax.axis('off')
    if name=='math_corr.png':
        ax.text(.035,.72,r'$G_v=S_v(x)[1+0.00035(T-20)]+0.0005(T-20)$',va='center',ha='left',fontsize=16,color='#173E60')
        ax.text(.035,.23,r'$\quad+0.000075\sin(7x)(T-20)+d(0.001+0.0015x)$',va='center',ha='left',fontsize=16,color='#173E60')
    else:ax.text(.04,.5,'$'+latex+'$',va='center',ha='left',fontsize=16,color='#173E60')
    f.savefig(F/name,dpi=180,facecolor='white');plt.close(f)
equation('math_piecewise.png',r'S_v(x)=y_{i,v}+\frac{y_{i+1,v}-y_{i,v}}{x_{i+1}-x_i}(x-x_i)')
equation('math_corr.png',r'G_v=S_v(x)[1+0.00035(T-20)]+0.0005(T-20)+0.000075\sin(7x)(T-20)+d(0.001+0.0015x)')
equation('math_unc.png',r'u_G=\sqrt{(G_x u_x)^2+(G_Tu_T)^2+(G_du_d)^2+u_{model}^2}')
equation('math_margin.png',r'm_{accept}=t-|G-r|-2u_G\quad ;\quad m_{reject}=t-|G-r|+2u_G')

s=[]
# 1 cover
s += [Spacer(1,20),P('paceval.  |  SCIENTIFIC FUNCTIONALITY STUDY','call'),
P('Industrial Calibration<br/>at Formula Scale','title'),
P('Long Piecewise Mathematical Functions, Versioned Execution Graphs and Auditable Mathematical Quality Margins','subtitle'),
image('00_calibration_hero.png',maxw=495,maxh=265),Spacer(1,16),
P('<b>13 November 2026</b>  |  English research report  |  Real paceval SDK 4.25 execution','small'),line(),
P('<b>Scientific claim.</b> This demonstrator establishes mathematical feasibility: a compatible paceval Linux runtime created and executed 121 persistent graphs for two 4,096-interval calibration models, and 569 graphs for two 65,536-interval models. Each execution was checked independently. No real measurement traceability, product certification, instrument accuracy or hardware acceleration is claimed.'),
P('The title image is an editorial scientific illustration, not a photograph of tested laboratory equipment.','caption'),PageBreak()]
#2
s += [Heading('01','Research question and industrial scope'),
P('Can an industrial host use one versioned mathematical execution layer to evaluate <b>large sensor transfer functions</b>, temperature and drift corrections, analytical sensitivities, uncertainty expressions and auditable quality-decision margins without rewriting its supervisory code when a calibration formula changes?'),
P('The predecessor study already established a longer than seven-million-character piecewise formula and modular 65,536-segment execution. This expanded study concentrates on a complete <b>functional chain</b>, preserving two versions simultaneously and checking both over synthetic sensor inputs.'),
P('The chosen first application is read-only, non-safety-critical machine-axis and precision-sensor correction. Control actuation, true device calibration and decisions with safety consequences are excluded.'),
*fig('01_executed_architecture.png','Figure 1. Verified execution responsibilities. Formula computation and mathematical guard margins are inside paceval. The C++ program handles input validation, routing, independent reference checks and status selection.',maxh=245),
P('The literature distinguishes mathematical calibration algorithms from metrological traceability. NIST requires a documented calibration chain and associated uncertainty; IEC 61298-2:2026 covers designated reference-condition performance testing but excludes process measurement transmitters [2, 3].','small'),PageBreak()]
#3
s += [Heading('02','Model definition and endpoint ownership'),
P('The original three-point example is preserved as a real paceval scalar graph. It returns the expected values 6, 4.5, 3, 14 and 25 at inputs 1.5, 2.0, 2.5, 3.0 and 3.5 respectively. Its generalization uses a uniform piecewise-linear interpolation model for x in [0, 1].'),
image('math_piecewise.png',maxh=60),
P('The data knots are synthetic samples of an explicitly stated oscillatory function. Model v2 modifies model v1 by 0.002 sin(5x) + 0.001x. For all but the final interval, each knot belongs to the segment on its right; the final interval owns x = 1. Out-of-range and nonfinite inputs are rejected before graph evaluation.'),
*fig('02_versioned_calibration_curves.png','Figure 2. The two models can be created, retained and executed independently through persistent paceval handles; both curves are shown at T = 30 °C.',maxh=255),
P('Model revision here means a controlled mathematical parameter change, not recalibration of physical equipment.'),PageBreak()]
#4
s += [Heading('03','Temperature and drift compensation'),
P('Industrial calibration often involves operating conditions besides the raw sensor reading. The demonstrator composes the interpolated value with explicitly synthetic temperature and drift corrections, without replacing the surrounding control and measurement infrastructure.'),
image('math_corr.png',maxh=80),
P('This is a version-independent formula graph that receives the version-specific interpolant S and local slope from the routed paceval segment graphs. The input domain is 0 to 60 °C and normalized drift from -1 to 1. All numeric coefficients are illustrative and dimensionless.'),
*fig('03_temperature_compensation.png','Figure 3. Real paceval evaluations of the corrected v1 output at different synthetic operating temperatures. The distinct curves demonstrate a combined reusable mathematical expression.',maxh=260),PageBreak()]
#5
s += [Heading('04','Full two-variable response surface'),
P('The graph registry contains the precise text of every executed formula. For scientific visualization, the C++ demonstrator evaluated the actual paceval functions on a declared 61 by 41 grid of raw signal and temperature values. No separate Python implementation was substituted to generate the plotted surface.'),
*fig('04_calibration_surface_3d.png','Figure 4. Corrected response surface from the original paceval SDK, model v1, normalized drift d = 0. The surface represents a constructed mathematical calibration model, not sensor measurements.',maxh=340),
P('For inspection and reproduction, the underlying data are stored in results/calibration_surface.csv. Identical equations and parameter values are used for the separate reference audit.'),PageBreak()]
#6
s += [Heading('05','Versioning, concurrent execution and rollback readiness'),
P('Both formula sets are active simultaneously. Each graph has a version identifier, role, mathematical expression, declared input schema and unit description. A version comparison is recorded for all 720 synthetic input samples. This demonstrates how a supervisory application can preserve earlier mathematical behavior while evaluating a revision.'),
*fig('05_formula_revision_delta.png','Figure 5. Differences between independently computed v2 and v1 corrected values at T = 30 °C. Neither curve is presented as a more accurate model.',maxh=265),
P('A production lifecycle would additionally require signed calibration artifacts, authorized approval, provenance, expiration policies, controlled activation, rollback and independent metrological requalification. The demonstrator does not claim to implement these operational mechanisms.'),PageBreak()]
#7
s += [Heading('06','Synthetic residuals and targeted anomaly scenarios'),
P('Four deterministic synthetic groups exercise different aspects of the formula execution: machine-axis correction, precision sensor, quality gate and temperature cycle. The quality-gate inputs contain deliberate artificial offsets to exercise all three decision states. There is no real sensor defect dataset.'),
*fig('06_quality_gate_residuals.png','Figure 6. Residuals from real paceval evaluation for the synthetic quality-gate scenario. Dashed lines show the illustrative raw tolerance; final decisions use uncertainty-aware margins.',maxh=300),
P('The reference signal originates from the source synthetic generating function and is deliberately perturbed by known artificial deviations. Thus these residuals are reproducible experiment inputs and not empirical measurement errors.'),PageBreak()]
#8
s += [Heading('07','First-order propagation of uncertainty'),
P('Three analytical sensitivity functions are represented as paceval mathematical graphs, along with the combined standard uncertainty below. Input uncertainty terms are assumed uncorrelated in this first research model. A real measurement chain requires a justified covariance structure and a validated model uncertainty budget.'),
image('math_unc.png',maxh=75),
*fig('07_uncertainty_and_acceptance_margin.png','Figure 7. Version v1: the calculated standard-uncertainty quantity and acceptance margin are separate real paceval outputs for the synthetic quality-gate scenario.',maxh=275),
P('These numbers do not establish coverage probability or traceable uncertainty. For non-smooth transfer functions, the local derivative at a knot is defined one-sided and is not a global differentiability certificate. This experiment does not enable TINC.'),PageBreak()]
#9
s += [Heading('08','Analytical sensitivities and piecewise boundaries'),
P('A piecewise-linear graph has an ordinary derivative inside each open segment, but not generally at the internal knots. This study declares a right-segment sensitivity convention for internal knots and a last-segment convention at x = 1. It is used consistently by the native reference and independent 80-digit audit.'),
*fig('08_local_piecewise_sensitivity.png','Figure 8. Local dG/dx at T = 30 °C. Visible changes follow the synthetic transfer-function structure and are computed from persistent paceval derivative graphs.',maxh=310),
P('For instruments requiring continuous first derivatives, a shape-preserving cubic Hermite interpolation may be a later model choice; SciPy documents PCHIP as shape-preserving and continuously first differentiable [5]. PCHIP is not implemented in this demonstrator.'),PageBreak()]
#10
s += [Heading('09','Mathematical quality decisions'),
P('The host does not invent a numeric safety decision. paceval evaluates residuals, the combined uncertainty and two explicit guard margins, after which the host performs only the three-way comparison.'),
image('math_margin.png',maxh=63),
P('<b>ACCEPT</b> if m_accept ≥ 0; <b>REJECT</b> if m_reject &lt; 0; otherwise <b>REVIEW</b>. The multiplier 2 is an arbitrary research policy parameter, not evidence of a metrological or statistical coverage guarantee.'),
*fig('09_model_version_decisions.png','Figure 9. Outcomes of 720 deterministic inputs evaluated independently in each model version. Each status is selected from actual paceval mathematical margins.',maxh=305),PageBreak()]
#11
s += [Heading('10','Governance score family'),
P('Beyond corrected measurements, the demonstrator constructs 16 different persistent composite score expressions per model version. Each score combines absolute residual, calculated uncertainty, local derivative sensitivity and operating drift using explicit versioned coefficients.'),
*fig('10_governance_score_families.png','Figure 10. Sixteen distinct graph expressions are evaluated for every synthetic input and version. These score values are not probabilities or approved industrial quality metrics.',maxh=315),
P('The score family shows how formula-governance requirements may be tested as mathematics without changing the C++ data acquisition or scheduling host. All generated strings are retained in results/graph_registry.csv.'),PageBreak()]
#12
s += [Heading('11','Large expression capacity and routed batch execution'),
P('The original historical report demonstrated a single 7,712,198-character monolithic function with 65,536 segments. Here we independently re-executed the full two-model framework at 65,536 segments per version, with 512 masked segments per graph, using persistent graph handles and routed single-graph batches.'),
*fig('11_verified_graph_capacity.png','Figure 11. 121 persistent computation objects for the primary 4,096-interval case and 569 for the dual-model 65,536-interval capacity case. This is a count of executed mathematical functionality, not a performance comparison.',maxh=300),
P('The 569-graph capacity run includes 512 interpolation and slope graphs, 56 postprocessing graphs, and one original three-point historical anchor. The independent 80-digit audit succeeded separately for this capacity run.'),PageBreak()]
#13
s += [Heading('12','Acceptance-margin surface and operating context'),
P('In addition to the calibrated response surface, a second actual paceval output grid shows how a synthetic tolerance policy interacts with a revised formula. This illustrates a mathematically explicit decision surface, not a validated threshold policy for any production machine.'),
*fig('12_acceptance_margin_surface.png','Figure 12. Version v2 acceptance margin across normalized sensor input and temperature. The recorded paceval graph outputs can be recalculated by rebuilding and executing the project.',maxh=345),
P('An actual industrial implementation must agree on a qualified limit, a documented uncertainty model and explicit behavior near the boundary. Observed agreement on a finite sample is not a general proof of margin stability.'),PageBreak()]
#14
base=json.loads((R/'results/sdk_run_summary.json').read_text());large=json.loads((R/'results/large_capacity/sdk_run_summary.json').read_text());audit=json.loads((R/'results/independent_80digit_audit.json').read_text());auditlarge=json.loads((R/'results/large_capacity/independent_80digit_audit.json').read_text())
s += [Heading('13','Validation and reproducibility'),
P('All numerical claims below refer to completed executable runs with the original paceval SDK 4.25 shared library, and not to assumed outcomes. The C++ source includes a separately implemented mathematical reference used for every stored input; an independent Python-mpmath script recomputes the 11 quantities with 80-decimal-digit arithmetic.'),
table([
 ['Check','4,096 intervals × 2','65,536 intervals × 2'],
 ['Executed persistent paceval graphs',str(base['graph_count']),str(large['graph_count'])],
 ['Synthetic input rows',str(base['sample_count']),str(large['sample_count'])],
 ['Actual paceval graph output values',f"{base['graph_outputs']:,}",f"{large['graph_outputs']:,}"],
 ['Independent native quantity assertions',f"{base['independent_cpp_numerical_checks']:,}",f"{large['independent_cpp_numerical_checks']:,}"],
 ['80-decimal-digit numerical checks',f"{audit['quantity_comparisons']:,}",f"{auditlarge['quantity_comparisons']:,}"],
 ['Largest high-precision absolute difference',f"{audit['max_abs_discrepancy']:.3g}",f"{auditlarge['max_abs_discrepancy']:.3g}"],
 ['Decision agreement with decimal oracle','PASS','PASS'],
 ],[205,145,145]),Spacer(1,14),
P('Numerical differences are in normalized synthetic model units. The high-precision check uses an independently written mathematical formula and high-precision transcendentals; its small disagreement with binary64 partly reflects coefficient rounding, not a measurement-accuracy result.'),
P('The source uses C++17 and the original paceval API. Batch routing is the C++ host responsibility; interpolation, correction, derivative, uncertainty and mathematical scoring are real paceval expressions. Test commands are documented in README.md. The Linux runtime library remains external to the publication.'),
P('<b>Reproduction assets:</b> input manifest, exact formula registry, program sources, recorded graph outputs, 80-digit audit JSON, capacity-run evidence and 12 regenerable scientific figures. No timing or acceleration comparisons are part of this functionality study.','small'),PageBreak()]
#15
s += [Heading('14','Limitations, standards, and next experimental milestone'),
P('This is a verified mathematical software demonstrator, not accredited instrument calibration. All knot values, reference data, drift factors, quality tolerances and standard uncertainties are synthetic. It contains no traceable calibration chain, real sampling hardware, physical uncertainty budget, industrial validation, safety certification or certified interval-enclosure evidence.'),
P('<b>Relevant external context:</b> NIST distinguishes measurement-result traceability from software calculations [2]. IEC 61298-2:2026 applies to process-instrument tests under reference conditions and excludes process measurement transmitters regulated in IEC 62828 [3]. ISO/IEC 17025 specifies laboratory competence requirements and does not certify this project by reference alone [4].'),
P('The next justified applied pilot is a sensor or machine axis with an approved measurement dataset, reference equipment and its full uncertainty statement. Formula updates and approval/rollback workflows should be independently audited against an instrument-qualified model. OPC UA companion information models are one possible future integration interface [6].'),
line(),Heading('15','References'),
P('[1] paceval. Mathematical Engine C/C++ API version 4.25. https://paceval.com/api/','source'),
P('[2] NIST. Metrological Traceability: Frequently Asked Questions and NIST Policy. https://www.nist.gov/metrology/metrological-traceability','source'),
P('[3] IEC 61298-2:2026. Process measurement and control devices, reference-condition performance tests. https://webstore.iec.ch/en/publication/87417','source'),
P('[4] ISO/IEC 17025:2017. General requirements for the competence of testing and calibration laboratories. https://www.iso.org/standard/66912.html','source'),
P('[5] SciPy PchipInterpolator reference and associated Fritsch/Butland method. https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.PchipInterpolator.html','source'),
P('[6] OPC Foundation, OPC UA Companion Specifications. https://opcfoundation.org/about/opc-technologies/opc-ua/ua-companion-specifications/','source'),
P('[7] NIST Technical Note 1297, Guidelines for Evaluating and Expressing the Uncertainty of NIST Measurement Results. https://www.nist.gov/pml/nist-technical-note-1297','source'),
Spacer(1,9),P('<b>Research conclusion.</b> Versioned, long piecewise calibration and uncertainty-aware mathematical scoring are demonstrably executable by real paceval graphs. Practical sensor calibration benefits require a separate measurement-based study.','call')]
D.build(s)
print('Wrote',OUT,OUT.stat().st_size)
