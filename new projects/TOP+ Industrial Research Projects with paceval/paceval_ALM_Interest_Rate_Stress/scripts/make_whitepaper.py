#!/usr/bin/env python3
"""Standalone report, compiled only from recorded original paceval data and cited context."""
from pathlib import Path
import json, pandas as pd, os
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.colors import HexColor,white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from PIL import Image as PILImage
p=Path(__file__).resolve().parents[1];res=p/'results';fig=p/'figures';pdf=p/'paceval_ALM_Interest_Rate_Stress_Whitepaper_EN.pdf'
try:
 pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
 pdfmetrics.registerFont(TTFont('DejaVuBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
except:pass
f='DejaVu';bold='DejaVuBold';navy=HexColor('#162d4c');blue=HexColor('#2579b1');gold=HexColor('#a76d22');slate=HexColor('#41556b');muted=HexColor('#6d7d8e')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='H1X',fontName=bold,fontSize=17,leading=22,spaceAfter=13,textColor=navy))
styles.add(ParagraphStyle(name='H2X',fontName=bold,fontSize=11.6,leading=15,spaceBefore=9,spaceAfter=6,textColor=blue))
styles.add(ParagraphStyle(name='BodyX',fontName=f,fontSize=9,leading=14,spaceAfter=9,textColor=slate))
styles.add(ParagraphStyle(name='TinyX',fontName=f,fontSize=7.6,leading=11.5,spaceAfter=7,textColor=muted))
styles.add(ParagraphStyle(name='CaptionX',fontName=f,fontSize=8.3,leading=12,textColor=slate,spaceBefore=7,spaceAfter=12))
styles.add(ParagraphStyle(name='EqX',fontName=f,fontSize=9,leading=15,textColor=navy,leftIndent=18,spaceBefore=8,spaceAfter=12))
styles.add(ParagraphStyle(name='TtlX',fontName=bold,fontSize=23,leading=29,textColor=navy,spaceAfter=15))
styles.add(ParagraphStyle(name='SubtitleX',fontName=f,fontSize=12,leading=18,textColor=blue,spaceAfter=13))

def para(t,style='BodyX'):return Paragraph(t,styles[style])
def h(t):return para(t,'H1X')
def sub(t):return para(t,'H2X')
def page():story.append(PageBreak())
def foot(canvas,doc):
 canvas.saveState();w,h=A4
 canvas.setStrokeColor(HexColor('#d7e0ea'));canvas.line(18*mm,17*mm,w-18*mm,17*mm)
 canvas.setFont(f,7.5);canvas.setFillColor(muted)
 canvas.drawString(18*mm,12*mm,'paceval. | Independent mathematical research | 15 November 2026')
 canvas.drawRightString(w-18*mm,12*mm,f'WP 33  •  {doc.page}')
 if doc.page>1:
  canvas.setFont(bold,8.2);canvas.setFillColor(navy);canvas.drawString(18*mm,h-16*mm,'ASSET–LIABILITY CASH FLOW AND RATE STRESS')
  canvas.setStrokeColor(HexColor('#d7e0ea'));canvas.line(18*mm,h-19*mm,w-18*mm,h-19*mm)
 canvas.restoreState()
doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=24*mm,bottomMargin=22*mm,title='paceval | Asset-Liability Cash Flow and Interest-Rate Stress Kernels',author='paceval mathematical research demonstrator')
aw=A4[0]-36*mm
story=[]
def figure(number,name,title,caption):
 path=fig/f'fig{number:02d}_{name}.png'
 im=PILImage.open(path);rw,rh=im.size;maxw=aw;maxh=156*mm
 scale=min(maxw/rw,maxh/rh)
 story.append(Spacer(1,7*mm));story.append(Image(str(path),width=rw*scale,height=rh*scale))
 story.append(para(f'<b>Figure {number}.</b> {caption}','CaptionX'))

