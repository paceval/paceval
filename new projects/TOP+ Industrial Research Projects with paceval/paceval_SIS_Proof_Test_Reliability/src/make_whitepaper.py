"""Create the independently documented English scientific PDF from recorded paceval runs.
No speed/energy benchmarks and no operational SIL certification assertions.
"""
from pathlib import Path
import json,csv,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures';RES=ROOT/'results'
J=json.loads((RES/'execution_evidence.json').read_text());H=json.loads((RES/'high_precision_audit.json').read_text());MAN=json.loads((FIG/'figure_manifest.json').read_text())
R=list(csv.DictReader((RES/'model_summary.csv').open()))
PDF=ROOT/'paceval_SIS_Proof_Test_Reliability_Whitepaper_EN.pdf'
NAVY=colors.HexColor('#0B3150');TEAL=colors.HexColor('#12A5AB');ORANGE=colors.HexColor('#DF6D36');MUTED=colors.HexColor('#48627A')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BigTitleWP',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=24,leading=28,textColor=NAVY,spaceAfter=11,alignment=TA_LEFT))
styles.add(ParagraphStyle(name='TitleWP',parent=styles['Heading1'],fontName='Helvetica-Bold',fontSize=15,leading=20,textColor=NAVY,spaceBefore=9,spaceAfter=10))
styles.add(ParagraphStyle(name='SubWP',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=10.5,leading=14,textColor=NAVY,spaceBefore=8,spaceAfter=5))
styles.add(ParagraphStyle(name='BodyWP',parent=styles['Normal'],fontName='Helvetica',fontSize=9.2,leading=13.1,textColor=colors.HexColor('#213544'),spaceAfter=7))
styles.add(ParagraphStyle(name='SmallWP',parent=styles['Normal'],fontName='Helvetica',fontSize=8.3,leading=11.5,textColor=colors.HexColor('#31485A'),spaceAfter=5))
styles.add(ParagraphStyle(name='CaptionWP',parent=styles['Normal'],fontName='Helvetica-Oblique',fontSize=8.2,leading=11,textColor=MUTED,spaceAfter=9))
styles.add(ParagraphStyle(name='FormulaWP',parent=styles['Normal'],fontName='Courier',fontSize=8.8,leading=13,textColor=NAVY,spaceBefore=7,spaceAfter=8,leftIndent=10))
styles.add(ParagraphStyle(name='RefWP',parent=styles['Normal'],fontName='Helvetica',fontSize=7.7,leading=10.2,textColor=colors.HexColor('#273C4B'),spaceAfter=6))

def P(txt,style='BodyWP'):return Paragraph(txt,styles[style])
def heading(t):return P(html.escape(t),'TitleWP')
def sub(t):return P(html.escape(t),'SubWP')
def txt(t):return P(t)
def pic(n,width=470):
    p=next(FIG.glob(f'{n:02d}_*.png'));from PIL import Image as PIL
    w,h=PIL.open(p).size
    im=Image(str(p),width=width,height=width*h/w)
    return im

def equation(name,width=474):
    from PIL import Image as PIL
    p=FIG/('equation_'+name+'.png'); w,h=PIL.open(p).size
    return Image(str(p),width=width,height=width*h/w)

