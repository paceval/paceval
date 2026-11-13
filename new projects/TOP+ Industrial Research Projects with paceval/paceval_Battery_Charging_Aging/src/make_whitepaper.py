"""Typeset the final English WP_039 whitepaper from measured paceval CSV outputs.
The source charts and SDK results must exist; no missing results are fabricated.
Render and inspect every output page before publication.
"""
from pathlib import Path
import csv, json, math, io
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures';OUT=ROOT/'paceval_Battery_Charging_Aging_Whitepaper_EN.pdf'
SUMMARY={}
for line in (ROOT/'results/execution_summary.txt').read_text().splitlines():
    if '=' in line:
        a,b=line.split('=',1);SUMMARY[a]=b
check=json.loads((ROOT/'results/high_precision_audit.json').read_text())
report=pd.read_csv(ROOT/'examples/optimized_schedule_comparison.csv')
fonts=Path('/usr/share/fonts/truetype/dejavu')
pdfmetrics.registerFont(TTFont('DejaVu',str(fonts/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVu-Bold',str(fonts/'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVu-Bold')
NAVY=colors.HexColor('#14253B');TEAL=colors.HexColor('#0C7F8D');ACCENT=colors.HexColor('#CF821A')
GRAY=colors.HexColor('#536472');PALE=colors.HexColor('#E8F4F4');LIGHT=colors.HexColor('#F1F5F8')
PAGEW,PAGEH=A4
styles={}
styles['kicker']=ParagraphStyle('kicker',fontName='DejaVu-Bold',fontSize=8,leading=11,textColor=TEAL,spaceAfter=7)
styles['big']=ParagraphStyle('big',fontName='DejaVu-Bold',fontSize=21.3,leading=27,textColor=NAVY,spaceAfter=12)
styles['subtitle']=ParagraphStyle('subtitle',fontName='DejaVu',fontSize=10,leading=16,textColor=GRAY,spaceAfter=14)
styles['h1']=ParagraphStyle('h1',fontName='DejaVu-Bold',fontSize=15,leading=21,textColor=NAVY,spaceAfter=13,spaceBefore=1)
styles['h2']=ParagraphStyle('h2',fontName='DejaVu-Bold',fontSize=10,leading=15,textColor=TEAL,spaceAfter=7,spaceBefore=12)
styles['p']=ParagraphStyle('p',fontName='DejaVu',fontSize=9.0,leading=14.1,textColor=NAVY,spaceAfter=10)
styles['p_small']=ParagraphStyle('p_small',parent=styles['p'],fontSize=8.4,leading=12.6,spaceAfter=7)
styles['cap']=ParagraphStyle('cap',fontName='DejaVu',fontSize=7.9,leading=11.3,textColor=GRAY,spaceAfter=11)
styles['note']=ParagraphStyle('note',fontName='DejaVu',fontSize=8.6,leading=13,textColor=GRAY,spaceAfter=9)
styles['table']=ParagraphStyle('table',fontName='DejaVu',fontSize=8.0,leading=12,textColor=NAVY)
styles['table_head']=ParagraphStyle('table_head',parent=styles['table'],fontName='DejaVu-Bold',textColor=NAVY)

def P(t,kind='p'):return Paragraph(t,styles[kind])
def header_footer(canvas,doc):
    canvas.saveState()
    w,h=A4
    canvas.setStrokeColor(colors.HexColor('#C1D8DE'));canvas.setLineWidth(.65)
    canvas.line(44,h-39,w-44,h-39)
    canvas.setFont('DejaVu-Bold',7.0);canvas.setFillColor(TEAL)
    canvas.drawString(45,h-28,'PACEVAL   |   SCIENTIFIC RESEARCH DEMONSTRATOR   |   WP_039')
    canvas.setStrokeColor(colors.HexColor('#C1D8DE'));canvas.line(45,37,w-45,37)
    canvas.setFont('DejaVu',7);canvas.setFillColor(GRAY)
    canvas.drawString(45,25,'Battery charging and synthetic aging terms  |  13 November 2026')
    canvas.drawRightString(w-45,25,str(doc.page))
    canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=55,bottomMargin=49,title='WP_039 - Battery Charging Cost and Aging Terms with paceval',author='paceval Research Demonstrator',subject='Verified mathematical graph execution in synthetic battery charging scheduling')
story=[]
def S(h=8):story.append(Spacer(1,h))
def H(t):story.append(P(t,'h1'))
def H2(t):story.append(P(t,'h2'))
def p(t):story.append(P(t))
def tab(rows,widths,caption=None):
    data=[[P(str(c),'table_head' if i==0 else 'table') for c in row] for i,row in enumerate(rows)]
    tbl=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.7,TEAL)]))
    story.append(tbl)
    if caption:story.append(P(caption,'cap'))

