#!/usr/bin/env python3
"""Generate a scientifically traceable 14-page English paper from executed data."""
import csv,os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Image,Table,TableStyle,PageBreak,Spacer,KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from xml.sax.saxutils import escape
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent.parent
FIG=ROOT/'figures';OUT=ROOT/'paceval_Semiconductor_Wafer_Overlay_Whitepaper_EN.pdf'
NAV=HexColor('#15334a');TEAL=HexColor('#008c91');GRAY=HexColor('#52697b');PALE=HexColor('#f1f7f9');CORAL=HexColor('#ea694f')
F='/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('DejaVu',F+'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuBold',F+'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuMono',F+'DejaVuSansMono.ttf'))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='H',fontName='DejaVuBold',fontSize=16,leading=21,textColor=NAV,spaceBefore=0,spaceAfter=12))
styles.add(ParagraphStyle(name='H2Wafer',fontName='DejaVuBold',fontSize=11,leading=15,textColor=TEAL,spaceBefore=10,spaceAfter=6))
styles.add(ParagraphStyle(name='BodyWafer',fontName='DejaVu',fontSize=9.0,leading=13.8,textColor=NAV,spaceAfter=9))
styles.add(ParagraphStyle(name='TinyWafer',fontName='DejaVu',fontSize=7.7,leading=11,textColor=GRAY,spaceAfter=6))
styles.add(ParagraphStyle(name='CaptionWafer',fontName='DejaVu',fontSize=8.2,leading=11.6,textColor=GRAY,alignment=TA_CENTER,spaceAfter=10))
styles.add(ParagraphStyle(name='TitleWafer',fontName='DejaVuBold',fontSize=26,leading=33,textColor=NAV,spaceAfter=12))
styles.add(ParagraphStyle(name='SubWafer',fontName='DejaVu',fontSize=12,leading=19,textColor=TEAL,spaceAfter=10))
styles.add(ParagraphStyle(name='WhiteSmallWafer',fontName='DejaVu',fontSize=10,leading=14,textColor=NAV,spaceAfter=8))
W,H=A4;LEFT=20*mm;RIGHT=19*mm;TOP=22*mm;BOTTOM=18*mm;CONTENT=W-LEFT-RIGHT
class Report(BaseDocTemplate):
 def __init__(self,path):
  super().__init__(str(path),pagesize=A4,leftMargin=LEFT,rightMargin=RIGHT,topMargin=TOP,bottomMargin=BOTTOM,
                   title='Semiconductor Wafer Overlay and Distortion Correction with paceval',author='paceval independent research demonstrator')
  frame=Frame(LEFT,BOTTOM,CONTENT,H-BOTTOM-TOP,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
  self.addPageTemplates(PageTemplate(id='normal',frames=frame,onPage=self.frame_page))
 def frame_page(self,c,doc):
  c.setStrokeColor(HexColor('#dae4eb'));c.setLineWidth(.65);c.line(LEFT,H-15*mm,W-RIGHT,H-15*mm)
  c.setFont('DejaVuBold',8.2);c.setFillColor(TEAL);c.drawString(LEFT,H-12.7*mm,'paceval.   |   SEMICONDUCTOR RESEARCH')
  c.setFont('DejaVu',7.3);c.setFillColor(GRAY);c.drawRightString(W-RIGHT,H-12.7*mm,'Independent reproducible demonstrator  ·  2026')
  c.line(LEFT,13.7*mm,W-RIGHT,13.7*mm)
  c.setFont('DejaVu',7.2);c.drawString(LEFT,9.9*mm,'Synthetic data · Mathematical feasibility · Not fab-qualified')
  c.drawRightString(W-RIGHT,9.9*mm,f'{doc.page}')
def P(txt,style='BodyWafer'):
 return Paragraph(txt,styles[style])
def h(txt):return P(txt,'H')
def h2(txt):return P(txt,'H2Wafer')
def b(txt):return P(txt)
def cap(txt):return P(txt,'CaptionWafer')
def img(path,width=CONTENT,height=None):
 from PIL import Image as PILImage
 im=PILImage.open(path);rw,rh=im.size
 if height is not None: width=min(width,height*rw/rh)
 else:height=width*rh/rw
 return Image(str(path),width=width,height=height,kind='proportional',hAlign='CENTER')
def plot(name,height=67*mm):
 path=FIG/(name+'.png')
 from PIL import Image as PILImage
 rw,rh=PILImage.open(path).size
 width=min(CONTENT,height*rw/rh)
 return img(path,width=width,height=width*rh/rw)
def table(rows,widths=None,small=8.2):
 tbl=Table([[P(escape(str(x)),'TinyWafer') for x in row] for row in rows],colWidths=widths or [CONTENT/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='CENTER')
 tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('TEXTCOLOR',(0,0),(-1,0),NAV),
 ('GRID',(0,0),(-1,-1),.35,HexColor('#e1e8ee')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
 ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor('#fafcfd')]),('LEFTPADDING',(0,0),(-1,-1),7),
 ('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 return tbl

def equation(key,latex,width=CONTENT*.89):
 fname=FIG/('math_'+key+'.png')
 f=plt.figure(figsize=(10,.7),facecolor='white');f.text(.5,.5,r'$'+latex+r'$',ha='center',va='center',fontsize=16,color='#15334a');f.savefig(fname,dpi=220,bbox_inches='tight',pad_inches=.09);plt.close(f)
 return img(fname,width=width)

def pagebreak(): return PageBreak()

# Measured figures, never estimates.
with open(ROOT/'results'/'wafer_summary.csv',newline='') as f:rows=list(csv.DictReader(f))
lot0=[r for r in rows if r['lotId']=='0']
story=[]

def page(*parts):
 story.extend(parts);story.append(pagebreak())

# 01 Cover
story.extend([Spacer(1,14*mm),P('SEMICONDUCTOR WAFER<br/>OVERLAY &amp; DISTORTION CORRECTION','TitleWafer'),
 P('Reusable mathematical execution graphs, model revisions, sensitivity fields and quality functions with paceval','SubWafer'),
 img(FIG/'00_wafer_overlay_hero.png',width=CONTENT),
 cap('Concept illustration only; not measured semiconductor equipment or computed research data.'),Spacer(1,11*mm),
 P('<b>Independent scientific research demonstration</b>  |  14 November 2026','WhiteSmallWafer'),
 P('Executed using the original paceval Mathematical Engine 4.25 and its Linux shared library. Ten synthetic wafer lots, two calibrated formula families and strict independent numerical verification. No fab measurement, equipment control or qualification is claimed.','BodyWafer'),
 P('Verified result: 360 persistent paceval graphs, 3,735,720 graph outputs, 420 multi-graph batches, and full mathematical reference checks. This is a functional feasibility report, not a runtime benchmark.','BodyWafer'),pagebreak()])

# 02 introduction
page(h('1. Industrial use case and state of the art'),
 b('Semiconductor photolithography aligns a succession of fine patterned layers. Overlay error is the relative two-dimensional misalignment between patterns on adjoining layers, often summarized from metrology marks across a wafer. Position-dependent and temperature-dependent distortion can be modeled as a correction field and used in engineering review or appropriately qualified control workflows. Mathematical consistency is necessary, but it does not itself establish measurement traceability or scanner qualification.'),
 b('Industrial systems use optical diffraction-based measurements and electron-beam approaches together with scanner measurements and analytical software. ASML describes YieldStar diffraction-based overlay measurements, semiconductor pattern inspection, and correction feedback to lithography processes. NIST has an active 2026 research project combining SEM measurements with physical simulation and AI for overlay metrology; the research addresses detection limits and measurement trustworthiness [1-3].'),
 b('A peer-reviewed 2025 article studies fifth-order two-dimensional polynomial overlay compensation and actuator-related corrections [4]. Its results motivate including nonlinear and higher-order overlay fields, without implying that a synthetic polynomial demonstration reproduces actual process physics or the behavior of qualified production machines.'),
 h2('Purpose of this experiment'),
 b('We investigate whether the same independently defined industrial mathematical expressions can be serialized into persistent paceval graphs, revised without changing application orchestration, evaluated for many wafer positions, and combined with residual scores, quality margins and analytic sensitivities. We do not claim improved wafer yield, fab deployment or speed advantages.'),
 table([['Industrial information','Demonstrated synthetic proxy'],['Measured x/y overlay','Input CSV: observed displacement in nanometers'],['Wafer location','Normalized coordinates on a 300 mm wafer'],['Operating temperature','Temperature-dependent polynomial basis'],['Correction map','Two independent paceval expressions for dx and dy'],['Engineering quality review','Numerical guards, uncertainty and Boolean categories']], [CONTENT*.35,CONTENT*.65]))

# 03 diagram
page(h('2. Research architecture and source of evidence'),
 b('The architecture separates three responsibilities. The C++ host generates reproducible measurements, parses and validates CSV, performs independent Householder QR fitting, manages computation handles and stores outputs. The real paceval SDK owns every registered overlay formula, observed-versus-predicted residual, risk function, signed margin, logical quality region and analytic first derivative. The independent Python audit later recomputes the published values without calling the SDK.'),
 plot('01_research_workflow',55*mm),cap('Figure 1. Demonstrator execution architecture; conceptual system diagram, not physical deployment.'),
 h2('Two controlled formula families per lot'),
 b('Every one of ten synthetic wafer lots receives a quadratic/temperature-aware model v1 and a cubic-plus-trigonometric model v2. Both are retained simultaneously as distinct persistent graph sets. They share a declared variable order and compatible output columns, allowing data to pass through the same host-level orchestrator. There are 18 graph definitions per version and lot, or 360 executed graphs in total.'),
 h2('From metrology row to mathematical decision'),
 b('A site record provides x, y, temperature, observed dx and dy, measurement standard uncertainty and a site identifier. paceval emits predicted dx/dy and a residual vector. Additional paceval graphs compute the residual norm, quality margins, normalized loss, derivatives and acceptance regions; the C++ host checks the resulting Boolean partition before assigning the display category. No hardware actuator or interlock is connected.'))

# 04 math
page(h('3. Defined mathematical model'),
 b('A 300 mm diameter synthetic wafer is normalized to unit radius. Temperature is referenced to 25 degrees Celsius. All overlay outputs are expressed in synthetic nanometers.'),
 equation('coordinates',r'u=\frac{x}{150\,\mathrm{mm}},\quad v=\frac{y}{150\,\mathrm{mm}},\quad \tau=\frac{T-25^\circ\mathrm{C}}{20^\circ\mathrm{C}}'),
 equation('polynomial',r'\widehat{\Delta x}=\sum_k a_k\,\phi_k(u,v,T),\quad \widehat{\Delta y}=\sum_k b_k\,\phi_k(u,v,T)'),
 b('The lower-order candidate has nine basis functions: 1, u, v, u², uv, v², temperature offset and two temperature-position interactions. The extended candidate adds u³, u²v, uv², v³ and two harmonics sin(pi u) cos(pi v), sin(pi v) cos(pi u). The fitted coefficients and every generated expression are archived. Fitting is host-side Householder QR; evaluation of the resulting mathematical models is carried out in the paceval graphs.'),
 equation('residual',r'r=\sqrt{(\Delta x_{\mathrm{obs}}-\widehat{\Delta x})^2+(\Delta y_{\mathrm{obs}}-\widehat{\Delta y})^2}'),
 equation('guard',r'g_r=3.5\sigma-r,\qquad m_{\mathrm{wafer}}=1-u^2-v^2'),
 b('The declared synthetic quality policy distinguishes ACCEPT, REVIEW and REJECT at residual thresholds 2σ and 3.5σ and additionally checks the circular wafer domain. These values are illustrative scientific test parameters, not allowable limits specified by any semiconductor manufacturer.'),
 h2('Sensitivities and uncertainty'),
 b('The four derivatives of the two correction functions with respect to u and v are explicitly differentiated in source code and stored as paceval expressions. A first-order illustrative combined uncertainty adds the declared observed sigma and a 0.00015 normalized-position uncertainty contribution through those derivatives. This is not a qualified metrology uncertainty budget.'))

# 05 api
page(h('4. Original paceval execution and numeric conversion'),
 b('The study compiles the original paceval 4.25 API source and header, with only the relative include path in the .cpp adapted for this project. A separately supplied compatible Linux shared library performs graph creation and actual calculations. Each model has 18 persistent handles; the complete graph set is evaluated with paceval_dGetMultipleComputationsResultsExt. The graph-major output arrangement is tested against known independent values and against a scalar paceval_dGetComputationResult path.'),
 table([['Actual paceval-owned function groups','Explicit graph names'],['Overlay and residuals','overlayDx, overlayDy, residualX, residualY, residualNorm'],['Domains and guards','waferMargin, residualMargin'],['Logical policy and nonlinear score','accept, review, reject, riskScore'],['Jacobian of displacement field','dDx_dU, dDx_dV, dDy_dU, dDy_dV'],['Uncertainty and clipping','illustrativeUncertainty, clampedResidual'],['Deterministic record routing','fieldSlot (modulo)']], [CONTENT*.47,CONTENT*.53]),
 h2('User-requested number conversions are actually used'),
 b('<font color="#008c91"><b>paceval_dConvertStringToFloat</b></font> parses each validated numeric CSV field. The parser also accepts mathematical expressions and a comma decimal separator, so the C++ host first enforces an explicit canonical decimal-token grammar and finite-value/physical-range policy. <font color="#008c91"><b>paceval_dConvertFloatToString</b></font> generates the numeric text in output CSV and formula coefficients. In this SDK the routine produces approximately 15 significant digits; source and output serialization are independently audited and are not claimed to preserve every binary64 bit.'),
 h2('Conditional and numerical operators'),
 b('The executed model combines Boolean AND/OR, relational operators, square and square root, sine and cosine, min/max, and the mathematical modulo operator for a record bin. Explicit regression tests also verify the C++-style symmetric % operator: (-1) mod 10 is 9 whereas (-1) % 10 is -1. Products used in comparisons are explicitly parenthesized, e.g. residual <= (2*sigma), so the tested expression grammar cannot silently regroup the threshold. Other available paceval functions are not inserted without scientific need.'))

# 06 workload
page(h('5. Deterministic workload and model life cycle'),
 b('Ten lots each contain 377 synthetic metrology sites on a circular 23 by 23 point lattice, with a fixed train/holdout split. The host generates a second 10,000-position set for every lot using a deterministic radial angular sequence. Every spatial site records a synthetic observed x/y displacement, a temperature and a declared sigma. Some samples deliberately include moderate and large outliers. Values, data provenance and version identity are stored in the distributed CSV.'),
 b('The two model families are each fitted from training samples only, and independently checked with NumPy/LAPACK least squares. Coefficients are serialized as versioned math text via paceval number conversion before graphs are registered. All held-out points remain excluded from the fit. Separately stored handles ensure that a revision cannot silently mutate a previously registered model.'),
 plot('13_coefficient_versions',72*mm),cap('Figure 2. Versioned fitted x coefficients for the first synthetic lot, from the recorded run.'),
 b('The richer model has more degrees of freedom and can represent cubic and harmonic distortions, but it is not automatically the correct model for a real wafer. Real fitting requires instrument provenance, measurement covariance, appropriate spatial sampling, holdout campaigns and an approved operating envelope.'))

# 07 metrics
page(h('6. Actual executed research results'),
 table([['Executed numerical fact','Measured count'],['Persistent paceval graph objects','360'],['10,000 input positions × 10 lots × 2 versions','200,000 graph input records'],['Additional metrology record evaluations','7,540 graph input records'],['Total paceval graph-result cells','3,735,720'],['Real multi-graph batch calls','420'],['Independent mathematical result checks','117,144'],['Independent 80-digit reference checks','4,000']], [CONTENT*.65,CONTENT*.35]),
 plot('05_lot_residual_rms',65*mm),cap('Figure 3. RMS overlay residual on the full synthetic grid, separately for each lot and formula version.'),
 b('Both families execute successfully. For lot 0, the quadratic model yields 0.560 nm RMS residual and the extended model 0.359 nm. The measured difference is a controlled result of these synthetic input models, not a demonstrated gain in commercial overlay control.'))

# 08 quality
page(h('7. Synthetic quality-policy decisions'),
 b('The quality gate is implemented as relational and logical paceval expressions with explicit product parentheses. Its three results are checked for mutually exclusive and exhaustive classification for every input row. A signed residual guard provides numerical distance to the 3.5σ threshold. A clipped residual expression illustrates paceval min/max usage without changing the original uncapped result.'),
 plot('06_quality_decision_share',64*mm),cap('Figure 4. Fraction of ACCEPT/REVIEW/REJECT outcomes for two genuine paceval graph families.'),
 plot('14_quality_margin_wafer',72*mm),cap('Figure 5. Signed hypothetical quality margin on the first wafer using the extended model.'),
 b('These flags are demonstrations of mathematical condition evaluation only. They do not constitute semiconductor wafer inspection pass/fail decisions.'))

# 09 wafer
page(h('8. Wafer correction vectors and two-dimensional fields'),
 b('A correction model is most interpretable when both x and y displacement components are spatially visible. The actual paceval graph outputs are plotted below without using the native Python reference as publication data.'),
 plot('02_overlay_dx_wafer',78*mm),cap('Figure 6. x displacement map (nanometers) from the actual v2 paceval results for lot 0.'),
 plot('03_overlay_vector_field',73*mm),cap('Figure 7. Two-component overlay correction field; directional arrows show synthetic model values.'))

# 10 model revision
page(h('9. Three-dimensional response and formula revisions'),
 b('The multi-dimensional mathematical representation allows corrected displacement to be visualized as a surface. The controlled v1-to-v2 revision is not a parameter tweak inside an existing handle: new graph objects preserve both formulations and their independently fitted coefficients.'),
 plot('07_overlay_surface_3d',78*mm),cap('Figure 8. Actual paceval v2 correction surface across the normalized wafer domain.'),
 plot('09_version_difference_map',77*mm),cap('Figure 9. Change in predicted x displacement from the old model v1 to v2.'))

# 11 sensitivity
page(h('10. Analytic sensitivity and illustrative uncertainty'),
 b('Derivatives of the polynomial and trigonometric basis are derived explicitly and evaluated using independent paceval graphs. The host does not differentiate the resulting maps numerically. The accompanying uncertainty expression is an illustrative first-order propagation with a stipulated position uncertainty and the synthetic input sigma; no certified traceability or statistical coverage is implied.'),
 plot('08_spatial_sensitivity',77*mm),cap('Figure 10. Magnitude of the x displacement gradient, from computed paceval derivatives.'),
 plot('10_uncertainty_propagation',67*mm),cap('Figure 11. Illustrative combined uncertainty response versus wafer-domain margin.'))

# 12 holdout
page(h('11. Holdout sites, radial behavior and synthetic model limits'),
 b('A model can reproduce training data yet fail between observations or outside its intended operating regime. Our deterministic holdout partition is excluded from every coefficient fit; the independently audited holdout file contains the actual paceval model outputs on unseen sites. Temperature effects and radial residuals are displayed directly, while the complete guard and finite-input policies remain active.'),
 plot('12_temperature_holdout_residual',76*mm),cap('Figure 12. Actual paceval residuals for previously unused metrology sites across temperature.'),
 plot('11_radial_residual_profile',68*mm),cap('Figure 13. Synthetic wafer-radius profile of residual RMS for both formula families.'))

# 13 validation
page(h('12. Independent verification and reproducibility'),
 b('The complete C++ experiment uses real Graph Create and Multi-Graph Batch APIs with per-result error arrays. Host-based aggregation does not substitute for the mathematical cost, margin, sensitivity or logical functions: all these figures originate in the paceval outputs. Scalar and batch layouts were cross-checked with small known values. Numerical CSV input is strictly validated before being parsed with paceval routines.'),
 table([['Validation category','Successful independent check'],['Archived graph cell values','117,144 reconstructed mathematically'],['Logical decisions and record bins','26,032 exact categorical comparisons'],['Independent 80-digit mpmath cells','4,000'],['Fitted coefficients','480 via separate NumPy/LAPACK least-squares'],['Invalid input and parser tests','Rejected NaN, comma numbers, expressions, malformed tokens'],['Graph performance benchmarking','Not part of this publication']], [CONTENT*.47,CONTENT*.53]),
 b('The independent reference reconstructs each basis, analytic derivative, residual, quality score, and indicator from released CSV coefficients. Eighty-digit mpmath checks use the actual released decimal input and coefficient text. Low-level differences and tolerances remain available in results/independent_numerical_audit.json but are intentionally not tabulated as a paceval-versus-C++ precision comparison in the published paper.'),
 h2('Reproduce the whole calculation'),
 P('cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so<br/>cmake --build build -j<br/>./build/wafer_overlay --generate<br/>./build/wafer_overlay --run --lot-limit 10 --grid-limit 10000 --out results<br/>python3 src/verify_results.py<br/>ctest --test-dir build --output-on-failure','TinyWafer'),
 b('The original source/header of the licensed SDK are included; the separate binary Shared Library is not redistributed. Scripted figures and formula inventory are part of the package.'))

# 14 limitations refs
story.extend([h('13. Industrial interpretation, limitations and next pilot'),
 b('This study demonstrates that a reusable mathematical engine can execute a substantial family of two-dimensional semiconductor overlay correction expressions, sensitivities, logical quality gates and residual metrics through stable graph handles. The evidence is concrete: the 360 original paceval graphs executed successfully on the declared synthetic workload and the independently reconstructed outputs passed the specified tests.'),
 h2('Scientific constraints'),
 b('No measured fab overlay data, physical stepper/scanner response, calibrated SEM detector, uncertainty traceability or wafer qualification was used. Synthetic displacement magnitudes and threshold policies were constructed for this numerical experiment; they are not data about any real semiconductor customer, process or tool. The host uses a conventional least-squares fit, so the study does not imply that paceval itself offers a ready-made semiconductor calibration optimizer. TINC was not exercised, and hardware acceleration is a future research avenue, not a verified result.'),
 h2('A scientifically appropriate industrial follow-up'),
 b('A credible future evaluation would use approved, licensed wafer overlay metrology at multiple temperatures and lot configurations; designate held-out wafers/lots; compare the residual map with a validated accepted reference; check uncertainty and contamination/outlier policies; maintain controlled revision IDs and replay; and submit the results to metrology specialists. No operational cost, lithography performance or yield benefit is inferred from this synthetic demonstration.'),
 h2('References and official documentation'),
 P('[1] ASML. Measuring accuracy - Lithography principles. https://www.asml.com/en/technology/lithography-principles/measuring-accuracy','TinyWafer'),
 P('[2] NIST (2026). Overlay Metrology Using Physics and AI-Based Scanning Electron Microscopy. https://www.nist.gov/programs-projects/overlay-metrology-using-physics-and-ai-based-scanning-electron-microscopy','TinyWafer'),
 P('[3] NIST (2025). Detection limits of AI-based SEM dimensional metrology. https://www.nist.gov/publications/detection-limits-ai-based-sem-dimensional-metrology','TinyWafer'),
 P('[4] Nanoscale Advances (2025), Method of high-order advanced lithography overlay correction. DOI: 10.1039/d5na00682a. https://doi.org/10.1039/d5na00682a','TinyWafer'),
 P('[5] paceval. Mathematical Engine 4.25 API and Product Brief. https://paceval.com/api/ ; https://paceval.com/product-brief/','TinyWafer'),
 P('[6] Original WP 01: Semiconductor Wafer Overlay and Distortion Correction (two-page proposal), archived under docs/Original_WP01_Proposal.pdf','TinyWafer'),
 Spacer(1,7*mm),P('Research status: completed synthetic mathematical execution study. No production tool deployment or semiconductor metrology certification.','TinyWafer')])
Report(OUT).build(story)
print('Wrote',OUT)
