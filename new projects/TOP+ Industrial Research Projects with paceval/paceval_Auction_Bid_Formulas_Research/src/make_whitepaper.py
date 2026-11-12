#!/usr/bin/env python3
"""Rebuild the application-focused scientific report from verified paceval CSV data."""
from pathlib import Path
import csv
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Image,Table,TableStyle,PageBreak,Spacer,KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from xml.sax.saxutils import escape
R=Path(__file__).resolve().parents[1]
PDF=R/'paceval_Auction_Bid_Formulas_Whitepaper_EN.pdf'
for name,path in [('Noto','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,path))
navy=colors.HexColor('#18354b');teal=colors.HexColor('#087d87');muted=colors.HexColor('#536575')
ST={
 'cover':ParagraphStyle('cover',fontName='Bold',fontSize=23,leading=30,textColor=navy,spaceAfter=13),
 'h':ParagraphStyle('h',fontName='Bold',fontSize=17,leading=23,textColor=navy,spaceAfter=13),
 's':ParagraphStyle('s',fontName='Bold',fontSize=10.5,leading=15,textColor=teal,spaceBefore=7,spaceAfter=7),
 'b':ParagraphStyle('b',fontName='Noto',fontSize=9,leading=14,textColor=navy,spaceAfter=10),
 'sm':ParagraphStyle('sm',fontName='Noto',fontSize=7.5,leading=11.5,textColor=muted,spaceAfter=6),
 'eq':ParagraphStyle('eq',fontName='Noto',fontSize=9,leading=15,textColor=navy,leftIndent=10,spaceAfter=8)}
story=[]
def H(s):story.append(Paragraph(escape(s),ST['h']))
def S(s):story.append(Paragraph(escape(s),ST['s']))
def P(s):story.append(Paragraph(s,ST['b']))
def M(s):story.append(Paragraph(s,ST['sm']))
def E(s):story.append(Paragraph(escape(s),ST['eq']))
def page():story.append(PageBreak())
def img(name,maxw=480,maxh=255,cap=None):
 fp=R/'figures'/name
 with PILImage.open(fp) as im:w,h=im.size
 sc=min(maxw/w,maxh/h);story.append(Image(str(fp),w*sc,h*sc))
 if cap:M(cap)
def tab(rows,widths=[265,220]):
 data=[[Paragraph(escape(str(c)),ST['sm']) for c in row] for row in rows]
 t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6f2f2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f8f9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.8,teal),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
 story.append(t)
def footer(c,d):
 c.setStrokeColor(colors.HexColor('#bacdd3'));c.line(48,43,A4[0]-48,43)
 c.setFillColor(muted);c.setFont('Noto',7)
 c.drawString(48,30,'paceval | Programmable Auction and Bid Formulas | November 2026')
 c.drawRightString(A4[0]-48,30,str(d.page))
with (R/'examples/offers.csv').open() as f:offers=list(csv.DictReader(f))
elig=sum(int(r['eligible']) for r in offers)
mean=sum(float(r['final_unit_bid_eur']) for r in offers)/len(offers)
margin=sum(float(r['gross_margin_fraction']) for r in offers)/len(offers)
# 1
M('PACEVAL | SCIENTIFIC WHITE PAPER | EXECUTED RESEARCH DEMONSTRATOR')
story.append(Paragraph('Programmable Auction<br/>and Bid Formulas',ST['cover']))
P('<b>Reusable industrial supplier quotation models with controlled mathematical policy versions.</b>')
img('00_auction_hero.png',480,290,'Cover: conceptual illustration of procurement and bidding, not a photograph of a real tender.')
tab([['Recorded technical study','Outcome'],['Mathematical quotation policies','50 versioned formulas in five families'],['Original paceval handles','51 including an immutable policy update'],['Synthetic offer requests','10,000; independent numerical validation passed'],['Scientific 3D parameter sweep','3,721 paceval-calculated points']])
M('The documented workflow uses synthetic procurement values, not verified actual bidding outcomes.')
page()
# 2
H('1. Industrial use case and current state of the art')
P('Industrial suppliers submit commercial quotations to procurement teams through requests for quotation, tenders and reverse auctions. Each offer may involve a negotiated quantity, cost estimate, delivery lead time, risk allowance and contract terms. An internal supplier decision workflow calculates a proposed unit price and may then apply commercial controls such as a price floor or eligibility threshold.')
P('This demonstrator represents a hypothetical component manufacturer submitting quotations under multiple interchangeable pricing policies. Each request contains unit cost, purchase quantity, risk allowance, lead-time estimate, volatility indicator and quantity-discount fraction. The calculation engine produces a proposed EUR-per-item bid. A separate host process applies a synthetic markup floor and a fictitious buyer price ceiling. This shows how mathematical execution and commercial policy can remain separately auditable.')
S('What current research contributes')
P('Combinatorial procurement research considers multiple suppliers, lots, order allocation and transport cost, rather than a single price formula. Abbaas and Ventura (2024) study iterative supplier-selection auctions. Herrmann and Cobo Martín (2024/2025) review the practical adoption gap in tender pricing research. Rottner (2025) analyzes fixed-budget pay-as-bid procurement. These results define an industrial context but are not experimental claims about the present demonstrator.')
P('The project therefore studies reproducible quotation arithmetic. It does not estimate bidder equilibrium, supplier competition, actual award likelihood or profit optimization.')
M('References: Abbaas and Ventura (2024); Herrmann and Cobo Martín (2024/25); Rottner (2025); paceval API. Full URLs are on page 10.')
page()
# 3
H('2. Experimental architecture and application boundary')
P('The research question is whether a portfolio of nonlinear, versioned, deterministic supplier quotation formulas can be implemented as persistent paceval expressions and reused over distinct offers while preserving an explicit boundary between arithmetic and commercial decision logic.')
img('01_architecture.png',480,235,'Figure 1. Actual C++ / paceval responsibilities: offer variables are evaluated in a reusable computation, while policy controls and records remain external.')
tab([['Mathematical engine: paceval','Application: C++ host'],['Register 50 formula versions plus one revision','Generate synthetic offers and check input domain'],['Evaluate expressions for new numerical inputs','Enforce illustrative floor and buyer ceiling'],['Run scalar and packed batch formula calls','Calculate gross margin, totals and eligibility'],['Return deterministic formula outputs','Export reproducible CSV and audit records']])
P('The formula registry is explicit: each paceval computation handle is retained and later reused without reconstructing its expression. A revised first policy is created independently so earlier version results remain reproducible.')
page()
# 4
H('3. Defined mathematical bid models')
P('All proposed bids are unit prices in EUR per item. The inputs are unit cost C and risk R (EUR per item), quantity q (items), lead time L (days), discount d and volatility v (dimensionless). Coefficients a, b, and k are declared per rule. The families share a cost-plus term but differ in risk and volume-adjustment functions.')
E('B1 = C(1+a) + R(1+b*v) - C*d*k*q/(q+100)')
E('B2 = C(1+a) + R(1+b*L^2/900) - C*d*k*q/(q+100)')
E('B3 = C(1+a) + R(1+b*sqrt(1+v^2)) - C*d*k*q/(q+100)')
E('B4 = C(1+a) + R(1+b*v) - C*d*k*ln(1+q)/ln(1001)')
E('B5 = C(1+a) + R(1+b*exp(-L/30)) - C*d*k*q/(q+100)')
P('All expressions are dimensionally well-defined with the stated normalized ratios. In the exported registry, ten coefficient configurations belong to each family. This is a mathematical model of quotations, not a proven behavioral model of auction participants.')
S('Separate host-side business constraints')
E('Final unit bid = max(Bj, 1.03*C)')
E('Gross margin fraction = (Final unit bid - C) / Final unit bid')
E('Quotation total = q * Final unit bid')
P('A binary eligibility flag is true when the final bid does not exceed the synthetic buyer ceiling. A 3% markup floor is distinct from a 3% gross margin and is not represented as an actual supplier contract.')
page()
# 5
H('4. Deterministic dataset and executed SDK integration')
P('The source program creates 50 individual policy graphs from five formula families and ten sets of coefficients. A new version of the first formula is added independently. A deterministic fixed-seed generator produces 10,000 synthetic offers that span costs, quantities, lead times, risk premiums, discounts and volatility. Every policy evaluates 200 scenarios. A separate 61-by-61 parameter grid uses the first policy with remaining parameters fixed.')
tab([['Recorded work item','Executed result'],['Reusable paceval computation handles','51'],['Distinct original quotation policies','50'],['Synthetic offer evaluations','10,000'],['Scalar evaluations including 3D and revisions','13,821'],['Independent packed batch results','1,600'],['3D price-response points','3,721'],['Independent 80-digit decimal samples','500; successful'],['SDK integration with CMake / CTest','1 / 1 passed']],[300,185])
P('The real C++ program calls the provided paceval SDK facade for initialization, expression registration, scalar evaluation, packed evaluation and resource cleanup. A separate native mathematical model and 80-digit decimal reference check the arithmetic independently. Detailed numerical checks remain in technical records, not as C++ versus paceval accuracy charts in this report.')
page()
# 6
H('5. Quotation policies and commercial result summaries')
img('02_unit_bid_policies.png',475,222,'Figure 2. Mean proposed per-item bid across 50 formula configurations, as computed by the executed synthetic supplier requests.')
img('03_buyer_ceiling_eligibility.png',475,210,'Figure 3. Share of synthetic final offers below the hypothetical buyer price ceiling, grouped by pricing rule.')
P(f'Across 10,000 synthetic offer requests, {elig:,} final bids were no higher than their randomly assigned synthetic buyer ceilings. The mean final unit bid was EUR {mean:.2f}. These numbers are properties of the declared deterministic workload and must not be interpreted as auction clearing outcomes or competitive win rates.')
page()
# 7
H('6. Gross-margin scenario and versioning behavior')
img('04_gross_margin.png',470,215,'Figure 4. Indicative gross-margin fractions after the declared unit-cost floor, grouped by versioned policy.')
img('07_versioned_rule.png',470,215,'Figure 7. Two independently created expression versions remain simultaneously available as the quantity changes.')
P(f'The observed mean indicative gross-margin fraction is {margin:.4f} on the sampled synthetic requests. Actual profit depends on omitted operating costs, contractual terms and fulfilled orders. The two versioned curves demonstrate controlled changes in the executable mathematical quotation rule, not automatically improved profitability.')
page()
# 8
H('7. Three-dimensional industrial parameter study')
P('For the first bid rule, quantity and volatility are varied on a fixed 61-by-61 grid while cost, unit risk allowance, discount and lead time are held constant. Every plotted height is a value calculated with the persistent paceval computation handle. This shows how a readable formula can generate a reproducible bid-pricing decision surface.')
img('05_bid_response_surface.png',470,287,'Figure 5. Actual 3D proposed unit-bid surface: quantity and volatility versus calculated EUR per item.')
img('06_bid_contours.png',470,220,'Figure 6. Contour representation of the same executed parameter sweep; colors denote EUR per item.')
page()
# 9
H('8. Synthetic offer population and industrial interpretation')
img('08_cost_bid_scatter.png',475,287,'Figure 8. Each dot is one executed synthetic quotation, with price-ceiling eligibility distinguished from the underlying price formula.')
P('The quotation and total-price outputs can be used as a numerical input layer for supplier pricing support, procurement simulations and controlled policy-scenario analysis. Every output remains connected to its model version and source inputs. In real industrial deployments, policy approval, allowable discount contracts, risk calibration, quality criteria and legal award rules must be managed separately.')
S('Scientific and commercial limitations')
P('All cost distributions, buyer ceilings and policies are synthetic. No actual customer orders, winning auction prices, procurement mechanism equilibria or statistically calibrated bid success models were used. Finite numerical agreement is evidence for the tested code path, not universal exactness or an industrial certification. Price eligibility does not imply winning an auction.')
page()
# 10
H('9. Reproducibility, references and conclusion')
S('Reproduce the mathematical computation')
E('cmake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so')
E('cmake --build build -j && ctest --test-dir build --output-on-failure')
E('./build/auction_bids --out reproduced')
E('python3 src/verify_results.py && python3 src/high_precision_reference.py')
E('python3 src/make_figures.py && python3 src/check_readme_math.py')
P('The sources in src/, frozen records in examples/ and independently created audit files in results/ enable the documented experiment to be re-executed. The original paceval C/C++ facade is supplied, while the compatible shared runtime library remains an external dependency.')
S('Selected references')
for line in [
 'Abbaas and Ventura (2024), Mathematics 12(14), 2228. doi.org/10.3390/math12142228',
 'Herrmann and Cobo Martín (2024/2025), Review of Managerial Science. doi.org/10.1007/s11301-024-00424-1',
 'Rottner (2025), Auctioning Off Budgets in Procurement. doi.org/10.1111/1756-2171.70028',
 'paceval Mathematical Engine C/C++ API: https://paceval.com/api/',
 'paceval public source repository: https://github.com/paceval/paceval']:
 M(line)
S('Research conclusion')
P('The executed study demonstrates that 50 distinct, versioned nonlinear industrial quotation formulas can be represented by reused paceval computation handles and integrated into a deterministic C++ supplier quotation workflow. The resulting bids, eligibility classifications, response surfaces and model-version effects are reproducible within the defined synthetic experimental conditions. No claims about auction optimization or commercial effectiveness are made.')

doc=SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=52,leftMargin=52,topMargin=51,bottomMargin=60)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(PDF)
