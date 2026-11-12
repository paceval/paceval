#!/usr/bin/env python3
"""Reproducible English PDF from audited WP031 data; bounded page layout."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
import csv,json
R=Path(__file__).resolve().parents[1];F=R/'figures';OUT=R/'paceval_Reconfigurable_Robotic_Trajectory_Costs_Whitepaper_EN.pdf';W,H=A4
navy=HexColor('#12364d');teal=HexColor('#008d8e');muted=HexColor('#586f7e')
can=canvas.Canvas(str(OUT),pagesize=A4);can.setTitle('WP031 Reconfigurable Robotic Trajectory Cost Functions | paceval')
body=ParagraphStyle('body',fontName='Helvetica',fontSize=10.1,leading=15.7,textColor=navy)
small=ParagraphStyle('small',parent=body,fontSize=9.1,leading=13.8)
pg=0
def start(title=''):
 global pg
 pg+=1;can.setFillColor(navy);can.rect(0,H-15,W,15,fill=1,stroke=0);can.setStrokeColor(teal);can.line(42,43,W-42,43)
 can.setFillColor(muted);can.setFont('Helvetica',7.5);can.drawString(42,30,'paceval | Reconfigurable Robotic Trajectory Cost Functions | November 2026');can.drawRightString(W-42,30,str(pg))
 if title:
  can.setFillColor(navy);can.setFont('Helvetica-Bold',16.3);can.drawString(42,H-61,title);can.setStrokeColor(teal);can.line(42,H-72,W-42,H-72)
 return H-96
def text(s,y,sm=False):
 p=Paragraph(s,small if sm else body);_,h=p.wrap(W-86,600)
 if y-h<72:raise RuntimeError(f'Page {pg} text overflow {s[:45]}')
 p.drawOn(can,43,y-h);return y-h-(10 if sm else 15)
def title(s,y):
 if y<96:raise RuntimeError('heading overflow')
 can.setFillColor(teal);can.setFont('Helvetica-Bold',11);can.drawString(43,y-13,s);return y-33
def fig(s,y,maxh=330):
 img=ImageReader(str(F/(s+'.png')));iw,ih=img.getSize();w=W-94;h=w*ih/iw
 if h>maxh:h=maxh;w=h*iw/ih
 if y-h<75:raise RuntimeError(f'Page {pg} image overflow {s}')
 can.drawImage(img,(W-w)/2,y-h,width=w,height=h);return y-h-13
def finish():can.showPage()
winners=list(csv.DictReader(open(R/'examples'/'selected_trajectories.csv')))
audit=json.loads((R/'results'/'results_audit.json').read_text())
# cover
start();can.setFillColor(teal);can.setFont('Helvetica-Bold',11);can.drawString(42,H-78,'PACEVAL  |  SCIENTIFIC RESEARCH DEMONSTRATOR')
can.setFillColor(navy);can.setFont('Helvetica-Bold',23);can.drawString(42,H-116,'Reconfigurable Robotic');can.drawString(42,H-148,'Trajectory Cost Functions')
can.setFillColor(muted);can.setFont('Helvetica',11);can.drawString(43,H-170,'Complete-path scoring under alternative industrial priorities')
can.drawImage(ImageReader(str(F/'00_robotic_trajectory_hero.png')),42,H-460,width=W-84,height=265)
y=H-483
y=text('<b>Executed research result.</b> Eight persistent paceval mathematical graphs, 16 deterministic complete-trajectory candidates of 51 samples each, four operating-priority models and one immutable formula revision. The original Linux SDK integration passed 6,783 scalar independent comparisons and 320 batch checks.',y)
y=text('<b>Research scope.</b> Two-joint planar robot, analytical kinematics, finite-difference velocity, acceleration and jerk, two padded disk obstacles, and a host-managed sampled feasibility filter. Neither physical robot hardware nor MoveIt 2 was connected.',y)
y=text('<i>Cover image is a visualization of the actually selected output trajectories, not a photograph or a claim of full industrial robot certification.</i>',y,True);finish()
# intro
y=start('1. Industrial use case and state of the art')
y=text('Industrial robot applications routinely require trade-offs among accurate positioning, controlled motion, obstacle clearance and proximity to kinematic singularities. The preferred trade-off can change between precision assembly, delicate handling and movement through cluttered workspaces.',y)
y=title('Current engineering practice',y)
y=text('Modern motion planning systems compute kinematic states, check scene constraints, and rank or optimize candidate trajectories using chosen cost terms. MoveIt 2 exposes STOMP cost/validity callbacks for sampled full paths; CHOMP is an example of gradient-based motion optimization. Published work also studies jerk-oriented trajectories in industrial robotics. This feasibility study is a standalone numerical kernel, not a replacement for these planners.',y)
y=title('The concrete demonstrated workflow',y)
y=text('A deterministic C++ host generates 16 full joint-space candidates sharing identical start and end states. For each candidate it constructs 51 synchronized samples, computes finite-difference motion features and checks discrete joint and link-obstacle constraints. Persistent paceval execution graphs then evaluate the analytical joint kinematics and alternative cost functions; the host sums per-sample scores and chooses the lowest-cost feasible complete path.',y)
y=title('Industrial question addressed',y)
y=text('Can the same fixed candidate library be rescored under different, versioned mathematical preferences without rebuilding those formulas for each evaluation, and can its outputs be audited independently? The answer is positive for the defined numerical test, while actual industrial performance remains untested.',y)
y=text('Technical sources: MoveIt STOMP task API, CHOMP tutorials and relevant modern jerk-oriented trajectory research are linked in the README and in this report references.',y,True);finish()
# model
y=start('2. Mathematical model and assumptions')
y=text('Planar two-link geometry: lengths l1 = 1.00 m and l2 = 0.78 m. Each candidate has N = 51 joint states, common endpoints, and fixed sample interval dt = 0.08 s (total sampled duration 4.0 s). Joint angles q1 and q2 are measured in radians.',y)
y=title('Forward kinematics and singularity indicator',y)
y=text('<b>x(q)</b> = l1 cos(q1) + l2 cos(q1 + q2)<br/><b>y(q)</b> = l1 sin(q1) + l2 sin(q1 + q2)<br/><b>det(J)</b> = l1 l2 sin(q2).',y)
y=title('Versioned mathematical objective evaluated by paceval',y)
y=text('For each sampled state the registered analytical graph computes a weighted sum of six terms: squared Cartesian tracking error, squared joint velocity, squared joint acceleration, squared joint jerk, a regularized clearance proximity term and a regularized singularity proximity term.',y)
y=text('<b>J(q)</b> = wp ||p(q)-target||² + wv ||v||² + wa ||a||² + wj ||j||² + wo / (0.05 + c²) + ws / (0.1 + det(J)²).',y)
y=text('The scalar full-trajectory objective is the finite sum dt times these sampled costs. The unnormalized weights and regularizers are explicitly synthetic engineering preferences, chosen for a controllable numerical demonstration. The combined score has illustrative units rather than a calibrated physical interpretation.',y)
y=title('Discrete feasibility checks',y)
y=text('The C++ host checks padded segment-to-disk squared-clearance c >= 0, finite-difference joint velocity magnitude <= 2.7 rad/s, acceleration magnitude <= 40 rad/s², and absolute Jacobian determinant >= 0.28 m². These are checks at sampled instants only, not continuous-time certificates. Two fixed padded disks and zero-thickness link centerlines define the idealized scene.',y);finish()
# architecture
y=start('3. Persistent mathematical execution architecture')
y=text('The original paceval_main.h and paceval_main.cpp are compiled from src/ and linked against a separately supplied, compatible paceval Linux shared library. The engine initializes once, creates persistent expression handles, reuses these for every candidate and releases them at shutdown.',y)
y=title('Eight real reusable graph handles',y)
y=text('Three handles compute x(q), y(q) and det(J). Five further handles compute the complete per-sample cost for: precision v1, gentle v1, clearance v1, balanced v1 and gentle v2. Each cost graph contains the kinematics and all weighted mathematical penalties. An update to the gentle-policy jerk coefficient is registered as a new handle rather than overwriting the previous one.',y)
y=title('Explicit C++ / paceval division',y)
y=text('<b>Inside paceval:</b> expression parsing, persistent graph computation, scalar calculation, and packed multi-input batch evaluation. <b>Inside C++:</b> deterministic joint paths, finite-difference features, closest point on each link segment, discrete feasibility, path summation, selection, CSV export and an independently implemented arithmetic oracle.',y)
y=title('Scalar and batch verification',y)
y=text('The application calls paceval_dGetComputationResult for every score and kinematic value. It also invokes paceval_dGetComputationResultExt on 64 packed samples for each of five cost graphs. Each result is checked against the independent native C++ formula using fixed predeclared tolerances; detailed diagnostics are retained in the audit CSV, not printed as an accuracy competition in this Whitepaper.',y)
y=text('A path may be chosen by a different policy while all candidate geometry and feasibility constraints remain unchanged. This is the exact reconfigurability property tested in the experiment.',y);finish()
# numeric
ranks=', '.join(f"{w['policy']} v{w['version']} selects #{w['candidate']}" for w in winners)
y=start('4. Executed test and independently checked results')
y=text('The original paceval runtime executed a complete deterministic trajectory experiment. Unlike the earlier local 20-waypoint greedy demonstration, each alternative here is a whole 51-sample trajectory with common endpoints, and each policy evaluates the same fixed candidate set.',y)
y=title('Executed and audited properties',y)
for line in [f"8 persistent mathematical expression graphs",f"16 complete trajectory candidates, each with 51 samples",f"5 cost-policy versions, four distinct original operating priorities",f"{audit['scalar_comparisons']:,} independent scalar-value comparisons",f"{audit['batch_results']} independently checked packed SDK batch results",f"510 independently checked 80-digit forward-kinematics values",'1/1 CMake/CTest integration test passed']:
 y=text('• '+line,y,True)
y=title('Observed impact of changing the mathematical objective',y)
y=text(ranks+'.',y)
y=text('The precision objective selected candidate 3, the gentle objective candidate 12, and the clearance-priority objective candidate 4. The balanced model selected candidate 3. Both gentle-policy versions remain independently accessible, even when they select the same candidate.',y)
y=text('These are rankings within a fixed, deliberately small candidate library. They are not globally optimal trajectories or certified collision-free robot programs.',y,True);finish()
# figure pages
pages=[('5. Industrial path selection','The actual paceval-scored paths differ depending on the preference selected for the same robot, same endpoints and same obstacles.','01_selected_cartesian_paths','Figure 1. Selected complete Cartesian tool paths and two padded synthetic disks.','02_joint_space_paths','Figure 2. Joint-space curves for the corresponding selected trajectories.'),
('6. Smoothness and sampled feasibility','All candidates are scored as complete sampled paths. Each accepted path satisfies the stated instantaneous finite-grid checks, while unsampled collisions and actuator dynamics remain out of scope.','03_cost_profiles','Figure 3. Weighted objective profiles along selected full candidate paths.','04_sampled_clearance','Figure 4. Minimum squared segment-to-disk margins at individual sampled instants.'),
('7. Candidate ranking and motor positions','Reconfigurable preferences result in distinct score orderings. The model does not manipulate positions between samples to optimize the path; it selects from a frozen finite candidate library.','05_policy_candidate_costs','Figure 5. Feasible complete-candidate costs across the four priority models and revised version.','06_joint_time_profiles','Figure 6. Temporal motion of joint 1 for the selected operating modes.'),
('8. Immutable formula revision and cost map','Changing the jerk weighting creates a separate persistent paceval graph. This supports a traceable before-and-after comparison without invalidating the original expression.','07_immutable_revision','Figure 7. Gentle-mode v1 and v2 instantaneous cost evaluations.','08_discrete_cost_surface','Figure 8. Discrete, masked 3D cost surface of the physically sampled finite candidate set.')]
for section,intro,first,cap,second,cap2 in pages:
 y=start(section);y=text(intro,y);y=fig(first,y,248);y=text(cap,y,True);y=fig(second,y,245);y=text(cap2,y,True);finish()
# limits
y=start('9. Scientific limitations and industrial interpretation')
y=title('What was successfully implemented',y)
y=text('The program evaluates shared analytical robot kinematics and five genuinely versioned mathematical cost functions through the original paceval SDK. It selects among complete candidate paths under unchanged host-enforced sampled feasibility rules. Independent native and 80-decimal-digit calculations, CSV consistency checks and packed SDK evaluations passed on the published dataset.',y)
y=title('What still requires independent engineering work',y)
y=text('The model represents two planar zero-thickness links and exactly two padded circular obstacles. Sampled collision margins do not certify clearance between samples. Its simple joint velocity and acceleration limits do not model torque saturation, rigid-body dynamics, controller tracking errors or real sensor uncertainty. A finite candidate set cannot prove global optimality.',y)
y=title('Relevant next engineering step',y)
y=text('Integrate a documented, physically identified multi-joint robot with a real collision scene and the preferred MoveIt 2 trajectory-optimization workflow. Its STOMP task abstraction accepts a cost/validity callback, making it a natural integration target, but that step must include consistent collision checking, safety constraints, actual timing measurements and any required robot-specific verification.',y)
y=title('Research conclusion',y)
y=text('The additional WP031 contribution is controlled reconfiguration of full-path cost mathematics and demonstrably different complete-path choices. It extends the previous two-joint local waypoint study without claiming a new motion-planning algorithm or operational robot deployment.',y);finish()
# refs
y=start('10. Reproducibility and scientific references')
y=title('Reproduction commands',y)
y=text('Configure: cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so. Build: cmake --build build -j. Test: ctest --test-dir build --output-on-failure. Data: ./build/trajectory_costs --out examples. Independent audits: python3 src/verify_results.py and python3 src/high_precision_reference.py. Figures: python3 src/make_figures.py.',y)
y=title('Audited files',y)
y=text('README.md; src/trajectory_costs.cpp; src/paceval_main.h; src/paceval_main.cpp; src/CMakeLists.txt; examples/trajectory_candidates.csv; examples/selected_trajectories.csv; examples/selected_path_points.csv; examples/formula_registry.csv; examples/numeric_audit.csv; results/high_precision_audit.json; results/results_audit.json; figures/*.png and *.pdf.',y)
y=title('Scientific and technical references',y)
refs=[('MoveIt 2 STOMP composable task API','https://github.com/moveit/moveit2/blob/main/moveit_planners/stomp/include/stomp_moveit/stomp_moveit_task.hpp'),('MoveIt 2 CHOMP planning documentation','https://github.com/moveit/moveit2_tutorials/blob/main/doc/how_to_guides/chomp_planner/chomp_planner_tutorial.rst'),('Time-jerk optimal trajectory planning (2024)','https://doi.org/10.1002/rob.22298'),('paceval official project and API','https://github.com/paceval/paceval')]
for nm,url in refs:y=text('<b>'+nm+'</b>: '+url.replace('&','&amp;'),y,True)
y=text('The report presents synthetic engineering scores for mathematical reproducibility. No real robot, MoveIt 2 service, actual industrial cycle or performance benefit has been experimentally measured.',y,True);finish()
can.save();print('PDF pages',pg,OUT)