def img(path,max_width=484,max_height=270):
    im=PILImage.open(path);w,h=im.size;f=min(max_width/w,max_height/h)
    story.append(Image(str(path),width=w*f,height=h*f,hAlign='CENTER'))
def fig(no,name,caption,max_height=245):
    img(FIG/(name+'.png'),max_height=max_height)
    story.append(P(f'<b>Figure {no}.</b> {caption}','cap'))

def page():story.append(PageBreak())
EQDIR=FIG/'equations';EQDIR.mkdir(exist_ok=True)
def eq(tag,expression,display_width=470):
    path=EQDIR/(tag+'.png')
    fig,ax=plt.subplots(figsize=(14,0.85));ax.axis('off')
    ax.text(.5,.53,'$'+expression+'$',ha='center',va='center',fontsize=18,color='#14253B')
    fig.savefig(path,dpi=180,bbox_inches='tight',pad_inches=.05,transparent=True)
    plt.close(fig)
    img(path,max_width=display_width,max_height=55)
    S(6)

# PAGE 1 - cover
story.append(P('PACEVAL   /   WP_039   /   SCIENTIFIC WHITEPAPER','kicker'))
story.append(P('Battery Charging Cost<br/>and Aging Terms<br/>with paceval','big'))
story.append(P('Reusable mathematical charging and degradation-surrogate expressions inside an audited C++ scheduling workflow','subtitle'))
img(FIG/'00_battery_charging_hero.png',max_width=502,max_height=251)
S(8)
p('<b>Research outcome.</b> 23 original paceval graphs, '+format(int(SUMMARY['PACEVAL_MULTI_GRAPH_BATCH_RESULTS']),',')+' actual Multi-Graph-Batch values and 36 feasible synthetic charging schedules.')
p('<b>Scientific boundary.</b> Charging prices, driving traces, temperatures and the aging-cost coefficients are synthetic. This work validates mathematical feasibility and repeatability; it does <b>not</b> quantify physical capacity fade, real charging savings or industrial deployment.')
story.append(P('All scientific plots are generated from the actual C++/paceval results. The cover is conceptual artwork, not an observed battery or certified equipment design.','note'))
page()

# PAGE 2
H('1. Industrial application and current research')
p('Electric-vehicle charging orchestration spans two different time scales: electricity expense is paid per charging session, while electrochemical aging accumulates over many cycles and calendar days. A practical charging service must satisfy a departure requirement, availability windows and battery constraints while comparing alternative mathematical charging policies.')
p('The supplied WP_039 proposal isolates a quadratic, time-indexed cost callback as the reproducible starting point. It deliberately does not claim that a simple quadratic term is a physical battery aging model. This project expands the mathematical kernel while preserving the host optimization boundary: a C++ dynamic-programming planner consumes the <b>actual paceval-evaluated</b> cost functions and state transitions.')
H2('Research motivation grounded in external literature')
p('Nnorom et al. (2026) examine the tension between hourly operating objectives and multi-year aging via optimization. Appleton and Fotouhi (2023) study charging/degradation tradeoffs under electrical and thermal constraints. NLR/NREL BLAST includes empirically informed temperature, SOC and cycling effects, far beyond the present toy penalty. EVI-Pro characterizes real travel-demand requirements. These references motivate the structure but their empirical models and data are <b>not</b> silently imported into this study [1-5].')
tab([['Question','What is actually demonstrated?'],['Mathematical execution','Persistent reusable expressions for energy, costs, constrained SOC dynamics, surrogate stress and gradients.'],['Optimization','Cost-minimal paths on a small 36-state, 24-hour lattice using paceval-computed edge values.'],['Physical aging','NOT modeled or predicted. Synthetic penalty coefficients are not capacity-fade or SOH calibration.'],['Industrial reality','No OEM charger controls, measured cell temperature, live tariffs or field validation.']],[145,350])
p('The central technical result is a tested, inspectable separation between a programmable mathematical engine and deterministic charging orchestration, not a superiority claim over native numerical or battery-management systems.')
page()

