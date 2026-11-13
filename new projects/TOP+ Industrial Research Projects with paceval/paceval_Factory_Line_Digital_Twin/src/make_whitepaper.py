#!/usr/bin/env python3
"""Create a research whitepaper from actually executed original paceval results.
Every figure reads a stored original numerical/event CSV, not AI-generated experimental data.
"""
from pathlib import Path
import csv, json, io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RImage, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent.parent
PDF=ROOT/'paceval_Factory_Line_Digital_Twin_Whitepaper_EN.pdf'
R=dict(csv.reader((ROOT/'results/execution_summary.csv').open()))
sc=list(csv.DictReader((ROOT/'examples/scenario_summary.csv').open()))
H=json.loads((ROOT/'results/high_precision_audit.json').read_text())
CHECK=json.loads((ROOT/'results/trace_integrity_audit.json').read_text())
assert int(R['original_paceval_graphs'])==38
assert int(R['scenario_modules_executed'])==20
assert len(sc)==20 and H['all_passed'] and CHECK['passed']
NAVY=colors.HexColor('#12263a');DARK=colors.HexColor('#24384d');TEAL=colors.HexColor('#087b92');ORANGE=colors.HexColor('#e69c35');LIGHT=colors.HexColor('#edf4f6');MUTED=colors.HexColor('#677686')
regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',regular));pdfmetrics.registerFont(TTFont('DV-Bold',bold))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold',italic='DV',boldItalic='DV-Bold')
S={
 'kicker':ParagraphStyle('kicker',fontName='DV-Bold',fontSize=9,leading=15,textColor=TEAL,spaceAfter=7),
 'cover':ParagraphStyle('cover',fontName='DV-Bold',fontSize=26,leading=34,textColor=NAVY,spaceAfter=8),
 'subtitle':ParagraphStyle('subtitle',fontName='DV',fontSize=11,leading=17,textColor=DARK,spaceAfter=9),
 'h':ParagraphStyle('h',fontName='DV-Bold',fontSize=17,leading=24,textColor=NAVY,spaceAfter=10),
 'h2':ParagraphStyle('h2',fontName='DV-Bold',fontSize=11,leading=16,textColor=TEAL,spaceBefore=11,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.2,leading=14.4,textColor=DARK,spaceAfter=9),
 'small':ParagraphStyle('small',fontName='DV',fontSize=8.4,leading=12.4,textColor=DARK,spaceAfter=7),
 'caption':ParagraphStyle('caption',fontName='DV',fontSize=7.8,leading=11,textColor=MUTED,spaceAfter=9),
 'note':ParagraphStyle('note',fontName='DV',fontSize=9.1,leading=14.5,textColor=NAVY,spaceAfter=8),
 'tiny':ParagraphStyle('tiny',fontName='DV',fontSize=7.5,leading=11,textColor=DARK,spaceAfter=4),
}
E=[]
def P(x,sty='body'):E.append(Paragraph(x,S[sty]))
def H1(x):P(x,'h')
def H2(x):P(x,'h2')
def paragraph_list(xs):
 for x in xs:P('• '+x)
