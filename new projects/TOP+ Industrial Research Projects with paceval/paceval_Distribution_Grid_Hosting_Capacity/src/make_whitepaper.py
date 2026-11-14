#!/usr/bin/env python3
"""Create the standalone English WP11 science paper from genuine execution-evidence data."""
from pathlib import Path
import json,csv
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from PIL import Image as PILImage

ROOT=Path(__file__).resolve().parents[1];RES=ROOT/'results';FIG=ROOT/'figures';OUT=ROOT/'paceval_Distribution_Grid_Hosting_Capacity_Whitepaper_EN.pdf'
evidence=json.loads((RES/'execution_evidence.json').read_text());audit=json.loads((RES/'independent_validation_audit.json').read_text());
with (RES/'hosting_capacity.csv').open() as f:hc=list(csv.DictReader(f))
try:
 pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
 pdfmetrics.registerFont(TTFont('DejaVuBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
except Exception:pass
PAGE_W,PAGE_H=A4;navy=HexColor('#173941');teal=HexColor('#147E82');soft=HexColor('#E9F4F2');gold=HexColor('#D49B3D');dark=HexColor('#233A3E')
styles={
 'cover':ParagraphStyle('cover',fontName='DejaVuBold',fontSize=23,leading=30,textColor=navy,spaceAfter=10),
 'subtitle':ParagraphStyle('subtitle',fontName='DejaVu',fontSize=12,leading=17,textColor=teal,spaceAfter=15),
 'h1':ParagraphStyle('h1',fontName='DejaVuBold',fontSize=14,leading=19,textColor=navy,spaceAfter=11),
 'h2':ParagraphStyle('h2',fontName='DejaVuBold',fontSize=10.3,leading=15,textColor=teal,spaceBefore=9,spaceAfter=4),
 'body':ParagraphStyle('body',fontName='DejaVu',fontSize=8.7,leading=13.5,textColor=dark,spaceAfter=7),
 'small':ParagraphStyle('small',fontName='DejaVu',fontSize=7.3,leading=11,textColor=dark,spaceAfter=5),
 'caption':ParagraphStyle('caption',fontName='DejaVu',fontSize=7.6,leading=11.6,textColor=navy,spaceBefore=4,spaceAfter=10),
 'callout':ParagraphStyle('callout',fontName='DejaVuBold',fontSize=9.4,leading=15,textColor=navy,spaceAfter=7),
 'tablehead':ParagraphStyle('tablehead',fontName='DejaVuBold',fontSize=7.4,leading=11,textColor=colors.white),
 'table':ParagraphStyle('table',fontName='DejaVu',fontSize=7.25,leading=10.5,textColor=dark),
}
MARGIN=44;W=PAGE_W-2*MARGIN
story=[]
def P(s,style='body'):
 story.append(Paragraph(s,styles[style]))
def S(n=6):story.append(Spacer(1,n))
def newpage(title):
 story.append(PageBreak());P(title,'h1')
def figure(stem,caption,width=455):
 p=FIG/(stem+'.png');assert p.exists(),p
 im=PILImage.open(p);w,h=im.size;wid=min(width,W);ht=wid*h/w
 story.append(Image(str(p),width=wid,height=ht));P(caption,'caption')
def table(header,rows,widths=None):
 dat=[[Paragraph(str(v),styles['tablehead']) for v in header]]+[[Paragraph(str(v),styles['table']) for v in row] for row in rows]
 n=len(header);tb=Table(dat,colWidths=widths or [W/n]*n,repeatRows=1,hAlign='LEFT')
 tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,soft]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.4,teal)]));story.append(tb);S(8)
def build_equation(text,stem,width=490):
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(10.2,1.05));ax.axis('off');ax.text(.5,.5,text,ha='center',va='center',fontsize=17,color='#183E46');fig.savefig(FIG/(stem+'.png'),dpi=180,bbox_inches='tight',pad_inches=.12,facecolor='white');plt.close(fig)
 p=FIG/(stem+'.png');im=PILImage.open(p);story.append(Image(str(p),width=width,height=width*im.size[1]/im.size[0]));S(4)

