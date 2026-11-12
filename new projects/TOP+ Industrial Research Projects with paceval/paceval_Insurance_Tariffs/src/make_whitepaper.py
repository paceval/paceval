#!/usr/bin/env python3
"""Build the publication whitepaper from real exported research data."""
import json
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage
R=Path(__file__).resolve().parents[1];E=R/'examples';F=R/'figures'
AUD=json.loads((E/'high_precision_audit.json').read_text());RUN=json.loads((E/'run_summary.json').read_text())
FONT='/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('ResearchSans',FONT+'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('ResearchSansBold',FONT+'DejaVuSans-Bold.ttf'))
S=getSampleStyleSheet()
S.add(ParagraphStyle(name='H1custom',fontName='ResearchSansBold',fontSize=15,leading=21,textColor=colors.HexColor('#09273e'),spaceAfter=10))
S.add(ParagraphStyle(name='H2custom',fontName='ResearchSansBold',fontSize=11,leading=15,textColor=colors.HexColor('#087a92'),spaceBefore=10,spaceAfter=5))
S.add(ParagraphStyle(name='BodyCustom',fontName='ResearchSans',fontSize=9.2,leading=14,spaceAfter=8))
S.add(ParagraphStyle(name='SmallCustom',fontName='ResearchSans',fontSize=7.5,leading=10,spaceAfter=4))
S.add(ParagraphStyle(name='TitleCustom',fontName='ResearchSansBold',fontSize=23,leading=30,textColor=colors.HexColor('#09273e'),spaceAfter=15))
S.add(ParagraphStyle(name='CaptionCustom',fontName='ResearchSans',fontSize=8,leading=12,textColor=colors.HexColor('#526a79'),spaceBefore=5,spaceAfter=11))
W,H=A4; doc=SimpleDocTemplate(str(R/'paceval_Insurance_Tariffs_Whitepaper_EN.pdf'),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=55,bottomMargin=53,title='paceval High-Volume Insurance Tariff Evaluation',author='paceval research demonstrator')
story=[]
def P(t,style='BodyCustom'):story.append(Paragraph(t,S[style]))
def heading(t):P(t,'H1custom')
def sub(t):P(t,'H2custom')
def chart(file,caption,width=490):
    path=F/file;im=PILImage.open(path);h=int(width*im.height/im.width)
    if h>235:h=235;width=int(h*im.width/im.height)
    story.append(Image(str(path),width=width,height=h));P(caption,'CaptionCustom')
def tbl(data,widths=None):
    data=[[Paragraph(str(v),S['SmallCustom']) for v in row] for row in data]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d9eef4')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f8fa')]),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#087a92')),
    ]));story.append(t);story.append(Spacer(1,13))
