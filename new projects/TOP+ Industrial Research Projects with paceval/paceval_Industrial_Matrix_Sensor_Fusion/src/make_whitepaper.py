#!/usr/bin/env python3
"""Create an independent scientific PDF from actual paceval execution results."""
from pathlib import Path
import sys,json,html
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
file=root/'paceval_Industrial_Matrix_Sensor_Fusion_Whitepaper_EN.pdf'
s128=json.loads((root/'results/matrix_128_summary.json').read_text());s512=json.loads((root/'results/matrix_512_summary.json').read_text())
val=json.loads((root/'results/independent_audit.json').read_text())
pdfmetrics.registerFont(TTFont('DVS','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVS-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
W,H=A4;LEFT=48;RIGHT=48;CW=W-LEFT-RIGHT
INK=HexColor('#112D48');BLUE=HexColor('#157C9A');MUTED=HexColor('#536D83');LGRAY=HexColor('#DDE6EC');LITE=HexColor('#EEF4F7')
c=canvas.Canvas(str(file),pagesize=A4,pageCompression=1)
c.setTitle('Programmable Matrix Mathematics for Industrial Sensor Fusion with paceval')
c.setAuthor('paceval | independent scientific research demonstrator')
page=0;y=0

def footer():
    c.setStrokeColor(LGRAY);c.line(LEFT,48,W-RIGHT,48)
    c.setFont('DVS',7.2);c.setFillColor(MUTED)
    c.drawString(LEFT,35,'paceval.  |  Programmable Matrix Mathematics for Industrial Systems  |  2026')
    c.drawRightString(W-RIGHT,35,str(page))
def new(title='',subtitle=''):
    global page,y
    if page:footer();c.showPage()
    page+=1;y=H-49
    if title:
        c.setFont('DVS-Bold',16.6);c.setFillColor(INK);c.drawString(LEFT,y,title);y-=13
        c.setLineWidth(1.7);c.setStrokeColor(BLUE);c.line(LEFT,y-3,W-RIGHT,y-3);y-=29
    if subtitle:p(subtitle,size=9.1,leading=13.5,space=13)
def p(text,size=9.2,leading=14.3,space=10,bold=False):
    global y
    style=ParagraphStyle('Z',fontName='DVS-Bold' if bold else 'DVS',fontSize=size,leading=leading,textColor=INK,spaceAfter=0,allowWidows=0,allowOrphans=0)
    par=Paragraph(text,style);w,h=par.wrap(CW,760);par.drawOn(c,LEFT,y-h);y-=h+space
    if y<60:raise RuntimeError(f'Overrun on PDF page {page} y={y:.1f}: {text[:70]}')
def h2(text):
    global y
    y-=7;c.setFillColor(BLUE);c.setFont('DVS-Bold',11);c.drawString(LEFT,y,text);y-=19
    if y<60:raise RuntimeError('section exceeds page')
def line(text):p('• '+text,size=8.8,leading=12.7,space=6)
def fig(no,slug,caption,max_h=260,w=CW):
    global y
    fname=root/'figures'/f'{no:02d}_{slug}.png';im=PILImage.open(fname);iw,ih=im.size
    scale=min(w/iw,max_h/ih);sw,sh=iw*scale,ih*scale
    if y-sh-32<56:raise RuntimeError(f'Figure {no} would overflow page {page} (y={y:.1f}, sh={sh:.1f})')
    c.drawImage(str(fname),LEFT+(CW-sw)/2,y-sh,width=sw,height=sh,preserveAspectRatio=True,mask='auto')
    y-=sh+7;p('<i>'+caption+'</i>',size=8,leading=11.7,space=12)
def tab(rows,widths=None,size=8.1):
    global y
    styles=[ParagraphStyle('th',fontName='DVS-Bold',fontSize=size,leading=11,textColor=INK),ParagraphStyle('tc',fontName='DVS',fontSize=size,leading=11.4,textColor=INK)]
    data=[[Paragraph(html.escape(str(v)),styles[0 if i==0 else 1]) for v in row]for i,row in enumerate(rows)]
    tbl=Table(data,colWidths=widths or [CW/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LITE),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#FFFFFF'),HexColor('#F7FAFB')]),('LINEBELOW',(0,0),(-1,0),.9,HexColor('#86B5C6')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6)]))
    _,th=tbl.wrap(CW,y-60);tbl.drawOn(c,LEFT,y-th);y-=th+13
    if y<60:raise RuntimeError(f'Table overflow page {page}')

new()
c.setFont('DVS-Bold',9);c.setFillColor(BLUE);c.drawString(LEFT,y,'PACEVAL  |  EXECUTED SCIENTIFIC RESEARCH DEMONSTRATOR');y-=27
p('Programmable Matrix Mathematics<br/>for Industrial Sensor Fusion',size=24,leading=33,bold=True,space=9)
p('Complete SPD matrix operations, digital-twin covariance fusion and versioned mathematical quality rules',size=10.3,leading=15.5,space=13)
hero=root/'figures/00_industrial_matrix_sensor_fusion_hero.png';img=PILImage.open(hero)
assert img.size==(2400,1200)
w=CW;sh=w/2;c.drawImage(str(hero),LEFT,y-sh,width=w,height=sh);y-=sh+7
p('<i>Concept illustration; not a computed research result.</i>',size=8.3,space=13)
h2('Verified outcome')
p('Using the original <b>paceval C++ SDK 4.25</b>, new complete <b>128 × 128 and 512 × 512</b> dense symmetric positive-definite matrices were factored and inverted. A synthetic, six-dimensional industrial sensor-fusion model was executed in <b>32 versioned scenarios</b>. The 512-dimensional run used <b>17 persistent graphs</b> and produced <b>67,538,758 actual paceval graph outputs</b>.')
p('Independent full-matrix and sensor-fusion checks have passed. The historical 1024-dimensional experiment described in the supplied source report is background and is not counted as newly executed.',size=8.8,leading=13.5)
p('13 November 2026  |  Functionality and feasibility  |  Synthetic data  |  No performance comparisons',size=8.1,space=1)

new('1. Introduction: Industrial use case')
p('A manufacturing inspection cell may receive overlapping observations from laser scanners, thermal sensors, coordinate measurement systems and machine-state estimators. Each measurement has an uncertainty model. A digital twin that combines such information needs covariance matrices, reliable matrix factorizations and a consistently applied mathematical definition of acceptable disagreement.')
p('The present research illustrates a supervisory precision-metrology application: two six-dimensional synthetic sensors observe the same nominal state; their covariance models encode uncertainty and correlation. A mathematical fusion algorithm estimates a common state, then computes a normalized innovation statistic, uncertainty radius, versioned quality scores and signed margins. The output is a repeatable quality report, <b>not</b> direct control of an actuator.')
h2('Why a mathematical execution engine is relevant')
p('The base matrix operations are well-established. The research question is whether those operations, plus frequently modified application-specific equations and score rules, can be represented as reusable mathematical execution graphs. The algorithm preserves the distinction between the general matrix decomposition, the application-layer uncertainty equations, and a final host-side quality decision.')
h2('Current scientific and industrial context')
p('LAPACK provides standard Cholesky decomposition and SPD solving [1,2]. Recent research on square-root visual-inertial estimation (2025) illustrates the importance of structured positive-definite covariance representations [3]. Multisensor data fusion in CNC digital twins has been reviewed in 2025 [4]. NIST research, including a 2026 workshop report, emphasizes uncertainty quantification, digital-twin credibility and verification/validation throughout the model lifecycle [5,6].')
p('The present study does not claim to invent sensor fusion or matrix decomposition. It establishes which mathematical operations were actually performed using paceval, and how their outputs can be reused in versioned, application-specific formulas.')

new('2. Research question and execution architecture')
p('<b>Core question.</b> Can the original paceval library actually compute a full general dense SPD Cholesky factorization and inverse, and then execute complete sensor-fusion functions and versioned quality rules by reusing mathematical graphs?')
fig(1,'research_architecture','Figure 1. Research architecture. Data are synthetic; paceval executes mathematical operations, while C++ controls operation order and final policy.',max_h=190)
tab([['Layer','Actual responsibility'],['Input data','Generate deterministic SPD matrices, synthetic sensor observations and documented model versions.'],['Original paceval SDK 4.25','Evaluate square-root, division, Schur updates, inverse assembly, covariance fusion, mathematical scores and sensitivity graphs.'],['C++ orchestrator','Order dependent pivots, manage matrices and batches, validate domains and select decision labels.'],['Independent scientific audit','Verify every complete matrix entry with NumPy/LAPACK and inspect 80-decimal-digit samples using mpmath.']],[140,CW-140],size=8.0)
p('The research software is a real original SDK integration. No imitation paceval engine, locally precomputed result substitution or hidden external solver is used in the productive C++ matrix path.')

new('3. Complete mathematical definitions')
h2('Full symmetric positive-definite decomposition')
p('For a real SPD matrix A, a lower-triangular factor L exists with positive diagonal entries such that <b>A = L L<super>T</super></b>. A right-looking update forms the diagonal pivot, computes the column below the pivot and updates the trailing Schur complement. These operations run through persistent paceval graphs: <b>sqrt(a)</b>, <b>a/b</b> and <b>a-b*c</b>.')
p('After Cholesky decomposition, the program constructs T = L<super>-1</super> by forward elimination. It then assembles the complete inverse A<super>-1</super> = T<super>T</super>T. The multiplication and accumulation are evaluated through the persistent <b>a+b*c</b> graph. Scalar log-determinant terms use <b>ln(a)</b> and <b>a+2*b</b>.')
h2('Two-sensor information fusion')
p('For independently modeled sensor estimates m₁ and m₂ with covariance matrices P₁ and P₂, the information-form model is <b>P<sub>f</sub> = (P₁<super>-1</super> + P₂<super>-1</super>)<super>-1</super></b>, and the fused estimate is <b>x̂ = P<sub>f</sub> (P₁<super>-1</super>m₁ + P₂<super>-1</super>m₂)</b>. Covariance formation, matrix/vector products and accumulation use paceval graph calls.')
p('Sensor disagreement is quantified using <b>d² = (m₁ − m₂)<super>T</super> (P₁ + P₂)<super>-1</super> (m₁ − m₂)</b>. This covariance describes the difference between independent observations, and is not the fused covariance. The demo treats dimensions and uncertainty scales as normalized synthetic quantities.')
h2('Versioned mathematical gates')
p('A version-specific score combines d², a quadratic temperature term, an uncertainty-radius term and the sensor-disagreement norm. Two distinct score graphs, two signed-margin graphs and two analytical temperature-derivative graphs coexist. The illustrative gate threshold is 12.592, with a separate host classification into ACCEPT, REVIEW and REJECT. This policy is not a statistically calibrated industrial certification rule.')

new('4. Actual paceval execution and graph responsibilities')
p('The public source files paceval_main.h and paceval_main.cpp are integrated into a CMake-based Linux C++ program. The compatible Linux paceval shared library is provided externally. The SDK original copyright notices are maintained; the relative header include is adjusted for standalone build layout.')
tab([['Graph family','Purpose'],['sqrt(a), a/b','Pivot and triangular division'],['a-b*c','Cholesky Schur and forward-inverse updates'],['a+b*c','Inverse assembly and matrix/vector accumulation'],['ln(a), a+2*b','Complete log-determinant'],['a+b, a-b, a*a, abs(a)','Covariance, innovation and derived sensor measures'],['Six distinct versioned graphs','Quality scores, signed margins, temperature derivatives']],[CW*.37,CW*.63])
p('A total of <b>17 distinct graphs</b> were successfully registered and each one executed for actual model inputs. Matrix dependency scheduling remains in C++ because later pivots depend on earlier updates; C++ does not replace the arithmetic graph kernels with native mathematics.')
p('For matrices of dimension n, complete factors, inverses and input matrices are archived as little-endian IEEE-754 binary64 files. The graph execution inventory and registry record the actual function strings, variable declarations, API call counts and graph-output counts.')

new('5. Verified new large-matrix outcomes')
tab([['New execution property','128 × 128','512 × 512'],['Complete inverse entries','16,384','262,144'],['Distinct persistent paceval graphs','17','17'],['Actual graph outputs',f"{s128['graph_outputs']:,}",f"{s512['graph_outputs']:,}"],['Full Cholesky reconstruction','Verified','Verified'],['Full inverse identity','Verified','Verified'],['Independent NumPy inverse','All entries checked','All entries checked'],['Sensor fusion scenarios','32','32'],['Executed quality-surface samples','625','625']],[CW*.45,CW*.275,CW*.275])
h2('Independent numerical verification')
p('An independent implementation loaded every matrix entry and checked the full input SPD matrix, complete Cholesky factor, complete inverse, symmetry, log-determinant and matrix identities against NumPy/LAPACK. An additional independent implementation verified every complete sensor-fusion state, covariance diagonal, model score, signed quality margin and decision. An 80-decimal-place mpmath audit checked 56 values from selected scenarios.')
p('Detailed numerical differences are preserved in the machine-readable audit rather than displayed as C++-versus-paceval accuracy comparisons in this public whitepaper. Results refer to well-conditioned synthetic matrices; general ill-conditioned or indefinite matrices are not certified by these tests.')
p('The supplied source report additionally describes a historical complete 1024-dimensional experiment. That earlier result is not presented as a new run of this project.')

new('6. Dense matrix input and complete factor')
fig(2,'dense_spd_input','Figure 2. Upper-left block of the complete synthetic 512-dimensional SPD input. The full 512 × 512 matrix is available as binary64 data.',max_h=290)
fig(3,'cholesky_factor','Figure 3. Upper-left block of the complete paceval-calculated lower-triangular Cholesky factor.',max_h=265)

new('7. Complete inverse and covariance interpretation')
fig(4,'inverse_matrix','Figure 4. Upper-left block of the complete paceval-calculated SPD inverse, not a selected-entry calculation.',max_h=270)
fig(6,'fused_covariance_ellipses','Figure 5. Illustrative two-coordinate covariance ellipses from selected full six-dimensional paceval sensor-fusion results.',max_h=258)

new('8. Fusion results and innovation gating')
fig(5,'fused_state_versions','Figure 6. Fused first state coordinate from 16 synthetic measurement scenarios across both preserved model versions.',max_h=255)
fig(7,'mahalanobis_scenarios','Figure 7. Normalized sensor innovation across synthetic operating scenarios; large disagreement leads to flagged cases.',max_h=250)

new('9. Versioned mathematical quality decisions')
fig(8,'quality_guard_regions','Figure 8. Signed acceptance margins evaluated in paceval. The host assigns the final research-only decision.',max_h=249)
fig(12,'quality_decision_counts','Figure 9. Synthetic quality outcomes from two independently preserved mathematical score versions.',max_h=241)

new('10. Quality surface evaluated by paceval')
fig(9,'quality_score_surface_3d','Figure 10. Genuine 625-point paceval score surface varying the innovation statistic and operating temperature, model v2.',max_h=355)
p('A complete sweep of 25 × 25 points was submitted to the original paceval multi-graph batch API. The same inputs were evaluated across both score versions, two signed-margin expressions and two analytical derivative expressions. The surface uses the recorded 625-point result file; it is not an interpolated external reference calculation.')

new('11. Industrial gate map and sensitivities')
fig(10,'quality_contour_gate','Figure 11. Executed model-v2 quality contours with the illustrative signed decision boundary.',max_h=255)
fig(11,'temperature_sensitivities','Figure 12. Analytic temperature derivatives from two separate actual paceval graphs.',max_h=252)

new('12. Interpretation and research limitations')
h2('What is actually established')
line('Mathematical feasibility of fully populated dense SPD Cholesky, inversion and log-determinant through the original paceval API.')
line('Two-source covariance fusion including uncertainty and complete six-dimensional state estimates using reusable paceval graph kernels.')
line('Simultaneously available mathematical model versions, signed constraint margins and analytical score sensitivities.')
line('Independent complete-matrix, complete-fusion and selected high-precision checks, all passed.')
h2('What this study does not claim')
p('No real industrial measurement data were used. The six-dimensional observation vectors, covariance coefficients and quality threshold are synthetic. The report therefore does not validate metrological traceability, safety performance, automated actuator control or deployment suitability for any specific machine or component.')
p('The study does not investigate certified TINC interval bounds, arbitrary indefinite matrices, severe ill conditioning, production-grade hardware acceleration, or actual commercial productivity outcomes. The new scientific output is a verified execution and integration demonstration, <b>not</b> an assertion of superiority over specialized matrix libraries.')
h2('Next industrial research stage')
p('A practical follow-up is to run an approved non-actuating shadow system with real multisensor metrology records, separately document physical units and sensor covariance calibration, reserve independent holdout equipment, validate measurement uncertainty, and adopt an approved version/rollback workflow for mathematical score rules. This is a proposed study, not a completed deployment.')

new('13. Reproducibility and scientific references')
h2('Full reproduction from the package')
p('Build: <font face="DVS-Bold">cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so</font>; run <font face="DVS-Bold">cmake --build build</font>, then <font face="DVS-Bold">./build/matrix_sensor_fusion . --n 128</font> and <font face="DVS-Bold">./build/matrix_sensor_fusion . --n 512</font>. Run <font face="DVS-Bold">ctest --test-dir build --output-on-failure</font>.')
p('Independent audit: <font face="DVS-Bold">OPENBLAS_NUM_THREADS=1 python3 src/verify_results.py .</font>. Graph assignment: <font face="DVS-Bold">python3 src/verify_inventory.py .</font>. Regenerate all scientific figures using <font face="DVS-Bold">python3 src/make_figures.py .</font>.')
h2('Dated scientific and technical sources')
refs=[
'[1] Netlib LAPACK, DPOTRF. Official documentation of blocked Cholesky factorization. https://www.netlib.org/lapack/explore-html/d2/d09/group__potrf_ga84e90859b02139934b166e579dd211d4.html',
'[2] Netlib LAPACK, DPOTRS. Official SPD equation-solving documentation. https://www.netlib.org/lapack/explore-html/d3/dc8/group__potrs_ga70a04d13ff2123745a26b1e236212cf7.html',
'[3] Peng et al. sqrtVINS: Robust and Ultrafast Square-Root Filter-based 3D Motion Tracking, 2025, arXiv 2510.10346. Preprint.',
'[4] Cao, Y. Multisensor Data Fusion-Driven Digital Twins in Computer Numerical Control Machining: A Review. Machines 13 (2025), 921. DOI: 10.3390/machines13100921.',
'[5] Frechette, Shao and Pease. Digital Twins Workshops Summary Report. NISTIR 8620 (July 2026). DOI: 10.6028/NIST.IR.8620.',
'[6] NIST, Digital Twins for Advanced Manufacturing program, 2024–2026. https://www.nist.gov/programs-projects/digital-twins-advanced-manufacturing',
'[7] Zhang et al. Hybrid digital twins for smart manufacturing: Architectures, fusion paradigm, and implementation challenges. Journal of Manufacturing Systems 85 (2026). DOI: 10.1016/j.jmsy.2025.12.029.',
'[8] Li et al. Towards adaptive closed-loop optimization: A review of sensor placement for digital twins in mechanical systems. Journal of Manufacturing Systems 88 (October 2026). DOI: 10.1016/j.jmsy.2026.07.027.',
'[9] paceval Mathematical Engine and public API. https://paceval.com/api/; https://github.com/paceval/paceval.'
]
for r in refs:p(html.escape(r),size=7.5,leading=10.5,space=6)
p('Research status as of 13 November 2026: executable original paceval research; synthetic datasets; no physical instrument certification or deployed industrial system.',size=8,leading=11,space=2)
footer();c.showPage();c.save()
print('SUCCESS generated',file,'with',page,'A4 pages')
