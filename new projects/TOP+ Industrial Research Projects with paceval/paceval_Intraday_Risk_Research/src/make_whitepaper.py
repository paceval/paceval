#!/usr/bin/env python3
"""Rebuild English research PDF from released reproducible paceval outputs."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
R=Path(__file__).resolve().parents[1];F=R/'figures';P=R/'paceval_Intraday_Risk_Whitepaper_EN.pdf'
W,H=595.28,841.89;navy=HexColor('#17354d');teal=HexColor('#138a9e');muted=HexColor('#536475');gray=HexColor('#eef3f5')
c=canvas.Canvas(str(P),pagesize=(W,H));c.setTitle('paceval | Intraday Risk Metric Recalculation | English Research Whitepaper')
body=ParagraphStyle('body',fontName='Helvetica',fontSize=10.4,leading=16,textColor=navy);small=ParagraphStyle('small',parent=body,fontSize=9.3,leading=14)
def page(name=None):
 c.setStrokeColor(teal);c.setLineWidth(1.3);c.line(39,H-64,W-39,H-64)
 c.setFont('Helvetica-Bold',9);c.setFillColor(teal);c.drawString(39,H-44,'PACEVAL  |  INDEPENDENT SCIENTIFIC RESEARCH  |  NOVEMBER 2026')
 c.setFont('Helvetica',8);c.setFillColor(muted);c.drawString(39,27,'paceval  |  Intraday Risk Metric Recalculation');c.drawRightString(W-39,27,str(c.getPageNumber()))
 if name:c.setFont('Helvetica-Bold',17);c.setFillColor(navy);c.drawString(39,H-96,name)
 return H-122
def p(txt,y,sty=body):
 q=Paragraph(txt,sty);_,h=q.wrap(W-78,700)
 if y-h<62:raise RuntimeError('Text outside page near '+str(txt[:40]))
 q.drawOn(c,39,y-h);return y-h-12
def head(txt,y):c.setFont('Helvetica-Bold',11);c.setFillColor(teal);c.drawString(39,y-11,txt);return y-28
def fig(filename,y,maxh=245):
 im=ImageReader(str(F/(filename+'.png')));iw,ih=im.getSize();width=min(W-85,maxh*iw/ih);height=width*ih/iw
 if height>maxh:height=maxh;width=height*iw/ih
 if y-height<75:raise RuntimeError('Figure outside page '+filename)
 c.drawImage(im,(W-width)/2,y-height,width=width,height=height);return y-height-10
def nextpage():c.showPage()
# Cover
y=page();c.setFont('Helvetica-Bold',25);c.setFillColor(navy);c.drawString(39,H-120,'Intraday Risk Metric');c.drawString(39,H-152,'Recalculation');c.setFont('Helvetica',12);c.setFillColor(muted);c.drawString(39,H-180,'Reusable analytical risk kernels with frozen covariance')
c.drawImage(ImageReader(str(F/'00_intraday_risk_hero.png')),39,H-485,width=W-78,height=278,mask='auto');y=H-513
y=p('<b>Executed research outcome.</b> Fifty distinct risk expressions plus one immutable revision, 20,000 completed synthetic market updates, 24,167 scalar paceval evaluations, 1,600 packed batch checks and 3,721 numerical surface points.',y)
y=p('<b>Scope.</b> A deliberately bounded, frozen-covariance analytical research workflow. Not a bank-approved market-risk system, a measured real-time engine or regulatory expected shortfall.',y)
y=p('<i>Cover is a conceptual image, not a numerical research result.</i>',y,small);nextpage()
# Context
y=page('1. Industrial context and current practice')
y=p('Banks and investment firms monitor portfolio factor exposures and risk limits as positions and market prices change during a trading day. A typical production chain combines position capture, market data controls, valuation, approved sensitivity models, risk aggregation and exception processing. The mathematical kernel here is only the risk aggregation calculation.',y)
y=head('Example operational workflow',y)
y=p('A risk desk receives approved, dimensioned position sensitivities, obtains a previously calibrated covariance matrix, evaluates a risk metric, checks an internal research limit, and records changes across market updates. This demonstrator executes that repeatable mathematical subfunction with paceval while all approvals and risk-limit routing remain in the C++ host.',y)
y=head('What current practice does, and does not, imply',y)
y=p('Classical RiskMetrics-style delta-normal measurement uses the quadratic portfolio variance form. Regulatory market-risk internal-model approaches under the Basel Framework may instead require expected shortfall, backtesting, model approval, and detailed risk-factor treatment. The Basel Core Principles emphasize market-risk limits, independent controls, and reliable valuation data. Therefore the present metric must not be labelled regulatory expected shortfall or an approved capital number.',y)
y=head('Research question',y)
y=p('Can fifty controlled mathematical risk expressions, using a frozen covariance input and synthetic intraday position updates, be registered as persistent paceval computation objects and evaluated repeatedly while retaining transparent independent numeric checks, scalar and batch execution, and explicit formula versioning?',y)
y=p('Sources: RiskMetrics Technical Document (1996); BIS MAR30 (updated July 2024); BIS Basel Core Principles (April 2024); paceval public C/C++ API. Full links appear on page 10.',y,small);nextpage()
# Math
y=page('2. Defined mathematical model')
y=p('The signed position exposures w1 and w2 are in EUR millions. Covariance entries describe dimensionless daily factor returns; thus the risk measure is in EUR millions. The synthetic shock s is dimensionless. The covariance matrix is constant for every experiment, and it is positive definite: det(Sigma)=0.0002*0.00045-0.00012^2=7.56e-8 &gt; 0.',y)
y=head('Frozen covariance and the baseline',y)
for eq,desc in [
('Sigma = [[0.00020, 0.00012], [0.00012, 0.00045]]','Fixed, internally consistent 2 x 2 factor-return covariance matrix.'),
('q = 0.00020*w1^2 + 0.00024*w1*w2 + 0.00045*w2^2','Two-factor quadratic portfolio variance.'),
('R0 = sqrt(q)','Delta-normal-style portfolio standard-deviation metric; not Value at Risk.'),
('R1 = sqrt(q)*(1 + a*s)','Multiplicative synthetic shock to the baseline risk metric.'),
('R2 = sqrt(q + 0.00002*a*(w1^2+w2^2)*s^2)','Illustrative shock-dependent variance augmentation.'),
('R3 = sqrt(0.0002*w1^2 + 0.00045*w2^2 + 2*(0.00012+0.00002*a*s)*w1*w2)','Bounded synthetic covariance sensitivity.'),
('R4 = sqrt(q) + 0.004*a*sqrt(w1^2+w2^2)*sqrt(1+s^2)','Illustrative concentration-type, non-negative risk add-on.'),
('R5 = sqrt(q) + 0.00015*a*abs(w1*w2)*s^2 + 0.002*b*sqrt(1+s^2)','Nonlinear two-factor interaction add-on.')]:
 c.setFont('Courier-Bold',8.4);c.setFillColor(navy)
 # wrap long expressions with paragraphs instead of clipping
 y=p('<font name="Courier" size="8">'+eq.replace('&','&amp;').replace('<','&lt;')+'</font>',y,small)
 y=p(desc,y,small)
y=p('Fifty formulas vary a and b across five families. Bounds on signed positions, shock size and coefficients ensure the expressions are finite and their square-root radicands nonnegative for the defined workload.',y,small);nextpage()
# Arch
y=page('3. paceval architecture and responsibilities')
y=head('What the paceval runtime calculates',y)
y=p('The original SDK parses each formula into a computation object using paceval_CreateComputation. Repeated scalar evaluation uses paceval_dGetComputationResult. Separate packed-batch validation uses paceval_dGetComputationResultExt. The mathematical handles are created once and deleted on application shutdown.',y)
y=head('Which operations remain outside paceval',y)
y=p('The C++ host controls deterministic pseudorandom inputs, bounded-value checks, simulation ordering, formula-selection policy, synthetic limits, CSV export and independent reference arithmetic. It does not estimate a covariance matrix, fit a distribution, perform VaR backtesting, price options or connect to a live exchange.',y)
from reportlab.lib.colors import white
for idx,(one,two) in enumerate([('Synthetic positions','EUR million'),('Input contract','C++ validation'),('paceval','51 graph handles'),('Risk review','Host decision')]):
 x=39+idx*139;c.setFillColor(gray if idx!=2 else HexColor('#d6eff1'));c.setStrokeColor(teal);c.roundRect(x,H-403,121,68,6,stroke=1,fill=1);c.setFillColor(navy);c.setFont('Helvetica-Bold',9);c.drawCentredString(x+60,H-361,one);c.setFont('Helvetica',8);c.drawCentredString(x+60,H-375,two)
 if idx<3:c.setFont('Helvetica-Bold',14);c.setFillColor(teal);c.drawString(x+124,H-367,'>')
y=H-433;y=head('Immutable mathematical revision',y)
y=p('The fifty base formulas remain registered throughout the experiment. A different coefficient creates a 51st calculation object. The old and revised expressions are evaluated side by side, showing that a controlled formula update does not rewrite earlier computations.',y)
y=head('Analytical model interpretation',y)
y=p('Risk figures are simulated pointwise outputs of specified formulas. In real trading-book risk management, valuation controls, data lineage, governance, market calibration, sensitivity generation, approved limits and independent validation are additional essential tasks.',y);nextpage()
# Workload
y=page('4. Executed workload and numerical assurance')
y=p('The complete deterministic experiment uses a fixed random seed (20261112), finite synthetic position inputs, fifty formula variants and an additional immutable revision. Scalar checks compare selected calls with a separately implemented C++ reference; the released sampled data undergo an independent 80-digit mpmath audit.',y)
y=head('Reproducible evidence from the paceval SDK',y)
metrics=[('Original mathematical expression variants','50'),('Persistent graphs including controlled revision','51'),('Completed synthetic intraday updates','20,000'),('Scalar SDK evaluations','24,167'),('Packed batch checks','1,600'),('3D surface sample points','3,721'),('Independent 80-digit numerical sample checks','500 / 500 passed'),('Invalid input contract checks','3 / 3 passed'),('CMake / CTest integration','1 / 1 passed')]
for k,(label,value) in enumerate(metrics):
 c.setFillColor(gray if k%2==0 else white);c.rect(39,y-25,W-78,26,stroke=0,fill=1);c.setFillColor(navy);c.setFont('Helvetica',9.4);c.drawString(47,y-17,label);c.setFont('Helvetica-Bold',9.4);c.drawRightString(W-47,y-17,value);y-=27
y-=26;y=p('The experiment tests graph reuse and the mathematical workflow, not processing-speed superiority or p99.9 latency. The recorded count of formula evaluations includes the replay, numerical surface, stress curves and formula-revision experiments. Released audit files contain detailed numerical checks; this public research report does not compare C++ and paceval numerical errors.',y,small)
y=p('The resulting risk levels are neither estimates of future portfolio losses nor calibrated regulatory capital requirements. Intraday risk limits and numerical thresholds in this experiment are explicitly synthetic.',y,small);nextpage()
# diagrams
sections=[('5. Intraday replay and rule distributions',[('01_intraday_replay','Synthetic replay sampled every 25th update; colored points show illustrative host alerts.'),('02_risk_distribution','Distribution of sampled portfolio risk measure values.')]),('6. Risk rules and portfolio factor sensitivity',[('03_rule_family_risk','Different analytical rule variants yield differing research risk levels.'),('04_risk_surface_3d','3D risk surface from 3,721 actual paceval values with frozen covariance.')]),('7. Risk contours and stress scenarios',[('05_risk_contours','Two-factor risk contours use the same computed 3D grid.'),('06_stress_scenarios','Four model families evaluated over a bounded synthetic shock range.')]),('8. Immutable revisions and risk-limit examples',[('07_formula_versioning','The old and revised formulas remain individually callable.'),('08_risk_limit_alerts','Host-calculated illustrative risk-limit events across formula variants.')])]
for title,parts in sections:
 y=page(title)
 for filename,description in parts:
  y=fig(filename,y,243);y=p('<b>Figure.</b> '+description,y,small);y-=10
 nextpage()
# Repro and refs
y=page('9. Research interpretation and references')
y=p('<b>Demonstrated.</b> Fifty variant mathematical expressions, controlled immutable changes, repeated evaluations on synthetic intraday exposures, scalar and batch invocation of the original paceval SDK, and a two-factor 3D analytical risk response are all executed and independently checked.',y)
y=p('<b>Not established.</b> This is not a production market-risk monitoring platform or a backtested/approved VaR, expected shortfall, stressed ES, or Basel capital calculation. Covariance estimation, non-Gaussian tail losses, nonlinear derivative valuations, liquidity horizons and market-data integrity are not modelled. Results do not constitute investment advice.',y)
y=head('Reproduction from the GitHub package',y)
y=p('The C++ target builds using src/CMakeLists.txt with a compatible paceval Linux shared library supplied externally. Run intraday_risk with --updates 20000 and --out, then use src/verify_results.py, src/high_precision_reference.py, src/make_figures.py, src/make_whitepaper.py and src/check_readme_math.py. All released scientific graphs are regenerated from the supplied examples/ CSVs.',y)
y=head('Selected research and industrial references',y)
for ref in [
'RiskMetrics, Technical Document, 4th edition (1996), www.msci.com/documents/10199/5915b101-4206-4ba0-aee2-3449d5c7',
'BIS, Basel Framework MAR30, Internal models approach: general provisions, updated 2024-07-05, www.bis.org/committees/bcbs/basel-framework/standard/mar/30/inforce/2023-01-01/published/2024-07-05',
'BIS, Basel Core Principles BCP40, published 2024-04-25, www.bis.org/committees/bcbs/basel-framework/standard/bcp/40/inforce/2024-04-25/published/2024-04-25',
'Reserve Bank of Australia, Measuring Traded Market Risk: VaR and Backtesting Techniques (1997), www.rba.gov.au/publications/rdp/1997/9708/value-at-risk.html',
'paceval C/C++ API, version 4.25 documentation, paceval.com/api/']:
 y=p(ref,y,small)
c.save();print('Created',P)
