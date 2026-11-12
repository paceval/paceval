"""Generate a fixed-layout, publication-style PDF from verified WP032 files.
Scientific plots are generated separately by make_figures.py from paceval outputs.
"""
import csv,json, re
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'paceval_ECG_Feature_Rule_Evaluation_Whitepaper_EN.pdf'
WIDTH,HEIGHT=595.28,841.89
NAVY=HexColor('#15344F');TEAL=HexColor('#168C9B');INK=HexColor('#243443');GRAY=HexColor('#566778');LIGHT=HexColor('#EEF5F7')
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',font));pdfmetrics.registerFont(TTFont('DVB',bold))
styles={
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.0,leading=14.7,textColor=INK,spaceAfter=4),
 'small':ParagraphStyle('small',fontName='DV',fontSize=8,leading=12.6,textColor=INK),
 'caption':ParagraphStyle('caption',fontName='DV',fontSize=7.4,leading=10.8,textColor=GRAY),
 'bullet':ParagraphStyle('bullet',fontName='DV',fontSize=8.6,leading=13.4,textColor=INK),
}
c=canvas.Canvas(str(OUTPUT),pagesize=(WIDTH,HEIGHT),pageCompression=1)
c.setTitle('WP032 - ECG Feature and Rule Evaluation | paceval Research')
page=0

def footer():
 c.setStrokeColor(HexColor('#D6E2E7'));c.line(45,45,550,45)
 c.setFont('DV',7);c.setFillColor(GRAY);c.drawString(46,32,'paceval | research-grade mathematical execution | WP032 | November 2026')
 c.drawRightString(546,32,str(page))
def start(title=None,kicker=None):
 global page
 if page: c.showPage()
 page+=1
 c.setFillColor(NAVY);c.rect(0,HEIGHT-16,WIDTH,16,stroke=0,fill=1)
 c.setFillColor(TEAL);c.setFont('DVB',9);c.drawString(47,HEIGHT-42,kicker or 'PACEVAL  |  SCIENTIFIC RESEARCH DEMONSTRATOR')
 footer()
 if title:
  c.setFillColor(NAVY);c.setFont('DVB',16.5);c.drawString(46,HEIGHT-81,title)
  c.setStrokeColor(TEAL);c.setLineWidth(1.25);c.line(46,HEIGHT-92,550,HEIGHT-92)
 return HEIGHT-113

def para(text,y,size='body',indent=0):
 p=Paragraph(text,styles[size]);w=500-indent;_,h=p.wrap(w,800)
 p.drawOn(c,47+indent,y-h)
 if y-h<65:raise RuntimeError(f'page {page} overflow at {text[:30]}')
 return y-h-(10 if size=='body' else 7)
def section(text,y):
 c.setFillColor(TEAL);c.setFont('DVB',11.2);c.drawString(47,y-12,text)
 return y-25

def table(items,y,widths=(190,313),rowh=27):
 for i,(label,val) in enumerate(items):
  h=rowh if not isinstance(val,tuple) else val[1]
  c.setFillColor(LIGHT if i%2==0 else HexColor('#FFFFFF'));c.rect(47,y-h,503,h,fill=1,stroke=0)
  c.setFont('DVB',8.1);c.setFillColor(NAVY);c.drawString(57,y-h+9,str(label))
  c.setFont('DV',8.2);c.setFillColor(INK)
  s=val if isinstance(val,str) else val[0]
  if len(s)>63:
   y2=para(s,y-6,'small',indent=191)
  else:c.drawString(57+widths[0],y-h+9,str(s))
  y-=h
 return y-12

def fig(path,y,height=235,caption=''):
 from PIL import Image
 im=Image.open(ROOT/path)
 iw,ih=im.size
 w=min(492,height*iw/ih)
 h=w*ih/iw
 if h>height:h=height;w=h*iw/ih
 c.drawImage(ImageReader(im),47+(503-w)/2,y-h,width=w,height=h,mask='auto')
 y=y-h-11
 if caption:y=para(caption,y,'caption')
 return y-10

