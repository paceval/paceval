#!/usr/bin/env python3
"""Rebuild a fixed-layout, 11-page scientific report. Requires reportlab."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
import json
ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'paceval_Interchangeable_Trading_Indicators_Whitepaper_EN.pdf'
W,H=A4;L=45;R=45;TEXT=W-L-R
NAVY=HexColor('#0e2037');CYAN=HexColor('#168ca8');GREY=HexColor('#576579');PALE=HexColor('#eaf3f6')
fonts='/usr/share/fonts/truetype/dejavu'
pdfmetrics.registerFont(TTFont('DV',fonts+'/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DV-Bold',fonts+'/DejaVuSans-Bold.ttf'))
c=canvas.Canvas(str(PDF),pagesize=A4);c.setTitle('Interchangeable Quantitative Trading Indicators | paceval research demonstrator')
styles={
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.1,leading=15.2,textColor=NAVY,spaceAfter=7),
 'sub':ParagraphStyle('sub',fontName='DV-Bold',fontSize=11.2,leading=15,textColor=CYAN,spaceAfter=6),
 'muted':ParagraphStyle('muted',fontName='DV',fontSize=8.1,leading=12,textColor=GREY,spaceAfter=6),
 'small':ParagraphStyle('small',fontName='DV',fontSize=7.5,leading=11,textColor=NAVY,spaceAfter=4),
}
page=0; y=0

def new(title=None):
 global page,y
 if page:
  c.setStrokeColor(HexColor('#d9e5e9'));c.line(L,35,W-R,35)
  c.setFont('DV',7);c.setFillColor(GREY);c.drawString(L,22,'paceval. | Interchangeable Quantitative Trading Indicators | Research demonstrator | 2026');c.drawRightString(W-R,22,str(page))
  c.showPage()
 page+=1;y=H-48
 if title:
  c.setFont('DV-Bold',16);c.setFillColor(NAVY);c.drawString(L,y,title);y-=18
  c.setStrokeColor(CYAN);c.setLineWidth(1.5);c.line(L,y,W-R,y);y-=22

def para(text,style='body'):
 global y
 p=Paragraph(text,styles[style]);_,h=p.wrap(TEXT,900)
 if y-h<60:raise RuntimeError(f'Page {page} overflows: {text[:45]}')
 p.drawOn(c,L,y-h);y-=h+10

def image(name,maxheight=300,caption=None):
 global y
 path=ROOT/'figures'/name
 im=ImageReader(str(path));w,h=im.getSize();scale=min(TEXT/w,maxheight/h)
 width,height=w*scale,h*scale
 if y-height-20<48:raise RuntimeError(f'Page {page} image overflows: {name}')
 c.drawImage(im,L+(TEXT-width)/2,y-height,width=width,height=height,mask='auto');y-=height+8
 if caption:para(caption,'muted')

def table(rows,widths=None):
 global y
 widths=widths or [TEXT*.34,TEXT*.66]
 for n,(a,b) in enumerate(rows):
  h=29 if len(b)<95 else 40
  if y-h<52:raise RuntimeError('Table overflow')
  c.setFillColor(PALE if n%2==0 else HexColor('#f9fbfc'));c.rect(L,y-h,TEXT,h,stroke=0,fill=1)
  c.setFont('DV-Bold',8.2);c.setFillColor(NAVY);c.drawString(L+8,y-19,a)
  pp=Paragraph(b,styles['small']);_,ph=pp.wrap(widths[1]-16,h);pp.drawOn(c,L+widths[0]+5,y-10-ph)
  y-=h+3
 y-=10

# Cover
new()
c.setFont('DV-Bold',23);c.setFillColor(NAVY);c.drawString(L,y,'Interchangeable Quantitative');y-=31;c.drawString(L,y,'Trading Indicators');y-=31
c.setFont('DV',11);c.setFillColor(CYAN);c.drawString(L,y,'Executable, independently audited paceval expression-graph demonstrator');y-=25
image('00_trading_hero.png',maxheight=300,caption='Cover illustration: conceptual market imagery. Numerical figures in this paper use exported paceval results, not generated artwork.')
para('<b>Research outcome.</b> A tested C++ host evaluates six reusable indicator/feature operations and 128 distinct, versioned paceval scoring formulas on a deterministic synthetic sequence. The 48,640 reported score evaluations and 2,048 packed batch checks agree with a separate native arithmetic implementation.', 'body')
para('<b>Scope.</b> This is a causal computational feasibility study, not market forecasting, portfolio backtesting, investment advice, trading performance or a production exchange connection. All inputs are synthetic.', 'muted')
# 2
new('1. Research question and system boundary')
para('Can interchangeable mathematical indicator and scoring formulas be executed as persistent paceval computation graphs while maintaining causal data dependencies, explicit initialization and independently auditable numerical outputs?')
image('01_execution_architecture.png',250,'Figure 1. An explicit boundary separates chronological host state from reusable paceval mathematical graphs.')
para('The C++ host owns the strictly chronological synthetic price series, window contents, warm-up, normalization, formula IDs, data serialization, failure handling and independent arithmetic checks. paceval owns the six reusable core graphs, 128 version-one composite scoring graphs and a controlled version-two graph.')
para('<b>Not implemented:</b> brokerage execution, price-feed adapters, market microstructure, realistic data cleaning, transaction costs, slippage, or risk-adjusted trading returns. No future sample enters an earlier model evaluation.','muted')
# 3
new('2. Approved mathematical contracts')
para('<b>EMA(n):</b> EMA(t) = alpha * P(t) + (1-alpha) * EMA(t-1), alpha = 2/(n+1). For EMA(12), EMA(20), EMA(26), the first closing price seeds the state.')
para('<b>MACD(12,26,9):</b> MACD = EMA(12) - EMA(26); signal = EMA(9) of MACD; histogram = MACD - signal. Every EMA update is evaluated through the same paceval EMA kernel.')
para('<b>RSI(14), Wilder variant:</b> G and L are first initialized as mean positive and negative price changes over the first 14 intervals, then updated as G(t) = G(t-1)*(13/14)+gain/14, with the analogous rule for L. RSI = 100*G/(G+L). If both averages vanish, the host sets RSI=50 by declared convention.')
para('<b>Realized volatility:</b> the host computes the sample standard deviation of the trailing 20 log returns, annualized by sqrt(252). This rolling reduction is not claimed as a paceval graph.')
para('<b>Normalized features:</b> m = (100*(P/EMA20-1))/5; h = (100*(MACD-signal)/P)/1.5; q = (RSI-50)/50; v = (annualized volatility in percent)/20.')
para('<b>Score formula j (0..127):</b> score = 1/(1+exp(-z)), where z = a+b*m+c*h+d*q+e*v+k1(j)*m*q+k2(j)*h*v. Model-specific interaction constants k1 and k2 are embedded directly into each paceval expression string. The other coefficients are versioned model inputs. Score is a bounded mathematical descriptor, not a calibrated probability or actionable recommendation.')
# 4
new('3. Causal research workload')
para('The synthetic series has 420 indexed bars, positive prices and no random-number dependencies. Every indicator consumes only the current and past bars. Outputs begin at bar index 40 after deterministic warm-up. The original and truncated replays freeze the same formulas and initialization choices.')
image('02_price_and_ema.png',270,'Figure 2. Synthetic closing prices and paceval-evaluated EMA(20). No recorded or licensed exchange dataset is included.')
para('The experiment intentionally tests computation semantics and auditable outputs without claiming that the generated path captures empirical market characteristics. Production studies should introduce licensed, timestamped market data, documented corporate actions, and realistic event-time conventions.','muted')
# 5
new('4. Indicator state and synchronization')
image('03_rsi_macd.png',320,'Figure 3. RSI and MACD indicator states evaluated on the same chronological input stream.')
para('EMA and Wilder smoothing are state-dependent. The host updates each state exactly once per bar and supplies previously computed state values to the reusable paceval graph. All 128 score models then consume the same frozen feature vector for that bar.')
para('Cross-platform numerical results may differ if data adjustment, seeding, warm-up, missing-value treatment or smoothing conventions differ; the published numerical contract fixes each choice. <b>State management is not delegated to an expression graph.</b>')
# 6
new('5. Interchangeable score families')
image('04_five_score_models.png',320,'Figure 4. Five representative, genuinely distinct mathematical scoring graphs (of 128).')
para('All score graphs persist through the full 380-bar evaluation window. Each model has an ID, version, coefficient record and immutable expression string. The arithmetic application can exchange models without changing the indicator state pipeline.')
para('The model weights are deterministic experimental parameters. They were not trained, optimized, tested for profitability, or selected using future observations.','muted')
# 7
new('6. Full 128-formula evaluation matrix')
image('05_score_family_map.png',330,'Figure 5. All 48,640 emitted mathematical scores, directly exported from paceval and independently checked.')
para('The two interaction coefficients use 16 and eight distinct allowed values, yielding 128 distinct expression strings. Model-specific linear coefficients are supplied as versioned numeric inputs. The host also executes 16 packed input vectors per graph through the original paceval batch API, with individual SDK error-code checking.')
# 8
new('7. Calculated 3D score surface')
image('06_score_response_surface.png',380,'Figure 6. The 61-by-61 mathematical score landscape (3,721 actual paceval evaluations), varying momentum and RSI while holding MACD and volatility fixed.')
para('The 3D surface is a sensitivity visualization of a declared mathematical function under controlled inputs. It is not a return surface, a risk forecast, or evidence of an optimal trading strategy.')
# 9
new('8. Controlled formula versioning')
image('07_controlled_model_update.png',325,'Figure 7. V1 and V2 of model 0 coexist. The second version changes one coefficient under a separately specified version record.')
para('The updated graph is created separately; 128 original graphs are not replaced. Repeated evaluation of both versions allows direct numerical comparison under precisely the same indicator input vectors. No automated promotion rule or live strategy update is implemented.')
# 10
new('9. Independent numerical and temporal audit')
image('08_numerical_audit.png',305,'Figure 8. Absolute numerical differences for 48,640 results versus separately coded native C++.')
report=json.loads((ROOT/'results'/'independent_audit.json').read_text())
para(f'<b>Observed:</b> 48,640 scalar score results and 2,048 packed batch values matched separate C++ arithmetic within 1e-9 * (1+|reference|). A separate 80-digit Decimal audit checked {report["high_precision_comparisons"]:,} exported score rows. The maximum observed absolute difference in that audit was {report["max_absolute_difference_to_high_precision"]:.3g}. These are sample-specific results, not a global floating-point proof.')
para('<b>Look-ahead regression check:</b> the full 420-bar run and a separate 240-bar run agreed exactly on all 200 overlapping state rows and 25,600 overlapping score rows, establishing prefix invariance for the included deterministic test. This is not evidence of successful backtesting on live data.')
# 11
new('10. Reproducibility, limitations and references')
para('<b>Build:</b> compile src/trading_indicators.cpp with the original src/paceval_main.cpp and include src/paceval_main.h using CMake. Link a separately provided compatible x86-64 Linux paceval shared library. The original SDK license headers remain in the SDK files; the shared runtime is not redistributed.')
para('<b>Reproduce:</b> run CTest, then the executable with --out reproduced; run an additional --bars 240 replay; invoke src/verify_results.py for the 80-digit and prefix audits; generate numerical figures using src/make_figures.py. All numerical results and chart source files are included.')
table([('paceval responsibility','Graph creation, EMA recurrences, RSI arithmetic, feature transformations, composite scores, packed evaluation.'),('C++ host responsibility','Chronological price series, rolling volatility reduction, warm-up, model registry, failure handling, audit and CSV export.'),('Scientific boundary','Causal arithmetic feasibility on synthetic inputs; no tested predictive value, financial suitability, or trading performance.')])
para('<b>References:</b> paceval public API: https://paceval.com/api/ ; QuantConnect indicator warm-up and definitions: https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/key-concepts ; rolling window conventions: https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/rolling-window ; pandas-ta indicator naming: https://github.com/aarigs/pandas-ta .','small')
para('<b>Conclusion.</b> A specified library of 128 interchangeable mathematical scoring functions, supported by reusable paceval indicator-update graphs, was executed and checked successfully. Whether any formulation improves investment decisions remains a separate, untested empirical question.')
# last footer
c.setStrokeColor(HexColor('#d9e5e9'));c.line(L,35,W-R,35);c.setFont('DV',7);c.setFillColor(GREY);c.drawString(L,22,'paceval. | Interchangeable Quantitative Trading Indicators | Research demonstrator | 2026');c.drawRightString(W-R,22,str(page))
c.save();print('Created',PDF,'pages',page)