def tbl(header,items,widths=None):
 widths=widths or [170,300]
 content=[[Paragraph(str(v),S['tiny']) for v in header]]+[[Paragraph(str(c),S['tiny']) for c in r] for r in items]
 t=Table(content,colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('TEXTCOLOR',(0,0),(-1,0),NAVY),('BOTTOMPADDING',(0,0),(-1,0),9),('TOPPADDING',(0,0),(-1,0),8),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f8f9')]),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,1),(-1,-1),6),('TOPPADDING',(0,1),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.7,TEAL)]))
 E.append(t);E.append(Spacer(1,9))
def page():E.append(PageBreak())
def img(file,width=487):
 from PIL import Image
 pic=Image.open(ROOT/'figures'/file)
 h=width*pic.height/pic.width
 if h>250:
  width=width*(250/h);h=250
 E.append(RImage(str(ROOT/'figures'/file),width=width,height=h))
def figure(n,source,caption):
 img(source,455)
 P(f'<b>Figure {n}.</b> {caption}','caption')
def eqtex(formula,width=475):
 fig=plt.figure(figsize=(10,0.65),dpi=185)
 fig.patch.set_alpha(0)
 fig.text(0.01,0.45,formula,fontsize=17,ha='left',va='center',color='#12263a')
 buf=io.BytesIO();fig.savefig(buf,format='png',transparent=True,dpi=170,bbox_inches='tight',pad_inches=.11);plt.close(fig);buf.seek(0)
 from PIL import Image
 pic=Image.open(buf);h=36.0;w_raw=h*pic.width/pic.height
 width=min(width,w_raw);h=width*pic.height/pic.width
 buf.seek(0);E.append(RImage(buf,width=width,height=h));E.append(Spacer(1,6))
def foot(c,doc):
 w,h=A4
 c.saveState()
 if doc.page>1:
  c.setStrokeColor(colors.HexColor('#d8e3e8'));c.setLineWidth(.55);c.line(44,h-39,w-44,h-39)
  c.setFont('DV-Bold',7.1);c.setFillColor(TEAL);c.drawString(46,h-32,'PACEVAL | WP_040  |  SCIENTIFIC RESEARCH DEMONSTRATOR')
 c.setStrokeColor(colors.HexColor('#d8e3e8'));c.line(44,39,w-44,39)
 c.setFont('DV',7);c.setFillColor(MUTED)
 c.drawString(46,27,'WP_040 / paceval | synthetic factory-line mathematical digital twin | 13 November 2026')
 c.drawRightString(w-46,27,str(doc.page))
 c.restoreState()
doc=SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=51,bottomMargin=55,
 title='WP_040 Factory-Line Digital Twin Formula Modules with paceval',author='paceval research demonstrator',subject='Synthetic discrete-event manufacturing study with genuine paceval mathematical execution')
