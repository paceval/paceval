#!/usr/bin/env python3
"""Rebuild the evidence-based English WP-010 research report from package files."""
import csv, json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
                               Table, TableStyle, KeepTogether, HRFlowable)
from reportlab.lib.colors import HexColor

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'paceval_Portfolio_Stress_Whitepaper_EN.pdf'
with (ROOT/'examples'/'validation.json').open() as f: RUN=json.load(f)
with (ROOT/'examples'/'independent_audit.json').open() as f: AUDIT=json.load(f)
with (ROOT/'examples'/'risk_metrics.csv').open() as f:
    RISKS={int(row['rule_id']):row for row in csv.DictReader(f)}
# Open-source font is a system dependency for rendering the PDF, not redistributed.
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
fontb='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if Path(font).exists():pdfmetrics.registerFont(TTFont('PaperRegular',font));pdfmetrics.registerFont(TTFont('PaperBold',fontb))
else:font='Helvetica';fontb='Helvetica-Bold'
FONT='PaperRegular' if 'PaperRegular' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
BOLD='PaperBold' if 'PaperBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
NAVY=HexColor('#10344c');CYAN=HexColor('#047c99');MUTED=HexColor('#516a7a');PALE=HexColor('#ecf5f8')
S=getSampleStyleSheet()
S.add(ParagraphStyle(name='Cover',fontName=BOLD,fontSize=22,leading=27,spaceAfter=12,textColor=NAVY))
S.add(ParagraphStyle(name='Lead',fontName=FONT,fontSize=10.7,leading=16,spaceAfter=13,textColor=MUTED))
S.add(ParagraphStyle(name='HOne',fontName=BOLD,fontSize=14.5,leading=19,spaceAfter=11,textColor=NAVY))
S.add(ParagraphStyle(name='HTwo',fontName=BOLD,fontSize=10.7,leading=15,spaceBefore=8,spaceAfter=5,textColor=CYAN))
S.add(ParagraphStyle(name='BodyPaper',fontName=FONT,fontSize=9.0,leading=13.3,spaceAfter=9,textColor=NAVY))
S.add(ParagraphStyle(name='SmallPaper',fontName=FONT,fontSize=8.0,leading=11.2,spaceAfter=6,textColor=MUTED))
S.add(ParagraphStyle(name='FigureCap',fontName=FONT,fontSize=8.2,leading=11.5,spaceAfter=9,textColor=MUTED))
S.add(ParagraphStyle(name='TableHeadP',fontName=BOLD,fontSize=8.5,leading=11,textColor=NAVY))
S.add(ParagraphStyle(name='TableCellP',fontName=FONT,fontSize=8.2,leading=11,textColor=NAVY))
S.add(ParagraphStyle(name='CiteP',fontName=FONT,fontSize=7.7,leading=10.7,textColor=NAVY))

def P(text,style='BodyPaper'):return Paragraph(text,S[style])
def head(text):return P(text,'HOne')
def sub(text):return P(text,'HTwo')
def fig(num,name,caption,width=475):
    from PIL import Image as PILImage
    path=ROOT/'figures'/(name+'.png')
    with PILImage.open(path) as im:w,h=im.size
    return [Image(str(path),width=width,height=width*h/w),
            P(f'<b>Figure {num}.</b> {caption}','FigureCap')]
def table(headers,data,widths=None):
    rows=[[P(str(q),'TableHeadP') for q in headers]]+[[P(str(v),'TableCellP') for v in row] for row in data]
    t=Table(rows,colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),
      ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor('#f8fbfc')]),
      ('LINEBELOW',(0,0),(-1,0),.65,CYAN),('LINEBELOW',(0,1),(-1,-1),.3,HexColor('#d5e4ea')),
      ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
      ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    return t

story=[]
def page():story.append(PageBreak())
# PAGE 1
story += [P('paceval. | SCIENTIFIC RESEARCH DEMONSTRATOR','HTwo'),
          P('Programmable Portfolio Stress-Scenario Mathematics','Cover'),
          P('A validated mathematical execution layer for synthetic cross-factor portfolio P&amp;L, version-controlled rules, and transparent empirical tail-risk metrics.','Lead')]
