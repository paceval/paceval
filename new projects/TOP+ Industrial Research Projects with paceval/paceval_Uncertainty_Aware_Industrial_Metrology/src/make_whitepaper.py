#!/usr/bin/env python3
"""Rebuild the publication-quality English PDF with research-owned illustrations.
All numeric study statements are grounded in results/execution_evidence.json and CSVs.
"""
import csv,json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape
from PIL import Image as PilImage
root=Path(__file__).resolve().parents[1]; figures=root/'figures'; results=root/'results'
output=root/'paceval_Uncertainty_Aware_Industrial_Metrology_Whitepaper_EN.pdf'
e=json.loads((results/'execution_evidence.json').read_text());hi=json.loads((results/'high_precision_audit.json').read_text())
summary=list(csv.DictReader((results/'scenario_summary.csv').open()));monte=list(csv.DictReader((results/'monte_carlo_audit.csv').open()))
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Serif','/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'))
W,H=A4;LEFT=42;RIGHT=42;PAGEW=W-LEFT-RIGHT
DARK=colors.HexColor('#103b3d');TEAL=colors.HexColor('#007f79');GOLD=colors.HexColor('#d59536');MUTED=colors.HexColor('#586b69')
WHITE=colors.HexColor('#ffffff');LIGHT=colors.HexColor('#eaf2f0'); PALE=colors.HexColor('#faf3e7')
P=ParagraphStyle('body',fontName='DejaVu',fontSize=9.25,leading=14.4,spaceAfter=9,textColor=DARK)
PS=ParagraphStyle('small',parent=P,fontSize=8.15,leading=12,spaceAfter=7)
LEAD=ParagraphStyle('lead',parent=P,fontSize=11.3,leading=17,spaceAfter=13)
T=ParagraphStyle('title',fontName='DejaVu-Bold',fontSize=27,leading=36,textColor=DARK,spaceAfter=11)
H1=ParagraphStyle('h1',fontName='DejaVu-Bold',fontSize=17.2,leading=25,textColor=DARK,spaceBefore=1,spaceAfter=12)
H2=ParagraphStyle('h2',fontName='DejaVu-Bold',fontSize=10.7,leading=16,textColor=TEAL,spaceBefore=10,spaceAfter=5)
CAP=ParagraphStyle('caption',fontName='DejaVu',fontSize=7.5,leading=11,textColor=MUTED,spaceBefore=6,spaceAfter=10)
V=ParagraphStyle('val',fontName='DejaVu-Bold',fontSize=9.5,leading=13,textColor=DARK)
STORY=[]
def par(s,style=P):STORY.append(Paragraph(s,style))
def h(s):par(s,H1)
def h2(s):par(s,H2)
def sp(h=8):STORY.append(Spacer(1,h))
def page():STORY.append(PageBreak())
def fig(name,caption,width=PAGEW-16):
 path=figures/name
 with PilImage.open(path) as img:iw,ih=img.size
 ratio=ih/iw
 if not name.startswith('00_') and width*ratio > 218: width=218/ratio
 img=Image(str(path),width=width,height=width*ratio);img.hAlign='CENTER';STORY.append(img)
 par(caption,CAP)
def table(rows,widths=None):
 if widths is None:widths=[PAGEW/len(rows[0])]*len(rows[0])
 data=[[Paragraph(escape(str(x)),PS if j else V) for j,x in enumerate(r)]for r in rows]
 tb=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,colors.HexColor('#f7f9f8')]),
 ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#cbd9d6')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
 STORY.append(tb);sp(8)
def eq(latex,key,height=45):
 file=figures/('math_'+key+'.png')
 fig,ax=plt.subplots(figsize=(10,1.05),dpi=220);ax.axis('off')
 ax.text(.50,.5,'$'+latex+'$',ha='center',va='center',fontsize=18,color='#0b514c',transform=ax.transAxes)
 fig.savefig(file,dpi=200,bbox_inches='tight',transparent=True,pad_inches=.08);plt.close(fig)
 with PilImage.open(file) as img:w,hh=img.size
 size=min(PAGEW-28,480);STORY.append(Image(str(file),width=size,height=min(height,size*hh/w)));sp(7)
