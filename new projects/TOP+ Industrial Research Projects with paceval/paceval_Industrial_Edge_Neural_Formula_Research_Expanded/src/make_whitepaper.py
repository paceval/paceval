#!/usr/bin/env python3
"""Scientific English research report grounded in executed paceval result files."""
from pathlib import Path
import json,csv,re
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor,white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image
P=Path(__file__).resolve().parents[1]; out=P/'paceval_Industrial_Edge_Neural_Formula_Research_Expanded_EN.pdf'
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
ink=HexColor('#1E2C33');teal=HexColor('#238B86');pink=HexColor('#C95069');grey=HexColor('#5B6872');pale=HexColor('#F0F6F5')
W,H=595.276,841.89; L=48; R=48; CW=W-L-R;B=62
C=Canvas(str(out),pagesize=(W,H),pageCompression=1);C.setTitle('From trained neural networks to reusable paceval execution graphs - Industrial edge research');C.setAuthor('paceval research demonstrator | 13 November 2026')
N=0;y=H-63
style=ParagraphStyle('paragraph',fontName='DejaVu',fontSize=9.25,leading=14.4,textColor=ink,spaceAfter=4,allowWidows=0,allowOrphans=0)
small=ParagraphStyle('small',parent=style,fontSize=8.05,leading=11.8)
caption=ParagraphStyle('caption',parent=small,textColor=grey,fontSize=7.55,leading=10)

def page(title=None,kicker='INDUSTRIAL EDGE AI  /  PACEVAL RESEARCH'):
 global N,y
 if N:C.showPage()
 N+=1;y=H-51
 C.setFillColor(ink);C.setFont('DejaVuBold',8);C.drawString(L,H-28,kicker)
 C.setStrokeColor(teal);C.setLineWidth(.9);C.line(L,H-35,W-R,H-35)
 if title:sub(title)
 C.setFont('DejaVu',7.4);C.setFillColor(grey);C.drawString(L,34,'paceval  |  Synthetic research demonstrator  |  13 Nov 2026');C.drawRightString(W-R,34,str(N))

def gap(v=8):
 global y;y-=v

def para(s,variant='normal'):
 global y
 styl={'normal':style,'small':small,'caption':caption}[variant];p=Paragraph(s,styl);w,h=p.wrap(CW,800)
 if y-h<B:page()
 p.drawOn(C,L,y-h);y-=h+7

def sub(s):
 global y
 if y<100:page()
 C.setFillColor(ink);C.setFont('DejaVuBold',17 if N>1 else 26)
 # single or two-line heading (wrap using paragraph)
 p=Paragraph(s,ParagraphStyle('head',fontName='DejaVuBold',fontSize=17 if N>1 else 26,leading=22 if N>1 else 31,textColor=ink));w,h=p.wrap(CW,120);p.drawOn(C,L,y-h);y-=h+17

def head(s):
 global y
 if y<120:page()
 p=Paragraph(s,ParagraphStyle('subhead',fontName='DejaVuBold',fontSize=11.2,leading=15,textColor=teal));w,h=p.wrap(CW,120);p.drawOn(C,L,y-h);y-=h+6

def image(name, width=CW,height=None,cap=None):
 global y
 fn=P/'figures'/name
 with Image.open(fn) as im:ow,oh=im.size
 if height is None:height=width*oh/ow
 if y-height <B+26:page()
 C.drawImage(ImageReader(str(fn)),L+(CW-width)/2,y-height,width=width,height=height,mask='auto');y-=height+8
 if cap:para(cap,'caption')

def table(headers,rows,widths=None):
 global y
 data=[headers]+rows;t=Table(data,colWidths=widths if widths else [CW/len(headers)]*len(headers),hAlign='LEFT')
 t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,0),'DejaVuBold'),('FONTNAME',(0,1),(-1,-1),'DejaVu'),('FONTSIZE',(0,0),(-1,-1),8),('LEADING',(0,0),(-1,-1),11.7),('BACKGROUND',(0,0),(-1,0),pale),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,HexColor('#FAFBFB')]),('TEXTCOLOR',(0,0),(-1,-1),ink),('GRID',(0,0),(-1,-1),.25,HexColor('#DCE5E4')),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]));tw,th=t.wrap(CW,700)
 if y-th<B:page()
 t.drawOn(C,L,y-th);y-=th+12

def bullet(s):para('<font color="#238B86"><b>•</b></font>  '+s)