# PAGE 1
start()
c.setFillColor(NAVY);c.setFont('DVB',24);c.drawString(47,HEIGHT-105,'ECG Feature and Rule Evaluation')
c.setFillColor(GRAY);c.setFont('DV',11);c.drawString(47,HEIGHT-130,'Reusable mathematical ECG postprocessing with paceval')
c.drawImage(str(ROOT/'figures/00_ecg_hero.png'),47,HEIGHT-459,width=503,height=277,mask='auto')
y=HEIGHT-491
y=section('Research outcome',y)
y=para('An original paceval C++ integration evaluated <b>51 persistent mathematical graphs</b> over <b>10,000 deterministic synthetic feature records</b>, with independent native checks and a separately implemented 80-decimal-digit audit.',y)
y=table([('Execution graphs','50 distinct models + 1 immutable revision'),('Scalar evaluations','13,923'),('Batch comparisons','1,600'),('Independent high-precision checks','500 passed'),('Scientific figures','Eight result graphics from paceval-generated CSV')],y,rowh=25)
y=para('<b>Scope:</b> Non-clinical mathematical research; no patient recordings, diagnostic classification, clinical sensitivity/specificity, device validation or prospective evaluation.',y,'small')
# PAGE 2
y=start('1. Industrial context and research question')
y=para('Ambulatory ECG monitors, ECG interpretation pipelines and biomedical software work with characteristic waveform measurements such as successive RR intervals, QRS-complex duration and signal-amplitude features. A pipeline may compute these features first, then apply configurable scoring and review rules to previously measured values.',y)
y=section('Current state of the art',y)
y=para('Established ECG research uses annotated waveform corpora and standardized preprocessing. The PhysioNet MIT-BIH database provides 48 approximately half-hour, two-channel recordings, while PTB-XL contains 12-lead ECG recordings for research. The LUDB collection provides delineation annotations for 200 ten-second 12-lead recordings. These datasets support research but do not make arbitrary score coefficients medically meaningful.',y)
y=section('Industrial question',y)
y=para('Can a manufacturer or laboratory maintain multiple explicit feature-to-score rules as separately versioned mathematical formulas, evaluate them repeatedly on standardized feature vectors, and reproduce their output after formulas change?',y)
y=section('System boundary',y)
y=para('<b>Upstream host:</b> ECG acquisition, filtering, detection, beat delineation, extraction, normalization and data-governance policy. <b>paceval:</b> expression creation, persistent handles, scalar evaluation and independent-value-set batch evaluation. <b>Downstream host:</b> threshold flagging, storage and review workflow.',y)
y=para('<b>Important:</b> The research uses no real ECG waveforms and does not calculate clinically validated RR or QRS measurements. Its inputs have plausible illustrative units but fully synthetic values.',y)
# PAGE3
y=start('2. Defined mathematical feature model')
y=para('The illustrative source expression in WP032 is score = a RRmean + b RRstd + c QRS_width. This implementation extends that concept to normalized features so all sums and nonlinear terms are dimensionless.',y)
y=table([('r','(RRmean - 800 ms) / 100 ms'),('d','(RRstd - 15 ms) / 20 ms'),('q','(QRSwidth - 90 ms) / 15 ms'),('a','(Amplitude - 1 mV) / 0.2 mV')],y,rowh=28)
y=section('Five score families',y)
y=para('Every family contains ten distinct alpha/beta coefficient settings (50 separate expression strings):',y)
for line in [
 'F1 Linear: z = alpha*r + beta*d + 0.36*q + 0.12*a',
 'F2 Interaction: z = alpha*r*d + beta*q*a + 0.19*d',
 'F3 Quadratic: z = alpha*r^2 + beta*d^2 + 0.22*q^2 - 0.3',
 'F4 Periodic: z = alpha*sin(r) + beta*cos(q) + 0.17*d*a',
 'F5 Log-exp: z = alpha*ln(1+r^2) + beta*exp(-d^2) + 0.18*q*a',
 ]:y=para(line,y,'small')
