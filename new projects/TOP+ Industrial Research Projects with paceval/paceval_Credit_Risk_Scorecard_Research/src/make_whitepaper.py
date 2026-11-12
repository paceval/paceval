#!/usr/bin/env python3
"""Build the English research paper with the same editorial architecture as the supplied 9-page reference."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
root=Path(__file__).resolve().parents[1]; target=root/'paceval_Credit_Risk_Scorecard_Whitepaper_EN.pdf'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',font));pdfmetrics.registerFont(TTFont('DV-B',bold))
ink=colors.HexColor('#14293a');teal=colors.HexColor('#168c9c');gray=colors.HexColor('#596a76');navy=colors.HexColor('#0b1627');light=colors.HexColor('#eaf3f5')
styles={
 'title':ParagraphStyle('title',fontName='DV-B',fontSize=23,leading=27,textColor=ink,spaceAfter=11),
 'sub':ParagraphStyle('sub',fontName='DV',fontSize=12,leading=17,textColor=teal,spaceAfter=10),
 'head':ParagraphStyle('head',fontName='DV-B',fontSize=17,leading=22,textColor=ink,spaceAfter=12),
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.4,leading=15.5,textColor=ink,spaceAfter=12),
 'note':ParagraphStyle('note',fontName='DV',fontSize=8.1,leading=12,textColor=gray,spaceAfter=9),
 'caption':ParagraphStyle('caption',fontName='DV',fontSize=8.1,leading=12,textColor=gray,alignment=TA_CENTER,spaceAfter=13),
 'th':ParagraphStyle('th',fontName='DV-B',fontSize=8.7,leading=12,textColor=ink),
 'td':ParagraphStyle('td',fontName='DV',fontSize=8.5,leading=13,textColor=ink),
}
P=lambda text,kind='body':Paragraph(text,styles[kind]); story=[]
def add(*paras):
 for t in paras:story.append(P(t))
def head(n,name):story.append(P(f'{n}. {name}','head'))
def fig(name,caption,w=514):
 from PIL import Image as PIL
 path=root/'figures'/name;im=PIL.open(path);h=w*im.height/im.width
 if h>268:h=268;w=h*im.width/im.height
 story.append(Image(str(path),width=w,height=h));story.append(P(caption,'caption'))
def table(rows,widths=None):
 data=[[P(str(c),'th' if i==0 else 'td') for c in row] for i,row in enumerate(rows)]
 tb=Table(data,colWidths=widths or [256,258],hAlign='LEFT',repeatRows=1)
 tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),light),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f8f9')]),('LINEBELOW',(0,0),(-1,0),.6,teal),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(tb);story.append(Spacer(1,15))
def new():story.append(PageBreak())
story.append(P('Reusable Credit Risk Decision Mathematics','title'))
story.append(P('An executable, independently audited paceval C++ scorecard mathematics demonstrator','sub'))
fig('00_credit_risk_hero.png','Cover illustration: synthetic scorecard inputs, reusable mathematical graphs and independent checks.',514)
add('<b>Research outcome.</b> Using the supplied paceval 4.25 C/C++ facade and a compatible Linux x86-64 engine, 100 reusable scorecard graphs executed 10,000 scalar calculations and 6,400 additional batch evaluations. All agreed with independently coded native C++ arithmetic within the declared tolerance. A separate 80-digit Python Decimal audit passed all 10,000 exported samples.')
add('<b>Scope.</b> Fixed coefficients are generated synthetically and are not fitted, calibrated, or validated on borrower outcomes. All displayed logistic outputs are illustrative, not verified probabilities of default. Numerical correctness does not imply suitability for credit decisions, regulatory adverse-action notices or risk-model governance.')
new();head(1,'Research question and execution architecture')
add('The original WP-018 proposal considered whether repeatedly used credit-scorecard expressions could be executed with paceval. This implementation establishes an executable mathematical use case, deterministically specified synthetic inputs, reusable formula handles and two independent arithmetic checks.')
fig('01_execution_architecture.png','Figure 1. Execution boundaries: host-side input/model policies and independent audit are separate from graph evaluation.')
add('The host generates bounded numerical features, maintains 100 coefficient sets, calculates additive log-odds contributions and exports traceable samples. The host creates one paceval computation handle per scorecard formula and reuses it across cases. Both the scalar API and batched API were executed with the supplied library; reason indexing is separately implemented by the host.')
add('<b>Evidence boundary.</b> The actual paceval SDK path, native reference and independently specified decimal oracle were executed successfully. The numeric checks establish arithmetic feasibility only; credit-model validity and regulatory suitability are separate questions.','')
new();head(2,'Mathematical scorecard contracts')
table([['Component','Declared mathematical meaning'],['Linear predictor','z = intercept + sum(j=0..4) b[j] * x[j]'],['Logistic transform','s(z) = 1 / (1 + exp(-z)); numerically stable native implementation'],['Synthetic feature domain','Five independent bounded features x[j] in [0,1]'],['Coefficients','100 fixed-seed synthetic intercept/coefficient sets; positive b[j]'],['Contribution ranking','argmax of b[j] * x[j], with first-index tie-breaking'],['Scenario','An illustrative single-feature intervention, not a causal counterfactual']])
fig('02_logistic_kernel.png','Figure 2. Mathematical logistic transform; not an empirically calibrated credit default curve.',514)
add('A logistic scorecard can map log-odds to a number in (0,1). Calling that number a real-world probability of default requires labels, training and out-of-time calibration. Those requirements are outside this arithmetic experiment. The contribution ranking is an exact decomposition of this additive synthetic score only; it is not an automatically compliant adverse-action explanation.')
new();head(3,'Deterministic research workload')
add('A fixed XOR-shift-style integer generator with seed 20261112 creates 100 coefficient vectors and 100 synthetic feature vectors. The same 100 vectors are reused across 100 scorecards. Two explicit boundary cases use all-zero and all-one features. The verified paceval experiment therefore contains 10,000 scalar evaluations; additionally, 64 inputs per scorecard were evaluated through the SDK batch API (6,400 outputs).')
fig('03_synthetic_output_distribution.png','Figure 3. Distribution across 10,000 exported scores (100 cases per scorecard), not observed borrower defaults.')
add('The export CSV contains the model identifier, all five coefficients, all five feature values, intercept, linear predictor, logistic output and strongest positive log-odds contribution index. This makes the exported arithmetic independently reproducible. It does not contain borrower records, protected attributes, observed outcomes or actual credit decisions.')
new();head(4,'paceval execution and independent numerical audit')
summary=json.loads((root/'results/high_precision_audit.json').read_text())
table([['Verification','Observed result'],['SDK-enabled CTest','1 / 1 passed'],['Reusable paceval graphs','100 created and reused'],['paceval scalar versus native','10,000 / 10,000 passed'],['paceval batch versus native','6,400 / 6,400 passed'],['Independent Decimal audit',f"{summary['rows_checked']:,} / {summary['rows_checked']:,} passed"],['Decimal working precision','80 significant decimal digits'],['Maximum exported-score discrepancy',f"{float(summary['max_absolute_pd_difference']):.4e}"],['Numerical thresholds','SDK/native: 1e-10; Decimal/export: 1e-12']])
fig('06_independent_numeric_audit.png','Figure 4. Independent 80-digit reconstruction of the exported synthetic arithmetic outputs.')
add('The Decimal audit reconstructs the linear predictor and logistic transform from the printed decimal coefficients and feature values, then verifies the recorded score and contribution ranking. The maximum deviation reflects binary64 versus decimal evaluation and finite export precision. It does not constitute an exhaustive proof of correctness over all possible inputs.')
new();head(5,'Sensitivity analysis and contribution tracing')
fig('05_single_feature_sensitivity.png','Figure 5. One-feature sensitivity in a fixed synthetic scorecard; remaining inputs and coefficients do not change.')
fig('04_logodds_contributions.png','Figure 6. Additive log-odds decomposition with the strongest positive synthetic contribution highlighted.')
add('Sensitivity is measured by direct reevaluation of the logistic expression as one normalized feature varies over [0,1]. These are hypothetical numerical perturbations, not causal interventions. Because coefficients are all positive in this pilot, an increased feature cannot reduce the logistic output; this restriction is a property of the synthetic generator, not of real credit data.')
new();head(6,'Reusable expression graphs and model traceability')
add('Each of the 100 coefficient sets is treated as a different research formula version. A paceval computation object was created once per formula and reused for new synthetic input vectors. Each handle is checked and disposed of by the host. A production system would require persistent registry metadata, stable schema signatures and explicit invalidation/promotion procedures beyond this program.')
add('The study intentionally addresses successful mathematical graph execution, arithmetic agreement and model traceability. The tested computation contracts are independent of processor-specific timing. No claims about financial accuracy, model discrimination or deployment readiness follow from these tests.')
fig('07_evidence_boundary.png','Figure 7. Verified mathematical execution and numerical checks contrasted with untested financial-model suitability.')
add('The project makes no claims concerning SQL equivalence, scorecard calibration, AUC, fairness, causal attribution or regulatory approvals. These are outside the released mathematical feasibility experiment.')
new();head(7,'Reproducibility, implementation and governance')
add('<b>Build.</b> Run <font name="DV-B">cmake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so</font> followed by <font name="DV-B">cmake --build build</font> and <font name="DV-B">ctest --test-dir build --output-on-failure</font>. Run <font name="DV-B">./build/credit_scorecard --models 100 --cases 100 --out reproduced.csv</font>, then run the bundled 80-digit high-precision audit against that CSV.')
table([['Responsibility','Implemented component'],['Synthetic scorecards and native reference','src/credit_scorecard.cpp'],['Reusable paceval graph execution','src/paceval_main.cpp plus compatible external shared engine'],['Numerical high-precision oracle','src/high_precision_reference.py'],['Scientific figures','src/make_figures.py'],['Paper rendering','src/make_whitepaper.py'],['Synthetic sample records','examples/scorecard_samples.csv']])
add('The package includes the supplied paceval_main.h and paceval_main.cpp (public SDK 4.25 facade), with the relative include adjusted for the local src/ directory. The engine shared library is an external runtime dependency and is intentionally not redistributed. The original SDK source copyright and AGPL notices are retained. The SDK-enabled source, including scalar and batch APIs, was compiled and executed with the supplied compatible Linux runtime.')
add('<b>Governance.</b> EBA loan-origination guidelines address creditworthiness assessment and monitoring. Some AI systems used for evaluating natural-person creditworthiness fall within Annex III of Regulation (EU) 2024/1689, subject to the applicable legal provisions. US Regulation B expects specific, accurate principal adverse-action reasons. No compliance is claimed for this arithmetic research project.')
new();head(8,'External references and conclusions')
refs=[
('paceval mathematical engine and C/C++ API','https://paceval.com/api/'),
('paceval public sources and examples','https://github.com/paceval/paceval'),
('EBA loan origination and monitoring guidelines, EBA/GL/2020/06','https://www.eba.europa.eu/activities/single-rulebook/regulatory-activities/credit-risk/guidelines-loan-origination-and-monitoring'),
('EU Artificial Intelligence Act, Regulation (EU) 2024/1689, Annex III','https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng'),
('US CFPB, Regulation B, 12 CFR 1002.9','https://www.consumerfinance.gov/rules-policy/regulations/1002/9/'),
('CFPB circular on adverse-action reasons for complex algorithms','https://www.consumerfinance.gov/compliance/circulars/circular-2022-03-adverse-action-notification-requirements-in-connection-with-credit-decisions-based-on-complex-algorithms/'),
('UCI Statlog German Credit dataset (not included or analyzed)','https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data')]
for i,(label,url) in enumerate(refs,1):story.append(P(f'{i}. <b>{label}</b><br/><font color="#168c9c">{url}</font>','note'))
add('<b>Conclusion.</b> The defined credit-scorecard arithmetic use case has been implemented and executed successfully with the supplied paceval engine. In 100 reusable graphs, all 10,000 scalar and 6,400 batch evaluations agreed with independent native C++ arithmetic within the specified tolerance; an additional 80-digit Decimal audit verified all 10,000 exported scores. The outcome demonstrates numerical feasibility, not calibrated credit-default predictions, regulatory readiness or customer adoption.')

def footer(canvas,doc):
 canvas.saveState();w,h=A4; canvas.setStrokeColor(colors.HexColor('#dbe6e9'));canvas.line(43,38,w-43,38)
 canvas.setFont('DV',7.5);canvas.setFillColor(gray);canvas.drawString(43,26,'paceval. | Reusable Credit Risk Decision Mathematics | Research demonstrator | 2026');canvas.drawRightString(w-43,26,str(doc.page));canvas.restoreState()
doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=43,rightMargin=43,topMargin=32,bottomMargin=56,title='Reusable Credit Risk Decision Mathematics',author='paceval research demonstration')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(target)