def footer():C.save()
summary=json.loads((P/'results/sdk_run_summary.json').read_text())
audit=json.loads((P/'results/independent_high_precision_audit.json').read_text())
with (P/'results/split_metrics.csv').open() as f:rows=list(csv.DictReader(f))
metrics={(a['version'],a['split']):a for a in rows}
# Cover
page(kicker='SCIENTIFIC RESEARCH  /  EXECUTED C++ FEASIBILITY DEMONSTRATOR')
sub('From Trained Neural Networks to Reusable Mathematical Execution Graphs')
para('<b>Industrial edge condition monitoring with original paceval SDK 4.25</b>')
image('00_edge_neural_formula_hero.png',height=247,cap='Conceptual illustration: bearing features, neural inference, reusable mathematical execution and advisory decisions.')
head('Research question')
para('Can a small frozen trained neural network, its numerical feature normalization and its version-controlled advisory scoring be deployed as reusable paceval execution graphs while preserving mathematical results and allowing controlled model revisions?')
head('Evidence classification')
para('This report includes real execution with the user-provided Linux paceval shared library, a synthetic training dataset, two trained network revisions, real graph executions and independent numeric reference calculations. It does <b>not</b> establish industrial fault-detection validity or certified numerical error bounds.')
gap(8);para('<b>Research date:</b> 13 November 2026  |  <b>Programming language:</b> C++  |  <b>Data:</b> entirely synthetic  |  <b>Arithmetic:</b> double precision')
# p2
page('1. Executive summary')
para('Industrial condition monitoring analyzes vibration, motor-current signals, temperatures and operating points to identify possible equipment deterioration. Compact trained neural networks are one candidate for classifying derived feature vectors. The special proposition of paceval is not network training: it is the deployment of frozen mathematical expressions as persistent, reusable computation objects alongside other application-specific formulas.')
table(['Executed item','Observed result'],[
 ['Persistent paceval graph handles',str(summary['graph_count'])],['Two trained models, architecture','8 inputs → 8 → 4 → 1'],['Synthetic inputs / independent virtual bearing identities','1,536 / 48'],['Graph outputs and batch calls',f"{summary['graph_outputs']:,} / {summary['batch_calls']:,}"],['Independent 80-digit high-precision comparisons',f"{audit['independent_network_and_score_comparisons']:,}"],['Largest audited network error',f"{audit['max_absolute_difference_in_neural_output']:.2e}"],['Numerical outcome','PASS; no threshold flips in audited subset']],[280,CW-280])
