#!/usr/bin/env python3
"""Create the English WP_044 PDF from independently verified original-SDK outputs.
The PDF uses page-controlled layouts and correctly rendered mathematical equations;
no literal LaTeX code appears as unformatted Markdown.
"""
from pathlib import Path
import csv,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as Pil
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
R=Path(__file__).resolve().parents[1];F=R/'figures';RUN=json.loads((R/'results/execution_summary.json').read_text());AUD=json.loads((R/'results/high_precision_audit.json').read_text());assert AUD['status']=='passed' and RUN['paceval_persistent_graphs']==28
CON=list(csv.DictReader((R/'examples/grid_convergence.csv').open()));OUTPUT=R/'paceval_Bulk_Wave_Kernels_Whitepaper_EN.pdf'
for name,file in [('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,file))
NAVY=HexColor('#112743');TEAL=HexColor('#167b9a');SLATE=HexColor('#617180');BLUE=HexColor('#eaf5f9');LIGHT=HexColor('#f3f7f9');ORANGE=HexColor('#dd9949');DARK=HexColor('#101b32')
S={'title':ParagraphStyle('Cover',fontName='DejaVu-Bold',fontSize=23,leading=31,textColor=NAVY,spaceAfter=14),
'subtitle':ParagraphStyle('ST',fontName='DejaVu',fontSize=11.2,leading=17,textColor=TEAL,spaceAfter=15),
'h':ParagraphStyle('H',fontName='DejaVu-Bold',fontSize=17,leading=23,textColor=NAVY,spaceAfter=12),
's':ParagraphStyle('S',fontName='DejaVu-Bold',fontSize=11,leading=15,textColor=TEAL,spaceBefore=9,spaceAfter=5),
'b':ParagraphStyle('B',fontName='DejaVu',fontSize=9.1,leading=14.3,textColor=NAVY,spaceAfter=8),
'small':ParagraphStyle('Sm',fontName='DejaVu',fontSize=8.0,leading=12,textColor=SLATE,spaceAfter=7),
'cap':ParagraphStyle('Cap',fontName='DejaVu',fontSize=7.7,leading=10.5,textColor=SLATE,spaceAfter=9,alignment=TA_CENTER),
'cell':ParagraphStyle('Cell',fontName='DejaVu',fontSize=7.85,leading=11.3,textColor=NAVY),
'cellB':ParagraphStyle('CB',fontName='DejaVu-Bold',fontSize=7.9,leading=11.3,textColor=NAVY)}
STORY=[]
def p(t,k='b'):STORY.append(Paragraph(t,S[k]))
def h(t):p(t,'h')
def sub(t):p(t,'s')
def page():STORY.append(PageBreak())
def space(h=8):STORY.append(Spacer(1,h))
def fig(name,caption,width=474,maxh=248):
 path=F/(name+'.png');im=Pil.open(path);w,h=im.size;f=min(width/w,maxh/h);STORY.append(KeepTogether([Image(str(path),w*f,h*f),Paragraph(caption,S['cap'])]))
def img(name,width=470,maxh=234):
 path=F/(name+'.png');im=Pil.open(path);w,h=im.size;f=min(width/w,maxh/h);STORY.append(Image(str(path),w*f,h*f))
def tab(rows,widths=None):
 data=[[Paragraph(str(c),S['cellB' if i==0 else 'cell']) for c in row] for i,row in enumerate(rows)]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,LIGHT]),('LINEBELOW',(0,0),(-1,0),.75,TEAL),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9)]));STORY.append(t);space(9)
def eq(name,tex):
 path=F/(name+'.png');figure=plt.figure(figsize=(10,.68),facecolor='white');figure.text(.03,.47,'$'+tex+'$',ha='left',va='center',fontsize=19,color='#193b5b');figure.savefig(path,dpi=170,bbox_inches='tight',pad_inches=.12);plt.close(figure)