def figure(n,width=464):return [pic(n,width),P(f'<b>Figure {n}.</b> '+html.escape(MAN[str(n)]['caption']),'CaptionWP')]
def table(header, rows, widths=None):
    arr=[[P(html.escape(str(x)),'SmallWP') for x in header]]+[[P(html.escape(str(x)),'SmallWP') for x in r] for r in rows]
    t=Table(arr,colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDEFF0')),('GRID',(0,0),(-1,-1),.25,colors.HexColor('#CAD6DA')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    return t

story=[]
def add(*flow):story.extend(flow)
def newpage(title):story.append(PageBreak());story.append(heading(title))
# 1
add(Spacer(1,10),P('paceval. | INDUSTRIAL MATHEMATICAL RESEARCH','SmallWP'),P('Safety Instrumented System<br/>Proof-Test Reliability Kernels','BigTitleWP'),P('WP 29 | Reusable reliability probability, uncertainty and decision-margin graphs','SubWP'))
add(Image(str(FIG/'00_sis_proof_test_hero.png'),width=506,height=253),Spacer(1,11))
add(txt('<b>Research objective.</b> Demonstrate, through the original paceval Mathematical Engine, controlled and independently verifiable mathematical screening of low-demand proof-test assumptions for two alternative channel architectures. The study evaluates synthetic failures, diagnostic and proof-test coverage, maintenance age, repair proxies, common causes and screening targets.'))
add(P('<b>Evidence status:</b> The C++ program and SDK are genuinely executed. The inputs are synthetic. No real SIF, SIL verification, functional-safety certification or schedule approval is claimed.','SmallWP'))
add(P('Research publication | 15 November 2026 | Original SDK 4.25 / local Linux runtime | English edition','SmallWP'))
# 2
newpage('Executive summary')
add(txt('Industrial facilities use safety instrumented functions (SIFs) to respond to defined process hazards. Their sensors, logic solvers and final elements may fail dangerously without immediate detection. Proof testing and diagnostic routines affect the duration for which such failures can remain hidden. Functional safety assessment must therefore distinguish mathematical reliability calculations from documented operational evidence and complete lifecycle management.'))
add(txt('This research implements two intentionally simplified low-demand architectures: M1 is an idealized single-channel (1oo1) model and M2 is an idealized parallel-channel (1oo2) model incorporating a beta-style common-cause parameter. Neither is a substitute for a complete IEC 61508 or IEC 61511 verification. The fully specified mathematical expressions are evaluated through real reusable paceval graphs, while the C++ host owns the stateful workflow and result collection.'))
add(table(['Verified quantitative evidence','New WP29 study'],[
 ('Synthetic input scenarios',f"{J['scenario_count']:,}"),('Architectural model cases',f"{J['model_point_cases']:,}"),('Executed persistent paceval graphs',f"{J['unique_graphs_executed']:,}"),('Executed paceval graph-point values',f"{J['graph_point_evaluations']:,}"),('Independent native individual checks',f"{J['independent_native_checks']:,}"),('Independent 85-digit result checks',f"{H['verified_quantities']:,}"),('Direct high-precision integrations',f"{H['independent_numerical_integrals']:,}")],[275,205]))
add(Spacer(1,9),txt('The software demonstrates formula versioning, full function evaluation, data-contract checks, batch execution, analytic sensitivities, Boolean screening rules and independent mathematical reproducibility. It does not establish measured reliability, environmental qualification, functional-safety compliance or any real economic benefit.'))
# 3
newpage('1. Industrial use case and contemporary safety practice')
add(txt('A process-industry SIF begins with a specific safety requirement, for example shutting an isolation valve following detection of dangerous pressure. At a high level, a sensor and safety logic command a final element. Dangerous detected faults can be addressed through diagnostic and repair workflows; dangerous undetected faults may remain latent until a proof test or genuine demand. A test schedule can be meaningful only if it represents the complete safety function and the failures it can reveal.'))
add(txt('IEC 61508 provides the general functional-safety framework. IEC 61511-1:2016 with its 2017 amendment provides process-industry requirements, while ISA-84 technical guidance supports SIL-verification practice. Public 2023-2024 guidance discusses simplified PFD formulations, common-cause contributions and the importance of proof-test coverage. In 2025, ISA expanded low-integrity protection-layer guidance; this does not simplify the obligations for full SIF qualification. [1-5]'))
add(txt('<b>Technical challenge.</b> In practice, failure-rate assumptions, documented diagnostic coverage, partial proof tests, restoration time, channel independence, demand mode, common causes and mission age all affect numerical estimates. A formula engine can preserve complex calculation rules and evaluate many assumption cases, but cannot authenticate the underlying test procedures or plant history.'))
add(*figure(1,446))
# 4
newpage('2. Baseline kernels and extended mathematical contracts')
add(txt('The original WP29 proposes four concise mathematical kernels: the low-demand approximation, diagnostic coverage, interval sensitivity and a margin to a project target. The new study retains these as explicit reference features and adds controlled finite-rate probability models. All numerical inputs use hours, failures per hour and dimensionless coverages.'))
add(equation('01_base_rates'),equation('02_baseline'),equation('03_target'))
add(txt('The main experiment includes positive rates and positive proof intervals to avoid evaluating the removable singularity in a quotient survival integral. Nonfinite values, invalid probabilities, invalid numeric CSV fields and out-of-domain model inputs are rejected before graph execution. Zero-rate and zero-interval limiting values are treated analytically rather than silently passed to an invalid quotient.'))
add(table(['Input / output contract','Meaning'],[
 ('lambda_D, DC','Dangerous failure rate and diagnostic coverage'),('c, T, H','Proof-test coverage, interval, assumed uncovered-mode age'),('MTTR, beta','Repair-availability proxy and common-cause fraction'),('PFD_target','Synthetic, project-specific arithmetic target'),('PFDavg, margin','Average modeled failure-on-demand probability and margin'),('Sensitivity','Explicit derivatives versus interval and coverage')],[190,290]))
# 5
newpage('3. Two distinct mathematical architecture models')
add(txt('Let u = lambda_D(1 - DC), c denote proof-test coverage, k = 1 - c and r = lambda_D DC. The per-channel detected-availability factor is B = 1/(1 + r*MTTR). The quotient A(z) = (1 - exp(-z))/z is the average survival function over one fixed proof-test cycle for positive z. Set z = u*c*T.'))
add(equation('04_survival'),equation('05_pfd_1oo1'),equation('06_pfd_1oo2'))
add(txt('M1 represents one channel. M2 assumes two synchronized, identical channels capable of fulfilling the action independently. A beta-style common-cause component is introduced explicitly. The probability formula is internally consistent with the stated simplified exponential model but is NOT a generic proof of compliance or full IEC-recommended 1oo2 calculation.'))
add(txt('<b>Specific idealizations.</b> The uncovered-failure age H is treated as frozen within the representative proof-test interval; detected failure availability is a simple stationary repair proxy; tests do not introduce unavailability; and independent-channel failure rates and common causes are homogeneous. Real proof-test execution, staggered test schedules and maintenance bypass states are excluded.'))
add(txt('All graph formulas, version identifiers, input contracts and tested API routes are archived in the machine-readable function registry. Native and high-precision references compute the probabilities independently from the graph parser.'))
# 6
newpage('4. Why the original paceval engine is meaningful here')
add(txt('Forty domain-specific mathematical execution graphs are created once in the real paceval runtime, twenty for each architectural model. The primary C++ workflow reads numeric CSV data through paceval number conversion after a strict lexical precheck, routes all independent input sets through the documented multi-graph batch API, checks every returned error code, and writes output through the official float-to-string converter.'))
add(table(['Operation or function group','Actual owner and scope'],[
 ('Input contract, data provenance','C++ host, mandatory before each graph batch'),('Dangerous detected / undetected rates','paceval M1/M2 graph executions'),('Exponential proof-test survival and PFD','paceval M1/M2 graph executions'),('Interval and coverage sensitivities','paceval explicit analytic graphs'),('Target margin, relative ratio, review score','paceval composite graph calculations'),('Logical/relational target guard','paceval Boolean graph output (0/1)'),('Screen status, result file routing','C++ orchestration of hypothetical policy'),('Independent high-precision validation','Separate mpmath and native C++')],[215,265]))
add(txt('Persistent formula versions remain separately addressable. In the absence of cross-handle dependencies, mathematical expressions are composed directly or intermediate values can be carried between graph groups without assuming that paceval is a general stateful solver. There is no MCP execution claim: this experiment uses the local original SDK.'))
add(txt('The official API and public product brief describe reusable calculation handles, arithmetic, relational and logical operators, number conversion and multi-graph batch functions. All production declarations were validated against the supplied original SDK and compatible Linux binary. [6]'))
# 7
newpage('5. Proof-cycle probability and time dependence')
add(txt('PFD is time dependent within a proof-test interval. Even when the proof-test model has an arithmetic average, its instantaneous modeled probability grows as age progresses. The example below is calculated with the paceval instantaneous-probability graph at 201 ages for both versions. Dashed levels are the corresponding paceval average-probability outputs for the same synthetic case.'))
add(*figure(2,450))
add(txt('The different channel architecture assumptions produce different results under the same numerical input vector. The plot does not represent observed test performance; nor does a lower mathematical PFD certify that a duplicated channel arrangement is appropriate for a particular SIF.'))
# 8
newpage('6. Proof-test interval and mathematical uncertainty')
add(txt('The main synthetic dataset spans multiple proof-test intervals, diagnostic coverages and proof-test coverages. Because the parameters vary together, the scatter plot is a multi-parameter cross-section rather than a one-parameter causal experiment. The companion surfaces hold the other inputs fixed, demonstrating that the same persistent graph can accept alternate documented parameter sets.'))
add(*figure(3,444))
add(*figure(4,444))
# 9
newpage('7. Two-dimensional surfaces and analytical sensitivity')
add(txt('The surface for model M2 evaluates the direct compound channel probability rather than a post-hoc approximation computed outside paceval. Analytic partial derivatives provide local uncertainty and governance cues for changes in a chosen proof interval or test coverage. They do not measure the empirical uncertainty of the failure-rate parameters themselves.'))
add(*figure(5,444))
add(*figure(9,444))
# 10
newpage('8. Assumption-driven output distributions')
add(txt('The two model architectures are evaluated against identical input rows. Their output distributions reflect the selected synthetic covariates and the mathematical independence/common-cause assumptions. Values from these two distinct architectures must not be called successive validated revisions of a real plant SIF.'))
add(*figure(7,440))
add(*figure(10,440))
# 11
newpage('9. Research-only threshold decisions')
add(txt('The end-to-end computation outputs a signed project margin, a normalized review score, an expected-loss illustration and a combined logical guard. The host maps these into SCREEN_PASS, SCREEN_REVIEW and SCREEN_REJECT for a hypothetical policy. No status may be interpreted as proof that a real safety function fulfils an SIL requirement.'))
add(*figure(6,444))
add(table(['Synthetic case result','M1: 1oo1','M2: 1oo2'],[
 ('SCREEN_PASS',R[0]['screen_pass'],R[1]['screen_pass']),('SCREEN_REVIEW',R[0]['screen_review'],R[1]['screen_review']),('SCREEN_REJECT',R[0]['screen_reject'],R[1]['screen_reject']),('Mean PFD average',R[0]['mean_pfd'],R[1]['mean_pfd'])],[230,125,125]))
# 12
newpage('10. Margins, common causes and hypothesis limits')
add(txt('A continuous margin is more informative than a binary threshold on its own. In this demonstration, the target is an explicitly assigned synthetic design-screening value. The common-cause fraction in M2 is also a hypothetical parameter, not an inferred beta from actual failures. Both must be verified independently before the approach can inform an engineering assessment.'))
add(*figure(11,441))
add(*figure(12,441))
# 13
newpage('11. Mathematical verification and numerical evidence')
add(txt('The main C++ research calculation evaluated the recorded graphs through the original paceval SDK. Separately developed native probability expressions independently checked complete PFD, instantaneous probability, margin, ratio, risk-score and dangerous failure-rate quantities for every model case. The additional mpmath reference used 85 decimal places and direct integration of instantaneous proof-cycle probability.'))
add(table(['Executed verification component','Result'],[
 ('Persistent domain graphs used',str(J['unique_graphs_executed'])),('Original paceval graph-point outputs',f"{J['graph_point_evaluations']:,}"),('Independent native checks',f"{J['independent_native_checks']:,}"),('85-digit independently checked values',str(H['verified_quantities'])),('Direct high-precision integrations',str(H['independent_numerical_integrals'])),('85-digit sensitivity checks',str(H['analytic_sensitivity_checks'])),('Documented mathematical result',H['result'])],[285,195]))
add(Spacer(1,8),txt('This mathematical verification does not confirm any site failure data, systematic fault reduction, common-cause dependence model or the certified implementation of a real proof test. Intervals of numerical rounding are not confidence intervals for equipment reliability. The technical audit files contain the numerical deviations; this public paper reports their test outcome rather than a comparative engine-accuracy benchmark.'))
# 14
newpage('12. Reproducibility and publication control')
add(txt('The repository includes original SDK integration files in src, the full C++17 demonstrator, CMake configuration, documented test commands, deterministic generated inputs, recorded result files, an explicit mathematical execution inventory, formula registry, two end-to-end architecture paths, independent mpmath reference and the thirteen result graphics.'))
add(P('cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/path/to/libpaceval.so','SmallWP'))
add(P('cmake --build build -j    ;    ctest --test-dir build --output-on-failure','SmallWP'))
add(P('./build/sis_reliability --run 100000 replay_results','SmallWP'))
add(P('python3 validation/check_mpmath.py replay_results','SmallWP'))
add(txt('The original compatible Linux shared library is deliberately excluded from the public ZIP. The source retains the official paceval interface and necessary copyright text. All Markdown files, including nested documentation, pass an archive-wide GitHub mathematics and local-link preflight with negative regression cases. A remote GitHub rendering check is not claimed.'))
add(*figure(13,435))
# 15
newpage('13. Limitations, future studies and engineering conclusion')
add(txt('The most important boundary is clear: mathematically consistent low-demand probability calculations are only one component of an industrial functional-safety verification. Even successful paceval arithmetic cannot establish whether a SIF was specified correctly, installed appropriately, tested effectively, maintained safely or shown to achieve its required risk reduction.'))
add(txt('A next-stage project would use legitimately available FMEDA failure-mode data and field proof-test observations, formally documented test coverage, sensor–logic–final-element architecture, individual component proof intervals, common-cause parameters, repair procedures, and a reference model accepted by qualified functional-safety engineers. It would then assess model validity separately from numerical execution.'))
add(txt('The positive functional result is that the original paceval engine executed reusable, versioned reliability probability and decision-kernel equations across a substantial synthetic parameter study. Independent numerical calculations reproduced the declared mathematical results. This establishes an implementation feasibility result, not a safety certification or operational approval.'))
add(*figure(8,428))
#16 references
newpage('Scientific references and source provenance')
refs=[
 '[1] IEC 61508-6:2010, Functional safety of electrical/electronic/programmable electronic safety-related systems, guidance for application of IEC 61508-2 and IEC 61508-3.',
 '[2] ANSI/ISA-61511-1-2018 / IEC 61511-1:2016+AMD1:2017, Functional safety: Safety instrumented systems for the process industry sector. ISA standards catalogue: https://www.isa.org/standards-and-publications/isa-standards/isa-84-standards',
 '[3] ISA-TR84.00.02-2022, Safety Integrity Level (SIL) Verification of Safety Instrumented Functions. ISA standards catalogue.',
 '[4] Offshore Norge, Recommended guidelines for application of IEC 61508 and IEC 61511 in the Norwegian petroleum industry, No. 070, rev. 06, October 2023. https://www.offshorenorge.no/contentassets/adc7e1512f90400cb7fe9f314600bed6/070---recommended-guidelines-for-the-application-of-iec-61508-and-iec-61511-rev.-06.pdf',
 '[5] exida, Predicting Proof Test Coverage with an FMEDA, recorded webinar, May 2023. https://www.exida.com/webinars/recordings/predicting-proof-test-coverage-with-an-fmeda',
 '[6] paceval Mathematical Engine, Official API specification and Product Brief. https://paceval.com/api/ ; https://paceval.com/product-brief/',
 '[7] The 61508 Association, SIL Calculations and use of IEC 61508-6, training presentation, June 2024. https://61508.org/wp-content/uploads/2024/11/10B-SIL-Calculations-and-use-of-IEC-61508-6.pdf',
 '[8] ISA, ISA-84 Standards and associated technical guidance. ISA-84.91.03-2025 addresses low-integrity protection layers and is distinct from verification of a full SIS.'
]
for r in refs: add(P(html.escape(r),'RefWP'))
add(Spacer(1,12),txt('<b>Evidence provenance.</b> This study was generated and executed with a compatible original paceval Linux library and independently checked equations. All numerical cases are synthetic. No external technical source verifies the new paceval results.'))

def furniture(canvas,doc):
    canvas.saveState();w,h=A4
    canvas.setStrokeColor(TEAL);canvas.setLineWidth(1);canvas.line(44,h-35,w-44,h-35)
    canvas.setFont('Helvetica-Bold',8);canvas.setFillColor(NAVY);canvas.drawString(44,h-26,'paceval. | SCIENTIFIC RESEARCH · WP 29')
    canvas.setFont('Helvetica',7.5);canvas.setFillColor(MUTED);canvas.drawRightString(w-44,h-26,'MATHEMATICAL SCREENING · NOT SAFETY CERTIFICATION')
    canvas.line(44,32,w-44,32);canvas.drawString(44,19,'Original paceval SDK | synthetic low-demand reliability study');canvas.drawRightString(w-44,19,f'{doc.page}')
    canvas.restoreState()

doc=SimpleDocTemplate(str(PDF),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=52,bottomMargin=44,author='paceval industrial research demonstrator',title='Safety Instrumented System Proof-Test Reliability Kernels',subject='Synthetic probability-of-failure-on-demand mathematical graph execution and independent verification')
doc.build(story,onFirstPage=furniture,onLaterPages=furniture)
print('WHITEPAPER GENERATED',PDF)
from pypdf import PdfReader
print('PDF PAGES',len(PdfReader(str(PDF)).pages))
