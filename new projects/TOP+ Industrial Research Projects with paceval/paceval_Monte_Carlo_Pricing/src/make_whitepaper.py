#!/usr/bin/env python3
"""Render the verified English research whitepaper from package figures/data.

Run from the repository root: python3 src/make_whitepaper.py
The only input documents are inside this GitHub package.
"""
from pathlib import Path
import json
import csv
import os
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether,HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'paceval_Monte_Carlo_Pricing_Whitepaper_EN.pdf';FIG=ROOT/'figures'
# Installed fonts only; the PDF embeds necessary glyphs, no font file distributed.
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DV-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold',italic='DV',boldItalic='DV-Bold')
BLUE=colors.HexColor('#103c5d');TEAL=colors.HexColor('#008b95');LIGHT=colors.HexColor('#e9f3f5');SLATE=colors.HexColor('#456273');WHITE=colors.white
styles={
 'title':ParagraphStyle('title',fontName='DV-Bold',fontSize=20,leading=25,textColor=BLUE,spaceAfter=14),
 'sub':ParagraphStyle('sub',fontName='DV',fontSize=12.6,leading=18,textColor=SLATE,spaceAfter=12),
 'h':ParagraphStyle('h',fontName='DV-Bold',fontSize=13.6,leading=20,textColor=BLUE,spaceBefore=5,spaceAfter=8),
 'h2':ParagraphStyle('h2',fontName='DV-Bold',fontSize=10.3,leading=15,textColor=BLUE,spaceBefore=6,spaceAfter=4),
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.25,leading=15,textColor=BLUE,spaceAfter=10),
 'tiny':ParagraphStyle('tiny',fontName='DV',fontSize=7.5,leading=11,textColor=SLATE,spaceAfter=5),
 'caption':ParagraphStyle('caption',fontName='DV',fontSize=8,leading=12,textColor=SLATE,spaceBefore=2,spaceAfter=9),
 'table':ParagraphStyle('table',fontName='DV',fontSize=8.15,leading=12.1,textColor=BLUE),
 'tablehead':ParagraphStyle('tablehead',fontName='DV-Bold',fontSize=8.1,leading=12.2,textColor=WHITE),
 'code':ParagraphStyle('code',fontName='DV',fontSize=8.1,leading=13.3,textColor=BLUE,spaceAfter=7),
}
P=lambda s,kind='body':Paragraph(s,styles[kind])
W,H=A4;CONTENT=W-2*48

def fig(stem,width=495):
 from PIL import Image as PILImage
 path=FIG/(stem+'.png');im=PILImage.open(path);iw,ih=im.size
 return Image(str(path),width=width,height=width*ih/iw)