eq('_eq_wave',r'h_{tt}=h_{zz}-\frac{3}{z}h_z-(k^2+q+\delta)h+S(t,z)')
eq('_eq_operator',r'D_zh_i=\frac{h_{i+1}-h_{i-1}}{2\Delta z},\qquad D_{zz}h_i=\frac{h_{i+1}-2h_i+h_{i-1}}{(\Delta z)^2}')
eq('_eq_bessel',r'h_B(t,z)=a\,z^2J_2(mz)\cos(\omega t),\quad\omega^2=k^2+q+m^2')
eq('_eq_zero',r'h_0(t,z)=a(1+0.08z^4)\cos(\omega t),\quad\omega^2=k^2+q+\delta')
eq('_eq_mms',r'h_M(t,z)=az^2\sin(mz)\cos(\omega t)')
eq('_eq_source',r'S=a\cos(\omega t)[(k^2+q-\omega^2+m^2)z^2\sin(mz)+4\sin(mz)-mz\cos(mz)]')
eq('_eq_energy',r'E=\frac{1}{2}\int_1^2z^{-3}(h_t^2+h_z^2+(k^2+q)h^2)\,dz')
eq('_eq_flux',r'F=-z^{-3}h_t h_z,\qquad \Delta a=-\delta h')
# 1 cover
p('PACEVAL  |  SCIENTIFIC RESEARCH DEMONSTRATOR','subtitle')
p('Parameterized Bulk-Wave<br/>Evaluation Kernels<br/>with paceval','title')
p('AdS5-inspired Fourier-mode waves, reusable analytical kernels, verified numerical convergence, real Multi-Graph-Batch execution and mathematically controlled formula revisions.','subtitle')
img('00_bulk_wave_hero',480,240)
p('Title image: original conceptual visualization of a warped bulk wave. It is not a measured or experimentally discovered gravitational phenomenon. The numbered scientific figures use the actual computation outputs.','small')
space(10)
p('<b>Verified scope:</b> 28 reusable original-SDK mathematical graphs; 663,784 real batch results; 12 completed PDE time integrations; 2,779 independent 80-digit reference checks passed; CTest succeeded.','small')
p('13 November 2026  |  English research whitepaper  |  WP_044','small')
page()
# 2 use case
h('1. Research use case and current scientific context')
p('Computational physics and engineering workflows often solve a time-dependent PDE while repeatedly evaluating parameterized mathematical expressions over a spatial discretization. Interchangeable expressions are useful in reduced-order wave physics, spectral mode calculations, numerical-code verification, inverse modelling and repeated parameter surveys. The present study investigates whether the original paceval engine can act as an explicit and auditable mathematical execution layer inside such a workflow.')
p('The original WP_044 proposal describes the bulk-wave acceleration h_tt = -k² h + h_zz - 3 h_z/z. This is consistent with the spatial operator appearing after Fourier separation in an AdS5 conformal-coordinate model. Its exact physical interpretation depends on gauge choice, polarization, boundary or junction conditions and the gravitational theory, none of which is inferred from a successful numerical run alone.')
sub('Scientific point of comparison')
p('The Randall–Sundrum literature describes graviton radial modes in conformal coordinates with Bessel functions of order two. Numerical verification practice, including the NIST approach to the method of manufactured solutions, distinguishes correctness of an implementation from validation of its real-world physical model.')
tab([['What this executable delivers','What it does not imply'],['Real reusable paceval expression handles','No observation of extra dimensions'],['Second-order finite-difference convergence on analytic modes','No real gravitational-wave detection'],['Source, RHS, energy, parameter and versioned expressions','No nonlinear 5D Einstein evolution'],['Deterministic finite-domain RK4 experiment','No proof of faster-than-light communication']],[238,244])
page()
#3
h('2. Mathematical model and coordinate domain')
p('The controlled problem is a linear Fourier-mode field on a fixed conformal bulk coordinate interval z in [1, 2]. The coefficient of h_z is inherited from the five-dimensional conformal metric. The additional potential q is a dimensionless numerical test parameter, not a derived physical particle mass. The separately versioned delta modifies that potential without overwriting the baseline graph.')
img('_eq_wave',470,85)
p('Here k is the Fourier wave number along a suppressed spatial direction, t and z are dimensionless and S is a deliberately specified manufactured source. Boundary values are the exact solution at z=1 and z=2, so boundary work may cause the energy within this finite interval to change.')
sub('Admissible research input domain')
tab([['Variable','Controlled range or value'],['z','1.0 to 2.0 (away from coordinate singularity z=0)'],['k','Positive, with sweeps from 0.55 to 2.75'],['q','Nonnegative numerical potential; sweep 0.10 to 1.20'],['delta','Zero in baseline; 0.55 in versioned homogeneous case'],['time horizon','0.6 dimensionless time units'],['spatial grids','25, 49, 97 nodes; refinement ratio 2'],['time integrator','Classical RK4 with timestep <= 0.30 spatial interval']],[165,317])
p('The full metric and physical polarization constraints are not evolved by this scalar test harness. No ad hoc physical unit system is imposed on these normalized modes.','small')
page()
#4
h('3. Independent exact modes and test forcing')
p('The study uses three mathematically distinct radial profiles and a fourth versioned copy of the zero mode. Exact solutions and prescribed Dirichlet boundaries are constructed independently from the paceval acceleration graph.')
sub('Homogeneous polynomial zero mode')
img('_eq_zero',470,72)
p('For the unmodified zero mode, q and delta are zero; in the revision, delta is 0.55 and the exact frequency is changed consistently. The radial operator annihilates both the constant and z-to-the-fourth components in the continuum equation.')
sub('Homogeneous oscillatory Bessel mode')
img('_eq_bessel',470,74)
p('The order-two Bessel function comes from the exact homogeneous radial equation. C++ uses its standard-library implementation only to provide initial and Dirichlet data; the interior PDE acceleration is evaluated by paceval.')
sub('Forced manufactured mode')
img('_eq_mms',465,58)
img('_eq_source',470,90)
p('The forcing is part of the actual paceval RHS, not a post-hoc adjustment. Choosing an exact field plus the corresponding source is a recognized numerical-code verification technique. This test does not claim a physically excited gravitational source.','small')
page()
#5
h('4. Spatial operators, integration and energy diagnostics')
p('Centered finite differences approximate the two radial derivatives. The paceval engine evaluates those differences, their warped combination and the complete right-hand side. C++ advances the coupled first-order state using a fixed-step fourth-order Runge–Kutta algorithm, imposing exact boundary values at each intermediate stage.')
img('_eq_operator',474,78)
p('For smooth modes, centered differences have a second-order truncation error in space; with a time increment proportional to the mesh width, the fourth-order time-stepping error is smaller and the observed spatial convergence should approach order two.')
sub('Weighted energy and boundary exchange')
img('_eq_energy',470,70)
img('_eq_flux',470,68)
p('The weighted energy density and the flux proxy are both computed with persistent paceval expressions. Energy in the finite interval need not remain constant because Dirichlet boundaries move with the exact mode and because the manufactured test contains a source. Reported energy is a numerical diagnostic, not an assertion about conserved physical gravitational energy in a curved spacetime.')
page()
#6
h('5. Actual original-SDK paceval execution')
p('The C++ executable initializes the original paceval shared runtime, registers 28 expression handles once, and repeatedly evaluates subsets of these handles through the real Multi-Graph-Batch API. Every registered expression is actually exercised by the 7,623-point parameter survey. The dynamics use selected full RHS, weighted energy, error and flux graphs.')
tab([['Mathematical function family','Actual execution owner'],['Warped first and second spatial differences','paceval: reusable graphs'],['Complete Fourier-mode acceleration, forced RHS','paceval: full expressions'],['Independent revision of RHS and potential','paceval: separate persistent graphs'],['Analytical source, exact manufactured field and sensitivities','paceval: reusable expressions'],['Energy density, flux, source power and residuals','paceval: reusable expressions'],['Stateful RK4 stepping, boundary assignment, state storage','C++: numerical orchestration'],['Bessel J2 exact boundary/initial reference','C++: standard-library special function'],['Independent 80-digit oracle','Python mpmath: validation only']],[256,226])
p('The SDK interface returns a false status on successful multi-graph calls in this library revision; the implementation additionally checks the returned per-output error codes. Scalar-host and independently evaluated mathematical expressions are never counted as paceval graphs.')
p('The detailed expression strings, actual API route and execution owner are recorded in examples/formula_registry.csv and results/math_execution_inventory.csv.','small')
page()
#7 numbers
h('6. Reproduced executable outcomes')
tab([['Quantity','Actual value'],['Original persistent paceval expression graphs',str(RUN['paceval_persistent_graphs'])],['Successful original Multi-Graph-Batch calls',f"{RUN['multi_graph_batch_calls']:,}"],['Successfully evaluated paceval outputs',f"{RUN['paceval_batch_outputs']:,}"],['Analytic or manufactured mode cases','4'],['Spatial resolutions for each case','25, 49, 97 grid points'],['Complete RK4 field simulations','12'],['Parameterized surface evaluation positions',f"{RUN['parameter_surface_points']:,}"],['C++ independent mathematical spot checks',f"{RUN['host_native_oracle_checks']:,}"],['Independent 80-decimal-digit values',f"{AUD['independently_checked_values']:,} passed"],['Maximum observed final L2 error',f"{RUN['max_final_L2_error']:.6g}"],['Real CMake/CTest original-SDK test','1 / 1 passed']],[270,212])
p('The four cases are deterministic and deliberately constructed to allow an exact mathematical reference. A second-order convergent trajectory is not evidence that the physical AdS5 model is the unique or correct theory for any observed universe.')
sub('Source-data and output provenance')
p('There are no measured laboratory, astronomical or gravitational-wave datasets in this package. The numerical dataset consists of dimensionless analytic initial and boundary values, exactly specified forcing and actual paceval C++ calculation outputs. The conceptual cover is not used as scientific data.')
page()
#8
h('7. Numerical mode profiles and bulk-coordinate evolution')
fig('01_four_modes_final_profiles','Figure 1. Four paceval-integrated final profiles (solid) alongside independent exact reference solutions (dashed).',470,227)
fig('02_bessel_spacetime_heatmap','Figure 2. Actual Bessel-mode field values at logged time slices over the bulk coordinate.',470,225)
page()
#9
h('8. Three-dimensional field and time-dependent error')
fig('03_bessel_spacetime_surface_3d','Figure 3. Genuine 3D visualization of the calculated Bessel-mode trajectory, not a simulated gravitational-wave detector.',472,230)
fig('12_error_time_history','Figure 12. Field accuracy histories of all four test modes at 97 grid points.',470,226)
page()
#10
h('9. Verification of spatial discretization order')
fig('04_second_order_spatial_convergence','Figure 4. L2 error versus spatial step, showing systematic refinement towards the independently known analytic solutions.',470,222)
fig('05_observed_order','Figure 5. All four mode families approach the second-order accuracy of the centered spatial stencil.',470,226)
page()
#11
h('10. Operator residual and manufactured forcing checks')
fig('06_discrete_operator_residuals','Figure 6. Finite-difference operator residual against each exact continuum wave acceleration.',470,220)
fig('08_manufactured_source_and_acceleration','Figure 8. Real paceval source and numerical acceleration compared with the analytical manufactured acceleration.',470,225)
page()
#12
h('11. Energy on a driven finite-domain interval')
fig('07_weighted_energy_and_boundary_flux','Figure 7. Weighted wave-field energy and estimated boundary flux, evaluated from paceval graph outputs.',475,260)
p('The boundary data are time dependent. Consequently, a changing finite-domain energy is expected rather than evidence of a numerical instability or nonconservation of the full physical system. The present mesh-based flux is a diagnostic, not a demonstrated convergence of an independently derived continuum balance. An explicit high-order energy-flux audit remains a future experiment.')
sub('Practical numerical implication')
p('The model supplies a useful architectural pattern: a physical or geometric kernel can be replaced or versioned without rewriting the C++ state integrator. The scientific usefulness of that architectural separation still depends on model appropriateness, stability and independent validation.')
page()
#13
h('12. Bulk-wave parameter surfaces and numerical potential')
fig('09_parameterized_rhs_surface_3d','Figure 9. 3D acceleration of a fixed probe field (manufactured source disabled), generated by the real paceval graph sweep.',471,234)
fig('10_potential_parameter_contours','Figure 10. Unforced probe-field acceleration as the numerical potential q varies, with all other model inputs controlled.',470,217)
page()
#14
h('13. Mathematical versioning and sensitivities')
fig('11_versioned_rhs_difference','Figure 11. Independently registered formula-version difference, not a physical detection or new dispersion law.',470,268)
p('The baseline RHS is retained unchanged. An additional registered expression subtracts delta times the field, so the revision is locally auditable. Explicit paceval sensitivities with respect to k, q and delta, together with versioned energy density and change functions, are included in the 28-graph registry and exercised by the parameter sweep.')
p('Parameter gradients represent derivatives of the defined computational expressions. They cannot by themselves establish an independently meaningful physical interpretation for the tunable numerical potential.')
page()
#15
h('14. Scientific interpretation, limitations and next steps')
sub('What has been established')
p('The mathematical wave kernel is reusable and can be evaluated at many spatial points, time steps and parameter combinations with the actual paceval SDK. The independently specified analytic and manufactured solutions display the expected second-order spatial convergence. Multiple versioned expressions remain available, and core mathematical functions are executed by paceval rather than replaced with C++ numeric approximations.')
sub('What has not been established')
p('This study does not solve nonlinear Einstein equations or gravitational backreaction. It does not derive junction conditions for a specific brane model, apply observable signal-transfer boundary conditions, infer a shortcut between spacetime events, or demonstrate gravitational propagation outside the light cone. The coordinate interval excludes the conformal boundary z=0; external exact Dirichlet boundaries are deliberately imposed. No physical measurement or spacecraft ephemeris is processed.')
sub('Scientific extension with falsifiable gates')
tab([['Extension','Needed objective scientific check'],['Physical boundary conditions','Self-adjoint radial spectrum and flux consistency'],['Independent numerical solvers','Agreement against high-order and spectral discretizations'],['Physical five-dimensional gravity','Gauge and tensor constraints, junction conditions, backreaction'],['Actual bulk-to-brane signal analysis','Correct causal geometry, emitter-receiver boundary problem'],['Publication-oriented uncertainty','Numerical error bars, systematic variation and external review']],[233,249])
page()
#16
h('15. Reproducibility, references and conclusion')
p('The root README describes the build and reproduction commands. The included original paceval_main.h and paceval_main.cpp are linked to a separately obtained compatible original Linux shared runtime; its binary is intentionally excluded from this release. The 28 definitions are stored in examples/formula_registry.csv and the actual mathematical ownership in results/math_execution_inventory.csv.')
p('Build: <font color="#167b9a">cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/path/to/libpaceval_linux_sharedLIB.so</font>')
p('Run: <font color="#167b9a">cmake --build build -j; ctest --test-dir build --output-on-failure; ./build/bulk_wave_kernels --out . --n0 25 --time 0.6 --courant 0.30</font>')
p('Independent replay: <font color="#167b9a">python3 src/high_precision_reference.py; python3 src/verify_results.py; python3 src/make_figures.py; python3 src/make_whitepaper.py</font>')
sub('Independent scientific sources')
p('[1] The Randall–Sundrum Model: conformal coordinates and graviton modes. https://ncatlab.org/nlab/files/Gabella-RandallSundrumModel.pdf','small')
p('[2] Durham University thesis: AdS conformal radial functions, Bessel order two. https://etheses.durham.ac.uk/id/eprint/2242/1/2242_252.pdf','small')
p('[3] OSTI: AdS5 bulk wave mode equations. https://www.osti.gov/pages/servlets/purl/2579340','small')
p('[4] NIST IR 8298, verification and validation methods for numerical simulation. https://nvlpubs.nist.gov/nistpubs/ir/2020/NIST.IR.8298.pdf','small')
p('[5] Roache, Fundamentals of Verification and Validation; method of manufactured solutions. https://www.marin.nl/api/marin/downloads/get-download/6045/0/2704/block_files_hlee9l0uubi5p/8n76MTt2KkFhEwJLXf6U64eXsrI%3D/2009-FVVBook-Roache.pdf','small')
p('[6] paceval C/C++ mathematical engine, original public SDK: https://github.com/paceval/paceval','small')
p('[7] Original five-page WP_044 proposal (provided as part of this GitHub ZIP).','small')
sub('Conclusion')
p('<b>Verified numerical feasibility:</b> 28 real paceval graphs, 663,784 validated batch outputs and independent reference checks demonstrate reusable, parameterized AdS5-inspired bulk-wave mathematics. The experiment does not establish a physical gravitational-wave shortcut or a fifth-dimensional observational signal.')
# page decorations
PW,PH=A4
def decoration(c,doc):
 c.saveState();number=c.getPageNumber();c.setFillColor(DARK);c.rect(0,PH-8,PW,8,stroke=0,fill=1);c.setFont('DejaVu-Bold',7.2);c.setFillColor(TEAL);c.drawString(45,PH-30,'PACEVAL  /  PARAMETERIZED BULK WAVE  /  RESEARCH');c.setStrokeColor(HexColor('#cadce1'));c.line(45,PH-46,PW-45,PH-46);c.line(45,44,PW-45,44);c.setFont('DejaVu',7.1);c.setFillColor(SLATE);c.drawString(45,32,'WP_044  |  mathematical wave-kernel verification  |  13 November 2026');c.drawRightString(PW-45,32,str(number));c.restoreState()
DOC=SimpleDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=52,rightMargin=52,topMargin=63,bottomMargin=54,title='Parameterized Bulk-Wave Evaluation Kernels with paceval',author='paceval scientific research demonstrator')
DOC.build(STORY,onFirstPage=decoration,onLaterPages=decoration)
print(OUTPUT)
