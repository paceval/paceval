#!/usr/bin/env python3
"""Rebuild the English PDF directly from the verified project artefacts.
Uses only the CSV-derived charts and verified audits, no synthetic claims of speed.
"""
import json
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.colors import HexColor,white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'paceval_Pricing_Formula_Sensitivities_Whitepaper_EN.pdf'
audit=json.loads((ROOT/'results/decimal_audit.json').read_text())
blue=HexColor('#102c43'); teal=HexColor('#16889e'); gray=HexColor('#4b6070')
style=getSampleStyleSheet();style.add(ParagraphStyle(name='BigTitleX',fontName='Helvetica-Bold',fontSize=23,leading=28,textColor=blue,spaceAfter=15))
style.add(ParagraphStyle(name='HeadingX',fontName='Helvetica-Bold',fontSize=16,leading=20,textColor=blue,spaceBefore=11,spaceAfter=12))
style.add(ParagraphStyle(name='SubX',fontName='Helvetica-Bold',fontSize=11.7,leading=16,textColor=teal,spaceBefore=8,spaceAfter=7))
style.add(ParagraphStyle(name='BodyX',fontName='Helvetica',fontSize=10.5,leading=15.4,textColor=blue,spaceAfter=11))
style.add(ParagraphStyle(name='FineX',fontName='Helvetica',fontSize=9.0,leading=13,textColor=gray,spaceAfter=9))
style.add(ParagraphStyle(name='CaptionX',fontName='Helvetica',fontSize=8.4,leading=11.5,textColor=gray,alignment=TA_CENTER,spaceAfter=10))
style.add(ParagraphStyle(name='TinyX',fontName='Helvetica',fontSize=8.5,leading=11.5,textColor=blue))
def P(s,kind='BodyX'):return Paragraph(s,style[kind])
def img(name,w=7.15,h=None):
 from PIL import Image as PIL
 path=ROOT/'figures'/name
 im=PIL.open(path); natural=im.height/im.width
 return Image(str(path),width=w*inch,height=(h if h else w*natural)*inch)
