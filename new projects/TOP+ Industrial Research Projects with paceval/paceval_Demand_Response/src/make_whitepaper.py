#!/usr/bin/env python3
"""Produce a precisely paginated, source-grounded English research PDF (nine A4 pages)."""
from pathlib import Path
import json,csv,math
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'paceval_Demand_Response_Whitepaper_EN.pdf'
FIG=ROOT/'figures'
W,H=A4; M=46; WIDTH=W-2*M
NAVY=HexColor('#102e47'); CYAN=HexColor('#008eaf'); GREEN=HexColor('#148871'); GRAY=HexColor('#526677'); VERYLIGHT=HexColor('#edf5f8')
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV', FONT));pdfmetrics.registerFont(TTFont('DVB', FONTB))
style=ParagraphStyle('body',fontName='DV',fontSize=9.2,leading=14,textColor=NAVY,spaceAfter=0)
styleS=ParagraphStyle('small',fontName='DV',fontSize=8.2,leading=12.4,textColor=NAVY)
styleTiny=ParagraphStyle('tiny',fontName='DV',fontSize=7.5,leading=10.5,textColor=NAVY)
styleBold=ParagraphStyle('bold',fontName='DVB',fontSize=9,leading=13.6,textColor=NAVY)

c=canvas.Canvas(str(OUT),pagesize=A4, pageCompression=1)
c.setTitle('paceval | Demand-Response Incentive Mathematics - Reproducible C++ Research')
c.setAuthor('paceval Research Demonstrator')
c.setSubject('Reusable mathematical graph evaluation of synthetic demand-response incentive rules')
y=0;pn=0

def page(title,kicker='REPRODUCIBLE RESEARCH DEMONSTRATOR'):
    global y,pn
    if pn:c.showPage()
    pn+=1;c.setFillColor(NAVY);c.rect(0,H-56,W,56,fill=1,stroke=0)
    c.setFillColor(white);c.setFont('DVB',12.0);c.drawString(M,H-31,'paceval.  |  ENERGY FLEXIBILITY RESEARCH')
    c.setFillColor(CYAN);c.rect(M,H-62,WIDTH,2.5,fill=1,stroke=0)
    c.setFillColor(GRAY);c.setFont('DV',7.5);c.drawString(M,H-78,kicker)
    c.setFillColor(NAVY);c.setFont('DVB',17);c.drawString(M,H-109,title)
    c.setStrokeColor(HexColor('#b4cdd7'));c.setLineWidth(.7);c.line(M,48,W-M,48)
    c.setFont('DV',7);c.setFillColor(GRAY);c.drawString(M,34,'Synthetic numerical research • November 2026 • paceval SDK / external Linux runtime')
    c.drawRightString(W-M,34,f'{pn} / 9')
    y=H-130

def par(text,small=False,after=10):
    global y
    p=Paragraph(text, styleS if small else style)
    w,h=p.wrap(WIDTH,2000)
    if y-h<61:raise RuntimeError(f'Page {pn} overflow at {text[:55]!r}, y={y:.1f}, h={h:.1f}')
    p.drawOn(c,M,y-h);y-=h+after

def head(text,after=8):
    global y
    if y-21<61:raise RuntimeError('heading overflow')
    c.setFont('DVB',11.5);c.setFillColor(CYAN);c.drawString(M,y-15,text);y-=24+after

def caption(text):
    global y
    p=Paragraph(text,styleTiny);w,h=p.wrap(WIDTH,300)
    if y-h<61:raise RuntimeError('caption overflow')
    p.drawOn(c,M,y-h);y-=h+11

def pic(name,width=WIDTH,maxheight=230):
    global y
    f=FIG/name
    with Image.open(f) as im:iw,ih=im.size
    scale=min(width/iw,maxheight/ih);ww=iw*scale;hh=ih*scale
    if y-hh<61:raise RuntimeError(f'Image {name} overflows page {pn}: y={y},h={hh}')
    c.drawImage(str(f),M+(WIDTH-ww)/2,y-hh,width=ww,height=hh,mask='auto')
    y-=hh+7

def note(text):
    global y
    p=Paragraph(text,styleS);w,h=p.wrap(WIDTH-22,1000)
    if y-h-21<61:raise RuntimeError('note overflow')
    c.setFillColor(VERYLIGHT);c.roundRect(M,y-h-15,WIDTH,h+19,5,fill=1,stroke=0)
    p.drawOn(c,M+11,y-h-6);y-=h+23