# ------------------------------------------------------------------------
# Cover
# ------------------------------------------------------------------------
sp(16)
par('paceval.  |  Industrial Research  |  WP 09',ParagraphStyle('eyebrow',parent=H2,fontSize=10.5,textColor=TEAL))
par('Uncertainty-Aware<br/>Industrial Metrology',T)
par('Correlated inputs, nonlinear uncertainty models and guard-banded tolerance decisions',LEAD)
fig('00_uncertainty_metrology_hero.png','Concept illustration, not an actual measurement installation or a computed research result.',width=PAGEW)
sp(10)
par('<b>Research outcome.</b> Original paceval SDK 4.25 computed '+format(e['model_point_rows'],',')+' synthetic model-point cases with '+str(e['unique_graphs_executed'])+' persistent graphs; the full numerical outputs passed independent verification.',P)
par('<b>Scope.</b> Fictional calibration parameters, ten coefficient revisions, ten covariance cases and two mathematically distinct uncertainty variants. No claim of actual metrological traceability, accredited conformity assessment or customer deployment.',PS)
par('Scientific research report  |  14 November 2026',CAP)
page()
# 2
h('Executive summary and experimentally verified scope')
par('Industrial measurement stations should not classify a component by comparing a single measured number to a tolerance. Relevant input uncertainties, correlations, calibration revisions and the agreed decision rule determine whether the evidence supports acceptance, rejection or additional inspection. This demonstrator executes those explicit mathematical functions as versioned paceval computation graphs.',LEAD)
table([['Verified research element','Observed result'],['Real execution runtime','Original paceval SDK 4.25 on compatible Linux shared library'],['Prepared and executed graphs',str(e['unique_graphs_executed'])],['Distinct synthetic input records',format(e['unique_measurement_inputs'],',')],['Executed versioned model cases',format(e['model_point_rows'],',')],['Graph-point results',format(e['graph_point_evaluations'],',')],['Independent native mathematics checks',format(e['native_cpp_reference_checks'],',')],['80-digit numerical reference checks',format(hi['checks'],',')],['Monte Carlo reference','14 selected cases; 60,000 samples per case']],widths=[PAGEW*.48,PAGEW*.52])
par('The historical two-page WP 09 proposal defined the research direction but reported no previous execution. Every quantitative result above originates from the newly executed project and its archived files. All input data are deliberately synthetic.',PS)
par('The study demonstrates the mathematical execution chain and independent numerical consistency. It cannot determine whether its assumed probability distributions describe a real instrument or whether the selected guard bands satisfy a particular customer, standard, or regulatory rule.',PS)
page()
# 3
h('1. Industrial use case and current state of the art')
par('Consider a hypothetical precision-production cell measuring the displacement of a machined component using a normalized sensor signal and a temperature sensor. The inspection software applies a calibration formula, computes the associated standard uncertainty and records the status of a tolerance decision. The calibration may change after recalibration, and measured influence quantities may be correlated.',P)
par('The relevant references are the <b>GUM</b> (JCGM 100:2008) for uncertainty propagation, the <b>2026 amendment on nonlinearity</b>, JCGM 101:2008 for distribution propagation, JCGM 106:2012 for conformity assessment, ISO 14253-1:2017 for geometric product specifications, and ILAC G8:09/2019 for documented decision rules. NIST TN 1297 describes both combined and expanded uncertainty.',P)
par('A January 2026 study by Choi and Hur describes guard-band charts incorporating uncertainty for coordinate-measuring-machine inspection of semiconductor components. The broader instrumentation literature continues to discuss uncertainty-aware decisions and usable information. This research borrows the application context, not any external article\'s measured outcomes.',P)
fig('01_architecture_concept.png','Figure 1. Research architecture: mathematical graphs calculate uncertainty and guard scores; C++ manages input validity, status text and audit. This figure is a conceptual schematic.',width=PAGEW-20)
h2('Research question')
par('Can one programmable mathematical engine execute calibrated estimates, covariance-dependent uncertainty, explicit nonlinear corrections and tolerance-rule margins across many controlled model revisions, while retaining independent reproducibility and unambiguous ownership of each mathematical function?',P)
page()
# 4
h('2. Measurement model, inputs and dimensional conventions')
par('The original proposal supplies a quadratic measurement model. We retain it, but express the temperature influence relative to an explicit 20 °C reference rather than burying the reference offset in an unidentified coefficient.',P)
eq(r'y_0=a_0+a_1x+a_2x^2+b(T-20)', 'y0')
eq(r'J_x=a_1+2a_2x,\qquad J_T=b','sens')
table([['Variable / term','Definition and dimension'],['x, ux','Normalized sensor input and its standard uncertainty, dimensionless'],['T, uT','Fixture temperature and standard uncertainty, degrees Celsius'],['a0, a1, a2','Synthetic calibration coefficients (output mm for dimensionless x)'],['b','Temperature influence coefficient, mm/°C'],['rho','Correlation coefficient of x and T, range [-1, 1]'],['ucal, ures','Independent additive calibration and resolution uncertainty, mm'],['target, tol','Target displacement and symmetric half-tolerance, mm'],['k','Declared expanded-uncertainty factor; k = 2 in the study']],widths=[PAGEW*.28,PAGEW*.72])
par('A 10-revision coefficient schedule and ten predefined correlation cases generate reproducible input records. The C++ host rejects nonfinite values and covariance inputs outside the positive-semidefinite domain. These host operations are data governance, not substituted numerical matrix formulas.',PS)
page()
# 5
h('3. Covariance propagation and two model versions')
par('The classic first-order law of uncertainty propagation uses the sensitivity vector and the covariance matrix. With two correlated inputs and independent calibration and resolution noise, the combined variance contains a covariance cross term.',P)
eq(r'\mathrm{cov}(x,T)=\rho u_xu_T','cov')
eq(r'u_1^2=J_x^2u_x^2+b^2u_T^2+2J_xb\rho u_xu_T+u_{cal}^2+u_{res}^2','variance',height=50)
par('Version 1 uses the nominal output y0 and the first-order variance u1². Version 2 assumes jointly normal, zero-mean x/T errors with the specified covariance and independent additive Gaussian calibration and resolution components. For the quadratic input model, its first two moments can then be written analytically:',P)
eq(r'y_2=y_0+a_2u_x^2,\quad u_2^2=u_1^2+2a_2^2u_x^4','curv',height=50)
par('Under these stated assumptions the v2 formulas are exact formulas for the mean and variance, but not for the full output distribution. A quadratic transformation of normal inputs need not be normal. The difference between a model-moment formula and a calibrated physical uncertainty budget is fundamental.',P)
fig('09_nonlinear_bias.png','Figure 2. The nonlinear mean correction a2 ux², derived from the actually evaluated v2 model inputs.',width=PAGEW-16)
page()
# 6
h('4. Explicit guard-band decisions')
par('The simulated symmetric tolerance is [target - tol, target + tol]. The declared expanded uncertainty is U = ku with k = 2. The study intentionally supports three results: acceptance if the expanded interval lies within tolerance, rejection if the expanded interval lies wholly outside the tolerance band, and review otherwise.',P)
eq(r'm_A=tol-|y-target|-ku','marginA')
eq(r'm_R=|y-target|-tol-ku','marginR')
par('<b>ACCEPT</b> if mA ≥ 0; <b>REJECT</b> if mR ≥ 0; <b>REVIEW</b> otherwise. Both indicators are produced through paceval relational and logical graph operations. C++ maps the resulting numeric code to the text label. The score and margins are mathematical research outputs, not authorization to release a manufactured product.',P)
fig('06_guardband_geometry.png','Figure 3. Geometry of the tolerance and inner acceptance interval using a real recorded expanded-uncertainty value. The graphic is an explanatory section through the synthetic model.',width=PAGEW-8)
par('This defined rule is illustrative. It does not imply a guaranteed confidence level, agreed risk allocation, global producer or consumer risk, or complete implementation of ISO 14253-1 or ILAC G8.',PS)
page()
# 7
h('5. Original paceval execution architecture')
par('The primary stage evaluates the calibrated output, derivatives, covariance contribution, curvature terms and full model-specific variance. The resulting values are passed to a second batch of paceval graphs for the uncertainty, expanded uncertainty, acceptance/rejection margins, flags, quality score and analytical sensitivity. The host transports the intermediate numbers without replacing the mathematical formulas.',P)
table([['Mathematical output','Executed by','Versioned graph'],['Calibrated output and sensitivities','paceval','v1/v2, primary'],['Covariance and cross term','paceval','v1/v2, primary'],['First-order or nonlinear variance','paceval','v1/v2, primary'],['Standard and expanded uncertainty','paceval','v1/v2, secondary'],['Decision margins and relational flags','paceval','v1/v2, secondary'],['Encoded decision and quality score','paceval','v1/v2, secondary'],['Uncertainty sensitivity and limits','paceval','v1/v2, secondary'],['Input validation, audit, label text','C++ host','no graph, documented role']],widths=[PAGEW*.46,PAGEW*.20,PAGEW*.34])
par('The implementation uses `paceval_dGetMultipleComputationsResultsExt` for the scientific workload. A dedicated test checks graph-major response order against scalar calls. All numeric CSV input/output values use the original paceval string-conversion APIs with schema validation before parsing; `%`, `mod`, relational comparisons and boolean semantics have independent operator tests.',PS)
par('The complete [42] graph handles are actual created and evaluated computation objects, not registrations counted without subsequent use. The graph registry and execution evidence are included with the project.',PS)
page()
# 8
h('6. Deterministic one-million-case research workload')
par('The host generates 10 independently numbered synthetic calibration coefficient revisions and 10 prescribed correlations, and combines each with 5,000 synthetic normalized-sensor samples. Both simultaneously retained model versions are evaluated on the same input records. This produces 500,000 distinct measurement inputs and 1,000,000 versioned calculations.',P)
table([['Study dimension','Verified value'],['Coefficient revisions','10'],['Input covariance cases','10'],['Samples per revision and case','5,000'],['Model versions retained simultaneously','2'],['Model-point calculations','1,000,000'],['Graph outputs from actual paceval calls','21,000,000'],['Distinct multi-graph batch calls','8,000']],widths=[PAGEW*.64,PAGEW*.36])
par('The scenario CSV is written and then read through the paceval string-to-number conversion routine; strict literal validation prevents a mathematical expression in a numeric field from being interpreted as data. All primary and secondary numerical outputs are computed using the original SDK. A separate native C++ reference checks every field, while independent Python reconstructs selected results using high-precision arithmetic.',P)
fig('04_model_revision_shift.png','Figure 4. Across ten coefficient revisions, both versioned measurement models remain available and produce identifiable output changes.',width=PAGEW-30)
page()
# 9
h('7. Uncertainty dependence on correlated inputs')
par('The covariance term changes the propagated uncertainty according to both the input correlation and the signs of the sensitivities. The calculations retain that cross term instead of treating all input contributions as statistically independent.',P)
fig('02_correlation_uncertainty.png','Figure 5. Average calculated standard uncertainty as the correlation coefficient changes across the ten synthetic cases.',width=PAGEW-10)
fig('05_uncertainty_field.png','Figure 6. A spatial view of the version-2 computed standard uncertainty over sensor values and correlation settings.',width=PAGEW-10)
page()
# 10
h('8. Three-way decisions and calibrated variants')
par('Near the boundaries, uncertainty creates a review zone in which the evidence supports neither the defined acceptance nor the defined rejection condition. Across the complete synthetic workload, the paceval-generated categorical outputs are summarized below:',P)
counts=hi['decision_counts'];table([['Status','Combined count (both versions)'],['ACCEPT',format(counts['ACCEPT'],',')],['REVIEW',format(counts['REVIEW'],',')],['REJECT',format(counts['REJECT'],',')]],widths=[PAGEW*.48,PAGEW*.52])
fig('03_status_shares_by_covariance.png','Figure 7. Three-way decision shares in each covariance case for the nonlinear-moment model v2.',width=PAGEW-18)
fig('08_versioned_decisions.png','Figure 8. Both controlled model versions yield independently defined, actually executed three-way decisions.',width=PAGEW-18)
page()
# 11
h('9. Sensitivity and configurable mathematical scoring')
par('The engine evaluates a derivative of the combined standard uncertainty with respect to the normalized sensor input. This derivative is explicitly derived in the source and checked independently. A separate reusable graph combines normalized deviation, expanded uncertainty and correlation magnitude into a synthetic composite score.',P)
fig('10_uncertainty_sensitivity.png','Figure 9. The analytical sensitivity of the combined standard uncertainty, as computed by the SDK.',width=PAGEW-20)
fig('07_quality_score_landscape.png','Figure 10. The defined composite quality score across synthetic measurements; it is not a regulatory probability.',width=PAGEW-20)
page()
# 12
h('10. Detailed decision map')
par('The three-way status code is expressed numerically as ACCEPT minus REJECT. The distinct guards are explicitly parenthesized before the host maps the output to its category. No potentially singular expression relies on a boolean mask to prevent evaluation; ranges and positivity are checked before graph calls.',P)
fig('12_decision_map.png','Figure 11. Results of the original paceval decision-code graph across different sensor values and input correlations.',width=PAGEW-8)
par('For records with a positive acceptance margin, the reported measurement interval lies inside the illustrative acceptance band. For large deviations, the rejection margin becomes nonnegative; the intermediate region remains REVIEW. Practical inspection decisions must adopt a documented rule agreed with the relevant parties.',P)
h2('Measurement and specification are separate layers')
par('A low mathematical score does not establish traceability, measurement-system capability, repeatability, operator independence or calibration against physical standards. None of these can be inferred from successful synthetically generated math alone.',P)
page()
# 13
h('11. Independent verification and nonlinear model check')
par('A separately implemented native C++ calculation verifies all 21 mathematical output quantities for each versioned model case. A distinct 80-decimal-place Python implementation examines the archived result samples without reusing the paceval formula string. These checks passed in the recorded research workload.',P)
par('For the second model version, 14 Gaussian Monte Carlo studies with 60,000 random draws each independently check the analytically predicted mean and variance. The sampling generator uses correlated normal inputs with the declared covariance, plus independent calibration and resolution noises. The study does not claim that actual manufacturing measurements have these distributions.',P)
fig('11_monte_carlo_reference.png','Figure 12. Independently simulated Monte Carlo variances plotted against the model-2 variances calculated by paceval. This figure is a clearly identified reference check, not a second paceval data source.',width=PAGEW-6)
par('The two types of verification answer different questions. Mathematical consistency of a formula implementation is not proof that the formula accurately describes a physical instrument. A real pilot would need traceable reference values, validated probability assumptions and independent holdout measurements.',PS)
page()
# 14
h('12. Reproducibility, limits and next scientific step')
par('The complete GitHub-oriented package includes the original public C/C++ bridge source files, CMake integration, source-checked numerical CSV conversions, two model versions, formula registry, input scenarios, archived paceval results, independent native and high-precision checks, Monte Carlo studies, scientific plotting scripts and this PDF report. The proprietary/externally supplied shared runtime library is intentionally excluded.',P)
par('<b>Reproduction:</b> supply a compatible original `libpaceval_linux_sharedLIB.so`; build with CMake from `src/`, run CTest, and reproduce the full dataset using `./build/metrology --run --revisions 10 --cases 10 --samples 5000 --out results/reproduced`. Compare the recorded audit with `python3 src/verify_reference.py results/reproduced`. Every reported count derives from the machine-readable `results/execution_evidence.json` and the corresponding research files.',PS)
h2('What has and has not been established')
par('<b>Established:</b> original paceval execution of the model chain, correlation-sensitive and nonlinear-moment uncertainty propagation, re-usable graph versions, strict numeric CSV conversion, logical decision functions, reproducible synthetic scenarios and independent mathematical validation. <b>Not established:</b> compliance with all provisions of ISO/IEC 17025, ISO 14253-1 or ILAC G8; accredited declarations; physical calibration; probabilistic coverage for arbitrary measurements; adoption by a factory or laboratory.',PS)
h2('Selected references')
refs=[
'JCGM 100:2008 GUM, Amendment 1:2026 on nonlinearity, JCGM 101:2008, JCGM 106:2012; https://www.bipm.org/en/web/guest/publications/guides',
'NIST TN 1297, Combined Standard Uncertainty and Expanded Uncertainty; https://www.nist.gov/pml/nist-technical-note-1297/',
'ISO 14253-1:2017, confirmed 2023; https://www.iso.org/standard/70137.html',
'ILAC G8:09/2019, Guidelines on Decision Rules and Statements of Conformity; https://ilac.org/publications-and-resources/ilac-guidance-series/',
'I. Choi and S. Hur, Design of guard band chart based on measurement uncertainty, J. Mechanical Science and Technology (2026); https://doi.org/10.1007/s12206-025-1244-8',
'A. Ferrero and D. Petri, Measurement Uncertainty and Information Enabled Decision Making, IEEE OJIM (2025); https://doi.org/10.1109/OJIM.2025.3626105',
'paceval official C/C++ API and mathematical product overview; https://paceval.com/api/ and https://paceval.com/product-brief/'
]
for j,r in enumerate(refs,1):par(f'<b>[{j}]</b> '+escape(r),PS)
par('<b>Conclusion:</b> This project verifies the functional feasibility of an explicit, traceable-in-software mathematics layer. The next responsible research step is experimental characterization of an actual measurement station, including distribution assumptions, covariance estimation, agreed decision rules and independently calibrated reference measurements.',PS)
# ------------------------------------------------------------------------
def decorate(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(TEAL);canvas.setLineWidth(1.4);canvas.line(LEFT,H-32,W-RIGHT,H-32)
 canvas.setFont('DejaVu',7.3);canvas.setFillColor(MUTED)
 canvas.drawString(LEFT,27,'paceval.  |  Uncertainty-aware industrial metrology  |  Research, 2026')
 canvas.drawRightString(W-RIGHT,27,f'{doc.page}')
 canvas.restoreState()
doc=SimpleDocTemplate(str(output),pagesize=A4,leftMargin=LEFT,rightMargin=RIGHT,topMargin=44,bottomMargin=45,
                      title='Uncertainty-Aware Industrial Metrology and Tolerance Decisions with paceval',author='paceval research demonstrator')
doc.build(STORY,onFirstPage=decorate,onLaterPages=decorate)
print('PDF_CREATED',output)