# PAGE 3
H('2. Defined industrial use case and system boundary')
H2('Synthetic but physically consistent 24-hour scheduling contract')
tab([['Quantity','Frozen input / rule'],['Nominal battery energy','64.4 kWh'],['AC energy to battery','Constant assumed efficiency of 0.92'],['Charger actions','0, 2, 4, 6, 8 or 10 kW; one-hour intervals'],['Availability','Hours 0-7 and 18-23; other hours cannot charge'],['Driving events','9.20 kWh at hour 8 and 5.52 kWh at hour 18'],['SOC limits and target','15%-92% operating interval; 80% at hour 24'],['Departure policy','SOC before 08:00 must be at least 20/35'],['Input scenarios','6 deterministic synthetic time-of-use tariffs and temperatures'],['Cost policies','Aging weights 0, 8, 30 EUR per synthetic risk unit, and two formula versions']],[162,333])
H2('Processing stages')
p('<b>1.</b> The host generates repeatable tariff/travel/cell-temperature inputs. <b>2.</b> Paceval graph handles are created once per run. <b>3.</b> Multi-Graph batches evaluate proposed 24-hour state/power transitions and 3D chart surfaces. <b>4.</b> C++ rejects infeasible transitions and carries out dynamic programming. <b>5.</b> Independent C++/mpmath checks verify numerical calculations and energy-balance invariants. <b>6.</b> Only executed data are exported as scientific charts.')
p('All claims are relative to the declared <b>discrete</b> model. Optimizing this contract is not a guarantee of a globally optimal continuous-time policy or a safe vehicle control command.')
page()

# PAGE 4
H('3. Mathematical model: energy and state of charge')
p('Let P be charger input power in kW, Δt the slot length in hours, C the energy capacity in kWh, D the fixed driving-consumption event in kWh and s the dimensionless state of charge. All charging and driving energy balances are evaluated with persistent paceval graphs.')
H2('Purchased electrical energy and stored electrical energy')
eq('grid_energy',r'E_{\mathrm{grid},t}=P_t\Delta t,\qquad E_{\mathrm{stored},t}=\eta P_t\Delta t')
H2('Temporal state transition including prescribed driving')
eq('soc_transition',r's_{t+1}=s_t-\frac{D_t}{C}+\frac{\eta P_t\Delta t}{C}')
p('The application has a 35-interval SOC lattice (36 states). Because a 2 kW charging action stores 1.84 kWh per hour and 1/35 of 64.4 kWh is exactly 1.84 kWh, every permitted state transition remains on this discrete lattice. This exact alignment is intentional and is verified on each selected path.')
H2('Tariff charge and physically meaningful feasibility gates')
eq('electricity_charge',r'C_{\mathrm{elec},t}=c_tP_t\Delta t')
eq('soc_margins',r's_{\mathrm{postdrive},t}\geq s_{\min},\quad s_{t+1}\leq s_{\max},\quad 0\leq P_t\leq P_{\max}')
p('The engine directly computes the margins for post-drive SOC, next-step upper SOC and remaining charger power. The host enforces nonnegative margins and availability as discrete decisions, with a further 08:00 departure reserve and 24-hour terminal SOC equality.')
page()