image('01_pipeline_architecture.png',height=130,cap='The evaluation system separates external feature acquisition, frozen model weights, deterministic mathematical inference, rule evaluation and the final advisory policy.')
para('The comprehensive trained-network experiment remains a controlled synthetic pilot. Industrial functional validation would require a permitted real dataset and tests on held-out physical bearings, including operating-condition shifts, feature validation and domain-specific error analysis.')
# p3
page('2. Scientific foundation and contribution of the original paceval research')
para('The accompanying paceval paper, <i>Conversion of neural networks to closed-form expressions as human-readable mathematical functions</i> (2015–2023), proposes recording scalar operations with a <b>RecordFormula</b> value and tracing a neural network dynamically through Julia/Flux. Each scalar stores its numerical value and the mathematical expression that produced it. The paper also describes splitting the output into formulas with intermediate variables at network-layer boundaries, avoiding repeated expansion of identical subexpressions.')
head('How this study extends the original method')
bullet('Replaces an untrained synthetic test network with two reproducibly <b>trained</b>, frozen 8–8–4–1 models. The models remain synthetic and have no established clinical or industrial diagnostic validity.')
bullet('Implements the same mathematical export idea through an explicit C++ architecture-aware exporter and a separately executable Python scalar operator tracer. No untested Julia, Flux or ONNX-to-paceval conversion is claimed.')
bullet('Executes normalizations, all neural layers, flattened output formulas and downstream advisory mathematics through the original paceval API. The host handles CSV, model lifecycle and discrete rule selection.')
bullet('Independently checks the complete computations and uses held-out synthetic bearing identities and shifted operating conditions to separate numerical parity from generalization quality.')
image('07_formula_export_size.png',height=206,cap='Executed scalar-tracer output shows why explicit intermediate variables reduce duplicated textual formula length for this architecture.')
# p4
page('3. Industrial use case and dataset construction')
para('A monitoring gateway might collect vibration acceleration, motor-current signals, rotational speed, load and temperatures. Conventional signal processing produces features such as RMS, crest factor, kurtosis and band energy. A compact frozen network transforms these features into an advisory score; a later rule layer controls whether operators are asked to inspect or review the measurement. The model does not actuate a machine.')
head('Frozen synthetic experimental data')
para('The generator creates 48 distinct virtual bearings, 32 windows per bearing. Their identities are split into 24 training groups, 8 validation groups, 8 ordinary held-out groups and 8 groups with deliberately shifted rotational operating conditions. Normalization mean and standard deviation are calculated only from the training groups. Each frozen revision is trained by deterministic batch Adam for 600 epochs using only the training group.')
para('Eight input features are vibration RMS, crest factor, kurtosis, vibration band energy, motor-current RMS, harmonic-current ratio, bearing temperature and shaft speed. Labels are synthetic and follow the generator rules: they are not measured physical faults. Fault-prediction percentages in the following plots therefore characterize only this controlled simulation.')
image('05_normalized_feature_shift.png',height=232,cap='RMS feature-distance surrogate calculated through paceval. A larger shifted-group distance reflects the chosen synthetic operating-point construction, not a validated out-of-distribution detector.')
# p5
page('4. Mathematical model and explicit execution ownership')
head('Frozen network')
para('For feature vector <b>f</b>, the normalization is xᵢ = (fᵢ − μᵢ)/σᵢ. The hidden layers are h₁ = sigmoid(W₁x + b₁) and h₂ = sigmoid(W₂h₁ + b₂). The network output is s = sigmoid(w₃ᵀh₂ + b₃), where sigmoid(z) = 1/(1 + exp(−z)). All weights and constants are exported with round-trip binary64 decimal precision.')
head('Execution architecture')
para('Eight reusable paceval graphs normalize raw features. Each trained model uses eight first-layer graphs, four second-layer graphs, one output graph and one alternatively flattened output expression. The flattened and layered paths represent the same frozen network using different graph organizations. Twenty-four additional graph handles, twelve per model version, implement decision margins, review bands, model-aware operating corrections, advisory scoring, feature distance and analytic derivatives.')
para('The C++ host intentionally retains loading and validation, model/graph registry, chunk orchestration, outlier rejection and the final discrete MONITOR / REVIEW / ADVISE_INSPECTION action selection. Model training is offline in Python. No automatic differentiation or TINC-based certified interval result is claimed.')
image('10_executed_reference_overlay.png',height=227,cap='Actual original-SDK paceval outputs and an independently coded C++ forward pass overlay on held-out synthetic bearing vectors.')
# p6
page('5. Synthetic trained-model results')
para('Classification quality is a property of the chosen synthetic feature generator and trained weights, not an improvement introduced by paceval. Both the independently implemented native calculation and paceval evaluate the same frozen mathematics. The independent held-out and shifted partitions intentionally challenge the generator-specific learned relationship.')
summary_rows=[]
for v in ['v1','v2']:
 for sp,label in [('validation','Validation'),('test','Held-out'),('shift_test','Shifted operation')]:
  a=metrics[(v,sp)];summary_rows.append([v,label,f"{100*float(a['accuracy']):.2f}%",f"{100*float(a['negative_false_alarm_rate']):.2f}%"])