y=section('Common nonlinear transform',y)
y=para('<b>score = 1 / (1 + exp(-z))</b>. This bounds the score between zero and one but does <b>not</b> convert it into a calibrated probability of arrhythmia or any other medical condition.',y)
y=para('Coefficients: alpha = 0.28 + 0.048 j + 0.015 f; beta = 0.16 + 0.032 j, with family f = 0..4 and variant j = 0..9. The version-2 copy of model 1 increases alpha by 0.09 without changing model 1.',y,'small')
# PAGE4
y=start('3. paceval execution architecture')
y=section('Verified API boundary',y)
y=para('The C++ executable compiles the supplied original <b>paceval_main.cpp</b>, includes <b>paceval_main.h</b>, and links against a compatible external Linux paceval 4.25 runtime. The shared library is intentionally not part of the public ZIP.',y)
y=table([('Initialization','paceval_InitializeLibrary'),('Expression compilation','paceval_CreateComputation'),('Scalar computation','paceval_dGetComputationResult'),('Multi-input batch','paceval_dGetComputationResultExt'),('Error inspection','paceval_GetIsError and per-batch error codes'),('Cleanup','paceval_DeleteComputation; paceval_FreeLibrary')],y,rowh=29)
y=section('Controlled versioning and feature flow',y)
y=para('Fifty formula handles are created at startup and reused with changed feature inputs. A revised model creates a 51st handle; the original remains callable and yields its original values. The C++ host handles feature unit conversion, validity checks, deterministic test generation and review thresholding.',y)
y=section('Batch and scalar comparison',y)
y=para('Each of the 50 graph handles was evaluated on 32 independent deterministic feature vectors using the official batch API; 1,600 batch values were checked by a separately coded C++ mathematical reference.',y)
y=para('This experiment tests reusable expression execution, not integrated ECG acquisition, real-time latency, diagnostic classification or medical-device qualification.',y)
# PAGE5
y=start('4. Deterministic workload and completed checks')
y=para('A seeded xorshift64* generator produces 10,000 synthetic feature inputs. Family assignment cycles through all 50 formulas. Every output is independently evaluated in native C++ using identical mathematical meaning. Separately, 500 exported cases were checked using 80-digit mpmath operations.',y)
y=table([('Seed','20261112'),('Synthetic replay feature records','10,000'),('Persistent formula handles','51'),('Scalar evaluations','13,923'),('Independent batch checks','1,600'),('High-precision spot checks','500 / 500 passed'),('CMake and CTest','1 / 1 passed')],y,rowh=29)
y=section('Non-clinical review policy',y)
y=para('The demonstration host flags a score if it is at least 0.65. In this fixed synthetic workload, 1,658 records meet that policy. The number is a deterministic demonstration result, not a false-alarm rate, patient-risk estimate or clinical screening performance metric.',y)
y=section('Validation artifacts',y)
y=para('The full numerical comparison remains in <b>results/</b> technical logs and high-precision audit JSON. The public result figures and discussion focus on computed feature scores, version changes and the effect of rule selection rather than numerical deviations between C++ and paceval.',y)
# PAGE6
y=start('5. Feature-score replay and family behaviour')
y=fig('figures/01_feature_replay.png',y,230,'Figure 1. The first 600 paceval-derived score values; the dashed threshold is a deliberately synthetic review policy.')
y=fig('figures/03_rule_families.png',y,229,'Figure 2. Score distributions by expression family over the synthetic replay. The differences reflect formula design, not diagnostic merit.')
# PAGE7
y=start('6. Feature score response surfaces')
y=fig('figures/04_score_surface_3d.png',y,300,'Figure 3. An actual 61 x 61 paceval-evaluated score surface at fixed dispersion and amplitude features.')
y=fig('figures/05_score_contours.png',y,278,'Figure 4. Contours of the same 3,721 score evaluations, showing sensitivity to the normalized RR-mean and QRS-width inputs.')
# PAGE8
y=start('7. Versioning and review-rule sensitivity')
y=fig('figures/06_formula_versions.png',y,175,'Figure 5. Both formula versions remain simultaneously callable using separate persistent handles.')
y=fig('figures/08_threshold_sweep.png',y,175,'Figure 6. The number of synthetic records flagged varies with the host-chosen review threshold; no clinical operating point is claimed.')
y=fig('figures/07_rule_flags.png',y,145,'Figure 7. Fixed replay summary under the illustrative 0.65 research threshold.')
# PAGE9
y=start('8. Interpretation, limitations and next stage')
y=fig('figures/02_score_distribution.png',y,227,'Figure 8. Computed score frequencies across the 10,000 synthetic, non-patient feature vectors.')
y=section('What has been demonstrated',y)
y=para('The defined mathematical features-to-score pipeline can use reusable paceval computation handles, multiple distinct formula families, batch evaluation, and controlled model revision. Numerical output passed the separately implemented reference checks for this deterministic workload.',y)
y=section('What has not been demonstrated',y)
y=para('The demonstration has no empirical ECG waveform processing, validated beat detection, expert-labeled evaluation, patient stratification, external validation cohort, calibrated clinical risk probabilities, diagnostic sensitivity or specificity, prospective study, or medical-device clearance.',y)
y=section('Meaningful future experiment',y)
y=para('With appropriate permissions and license review, an independent host could extract fixed, audited RR and QRS features from PhysioNet records, preserve record-level train/test splits, and compare only reproducible mathematical postprocessing. Any diagnostic study would require a clinical protocol and separate validation.',y)
# PAGE10
y=start('9. Reproducibility, sources and conclusions')
y=section('Rebuild and run',y)
for line in [
 'cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/abs/path/libpaceval.so',
 'cmake --build build -j',
 'ctest --test-dir build --output-on-failure',
 './build/ecg_rules --records 10000 --out examples',
 'python3 src/high_precision_reference.py examples',
 'python3 src/make_figures.py ; python3 src/make_whitepaper.py',
 'python3 src/check_readme_math.py',
 ]:y=para(line.replace('&','&amp;'),y,'small')
y=section('Primary data files',y)
y=para('examples/feature_replay.csv; examples/formula_registry.csv; examples/ecg_score_surface.csv; examples/formula_version_surface.csv; examples/execution_summary.txt. Technical audits are in results/. All eight scientific figures are regenerated from those actual paceval-exported CSV values.',y)
y=section('Scientific and technical sources',y)
for line in [
 'PhysioNet, MIT-BIH Arrhythmia Database (v1.0.0): https://physionet.org/content/mitdb/1.0.0/',
 'PhysioNet, PTB-XL ECG Database: https://physionet.org/content/ptb-xl/',
 'PhysioNet, LUDB ECG delineation data: https://physionet.org/content/ludb/1.0.1/',
 'paceval Mathematical Engine C/C++ API v4.25: https://paceval.com/api/',
 ]:y=para(line,y,'small')
y=section('Conclusion',y)
y=para('The research establishes a reproducible and independently checked mathematical execution demonstrator for configurable ECG-feature rules. It is a non-clinical software-engineering feasibility study, not evidence of ECG diagnostic performance or clinical safety.',y)
c.save()
print('Created',OUTPUT,'pages=',page)
