#!/usr/bin/env python3
"""ReportLab scientific paper, grounded in the actual original paceval outputs.
All numbered figures are computed from recorded numeric results (not AI science figures).
The 2:1 conceptual hero is explicitly distinguished from experimental data.
"""
from pathlib import Path
import csv,io,json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RImage, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
PDF=ROOT/'paceval_Conservation_Law_Candidates_Whitepaper_EN.pdf'
SUM=dict(csv.reader((ROOT/'results'/'execution_summary.csv').open()))
MP=json.loads((ROOT/'results'/'high_precision_audit.json').read_text())
SCI=json.loads((ROOT/'results'/'scientific_audit.json').read_text())
REC=list(csv.DictReader((ROOT/'results'/'formula_registry.csv').open()))
assert len(REC)==36 and int(SUM['paceval_graphs'])==144
assert MP['all_checks_passed'] and MP['paceval_output_values_checked']==2304
NAVY=colors.HexColor('#102238');DARK=colors.HexColor('#26354A');TEAL=colors.HexColor('#0A8588');AMBER=colors.HexColor('#DD9A43');GRAY=colors.HexColor('#657286');LIGHT=colors.HexColor('#EDF5F4')
regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',regular));pdfmetrics.registerFont(TTFont('DV-Bold',bold));pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold',italic='DV',boldItalic='DV-Bold')
ST={
 'kicker':ParagraphStyle('kicker',fontName='DV-Bold',fontSize=9.0,leading=14,textColor=TEAL,spaceAfter=7),
 'cover':ParagraphStyle('cover',fontName='DV-Bold',fontSize=24,leading=32,textColor=NAVY,spaceAfter=9),
 'sub':ParagraphStyle('sub',fontName='DV',fontSize=10.5,leading=16.0,textColor=DARK,spaceAfter=10),
 'h1':ParagraphStyle('h1',fontName='DV-Bold',fontSize=16.5,leading=23,textColor=NAVY,spaceAfter=9),
 'h2':ParagraphStyle('h2',fontName='DV-Bold',fontSize=10.6,leading=15,textColor=TEAL,spaceBefore=8,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.0,leading=14.3,textColor=DARK,spaceAfter=9),
 'small':ParagraphStyle('small',fontName='DV',fontSize=8.1,leading=12.4,textColor=DARK,spaceAfter=7),
 'tiny':ParagraphStyle('tiny',fontName='DV',fontSize=7.2,leading=10.7,textColor=DARK,spaceAfter=3),
 'caption':ParagraphStyle('caption',fontName='DV',fontSize=7.7,leading=11.2,textColor=GRAY,spaceAfter=7),
 'note':ParagraphStyle('note',fontName='DV-Bold',fontSize=8.5,leading=13,textColor=NAVY,spaceAfter=8),
}
E=[]
def p(t,sty='body'):E.append(Paragraph(t,ST[sty]))
def h(t):p(t,'h1')
def h2(t):p(t,'h2')
def page():E.append(PageBreak())
def img(fname,width=475,maxheight=222):
 path=ROOT/'figures'/fname
 im=Image.open(path)
 ht=width*im.height/im.width
 if ht>maxheight:width*=maxheight/ht;ht=maxheight
 E.append(RImage(str(path),width=width,height=ht))
def fig(n,file,cap):
 img(file,width=463,maxheight=229)
 p(f'<b>Figure {n}.</b> {cap}','caption')
