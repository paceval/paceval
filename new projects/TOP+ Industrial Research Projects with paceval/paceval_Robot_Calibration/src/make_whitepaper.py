#!/usr/bin/env python3
"""Rebuild English research whitepaper from the committed example results."""
from pathlib import Path
import argparse, json, csv
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

NAVY=colors.HexColor('#102c3c');TEAL=colors.HexColor('#087f94');LIGHT=colors.HexColor('#eaf4f7');GREY=colors.HexColor('#586c78');GOLD=colors.HexColor('#c96d2d')
font_dir=Path('/usr/share/fonts/truetype/dejavu')
if (font_dir/'DejaVuSans.ttf').exists():
 pdfmetrics.registerFont(TTFont('DVS',str(font_dir/'DejaVuSans.ttf')))
 pdfmetrics.registerFont(TTFont('DVS-Bold',str(font_dir/'DejaVuSans-Bold.ttf')))
 REG='DVS';BOLD='DVS-Bold'
else: REG='Helvetica';BOLD='Helvetica-Bold'
styles={
 'title':ParagraphStyle('RTitle',fontName=BOLD,fontSize=23,leading=28,textColor=NAVY,spaceAfter=14),
 'sub':ParagraphStyle('RSub',fontName=REG,fontSize=12,leading=17,textColor=TEAL,spaceAfter=13),
 'h':ParagraphStyle('RH',fontName=BOLD,fontSize=16,leading=20,textColor=NAVY,spaceAfter=10),
 'h2':ParagraphStyle('RH2',fontName=BOLD,fontSize=11.2,leading=15,textColor=TEAL,spaceBefore=10,spaceAfter=5),
 'body':ParagraphStyle('RB',fontName=REG,fontSize=9.05,leading=14.1,textColor=NAVY,spaceAfter=8),
 'small':ParagraphStyle('RS',fontName=REG,fontSize=8,leading=11.8,textColor=GREY,spaceAfter=6),
 'caption':ParagraphStyle('RC',fontName=REG,fontSize=8,leading=11.3,textColor=GREY,spaceBefore=3,spaceAfter=8),
 'cell':ParagraphStyle('RT',fontName=REG,fontSize=8.15,leading=12,textColor=NAVY),
 'cellbold':ParagraphStyle('RTB',fontName=BOLD,fontSize=8.15,leading=12,textColor=NAVY),
}

def P(text,sty='body'):return Paragraph(text,styles[sty])

def picture(path,width=488,caption=None):
 from PIL import Image as PILImage
 with PILImage.open(path) as im:
  w,h=im.size
 height=width*h/w
 out=[Image(str(path),width=width,height=height)]
 if caption:out.append(P(caption,'caption'))
 return out

def grid(rows,widths):
 cells=[[P(str(c),'cellbold' if j==0 else 'cell') for j,c in enumerate(row)] for row in rows]
 table=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=0)
 table.setStyle(TableStyle([
  ('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.35,colors.HexColor('#cbd8e0')),
  ('LINEBELOW',(0,0),(-1,-2),.35,colors.HexColor('#d8e2e6')),
  ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white,colors.HexColor('#f2f7f8')]),
  ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),7),
  ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)
 ]));return table

def footer(can,doc):
 can.saveState();w,h=A4
 can.setStrokeColor(colors.HexColor('#b7d9df'));can.line(40,38,w-40,38)
 can.setFont(REG,7.3);can.setFillColor(GREY)
 can.drawString(41,24,'paceval  |  independently reproduced synthetic robot-calibration study  |  12 Nov 2026')
 can.drawRightString(w-41,24,str(doc.page));can.restoreState()