from PIL import Image as PILImage
hero=ROOT/'figures'/'00_portfolio_stress_hero.png'
with PILImage.open(hero) as im:w,h=im.size
story.append(Image(str(hero),width=498,height=498*h/w));story.append(Spacer(1,11))
story += [P('<b>Scientific question.</b> Can paceval prepare and repeatedly evaluate a governed library of explicit portfolio stress formulas across fixed scenarios while preserving reproducibility and numerical agreement?'),
          P('<b>Observed result.</b> In a controlled synthetic experiment, 100 independently prepared expressions were evaluated over 4,096 distribution scenarios and six separately named stresses. The formulas, scenario P&amp;L, empirical VaR/ES and a selected model update were independently audited.'),
          P('Research status: executed C++/Linux proof of concept, 12 November 2026. No market calibration, regulatory certification, or commercial deployment is implied.','SmallPaper')]
# PAGE 2
page();story += [head('1. Research contribution and implementation boundary'),
 P('WP-010 proposed a fixed portfolio with 100 scenario functions applied to pre-generated shocks. This work implements that research boundary and extends it to a four-factor delta-gamma-cross P&amp;L approximation, separate named stress scenarios, versioned mathematical rules and independently recomputed empirical tail statistics.'),
 P('The paceval library is the <b>mathematical execution component</b>: graph construction and reusable batch calculation. Scenario generation, input policy, risk-statistic aggregation, risk narratives and audit orchestration remain host responsibilities.'),
 *fig(1,'01_execution_architecture','Data-flow boundary between the deterministic C++ host and reusable paceval execution graphs.'),
 sub('Actual integration and reproducibility'),
 P('The official SDK facade <b>src/paceval_main.h</b> and <b>src/paceval_main.cpp</b> is compiled with <b>src/portfolio_stress.cpp</b>. Graphs are prepared with <b>paceval_CreateComputation</b>, checked with <b>paceval_GetIsError</b>, evaluated with <b>paceval_dGetComputationResultExt</b>, and disposed with <b>paceval_DeleteComputation</b> before library shutdown. The Linux runtime itself is supplied externally.'),
 P('The 100 independent graph definitions are published in <b>examples/rules.csv</b>; their computed results and risk reductions are included for full reproduction. The complete CMake project and validation scripts accompany this document.')]
# PAGE 3
page();story += [head('2. Mathematical portfolios, factor units and scenario assumptions'),
 P('Four dimensionless decimal changes represent equity returns <b>eq</b>, absolute interest-rate changes <b>ir</b>, relative FX moves <b>fx</b> and absolute credit-spread changes <b>cr</b>. Coefficients represent synthetic monetary sensitivities, and the model output is synthetic monetary P&amp;L. The portfolio is not a collection of independently re-priced market instruments.'),
 P('<b>General permitted formula:</b> P&amp;L = D<sub>eq</sub>eq + D<sub>ir</sub>ir + D<sub>fx</sub>fx + D<sub>cr</sub>cr + 0.5G<sub>eq</sub>eq<super>2</super> + 0.5G<sub>ir</sub>ir<super>2</super> + 0.5G<sub>cr</sub>cr<super>2</super> + X<sub>eq,fx</sub>eq·fx − H max(0,−eq). Families 0–3 successively add the nonlinear terms. Each rule uses its own fixed, documented coefficients.'),
 *fig(2,'02_factor_shock_distributions','Deterministically generated factor changes (shown in their own characteristic scale units).'),
 P('The scenario generator uses a fixed MT19937-64 seed, a specified Box–Muller transform and an explicit linear dependency structure between factors. It does not estimate a covariance matrix from market observations. Input validation checks finiteness and the declared bounds before evaluation.'),
 P('Six deliberately synthetic named stresses are stored separately in <b>examples/scenario_descriptions.csv</b>. They demonstrate multi-factor extremes but are <b>excluded</b> from the empirical VaR and ES distribution. The source data and all six narratives are disclosed.')]