def table(headers,rows,widths=None):
 widths=widths or ([225,270] if len(headers)==2 else [95,185,215])
 cells=[[Paragraph(str(v),ST['tiny']) for v in headers]]+[[Paragraph(str(v),ST['tiny']) for v in r] for r in rows]
 T=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
 T.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('LINEBELOW',(0,0),(-1,0),.8,TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F6F9F9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
 E.append(T);E.append(Spacer(1,8))
def eq(latex):
 fig0=plt.figure(figsize=(10,0.72),dpi=170);fig0.patch.set_alpha(0)
 fig0.text(.018,.51,latex,fontsize=17,ha='left',va='center',color='#102238')
 b=io.BytesIO();fig0.savefig(b,format='png',transparent=True,dpi=165,bbox_inches='tight',pad_inches=.12);plt.close(fig0)
 b.seek(0);pic=Image.open(b);h=35.0;w=h*pic.width/pic.height
 if w>480:h=h*480/w;w=480
 b.seek(0);E.append(RImage(b,width=w,height=h));E.append(Spacer(1,7))
def foot(c,doc):
 c.saveState();w,hh=A4
 if doc.page>1:
  c.setStrokeColor(colors.HexColor('#CFDADD'));c.line(44,hh-39,w-44,hh-39)
  c.setFillColor(TEAL);c.setFont('DV-Bold',7);c.drawString(46,hh-32,'PACEVAL | WP_041 | SCIENTIFIC MATHEMATICAL RESEARCH')
 c.setStrokeColor(colors.HexColor('#CFDADD'));c.line(44,39,w-44,39)
 c.setFillColor(GRAY);c.setFont('DV',7)
 c.drawString(46,27,'WP_041 · Synthetic conservation-law candidate verification · 13 November 2026')
 c.drawRightString(w-46,27,str(doc.page));c.restoreState()
# PAGE 1
p('PACEVAL  |  SCIENTIFIC RESEARCH WHITEPAPER  |  WP_041','kicker')
p('Computational Testing of<br/>Conservation-Law Candidates<br/>with paceval','cover')
p('An independently checked numerical demonstration using known dynamical laws, synthetic trajectories and original paceval Multi-Graph-Batch execution.','sub')
img('00_conservation_laws_hero.png',495,248)
p('Conceptual scientific artwork. Pendulum, orbit and mathematical surfaces are design illustrations; the numbered result plots in this paper come from the executable numerical output.','caption')
E.append(Spacer(1,8))
table(['EXECUTED SCOPE','ACTUAL VERIFIED RESULT'],[
 ('Candidate mathematical expressions','36 fixed candidates across 3 benchmark dynamical systems'),
 ('Real paceval execution','144 persistent graphs; 645,168 Multi-Graph-Batch results'),
 ('Independent audits','2,304 checks at 80 decimal digits; 288 candidate/noise/split evaluations'),
 ('Numerical result','12 predeclared true invariants recognized; 24 negative controls rejected in controlled tests')
],[181,314])
p('Research boundary: conditional verification against exact known vector fields; no unknown physical law discovered, no measured industrial installation and no performance-speed claim.','small')
page()
# PAGE 2
h('1. The scientific and industrial use case')
p('Manufacturing digital twins, vibration controllers, orbital systems and physics-guided machine learning depend on mathematical models that should respect basic dynamical constraints. A candidate invariant can be useful as a computational consistency check, but observing small variation on one trajectory alone does not establish a physical conservation law.')
p('The user-supplied independent proposal isolates an intentionally simplified local balance expression: R = |dE/dt + div(flux) - source|. This paper selects the ordinary-differential-equation analogue: evaluate an explicit total derivative along the modeled vector field. The application-level task is to distinguish known invariants from plausible false candidates across independent simulated trajectories and noise levels.')
h2('Context and verified literature')
p('Brunton, Proctor and Kutz (2016) introduced sparse identification of nonlinear dynamics (SINDy) as a broader equation-discovery framework [2]. Subsequent work on neural deflation studies the discovery of conservation laws directly from trajectories [3]. These references motivate the importance of independent, parsimonious candidate tests; this experiment does not claim novelty over those discovery methods.')
h2('Clear boundary between verification and discovery')
table(['QUESTION','ANSWER IN THIS PAPER'],[
 ('Known dynamical vector fields?','Yes: exact oscillator and Kepler equations are provided.'),
 ('Predefined candidate functions?','Yes: 36 explicit analytic expressions, including negative controls.'),
 ('Can paceval evaluate them?','Yes: each invariant, its unsimplified chain rule and two mathematical scores.'),
 ('Does it infer a new unknown law?','No; unseen systems, unknown dynamics, numerical time derivatives and physical measurements are not evaluated.')
],[208,287])
page()
# PAGE 3
h('2. Mathematical definition of conservation')
p('Let x(t) be a state vector and dx/dt = f(x,t) a specified dynamical system. A differentiable candidate I(x,t) is an invariant of this defined model if its total derivative vanishes throughout a valid state-time domain, not only at one sampled trajectory.')
eq(r'$\frac{d I}{d t}=\frac{\partial I}{\partial t}+\nabla I\cdot f(x,t)=0$')
p('We explicitly register the unsimplified component-wise chain rule rather than substituting the algebraically simplified constant zero. Thus the original paceval engine computes numerical additions, products, powers, reciprocal/radial functions and exponentials in a genuine cancellation test.')
h2('Three analytically controlled dynamical systems')
table(['SYSTEM','VECTOR FIELD AND PHYSICAL INTERPRETATION'],[
 ('Anisotropic 2D oscillator','dx/dt = v; dv/dt = -x; dy/dt = w; dw/dt = -4y. Mode frequencies 1 and 2.'),
 ('Planar Kepler problem','dx/dt = v; dy/dt = w; dv/dt = -mu*x/r^3; dw/dt = -mu*y/r^3; r = sqrt(x^2+y^2).'),
 ('Underdamped oscillator','dx/dt = v; dv/dt = -x - 2*zeta*v, with zeta = 0.075 and an explicit time-dependent invariant.')
],[170,325])
p('The initial states and smooth trajectories are generated analytically by C++ to avoid accidentally conflating numerical integration drift with conservation-law violations. Measured state vectors are separately perturbed for the declared observational-noise experiments.')
page()
# PAGE 4
h('3. Candidate library and physical interpretation')
h2('A. Anisotropic oscillator')
eq(r'$E_x=\frac{x^2+v^2}{2},\quad E_y=\frac{4y^2+w^2}{2}$')
p('The two mode energies are individually conserved, as are their sum and any differentiable function thereof. We include twelve oscillator candidates: four true invariant functions, including an algebraically dependent square, and eight counterexamples such as x, v, x*v and v^2.')
h2('B. Planar Kepler dynamics')
eq(r'$H=\frac{v^2+w^2}{2}-\frac{\mu}{r},\qquad L=xw-yv$')
p('Besides specific energy H and angular momentum L, both in-plane components of the Laplace-Runge-Lenz (LRL) vector are tested. The derived H^2 and L^2 candidates are mathematically conserved but not additional independent conservation laws. Six predeclared invariants are accompanied by six negative controls.')
h2('C. Damped oscillator')
eq(r'$I(t)=e^{2\zeta t}\left(v^2+2\zeta xv+x^2\right)$')
p('Raw mechanical energy dissipates and is therefore a negative control. The explicitly time-dependent I(t), and its square, remain conserved under the *declared* damped equation. This illustrates why a valid conserved quantity may require explicit time dependence and why arbitrary stationary-energy claims are incorrect.')
p('There are 12 positive candidate function labels in total (4+6+2); that is not a count of functionally independent invariants. The candidate set was fixed before running the numerical evaluation.')
page()
# PAGE 5
h('4. Actual original paceval integration')
p('The executable includes the original paceval_main.h and paceval_main.cpp interfaces, and dynamically accesses the separately supplied compatible original Linux library. All 36 candidate functions are registered with long-lived handles using paceval_CreateComputation, without creation inside the trajectory loop.')
table(['GRAPH FOR EACH CANDIDATE','EXECUTION OWNER'],[
 ('1. Candidate value I(x,t)','Real persistent paceval computation'),
 ('2. Explicit Lie derivative dI/dt','Real persistent paceval graph: full unsimplified chain rule'),
 ('3. Normalized |dI/dt| / (1 + |I|)','Real persistent paceval graph; absolute values built from sqrt(square)'),
 ('4. Squared Lie derivative (dI/dt)^2','Real persistent paceval graph'),
 ('Time sequence, reference trajectory, noise','C++ host: analytic solution and deterministic input generation'),
 ('RMS across many observations; selection','C++ host: aggregation and fixed thresholds, not paceval formulas')
],[228,267])
p('The 144 registered graphs are evaluated by the true paceval_dGetMultipleComputationsResultsExt API. Every individual SDK error code is checked and the tested library’s non-standard batch bool return convention is respected. Each model group uses 48 graph handles on blocks of trajectory or surface points.')
h2('Versioned formula declarations and exact ownership')
p('The complete source strings are committed to results/formula_registry.csv and src/generated_registry.h, with their source generator src/generate_registry.py. The machine-readable math_execution_inventory.csv identifies all execution owners and distinct API paths. The full source and its graph inventory are part of the project archive.')
page()
# PAGE 6
h('5. Reproducible numerical experiment design')
table(['CONTROL','DECLARED VALUE'],[
 ('Benchmark systems / candidates','3 dynamical systems; 36 frozen candidate expressions'),
 ('Noise levels','Standard deviations: 0, 0.005, 0.02, 0.05 in model-state units'),
 ('Initial conditions','4 distinct analytic trajectories per system'),
 ('Sample times','192 evenly spaced instants over normalized 0 to 14'),
 ('Train/held-out separation','Trajectories 0–1 for training; 2–3 for holdout; fixed before tests'),
 ('Candidate verification','Normalized Lie RMS < 1e-7 and mean per-trajectory drift < 0.002 + 12*sigma'),
 ('3D demonstration','65 × 65 phase-space points with true paceval Lie evaluations'),
],[215,280])
p('The thresholds are explicit demonstration-policy parameters, not rigorous floating-point enclosures, measured sensor-error models or evidence-optimized tuning. Gaussian state perturbations are deterministic for repeatability. Importantly, the noise does not alter the supplied exact ODE: the Lie expression evaluates the model at perturbed observed states. This is *not* a test of reconstructing a vector field from noisy data.')
h2('Independent controls')
p('The program checks each per-result error, finite input domain, squared-derivative identity, and 6,440 invariant-Lie reference values. A separate 80-digit mpmath program parses the exported literal expressions independently and checks 2,304 actual paceval result entries, including held-out phase-space samples.')
page()
# PAGE 7
h('6. Executed outcomes and scientific meaning')
table(['GROUNDED OUTPUT','ACTUAL OBSERVED RESULT'],[
 ('Persistent original paceval graphs','144 across 36 candidate laws'),
 ('Actual Multi-Graph-Batch results',f"{int(SUM['multi_graph_batch_outputs']):,}"),
 ('Batch API invocations',SUM['batch_api_invocations']),
 ('Scalar SDK spot checks',SUM['scalar_sdk_calls']),
 ('Distinct vector inputs, including surface',SUM['paceval_sample_vectors']),
 ('Analytic invariant Lie checks',SUM['analytic_lie_checks']),
 ('Largest absolute known-Lie cancellation',f"{float(SUM['analytic_lie_max_abs']):.3g}"),
 ('80-decimal-digit independent checks',MP['paceval_output_values_checked']),
 ('Train/held-out candidate/noise/split rows',SUM['classification_rows']),
],[245,250])
h2('Conditional recovery on a deliberately constructed candidate library')
p('Across the locked benchmark, all known invariant formulas were recovered and all counterexamples rejected at each declared noise level for both data splits. The held-out precision and recall are 1.00 *for this exact, intentionally separable and previously labeled mathematical library*. The direct Lie-derivative score uses the complete known vector field, so this result should never be extrapolated to unknown-physics discovery accuracy or real noisy derivative estimates.')
h2('Numerical result rather than performance marketing')
p('This paper reports mathematical executability, reproducibility and domain-specific interpretation, not measured speedups or C++-versus-paceval numerical-difference tables. The independent checks are shipped for technical audit and do not constitute experimental physical measurements.')
page()
# PAGE 8
h('7. Computed results I: oscillator and orbit')
fig(1,'01_oscillator_energy_invariants.png','The two separately conserved oscillator mode energies and their sum, evaluated as independent original paceval expressions along one analytic trajectory.')
fig(2,'02_kepler_orbit_trace.png','The exact source trajectory supplied to paceval for the Kepler model, shown in physical phase-space coordinates. It is synthetic benchmark input, not observed astronomical tracking.')
page()
# PAGE 9
h('8. Computed results II: two different kinds of conservation')
fig(3,'03_kepler_energy_momentum_lrl.png','Actually evaluated Kepler energy, angular momentum and two Laplace-Runge-Lenz components. The drawn quantities have different units and are displayed together only for numerical constancy.')
fig(4,'04_damped_corrected_invariant.png','The raw mechanical energy is decreasing while a mathematically correct time-weighted invariant stays constant under the specified damped oscillator.')
page()
# PAGE 10
h('9. Computed results III: 3D violation surface')
fig(5,'05_lie_violation_surface_3d.png','A 65 by 65 real paceval batch evaluation of the unsimplified Lie derivative for the FALSE candidate x*v in an undamped oscillator. The surface is not a physical potential.')
p('A genuine invariant has a vanishing derivative throughout its defined model domain. Conversely, x*v has derivative v^2 - x^2 under x-dot=v and v-dot=-x; its zero-valued curves alone do not make it globally conserved. This is why analyzing one trajectory, or a small sampled residual, is insufficient.')
page()
# PAGE 11
h('10. Computed results IV: contours and candidate separation')
fig(6,'06_lie_violation_contours.png','True paceval contour map of absolute Lie derivative for the oscillator negative-control expression x*v. Local zeros and globally nonzero regions coexist.')
fig(7,'07_candidate_lie_vs_drift.png','Held-out candidate scores at additive state-noise sigma = 0.02: recognized mathematical invariants versus the fixed negative controls, using actual paceval Lie and invariant values.')
page()
# PAGE 12
h('11. Computed results V: observational noise')
fig(8,'08_noise_robustness_drift.png','Observed trajectory drift rises with injected state-measurement noise, even though the theoretical analytic invariants of the exact ODE remain valid.')
fig(9,'09_counterexample_residuals.png','The 24 known non-invariants have strictly nonzero normalized Lie derivative RMS scores in the held-out data under the declared benchmark.')
page()
# PAGE 13
h('12. Computed results VI: conditional recall and graph inventory')
fig(10,'10_heldout_recall.png','Perfect held-out recall in this known-model/closed-candidate benchmark. This is NOT an estimate of out-of-family discovery performance.')
fig(11,'11_registered_graph_families.png','All 144 persistent real paceval graphs are accounted for, including candidate values, explicit total derivatives and two numerical residual scores.')
page()
# PAGE 14
h('13. Verification, methodological safeguards and limitations')
table(['AUDIT','RESULT'],[
 ('Original C++ program + SDK','Built with original paceval_main.cpp and external original library'),
 ('CMake/CTest','Passed with genuine original library'),
 ('Analytic Lie checks',f"{int(SUM['analytic_lie_checks']):,} passed, max |dI/dt| = {float(SUM['analytic_lie_max_abs']):.3g}"),
 ('Independent 80-digit mpmath',f"{MP['paceval_output_values_checked']:,} results passed"),
 ('Precision/recall and control labels','36 fixed candidates, four noise levels, two splits, 288 rows'),
 ('Reproducibility','Repeat byte-identical CSVs verified separately; hashes stored in package'),
],[210,285])
h2('Interpretation and what this does not establish')
p('With an exactly known vector field and analytically supplied chain-rule derivatives, the test is a candidate-verification benchmark. It is not autonomous discovery, a successful inference of true dynamics from noisy trajectories, a rigorous proof of physical truth from finite data, or a measurement of laboratory energy conservation. Even a zero-valued Lie derivative for a formally defined ODE only certifies compatibility with that ODE and its domain assumptions.')
p('Some recovered candidates are dependent functions of others. An independent-function discovery algorithm would require rank tests or another equivalence reduction, not simply counting 12 positive labels. Long noisy trajectories, solver discretization, model misspecification and sensor calibration remain future experiments.')
page()
# PAGE 15
h('14. Reproduction, research roadmap and references')
h2('Reproducible project')
p('Build with CMake from src/CMakeLists.txt after supplying a separately obtained original paceval Linux library. Typical commands: cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so; cmake --build build -j; ctest --test-dir build --output-on-failure; ./build/conservation_law_candidates --out .')
p('Independent reproduction runs src/high_precision_reference.py and src/verify_results.py, regenerates numbered scientific images using src/make_figures.py, and rebuilds this report with src/make_whitepaper.py. The checked-in original paceval SDK interfaces preserve their existing notices; no external runtime binary is redistributed.')
h2('Scientifically useful next experiments')
p('A realistic next stage would fit or discover f from incomplete/noisy observations, compare strong/weak-form differentiation, rank independent invariant families, extend to nonintegrable and forced or stochastic systems, quantify false-discovery rates on held-out physical datasets, and benchmark against modern constrained symbolic-regression or neural-law approaches. These tasks are not claimed here.')
h2('Research references')
for line in [
 '[1] WP_041 Computational Testing of Conservation-Law Candidates, user-supplied independent proposal, November 2026.',
 '[2] Brunton, Proctor, Kutz, Discovering governing equations from data by sparse identification of nonlinear dynamical systems. PNAS 113 (2016). DOI: 10.1073/pnas.1517384113.',
 '[3] Data-driven discovery of conservation laws from trajectories via neural deflation. Communications in Nonlinear Science and Numerical Simulation 143 (2025), 108563. DOI: 10.1016/j.cnsns.2024.108563.',
 '[4] paceval mathematical engine, original SDK API and Multi-Graph-Batch interface: https://paceval.com/api/',
 '[5] paceval open research repository: https://github.com/paceval/paceval'
]:p(line,'tiny')
h2('Conclusion')
p('<b>Verified outcome:</b> original paceval computes 36 reusable candidate laws, their unsimplified analytic Lie derivatives, and numerical validity scores via 144 actual persistent graphs across controlled physical examples and held-out synthetic trajectories. <b>Scientific boundary:</b> no unknown law, external sensor process or industrial advantage is thereby discovered.','small')
DOC=SimpleDocTemplate(str(PDF),pagesize=A4,leftMargin=50,rightMargin=50,topMargin=54,bottomMargin=54,
 title='WP_041 Conservation-Law Candidate Verification with paceval',author='paceval independent research demonstrator',subject='Original paceval SDK C++ deterministic conservation law verification')
DOC.build(E,onFirstPage=foot,onLaterPages=foot)
import fitz
pdf=fitz.open(PDF)
print('whitepaper created:',PDF,'pages:',len(pdf),'bytes:',PDF.stat().st_size)