# PAGE 5
H('4. Mathematical model: explicitly synthetic aging terms')
p('The original quadratic regularizer is preserved, but it is separated from two independent, non-calibrated stress terms. This distinction prevents a common misinterpretation: a power penalty is a mathematical preference, not an empirically established loss of usable battery capacity.')
H2('Cycle-like and calendar-like risk per slot')
eq('cycle',r'R_{\mathrm{cy},t}=k_{\mathrm{cy}}\left(\frac{P_t}{10\,\mathrm{kW}}\right)^2\Delta t')
eq('calendar',r'R_{\mathrm{cal},t}=k_{\mathrm{cal}}s_{\mathrm{mid},t}^2\exp\left[\alpha(T_t-25)\right]\Delta t')
p('The constants k<sub>cy</sub>=0.020, k<sub>cal</sub>=0.003 and α=0.040/°C are user-defined synthetic parameters per hour, not inferred from a cell or fleet dataset. The model distinguishes cycle- and calendar-style functions but does not estimate SOH, loss of lithium inventory, calendar lifetime, battery replacement economics or charge acceptance.')
H2('Two independently preserved objective versions')
eq('objectivev1',r'J_t^{(1)}=c_tP_t\Delta t+w_a(R_{\mathrm{cy},t}+R_{\mathrm{cal},t})+w_s(P_t/10)^2\Delta t')
eq('objectivev2',r'J_t^{(2)}=c_tP_t\Delta t+w_a(R_{\mathrm{cy},t}+R_{\mathrm{cal},t})(1+0.2s_{\mathrm{mid},t})+w_s(P_t/10)^2\Delta t')
p('Both expressions are real paceval computation handles, with 0/8/30 EUR per synthetic risk unit used as explicit what-if valuations. The second version introduces an SOC-weighted policy multiplier; the original function remains independently callable.')
page()

# PAGE 6
H('5. Execution: maximizing the actual paceval mathematical role')
p('The C++ application links the original, unchanged <b>paceval_main.h</b> and <b>paceval_main.cpp</b> interface to the original Linux runtime. Twenty-three mathematical functions are created once; repeated evaluations use <b>paceval_dGetMultipleComputationsResultsExt</b> on the same handles.')
tab([['Graph family','Real execution owner'],['Energy / transitions (6)','paceval: grid/stored/driving energy, post-drive/midpoint/next SOC'],['Tariff and aging (6)','paceval: tariff charge, synthetic cycle/calendar/total risk, age cost, quadratic smoothing'],['Two complete costs (2)','paceval: version 1 and independently retained version 2'],['Constraint margins (3)','paceval: lower post-drive SOC, upper next SOC, charger margin'],['Carbon proxy and derivatives (6)','paceval: synthetic grid-carbon term and marginal tariff, cycle, calendar, smooth, full objective'],['Scheduler and reductions','C++: deterministic traces, feasible-state filtering, path selection, reporting and CSV'],['Independent numerical checks','C++ native reference plus mpmath 80-digit arithmetic']],[200,295])
H2('Batch execution and error semantics')
p('Each input vector contains 17 declared model variables and every persistent handle shares the same variable declaration. The numerical result buffer is interpreted in graph-major order. The SDK batch return is treated as an error flag for this tested Linux library and <b>every individual returned error code and nonfinite output is checked</b>. Creation errors are checked separately.')
p('The machine-readable <b>results/math_execution_inventory.csv</b> records the exact execution owner and API for each graph. Dynamic programming, random-number generation, sampling, selection, data movement and plotting are not mislabeled as paceval functionality.')
page()