table(['Model','Partition','Accuracy','False-alert rate'],summary_rows,[67,160,126,CW-353])
image('02_generalization_and_false_alerts.png',height=226,cap='Observed synthetic classification performance differs across partitions. The original research question requires independent bearing-level holdout, not random window-level leakage.')
# p7
page('6. Decisions, domain shift and limitations')
para('The operational postprocessing uses a version-controlled mathematical rule, which is an illustrative advisory score, <b>not</b> a calibrated probability of failure. For score s, normalized vibration x₀, shaft speed x₇ and temperature x₆, the prototype constructs z = (s − 0.5) + a·x₀ − b·x₇ + 0.02·x₆ and q = sigmoid(3z). The coefficient pair (a,b) is (0.08,0.035) for v1 and (0.11,0.025) for v2. These coefficients are research fixtures rather than parameters fitted to actual maintenance costs.')
para('The signed margin m = s − 0.5 and review width 0.08 define an advisory rule: REVIEW when |m| is below 0.08; otherwise ADVISE_INSPECTION for nonnegative m and MONITOR for negative m. No production action is automated, and an equipment safety controller remains external.')
image('08_advisory_outcomes.png',height=210,cap='Actual paceval score margins with deterministic C++ category selection. Changes reflect synthetic features and model coefficients.')
image('11_paceval_composite_advisory_score.png',height=208,cap='The operating-point correction changes the advisory index even with the same trained network output; it must be separately audited and version-controlled.')
# p8
page('7. Versioned mathematical model updates')
para('Two frozen models are simultaneously available rather than modifying the active graph in place. The project emits a machine-readable registry of every expression, a model manifest with data and weight SHA-256 hashes, a complete score-difference file and an independent dynamic-trace audit. This demonstrates predictable deployment artifacts and traceability, not a quantified reduction in real engineering release costs.')
image('04_version_revision_scatter.png',height=350,cap='Recomputed frozen-network revision across held-out and shifted synthetic cases. Differences are expected because weights were independently trained. The diagonal indicates identical outputs.')
para('Any production deployment would still need a versioned data schema, signed binaries or formula assets, update/rollback procedure, operational monitoring, and separation between training, numerical evaluation and safety logic.')
# p9
page('8. Executed paceval functionality and model portability')
para('The central experimental result is the successful representation and execution of an entire frozen, trained neural model together with preprocessing and mathematical decision rules using the original paceval API. The model is not retrained or recompiled when new feature vectors are evaluated. Both trained revisions retain independent graph registries and can be selected without modifying the C++ orchestration algorithm.')
image('06_paceval_graph_coverage.png',height=240,cap='Functional inventory of all 60 executed persistent paceval computation objects. These are actual graphs registered through the user-supplied original SDK, not abstract diagrams.')
table(['Executed mathematical component','Verified implementation'],[
 ['Training-group feature normalization','8 shared persistent paceval graphs'],
 ['Frozen two-layer MLP','13 layer-structured graphs per model revision'],
 ['Alternative closed output form','1 flattened graph per revision'],
 ['Margins, correction, scores and derivatives','12 advisory graphs per revision'],
 ['Input validation and discrete policy','C++ host, independently traceable'],
 ['Two model revisions','Available concurrently; reproducible weight manifest']], [257,CW-257])