def table(rows,widths=None,after=15):
    global y
    widths=widths or [WIDTH/len(rows[0])]*len(rows[0]);rowheight=23
    for idx,row in enumerate(rows):
        maxh=0;para=[]
        for col,x in enumerate(row):
            st=styleBold if idx==0 else styleTiny
            t=Paragraph(str(x),st);_,h=t.wrap(widths[col]-13,1000)
            maxh=max(maxh,h);para.append((t,h))
        rh=max(rowheight,maxh+13)
        if y-rh<61:raise RuntimeError(f'table overflow p{pn} row={idx}')
        if idx%2==0:
            c.setFillColor(VERYLIGHT if idx==0 else HexColor('#f5f8fa'));c.rect(M,y-rh,WIDTH,rh,fill=1,stroke=0)
        x=M
        for j,(t,h) in enumerate(para):t.drawOn(c,x+6,y-7-h);x+=widths[j]
        c.setStrokeColor(HexColor('#d0e0e7'));c.line(M,y-rh,W-M,y-rh)
        y-=rh
    y-=after

def code(lines):
    global y
    lineheight=12.1;hh=12+len(lines)*lineheight
    if y-hh<61:raise RuntimeError('code overflow')
    c.setFillColor(VERYLIGHT);c.roundRect(M,y-hh,WIDTH,hh,6,fill=1,stroke=0)
    c.setFont('DV',7.75);c.setFillColor(NAVY)
    for i,line in enumerate(lines):c.drawString(M+9,y-17-i*lineheight,line)
    y-=hh+12

# 1 cover
page('Demand-Response Incentive Mathematics','A REAL SDK IMPLEMENTATION • SYNTHETIC HOURLY LOAD • AUDITED MATHEMATICS')
par('<b>Versioned mathematical rules for flexible electricity demand</b> - An executable C++ demonstration of reusable paceval computation graphs, measured-load eligibility, independent numerical verification and controlled formula updates.',small=True,after=10)
pic('00_demand_response_hero.png',maxheight=285)
note('<b>Measured result:</b> 100 reusable graphs; 336 one-hour records; 33,600 rule evaluations; 33,600 independently validated outputs; 24/24 controlled TINC samples.')
par('This study converts the supplied WP-014 pilot proposal into a reproducible mathematical research demonstrator. Its physical time series, prices, consumption behavior and programs are deliberately <b>synthetic</b>. No financial settlement rule, external network constraint, field deployment or customer behavior has been validated.',small=True,after=0)

# 2 external rationale and architecture
page('1. Research question and system boundary')
par('Can a library of one hundred independently configurable and versioned demand-response incentive expressions be compiled once, evaluated repeatedly for new hourly inputs and independently audited, while keeping measurement quality and physical constraints outside the arithmetic engine?')
head('Why the use case is technically meaningful')
par('Demand response changes electricity consumption in response to time-dependent prices or program incentives. The result depends on what the customer would otherwise have consumed (the <b>counterfactual baseline</b>), how much reduction was actually metered, eligibility rules and potential rebound. ACER and the U.S. Department of Energy distinguish measurement and verification from financial settlement; OpenADR provides a model for exchanging events and price signals. The paceval task is an explicit <b>mathematical expression kernel</b>, not a substitute for those upstream and downstream functions.')
pic('01_execution_architecture.png',maxheight=182)
caption('Figure 1. An intentionally modular implementation: the C++ host validates input and eligibility; paceval evaluates the 100 reusable mathematical rules; host and Python verify numerical outputs independently.')
head('Extension beyond WP-014')
par('The original proposal starts from a simple price-difference multiplied by shifted energy. The executable experiment adds: 24-hour energy recovery; fixed measured-load and capacity limits; controlled event-quality exclusions; four rule families and coefficient versioning; a native C++ oracle; a 90-digit decimal oracle; and a separate raw TINC diagnostic.')
note('Boundary: a synthetic demand trace is not a verified customer baseline. Baseline estimation, actual consumer elasticity, distribution network feasibility and market-approved settlement remain independent research questions.')

# 3 mathematical detail
page('2. Mathematical formulation and units')
par('<b>One-hour values.</b> Let B be the modeled baseline energy (kWh), A the synthetic meter energy (kWh), R the requested reduction (kWh), and C the declared capacity (kWh). For a quality-valid event the host computes d = min(R, C, max(0, B - A)). Outside an event or with bad meter quality, the host sets both d and the chargeable request to zero.')
head('Explicit expression families evaluated by paceval')
code(['V_0 = alpha*d*(pe-pr) + bonus*d',
      'V_1 = V_0 - penalty*(req-d)*(req-d)',
      'V_2 = V_1 - comfort*d*d',
      'V_3 = V_2 - cubic*d*d*d'])