# PAGE 7
H('6. Defined optimizer and complete run conditions')
H2('A discrete constrained global search over the declared lattice')
p('The host searches 24 one-hour stages and 36 SOC states with six charging actions per stage. Every candidate mathematical edge is evaluated by paceval, including state progression, both objectives, all SOC margins, energy and marginal cost functions. C++ dynamic programming then chooses the minimum-cost feasible edge sequence for the chosen synthetic tariff and policy version.')
p('At the end of every run the program reconstructs the selected trajectory and verifies the exact terminal state, time-dependent charger availability, the departure reserve, nonnegative SOC margins and the kWh balance. This is an optimum on the finite declared state/action grid only.')
H2('Declared research-workload dimensions')
tab([['Dimension','Count / value'],['Tariff cases','6 fixed synthetic profiles'],['Risk valuations','3 explicit synthetic aging weights'],['Formula versions','2 persistent independent mathematical cost functions'],['Completed schedule solutions','36 valid trajectories'],['Hourly solution output rows','864 (36 schedules × 24 steps)'],['2D mathematical surface','61 × 61 = 3,721 graph-evaluated points'],['Model scale','23 persistent paceval formula handles × every tested input']],[205,290])
H2('Energy balance as an independent scientific invariant')
eq('balance',r'64.4\cdot \frac{17}{35}+0.92\cdot38.0-14.72=64.4\cdot0.80')
p('All 36 schedules satisfy this 38.00 kWh grid input, 34.96 kWh stored energy, 14.72 kWh synthetic driving consumption and 80% final SOC. The thermal, price and electrochemical assumptions remain simplified by design.')
page()

# PAGE 8
H('7. Real SDK execution and independent numerical validation')
tab([['Actually executed quantity','Verified outcome'],['Original persistent paceval graphs',SUMMARY['PACEVAL_GRAPHS']],['True Multi-Graph-Batch result values',format(int(SUMMARY['PACEVAL_MULTI_GRAPH_BATCH_RESULTS']),',')],['Actual Multi-Graph-Batch API calls',SUMMARY['PACEVAL_BATCH_INVOCATIONS']],['Scalar reusable-graph checks',SUMMARY['PACEVAL_SCALAR_SPOT_CHECKS']],['Native C++ oracle result checks',format(int(SUMMARY['CXX_INDEPENDENT_REFERENCE_VALUES']),',')],['Independent 80-digit mpmath oracle checks',format(check['checked_paceval_graph_values'],',')],['Valid optimized charging schedules','36 / 36'],['Rejected deliberately invalid inputs','11 / 11'],['Original-SDK integration CTest','1 / 1 passed']],[270,225])
H2('Measured results, not performance or lifetime promises')
p('Every execution figure above comes from the finished original-SDK run and its recorded result files. The independent high-precision checks re-evaluate the literal mathematical registry using mpmath with 80 decimal digits. The native C++ reference is a separate implementation of the specified formulas. They demonstrate computational consistency for the executed domain; they do <b>not</b> prove globally bounded errors or scientifically calibrated battery behavior.')
p('There are intentionally no advertised processor speedups, native-vs-paceval accuracy-difference plots or claims of industrial cost savings in this public report. The numerical audit logs and complete formula inventory remain in the release package for reviewers.')
page()

# PAGE 9
H('8. Input tariffs and an optimized charging schedule')
p('The first figure shows the six fixed, synthetic electricity price traces. The second uses the exact paceval-evaluated 24-hour path selected by the C++ optimizer for the “night discount” case (aging weight 8, objective version 1).')
fig(1,'01_fixed_tariff_profiles','Six deterministic synthetic electricity tariffs. They are generated inputs, not provider prices or measured electricity market quotes.',235)
fig(2,'05_optimized_charge_power_and_tariff','Optimized charging power and the corresponding input tariff. The mathematical edge values were computed by the original paceval SDK.',245)
page()

# PAGE 10
H('9. Composite charging cost: actual paceval surfaces')
p('A 61-by-61 grid of charging power and starting SOC was evaluated in the actual SDK; only the visualization was created by matplotlib. The synthetic slot inputs are fixed at 0.31 EUR/kWh and 28°C, with a risk valuation of 8 EUR per synthetic risk unit.')
fig(3,'02_paceval_total_cost_surface_3d','3D composite cost surface, including tariff, surrogate aging valuation and power regularization.',260)
fig(4,'04_total_cost_contours','Contours of the identical paceval-evaluated mathematical objective; no interpolated measurements are claimed.',235)
page()

