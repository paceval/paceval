#!/usr/bin/env python3
"""English standalone PDF. All figures and result numbers come from recorded executed WP26 data."""
from pathlib import Path
import json,html,csv
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from PIL import Image as PImg
R=Path(__file__).resolve().parents[1];OUT=R/'paceval_Robot_Swept_Volume_Collision_Verification_Whitepaper_EN.pdf'
E=json.loads((R/'results/execution_evidence.json').read_text());C=json.loads((R/'results/exact_interval_audit.json').read_text());H=json.loads((R/'results/high_precision_audit.json').read_text())
FONTS='/usr/share/fonts/truetype/dejavu/'
for name,file in [('D','DejaVuSans.ttf'),('DB','DejaVuSans-Bold.ttf'),('DM','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(name,FONTS+file))
pdfmetrics.registerFontFamily('D',normal='D',bold='DB')
INK=HexColor('#242d36');ACC=HexColor('#087f91');GOLD=HexColor('#d99a63');GRAY=HexColor('#59636c');PALE=HexColor('#e9f5f6');LINE=HexColor('#dfe4e8');ALERT=HexColor('#a33340')
stylesheet=getSampleStyleSheet()
for name,kw in [
 ('H',dict(fontName='DB',fontSize=17,leading=22,textColor=INK,spaceAfter=13)),
 ('SH',dict(fontName='DB',fontSize=11,leading=14,textColor=ACC,spaceBefore=11,spaceAfter=6)),
 ('P',dict(fontName='D',fontSize=8.6,leading=14,textColor=INK,spaceAfter=9)),
 ('S',dict(fontName='D',fontSize=7.7,leading=11.5,textColor=GRAY,spaceAfter=7)),
 ('CAP',dict(fontName='D',fontSize=8,leading=12,textColor=GRAY,spaceBefore=4,spaceAfter=10)),
 ('CELL',dict(fontName='D',fontSize=7.6,leading=11,textColor=INK)),
 ('BCELL',dict(fontName='DB',fontSize=7.6,leading=11,textColor=INK)),
 ('EQ',dict(fontName='DM',fontSize=8,leading=12.5,textColor=INK,backColor=PALE,borderPadding=8,spaceAfter=10))]:stylesheet.add(ParagraphStyle(name='WP'+name,**kw))
W,HH=A4;M=44;CW=W-2*M;story=[]
def head(x):story.append(Paragraph(x,stylesheet['WPH']))
def sub(x):story.append(Paragraph(x,stylesheet['WPSH']))
def p(x):story.append(Paragraph(x,stylesheet['WPP']))
def small(x):story.append(Paragraph(x,stylesheet['WPS']))
def eq(x):story.append(Paragraph(html.escape(x),stylesheet['WPEQ']))
def page():story.append(PageBreak())
def table(rows,widths=None):
 data=[[Paragraph(str(y),stylesheet['WPBCELL' if i==0 else 'WPCELL']) for y in row] for i,row in enumerate(rows)]
 t=Table(data,colWidths=widths or [CW/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,0),1,ACC),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor('#f7f9fa')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
 story.append(t);story.append(Spacer(1,9))
def fig(n,title):
 files=sorted((R/'figures').glob(f'fig{n:02d}_*.png'));assert len(files)==1,files
 im=PImg.open(files[0]);iw,ih=im.size;ht=min(248,CW*ih/iw)
 story.append(Image(str(files[0]),width=CW,height=ht));story.append(Paragraph('<b>Figure '+str(n)+'.</b> '+title,stylesheet['WPCAP']))
# page 1
story.append(Spacer(1,680));page()
head('1  Industrial use case and research problem')
p('An industrial robot cell may coordinate the trajectories of multiple tools, grippers and payloads. Discrete waypoint checks ask whether representative geometric states overlap. Continuous swept-volume checking asks a different, stronger question: can the moving bodies intersect at any instant between those checked states? This is particularly important when relative motion is rapid, grazing, or nonuniform. A short collision may be completely absent from a sparse list of samples.')
p('This research demonstrates a precisely scoped mathematical component for that workflow. Two conservatively bounded spherical bodies move along three-dimensional quadratic relative trajectories. Given validated geometric coefficients, radii and a chosen clearance buffer, original paceval computation graphs produce the position, distance, signed margin, first and second derivatives, sensitivities and guarded pointwise status. A C++ host isolates stationary points, evaluates candidate extrema via paceval and records the global numerical minimum. An independently implemented rational Bernstein verifier then establishes whole-interval statements for the exact specified polynomial.')
sub('A concrete hypothetical robot-cell example')
p('Imagine two automation heads passing one another during a synchronized one-second transfer. Their relative x, y and z positions can be approximated by quadratic functions of normalized time. If the heads are conservatively enveloped by bounding spheres, the operator needs to know whether their surface clearance stays positive over the entire transfer. The mathematical kernel answers this narrow geometric question. A real safety application must additionally validate robot joint motion, true geometry, stopping behaviour, tracking errors and the safety-control system.')
sub('What has actually been executed')
table([['Evidence','Actual result'],['Engine', 'Original paceval SDK 4.25 with supplied Linux x86-64 shared library'],['Distinct domain graphs',f"{E['unique_graphs_executed']} of {E['unique_graphs_created']} created graphs executed"],['Trajectory-pair inputs',f"{E['trajectory_pair_count']:,} distinct synthetic cases; {E['model_case_combinations']:,} model outputs"],['Whole-interval exact checks',f"{C['certificate_count']:,} rational Bernstein decisions, {C['uncertified_case_count']} unresolved"],['Independent reference checks',f"{E['native_endvalue_assertions']:,} C++ and {H['independent_checks']:,} high-precision checks"]],[CW*.35,CW*.65]);small('The model parameters are fixed synthetic dyadic rationals. No measurements of an industrial robot cell were provided.')
page()
head('2  Current state of science and industry')
p('Modern collision-checking stacks already include specialist geometric libraries. FCL provides collision, distance and continuous-collision queries for many shapes; MoveIt integrates FCL and Bullet collision environments [1, 2]. The MoveIt OMPL documentation discusses how a motion is discretized into validation steps and why missed intermediate geometry is a meaningful concern [3]. These systems operate on geometries much richer than the spheres considered here.')
p('Jung, Son and Kim presented NeuralSVCD at the 2025 Conference on Robot Learning [4], illustrating current attention to continuous swept-volume detection beyond sparse waypoint states. Recent research on distance fields and continuous robot avoidance further explores smooth geometric representations, including Bernstein-polynomial fields, for articulated robots [5]. The present study is not a new general-purpose collision engine, nor does it claim to replace those specialized components. It isolates a small but mathematically auditable function family suitable for repeated formula evaluation.')
sub('The relevant standards environment')
p('ISO 10218-1:2025 addresses industrial robot safety; ISO 10218-2:2025 addresses industrial robot applications and cells [6]. ISO/TS 15066:2016 also covers collaborative robotic applications, with parts of its content reflected in the newer ISO 10218 series [7]. The standards concern far more than geometric intersection: design, integration, risk reduction, safety-function verification and validation must all be considered. No such conformity assessment was carried out here.')
sub('Position of the paceval mathematical engine')
p('paceval is a formula-to-execution-graph engine. In this study it carries the mathematical expressions used for path evaluation and collision-margin scoring. The C++ host retains domain checks, batch setup, root-search control and the chosen candidate selection. The exact rational verifier intentionally remains independent. The resulting separation of responsibilities is the main technical contribution of the demonstrator; the goal is proven function execution and reproducibility, not an unmeasured speed advantage.')
page()
head('3  Extended mathematical representation')
p('The source WP 26 proposes planar quadratic relative motion and continuous minimization of a squared-distance margin. This study extends the same idea to three Cartesian coordinates. The time variable u is dimensionless and lies between zero and one. A fixed synthetic one-second horizon is assumed. Each coordinate has a second-degree polynomial whose coefficients are in metres. Coefficients and radius values are exact fractions of 1/256, avoiding ambiguity when the separate exact rational certificate is constructed.')
eq('p_j(u) = a_j0 + a_j1*u + a_j2*u^2;   j = x, y, z;   u in [0,1]')
eq('D(u) = p_x(u)^2 + p_y(u)^2 + p_z(u)^2')
eq('R_1 = r1+r2;    R_2 = r1+r2+buffer')
eq('F_v(u) = D(u)-R_v^2;   c_v(u) = sqrt(D(u))-R_v')
p('F is measured in square metres. The surface clearance c is measured in metres. Strict positive F means separated spheres, zero means contact, and negative F means overlap. The two model versions are not competing software algorithms; they represent different geometric assumptions. The V2 buffer is illustrative, not a measured sensor or actuation uncertainty bound.')
sub('Stationary time candidates and analytic sensitivity')
eq("F'(u) = 2 * sum_j( p_j(u) * (a_j1+2*a_j2*u) )")
eq("F''(u) = 2 * sum_j( (a_j1+2*a_j2*u)^2 + 2*a_j2*p_j(u) )")
eq('partial F/partial a_x0 = 2*p_x;  partial F/partial a_x1 = 2*u*p_x')
p('Because F is a quartic, the derivative is cubic. Its distinct real stationary roots within [0,1] and both endpoints are sufficient candidate locations for the global minimum of this exact polynomial. The host isolates those candidate times with a numeric monotonic-interval root method, then queries the original paceval squared-margin graph. The host does not replace these final domain expressions with a native lookup.')
page()
head('4  Whole-interval mathematical verification')
p('A positive minimum at a finite set of time points does not establish strict clearance everywhere. To establish an interval-level result for this particular polynomial class, a separate verifier constructs exact rational power-basis coefficients for F. The polynomial is transformed to the degree-four Bernstein basis over each candidate interval. The Bernstein basis is nonnegative and sums to one. Consequently, the minimum and maximum control coefficients enclose the polynomial values throughout that entire interval [8].')
eq('min_i(b_i) <= F(u) <= max_i(b_i),  for all u in the tested subinterval')
p('The verifier recursively subdivides the interval at exact rational midpoints. When every Bernstein coefficient is strictly positive, the whole subinterval is proved separated. An exactly negative rational evaluation certifies an overlapping instant. An exact zero proves a contacting instant. A returned contact-only classification means the remaining investigated intervals also have nonnegative enclosures. The algorithm has a bounded subdivision depth and would explicitly return UNRESOLVED if it could not determine a classification; no such case occurred in this specific dataset.')
sub('Why the mathematical qualifier matters')
p('The input coordinates and radii are deliberately exact dyadic fractions. The Bernstein reasoning is exact rational arithmetic on the polynomial defined by those numbers. It does not prove that physical robot trajectories follow the polynomial, that a spherical approximation encloses every real link in every pose, that hardware actually moves as commanded, or that any controller and sensor are safety certified. The independently tested floating-point paceval values also do not automatically inherit a formal rounding certificate from the exact rational reference. These are distinct claims.')
sub('TINC is not silently substituted for a proof')
p('The paceval SDK supports pointwise Trusted Interval Computation (TINC), but checking finitely many times is not equivalent to proving a bound over all u. This research therefore uses the explicit exact rational Bernstein implementation for the interval decision and keeps paceval responsible for the original mathematical graph evaluations. The two are separately checked and clearly labeled.')
page()
head('5  Demonstrated original paceval functions')
p('The application contains two concurrently available graph families and a separate graph group for between-version comparisons. The original SDK performs the physical expressions for three-dimensional position, velocity, Euclidean distance, effective bounding radius, squared and surface margin, first and second derivatives, relative speed, negative-margin penalty, normalized margin score and analytically derived sensitivities.')
table([['Function / purpose','Actual executor','Graph ID or technical reason'],['3D position, velocity and distance','paceval','V1/V2: RELATIVE_*, VELOCITY_*, DISTANCE_*'],['Squared clearance and surface clearance','paceval','V1/V2: SQUARED_MARGIN, SIGNED_CLEARANCE'],['First/second time derivative','paceval','V1/V2: DERIVATIVE_TIME, SECOND_DERIVATIVE'],['Penalty, normalization, Boolean guard','paceval','V1/V2: NEGATIVE_MARGIN, NORM_MARGIN, POINTWISE_GUARD'],['Sensitivity to initial path, velocity and buffer','paceval','V1/V2: SENS_X0, SENS_X1, SENS_BUFFER'],['Mathematical model changes','paceval','COMPARE: MARGIN_DELTA, CLEARANCE_DELTA, BOTH_POINTWISE'],['Continuous root isolation','C++ host','Stateful cubic root splitting and bisection'],['Global minimum selection','C++ host','Compare paceval-evaluated candidates'],['Exact independent interval proof','Python reference','Fraction + Bernstein subdivision']],[CW*.39,CW*.20,CW*.41])
p('Each mathematical main-data graph was created and executed, not merely registered. The original scalar evaluation API, the multiple-graph batch API and their output ordering were exercised. Operator selftests separately confirm logical guards, comparisons, infix min/max and signed modulo semantics with the current library.')
page()
head('6  Test design and numerical evidence')
p('The fixed generator produces 4,096 unique relative trajectories in four synthetic families: intersecting, widely separated, accelerated and near-buffer paths. Special records include a narrowly missed intersection, exact midpoint tangency, endpoint contact, static overlap and near separation that changes under radius inflation. All inputs are canonical decimal representations of exact dyadic fractions. The C++ input validator rejects numeric expressions, nonfinite literals, malformed CSV widths and invalid radius domains.')
sub('What the independent numerical checks examine')
p('The C++ reference calculates squared distance, clearance, first derivatives, relative speed and sensitivities by a separate arithmetic path. A second independent 90-digit mpmath implementation evaluates physical expressions and finds the global minimum by an independently implemented cubic root-enumeration routine. These controls cover complete end values, rather than simply checking that formula registration succeeded. Detailed accuracy comparisons are retained in machine-readable audit files but are intentionally absent from the public publication.')
sub('A stronger but narrower exact classification')
p('For every one of the 8,192 version/scenario combinations, the separate rational Bernstein implementation examines the entire normalized time domain and produces a separation proof, an overlap witness or a contact-only proof, with a specified unresolved fallback. Because the input family has exact dyadic coefficients and a quartic distance law, these classifications are fully reproducible at the algebraic-model level.')
table([['Independent check type','Recorded result'],['Native C++ full-output assertions',f"{E['native_endvalue_assertions']:,} passed"],['90-decimal independent numerical assertions',f"{H['independent_checks']:,} passed"],['Exact Bernstein model interval classifications',f"{C['certificate_count']:,} resolved"],['Unresolved interval cases',f"{C['uncertified_case_count']}"],['Original SDK batch and operator tests','Executed; see CTest and audit logs']],[CW*.61,CW*.39])
page()
head('7  Recorded outcomes and a missed collision')
p('The main experiment shows why the endpoint-and-stationary-point examination matters. The coarse 32-interval grid reported a positive margin for two V1 trajectories and three V2 trajectories that nevertheless contained genuine geometric overlap in the original mathematical model. The independent rational certificates provide overlap witnesses and confirm the classification.')
table([['Whole-interval mathematical status','V1','V2'],['Strictly separated',f"{E['separated_V1']:,}",f"{E['separated_V2']:,}"],['At least one overlap witness',f"{E['overlap_V1']:,}",f"{E['overlap_V2']:,}"],['Contact without overlap',f"{E['near_tangent_V1']:,}",f"{E['near_tangent_V2']:,}"],['Unresolved','0','0']],[CW*.56,CW*.22,CW*.22])
sub('A reproducible narrow-collision counterexample')
p('Synthetic record T00000 sets x(u) = -2.015625 + 4u, y(u) = z(u) = 0 and R1 = 0.0078125 m. The exact minimum occurs at u = 0.50390625, where the squared margin is -0.00006103515625 m². The sampled 32-interval grid nevertheless observes a positive minimum of 0.00018310546875 m². This is an explicit instance in which the raster does not detect a short collision. It does not depend on unrecorded industrial measurements.')
sub('Effect of model versioning')
p('Inflating the nominal collision radius by the selected buffer produces more mathematical overlaps in the same input set. This is consistent with the definition of V2 and is not evidence about any real manufacturer sensor or robot tracking uncertainty. Tangential contact is retained as its own state rather than silently being called collision-free. The dense path plots and 3D figures were generated only from saved original paceval output values.')
page()
head('8  Figure evidence: missed overlap and buffer influence')
fig(1,'A narrow negative margin occurs between the 32-step sample times, while a dense graph evaluation shows the crossing. The underlying classification has an independent exact rational overlap witness.')
fig(2,'A fixed geometric buffer changes the sign of the surface clearance for a near-miss example. V1 and V2 are two physical model assumptions, not two numerical solvers.')
page()
head('9  Figure evidence: sampled and continuous minima')
fig(3,'The C++ host selects minima from paceval-evaluated stationary candidates. Crosses identify synthetic trajectories that a positive-margin coarse grid would have missed.')
fig(4,'Recorded minimum squared-margin distributions across both graph families. Their difference follows the added radius in V2.')
page()
head('10  Figure evidence: model versioning and proof status')
fig(5,'Difference of the recorded V2 and V1 minimum margins under conservative buffer inflation.')
fig(6,'All 8,192 exact rational interval classifications, distinguishing strict separation, overlapping witnesses and contact-only cases.')
page()
head('11  Figure evidence: minimum timing and tangency')
fig(7,'Location of the selected minimum during the normalized time interval. Interior minima demonstrate why testing only endpoints is insufficient.')
fig(8,'Analytic paceval first-derivative values across a designed exact tangency; the stationary point occurs at the contact.')
page()
head('12  Figure evidence: geometric and 3D parameter views')
fig(9,'Three-dimensional relative paths from the actual paceval position graphs, sampled for illustrative synthetic cases. This is not an articulated-arm mesh.')
fig(10,'A three-dimensional input/output parameter view generated from recorded V2 margin results for the near-buffer trajectory group.')
page()
head('13  Reproduction, claims and limitations')
p('The project contains the original SDK header and integration wrapper, CMake, canonical synthetic input CSV, executed result CSV files, an auditable graph inventory, exact rational Bernstein certificates, independent high-precision numerical checks and ten scientific diagrams in PNG and vector PDF. The compatible original Linux shared library is intentionally not redistributed. The main code is standard C++17 and uses no third-party C++ numerical libraries.')
p('A local CTest suite performs the original SDK selftest, CSV-to-paceval-to-CSV main flow, exact interval verification, independent numerical checks, archive-wide GitHub-mathematics validation and its negative regression test. GitHub itself has not been interacted with, and no online GitHub preview or repository publication is claimed. The full technical details of numeric tolerances remain in the internal audit records.')
sub('What is and is not established')
p('Established within this study: a connected set of original paceval graph computations is executed for real synthetic program inputs, its outputs agree with independently programmed model calculations on the tested values, and a separate exact rational interval algorithm produces valid entire-interval classifications for all specified quartic models. Not established: actual robot collision clearance, effectiveness of real protective stop functions, compliance with ISO 10218, applicability of the assumed spherical enclosure to complete articulated geometry, or robustness to unmodeled hardware errors.')
sub('A meaningful subsequent industrial study')
p('Integrate verified articulated-link forward kinematics, conservative capsule or mesh geometry, controller-sourced timestamped trajectories and measured motion tracking error. Run a specialist CCD library and a continuous bounded mathematical checker on matched datasets, including tangencies and high-curvature motions. Keep the robot-cell functional safety case separate from this preliminary mathematical demonstration.')
page()
head('14  Scientific and technical references')
refs=[
 ('[1]','Flexible Collision Library, ROS indexed package','https://index.ros.org/p/fcl/'),
 ('[2]','MoveIt, developer collision detection concepts','https://moveit.ai/documentation/concepts/developer_concepts/'),
 ('[3]','MoveIt/OMPL, motion edge discretization tutorial','https://moveit.github.io/moveit_tutorials/doc/ompl_interface/ompl_interface_tutorial.html'),
 ('[4]','Jung, Son, Kim. NeuralSVCD for Efficient Swept Volume Collision Detection. CoRL 2025','https://proceedings.mlr.press/v305/jung25e.html'),
 ('[5]','Real-time collision avoidance with robot distance fields. Robotics and Autonomous Systems, 2026','https://doi.org/10.1016/j.robot.2026.105394'),
 ('[6]','ISO robotics standards, including ISO 10218-1:2025 and -2:2025','https://www.iso.org/sectors/engineering/robotics'),
 ('[7]','ISO/TS 15066:2016. Collaborative robot technical specification','https://committee.iso.org/standard/62996.html'),
 ('[8]','Reliable Computing, Bernstein subdivision and convex-hull bound property','https://interval.louisiana.edu/reliable-computing-journal/volume-14/reliable-computing-14-pp-117-137.pdf'),
 ('[9]','Continuous Collision Detection benchmark and reference approach','https://continuous-collision-detection.github.io/'),
 ('[10]','paceval original C/C++ API documentation','https://paceval.com/api/'),
]
for code,title,url in refs:
 p(html.escape(code)+' <link href="'+html.escape(url,quote=True)+'" color="#087f91">'+html.escape(title)+'</link>')
sub('Boundary between the original brief and this executed experiment')
p('The source WP 26 dated 13 November 2026 is a proposed study that made no experimental result claims. The three-dimensional extension, exact-dyadic dataset, specific full-interval Bernstein test, original paceval graph evaluation and documented measurements of the synthetic mathematical outputs were produced in this implementation. Context sources provide scientific background only and do not establish the paceval outputs.')
small('Research artifact date: 15 November 2026. No safety certification, commissioning, production deployment or customer validation is implied.')
def cover(c,doc):
 c.saveState();hero=ImageReader(str(R/'figures/00_robot_swept_volume_hero_2400x1200.png'));c.drawImage(hero,0,HH-410,width=W,height=410,preserveAspectRatio=False)
 c.setFillColor(INK);c.rect(0,0,W,HH-410,stroke=0,fill=1);c.setStrokeColor(GOLD);c.setLineWidth(3.5);c.line(M,HH-421,W-M,HH-421)
 c.setFillColor(HexColor('#aedfe4'));c.setFont('DB',10);c.drawString(M,HH-456,'PACEVAL.   ROBOTICS & AUTOMATION   /   WP 26')
 c.setFillColor(colors.white);c.setFont('DB',21);c.drawString(M,HH-498,'Continuous Robot Swept-Volume')
 c.drawString(M,HH-528,'Collision Margin Verification')
 c.setFillColor(HexColor('#d4e5e7'));c.setFont('D',10.3);c.drawString(M,HH-568,'3D trajectory geometry, independent interval evidence,')
 c.drawString(M,HH-586,'and executable mathematical graphs with paceval')
 c.setFillColor(HexColor('#bdcbd0'));c.setFont('D',8.3);c.drawString(M,44,'Original paceval 4.25  |  Mathematics research  |  15 November 2026')
 c.restoreState()
def footer(c,doc):
 c.saveState();c.setStrokeColor(LINE);c.line(M,HH-39,W-M,HH-39);c.setFillColor(ACC);c.setFont('DB',8);c.drawString(M,HH-28,'paceval. / Continuous robot collision-margin research')
 c.setFillColor(GRAY);c.setFont('D',7);c.drawString(M,27,'Exact polynomial evidence is not industrial safety certification');c.drawRightString(W-M,27,f'{doc.page:02d}');c.restoreState()
doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=M,rightMargin=M,topMargin=57,bottomMargin=46,title='Continuous Robot Swept-Volume Collision Margin Verification with paceval',author='paceval mathematical research demonstration',subject='Original paceval C++ graph execution and independently certified polynomial intervals')
doc.build(story,onFirstPage=cover,onLaterPages=footer)
print('PDF GENERATED',OUT)
