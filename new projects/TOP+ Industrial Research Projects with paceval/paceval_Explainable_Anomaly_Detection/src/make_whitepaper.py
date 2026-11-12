#!/usr/bin/env python3
"""Publish the reproducible scientific report from checked project artifacts.
Uses ReportLab and embeds illustrations only from this local GitHub project.
"""
from pathlib import Path
import json, csv, math
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'paceval_Explainable_Anomaly_Detection_Whitepaper_EN.pdf'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',FONT));pdfmetrics.registerFont(TTFont('DejaVuBold',FONT_B))
NAVY=colors.HexColor('#153347'); TEAL=colors.HexColor('#0B8797'); LIGHT=colors.HexColor('#EAF5F7'); MUTED=colors.HexColor('#496578')
styles={}
styles['title']=ParagraphStyle('MyTitle',fontName='DejaVuBold',fontSize=22,leading=29,textColor=NAVY,spaceAfter=12)
styles['subtitle']=ParagraphStyle('MySubtitle',fontName='DejaVu',fontSize=11,leading=17,textColor=MUTED,spaceAfter=12)
styles['h1']=ParagraphStyle('MyH1',fontName='DejaVuBold',fontSize=15.3,leading=21,textColor=NAVY,spaceBefore=10,spaceAfter=10)
styles['h2']=ParagraphStyle('MyH2',fontName='DejaVuBold',fontSize=11,leading=15,textColor=TEAL,spaceBefore=9,spaceAfter=7)
styles['body']=ParagraphStyle('MyBody',fontName='DejaVu',fontSize=8.8,leading=13.3,spaceAfter=8,textColor=NAVY)
styles['small']=ParagraphStyle('MySmall',fontName='DejaVu',fontSize=8,leading=11.4,spaceAfter=7,textColor=MUTED)
styles['caption']=ParagraphStyle('MyCaption',fontName='DejaVu',fontSize=8,leading=11.3,spaceBefore=3,spaceAfter=10,textColor=MUTED)
styles['table']=ParagraphStyle('MyTable',fontName='DejaVu',fontSize=7.3,leading=10.5,textColor=NAVY)
styles['bold']=ParagraphStyle('MyTableBold',fontName='DejaVuBold',fontSize=7.3,leading=10.4,textColor=NAVY)
styles['code']=ParagraphStyle('MyCode',fontName='DejaVu',fontSize=8.5,leading=13,textColor=NAVY,spaceBefore=6,spaceAfter=9,backColor=LIGHT,borderPadding=7)

def P(s,sty='body'):return Paragraph(s,styles[sty])
def H(s):return P(s,'h1')
def SH(s):return P(s,'h2')
def IMG(name,caption,maxw=498,maxh=255):
    from PIL import Image as PILImage
    file=ROOT/'figures'/name
    im=PILImage.open(file);w,h=im.size;scale=min(maxw/w,maxh/h)
    image=Image(str(file),width=w*scale,height=h*scale)
    image.hAlign='CENTER'
    return [image,P(caption,'caption')]
def T(data,widths=None):
    cells=[[P(str(x),'bold' if i==0 else 'table') for i,x in enumerate(row)] for row in data]
    tb=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1)
    tb.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),LIGHT),('BOTTOMPADDING',(0,0),(-1,0),8),('TOPPADDING',(0,0),(-1,0),8),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F5F9FA')]),
        ('LINEBELOW',(0,0),(-1,0),.7,TEAL),('BOTTOMPADDING',(0,1),(-1,-1),6),('TOPPADDING',(0,1),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8)]))
    return tb

def headfooter(canvas,doc):
    canvas.saveState();w,h=A4
    canvas.setStrokeColor(TEAL);canvas.setLineWidth(.6)
    canvas.line(18*mm,h-17*mm,w-18*mm,h-17*mm)
    canvas.setFont('DejaVuBold',8);canvas.setFillColor(TEAL)
    canvas.drawString(18*mm,h-14*mm,'paceval.  /  RESEARCH DEMONSTRATOR  /  WP-017')
    canvas.line(18*mm,16*mm,w-18*mm,16*mm)
    canvas.setFont('DejaVu',7);canvas.setFillColor(MUTED)
    canvas.drawString(18*mm,12*mm,'Explainable Formula-Based Anomaly Detection  •  12 Nov 2026')
    canvas.drawRightString(w-18*mm,12*mm,str(doc.page))
    canvas.restoreState()

def csvrows(name):
 with open(ROOT/'examples'/name,encoding='utf8',newline='') as f:return list(csv.DictReader(f))