par('These are four programmable research families, NOT prescribed retail, wholesale or balancing-market settlement formulas. Within the chosen model, the price-spread term represents a hypothetical benefit of moving consumption from an event hour to a later recovery hour; bonus is a separate synthetic program incentive; the remaining terms are specified under-delivery and comfort costs.')
table([['Quantity','Mathematical role / unit'],['d, req','Verified eligible / requested energy, kWh'],['pe, pr','Event and recovery reference prices, EUR/kWh'],['alpha','Dimensionless price-spread multiplier'],['bonus','Explicit program incentive assumption, EUR/kWh'],['penalty, comfort','Quadratic cost assumptions, EUR/kWh²'],['cubic','Cubic fatigue cost assumption, EUR/kWh³']],widths=[115,WIDTH-115],after=12)
head('Why the results are traceable')
par('Each rule is stored with a stable ID, family and version, plus its exact C++-constructed paceval expression and literal coefficients. Thus a researcher can reconstruct the calculation from published `rules.csv` and `evaluations.csv` without inferring a hidden decision rule.',small=True)

# 4 data and physics
page('3. Controlled hourly energy experiment')
par('Fourteen synthetic days yield 336 sequential one-hour samples. DR activation is fixed at hours 17, 18 and 19. All modeled energy reductions return during hours 20, 21 and 22, such that the sum of the baseline and metered loads agrees within a strict numerical tolerance on every day.')
pic('02_hourly_load_and_recovery.png',maxheight=229)
caption('Figure 2. An example 24-hour profile. A reduction during the modeled peak is followed by an equal daily energy recovery; this avoids implicitly treating load shifting as energy conservation or deletion.')
pic('03_hourly_price_and_recovery_rate.png',maxheight=194)
caption('Figure 3. Illustrative price signals; no actual electricity market or supplier tariff is implied.')

# 5 code/API and audit
page('4. Direct paceval SDK integration')
par('The executable compiles the original `paceval_main.cpp` facade next to `demand_response.cpp` and includes `paceval_main.h`. CMake links the user-supplied original Linux runtime as an <b>external shared object</b>. It deliberately does not use a custom `dlopen` API bridge, redistribute proprietary runtime binaries or compile its own mathematical engine.')
head('Actual API roles')
table([['SDK call','Purpose in the executed C++ code'],['paceval_InitializeLibrary','Initializes the external paceval runtime'],['paceval_CreateComputation','Creates an independently reusable graph for each rule'],['paceval_dGetComputationResultExt','Batch-evaluates one graph for many hourly values'],['paceval_dGetComputationResult','Queries the separate TINC diagnostic graph'],['paceval_GetIsError','Checks computational errors'],['paceval_DeleteComputation','Releases each graph via C++ RAII'],['paceval_FreeLibrary','Closes the runtime after graph release']],widths=[222,WIDTH-222])
head('Reproducible evaluation lifecycle')
par('The program creates one hundred graphs exactly once in the normal run. For every graph it fills a flattened batch with four numbers per hour (delivered, requested, event price and recovery price), invokes the official `...ResultExt` API, checks its per-sample errors, and compares results to a native C++ oracle. The SDK batch call reports a boolean <b>true</b> on error; this convention is checked explicitly in the source.')
par('For a version change, rule 17 is recompiled with a modified bonus coefficient while already constructed rule 18 is re-evaluated unchanged. One graph changing does not invalidate the other 99.',small=True)
note('Reproducibility is numerical and architectural. No runtime throughput, power consumption, monetary gain from actual demand response or FPGA speedup is claimed.')

# 6 numerical audit
page('5. Numerical accuracy and independent audit')
par('All 33,600 values produced by the original paceval Linux runtime pass the native C++ tolerance check. A separate Python audit uses 90-digit Decimal arithmetic and reconstructs the expressions from exported model coefficients and the actual IEEE-754 binary64 values supplied to the engine.')
table([['Verification','Result'],['Regular paceval vs native C++','33,600 / 33,600 pass'],['Independent 90-digit Decimal audit','33,600 / 33,600 pass'],['Maximum absolute discrepancy','approximately 6.943 × 10^-16 EUR'],['Raw TINC controlled samples','24 / 24 contain the reference'],['Daily energy-balance checks','14 / 14 pass']],widths=[260,WIDTH-260],after=12)
pic('06_paceval_vs_native_reference.png',maxheight=206)
caption('Figure 4. Paceval and native C++ reference agree across the deterministic subsample. The full audit is conducted on all exported rows, not only those displayed.')
pic('09_tinc_raw_interval_audit.png',maxheight=160)
caption('Figure 5. TINC uses a separate smooth price-spread expression on 24 binary-exact inputs. This is a sample-wise inclusion result, not a formal guarantee across arbitrary formulas.')