# Cover page
P('Programmable Distribution Grid Hosting Capacity with paceval','cover')
P('Reusable AC network kernels, power-flow constraints, inverter control revisions and numerical feasibility maps','subtitle')
cover=FIG/'00_grid_hosting_hero.png';assert PILImage.open(cover).size==(2400,1200)
story.append(Image(str(cover),width=W,height=W/2));P('Figure 1. Concept illustration of a PV-rich distribution grid. Not a physical feeder photograph or a computed research map.','caption')
S(8)
P('Research outcome and scope','h2')
table(['Verified local computation','Evidence'],[
 ['Synthetic balanced radial AC network','12 buses, 11 branches'],
 ['Full scenario sweep',f"{evidence['scenario_count']:,} site/control/injection cases; all converged"],
 ['Original paceval engine',f"{evidence['unique_graphs_executed']} executed persistent graphs; {evidence['graph_point_evaluations']:,} graph-point outputs"],
 ['Independent reference',f"{audit['independent_python_reference_assertions']:,} assertions; {audit['selected_scipy_nonlinear_nodal_solutions']} nodal nonlinear solves; {audit['high_precision_decimal80_checks']} high-precision checks"]],[220,W-220])
P('14 November 2026  |  Synthetic research dataset  |  English technical whitepaper','small')

newpage('1. Industrial use case and current state of the art')
P('A distribution-grid planner must decide where and under what operating conditions rooftop photovoltaic systems, local generation, batteries or electric-vehicle chargers can be connected. Hosting capacity represents the injection or loading that can be accommodated before a specified network constraint is violated. It is fundamentally location-dependent: the same export can produce distinct line currents and voltage profiles at different nodes.')
P('In utility practice, engineering screening uses power-flow models, sometimes long time-series studies, to test voltage limits, thermal ratings and, separately, network protection, power quality, asset operations and control constraints. Hosting-capacity maps are therefore summaries of stated network assumptions, not substitutes for a complete interconnection study.')
P('Relevant developments','h2')
P('US Department of Energy planning guidance places hosting-capacity analysis within integrated distribution system planning. A 2025 Lawrence Berkeley National Laboratory study discusses utilities&#39; network and planning datasets. Peer-reviewed 2026 studies examine reactive-power inverter capability, topology and the interpretation of feasibility intervals across photovoltaic injection levels. These works motivate the present controlled, transparent mathematical kernel study rather than providing experimental validation of paceval itself.')
P('Research question','h2')
P('Can a real paceval execution layer evaluate the algebraic current/voltage update kernels, repeated network constraints, sensitivity proxies and independently versioned scoring functions of a balanced radial feeder without replacing the host-controlled AC network algorithm? This is a functionality and reproducibility investigation, not a speed test.')
figure('02_feeder_topology','Figure 2. Actual topology of the deterministic synthetic test feeder. Numbers are synthetic bus IDs; the diagram is a schematic layout of the tested model.',width=460)

newpage('2. Architecture: a host solver and a mathematical engine')
P('The C++ host generates and reads typed scenario CSV rows, manages the radial parent/child topology, controls the fixed-point backward/forward sweep, checks convergence and forms a final scenario status. The original paceval SDK creates persistent mathematical computation graphs once and evaluates their scalar, batch and multi-graph forms repeatedly.')
figure('01_execution_architecture','Figure 3. Conceptual software architecture. In contrast to the data charts, this figure is a schematic and does not plot a measured result.',width=470)
P('The solver does not outsource stateful network traversal to a formula interpreter. It sends node-level active/reactive demand and voltage estimates to paceval for complex injection-current components, and uses paceval again to compute individual real/imaginary branch-voltage updates. A topology-indexed reduction and iteration stopping policy remain in native C++. The independent Python reference is not substituted into the productive calculation path.')
P('CSV and execution integrity','h2')
P('The scenario file is generated using <b>paceval_dConvertFloatToString</b> and really parsed again through <b>paceval_dConvertStringToFloat</b>. A strict decimal-literal grammar is checked first because the paceval parser may also interpret mathematical expressions. Error status, finite values and input range are verified. Both % and mod, infix min/max and mixed logical/relational operators are subjected to separately executed SDK tests.')