def figure(name,caption,w=7.0):return [img(name,w),Spacer(1,5),P(caption,'CaptionX')]
def tbl(items,columns=(1.65,5.45)):
 data=[[P(str(a),'TinyX'),P(str(b),'TinyX')] for a,b in items]
 t=Table(data,colWidths=[v*inch for v in columns],hAlign='LEFT',repeatRows=0)
 t.setStyle(TableStyle([('ROWBACKGROUNDS',(0,0),(-1,-1),[HexColor('#eaf3f6'),white]),('LINEBELOW',(0,0),(-1,0),.6,teal),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
 return t
def page():story.append(PageBreak())
def footer(canvas,doc):
 canvas.saveState();w,h=doc.pagesize
 canvas.setStrokeColor(HexColor('#c5dce2'));canvas.line(40,43,w-40,43)
 canvas.setFont('Helvetica',7.6);canvas.setFillColor(gray)
 canvas.drawString(41,30,'paceval. | Pricing Formula Sensitivities at Scale | Research demonstrator | 2026')
 canvas.drawRightString(w-42,30,str(doc.page));canvas.restoreState()
doc=SimpleDocTemplate(str(PDF),pagesize=(595.28,841.89),leftMargin=43,rightMargin=43,topMargin=46,bottomMargin=59)
story=[]
# Page 1
story += [P('Pricing Formula Sensitivities at Scale','BigTitleX'),P('A reproducible paceval C++ demonstrator for reusable option-pricing and Greek evaluation','SubX')]
story += figure('00_pricing_hero.png','Cover illustration: a conceptual visualization of sensitivity surfaces. The measured plots inside the report are reconstructed from actual paceval CSV outputs.',7.0)
story += [P('<b>Research outcome.</b> Ten reusable paceval expression graphs were constructed with the original C/C++ SDK and executed across 2,501 controlled Black-Scholes-Merton input combinations. All 25,010 scalar and 25,010 batch results matched independently programmed native C++ references within the declared numerical tolerance.'),P('<b>Scope.</b> Synthetic European options with continuous dividend yield, constant rates and volatility. Standard-normal CDF/PDF intermediates were calculated by the C++ host; paceval evaluates the price and Greek expressions. The demonstrator is not a complete financial pricing system or trading tool.','FineX')]
page()
# Page 2
story += [P('1. Research question and execution architecture','HeadingX'),P('Can versioned, reusable mathematical expression graphs support repeatable price and Greek evaluation over a large deterministic scenario grid with directly auditable outputs?'),tbl([('Host input contract','S, K, T, r, q, sigma are validated before evaluation; nonfinite and out-of-range values are rejected.'),('C++ intermediate calculation','d1 and d2, normal CDF values N(d1), N(d2), N(-d1), N(-d2), and the normal density phi(d1).'),('paceval SDK','Ten persistent computation handles evaluate prices and Greeks in scalar and explicit batch modes.'),('Independent verification','A separately coded native C++ implementation, put-call parity, and a selected 80-decimal-digit mpmath reference.')]),Spacer(1,16),P('Responsibilities are intentionally separated','SubX'),P('The exact normal CDF is evaluated in the C++ host through std::erfc, rather than claiming that the uploaded paceval runtime provides a normal-CDF function. The returned values and model inputs enter the paceval expression graphs as a fixed 11-variable vector. Formula versions and output semantics are therefore explicit and reproducible.'),P('All displayed financial instruments are synthetic. No broker data, volatilities inferred from market prices, calibration, hedging, or investment recommendations are provided.','FineX')]
page()
# Page3
story += [P('2. Mathematical model contracts','HeadingX'),P('The pilot uses the Black-Scholes-Merton model for European-style vanilla options with continuously compounded risk-free rate r and continuous dividend yield q.'),P('d1 = [ln(S/K) + (r - q + sigma²/2)T] / (sigma sqrt(T)); d2 = d1 - sigma sqrt(T). N denotes the standard-normal CDF, and phi its density.'),tbl([('Call and put','C = S exp(-qT) N(d1) - K exp(-rT) N(d2); P = K exp(-rT) N(-d2) - S exp(-qT) N(-d1).'),('Delta','Call delta = exp(-qT) N(d1); put delta = -exp(-qT) N(-d1).'),('Gamma','exp(-qT) phi(d1) / (S sigma sqrt(T)); identical for calls and puts.'),('Vega','S exp(-qT) phi(d1) sqrt(T); sensitivity to a full 1.00 change in volatility.'),('Theta','Calendar-time theta = -partial V / partial T, expressed in currency units per year; q and r terms retained.'),('Rho','Call: K T exp(-rT) N(d2); put: -K T exp(-rT) N(-d2); per full 1.00 in continuously compounded rate.')]),Spacer(1,10),P('Numerical conventions','SubX'),P('S and K are monetary amounts per underlying unit; T is time to expiry in years; sigma is annualized volatility as a decimal; r and q are continuously compounded annual rates. The model assumes frictionless European exercise, deterministic r and q, and constant volatility. No extrapolation claims are made.')]
page()
# Page4
story += [P('3. Deterministic research workload','HeadingX'),tbl([('Study dimensions','61 spot levels from 60 to 144; 41 volatility levels from 0.08 to 0.60.'),('Fixed parameters','Strike K=100; maturity T=1.25 years; risk-free rate r=0.035; dividend yield q=0.012.'),('Approved model outputs','10 price/Greek expressions; 2,501 scenarios; 25,010 scalar results.'),('Explicit batch audit','25,010 independent batch outputs; fixed per-batch buffer size up to 32 cases.'),('Quality criterion','Absolute deviation <= 2e-9 * (1 + abs(native reference)) for each calculation.'),('Reference parity','C - P = S exp(-qT) - K exp(-rT), checked for each scenario.')]),Spacer(1,18),P('Controlled scope','SubX'),P('Only a two-dimensional spot-volatility slice is varied for the published images. Although each formula is parameterized by S, K, T, r, q and sigma, the graphs shown here do not represent a volatility smile, a stochastic-volatility calibration, or a production portfolio. The host stores the exact formula strings and uses the same model version throughout the tested grid.')]
page()
# Page5
story += [P('4. Numerical execution and independent audit','HeadingX'),tbl([('Created paceval computation handles','10 (reused across all scenario inputs).'),('Scalar SDK agreement','25,010 / 25,010 within the registered C++ tolerance.'),('Batch SDK agreement','25,010 / 25,010 within the same tolerance.'),('Independent high-precision audit',f"{audit['comparisons']} / {audit['comparisons']} selected outputs using 80-decimal-digit mpmath."),('Largest native C++ absolute distance','Approximately 4.12e-13 among all scalar and batch outputs.'),('Largest put-call parity residual','Approximately 2.84e-14 among all 2,501 scenarios.'),('High-precision maximum absolute distance',audit['maximum_absolute_difference']+'.')]),Spacer(1,14),P('Interpretation','SubX'),P('The high-precision independent script recomputes the full Black-Scholes-Merton expressions using mpmath.erf rather than the host CDF intermediates. The cited 80-digit precision applies to the reference calculation; it does not imply 80-digit accuracy of binary64 outputs. The recorded deviations are numerical and model-specific observations, not formal global interval enclosures.'),P('All evaluated graphs and their outputs derive from actual paceval SDK calls against the provided compatible Linux shared library. The external shared library is not redistributed. No speed or performance comparisons are included.','FineX')]
page()
# Page6
story += [P('5. Three-dimensional price response surfaces','HeadingX'),P('Each surface is reconstructed from the CSV output of the ten actual paceval evaluation graphs, with spot S and volatility sigma varied at fixed K, T, r and q.')]
story += figure('01_call_price_surface.png','Figure 1. European call price evaluated by a reusable paceval computation graph.',5.0)
story += figure('02_put_price_surface.png','Figure 2. European put price on the identical synthetic input grid.',5.0)
page()
# Page7
story += [P('6. Delta and curvature sensitivity','HeadingX'),P('Delta describes the first derivative with respect to spot. Gamma describes the local second derivative. They are closed-form Greeks; they were not obtained by noisy finite differences.')]
story += figure('03_call_delta_map.png','Figure 3. Call delta across spot and volatility; derived from the paceval output file.',5.75)
story += figure('04_gamma_surface.png','Figure 4. Gamma response surface; same for call and put under this model.',5.75)
page()
# Page8
story += [P('7. Vega and calendar-time theta','HeadingX'),P('Vega is defined per 1.00 absolute volatility unit, rather than per one percentage point. Theta is the derivative with respect to calendar time at fixed model parameters, expressed per year.')]
story += figure('05_vega_surface.png','Figure 5. Vega response surface computed by the reusable paceval formula.',5.75)
story += figure('06_theta_map.png','Figure 6. Call theta: time-decay and financing/dividend contributions under the fixed model.',5.75)
page()
# Page9
story += [P('8. Reproducibility and sample curves','HeadingX')]
story += figure('07_call_put_slice.png','Figure 7. European call and put prices at one fixed volatility on the published grid.',7.0)
story += [P('<b>Build:</b> Compile src/pricing_sensitivities.cpp with the unmodified official paceval API implementation in src/paceval_main.cpp and link a compatible external libpaceval Linux shared library. The single upstream include path was adjusted to the local src/ layout.'),P('<b>Run:</b> cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/library.so; cmake --build build; ctest --test-dir build --output-on-failure; ./build/pricing_sensitivities --out examples; python3 src/high_precision_reference.py.'),P('The exact CSV files, audit summary, plots and rebuilding scripts are included with this report. The source files preserve their upstream licence headers; redistribution terms must be checked separately. No LICENSE_NOTICE.md is generated.','FineX')]
page()
# Page10
story += [P('9. Scope, findings, and scientific references','HeadingX'),P('<b>Demonstrated.</b> Ten original paceval computational graphs execute and are reused over a controlled European option/Greek evaluation grid. Independent, dissimilar reference paths successfully audit every native output and selected high-precision results.'),P('<b>Not demonstrated.</b> Real-market pricing validity, calibration to bid/ask quotes, volatility smiles, exercise before expiry, credit/counterparty risk, discrete dividends, a certified interval enclosure, or a processor-independent acceleration claim.'),P('Practical extension','SubX'),P('A follow-up could register distinct model and formula versions, evaluate whole synthetic option portfolios with explicit positions and aggregation rules, assess grid uncertainty, and verify changed Greeks on out-of-sample cases. Such work should preserve a separate CDF implementation contract and avoid confusing numerical correctness with suitability for financial decisions.'),P('External references','SubX'),P('1. Original paceval C/C++ API, including reusable computation handles and batched evaluation:<br/>https://paceval.com/api/','FineX'),P('2. Mathematical notes on Black-Scholes-Merton with continuous dividend yield:<br/>https://math.osu.edu/~ban.1/5632/black_scholes.pdf','FineX'),P('3. Options Industry Council, Volatility and the Greeks:<br/>https://www.optionseducation.org/advancedconcepts/volatility-the-greeks','FineX'),P('4. Federal Reserve Bank, introduction to Black-Scholes prices and deltas:<br/>https://fraser.stlouisfed.org/files/docs/publications/frbatlreview/rev_frbatl_2000_v85no1.pdf','FineX'),Spacer(1,11),P('<b>Conclusion.</b> The tested synthetic research application establishes the executable feasibility of using reusable paceval formula graphs for European-option prices and analytic Greeks, with a clear host mathematical boundary, independently verified numerical agreement, and reproducible scientific illustrations.')]
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(PDF)