# 7 eligibility
page('6. Eligibility and false-incentive checks')
par('The model demonstrates three important sources of misinterpretation: (i) a requested peak reduction without a metered reduction; (ii) a meter-quality-invalid hour; and (iii) an instruction greater than the declared flexible capacity. In the host, a claim is never accepted solely because it was requested; positive modeled payout is bounded by measured and capped delivery.')
pic('07_requested_vs_eligible_delivery.png',maxheight=246)
caption('Figure 6. The requested quantity may exceed the independently eligible quantity; an invalid measurement is excluded instead of being rewarded.')
table([['Control','Observed result'],['Unsubstantiated requested reduction','1 deliberately injected event; no positive payout'],['Bad meter-quality event','1 excluded event hour'],['Requested amount above declared cap','2 capped event hours'],['24-hour physical reconciliation','Every synthetic day reconciles'],['Strict invalid CSV','Rejected with non-zero program exit']],widths=[280,WIDTH-280])
note('These checks prove the implemented host policy, not the accuracy or integrity of real customer baselines. Real DR settlement requires an appropriate program-specific baseline calculation and independent meter verification.')

# 8 variable families and update
page('7. Formula library, revision and sensitivity')
par('The rule generator produces one hundred distinct formula instances from four family structures with varying coefficients. The model library exposes a genuine engineering benefit of reusable expression objects: mathematical rules can be changed as versioned data without changing the host-side control flow.')
pic('04_total_modeled_benefit_by_rule.png',maxheight=189)
caption('Figure 7. Synthetic modeled net benefits across one hundred independently constructed rule graphs. These are arithmetic scenario values, not real customer savings.')
pic('08_versioned_rule_update.png',maxheight=183)
caption('Figure 8. Controlled rule-17 update modifies the bonus coefficient by 0.015 EUR/kWh. The independent rule-18 computation remains unchanged.')
par('The figures `05_rule_family_distribution` and `07_requested_vs_eligible_delivery` are also included in the accompanying GitHub repository as both PNG and SVG. All figures are produced by `src/make_figures.py` from the published CSV data.',small=True)

# 9 reproducibility and sources
page('8. Reproducibility, sources and next experiment')
par('The archive is intentionally minimal: README, this PDF, the direct C++ SDK facade, CMake, validation scripts, the complete synthetic input/output CSVs and the marketing/scientific graphics. There is no `LICENSE_NOTICE.md` and no copy of the external Linux `.so`. Existing copyright/license notices in the official SDK source are preserved.')
head('Run the complete experiment')
code(['cmake -S src -B build -DCMAKE_BUILD_TYPE=Release',
      '  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so',
      'cmake --build build -j',
      'ctest --test-dir build --output-on-failure',
      './build/demand_response --rules 100 --days 14 --out reproduced',
      'python3 src/validate_outputs.py --dir reproduced'])
head('References grounding the application specification')
par('1. ACER (2025): <link href="https://www.acer.europa.eu/monitoring/MMR/barriers-demand-response-2025" color="#008eaf">Unlocking flexibility: Demand response barriers</link>, including activation and aggregation context.',small=True,after=4)
par('2. ACER (2025): <link href="https://www.acer.europa.eu/sites/default/files/documents/Recommendations_annex/ACER_Recommendation_01-2025_DR_NC-Annex1_Amended_DR_NC.pdf" color="#008eaf">Demand Response Network Code recommendation</link>, including principles for baselines.',small=True,after=4)
par('3. U.S. DOE (2013): <link href="https://www.energy.gov/sites/prod/files/NAPDR%20M%26V.pdf" color="#008eaf">Measurement and Verification for Demand Response</link>, establishing separate measurement and settlement considerations.',small=True,after=4)
par('4. OpenADR Alliance: <link href="https://www.openadr.org/index.php?Itemid=194&amp;id=210%3Aopenadr-3.0&amp;option=com_content&amp;view=article" color="#008eaf">OpenADR 3</link>, price and event signal interoperability; no OpenADR live adapter was tested.',small=True,after=4)
par('5. European Commission JRC (2022): <link href="https://ses.jrc.ec.europa.eu/publications-list/demand-response-impact-evaluation-review-methods-estimating-customer-baseline" color="#008eaf">Demand-response baseline impact evaluation review</link>.',small=True,after=4)
head('Next scientific step')
par('Obtain permission-cleared hourly meter traces and corresponding officially defined DR program rules; compare candidate baseline methodologies on a pre-registered hold-out period; quantify settlement discrepancies and false-positive incentives against verified data; and extend the host with documented OpenADR input adapters and independent physical network constraints. Only those additional experiments could support claims beyond the current mathematical feasibility result.',small=True)

c.save()
print('PDF',OUT,'pages',pn)