newpage('3. Mathematical AC feeder model and sign convention')
P('The balanced single-phase-equivalent feeder has 12 buses and 11 series-impedance branches. Bus 0 is a fixed voltage slack at 1.0 + j0 per-unit. Real and reactive demand are positive in the load convention. An inverter exporting active power P_DER reduces net active demand. Positive reactive DER injection reduces reactive demand; reactive absorption is therefore a negative Q_DER in this sign convention.')
build_equation(r'$S_i=(P_{load,i}-P_{DER,i})+j(Q_{load,i}-Q_{DER,i})$','math_complex_demand')
build_equation(r'$I_{inj,i}=\overline{S_i/V_i},\qquad V_j=V_i-(R_{ij}+jX_{ij})I_{ij}$','math_ac_update')
P('At each backward sweep, the branch current equals the local load injection current plus all downstream branch currents. An updated voltage is calculated in topological forward order. The C++ host terminates when changes in the complete complex voltage state satisfy a fixed convergence tolerance. An independently assembled nodal-admittance nonlinear solver checks selected converged solutions.')
P('Constraint and loss kernels','h2')
build_equation(r'$m_V=\min(|V|-V_{min},\;V_{max}-|V|),\qquad m_I=I_{max}-|I|$','math_margins')
build_equation(r'$P_{loss}=R|I|^2,\qquad \Delta V_{proxy}=(RP+XQ)/V_{ref}$','math_losses')
P('The voltage-drop proxy is explicitly a local linear approximation and must not be confused with the solved complex-voltage state. Its analytic derivatives with respect to local P and Q are R/V_ref and X/V_ref. These are <b>not</b> nonlinear whole-network sensitivities.')

newpage('4. Actual paceval mathematical execution inventory')
P('A total of 29 distinct graph definitions were registered successfully and executed in the main research calculation. The original paceval engine performed the following mathematical functions with persistent handles:')
table(['Execution family','Actual graph responsibilities'],[
 ['Setpoints and injections','Two reactive control functions; P and Q net-demand expressions'],
 ['AC current and voltage','Complex current real/imaginary parts; complex branch-voltage real/imaginary updates'],
 ['Network quantities','Bus voltages; branch currents; real and reactive line losses; branch active and reactive powers'],
 ['Constraint expressions','Voltage low/high margins; combined minimum margin; thermal margin and utilization; Boolean pass/fail'],
 ['Programmable mathematics','Local approximate voltage-drop sensitivity, normalized margins, weighted quality score and two penalty revisions']
 ],[132,W-132])
P('A full manifest under <b>results/math_execution_inventory.csv</b> records each graph expression, the ownership boundary and its execution path. The numeric result rows are computed from genuine SDK calls; the independent Python and C++ numerical paths are used only as reference checks.')
P('Boolean and relational semantics','h2')
P('A branch passes the selected operating rule only if the voltage is within both bounds and the branch-current magnitude does not exceed its rating. Each relational subexpression is explicitly parenthesized; the logical operator returns a Boolean 0 or 1. Minimum, maximum and nonnegative violation penalties are evaluated by the actual paceval expression parser. No claim is made that a Boolean mask protects mathematically undefined subordinate expressions.')
P('Model revisions','h2')
build_equation(r'$Q_{DER}^{(1)}=0,\qquad Q_{DER}^{(2)}=-0.25\,P_{DER}$','math_mode')
P('The two independently callable control variants share the topology and constraint convention. Separately, two simultaneous branch penalty formulas assign different weights to undervoltage, overvoltage and thermal overload. All actual quantities and formula versions remain recorded in the registry. Neither a full Volt-VAR IEEE control curve nor automatic differentiation is claimed.')