def main(root,pdf):
 fig=root/'figures';e=root/'examples';s=json.loads((e/'summary.json').read_text());
 a=json.loads((e/'high_precision_audit.json').read_text())
 doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=47,leftMargin=47,topMargin=52,bottomMargin=53,
   title='paceval - Parameterized Robot Calibration Residuals',author='paceval research demonstrator',
   subject='Six-revolute-joint position calibration, reusable paceval execution graphs and independent validation')
 story=[]
 def nxt(title):story.append(PageBreak());story.append(P(title,'h'))
 def para(t):story.append(P(t))
 def figadd(name,w=465,cap=None):story.extend(picture(fig/(name+'.png'),w,cap))
 # Page 1 - cover
 story.append(P('PACEVAL | EXPERIMENTAL RESEARCH WHITEPAPER','small'))
 story.append(P('Parameterized Robot Calibration Residuals','title'))
 story.append(P('Reusable mathematical execution graphs in a six-joint, position-only kinematic calibration workflow','sub'))
 story.extend(picture(fig/'00_robot_calibration_hero.png',width=500,
     caption='Illustrative robotic metrology scene. No real robot or measurement instrument was operated.'))
 story.append(Spacer(1,15))
 para('<b>Research result.</b> Six reusable paceval graphs computed three Cartesian coordinates and three residuals for an illustrative six-revolute-joint (6R) arm. A separate damped least-squares C++ solver identified nine synthetic kinematic corrections from 120 measured positions and improved prediction on 48 independent positions.')
 story.append(grid([['Holdout RMSE before','%.4f mm'%(s['holdout_rmse_before_m']*1000)],
                    ['Holdout RMSE after','%.5f mm'%(s['holdout_rmse_after_m']*1000)],
                    ['Independent precision check','1,008 / 1,008 residual components passed'],
                    ['Raw TINC audit','24 / 24 sampled values enclosed']],[250,250]))
 story.append(Spacer(1,8));story.append(P('Original paceval 4.25 Linux runtime | GCC 14.2 and Clang 17 | Published source and test data | No performance comparisons','small'))
 # Page 2
 nxt('1. Research question and experimental architecture')
 para('Can reusable mathematical expression graphs evaluate three-dimensional robot kinematics and signed residual components over many measurement poses, while preserving numerical fidelity and supporting independently checked calibration parameters? This study converts the WP-016 research proposal into a controlled executable experiment.')
 para('The original proposal illustrates a two-link planar squared x-coordinate error. We extend it to a six-revolute-joint open chain with measured Cartesian TCP positions, nine estimated parameters, a fixed solver, a distinct held-out pose set and a deliberate non-identifiability control.')
 figadd('01_execution_architecture',465,'Figure 1. Precise separation between persistent paceval mathematics, host-owned optimizer, and independent numerical and observability audits.')
 story.append(P('Scope of calibration','h2'))
 para('The estimated parameter vector is (o1,...,o6, delta_l2, delta_l3, delta_l6). Joint-zero offsets are in radians and link corrections are in metres. The base frame, tool frame and all other link lengths are fixed by the synthetic model. This is <b>position-only calibration</b>; it is not a full six-component pose or commercial-robot calibration.')
 story.append(P('Physics versus numerical correctness','h2'))
 para('Recovering known injected model corrections is a valid software verification, but does not establish model adequacy for a physical robot. Sensor traceability, kinematic frames, unmodeled compliance and real measurement noise would require another study.')
 # Page3
 nxt('2. Six-axis kinematic model and observations')
 para('Six successive intrinsic local rotations follow the sequence Z-Y-Y-X-Y-Z, with translations after each joint rotation. Links 1 and 4 translate along their local z-axis and links 2, 3, 5 and 6 along their local x-axis. Nominal link lengths are (0.45, 0.53, 0.42, 0.16, 0.27, 0.14) metres.')
 para('For each observation i, measured TCP coordinate vector m_i is compared with the model f(q_i,theta). paceval evaluates each signed residual r_i = m_i - f(q_i,theta) in metres. Three coordinate expressions and three signed residual expressions are generated symbolically and provided as persistent calculation objects.')
 figadd('02_workspace_poses',425,'Figure 2. Independent training and withheld measurement configurations in the three-dimensional synthetic workspace.')
 story.append(P('Dataset construction','h2'))
 para('A fixed-seed deterministic generator builds 120 diverse calibration poses and 48 independent holdout poses. Known parameter offsets and bounded deterministic coordinate perturbations generate the measurements. A further 24 repeated poses deliberately lack parameter-identifying information. Complete double-precision CSV inputs are shipped with the program.')
 # Page4
 nxt('3. Direct SDK integration and solver')
 para('The project compiles the original SDK forwarding sources paceval_main.h and paceval_main.cpp and links the separately supplied Linux engine. paceval_CreateComputation creates three FK position graphs, three residual graphs, and a separate interval-mode control graph; the computation handles remain alive for the entire calibration.')
 para('For each parameter iterate, paceval_dGetMultipleComputationsResultsExt calculates residual components in batches. A central finite-difference scheme differentiates <b>these paceval residuals</b> with respect to the nine candidate parameters. The C++ host then forms J^T J and J^T r, solves a damped normal equation and accepts bounded parameter updates only if the sum of squared residuals decreases.')
 figadd('03_calibration_convergence',445,'Figure 3. Actual convergence from the nominal model to the calibrated parameters in four accepted iterations.')
 story.append(P('Mathematical responsibility','h2'))
 para('The native reference model uses explicit 3x3 matrix rotations and translations; it is employed only for synthetic observation generation and independent checks. The optimizer never replaces paceval-calculated residuals with that native model. The mathematical expressions are generated into a checked-in header; Python and SymPy are not needed to run the C++ program.')
 # Page 5
 nxt('4. Independent holdout result')
 para('Parameter fitting uses only the 120 calibration poses. After fitting, both the uncalibrated and calibrated models predict 48 entirely separate joint configurations. The coordinate-level RMSE decreases from <b>%.4f mm to %.5f mm</b>. The final residual is close to the synthetic measurement noise envelope and is not an industrial positioning specification.' % (s['holdout_rmse_before_m']*1000,s['holdout_rmse_after_m']*1000))
 figadd('04_holdout_position_errors',442,'Figure 4. The measured-vs-predicted TCP residual magnitude for every independent holdout configuration, before and after calibration.')
 figadd('07_error_distributions',340,'Figure 5. Distributions of nominal and calibrated TCP errors on the independent holdout set.')
 # Page 6
 nxt('5. Parameter recovery and identifiability')
 para('All nine injected corrections are recovered to a maximum absolute error of %.4g in their respective radian/metre units. The independently calculated sensitivity matrix has a minimum singular value of %.4f for the diverse training poses.' % (a['maximum_parameter_error'],a['training_singular_value_min']))
 figadd('05_parameter_recovery',440,'Figure 6. Known synthetic corrections against fitted zero offsets and link-length changes.')
 figadd('06_observability_spectrum',390,'Figure 7. The full calibration-pose set has numerical column rank nine; 24 identical poses do not. Values at 1e-12 on the plot are a display floor for zero singular values.')
 # Page 7
 nxt('6. Independent 100-digit arithmetic verification')
 para('An independent Python implementation evaluates the same six-joint sequence as 3x3 high-precision matrix products, rather than importing paceval formulas or trusting native C++ test outputs. All 1,008 normal-model and calibrated-model residual components over 168 poses lie within the predeclared numerical tolerance.')
 para('Maximum absolute reference difference: <b>%.3e m</b> across the complete independent audit. A separate NumPy SVD confirms the well-conditioned and rank-deficient pose designs. No numerical error claim is extended beyond the tested input domain and environment.' % a['max_absolute_coordinate_residual_difference_m'])
 figadd('09_high_precision_audit',415,'Figure 8. High-precision maximum residual difference compared with the configured acceptance tolerance.')
 story.append(P('TINC pointwise subexpression experiment','h2'))
 para('Twenty-four distinct synthetic inputs were evaluated for the smooth kinematic subexpression l2*cos(q2+o2). Raw TINC lower and upper outputs were compared against 100-digit evaluations of the actually passed binary64 inputs: <b>24 of 24 contained the reference</b>. This is a sample-wise numerical observation, not a global interval guarantee for the full kinematic model.')
 figadd('08_tinc_widths',355,'Figure 9. Widths of the 24 raw, unmodified TINC intervals for the audited kinematic subexpression.')
 # Page8
 nxt('7. Reproducibility and quality assurance')
 para('The GitHub archive contains a standalone CMake build in src/, the original SDK forwarding sources, the expanded symbolic coordinate and residual graphs, the synthetic input CSVs, the full parameter and holdout results, an independent high-precision audit, image-generation scripts and publication figures.')
 story.append(grid([
  ['Numerical kernel','6 ordinary paceval graphs plus one TINC graph'],
  ['Calibrated parameters','6 encoder offsets (radians) and 3 length corrections (metres)'],
  ['Training / holdout / degenerate','120 / 48 / 24 pose records'],
  ['High precision','1,008 coordinate residual comparisons, 100 decimal digits'],
  ['Reproducibility','Validated fixed-seed data generation and CSV roundtrip'],
  ['Input safety','Nonfinite coordinates, joint range errors and split mismatch rejected'],
  ['Test matrix','GCC, Clang, and ASan/UBSan builds; CTest and CSV replay']
 ],[195,305]))
 story.append(Spacer(1,13))
 story.append(P('Minimal Linux reproduction','h2'))
 para('From repository root, with an independently supplied, compatible original Linux .so:')
 story.append(P('<font name="%s">export PACEVAL_LIB=/absolute/path/to/libpaceval_linux_sharedLIB.so<br/>cmake -S src -B build -DCMAKE_BUILD_TYPE=Release<br/>cmake --build build --parallel<br/>ctest --test-dir build --output-on-failure<br/>./build/robot_calibration --out results --batch 128<br/>python3 src/validate_outputs.py --examples results</font>'%REG,'small'))
 story.append(P('Reproduction boundary','h2'))
 para('The executable requires C++17 and the original paceval engine; the scientific Python audit requires numpy and mpmath, and the optional visualizations and expression regeneration additionally require matplotlib and sympy. The repository does not redistribute the separately licensed original Linux engine binary.')
 # Page9
 nxt('8. Interpretation, applications and sources')
 para('<b>Technical result.</b> This implementation demonstrates that a non-trivial, 6-axis robot kinematic residual model can be compiled to persistent paceval graphs, reused across observations and parameter iterations, embedded within a host-owned nonlinear calibration solver and checked against independently calculated high-precision results. It additionally demonstrates why pose diversity matters for parameter identifiability.')
 para('<b>Research next steps.</b> Extend position-only residuals to orientation residuals on SO(3), model realistic joint-axis parameter changes, introduce sensor covariance and robust outlier handling, select poses to improve observability, and test against independently collected laser-tracker measurements. Independent field validation is necessary before any claim of hardware-specific absolute positioning accuracy.')
 story.append(P('Selected primary literature and documentation','h2'))
 for v in [
 'Lynch, K.M. and Park, F.C., Modern Robotics: Mechanics, Planning, and Control. Northwestern University, chapters on forward kinematics and robot Jacobians. https://modernrobotics.northwestern.edu/',
 'Okamura, K. and Park, F.C., Kinematic calibration using the product of exponentials formula. Robotica (2009). https://www.cambridge.org/core/journals/robotica/article/kinematic-calibration-using-the-product-of-exponentials-formula/8D1CCCF7F714A624B26FE37042432B5A',
 'Kang et al., Two-step calibration of 6-DOF industrial robots by grouping kinematic parameters based on distance constraints. Measurement (2024), 114906. https://www.sciencedirect.com/science/article/pii/S0263224124007917',
 'paceval mathematical engine: original C/C++ API and computation objects. https://paceval.com/api/',
 ]:
  story.append(P(v,'small'));story.append(Spacer(1,6))
 story.append(P('Transparency of evidence','h2'))
 para('All reported success and residual statistics are generated by this synthetically specified demonstrator. The hero graphic is illustrative and is not a photograph of a measurement conducted in this study. No speedup, interval certification, commercial robot validation, safety qualification or production deployment is claimed. The underlying SDK retains its original copyright and AGPL notices; no supplementary license notice file is added.')
 story.append(Spacer(1,15));story.append(P('Research release: November 12, 2026. Whitepaper and all figures are reproducible using the included input data and scripts.','small'))
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 print('PDF generated:',pdf)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
 p=ap.parse_args();main(p.root,p.output)
