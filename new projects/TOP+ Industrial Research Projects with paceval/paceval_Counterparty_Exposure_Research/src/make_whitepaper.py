#!/usr/bin/env python3
"""Rebuild the English technical whitepaper from shipped paceval outputs and plots."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT
import re
root=Path(__file__).resolve().parents[1]; figures=root/'figures'
pdf=root/'paceval_Counterparty_Exposure_Whitepaper_EN.pdf'
W,H=595.28,841.89
navy=HexColor('#17354d'); teal=HexColor('#138a9e'); muted=HexColor('#536475'); gray=HexColor('#eef3f5')
c=canvas.Canvas(str(pdf),pagesize=(W,H)); c.setTitle('paceval | Real-Time Counterparty Exposure Functions | Research Whitepaper')
style=ParagraphStyle('body',fontName='Helvetica',fontSize=10.5,leading=16,textColor=navy,spaceAfter=8)
small=ParagraphStyle('small',parent=style,fontSize=9.3,leading=14)

def frame(section):
    c.setStrokeColor(teal);c.setLineWidth(1.3);c.line(39,H-64,W-39,H-64)
    c.setFont('Helvetica-Bold',9);c.setFillColor(teal);c.drawString(39,H-44,'PACEVAL  |  INDEPENDENT SCIENTIFIC RESEARCH  |  NOVEMBER 2026')
    c.setFont('Helvetica',8);c.setFillColor(muted);c.drawString(39,27,'paceval  |  Real-Time Counterparty Exposure Functions')
    c.drawRightString(W-39,27,str(c.getPageNumber()))
    if section:c.setFont('Helvetica-Bold',17);c.setFillColor(navy);c.drawString(39,H-96,section)
    return H-122

def p(text,y,sty=style,x=39,width=W-78):
    q=Paragraph(text,sty);w,h=q.wrap(width,700);q.drawOn(c,x,y-h);return y-h-12

def head(text,y):
    c.setFillColor(teal);c.setFont('Helvetica-Bold',11);c.drawString(39,y-11,text);return y-28

def figure(name,y,height=255):
    path=figures/(name+'.png'); im=ImageReader(str(path)); iw,ih=im.getSize();wid=min(W-84,height*iw/ih);he=wid*ih/iw
    if he>height:he=height;wid=he*iw/ih
    c.drawImage(im,(W-wid)/2,y-he,width=wid,height=he,mask='auto');return y-he-8

def page():c.showPage()

# 1. COVER (conceptual illustration only)
y=frame(None)
c.setFillColor(navy);c.setFont('Helvetica-Bold',26);c.drawString(39,H-119,'Real-Time Counterparty')
c.drawString(39,H-151,'Exposure Functions')
c.setFont('Helvetica',13);c.setFillColor(muted);c.drawString(39,H-179,'Reusable mathematical kernels for exposure monitoring')
c.drawImage(ImageReader(str(figures/'00_counterparty_hero.png')),39,H-483,width=W-78,height=278,mask='auto')
y=H-509
y=p('<b>Executed research outcome.</b> Fifty original exposure expressions plus one independent formula revision; 20,000 completed synthetic updates; 24,167 scalar paceval evaluations; 1,600 batch checks; 3,721 points on a computed exposure surface.',y)
y=p('<b>Research scope.</b> Pointwise indicative exposure formulas, immutable expression handles and scenario sensitivities. Not a regulatory SA-CCR, initial margin, EAD, CVA, contractual netting or live risk service.',y)
y=p('<i>Cover artwork is a conceptual financial illustration and is not a plot of calculation data.</i>',y,small)
page()

# 2. Context
y=frame('1. Industrial use case and state of the art')
y=p('Derivatives and collateral desks monitor the current market value of exposures by counterparty or legally defined netting set. If portfolio value, collateral valuation or contract terms change, the risk platform needs a controlled mathematical response that can be audited and reused. The present experiment isolates one such mathematical kernel and repeatedly evaluates it using paceval.',y)
y=head('Operational process',y)
y=p('An upstream pricing and legally governed netting process supplies a net mark-to-market value. A collateral service supplies already approved amounts and illustrative haircuts. The C++ host checks value ranges and delivers these inputs to the corresponding versioned paceval mathematical expression. The resulting indicative positive exposure can inform a research dashboard or a policy review, not an automatic financial or regulatory decision.',y)
y=head('What existing standards actually require',y)
y=p('Basel III SA-CCR distinguishes replacement cost from potential future exposure (PFE), with a separate regulatory multiplier, and operates on detailed margined and unmargined netting-set definitions. ISDA collateral documentation involves variation margin, initial margin, agreement terms and eligibility. The EBA also describes specific model-validation requirements for initial margin models. The simplified research equations in this document are <b>not</b> substitutes for these frameworks.',y)
y=head('Research question',y)
y=p('Can a library of versioned, nonlinear positive-exposure functions be compiled into reusable paceval computation graphs, supplied with independent synthetic market updates, and tested for correct execution in both scalar and packed-batch modes? The answer is assessed by actual SDK execution and independent numerical audits.',y)
y=p('<b>Key sources:</b> Basel Committee counterparty credit risk overview and SA-CCR executive summary; ISDA collateral management suggested operational practices; EBA pro forma initial-margin-model validation (full links on page 10).',y,small)
page()

# 3 math
y=frame('2. Defined mathematical functions')
y=p('All monetary inputs and outputs are in EUR millions. The synthetic already-netted mark-to-market amount is <b>v</b>; pledged collateral is <b>c</b>; the illustrative recognition haircut is <b>h</b>; the normalized scenario shock is <b>s</b>; <b>t</b> is a synthetic threshold amount; and <b>f</b> is a collateral conversion factor. Coefficients a and b are fixed by a versioned rule registry.',y)
y=head('Positive part and five mathematical families',y)
models=[('P(d) = (d + sqrt(d*d)) / 2','Non-negative pointwise exposure, mathematically max(d,0).'),('E1 = P(v - c(1-h) - t + a*s)','Baseline with a linear scenario component.'),('E2 = P(v(1+a*s) - c(1-h) - t)','Proportional mark-to-market shock.'),('E3 = P(v + a*s + b*s*s - c(1-h) - t)','Quadratic nonlinear scenario sensitivity.'),('E4 = P(v - c(1-h)*(f+a*s) - t)','Illustrative collateral FX conversion.'),('E5 = P(v - c(1-h) - t) + a*sqrt(1+s*s)*P(v)','Additional purely illustrative nonlinear buffer; not PFE.')]
for eq,description in models:
    c.setFont('Courier-Bold',10);c.setFillColor(navy);c.drawString(43,y-10,eq);y-=22
    y=p(description,y,small)
y=head('Contracts and interpretation',y)
y=p('The program admits only finite and bounded inputs, including 0 <= h <= 0.5, 0.7 <= f <= 1.3 and -0.5 <= s <= 0.5. The 50 fixed expressions constitute five families times ten coefficient variants. The mathematical expressions implement a selected haircut as a reduction in recognized collateral, not a Basel or ISDA standardized haircut schedule.',y)
page()

# 4 architecture
y=frame('3. paceval execution architecture')
y=head('What paceval actually performs',y)
y=p('The original paceval C/C++ SDK creates each mathematical expression graph exactly once via paceval_CreateComputation. The application evaluates distinct input vectors using paceval_dGetComputationResult, with additional packed-array checks using paceval_dGetComputationResultExt. A modified coefficient expression is registered as a separate computation handle instead of overwriting an earlier formula.',y)
y=head('What the C++ host performs',y)
y=p('The host owns the deterministic generator, replay sequencing, finite-value and business-domain input contracts, rule selection, CSV output, numerical reference and graph disposal. This separation matters: paceval does not perform legal netting, pricing, collateral policy approval or a stochastic counterparty simulation.',y)
# manually drawn architecture
from reportlab.lib.colors import white
nodes=[('Synthetic market','state'),('Domain checks','in C++'),('paceval graphs','51 handles'),('Host reporting','and audit')]
for k,(a,b) in enumerate(nodes):
 x=41+k*139;c.setFillColor(gray if k!=2 else HexColor('#d6eff1'));c.setStrokeColor(teal);c.roundRect(x,H-395,121,70,6,stroke=1,fill=1)
 c.setFont('Helvetica-Bold',9);c.setFillColor(navy);c.drawCentredString(x+60,H-352,a)
 c.setFont('Helvetica',8);c.drawCentredString(x+60,H-367,b)
 if k<3:c.setFont('Helvetica-Bold',15);c.setFillColor(teal);c.drawString(x+125,H-359,'>')
y=H-430
y=head('Stable expression lifecycle',y)
y=p('The fifty original handles remain available throughout the workload. A 51st handle demonstrates an immutable revised expression. Existing evaluations are not changed retroactively. All paceval handles are freed before library shutdown, and each SDK operation is checked for errors.',y)
y=head('Deliberate exclusions',y)
y=p('A production platform would additionally need legal agreement handling, counterparty identity and netting-set validation, collateral eligibility, market data lineage, stress calibration, access control and external model validation. These requirements are outside this narrowly controlled mathematical research kernel.',y)
page()

#5 experimental
f=(root/'examples/sdk_execution.txt').read_text();y=frame('4. Deterministic workload and validation')
y=p('The replay uses a fixed pseudorandom seed (20261112) to generate synthetic finite market updates and associated collateral state. Fifty graph definitions are assigned cyclically. A completed 20,000-update replay is fully accounted for in the metrics file; every 100th update is exported in detail for independent examination.',y)
y=head('Executed evidence, not hypothetical results',y)
for label,val in [('Original formula variants','50'),('Graphs including controlled revision','51'),('Completed market updates','20,000'),('Scalar SDK evaluations','24,167'),('Packed batch checks','1,600'),('3D parameter grid','3,721'),('Independent 80-digit Decimal checks','200, all passed'),('Invalid input cases rejected','3'),('CTest integration','1/1 passed')]:
 c.setFillColor(gray if (len(label)%2) else white);c.rect(39,y-24,W-78,25,stroke=0,fill=1);c.setFillColor(navy);c.setFont('Helvetica',9.6);c.drawString(47,y-17,label);c.setFont('Helvetica-Bold',9.6);c.drawRightString(W-48,y-17,val);y-=26
y-=20
y=p('A proposed one-million-update experiment exceeded the execution window available for this research session; consequently it is <b>not</b> reported as completed. The provided C++ executable accepts a user-specified replay size for subsequent tests. The high-precision audit uses exported decimal representations of the sampled rows; it does not imply exact reconstruction of original binary floating-point values.',y,small)
y=p('Numerical differences between the SDK and the independent calculation are preserved only in the technical audit records, not as comparative accuracy figures in this public report. Passing finite tests cannot establish global correctness of a financial exposure model.',y,small)
page()

# 6-9 diagrams
pages=[('5. Exposure distributions and model families',[('01_sample_exposure_distribution','Distribution of sampled indicative positive exposures.'),('02_rule_family_exposure','Fifty formulas grouped into five distinct, versioned mathematical families.')]),
('6. Market stress and the 3D exposure model',[('03_market_stress_sensitivity','Market-shock sensitivity for four defined mathematical variants.'),('04_exposure_surface_3d','Surface calculated from 3,721 paceval evaluations; all axes show units.')]),
('7. Collateral mitigation and expression changes',[('05_collateral_contour','Zero-exposure boundary under an illustrative haircut and threshold.'),('06_immutable_formula_versioning','Previously registered formula stays available after a controlled revision.')]),
('8. Haircuts, collateral and scenario responses',[('07_haircut_scatter','Sampled net mark-to-market observations, colored by haircut.'),('08_collateral_vs_exposure','How the synthetic sample responds to collateral and market shocks.')])]
for heading,pairs in pages:
 y=frame(heading)
 for name,caption in pairs:
  y=figure(name,y,245)
  y=p('<b>Figure:</b> '+caption,y,small)
  y-=12
 page()

# 10 references
y=frame('9. Interpretation and reproducibility')
y=p('<b>Demonstrated finding.</b> Fifty distinct, synthetic exposure expressions, an immutable new version, repeated parameter reuse, scalar and packed-batch evaluations, and multiple stress/collateral diagrams were executed through the original paceval C/C++ runtime. Every sampled result selected for the independent 80-digit Decimal audit passed its numerical acceptance test.',y)
y=p('<b>Scientific boundary.</b> These values are neither regulatory exposure at default nor measured potential future exposure. Neither legal netting, comprehensive valuation, initial margin, wrong-way risk, CVA, loss given default, market calibration nor production system behavior is covered. The research does not provide trading, regulatory or investment advice.',y)
y=head('Reproduce from the GitHub package',y)
y=p('Compile with CMake from src/ using an externally supplied compatible paceval shared library. Run the executable with --out and --updates, then run src/verify_results.py, src/high_precision_reference.py, src/make_figures.py, src/make_whitepaper.py and src/check_readme_math.py. The shipped audit scripts read the released examples/ directory. The external runtime is intentionally excluded from this archive.',y)
y=head('Selected sources and standards',y)
refs=[
'BIS (2018), Counterparty credit risk in Basel III — Executive Summary, www.bis.org/publications/fsi-summary-counterparty-credit-risk-basel-iii-executive-summary',
'BIS, Counterparty credit risk overview and glossary, www.bis.org/committees/bcbs/basel-consolidated-guidelines/module/cri/40',
'ISDA (2026), Collateral Management Suggested Operational Practices, www.isda.org/collateral-management-sop/',
'EBA, Validation of pro forma initial margin models, www.eba.europa.eu/activities/direct-supervision-and-oversight/validation-pro-forma-initial-margin-models',
'paceval C/C++ interface, paceval.com/api/']
for ref in refs:y=p(ref,y,small)
c.save();print('Created',pdf)