# PAGE 4
page();story += [head('3. Empirical risk measurements without regulatory claims'),
 P('For each version the host converts portfolio P&amp;L to a loss L = −P&amp;L. The empirical nearest-rank VaR is the sorted loss at rank ceil(pN); ES at 97.5% is the mean of the largest ceil(0.025N) losses. This finite-sample convention is deliberately explicit and is recomputed independently from the exported data.'),
 *fig(3,'03_pnl_distribution','Distribution of synthetic scenario losses and illustrative 95% VaR / 97.5% ES for rule 17.',width=447),
 *fig(4,'04_var_es_across_models','Tail-risk summary across all 100 versioned mathematical rules.',width=447),
 P('The reported metrics are an empirical research diagnostic. They are not Basel FRTB Expected Shortfall capital measures: no liquidity-horizon scaling, stressed-period calibration, modellability tests, portfolio-limit accounting or regulatory aggregation has been attempted.','SmallPaper')]
# PAGE 5
page();story += [head('4. Named stress overlays and risk-factor consistency'),
 P('In addition to the fixed stochastic distribution, six separately identified hypothetical sets of factor shocks are applied to the same reusable rule graphs. Stress outcomes can be inspected directly without contaminating empirical tail statistics or giving the severe scenarios artificial probability weights.'),
 *fig(5,'05_named_stress_scenarios','Synthetic P&amp;L losses from six explicitly defined named cases across all 100 rule versions.'),
 sub('Guidance from external scientific and supervisory sources'),
 P('The Basel Committee stresses relevant risk coverage, coherent scenarios, documented objectives, governance and independent validation. The EBA guidance also calls for internally coherent dependencies between stressed risk factors. Those principles motivate the dataset and audit separation; this toy simulation does not claim to satisfy an institution’s full supervisory stress-testing requirements.'),
 P('Different model families change the loss distribution, but that numerical difference alone does not establish which economic model is valid. Actual portfolio stress testing requires real exposures, market-risk calibration, scenario rationale, governance, and backtesting where applicable.')]
# PAGE 6
page();story += [head('5. Controlled formula versioning and model governance'),
 P('Every mathematical rule is assigned a stable ID, family and version, and is converted to a concrete expression before its execution graph is created. The coefficient inventory is fixed for the published experiment. The C++ program then constructs a new <b>v2</b> of rule 17 after increasing its equity delta sensitivity by 25,000 synthetic monetary units per unit equity return.'),
 *fig(6,'06_version_update_isolation','Change in audited scenario P&amp;L for the deliberately updated rule. Other graph handles remain in service.'),
 P('The replacement graph is created and validated before being used. Rule 18 is re-evaluated before and after the update to ensure an unrelated mathematical rule does not drift. A separate CSV makes the 32 audited v1/v2 output pairs visible.'),
 P('<b>Engineering conclusion:</b> formula identity, versions, approvals and lifecycle are host application responsibilities; paceval supplies stable prepared mathematical computation objects. The program demonstrates a controlled local update, not a production registry, access-control system, or multi-tenant service.')]
# PAGE 7
page();story += [head('6. Independent numerical verification'),
 P('The C++ host independently recalculates every scenario result using a separate native function. Its output is compared with paceval using a stated tolerance of 10<super>−8</super>(1+|reference|). A separate 100-digit Python/MPMath implementation independently recomputes 1,000 selected P&amp;L outcomes and every result in the six named stresses.'),
 *fig(7,'07_numerical_crosscheck','Observed absolute differences between paceval calculations and the independent native C++ reference.'),
 table(['Verification item','Observed outcome'],[
 ('paceval P&amp;L outputs vs C++',f"{RUN['runtime_evaluations']:,} / {RUN['runtime_evaluations']:,} within tolerance"),
 ('Selected P&amp;L vs 100-digit oracle',f"{AUDIT['high_precision_100_digit_pnl_samples']:,} / {AUDIT['high_precision_100_digit_pnl_samples']:,} within tolerance"),
 ('Named stress results vs 100-digit oracle',f"{AUDIT['stress_values_high_precision_checked']:,} / {AUDIT['stress_values_high_precision_checked']:,} within tolerance"),
 ('VaR / ES independently recalculated',f"{AUDIT['empirical_risk_statistics_independently_checked']} / {AUDIT['empirical_risk_statistics_independently_checked']} rules"),
 ('Largest sampled high-precision discrepancy',f"{AUDIT['max_high_precision_sample_abs_discrepancy']:.3e} synthetic monetary units")],widths=[250,245])]