# PAGE 11
H('10. Synthetic degradation terms and sensitivity')
p('The first response surface is a deliberately uncalibrated cycle/calendar risk proxy; it must not be interpreted as a measured capacity loss or expected lifetime. The second is a real graph-based analytic derivative of the mathematical version-1 objective.')
fig(5,'03_aging_surrogate_surface_3d','Synthetic aging-risk surface on a 61-by-61 grid, executed by paceval.',254)
fig(6,'09_analytical_marginal_cost','Exact analytic marginal objective with respect to charging power evaluated as a separate paceval computation handle.',235)
page()

# PAGE 12
H('11. Feasible SOC and charging decision outcomes')
p('SOC trajectories are fully exported and audited against the selected paceval state transitions; the discrete scheduler enforces SOC safety, departure reserve and target equality. Charging is not permitted in the fixed driving interval.')
fig(7,'06_charge_schedule_soc_trajectories','Selected SOC trajectories for three synthetic tariffs. All reach exactly 80% at the terminal hour.',245)
fig(8,'10_optimized_schedules_heatmap','24-hour charging-power decisions for all six price profiles (aging weight 8, version 1), after the actual mathematical batch evaluation.',235)
page()

# PAGE 13
H('12. Cost/risk tradeoffs and preserved formula versions')
p('The horizontal axis represents synthetic electricity expense; the vertical axis is a dimensionless, uncalibrated stress index. The scatter is a mathematical tradeoff demonstration, not an estimate of battery lifetime or an achieved reduction in cell degradation.')
fig(9,'07_electricity_vs_aging_tradeoff','The chosen charging schedule changes as the assumed aging valuation changes, even when energy feasibility is held fixed.',245)
fig(10,'08_versioned_cost_functions','Version 2 adds an explicitly declared SOC factor and remains separately callable alongside version 1.',235)
page()

# PAGE 14
H('13. Scientific interpretation, reproducibility and next steps')
p('<b>Conclusion.</b> This is a successful real paceval Mathematical Engine demonstration of reusable, versioned cost functions and constrained numerical state transitions inside an industrially motivated charging planner. The code produced real optimization results under an explicit synthetic energy/scheduling contract. It did not use an experimental electrochemical aging model, measured charging telemetry, live electricity price data or a commercial BMS.')
H2('Reproduce with original SDK files and independently provided runtime')
p('From the GitHub package root, configure: <b>cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so</b>; build with <b>cmake --build build -j</b>; run <b>ctest --test-dir build --output-on-failure</b>; execute <b>./build/battery_charging_aging --out . --profiles 6 --weights 3 --surface 61</b>; then run the independent high-precision, scientific consistency, diagram and PDF scripts described in README.md.')
H2('Required next steps for a real industrial pilot')
p('Integrate independently licensed and time-stamped electricity prices and actual driving schedules; validate the charger/BMS limits and vehicle telemetry; replace the nonphysical risk proxy with chemistry- and temperature-specific experimental aging data (for example, a BLAST-derived surrogate); and compare observed SOH trajectories under independent validation splits. This study does not pre-approve a charge-control strategy.')
H2('Selected scientific and technical sources')
for item in [
 '[1] Nnorom et al. (2026), Aging-Aware Battery Control via Convex Optimization. https://web.stanford.edu/~boyd/papers/aging_aware_battery_control.html',
 '[2] NLR/NREL, Battery Lifespan and BLAST. https://www.nlr.gov/transportation/battery-lifespan',
 '[3] NLR/NREL, BLAST battery modeling. https://nrel.sitefinity.cloud/transportation/blast',
 '[4] Appleton &amp; Fotouhi (2023), A Model-Based Battery Charging Optimization Framework. https://doi.org/10.1007/s42154-023-00221-8',
 '[5] NLR/NREL EVI-Pro, charging demand and travel profiles. https://nrel.sitefinity.cloud/transportation/evi-pro',
 '[6] paceval public C++ SDK / API. https://github.com/paceval/paceval']:
    story.append(P(item,'p_small'))
story.append(P('<b>Source data:</b> user-supplied WP_039 proposal (November 2026). All experiments use synthetic deterministic inputs. Output evidence: examples/ and results/ in this release.','note'))

doc.build(story,onFirstPage=header_footer,onLaterPages=header_footer)
print('Generated',OUT)