newpage('5. Deterministic workload and independent verification')
P('Eight potential PV connection buses (IDs 4–11), two inverter setpoint variants and 64 equally spaced export levels over 0–2.5 pu yield 1,024 evaluated cases. The physical network assumptions are fixed; all line impedances, thermal ratings and synthetic demand levels are archived in the feeder parameter file. Every case is solved independently, and its eleven branch/bus constraints are evaluated by original paceval graphs.')
table(['Main workload and validation item','Verified result'],[
 ['Scenario evaluations',str(evidence['scenario_count'])],
 ['Feasible / violating scenarios',f"{evidence['feasible_scenarios']} / {evidence['infeasible_scenarios']}"],
 ['Distinct executed persistent graphs',str(evidence['unique_graphs_executed'])],
 ['Graph-point results',f"{evidence['graph_point_evaluations']:,}"],
 ['Host numerical reference groups',f"{evidence['native_cpp_reference_checks']:,}"],
 ['Independent Python result assertions',f"{audit['independent_python_reference_assertions']:,}"],
 ['Independent SciPy nodal equation solves',str(audit['selected_scipy_nonlinear_nodal_solutions'])],
 ['80-digit independent checks',str(audit['high_precision_decimal80_checks'])]
 ],[270,W-270])
P('The independent verifier uses complex NumPy arithmetic to reconstruct each complete scenario, then applies SciPy to a separate admittance-matrix formulation for selected cases. mpmath carries out selected high-precision evaluations. The numerical calculations pass the predefined audit tolerances; exact differences remain in technical audit files rather than in public engine-comparison tables.')
P('A hosting capacity is the greatest <b>feasible tested</b> active export at that connection point, for that specified control mode, within this bounded discrete sweep. The algorithm does not assume that a feasibility region is globally monotonic, or claim a globally continuous optimum.')

newpage('6. Results: site-dependent hosting limits')
P('The highest feasible tested export decreases for some downstream locations because different branch currents and voltage profiles become constraining. This is a finding of this specific synthetic feeder, not a universal geographic ranking.')
figure('03_discrete_hosting_by_site','Figure 4. Site-by-site discrete hosting values recorded from original paceval constraints and the converged host AC solution.',width=456)
bus4=[r for r in hc if int(r['candidate_bus'])==4]
bus9=[r for r in hc if int(r['candidate_bus'])==9]
P(f"At bus 4, the largest feasible tested injection is {float(bus4[0]['highest_feasible_der_pu']):.3f} pu (unity) versus {float(bus4[1]['highest_feasible_der_pu']):.3f} pu (reactive absorption). At bus 9, the corresponding values are {float(bus9[0]['highest_feasible_der_pu']):.3f} pu and {float(bus9[1]['highest_feasible_der_pu']):.3f} pu. These differences reflect the chosen feeder and control assumptions.")

newpage('7. Feasible and infeasible penetration regions')
figure('04_feasibility_unity','Figure 5. A voltage-and-thermal feasibility classification for every tested connection bus and injection level under unity power factor.',width=447)
figure('05_feasibility_reactive','Figure 6. Same synthetic feeder under the proportional reactive-absorption mode, with identical voltage and thermal thresholds.',width=447)

newpage('8. Voltage profiles, location and nonlinear response')
figure('06_maximum_bus_voltage','Figure 7. Maximum bus voltage for increasing PV injection at connection bus 7 in the two setpoint variants.',width=440)
figure('09_three_dimensional_voltage_surface','Figure 8. Recorded maximum-voltage surface for each siting location and injected active power under unity power factor.',width=440)

newpage('9. Thermal loading and line losses')
figure('07_thermal_margin_vs_export','Figure 9. Minimum branch-current margin may become negative, indicating a violated branch rating in the selected synthetic network.',width=445)
figure('08_grid_losses_vs_der','Figure 10. Resistive branch-loss totals derived from paceval I²R calculations for the full AC solution.',width=445)

newpage('10. Local physical profiles along the feeder')
figure('11_bus_voltage_profile','Figure 11. Bus-voltage distribution for selected injection levels at a single PV connection point.',width=440)
figure('12_branch_current_utilization','Figure 12. Branch-current ratios for selected injection levels compared with the synthetic rating of each branch.',width=440)