def page():story.append(PageBreak())
def decor(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#087a92'))
    canvas.line(48,H-35,W-48,H-35);canvas.line(48,40,W-48,40)
    canvas.setFont('ResearchSans',7.5);canvas.setFillColor(colors.HexColor('#526a79'))
    canvas.drawString(48,27,'paceval | numerical feasibility study | synthetic research data | 12 November 2026')
    canvas.drawRightString(W-48,27,str(doc.page));canvas.restoreState()

# 1. Cover
P('PACEVAL | SCIENTIFIC RESEARCH REPORT','SmallCustom')
P('High-Volume Insurance Tariff Evaluation','TitleCustom')
P('Programmable insurance mathematics • versioned execution graphs • independent numerical validation')
chart('00_insurance_hero.png','Figure 1. Illustrative research workflow. The actual measurements and software implementation are described on the following pages.',width=490)
sub('Verified result')
P(f"The completed C++ study created <b>{AUD['models']}</b> reusable mathematical models and performed <b>{AUD['evaluations_checked']:,}</b> premium calculations on <b>{AUD['policies']:,}</b> synthetic policy records. All evaluations passed an independent 100-digit numerical audit at the specified tolerance. Every rating-vector pair was invariant to a deliberately excluded non-rating tag.")
P('Technical scope: mathematical execution and reproducibility; not a legally approved insurance tariff, real customer quotation, or a general fairness certification.','SmallCustom')
page()

# 2. Motivation
heading('1. Research question and regulatory context')
P('Can a large collection of explicit synthetic insurance tariff formulas be represented as reusable paceval computation graphs, evaluated with changing policy inputs, updated by version, and independently audited without altering the meaning of the mathematical expressions?')
P('The starting five-page proposal WP-013 illustrated premium = b × (1 + a × age) × (1 + c × claim_count). This implementation deliberately defines age as the <b>age of the insured asset</b>, not the age of the insured person. The demonstration extends that baseline to mileage, coverage and deductible and introduces an intentionally narrow paired non-rating tag diagnostic.')
sub('External research and supervisory setting')
P('The Casualty Actuarial Society describes cost-estimation principles used in property and casualty ratemaking. EIOPA (2023) warns against unfair premium differentiation not linked to risk or service costs; its 2025 AI governance Opinion discusses explainability, documentation, fairness and human oversight. EU Test-Achats guidance addresses unisex individual insurance premium calculation. These requirements apply independently of how accurately a mathematical function is executed.')
P('No insurer data, customer pricing, approval status, protected personal attributes or actuarially fitted claim frequencies are included. All observed numeric results come from an explicitly deterministic synthetic workload.')
chart('01_research_workflow.png','Figure 2. Data flow and responsibility boundary: C++ host on both sides of the paceval execution graph.',width=495)
page()

# 3. Formula families
heading('2. Mathematical tariff families')
P('The five paceval input variables are age (insured asset years, 0–25), claims (integer 0–4), km (thousands of km annually, 1–50), cover (synthetic category 1–3), and excess (thousands of EUR, 0–2). All are bounded by input validation before any computation.')
P('For coefficients b, a, c, m, g, h, f that vary by model ID, the four families are:')
tbl([
 ['Family','Exact synthetic mathematical structure'],
 ['F1','b × (1 + a·age) × (1 + c·claims)'],
 ['F2','F1 × (1 + m·(km − 12)/12) × (1 + g·(cover − 1))'],
 ['F3','b × (1 + a·age) × (1 + c·claims) × (1 + g·(cover − 1)) × exp(m·(km − 12)/12) / (1 + h·excess)'],
 ['F4','b × [1 + a·age + c·claims + m·km/12 + g·(cover − 1) + f·age·claims] / (1 + h·excess)'],
],widths=[62,432])
P('All 100 explicit source expressions and coefficients are included in examples/models.csv. They are declared in the SDK only once, then reused over all policy inputs. The actual form of each graph is independent of the nonrating_tag field.')
chart('02_mathematical_families.png','Figure 3. Selected models for one controlled input sweep. The curves represent illustrative rules, not market premium observations.',width=480)
page()

# 4. Architecture
heading('3. Direct paceval C++ integration')
P('The C++17 application includes the supplied official paceval_main.h and compiles paceval_main.cpp directly. CMake links the separately supplied architecture-compatible libpaceval_linux_sharedLIB.so. No custom dynamic symbol loader is used. The published ZIP excludes the external runtime but preserves the original licensing comments in the SDK files.')
P('<b>paceval calls actually used:</b> paceval_InitializeLibrary, paceval_CreateComputation, paceval_dGetComputationResultExt, paceval_dGetComputationResult, paceval_GetIsError, paceval_DeleteComputation and paceval_FreeLibrary. Computation handles are RAII-managed and destroyed before library shutdown.')
P('For each formula, the host assembles fixed-size batches of five floating-point inputs. The graph is evaluated with the SDK batch API; its Boolean return is interpreted according to the SDK convention: true denotes an error. Each result is separately checked against a native C++ function implementing the same family.')
sub('Reproducibility and model governance')
P('A fixed seed creates 512 synthetic rating vectors. Each is duplicated under non-rating tag 0 and 1, yielding 1,024 policy rows. A model record contains its ID, integer version, coefficients and full textual expression. Updating model 17 from v1 to v2 creates a new handle without invalidating model 18 or any unrelated graph.')
chart('05_version_change.png','Figure 4. Reproducible controlled update, with both versions retained for audit.',width=480)
page()

# 5. Numeric evidence
heading('4. Numerical validation and error bounds')
tbl([
 ['Independent verification','Observed result'],
 ['Actual paceval premium evaluations',f"{AUD['evaluations_checked']:,} across {AUD['models']} models and {AUD['policies']:,} rows"],
 ['Native C++ comparison','All within 2 × 10⁻¹⁰ × (1 + |expected|) absolute tolerance'],
 ['100-digit independent arithmetic',f"{AUD['evaluations_checked']:,}/{AUD['evaluations_checked']:,} within 10⁻¹⁰ × (1 + |reference|)"],
 ['Maximum high-precision absolute discrepancy',f"{AUD['max_abs_difference']:.4g} EUR"],
 ['Counterfactual non-rating tag pair differences','All zero in these 512 synthetic pairs and 100 models'],
 ['Smooth-control TINC raw intervals',f"{AUD['tinc_reference_included']}/{AUD['tinc_raw_intervals_checked']} contain independent references"],
],widths=[210,284])
P('The independent Python reference uses mpmath at 100 decimal digits, with every CSV numerical input first parsed as a binary64 value and then converted exactly to high precision. It computes the four tariff families separately from the paceval parser and C++ native reference. A strict assertion rejects any result outside the prescribed tolerance.')
chart('04_native_validation.png','Figure 5. All recorded premium results satisfy the independent native comparison criterion.',width=480)
page()

# 6. Portfolio distribution
heading('5. Synthetic tariff portfolio examination')
P('The synthetic records are not drawn from real claims data and do not contain protected personal attributes. Pricing values are meaningful only in the constructed example; their distribution is a software demonstration and cannot be interpreted as calibrated loss cost, customer fairness or commercial premium adequacy.')
chart('03_premium_distribution.png','Figure 6. Actual output distribution for one formula over the exported synthetic policy records.',width=472)
chart('07_model_family_comparison.png','Figure 7. Differences among model family averages reflect chosen synthetic coefficients, not actual insurer risk estimates.',width=472)
page()

# 7. Counterfactual tag
heading('6. Input validation and bounded fairness diagnostics')
P('The C++ host rejects nonfinite numeric inputs, asset ages outside 0–25, non-integer or out-of-range claims, mileage outside 1–50 thousand km/year, invalid coverage codes and deductibles outside 0–2 thousand EUR. Malformed CSV rows and broken tag pairs are also rejected.')
P('For a controlled paired sensitivity audit, the demonstration creates two policy rows with identical five rating inputs and opposite nonrating_tag values. The tag is excluded from the paceval variable declaration and from all four expression families. Across all 100 models and 512 pairs, observed premium differences are exactly zero.')
P('This result checks only explicit tag invariance of the implemented functions. It does not rule out indirect discrimination through proxies, assess price walking or certify fairness under EU law. Such assessments require appropriate substantive claims data, relevant protected-group analysis where lawful, and independent legal/actuarial governance.')
chart('06_paired_tag_invariance.png','Figure 8. Observed invariance for deliberately controlled, equal-input synthetic pairs.',width=472)
page()

# 8. TINC
heading('7. Separate TINC diagnostic and reproducibility')
P('As an additional diagnostic, the project creates a separate TINC computation graph for the smooth polynomial age² + claims² and tests 24 points. Both input variables are exact small integers in these samples. Every unmodified raw interval contains the high-precision polynomial result. This control test is deliberately separate from the insurance tariff formulas; it is not a formal guarantee about arbitrary TINC results.')
chart('08_tinc_sample_audit.png','Figure 9. Raw TINC sample intervals and independently computed exact polynomial references.',width=470)
sub('How to reproduce')
P('Build src/insurance_tariffs.cpp and src/paceval_main.cpp with the provided src/CMakeLists.txt and an external compatible Linux paceval runtime. Run insurance_tariffs with --models 100 --pairs 512 --batch 128 --seed 20261112 --out run, then run python3 src/high_precision_reference.py run. The repository includes source scripts, CSV results, a JSON summary and eight diagrams in PNG/SVG formats.')
P('GCC and Clang builds, CTest validation, invalid-input rejection, batch invariance and a fresh ZIP extraction/rebuild are included in the release verification procedure.')
page()

# 9. Sources
heading('8. References and boundaries')
P('<b>Source of the case:</b> WP_013_High_Volume_Insurance_Tariff_Evaluation.pdf (user-supplied five-page scientific research proposal, November 2026). The present document extends its synthetic mathematical workload; it is not a measured performance study.')
sources=[
 ('Official paceval C/C++ API','https://paceval.com/api/'),
 ('CAS — P&C Insurance Ratemaking Principles','https://www.casact.org/statement-principles-regarding-property-and-casualty-insurance-ratemaking'),
 ('EIOPA — differential pricing supervisory statement, 2023','https://www.eiopa.europa.eu/publications/supervisory-statement-differential-pricing-practices-non-life-insurance-lines-business_en'),
 ('EIOPA — Opinion on AI governance and risk management, 2025','https://www.eiopa.europa.eu/eiopa-publishes-opinion-ai-governance-and-risk-management-2025-08-06_en'),
 ('EUR-Lex — Test-Achats/unisex insurance guidance','https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52012XC0113(01)'),
]
for name,url in sources:P('<b>'+name+'</b>: '+url,'SmallCustom')
sub('Scientific and publication limits')
P('The empirical result is successful mathematical computation of synthetic tariff expressions with reproducible numerical and versioning checks. The work provides no evidence that the sample pricing factors are actuarially adequate or legally permissible in a particular jurisdiction. It does not establish security of real customer data, absence of proxy discrimination, suitability of an underwriting decision or commercial performance benefits.')
P('The source package contains commented C++ code, official SDK facade files, Python reference tests, deterministic synthetic datasets, and all cited local diagrams. No performance speedups or hardware acceleration claims are reported. No proprietary Linux runtime library or separate LICENSE_NOTICE.md is included.')

doc.build(story,onFirstPage=decor,onLaterPages=decor)
print('Whitepaper written to',R/'paceval_Insurance_Tariffs_Whitepaper_EN.pdf')
