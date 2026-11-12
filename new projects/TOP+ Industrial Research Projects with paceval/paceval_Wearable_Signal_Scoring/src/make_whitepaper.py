#!/usr/bin/env python3
"""Build the English WP_036 scientific report from executed paceval data and original figures."""
import csv,math
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paceval_Wearable_Signal_Scoring_Whitepaper_EN.pdf'
W,H=595.28,841.89
NAVY=HexColor('#17354D');TEAL=HexColor('#087E8B');INK=HexColor('#243847');GRAY=HexColor('#596C77');LIGHT=HexColor('#EDF4F5');CORAL=HexColor('#DE5D49')
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('WP36',font));pdfmetrics.registerFont(TTFont('WP36B',bold))
styles={
 'body':ParagraphStyle('body',fontName='WP36',fontSize=8.85,leading=14.0,textColor=INK,spaceAfter=0),
 'small':ParagraphStyle('small',fontName='WP36',fontSize=7.75,leading=11.8,textColor=INK,spaceAfter=0),
 'caption':ParagraphStyle('caption',fontName='WP36',fontSize=7.4,leading=10.8,textColor=GRAY,spaceAfter=0),
 'lead':ParagraphStyle('lead',fontName='WP36',fontSize=10.8,leading=16.0,textColor=INK,spaceAfter=0)
}
c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
c.setTitle('WP036 - Wearable Signal Scoring Expressions with paceval')
c.setAuthor('paceval mathematical research demonstrator')
page=0

def footer():
 c.setStrokeColor(HexColor('#CADADF'));c.line(46,45,W-46,45)
 c.setFont('WP36',7);c.setFillColor(GRAY);c.drawString(47,31,'paceval | wearable mathematical scoring research | November 2026');c.drawRightString(W-47,31,str(page))
def begin(title='',kicker='PACEVAL | SCIENTIFIC RESEARCH DEMONSTRATOR'):
 global page
 if page:c.showPage()
 page+=1
 c.setFillColor(NAVY);c.rect(0,H-14,W,14,stroke=0,fill=1)
 c.setFont('WP36B',8);c.setFillColor(TEAL);c.drawString(47,H-42,kicker)
 footer()
 if title:
  c.setFont('WP36B',15.7);c.setFillColor(NAVY);c.drawString(46,H-79,title)
  c.setStrokeColor(TEAL);c.setLineWidth(1.2);c.line(46,H-90,548,H-90)
 return H-108

def text(s,y,kind='body',after=11,indent=0):
 p=Paragraph(s,styles[kind]);ww=501-indent;_,hh=p.wrap(ww,700)
 if y-hh<66:raise ValueError(f'page {page} overflow: {s[:65]} y={y} h={hh}')
 p.drawOn(c,47+indent,y-hh)
 return y-hh-after

def sect(s,y):
 if y<92:raise ValueError(f'page {page} section cannot fit')
 c.setFont('WP36B',10.5);c.setFillColor(TEAL);c.drawString(47,y-12,s)
 return y-27

def table(items,y,h=27):
 for k,(label,value) in enumerate(items):
  if y-h<68:raise ValueError(f'page {page} table overflow')
  c.setFillColor(LIGHT if k%2==0 else HexColor('#FFFFFF'));c.rect(47,y-h,501,h,stroke=0,fill=1)
  c.setFillColor(NAVY);c.setFont('WP36B',7.9);c.drawString(56,y-h+9,label)
  p=Paragraph(str(value),styles['small']);_,ph=p.wrap(295,h+2)
  if ph>h-4:raise ValueError('table value too tall: '+str(value))
  p.drawOn(c,250,y-(h+ph)/2)
  y-=h
 return y-13

def fig(stem,y,maxheight=230,caption=''):
 p=ROOT/'figures'/f'{stem}.png';im=Image.open(p); iw,ih=im.size
 ww=min(499,maxheight*iw/ih);hh=ww*ih/iw
 if hh>maxheight: hh=maxheight;ww=hh*iw/ih
 if y-hh-47<55:raise ValueError(f'figure overflow page={page}, fig={stem}, available={y}')
 c.drawImage(ImageReader(im),47+(501-ww)/2,y-hh,width=ww,height=hh,mask='auto')
 y-=hh+7
 if caption:y=text(caption,y,'caption',after=10)
 return y-6