newpage('11. Versioned mathematical decisions and margins')
P('Separate paceval graph handles implement two independently callable, weighted violation penalties, permitting controlled revisions without changing the underlying host AC solver. An AC solution may converge while violating operating limits; the mathematical score and final classification must remain distinct.')
figure('10_versioned_penalty_functions','Figure 13. Same physical scenario series evaluated by two persistent, alternative mathematical penalty graph expressions.',width=430)
figure('15_constraint_violation_count','Figure 14. Number of local operating limits violated in scenarios along the DER sweep; the status is not an official interconnection approval.',width=430)

newpage('12. Site and control decision summary')
figure('13_feasible_share_by_bus','Figure 15. Fraction of the discrete sweep meeting all modeled constraints, grouped by the candidate DER bus.',width=445)
figure('14_reactive_control_impact','Figure 16. Difference between the two explored fixed-reactive-power modes. A negative value is scenario-specific and should not be generalized to all smart-inverter controllers.',width=445)

newpage('13. Scientific limitations, reproducibility and references')
P('What was and was not established','h2')
P('The productive C++ executable called the original paceval engine to evaluate current-injection, voltage-update and downstream decision expressions. Both supported versions were kept simultaneously accessible; 1,024 full AC calculations converged; all modeled voltage/current constraint decisions were independently checked. These are results for a deterministic **synthetic balanced feeder** and represent mathematical proof of concept, not field calibration.')
P('Unmodeled requirements include three-phase imbalance, protection coordination and fault-current contribution, harmonic distortion, temporal load and PV behavior, regulator tap action, conductor temperature transients, standards-based DER control curves, N-1 security and utility-specific operating rules. Consequently, a computed permissible export must not be treated as an actual interconnection permit. TINC was not used, and no interval proof is claimed.')
P('Reproduction','h2')
P('From Linux x86-64 with the separately provided licensed paceval shared library, configure with <b>cmake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so</b>, build with CMake, run CTest, execute <b>./build/grid_hosting --run --steps 64 --out results/reproduced</b>, and run <b>python3 validation/verify_reference.py results/reproduced</b>. The original header and paceval_main.cpp are part of the package; the proprietary shared object is excluded.')
P('Source references (independent of paceval research results)','h2')
refs=[
 'US Department of Energy, Integrated Distribution System Planning: https://www.energy.gov/oe/integrated-distribution-system-planning',
 'Lawrence Berkeley National Laboratory, Bridging the Gap on Data and Analysis for Distribution System Planning (2025): https://eta.lbl.gov/publications/bridging-gap-data-and-analysis',
 'Electronics 2026, 15(9), 1867, Optimization-Based Hosting Capacity Assessment and Enhancement: https://doi.org/10.3390/electronics15091867',
 'Energies and related grid research (2026), topology-aware PV hosting capacity: https://www.mdpi.com/2673-4826/7/3/78',
 'Sustainable Energy, Grids and Networks (2026), From droop to optimality: https://doi.org/10.1016/j.segan.2026.102379',
 'paceval Mathematical Engine official API: https://paceval.com/api/'
]
for r in refs:P(r,'small')
P('All cited scientific findings belong to their respective sources and do not certify this paceval demonstration. The full numerical audit and formula manifest are included with the GitHub research archive.','small')


def footer(canvas,doc):
 canvas.saveState();w,h=A4
 canvas.setStrokeColor(teal);canvas.setLineWidth(.4);canvas.line(MARGIN,30,w-MARGIN,30)
 canvas.setFont('DejaVu',7.2);canvas.setFillColor(navy)
 canvas.drawString(MARGIN,19,'paceval | Distribution Grid Hosting Capacity | 2026')
 canvas.drawRightString(w-MARGIN,19,f'{doc.page}')
 canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=MARGIN,leftMargin=MARGIN,topMargin=40,bottomMargin=45,title='Programmable Distribution Grid Hosting Capacity with paceval',author='paceval Mathematical Research Demonstrator',subject='Full AC network and real paceval mathematical constraint graph execution')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('WHITEPAPER_BUILT',OUT,OUT.stat().st_size)