def table(rows,widths=None):
 r=[]
 for k,row in enumerate(rows):r.append([P(str(x),'tablehead' if k==0 else 'table') for x in row])
 obj=Table(r,colWidths=widths or [CONTENT/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
 obj.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f8fa')]),
   ('GRID',(0,0),(-1,-1),.3,colors.HexColor('#cbdce5')),('VALIGN',(0,0),(-1,-1),'TOP'),
   ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 return obj

def newpage(title):return [PageBreak(),P(title,'title'),HRFlowable(width='100%',thickness=2,color=TEAL,spaceAfter=11)]

def page(canvas,doc):
 canvas.saveState()
 canvas.setFillColor(BLUE);canvas.rect(0,H-14,W,14,fill=1,stroke=0)
 canvas.setFont('DV',7.5);canvas.setFillColor(SLATE)
 canvas.drawString(48,29,'paceval. | Reusable Payoff Kernels in Monte Carlo Pricing | Scientific Demonstrator')
 canvas.drawRightString(W-48,29,f'{doc.page}')
 canvas.restoreState()

prices=list(csv.DictReader((ROOT/'examples/prices.csv').open(newline='')))
val=(ROOT/'examples/validation.txt').read_text(); audit=json.loads((ROOT/'examples/high_precision_audit.json').read_text())
best=float([x for x in val.splitlines() if x.startswith('max_analytic_deviation_in_standard_errors=')][0].split('=')[1]);

s=[]
s.extend([P('Reusable Payoff Kernels in Monte Carlo Pricing','title'),
 P('An independently checked C++ feasibility demonstrator using reusable mathematical execution graphs with the original paceval Linux runtime','sub'),
 P('Research report | 12 November 2026 | Fully synthetic study, not financial advice','tiny'),
 fig('00_monte_carlo_hero',width=492),Spacer(1,11),
 P('<b>Research question.</b> Can a reusable mathematical execution layer evaluate a broad portfolio of pre-approved financial payoff functions across fixed Monte Carlo paths while preserving numerical agreement and traceable model variants?'),
 table([['Executed scope','Verified result'],['Scenario set','1,000,000 seeded GBM paths, 500,000 antithetic pairs'],['Model layer','5 reusable payoff graphs, 100 configured contract variants'],['Payoff evaluations','100,000,000 comparisons with native C++ reference'],['Independent checks','300 high-precision payoffs, 40 analytic prices, 24 TINC samples']],[174,CONTENT-174]),
 Spacer(1,8),P('<b>Core finding.</b> The explicit payoff kernels have been executed successfully with paceval using the official C/C++ SDK, and every evaluated payoff matched the native reference within its predetermined tolerance. Monte Carlo pricing error is assessed independently from expression-evaluation error.')])

s+=newpage('1 | Scientific purpose and architecture')
s.extend([P('Monte Carlo valuation repeatedly evaluates contract cash flows under simulated asset-price scenarios. The reusable mathematical subproblem is the explicit discounted payoff formula, not the stochastic path generator or the pricing policy. A stable API lets a single family formula receive different path features and contract parameters without rebuilding a graph for each call.'),
 fig('01_architecture',485),P('Figure 1. Exact division of responsibility: C++ generates and validates paths, whereas paceval evaluates approved discounted mathematical kernels; the C++ host performs reduction, uncertainty quantification and audit output.','caption'),
 P('This is distinct from a complete trading or risk platform. No real market data are loaded, risk-neutral inputs are fixed rather than calibrated, and the study does not test portfolio risk limits, American early exercise or transaction costs.'),
 P('The five C++-created graphs are reused for 100 contract definitions; the 100 contracts are parameter sets, <b>not</b> 100 independent expression structures. This distinction matters when interpreting the graph-reuse capability.')])

s+=newpage('2 | Risk-neutral scenarios and statistical design')
s.extend([P('The fixed research model is geometric Brownian motion (GBM) under a constant risk-neutral rate. With q = 0 and standard-normal Z, the maturity price satisfies:'),
 P('<b>S(T) = S(0) exp[(r - 0.5 sigma^2) T + sigma sqrt(T) Z]</b>'),
 table([['Frozen research parameter','Value'],['Initial asset price S(0)','100'],['Constant risk-neutral rate r','0.03 per year'],['Volatility sigma','0.20 per square-root-year'],['Maturity','1 year'],['Observation steps','16 discrete monitoring dates'],['Random generator','mt19937_64 raw words + specified Box-Muller transform'],['Seed / paths','20261112 / 1,000,000 (500,000 +/- pairs)']],[240,CONTENT-240]),
 Spacer(1,10),fig('03_antithetic_paths',475),P('Figure 2. Observed terminal values for paired +Z and -Z paths; paired outputs satisfy the analytical terminal-value identity under this GBM construction.','caption'),
 P('The path generator is intentionally deterministic. Both members of an antithetic pair use opposite normal innovations at each time step. The statistical standard error is estimated from <b>pair-average discounted payoffs</b>, preserving the correct independent sample count of 500,000. A Monte Carlo confidence interval concerns stochastic uncertainty, not rounding-error containment.')])

s+=newpage('3 | Mathematical payoff functions')
s.extend([P('Write z+ = max(z, 0), ST = terminal asset value, A = arithmetic mean of the 16 monitored prices, M = maximum observed price including the initial spot, K = strike, and C = positive cap. Every payoff includes exp(-rT) within the paceval graph.'),
 table([['Payoff family','Mathematical expression (discount applied)'],['European call','exp(-rT) (ST - K)+'],['European put','exp(-rT) (K - ST)+'],['Capped European call','exp(-rT) [(ST - K)+ - (ST - K - C)+]'],['Discrete Asian call','exp(-rT) (A - K)+'],['Discrete lookback call','exp(-rT) (M - K)+']],[176,CONTENT-176]),
 Spacer(1,11),fig('02_payoff_profiles',473),P('Figure 3. Terminal-price payoff profiles at strike K = 100 and cap C = 12. Asian and lookback functions depend on full-path features and are not represented by this terminal-only cross-section.','caption'),
 P('The verified paceval parser uses <b>(z + abs(z))/2</b> to express a positive part. The C++ source preserves the exact formula strings in a fixed list. Only explicitly approved formulas are evaluated; input validation rejects nonfinite values before calling the engine. An Asian average and lookback maximum are computed by the C++ host; these two features represent discrete monitoring, not continuous-exercise assumptions.')])

s+=newpage('4 | SDK integration and contract governance')
s.extend([P('The project directly compiles the official <b>paceval_main.cpp</b> SDK interface and includes <b>paceval_main.h</b> from the application. An architecture-compatible proprietary Linux runtime is supplied externally at build time. The application does not implement an alternative dynamic-function-dispatch adapter.'),
 table([['paceval API call','Actual research use'],['paceval_InitializeLibrary / FreeLibrary','Define and close the mathematical engine lifetime'],['paceval_CreateComputation','Create five reusable payoff graphs plus one TINC graph'],['paceval_dGetComputationResultExt','Evaluate payoff batches for fixed formula handles'],['paceval_dGetComputationResult','Read point result and TINC interval for 24 discounting samples'],['paceval_GetIsError / DeleteComputation','Check graph status and release handles']],[214,CONTENT-214]),
 Spacer(1,9),fig('05_contract_variations',475),P('Figure 4. Published 100-contract output grouped by formula family. Financial values are hypothetical and model-dependent.','caption'),
 P('A strike-version update is deliberately restricted to a single contract. The revised cash flow is evaluated with the same approved graph handle, and a separate unaffected contract is reevaluated before and after the modification. The C++ host owns version identity, strike selection and validation; no model identity is inferred from a handle alone.')])

s+=newpage('5 | Full-scale results and analytic controls')
s.extend([table([['Verified numerical quantity','Observed result'],['Path/contract evaluations','1,000,000 paths x 100 contract variants = 100,000,000'],['Native C++ payoff comparisons','100,000,000 within tolerance'],['Number of analytic European contracts','40 (20 calls, 20 puts)'],['Largest standardized analytic deviation',f'{best:.3f} antithetic-pair standard errors'],['100-decimal independent payoff checks','300 / 300 within tolerance'],['Observed pointwise TINC enclosures','24 / 24 (smooth discounted-terminal kernel)']],[278,CONTENT-278]),Spacer(1,10),fig('04_black_scholes_agreement',475),
 P('Figure 5. For European call and put variants, the Monte Carlo price minus the analytic Black-Scholes reference; error bars are +/-1.96 estimated antithetic-pair standard errors.','caption'),
 P('The native C++ mathematical kernel matches paceval pointwise across the full workload. The Monte Carlo price is not required to equal the analytical expectation exactly because the 1,000,000 pseudo-random paths introduce sampling uncertainty. All 40 European prices meet the predeclared permissive gross-error criterion |MC - analytic| <= 6 SE + 0.025. This criterion does not establish calibration to any traded security.')])

s+=newpage('6 | Independent numerical precision checks')
s.extend([P('The independent Python auditor uses mpmath at <b>100 decimal digits</b>. Published binary64 input values are promoted into high precision before the exact payoff formula is reevaluated; the script does not call paceval, and it independently recomputes the Black-Scholes reference for European options.'),
 table([['Check','Independent result'],['Selected discounted payoff outputs','300, no tolerance failures'],['Largest absolute 100-digit payoff discrepancy',f"{audit['max_payoff_abs_error']:.3e}"],['Analytic Black-Scholes price references','40, zero failures'],['Expected antithetic pair terminal identity','64 pairs, zero failures'],['Model revision samples','16, native reference and unaffected-contract check']],[251,CONTENT-251]),
 Spacer(1,10),fig('06_high_precision_audit',335),P('Figure 6. Absolute deviations from the independently calculated 100-decimal payoff results. The histogram is sample-based and does not assert a universal floating-point error bound.','caption'),
 fig('07_contract_update',335),P('Figure 7. A deliberately changed strike is processed by the original reusable formula graph without changing a separate contract.','caption')])

s+=newpage('7 | Interval experiments and scientific limits')
s.extend([P('The discrete call/put payoff contains a kink at the strike. In the tested paceval build, requesting TINC on the non-smooth positive-part call formula produced an invalid interval status at selected points; the research script therefore conducts its separate 24-sample TINC check for the smooth financial quantity <b>ST exp(-rT)</b>. This distinction is explicit so that an interval for the discounted underlying is not mistaken for an independently certified option-price interval.'),
 fig('08_tinc_intervals',475),P('Figure 8. Measured reported interval widths for 24 smooth discounted-terminal samples. All 24 reference values fall inside their reported intervals in this fixed audit.','caption'),
 P('The positive TINC results are <b>sample-wise observations</b>, not a global theorem of outward rounding or validated pricing intervals. The source code, reference inputs and high-precision audit are published in the project. The model also excludes market parameter uncertainty, discretization corrections for continuous extrema, stochastic model risk, correlations, counterparty default and external financial advice.'),
 P('Independent hardware evidence is restricted to Linux x86-64 using the supplied original runtime. ARM support, parallel graph scheduling, FPGA/ASIC execution, deterministic execution deadlines and power efficiency are outside the measured scope. No speed or energy advantage is claimed by this feasibility study.')])

s+=newpage('8 | Reproducibility and scientific references')
s.extend([P('<b>Build from repository root (Linux):</b>'),P('export PACEVAL_LIB=/absolute/path/to/libpaceval_linux_sharedLIB.so<br/>cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$PACEVAL_LIB"<br/>cmake --build build -j<br/>ctest --test-dir build --output-on-failure','code'),
 P('<b>Reproduce the full executed workload:</b>'),P('./build/monte_carlo_pricing --paths 1000000 --contracts 100 --steps 16 --batch 8192 --seed 20261112 --out reproduced<br/>python3 src/high_precision_reference.py reproduced','code'),
 P('The C++ program is <b>src/monte_carlo_pricing.cpp</b>; the official SDK interface is <b>src/paceval_main.h</b> and <b>src/paceval_main.cpp</b>; the independent audit is <b>src/high_precision_reference.py</b>. The compact publication outputs are in <b>examples/</b>: contracts.csv, prices.csv, path_samples.csv, payoff_audit.csv, model_update.csv, tinc_samples.csv, validation.txt and high_precision_audit.json. Every figure is provided as PNG and the eight scientific plots also have editable SVG equivalents in <b>figures/</b>.'),
 P('<b>Environment of the executed reference experiment:</b> Debian Linux 13 on x86-64, AMD EPYC 9V74 (five visible virtual CPUs), GCC 14.2, C++17, Release build, original provided Linux paceval shared runtime; actual study execution is sequential on one process. This is a reproducibility description, not a speed claim.'),
 P('<b>Selected scientific and technical references</b>','h2'),
 P('1. paceval, C/C++ API, computation handles, batch functions and TINC: https://paceval.com/api/','tiny'),
 P('2. QuantLib open-source European option example (Monte Carlo and antithetic sampling): https://github.com/lballabio/QuantLib/blob/master/Examples/EquityOption/EquityOption.cpp','tiny'),
 P('3. Black-Scholes formula and risk-neutral geometric Brownian motion: https://wanghemath.github.io/Book-MathFinance/chapters/chapter-16-black-scholes-formula.html','tiny'),
 P('4. Intel oneMKL Cookbook, Black-Scholes pricing: https://www.intel.com/content/www/us/en/docs/onemkl/cookbook/2021-4/black-scholes-formula-european-options-pricing.html','tiny'),
 P('The 100 million output checks and selected independent high-precision audits demonstrate correct reusable payoff evaluation for the specified synthetic workload. They do not constitute independent certification of a financial pricing system, performance superiority or market suitability.')])

doc=SimpleDocTemplate(str(OUT),pagesize=A4,topMargin=44,bottomMargin=51,leftMargin=48,rightMargin=48,title='paceval Reusable Payoff Kernels in Monte Carlo Pricing',author='paceval Research',subject='C++ SDK implementation and independent numerical feasibility validation')
doc.build(s,onFirstPage=page,onLaterPages=page)
print('Whitepaper generated:',OUT)