def eq(s,y,size=11.0):
 """Render scientific equations using mathtext rather than raw LaTeX PDF strings."""
 fig0=plt.figure(figsize=(9,0.55));fig0.patch.set_alpha(0)
 fig0.text(.01,.4,'$'+s+'$',fontsize=size,color='#17354d')
 import io
 b=io.BytesIO();fig0.savefig(b,format='png',dpi=260,transparent=True,bbox_inches='tight',pad_inches=.06);plt.close(fig0);b.seek(0)
 image=Image.open(b);iw,ih=image.size;wid=min(465.,max(140.,iw/260*72*1.15));ht=wid*ih/iw
 if y-ht<75:raise ValueError('equation overflow')
 b.seek(0);c.drawImage(ImageReader(b),62,y-ht,width=wid,height=ht,mask='auto');return y-ht-14

# 1 - cover
begin()
c.setFillColor(NAVY);c.setFont('WP36B',23);c.drawString(47,H-101,'Wearable Signal Scoring')
c.drawString(47,H-129,'Expressions with paceval')
c.setFont('WP36',10.1);c.setFillColor(GRAY);c.drawString(47,H-149,'Industrial IMU / PPG feature processing and versioned mathematical scores')
# original 2:1 illustration: 501 x 250.5 on A4
hero=ROOT/'figures'/'00_wearable_signals_hero.png';c.drawImage(str(hero),47,H-420,width=501,height=250.5,mask='auto')
y=H-438
y=text('Concept illustration, not a computed scientific result. All scientific result figures use actual paceval output.',y,'caption',after=17)
y=sect('Executed research outcome',y)
y=text('An original paceval C++ integration evaluated <b>51 persistent mathematical graphs</b> using features from <b>10,000 deterministic synthetic IMU/PPG windows</b>. All 50 scoring formulas, plus one revision, were compiled into reusable paceval handles and independently checked.',y)
y=table([('Synthetic windows','10,000 windows; 2,000,000 raw timestamps'),('Mathematical execution','13,923 scalar values; 1,600 batch values'),('Independent high-precision check','500 selected scores passed 80-digit verification'),('Scientific visualizations','Eight charts based on recorded paceval outputs')],y,h=26)
y=text('<b>Scope:</b> Non-clinical research demonstration only. No real people, diagnostic alerts, regulated device claims or clinical efficacy results are part of this experiment.',y,'small')
#2
y=begin('1. Industrial use case and current state of the art')
y=text('A modern wrist-worn device often combines optical photoplethysmography (PPG) with an inertial measurement unit (IMU). The optical signal contains pulsatile modulation but can be corrupted by motion, device contact, environmental light and sensor characteristics. Movement and optical signals therefore need separate preprocessing before a configurable scoring stage.',y)
y=sect('Practical engineering workflow',y)
y=text('<b>Sensor acquisition</b> leads to short time windows; <b>host preprocessing</b> computes standardized optical and motion features; a <b>mathematical evaluation engine</b> assigns configurable scores; and a <b>host decision system</b> presents or stores the outputs. paceval is tested here only for the mathematical scoring engine.',y)
y=sect('Contemporary research and published resources',y)
y=text('A 2026 technical review summarizes wearable ECG/PPG fusion, motion artifacts and signal-quality indices [1]. A 2025 PPG signal-quality review and validation study examines motion-related uncertainty in optical cardiovascular monitoring [2]. PPG-DaLiA provides recorded motion and physiological data from 15 participants [3], while PhysioNet provides additional exercise-based PPG and motion records [4]. None of these real-world datasets is used as input in this demonstration.',y)
y=sect('Research question and contribution',y)
y=text('Can 50 mathematically different wearable feature-to-score rules be created once, evaluated repeatedly from fixed synthetic signals and revised without overwriting earlier expressions? The experiment verifies source-level reproducibility and the mathematics of an explicit postprocessing layer; it does not validate a pulse detector, clinical classifier, or embedded product.',y)
y=sect('Regulatory framing',y)
y=text('The FDA general-wellness guidance updated in January 2026 distinguishes certain low-risk wellness functions from disease-oriented medical-device purposes [5]. This prototype makes no health diagnosis, risk prediction, treatment or clearance claim.',y)
#3
y=begin('2. Defined synthetic signals and preprocessing')
y=text('Every synthetic window spans <b>8 seconds at 25 Hz (200 sample times)</b>. A deterministic C++ generator combines a periodic optical component with motion-dependent contamination and three-axis acceleration around a constant gravity term. An independent host procedure extracts six window-level features.',y)
y=sect('Raw signal construction and physical assumptions',y)
y=text('The PPG channel is a normalized optical proxy, not an optical measurement in volts or an actual arterial waveform. Acceleration channels are normalized in units of g. Fixed seeds and bounded rates allow each window to be reconstructed. The generated pulse oscillation and movement cadence are not observed clinical measurements.',y)
y=eq(r'A_{\mathrm{RMS}}=\sqrt{\frac{1}{N}\sum_{i=1}^{N}(a_{x,i}^{2}+a_{y,i}^{2}+(a_{z,i}-1)^{2})}',y,11)
y=text('Here N = 200. The host additionally counts upward acceleration zero crossings as a cadence proxy and searches positive optical autocorrelation peaks at lags 12 through 38. The selected lag provides an illustrative pulse-frequency proxy; this is not a validated estimation algorithm.',y)
y=sect('Six dimensionless features supplied to paceval',y)
y=table([('a','Acceleration RMS divided by 0.65 g'),('c','Cadence proxy divided by 145 events per minute'),('h','Autocorrelation pulse proxy divided by 140 bpm'),('m','Motion artifact proxy divided by 0.65'),('p','PPG standard deviation / mean, divided by 0.12'),('q','Normalized optical autocorrelation peak, clipped to [0,1]')],y,h=28)
y=text('An input contract rejects nonfinite values and values outside the demonstration feature domain. The physical and statistical meaning of these normalization constants is intentionally limited to this synthetic workload.',y,'small')
#4
y=begin('3. Mathematical scoring functions')
y=text('Every score is a monotone nonlinear transformation of a dimensionless model expression. Five formula families each use ten distinct coefficient pairs, creating 50 immutable formula descriptions.',y)
y=eq(r'S(z)=\frac{1}{1+\exp(-z)}',y,15)
y=eq(r'z_{1}=\alpha a+\beta c+0.14h-0.37',y,12)
y=eq(r'z_{2}=\alpha q-\beta m+0.27p-0.30',y,12)
y=eq(r'z_{3}=\alpha ac+\beta pq-0.28m-0.37',y,12)
y=eq(r'z_{4}=\alpha\sin(a)+\beta\cos(h)+0.32q-0.42m-0.43',y,12)
y=eq(r'z_{5}=\alpha\ln(1+a^{2})+\beta\exp(-m^{2})+0.19pq-0.66',y,12)
y=eq(r'\alpha=0.36+0.049j+0.031f,\quad\beta=0.22+0.035j',y,10.3)
y=text('Family f = 0..4 and variant j = 0..9. The expressions test additive, multiplicative, trigonometric, logarithmic and exponential operators. The formula semantics are explicit in src/wearable_scoring.cpp and saved unmodified as CSV strings in examples/formula_registry.csv.',y)
y=sect('Interpretation of the mathematical outputs',y)
y=text('A bounded 0-to-1 score is <b>not</b> a calibrated clinical probability. These coefficients were chosen for a transparent technical demonstration, not fitted to physiological labels, activity categories, adverse events or clinical reference measurements.',y)
#5
y=begin('4. Original paceval execution and workload')
y=text('The application compiles the original <b>paceval_main.cpp</b> SDK bridge together with the C++ application, and loads the compatible external Linux paceval runtime. Formula strings are registered once with the original API; handles persist throughout the replay and are deleted at program shutdown.',y)
y=table([('Initializes runtime','paceval_InitializeLibrary'),('Compiles 51 expressions','paceval_CreateComputation'),('Scalar evaluation','paceval_dGetComputationResult'),('Independent-vector batch evaluation','paceval_dGetComputationResultExt'),('Error and validity check','paceval_GetIsError; per-result batch error codes'),('Releases graph handles','paceval_DeleteComputation and paceval_FreeLibrary')],y,h=30)
y=sect('Executed synthetic workload',y)
y=table([('Raw timestamps','2,000,000 (10,000 windows x 200 samples)'),('Different scoring formulas','50 original plus one separate revision'),('Scalar score computations','13,923'),('Batch results','1,600 (50 formulas x 32 input vectors)'),('Computed score-surface values','3,721 (61 x 61 parameter samples)'),('Synthetic threshold flags','420 of 10,000 at score >= 0.65')],y,h=28)
y=text('Host tasks: generate and preprocess raw synthetic signals, enforce domains, control thresholds, serialize files and independently validate the outputs. paceval tasks: parse and evaluate the defined mathematical expressions. Only the latter tasks are attributed to paceval.',y)
#6
y=begin('5. Actually generated IMU/PPG traces and replay')
y=fig('01_synthetic_ppg_imu_trace',y,245,'Figure 1. A saved synthetic optical and accelerometer window. The curves are signals generated in C++, not patient or device recordings.')
y=fig('02_scoring_replay',y,235,'Figure 2. Score replay from 10,000 actual paceval evaluations; a fixed synthetic technical review threshold is marked.')
#7
y=begin('6. Score distributions and operating policy')
y=fig('03_score_distribution',y,248,'Figure 3. Distribution of recorded mathematical scores over the 10,000 synthetic windows.')
y=fig('06_formula_family_thresholds',y,235,'Figure 4. The selected mathematical expression family changes the number of technical screen flags.')
y=sect('What the example policy means',y)
y=text('The fixed cutoff of 0.65 is defined by the external C++ host. Its 420 triggered flags are neither diagnoses nor estimates of medical sensitivity, specificity, risk, clinical prevalence or real-device alert performance.',y,'small')
#8
y=begin('7. Multidimensional signal-quality sensitivity')
y=fig('04_quality_score_surface_3d',y,262,'Figure 5. A real 61 x 61 paceval score field over normalized motion and optical periodicity features (fixed remaining inputs).')
y=fig('05_quality_score_contours',y,260,'Figure 6. Contour map of the same 3,721 paceval-evaluated mathematical input combinations.')
#9
y=begin('8. Reusable formulas and controlled revision')
y=fig('07_versioned_formula_response',y,245,'Figure 7. A newly created formula version changes the activity score while the earlier graph remains independently callable.')
y=fig('08_feature_scatter',y,248,'Figure 8. Signal-derived features colored by their assigned mathematical score. The synthetic data do not represent population statistics.')
#10
y=begin('9. Scientific validation and interpretation')
y=sect('What was independently verified',y)
y=text('The complete 10,000-window C++ replay passed an independently programmed mathematical reference for every score. Fifty different graphs were evaluated via the official batch function on 32 additional vectors each. A separate 80-decimal-digit Python implementation checked 500 exported scores. Four saved raw-trace windows yielded 24 independently reconstructed feature values.',y)
y=table([('Integration build and CTest','1 / 1 passed with the original paceval runtime'),('Independent decimal calculations','500 of 500 passed'),('Raw signal feature reconstructions','24 of 24 passed'),('Expected graph count','51 independently retrievable handles'),('Input contract checks','3 deliberate invalid inputs rejected')],y,h=29)
y=sect('Why the results are relevant to a wearable pipeline',y)
y=text('Reusable mathematical expression handles allow an application to maintain several explicit, auditable postprocessing equations independently of signal acquisition, detection or sensor-specific preprocessing. Version 2 was registered without invalidating version 1, allowing a controlled formula change and side-by-side numerical assessment.',y)
y=sect('Scientific and medical boundaries',y)
y=text('The data contain no real participants, no collected optical or inertial recordings, no validated physiological target labels and no clinical study. The result does not demonstrate a diagnosis, validated activity recognition, sensor robustness, medical device eligibility, calibrated probabilities or any execution-time, power or battery advantage.',y)
#11
y=begin('10. Reproducibility and external references')
y=sect('Reproduce with the original C/C++ SDK and external runtime',y)
y=text('The ZIP includes src/wearable_scoring.cpp, original paceval_main.h/cpp SDK files, src/CMakeLists.txt, deterministic raw-signal logic, 51 serialized formula definitions, full score data, high-precision audits, eight figure scripts/output pairs, and this whitepaper generator.',y)
y=text('Build: cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so; then cmake --build build -j; ctest --test-dir build --output-on-failure. Run ./build/wearable_scoring --windows 10000 --out examples, followed by the independent Python verification and figure scripts. All exact commands appear in README.md.',y,'small')
y=sect('Source references used in the domain review',y)
for r in [
 '[1] Wearable ECG/PPG multimodal signal monitoring review (2026), Sensors 26(11):3477: https://www.mdpi.com/1424-8220/26/11/3477',
 '[2] PPG signal quality assessment and reconstruction for heart-rate analysis (2025), Sensors 25(24):7556: https://pmc.ncbi.nlm.nih.gov/articles/PMC12736534/',
 '[3] Reiss, Indlekofer &amp; Schmidt (2019), PPG-DaLiA, UCI Machine Learning Repository: https://doi.org/10.24432/C53890',
 '[4] PhysioNet Wrist PPG During Exercise v1.0.0: https://physionet.org/content/wrist/1.0.0/',
 '[5] FDA General Wellness: Policy for Low Risk Devices, January 2026: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/general-wellness-policy-low-risk-devices',
 '[6] paceval original C/C++ interface and mathematical engine: https://github.com/paceval/paceval'
]:y=text(r,y,'small',after=9)
y=sect('Conclusion',y)
y=text('Original paceval C/C++ execution successfully demonstrated 50 reusable mathematical wearable signal-score definitions and an immutable revision over deterministic synthetic PPG and motion features. The published 3D score surfaces and result figures follow directly from executed values. Transfer to actual wearables requires a separately validated sensor-processing and domain-specific study.',y)
c.save()
print('PDF created:',OUT,'pages=',page)