para('The scalar path and the multi-graph batch path are both exercised in the C++ study. Mathematical equivalence is checked with independently implemented calculations. An FPGA/ASIC execution-graph implementation is a separate architectural research direction and was not evaluated in this feasibility experiment.')
# p10
page('9. Numerical verification and decision stability')
para('Every synthetic row and both frozen versions were compared against independently coded native C++ inference inside the application. The layered output was also compared to the flattened mathematical export. A separate Python program independently implemented 80-digit decimal inference, training-fold normalization, versioned advisory index and inspection-priority formulas.')
table(['Independent check','Outcome'],[['Numerical precision','80 decimal digits'],['Number of selected samples per frozen model',str(audit['audited_samples_per_version'])],['High-precision checks, including composed outcomes',f"{audit['independent_network_and_score_comparisons']:,}"],['Maximum network absolute difference',f"{audit['max_absolute_difference_in_neural_output']:.3e}"],['Threshold flips among audited samples',str(audit['threshold_flips_on_audit'])],['C++ native vs paceval and flattened path','Every input, both versions: PASS']],[324,CW-324])
para('These checks are finite-sample empirical audits. They do not prove a universal numerical error bound, certified threshold stability, clinical or industrial predictive validity, or TINC interval certification. Since the score distribution is sharply concentrated near 0 and 1, specific threshold stress tests should accompany any future real deployment.')
image('09_threshold_margin_surface_3d.png',height=253,cap='Executed paceval margin function over score and threshold values. The planar surface is mathematically expected because m = score − threshold.')
# p11
page('10. Mathematical integration and research extensions')
para('A functional research extension is to deploy the neural output together with operating-point corrections, nonlinear advisory scoring, constraint margins and other plant-specific mathematical functions in one versioned paceval execution layer. The present prototype demonstrates these classes of formulas in a small reproducible synthetic workflow.')
image('12_operating_point_surface_3d.png',height=345,cap='Nonlinear operating-point advisory surface: executed original paceval graph at fixed network score, varying normalized vibration and speed. Formula revisions can change the surface without changing the model architecture.')
head('Falsifiable next experiment')
para('Train a compact network on permitted industrial bearing measurements and keep physical bearing identities disjoint across training and independent testing. Validate the automatic export against the originating model at identical input windows, operators, weights and normalization. Test revision and rollback semantics, input rejection, decision-margin stability and operating-point shifts. An FPGA/ASIC implementation of the same execution graphs is a plausible future architecture but has not been demonstrated in this experiment.')
# p12
page('11. Reproduction, boundaries and scientific sources')
head('Reproduction instructions')
para('The complete ZIP contains <b>src/edge_neural_formula.cpp</b>, original SDK C++ API glue files, the source-only synthetic trainer, frozen decimal weights, numerical parity outputs, the RecordFormula-style operator tracer, high-precision reference code, the figure generator and this report. The proprietary/runtime binary is deliberately excluded from the distributable ZIP and must be provided separately.')
para('<font face="DejaVuBold">1.</font> Build with <font face="DejaVu">cmake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so</font>, then <font face="DejaVu">cmake --build build -j</font>.')
para('<font face="DejaVuBold">2.</font> Execute <font face="DejaVu">./build/edge_neural_formula . 128</font> from the project root. Run the independent scripts <font face="DejaVu">python3 src/verify_independent.py</font> and <font face="DejaVu">python3 src/trace_neural_formulas.py</font>.')
para('<font face="DejaVuBold">3.</font> Regenerate plots with <font face="DejaVu">python3 src/make_figures.py</font>. Reproducing the frozen training data requires Python NumPy; executing C++ itself requires only the original paceval SDK, libstdc++ and the Linux runtime.')
head('Scientific and operational boundaries')
para('No Paderborn bearing records, real patient information, operating plant measurements or third-party proprietary models are shipped. The model is not a validated failure detector. The historical paceval paper illustrates Julia dynamic tracking; this research uses a compatible but independent miniature Python tracer and a C++ graph generator. A flattened expression is mathematically equivalent for this specific supported MLP, not for arbitrary convolutional or dynamic neural architectures.')
head('Selected references')
para('[1] paceval. <i>Conversion of neural networks to closed-form expressions as human-readable mathematical functions.</i> Original user-supplied research paper (2015–2023), pp. 6–11. https://github.com/paceval/paceval/tree/main/paceval%20and%20artificial%20intelligence','small')
para('[2] Lessmeier et al. Paderborn University Bearing DataCenter. Vibration and motor-current research data, CC BY-NC 4.0. https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter','small')
para('[3] Goodarzi, Schütze and Schneider (2025). Domain shifts in industrial condition monitoring: a comparative analysis of automated machine learning models. J. Sens. Sens. Syst. 14, 119–132. https://doi.org/10.5194/jsss-14-119-2025','small')
para('[4] paceval C/C++ API and computation-handle documentation. https://paceval.com/api/','small')
para('[5] Earlier paceval research: <i>From Neural Networks to Reusable Mathematical Execution Graphs</i>, user-supplied research report, 13 November 2026.','small')
# p13 short scientific discussion and conclusions
page('12. Interpretation and conclusions')
para('The integrated research demonstrator verifies a technically important proposition: <b>an already trained compact sigmoid network and its surrounding mathematical decision functions can be represented as persistent, reusable mathematical graphs executed by the original paceval engine</b>. Training artifacts are separate from inference; each model revision has stable numerical weights, and every mathematical component is recorded in an execution inventory.')
head('What was demonstrated')
bullet('Working original paceval C++ API, reusable expression handles, multi-calculation and multi-graph evaluation, two frozen trained network revisions, neural layer boundaries and flattened export.')
bullet('Reproducible normalization, output scoring, margins, shifted-feature descriptors and analytical score sensitivities as actual paceval graphs.')
bullet('Independent parity against native C++, a RecordFormula-inspired operator trace and high-precision reference computations.')
head('What is not yet demonstrated')
bullet('A real rolling-bearing failure classifier validated on an industrial test set, calibrated risk probability, or approved safety function.')
bullet('A field-validated predictive maintenance system using recorded data from physical bearings under changing operational conditions.')
bullet('A general Julia/Flux or ONNX-to-paceval converter, formally certified numerical bounds, or a completed FPGA/ASIC execution prototype.')
gap(16)
para('<b>Scientific conclusion:</b> The original formula-export proposal is strengthened by a controlled trained-model example and independently validated inference. The most promising follow-up is a verified conversion pipeline for permitted real industrial data, followed by rigorous functional and numerical tests across model revisions and operating conditions.')
footer()
print('Saved',out,'pages',N,'bytes',out.stat().st_size)