def tab(rows,colwidths=None):
 rr=[[para(str(z),'TinyX') for z in row] for row in rows]
 t=Table(rr,colWidths=colwidths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('TEXTCOLOR',(0,0),(-1,0),white),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#f2f6fa'),white]),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.25,HexColor('#dbe3eb')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 story.append(t)

evidence=json.loads((res/'execution_evidence.json').read_text());hp=json.loads((res/'high_precision_audit.json').read_text());iv=json.loads((res/'invariant_audit.json').read_text())
s=pd.read_csv(res/'scenario_summary.csv');by={(r.model,r.scenario):r for r in s.itertuples()};base=by['V2','BASE'];down=by['V2','PARALLEL_DOWN'];flat=by['V2','FLATTENER'];steep=by['V2','STEEPENER']
# COVER
story.append(Spacer(1,8*mm));story.append(para('PACEVAL. FINANCIAL MATHEMATICS','SubtitleX'))
story.append(para('Asset–Liability Cash Flows and Interest-Rate Stress Kernels','TtlX'))
story.append(para('A reproducible, independently checked C++ mathematical demonstrator using the original paceval SDK 4.25','SubtitleX'))
cover=fig/'00_alm_financial_cover.png';story.append(Image(str(cover),width=aw,height=aw/2));story.append(Spacer(1,7*mm))
story.append(para('<b>Research status:</b> Original SDK executed on deterministic synthetic EUR cash flows. No bank deployment, regulatory certification or actual market portfolio is claimed.'))
story.append(para('15 November 2026  |  Working paper WP 33  |  Independent research study','TinyX'))
page()
# 2
story.append(h('1. Industrial problem and why it matters'))
story.append(para('A bank or insurer receives dated cash flows from assets while paying principal, coupons, deposits, annuities and other obligations. The timing of those payment streams is rarely identical. Revaluing them at a yield curve produces an economic-value perspective on the mismatch. A positive present-value balance on one day can change sign under adverse interest-rate movements, especially when asset and liability maturities differ.'))
story.append(para('A hypothetical treasury team therefore wants to evaluate identical contractual payments against a set of shocked term structures. The inputs are the cash-flow date or year fraction, EUR amount, asset/liability side and a defined zero-rate curve. The outputs are discounted values, the asset–liability net economic value, duration and convexity indicators, maturity buckets and a record of scenario sensitivity.'))
story.append(para('The role of paceval is intentionally narrower than an ALM platform: it executes the mathematically explicit pricing, derivative, rate-shock, comparison and guard formulas, while the C++ host handles variable-length aggregation, data validation and scenarios. A real ALM system would also forecast rate-sensitive cash flows, calibrate market curves, handle optionality, governance, accounting and supervisory definitions.'))
story.append(sub('Practical financial workflow'))
story.append(para('Validated dated obligations and assets → selected zero-rate curve and stress parameters → persistent paceval graphs → row-level discounted cash flows and sensitivities → C++ aggregation → paceval portfolio metrics → documented research-only classification.'))
page()
# 3
story.append(h('2. Contemporary methods and supervisory context'))
story.append(para('The Basel Committee revised interest-rate risk in the banking book (IRRBB) shock calibration on 16 July 2024. The revised Basel framework is effective from 1 January 2026 and distinguishes economic-value (EVE) and earnings (NII) measurement. The prescribed standardized EVE shocks include parallel up/down, steepener, flattener and short-rate up/down shapes. The actual currency-specific shock coefficients and supervisory models are not copied into the research experiment [1–3].'))
story.append(para('The European Central Bank’s December 2024 SREP methodology likewise treats interest-rate risk as a combination of economic-value and earnings considerations [4]. Insurers use a distinct framework: EIOPA supplies risk-free term structures and updated technical documentation, most recently on 6 November 2026 at the time of this report [5].'))
story.append(para('Contemporary quantitative software such as OpenGamma Strata offers calibrated curve and PV sensitivity services; QuantLib supports instrument-based bootstrapping and interpolated term structures [6–7]. This project does not compare unmeasured performance with these libraries. It tests a separable mathematical function-execution kernel that can be embedded in broader applications.'))
story.append(sub('Scope of the actual research experiment'))
story.append(para('The eight scenario labels resemble familiar ALM risk analyses, but their numerical amplitudes are research choices. They are neither Basel-prescribed EUR shock sizes nor EIOPA reference curves. The output is a fixed-cashflow valuation and analytic sensitivity study, not a standardized IRRBB SOT or Solvency II calculation.'))
page()
# 4
story.append(h('3. Mathematical construction'))
story.append(para('Both versions use a smooth continuously compounded illustrative EUR zero-rate function of maturity t, with t and the time constant τ measured in years:'))
story.append(para('r₀(t) = L + S[1 − exp(−t/τ)] + H(t/τ) exp(−t/τ)','EqX'))
story.append(para('Version V1 adds a parallel rate displacement: r₁(t) = r₀(t) + p. Version V2 adds distinct short- and long-tenor factors: r₂(t) = r₀(t) + p + s exp(−t/4) + ℓ[1 − exp(−t/4)]. The time scale 4 years is a declared synthetic shape convention. Both version graphs are retained independently and evaluated on the same contractual cash-flow records.'))
story.append(para('For a positive nominal cash flow CFᵢ due at maturity tᵢ, the discounted amount and its first two parallel-rate derivatives are:'))
story.append(para('PVᵢ = CFᵢ exp[−tᵢ r(tᵢ)]','EqX'))
story.append(para('∂PVᵢ/∂p = −tᵢPVᵢ     and     ∂²PVᵢ/∂p² = tᵢ²PVᵢ.','EqX'))
story.append(para('Net PV gap equals the sum of discounted asset payments minus discounted liabilities. Duration is the cash-flow-PV-weighted mean maturity on each side; the net parallel DV01 is 0.0001 times the derivative of the PV gap. The short- and long-shock derivatives in V2 are weighted by exp(−t/4) and [1 − exp(−t/4)]. All these explicit row and portfolio formulas are paceval graphs.'))
page()
# 5
story.append(h('4. Real execution architecture'))
story.append(para('The graph handles are created once through the original paceval_CreateComputation API. A verified layout probe establishes the actual result ordering of paceval_dGetMultipleComputationsResultsExt; repeated model rows use this real multi-graph batch interface. A second genuine single-graph batch computes the 81-point two-factor stress surface. The SDK number/string conversion functions handle the numerical research CSV pathway after strict grammar validation.'))
tab([['Mathematical group','Actual computation owner'],['Rate curves, discount factors, cash-flow PV','paceval V1/V2 persistent graphs'],['First and second sensitivities, local DV01','paceval V1/V2 graphs'],['Rate-range and combined logical quality guards','paceval graphs + host input precheck'],['Cashflow grouping and sum over dated records','C++ host, length-dependent reduction'],['Duration, net gap, convexity, net DV01, stress and loss margins','paceval SUM graphs'],['Cross-version differences and joint guard','paceval COMPARE graphs'],['Independent financial references','Separate native C++ and Python mpmath']],colwidths=[aw*.45,aw*.55])
story.append(Spacer(1,6*mm))
story.append(para(f'The real run recorded <b>{evidence["unique_graphs_executed"]} of {evidence["unique_graphs_created"]} executed graphs</b>, {evidence["input_rows"]:,} scenario-payment input rows, {evidence["batch_calls"]:,} real batch calls and {evidence["graph_point_evaluations"]:,} graph-point evaluations. These are separate measurement categories and must not be added together.'))
page()
# 6
story.append(h('5. Synthetic experiment and relevant results'))
story.append(para('The input is a reproducible fixed-seed sample of 512 asset and 512 liability payments. Each side has distinct maturity distributions, and all amounts are positive fixed nominal EUR-million obligations. Eight scenario copies create 8,192 input records, each evaluated in V1 and V2. No observed market prices, client positions or risk-free curves have been used.'))
rows=[['Scenario','V1 Δ EVE (EUR m)','V2 Δ EVE (EUR m)']]
for scenario in ['BASE','PARALLEL_UP','PARALLEL_DOWN','STEEPENER','FLATTENER','SHORT_UP','SHORT_DOWN','MIXED']:
 rows.append([scenario.replace('_',' ').title(),f'{by["V1",scenario].delta_eve_eur_m:+.3f}',f'{by["V2",scenario].delta_eve_eur_m:+.3f}'])
tab(rows,[aw*.4,aw*.30,aw*.30]);story.append(Spacer(1,7*mm))
story.append(para(f'In the baseline, the net asset-liability present-value gap is <b>EUR {base.net_gap_eur_m:+.3f} million</b>. The illustrative parallel-down shock changes it to <b>EUR {down.net_gap_eur_m:+.3f} million</b>, a net economic-value change of {down.delta_eve_eur_m:+.3f} million. For the nonparallel flattener, the V2 curve produces a gap of {flat.net_gap_eur_m:+.3f} million, whereas V1 correctly ignores the zero-parallel shape coefficients.'))
story.append(para('These financial magnitudes result from the chosen synthetic payment mix and curve parameters. They are not regulatory capital losses, trading P&amp;L or a real insurer balance-sheet report.'))
# fig pages
visuals=[
(1,'cashflow_maturity','Maturity distribution','Asset and liability discounted payments aggregated into whole-year maturity buckets from V2 paceval results.'),
(2,'stressed_zero_curves','Rate-curve deformation','Continuously compounded scenario curves evaluated at 90 tenors each using the original paceval multigraph path.'),
(3,'economic_value_gap','Net economic-value mismatch','Both models are applied to identical cashflows; only V2 reacts to the shape-only shock parameters.'),
(4,'stress_delta_eve','Stress-induced economic value changes','The fixed-book change in asset minus liability PV relative to the base scenario.'),
(5,'asset_liability_duration','Timing of assets and liabilities','PV-weighted mean maturities change when the present-value weights are shifted by the rate scenario.'),
(6,'net_dv01','Analytical parallel-rate sensitivity','The signed first derivative of net PV per one basis point, calculated from paceval derivative graphs.'),
(7,'bucketed_gap','Gap by maturity bucket','Contractual asset and liability PV is aggregated by payment timing to expose term structure mismatch.'),
(8,'3d_stress_surface','Two-factor stress map','An 81-point parallel/short-tenor stress surface, each value priced with real paceval single-graph batches.'),
(9,'alm_stress_heatmap','Two-dimensional EVE operating map','The same recorded stress-surface outputs in a plan view, showing nonlinear variation of the net gap.'),
(10,'tenor_exposures','Curve-factor derivatives','V2 net sensitivity to short- and long-tenor shape parameters obtained from explicit paceval derivative graphs.')]
for num,name,title,cap in visuals:
 page();story.append(h(f'6.{num}  {title}'));figure(num,name,title,cap)
 if num==2:story.append(para('The curves are deliberately parametric and synthetic. The Basel IRRBB scenario definitions are mentioned as motivation but their regulatory numerical calibration is not reproduced.'))
 if num==4:story.append(para('The V1 and V2 models coincide on zero short and long shape parameters, so the parallel shocks are identical by design. Nonparallel shocks require the V2 term structure to affect the pricing.'))
 if num==8:story.append(para('The surface is a finite grid, not a mathematically certified global extremum over all interest-rate perturbations. No stress optimization or global outlier bound is claimed.'))
# closing
page();story.append(h('7. Independent validation and methodological controls'))
story.append(para('Three separate checks were run. First, the C++ demonstrator performs its own independent native arithmetic reference assertions for representative individual cash flows. Second, Python mpmath independently re-evaluates the fixed cash flows, curve coefficients and valuation identities at 85 decimal digits, including the complete saved row dataset and selected two-factor surface coordinates. Third, a separate invariant audit reconciles aggregate present values and buckets and tests the expected behavior of the parallel-only formula under shape-only shocks.'))
story.append(para(f'The original run passed <b>{evidence["native_reference_checks"]:,} native assertions</b>, <b>{hp["independent_comparisons"]:,} independent high-precision comparisons</b>, and <b>{iv["independent_accounting_and_domain_checks"]:,} independent portfolio/domain checks</b>. Exact numerical differences and tolerances are provided only in the machine-readable technical audits, not as performance or competitive accuracy claims.'))
story.append(para('A distinct SDK unit test verifies operator grammar, precedence, logical 0/1 results, relational comparisons, infix min/max and the difference between signed remainder (%) and mathematical modulo (mod). Numeric CSV text is first restricted to finite literal grammar, preventing an arbitrary expression from being silently evaluated as a cashflow value.'))
story.append(sub('Reproducibility'))
story.append(para('The archive contains the complete C++ sources, original SDK interface files, deterministic generator, fixed input dataset, captured original-SDK results, every plotted figure as PNG and vector PDF, independent references and CTest configuration. The compatible external paceval runtime remains an explicit build argument and is not bundled. The eight cashflow stress scenarios are independent of the 81 surface-grid combinations.'))
page();story.append(h('8. Limits, industrial next steps and conclusions'))
story.append(para('This is a transparent mathematical kernel for a hypothetical, single-currency portfolio of contractual fixed payments. It is not an actuarial liability forecasting engine, a banking-book accounting implementation, an EIOPA curve engine, a regulatory IRRBB outlier-test calculator, an NII earnings simulator, or an industrial investment/risk decision system. Its parameter limits and example loss thresholds are only research model choices.'))
story.append(para('Important missing features include observed discount-curve bootstrapping, spread and credit risk, currency conversion, non-maturity deposit behavior, prepayments, optionality, endogenous repricing under stress, balance-sheet dynamics, cashflow calendars, regulatory scenario calibration and portfolio governance. Financial model review, independently observed data and applicable regulatory interpretations would all be necessary for industrial adoption.'))
story.append(para('The verified contribution is the full reuse of mathematical execution graphs for a meaningful ALM pipeline: explicit curve formation, discounted cash flows, analytical duration/convexity and tenor derivatives, summary gaps and cross-model comparisons. The true mathematical computations are executed in the original paceval SDK, while the C++ host manages datasets and aggregation.'))
story.append(sub('Key references (accessed 15 November 2026)'))
refs=[
'[1] Basel Committee, IRRBB, Basel Framework SRP31, 2024 update; effective 2026. bis.org/committees/bcbs/basel-framework/standard/srp/31',
'[2] Basel Committee, Application guidance SRP98, effective January 2026. bis.org/committees/bcbs/basel-framework/standard/srp/98',
'[3] Basel Committee, Recalibration of shocks for IRRBB, 16 July 2024. bis.org/publications/202407-standards-recalibration-shocks-interest-rate-risk-banking-book',
'[4] ECB, SREP methodology for IRRBB/CSRBB, December 2024. bankingsupervision.europa.eu',
'[5] EIOPA, Risk-free interest rate term structures, including November 2026 technical update. eiopa.europa.eu',
'[6] OpenGamma Strata, curve calibration and rate sensitivities. strata.opengamma.io',
'[7] QuantLib term structures and curve bootstrapping documentation. quantlib-python-docs.readthedocs.io',
'[8] paceval original 4.25 C/C++ SDK. paceval.com/api/']
for x in refs:story.append(para(x,'TinyX'))
doc.build(story,onFirstPage=foot,onLaterPages=foot)
print('PASS whitepaper generated',pdf)