def report():
 val=json.loads((ROOT/'examples/validation.json').read_text());audit=json.loads((ROOT/'examples/independent_audit.json').read_text())
 sel=csvrows('selection.csv');events=[r for r in csvrows('event_detection.csv') if r['split']=='test']; delays=[int(r['delay_samples']) for r in events]
 pagew=A4[0]-36*mm
 doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=21*mm,bottomMargin=21*mm,title='paceval – Explainable Formula-Based Anomaly Detection',author='paceval research demonstrator',subject='WP-017 independent offline numerical reproducibility study')
 S=[]
 # Page 1
 S += [Spacer(1,14),P('Explainable Formula-Based<br/>Anomaly Detection','title'),P('Versioned industrial sensor scoring with reusable paceval computation graphs, interpretable contributions and independently audited results.','subtitle')]
 S += IMG('00_anomaly_detection_hero.png','Cover illustration: industrial sensor monitoring and an example anomaly formula. Decorative data on the cover are not research measurements.',maxw=pagew,maxh=260)
 S += [SH('Experimental result at a glance'),T([['Quantity','Verified observation'],['Mathematical workload','100 individual score graphs × 4,080 valid sensor samples = 408,000 results'],['Independent verification','Native C++ reference on all scores; 110-digit independent audit on 200 pairs and 4,080 selected scores'],['Event outcomes','8/8 held-out synthetic fault events detected (persistence-based alarm path)'],['Interval diagnostic','24/24 raw TINC samples enclose the exact dyadic reference for the separately tested smooth polynomial']],widths=[125,374]),Spacer(1,8),P('Scientific scope: controlled synthetic, labeled signals; mathematical correctness and traceability are validated. This work does not establish real-world detector effectiveness, realtime operation or safety certification.','small'),PageBreak()]
 # Page 2
 S += [H('1. Research question and executable architecture'),P('WP-017 originally proposed a reusable arithmetic kernel for industrial anomaly scoring. This paper reports a direct experimental implementation, preserving the separation between numerical graph execution, signal metadata, stateful alarm logic and statistical assessment.'),P('The official paceval SDK sources are compiled into the executable and a separately supplied original x86-64 Linux runtime is loaded at execution. Every score uses a paceval computation object. C++ supplies strict data-quality checks, stable model IDs, batched input preparation and a deterministic offline monitoring policy.')]
 S += IMG('02_execution_architecture.png','Figure 1. Strict input-quality gating precedes paceval; interpretation, alarm state and audit remain distinct host responsibilities.',maxw=pagew,maxh=230)
 S += [SH('The mathematical kernel'),P('Define z=(x−μ)/(σ+ε), d=Δx/(dscale+ε), and cn=c/(cscale+ε). These are dimensionless normalization ratios. For each versioned rule, the anomaly score is the sum of three nonnegative terms: a deviation contribution, a change contribution, and a context contribution.'),T([['Family','Deviation contribution','Change contribution','Context contribution'],['0','w0 × |z|','w1 × |d|','w2 × |cn|'],['1','w0 × |z|','w1 × d²','w2 × |cn|'],['2','w0 × z²','w1 × |d|','w2 × |cn|'],['3','w0 × |z|','w1 × |d|','w2 × cn²']],widths=[65,142,139,153]),P('The 100 frozen rules each encode their own coefficients and threshold, while 12 shared paceval graphs separately reproduce the three score components for the selected rules. A new rule version can be compiled without modifying the existing 99 rule definitions.','small'),PageBreak()]
 # Page 3
 S += [H('2. Data generation, labels and quality control'),P('Sixteen independent synthetic channels are divided into four instrument classes (temperature, vibration, pressure and electrical monitoring). Four channels represent each class. Channels are split by fixed identity into two training, one validation and one held-out test stream per class. No customer or real plant measurements are present.')]
 S += IMG('01_sensor_events.png','Figure 2. Known injected events: a 7-sample spike and a 24-sample progressive drift in a deterministic 256-minute series.',maxw=pagew,maxh=227)
 S += [P('Every channel has 256 one-minute samples. Known anomalous windows are t=70–76 and t=160–183, determined before scoring. Native labels come from the generator; paceval has no access to labels and does not itself perform statistical classification.'),SH('Handling incomplete industrial inputs')]
 S += IMG('10_quality_gating.png','Figure 3. Sixteen missing, stale or bad-quality records are excluded before paceval evaluation.',maxw=pagew,maxh=190)
 S += [P('The strict CSV reader also rejects wrong field counts, non-finite values, invalid normalizations, duplicate timestamps and modifications of the frozen train/validation/test split. The design follows the OPC UA principle of evaluating source timestamps and measurement quality before using measured values.','small'),PageBreak()]
 # Page 4
 S += [H('3. Explainability and controlled formula revisions'),P('A mathematical score is not described as an unexplainable black box. The published selected_scores.csv file records the deviation, change and context contributions produced by paceval, along with the total score, exact rule ID, rule threshold, truth label and alarm state. A strict sum check prevents contributions from silently drifting away from the actual scoring computation.')]
 S += IMG('03_explainable_components.png','Figure 4. Decomposition of a selected score around a known synthetic spike; all displayed components are evaluated by reusable paceval graphs.',maxw=pagew,maxh=220)
 S += [P('Revision handling is intentionally controlled: rule 17 is recompiled with an updated deviation coefficient; its old result is still auditable. The 99 other score handles remain available and unchanged. Revision does not imply that the altered rule improves anomaly detection or was chosen for deployment.')]
 S += IMG('07_model_version_update.png','Figure 5. Change comparison of original rule 17 and its deliberately modified second version.',maxw=pagew,maxh=205)
 S += [PageBreak()]
 # Page 5
 S += [H('4. Frozen candidate selection and held-out evaluation'),P('Every family has 25 independently versioned formula candidates. Only labeled validation streams determine the winning rule in each class; the tie-breaker favors fewer false positives. The withheld test streams are then reported without further tuning. C++ verifies the expected F1 computations independently of the paceval arithmetic.')]
 S += IMG('05_candidate_score_map.png','Figure 6. Variation in validation F1 across 100 predeclared formula versions.',maxw=pagew,maxh=208)
 S += IMG('04_holdout_f1.png','Figure 7. Validation versus independently held-out pointwise F1 for the four selected model families.',maxw=pagew,maxh=208)
 S += [P('Raw threshold classification on the selected rules produced 100 true positives, 0 false positives and 24 false negatives on the held-out sample-level labels. These counts do not include the additional stateful-alarm persistence behavior. Because synthetic anomaly patterns are known and simple, these numbers are not general predictive-performance estimates.','small'),PageBreak()]
 # Page 6
 S += [H('5. Alarm persistence, event recall and detection delay'),P('A positive alarm state starts after two successive above-threshold scores and clears after two successive below-70%-threshold readings. Bad-quality input resets the alarm state. The evaluation explicitly distinguishes pointwise rule scores, positive alarm states, and event-level detection. Persistence can extend an alarm after the end of an event.')]
 S += IMG('06_event_detection_delays.png','Figure 8. First detection time after each of the eight independently held-out synthetic event onsets.',maxw=pagew,maxh=248)
 S += [T([['Outcome','Held-out synthetic result'],['Injected fault events','8 = 4 channels × (1 spike + 1 drift)'],['Detected fault events','8/8'],['Detection-delay range','1–12 one-minute samples'],['Raw threshold false positives','0 on the held-out samples'],['Persistent state false-positive samples','10 on held-out samples (post-event persistence)']],widths=[199,300]),Spacer(1,10),P('The event-level observation does not establish performance at other anomaly prevalence levels, operational regimes or real physical failure mechanisms. It is nonetheless a reproducible way to distinguish mathematics, stateful policy and detection assessment.','small'),PageBreak()]
 # Page 7
 S += [H('6. Independent numerical validation and interval observation'),P(f"The original paceval runtime performed {val['evaluated_score_count']:,} score evaluations. The largest native C++ absolute score difference was {val['native_max_absolute_difference']:.3e}. A separate 110-digit Decimal reference, reconstructing exact binary64 inputs with Decimal.from_float, verified {audit['independent_score_samples']} selected score/rule pairs and all {audit['selected_score_and_explanation_samples']:,} reported selected scores and their explanation components. The maximum high-precision difference for the selected 200 score samples was approximately 1.22 × 10⁻¹⁵.")]
 S += IMG('08_numerical_accuracy.png','Figure 9. Absolute residuals for 200 independently chosen, high-precision-recomputed rule/sample combinations.',maxw=pagew,maxh=204)
 S += IMG('09_tinc_control.png','Figure 10. Separate 24-sample interval diagnostic using x² + 1 on exactly representable dyadic inputs.',maxw=pagew,maxh=204)
 S += [P('All 24 original TINC intervals contain their separate exact reference value for this smooth dyadic control expression. This observation is not a formal proof of outward rounding or a global enclosure claim for nonsmooth scores containing |·|. No post-hoc widening of the raw reported intervals was applied.','small'),PageBreak()]
 # Page 8
 S += [H('7. Reproducible implementation and tested environment'),P('The executable is written in C++17 with CMake. The two original paceval SDK sources live in src/, not in a separate library folder. The externally supplied shared library remains an explicit deployment dependency. The official source notices are retained. No extra license-notice file is created.')]
 S += [T([['Actual SDK function','Purpose in this demonstrator'],['paceval_InitializeLibrary','Initialize original Linux runtime'],['paceval_CreateComputation','Build 100 versioned score graphs, 12 explanation graphs, one TINC graph'],['paceval_dGetMultipleComputationsResultsExt','Evaluate many computation handles over a batch of sensor parameter rows'],['paceval_dGetComputationResult','Evaluate changed rule and independent TINC diagnostic'],['paceval_GetIsError / paceval_GetErrorInformation','Check computation/compile failures'],['paceval_DeleteComputation / paceval_FreeLibrary','Release original objects and runtime']],widths=[225,274]),Spacer(1,13),SH('Tested setup'),P('Debian GNU/Linux 13 (trixie), x86-64, AMD EPYC 9V74 virtualized processor, 5 logical CPUs visible in this environment, GCC 14.2 and Clang 17. Original separately supplied paceval Linux shared object. AddressSanitizer and UndefinedBehaviorSanitizer were also exercised. These environment details describe the validation platform and are not throughput claims.')]
 S += [SH('Reproduction commands'),P('1. cmake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/original_paceval.so','code'),P('2. cmake --build build --parallel; ctest --test-dir build --output-on-failure','code'),P('3. ./build/anomaly_detection --out regenerated --batch 37','code'),P('4. python3 src/validate_outputs.py --examples regenerated','code'),P('5. python3 src/make_figures.py','code'),P('The source tests include a byte-identical CSV replay, explicit malformed-input cases and an independent high-precision reference. See README.md and examples/validation.json for all exact paths.','small'),PageBreak()]
 # Page 9
 S += [H('8. Scientific interpretation and future research'),P('This is a finished, reproducible synthetic feasibility study rather than a deployment claim. It establishes that a family of versioned anomaly formulas can be executed by persistent paceval computation objects and that their component attribution is independently auditable. The host rather than paceval owns data validity, anomaly-label construction, model-selection discipline, hysteresis, event scoring, and safety-related decisions.')]
 S += [SH('What remains to be validated'),P('The Numenta Anomaly Benchmark highlights detection delay and false-alarm costs in time-series monitoring. A meaningful deployment study should therefore evaluate archived, independently labeled industrial fault streams and measure event detection under varying regimes, sensor drift, class prevalence and operationally specified false-alarm costs. The current synthetic thresholds and reference baselines have not been shown to transfer to a physical plant.')]
 S += [P('Operational extensions include native OPC UA ingestion with verified source timestamps and quality bits, external validated rule registries, real streaming p99 latency measurements, forensic audit-log retention and model governance. A kernel timing observation alone would not establish a valid anomaly detector.')]
 S += [SH('Selected external references'),P('1. paceval API, C/C++ execution objects and batch evaluation: https://paceval.com/api/','small'),P('2. Numenta Anomaly Benchmark, v1.1, open benchmark corpus and scoring protocol: https://github.com/numenta/NAB','small'),P('3. Ahmad et al., Evaluating Real-Time Anomaly Detection Algorithms, ICMLA 2015: https://doi.org/10.1109/ICMLA.2015.141','small'),P('4. OPC Foundation, OPC UA Part 4, DataValue and SourceTimestamp specification: https://reference.opcfoundation.org/specs/OPC-10000-4/7.11','small'),P('5. paceval C/C++ sources and release information: https://github.com/paceval/paceval','small')]
 S += [SH('Publication artifacts'),P('The whitepaper is distributed together with README.md, src/anomaly_detection.cpp, src/paceval_main.h, src/paceval_main.cpp, src/validate_outputs.py, examples/selected_scores.csv, examples/event_detection.csv, examples/validation.json, examples/independent_audit.json and figures/01–10. All data in this demonstration are synthetic and generated deterministically by the published source code.')]
 S += [P('Conclusion: a reusable and explainable anomaly-score mathematical execution layer was successfully demonstrated with paceval and independently validated on a defined offline workload. The actual detection outcomes should be interpreted only within that workload.','body')]
 doc.build(S,onFirstPage=headfooter,onLaterPages=headfooter)
 print('Whitepaper created:',OUT)
if __name__=='__main__':report()