# PAGE 8
page();story += [head('7. Model-family evidence and TINC diagnostic'),
 P('The 100 expressions belong to four distinct, documented approximation families. Their differences are visible in independently calculated risk metrics. These families represent intentionally narrow test kernels and should not be interpreted as a calibrated instrument universe.'),
 *fig(8,'08_formula_family_comparison','The four expression families evaluated over the same fixed scenario distribution.'),
 P('A separate smooth arithmetic graph was evaluated in TINC mode on 24 samples. On the tested runtime the raw endpoints were point intervals and did not contain the 100-digit exact arithmetic reference in the 24 investigated cases. A clearly marked <b>host-side one-binary64-ULP expansion</b> of the reported endpoints contained all 24 references. This remains a finite-sample diagnostic and is not a proof of outward rounding for arbitrary inputs.'),
 P('The TINC diagnostic is <b>not</b> used in the P&amp;L or risk-metric calculation, and no mathematical certification is claimed. The raw outputs and the separate host expansion are published together in <b>examples/tinc_samples.csv</b>.')]
# PAGE 9
page();story += [head('8. Reproduction, scientific limits and references'),
 sub('Reproduce the study on an appropriate Linux host'),
 P('Provide a compatible original paceval Linux shared library outside the repository. Configure CMake with <b>-DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so</b>, then build and execute <b>portfolio_stress --scenarios 4096 --models 100 --batch 512 --seed 20261112 --out results</b>. Run the independent checker with <b>python3 src/validate_outputs.py --folder results</b>. All local source paths and outputs are listed in README.md.'),
 P('The tested configuration used x86-64 Linux, GCC 14.2, Clang 17, 100 prepared expressions, 4,096 distribution scenarios and six named stresses. Different batch sizes and a replay from the exported CSV were also checked. Source code and the exact runtime checksum are supplied in the README. The proprietary shared library is <b>not</b> redistributed.'),
 sub('Limits of inference'),
 P('No market history, actual positions or calibrated shock correlation matrices were used. The synthetic tail statistics do not provide backtested market-risk forecasts or regulatory ES. Formula agreement cannot establish model correctness, risk reduction, predictive usefulness, portfolio hedging benefits, operational safety or faster execution. This paper makes no speed comparisons.'),
 sub('Selected independent and vendor references'),
 P('[1] Basel Committee on Banking Supervision. <i>Stress testing principles</i> (2018); consolidated guidance RMA30 (2026). <link href="https://www.bis.org/committees/bcbs/basel-consolidated-guidelines/module/rma/30" color="#047c99">bis.org / RMA30</link>.','CiteP'),
 P('[2] European Banking Authority. <i>Guidelines on institutions’ stress testing</i> (EBA/GL/2018/04). <link href="https://www.eba.europa.eu/documents/10180/2282644/2b604bc8-fd08-4b17-ac4a-cdd5e662b802/Guidelines%20on%20institutions%20stress%20testing%20%28EBA-GL-2018-04%29.pdf" color="#047c99">eba.europa.eu</link>.','CiteP'),
 P('[3] European Union. Regulation (EU) 2019/876 (CRR II): market risk / Expected Shortfall. <link href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:32019R0876" color="#047c99">EUR-Lex</link>.','CiteP'),
 P('[4] paceval. <i>Official API integration and reusable computation interfaces</i>. Vendor documentation. <link href="https://paceval.com/api/" color="#047c99">paceval.com/api</link>.','CiteP'),
 P('[5] Source research proposal: <i>WP-010 Programmable Portfolio Stress-Scenario Mathematics</i>, supplied November 2026. This paper reports the subsequently executed synthetic experiment; the original proposal alone did not contain these test outcomes.','CiteP')]

def footer(canvas,doc):
 canvas.saveState();width,height=A4
 canvas.setStrokeColor(HexColor('#c5dde6'));canvas.setLineWidth(.5);canvas.line(45,45,width-45,45)
 canvas.setFont(FONT,8.0);canvas.setFillColor(MUTED)
 canvas.drawString(46,32,'paceval. | Portfolio Stress-Scenario Mathematics | Research demonstrator')
 canvas.drawRightString(width-46,32,f'{doc.page}')
 canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=47,rightMargin=47,topMargin=48,bottomMargin=58,
                     title='paceval Portfolio Stress-Scenario Mathematics',author='paceval research demonstrator',
                     subject='Validated synthetic portfolio mathematical execution and empirical stress analysis')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