# Page 1
P('PACEVAL | INDEPENDENT RESEARCH WHITEPAPER | WP_040','kicker')
P('Factory-Line Digital Twin<br/>Formula Modules with paceval','cover')
P('Reusable mathematical graphs inside a finite-buffer discrete-event manufacturing study','subtitle')
img('00_factory_twin_hero.png',495)
P('Concept artwork only. The figure is not a photograph of a real plant; numbered scientific figures later in the report derive from executed CSV results.','caption')
E.append(Spacer(1,11))
tbl(['EXECUTED SCOPE','VERIFIED RESULT'],[
 ('Persistent paceval mathematical functions','38 graphs, including 20 interchangeable local process-time versions'),
 ('Manufacturing study','20 simulations, 440 synthetic incoming jobs each, four serial machines'),
 ('Actual paceval batch calculation',f"{int(R['real_multi_graph_outputs']):,} outputs through {R['real_multi_graph_batch_calls']} batch invocations"),
 ('Independent checks',f"{int(R['independent_C++_formula_checks']):,} native and {H['independent_mpmath_checks']:,} high-precision reference values"),
],widths=[170,325])
P('<b>Research status.</b> A successfully executed mathematical and deterministic event-simulation feasibility study. No real plant data, industrial commissioning, predictive fidelity or measured speed advantage is claimed.','small')
page()
# Page 2
H1('1. Introduction and industrial use case')
P('Production-line simulation must explain how arrival streams, individual machining operations, machine downtime, intermediate buffers, scrap and bottlenecks interact. A local cycle-time formula is necessary but insufficient: the same expression can produce different system throughput when an upstream station is blocked or downstream capacity is unavailable.')
P('The source proposal [1] isolates the simplified relationship <b>throughput = rate × (1 − downtime fraction)</b> and proposes a public synthetic event trace with twenty interchangeable expressions. WP_040 extends this proposal into a reproducible four-station digital-twin research demonstrator. The essential question is whether versioned mathematical modules can be evaluated by the original paceval engine and used without changing the host simulation semantics.')
H2('Scientific and industrial context')
P('NIST describes ISO 23247 as a reference framework for manufacturing digital twins [2,3]. The newly published ISO 23247-6:2026 addresses composition and interoperability among manufacturing twins [4]. The FMI 3.0 Implementers’ Guide provides additional guidance for tool and model interoperability [5]. These references inform module separation, but the present program does not claim compliance, FMU export or a real-time bidirectional industrial twin.')
H2('What the demonstrator can and cannot answer')
tbl(['RESEARCH QUESTION','DEMONSTRATED EVIDENCE'],[
 ('Can a local formula be replaced?','20 separately registered persistent cycle-time expressions; same event-host code'),
 ('Can mathematical results propagate to a line?','Per-operation paceval durations feed event scheduling, finite queues and final throughput'),
 ('Can manufacturing KPIs use paceval?','18 additional persistent graphs include quality, energy and operational metric formulas'),
 ('Can field performance be certified?','Not from this experiment: no measured factory data or calibrated failures'),
],widths=[175,320])
P('The experiment is intentionally a numerical manufacturing-system kernel, not a general-purpose shop-floor integration platform.')
page()
# Page 3
H1('2. Defined four-station event-driven model')
P('The production system represents a deterministic serial process with the stations <b>Cutting → Robot transfer → Inspection → Packaging</b>. Every incoming unit has a unique job identifier and a scheduled exogenous arrival. Each station has one processing resource and FIFO input; downstream waiting buffers have capacities 3, 4 and 3. The external station-one backlog is unbounded and reported separately.')
tbl(['ELEMENT','EXACT RESEARCH ASSUMPTION'],[
 ('Incoming trace','440 jobs; arrival times in minutes: 4.80 × job + 0.14 × (job mod 7)'),
 ('Nominal station times','4.15, 5.15, 4.55, 4.80 min per operation, respectively'),
 ('Fixed intermediate buffers','Before stations two, three, four: 3, 4, 3 waiting slots'),
 ('Temporary shutdowns','Two predetermined downtime windows per station, persisted in C++ code'),
 ('Work conservation','Each arrival finishes as a passed unit or is rejected at a completed station'),
 ('Quality outcomes','Fixed pseudo-random draws compared with paceval mathematical reject probabilities'),
 ('Event scheduling','C++ priority queue; completed upstream stations block if next FIFO buffer is full'),
],widths=[173,322])
H2('Model structure and validation requirements')
P('A machine’s processing completion time is propagated through fixed unavailable windows without performing work during downtime. The simulated duration remains the active machine time predicted by paceval. A completed but blocked upstream station cannot start the following job until the next buffer has room.')
P('The output guard requires every input job to leave the line exactly once, no overlapping operations at the same station, no downstream operation beginning before the previous station completes, and no negative processing time. These invariants are checked independently from stored event CSVs.')
page()
# Page 4
H1('3. Mathematical models and units')
P('All twenty local formula versions are defined on synthetic operating attributes: b (nominal minutes/operation), w (wear proxy in [0,1]), T (temperature in degrees Celsius), L (load proxy) and φ (deterministic phase). The index k ranges from 0 to 19. The complete literal formula strings are included in the executed registry and are never silently reconstructed by Python for scientific plots.')
eqtex(r'$t_{k,s,j}=b_s\left[1+\beta_k+0.011w_j+0.0009(T_j-22)^2+0.014L_j\right.$')
eqtex(r'$\left.\qquad+\alpha_k\sin(\varphi_j+0.09k)+\delta_k w_jL_j\right]$')
eqtex(r'$\beta_k=0.010(k-9.5),\quad\alpha_k=0.003((k\;\mathrm{mod}\;4)+1),\quad\delta_k=0.006((k\;\mathrm{mod}\;5)-2)$')
P('A time result from this function is used as the station service requirement in the actual event calendar. It can be precomputed because the source job-specific wear, temperature, load and phase are exogenous, not derived from mutable queue state. Consequently the batch path and the event simulator use exactly the same frozen input records.')
H2('Additional quality and energy formulas')
eqtex(r'$p_{\mathrm{reject}}=0.006+0.010w+0.00007(T-22)^2$')
eqtex(r'$E_{\mathrm{operation}}=0.018b(1+0.2L)\quad[\mathrm{kWh}]$')
P('Quality probability is a declared uncalibrated surrogate, not measured failure propensity. Electricity is a declared synthetic per-operation model, not meter data. The same random draws and the same quality/energy graph handles are used in all twenty scenarios to isolate the mathematical effect of replacing cycle-time formulas.')
page()
# Page 5
H1('4. Operational mathematics executed by paceval')
P('After simulating each scenario, C++ passes aggregate observed event counts and durations to further persistent mathematical graphs. Those graphs, rather than a hidden native replacement, calculate the reported final numerical KPIs.')
eqtex(r'$R_{\mathrm{good}}=60N_{\mathrm{good}}/T_{\mathrm{line}}\;[\mathrm{units/hour}]$')
eqtex(r'$Y=N_{\mathrm{good}}/N_{\mathrm{arrived}},\qquad C_{\mathrm{electricity}}=p_E\,E_{\mathrm{total}}$')
P('The study defines a station-two <b>OEE-like decomposition</b> solely for illustrating reusable mathematical modules: (busy/T) × (ideal × processed/busy) × (passed/processed). The terms correspond respectively to active-time fraction, ideal-cycle performance and station first-pass quality. They are not a certified or standardized industrial OEE measurement.')
tbl(['FUNCTION GROUP','ENGINE RESPONSIBILITY'],[
 ('20 cycle-time variants','Twenty independently stored paceval computation handles, evaluated in multi-graph batches'),
 ('Quality, electricity and local diagnostics','Six real mathematical graph handles, including reject probability, energy and cycle-time comparisons'),
 ('System and station KPIs','Twelve additional real graph handles, including throughput, yield, OEE-like metrics, power-cost proxy and target margin'),
 ('Stateful events and decisions','C++ host only: event calendar, queues, machine blocking, deterministic shutdowns, random draws and file I/O'),
],widths=[175,320])
P('The complete expression texts, API assignments and ownership proof are in `examples/formula_registry.csv` and `results/math_execution_inventory.csv`. The batch API works on many input vectors and many formula handles per invocation.')
page()
# Page 6
H1('5. Actual original paceval SDK execution')
P('The C++ program compiles against the original `paceval_main.cpp` and `paceval_main.h` interface files and loads the separately supplied compatible original Linux paceval runtime. Every expression is registered once using `paceval_CreateComputation`. The production workload uses `paceval_dGetMultipleComputationsResultsExt` for the precomputed four-station operation matrix, the numerical response surface and the final system KPI evaluations.')
tbl(['RECORDED EXECUTION FACT','ACTUAL RESULT'],[
 ('Registered original paceval graphs','38'),
 ('Distinct replaceable process models','20'),
 ('Full operation-input rows','1,760 (440 jobs × 4 stations)'),
 ('Full simulated scenarios','20, with 440 arrivals per scenario'),
 ('Multi-graph batch invocations',R['real_multi_graph_batch_calls']),
 ('Individually checked batch outputs',f"{int(R['real_multi_graph_outputs']):,}"),
 ('Independent native mathematics checks',f"{int(R['independent_C++_formula_checks']):,}"),
 ('Independent high-precision mathematics checks',f"{H['independent_mpmath_checks']:,} at 80 decimal digits"),
],widths=[215,280])
H2('Error handling and reference checks')
P('Every per-result SDK error code is checked. The tested Linux SDK’s multi-graph call reports `false` for success; treating that return value as a conventional `true = success` indicator would be incorrect. Both finite outputs and independently programmed native mathematical formula values are tested. The numerical reference calculations do not replace the original paceval outputs.')
P('The generated response surface is 61 × 61 operating points with declared wear and temperature axes. It is a real paceval calculation and does not represent measured workcell behavior.')
page()
# Page 7
H1('6. Full reproducibility and numerical audit')
P('The code and deterministic source trace establish complete provenance. Per-operation paceval values are written to CSV, then inserted without reinterpretation into the event simulator. Every run uses the same seeded quality decisions. Original expression strings are additionally published for independent review.')
tbl(['INDEPENDENT GATE','RESULT'],[
 ('CMake compilation and full CTest SDK execution','Passed'),
 ('C++ independent formula checks',f"{int(R['independent_C++_formula_checks']):,} passed"),
 ('80-decimal-digit mpmath samples',f"{H['independent_mpmath_checks']:,} passed"),
 ('Max sampled native normalized difference',R['max_native_scaled_error']),
 ('Arrival/output conservation','440 arrivals = good + scrap for each scenario'),
 ('Baseline machine overlaps','None: four station calendars checked from exported events'),
 ('Baseline stage chronology','Every visited downstream stage begins after upstream completion'),
],widths=[225,270])
H2('Determinism versus physical certainty')
P('Reproducing the exact same CSV proves deterministic software execution under the same fixed inputs, not that factory machines will produce those event trajectories. The study treats real sensor-derived wear, machine-specific downtime distributions, empirical scrap probability and observed power as separate, future calibration tasks.')
P('The independently audited output is a complete mathematical/discrete-event numerical test. Independent metrology, plant telemetry and measurement uncertainty are not included.')
page()
# Page 8
H1('7. Scientific figures I: event progression and rate')
figure(1,'01_event_timeline.png','Scheduled station processing and event-calendar completion of the first 33 jobs of model 01. Longer calendar intervals can include declared downtime.')
figure(2,'02_good_throughput_by_formula.png','Executed good-unit throughput for all twenty independently registered and reused mathematical formula versions; line inputs and quality draws are held fixed.')
page()
# Page 9
H1('8. Scientific figures II: mathematical surfaces')
figure(3,'03_paceval_cycle_surface_3d.png','Actual 61 × 61 paceval computation for process time from model 10 over the wear-temperature domain.')
figure(4,'04_formula_revision_difference_contours.png','The mathematical difference in predicted cycle time between independent models 20 and 01, computed through paceval.')
page()
# Page 10
H1('9. Scientific figures III: system behavior')
figure(5,'05_flowtime_vs_throughput.png','Line good-unit output versus the observed mean flow time of passed parts, where buffer blocking and deterministic shutdowns influence completion order.')
figure(6,'06_station_blocking_and_downtime.png','The source of lost station-minutes in scenario 01: recorded after-service blocking and scheduled downtime are different mechanisms.')
page()
# Page 11
H1('10. Scientific figures IV: KPIs and conservation')
figure(7,'07_station_2_oee_decomposition.png','Original paceval stage-two KPI outputs under a deliberately defined, non-certified OEE-style decomposition.')
figure(8,'08_cumulative_flow.png','All 440 arrivals and all final good/scrap exits represented in the same deterministic event-calendar trace.')
page()
# Page 12
H1('11. Scientific figures V: formula execution and controls')
figure(9,'09_real_formula_module_outputs.png','Literal paceval cycle-time graph values for the same station and the same input job index, with three different independently retained versions.')
figure(10,'10_energy_cost_control.png','Electricity cost remains unchanged when the versioned process-time function is changed because the isolated per-operation energy and quality definitions are held fixed.')
page()
# Page 13
H1('12. Scientific interpretation and limitations')
P('The decisive result is the successful integration of twenty interchangeable, actual paceval mathematical functions into a working finite-buffer discrete-event manufacturing simulator. Formula replacement changes process durations and therefore line waiting times and final throughput. The simulator’s stateful logic is intentionally hosted by C++, not misrepresented as one giant mathematical expression.')
H2('What has NOT been demonstrated')
paragraph_list([
 'No physical factory-line measurements, actual sensor connection, machine parameter fit, real breakdown distribution, realistic mixed-product scheduling or calibration dataset.',
 'No hardware energy measurements, no cost savings from actual equipment, no measured performance speedups, no certified industrial OEE calculation.',
 'No FMI 3.0 executable FMU, ISO 23247 conformance, standardized factory digital-twin composition, or validated digital shadow.',
 'No mathematical guarantee that any one of the twenty synthetic formulas reflects a specific machine, plant, workcell or failure process.'
])
H2('Engineering implications')
P('The approach is relevant where many expressions must be maintained or compared while preserving a stable, auditable event host. C++ can provide data ingestion, event priority, decisions and state; paceval provides deterministic functional evaluation and reusable expression lifecycle. The performance advantage, if any, requires a separately controlled timing study, not a theoretical claim from formula counts alone.')
P('All conclusions above are limited to the frozen synthetic experimental design and its reproducible outputs. The source proposal remains a research hypothesis; the new project provides a verified implementation within that boundary.')
page()
# Page 14
H1('13. Reproduction, references and research outlook')
H2('One-command reproducibility after obtaining the SDK runtime')
P('Configure from `src/CMakeLists.txt` with `-DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so`, build with CMake, run CTest, then run `./build/factory_line_twin --out . --jobs 440 --variants 20 --surface 61`. Python scripts under `src/` independently verify the CSV values, produce the scientific figures and generate this PDF.')
H2('Recommended follow-up validation')
paragraph_list([
 'Collect real machine transition logs and workpiece-level state records; define exact engineering units, time synchronization and line topology.',
 'Determine empirical distributions of breakdown duration, repair, scrap, energy and queue routing; calibrate independently from an evaluation holdout.',
 'Validate source-by-source process-time expressions and downstream throughput on measured shift intervals with uncertainty quantification.',
 'Investigate OPC UA / MTConnect integration, standard digital-thread provenance, and FMI or similar component interfaces if a co-simulation system is needed.'
])
H2('References')
refs=[
 '[1] User-supplied independent proposal: WP_040 Factory-Line Digital Twin Formula Modules, November 2026.',
 '[2] NIST (2021): Use Case Scenarios for Digital Twin Implementation Based on ISO 23247. https://doi.org/10.6028/NIST.AMS.400-2',
 '[3] NIST (2026 update): Digital Twins for Advanced Manufacturing. https://www.nist.gov/programs-projects/digital-twins-advanced-manufacturing',
 '[4] ISO 23247-6:2026, Digital twin composition. https://www.iso.org/standard/87426.html',
 '[5] Modelica Association, FMI 3.0 Implementers Guide (2026). https://modelica.github.io/fmi-guides/main/fmi-guide/',
 '[6] paceval original Mathematical Engine API. https://paceval.com/api/'
]
for r in refs:P(r,'tiny')
H2('Conclusion')
P('<b>Verified:</b> a reproducible, original-paceval C++ mathematical-execution architecture for a synthetic event-driven factory line. <b>Not claimed:</b> validated plant digital-twin fidelity, deployed integration, industrial performance benefit or a measured return on investment.','small')
# Build and ensure no overflows creating unplanned pages.
doc.build(E,onFirstPage=foot,onLaterPages=foot)
from pypdf import PdfReader
n=len(PdfReader(str(PDF)).pages)
print('Created whitepaper',PDF,'pages=',n,'bytes=',PDF.stat().st_size)
assert n==14, f'Expected 14 carefully authored pages, got {n}; visually revise content and page breaks.'
