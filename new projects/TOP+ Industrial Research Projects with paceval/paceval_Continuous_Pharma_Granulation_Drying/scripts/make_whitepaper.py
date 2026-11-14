#!/usr/bin/env python3
"""Standalone research PDF, numbers and science plots only from actual paceval evidence."""
from pathlib import Path
import json,csv,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from PIL import Image as PImg
R=Path(__file__).resolve().parents[1];OUT=R/'paceval_Continuous_Pharma_Granulation_Drying_Whitepaper_EN.pdf'
D=json.loads((R/'results/execution_evidence.json').read_text());H=json.loads((R/'results/high_precision_audit.json').read_text())
base='/usr/share/fonts/truetype/dejavu/'
for n,f in [('D','DejaVuSans.ttf'),('DB','DejaVuSans-Bold.ttf'),('DM','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(n,base+f))
pdfmetrics.registerFontFamily('D',normal='D',bold='DB')
INK=HexColor('#183a43');ACC=HexColor('#588b7b');GOLD=HexColor('#b59448');GRAY=HexColor('#607479');PALE=HexColor('#edf5f0');LINE=HexColor('#dce7e2')
style=getSampleStyleSheet()
style.add(ParagraphStyle(name='HeadWP',fontName='DB',fontSize=17.8,leading=23,textColor=INK,spaceAfter=12))
style.add(ParagraphStyle(name='SubWP',fontName='DB',fontSize=10.8,leading=15.1,textColor=ACC,spaceBefore=10,spaceAfter=6))
style.add(ParagraphStyle(name='TxtWP',fontName='D',fontSize=9,leading=14.3,textColor=INK,spaceAfter=9))
style.add(ParagraphStyle(name='SmallWP',fontName='D',fontSize=8,leading=11.8,textColor=GRAY,spaceAfter=8))
style.add(ParagraphStyle(name='CapWP',fontName='D',fontSize=8.1,leading=12,textColor=GRAY,spaceAfter=9,spaceBefore=3))
style.add(ParagraphStyle(name='TableWP',fontName='D',fontSize=8,leading=11.2,textColor=INK))
style.add(ParagraphStyle(name='TableBoldWP',fontName='DB',fontSize=8,leading=11.2,textColor=INK))
style.add(ParagraphStyle(name='EqWP',fontName='DM',fontSize=8.1,leading=12.5,textColor=INK,backColor=PALE,borderPadding=8,spaceAfter=13))
W,Ht=A4;M=44;CW=W-2*M;story=[]
def p(x):story.append(Paragraph(x,style['TxtWP']))
def small(x):story.append(Paragraph(x,style['SmallWP']))
def head(s):story.append(Paragraph(s,style['HeadWP']))
def sub(s):story.append(Paragraph(s,style['SubWP']))
def eq(x):story.append(Paragraph(html.escape(x),style['EqWP']))
def page():story.append(PageBreak())
def tab(rows,widths=None):
 cells=[[Paragraph(str(t),style['TableBoldWP' if i==0 else 'TableWP']) for t in row] for i,row in enumerate(rows)]
 t=Table(cells,colWidths=widths or [CW/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,0),1,ACC),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor('#f8faf9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 story.append(t);story.append(Spacer(1,10))
def fig(n,caption,limit=265):
 imgs=sorted((R/'figures').glob(f'fig{n:02d}_*.png'));assert len(imgs)==1,imgs
 im=PImg.open(imgs[0]);w,h=im.size;hpt=min(limit,CW*h/w)
 story.append(Image(str(imgs[0]),width=CW,height=hpt));story.append(Paragraph('<b>Figure '+str(n)+'.</b> '+caption,style['CapWP']))
# Cover background is rendered by canvas on first-page callback.
story.append(Spacer(1,680));page()
head('1  Industrial use case and research question')
p('A continuous pharmaceutical solid-dose line can meter powder and liquid into a twin-screw wet granulator. The wet granules then pass through a fluidized or vibrated bed dryer before downstream conditioning, blending and tablet compression. The composition and moisture history of each moving material fraction depend on upstream water addition, air conditions and residence-time variation. A processing window defines the range of candidate settings that satisfy selected product-moisture and temperature indicators.')
p('This paper asks a narrow, reproducible question: can the original paceval Mathematical Engine execute linked mathematical kernels for the granulation water balance, two explicit drying formulations, quality constraints, sensitivity analysis and formulation-version comparisons across large sets of candidate process conditions? The work demonstrates mathematical function execution, not a validated GMP control strategy or pharmaceutical product quality assurance.')
sub('The application chain')
p('Validated dry-solid and granulating-liquid feed data, air temperature, relative humidity, moisture parameters, residence-time assumptions and limits enter reusable paceval graphs. The graphs return wet-basis outlet moisture, extremes under assumed residence-time uncertainty, product temperature, water removal, a latent heat-load indicator, PAT residual, mathematical sensitivities and signed feasibility margins. C++ labels and stores the resulting candidate status. The results could support an eventual calibrated model, but they do not authorize a material-diversion or tablet-release action.')
sub('A compact record of what was actually tested')
tab([['Evidence dimension','Executed result'],['Original mathematical engine','paceval 4.25, compiled with supplied Linux x86-64 library'],['Graph functions',f"{D['unique_graphs_executed']} of {D['unique_graphs_created']} domain graphs actually executed"],['Synthetic cases and versions',f"{D['scenario_count']:,} distinct cases, {D['model_scenario_combinations']:,} model/case combinations"],['Independent numerical checking',f"{D['native_endvalue_assertions']:,} native and {H['checks']:,} high-precision checks"],['Model windows',f"{D['feasible_V1']:,} V1 and {D['feasible_V2']:,} V2 candidate cases pass all illustrative conditions"]],widths=[CW*.37,CW*.63])
small('All processing parameters and simulated sensor values are synthetic. None are observations from a drug-product manufacturing plant.')
page()
head('2  Scientific and industrial state of the art')
p('ICH Q13 reached the ICH Step 4 stage in November 2022 and was issued as FDA guidance in March 2023 [1]. It explains process control, material traceability, integrated continuous operation and diversion in an appropriate quality framework. The FDA PAT framework (2004) promotes scientifically justified methods for process understanding and quality assurance [2]. Neither document constitutes approval of this example algorithm.')
p('Mechanistic continuous drying models have been demonstrated for vibrated fluidized beds using material, dryer temperature, air flow and other design parameters [3]. More recent work quantified spatial heterogeneity and showed that models with particle-size-related compartments can improve transferability [4]. A 2025 study combined product temperature and water-content prediction in one gray-box model and reported validation against a laboratory drying process [5]. Another 2025 study evaluated orthogonal near-infrared and mass-balance-based observations for loss on drying [6]. A 2026 review summarizes twin-screw wet granulation process technology and remaining modeling needs [7].')
p('Equipment vendors offer integrated granulation and drying technologies. GEA ConsiGma modules combine continuous twin-screw granulation with segmented fluid-bed drying, conditioning, and optional process measurements [8]. L.B. Bohle QbCon systems similarly emphasize connected manufacture and residence-time characteristics [9]. These commercial products and their own validation/traceability workflows are not included in this demonstration.')
sub('Why a mathematical execution-graph study is useful')
p('Industrial studies frequently evaluate many formula variants and repeated candidate points. The value tested here is explicit, reusable mathematical expression execution and traceable model-version comparisons. Specialist fluid-bed solvers, process analytical instrument software, statistical models and pharmaceutical quality systems offer other, complementary functions. No software-performance or energy-savings comparison is performed.')
page()
head('3  From wet granules to the dryer exit')
p('The model uses a single dry-solid basis throughout. Dry solids enter at a mass flow S (kg/h) and with baseline moisture M_feed (kg water per kg dry solid). Additional granulation liquid W is assumed to be water (kg/h). This deliberately simplifies a real liquid-binder formulation. The resulting apparent inlet dry-basis moisture is M0 = M_feed + W/S. The model does not predict mixing, distribution of binder, nucleation or agglomeration. A linear median-size indicator appears solely to illustrate graph evaluation, not to assert a particle-size distribution.')
sub('Dry- and wet-basis quantities')
eq('M0 = M_feed + W / S     [kg water / kg dry solid]')
eq('wet_basis_water_fraction = M / (1 + M)')
p('The distinction is essential: the numerical percentage reported as a possible loss-on-drying proxy uses wet basis, while the analytical kinetic equation evolves dry-basis water. Although a mass-loss-based moisture test might be applicable for certain materials, this model output is not a validated laboratory loss-on-drying method.')
sub('Example operating conditions')
p('An illustrative dry-solids feed of 20 kg/h and water/solids ratio of 0.17 corresponds to 3.4 kg/h granulating water. In the test files, feed and air temperatures, moisture coefficients, humidity, drying time and synthetic PAT observations vary deterministically between cases. Four scenario groups stress normal conditions, humid air, elevated temperatures, and insufficient residence time. All ranges and units are documented in the bundled CSV schema.')
page()
head('4  Model V1: single apparent drying rate')
p('The source whitepaper proposes a first-order approach of residual moisture to an equilibrium value, with a temperature-dependent kinetic coefficient. The new model preserves that kernel but makes humidity and the dry/wet distinction explicit. Temperature dependence is written relative to a reference temperature to make the chosen rate coefficient interpretable and avoid the extreme pre-exponential coefficients of an unreferenced Arrhenius form.')
eq('M_eq = M_base + a_RH * RH * exp[-b_T*(T_air - T_ref)]')
eq('k(T_air) = k_ref * exp[-Ea/R*(1/T_air - 1/T_ref)]')
eq('M1(t) = M_eq + (M0 - M_eq)*exp[-k(T_air)*t]')
p('All exponentials and material-state outputs are actual paceval graph results. The numerical program only validates finite domains and provides candidate arrays to paceval. The physical assumption M0 greater than M_eq is enforced before evaluation. It implies monotone moisture loss under the stated parameter restrictions.')
sub('Illustrative temperature and water-removal outputs')
eq('T_product = T_in + (T_air - T_in)*(1-exp[-h*t]) - Lc*(M0 - M1)')
eq('water_removed = S*(M0-M1)  [kg/h];  Q_latent = water_removed*2257/3600  [kW]')
p('The product-temperature relation and nominal 2,257 kJ/kg evaporation heat indicator are not a resolved gas humidity, sensible-heat or particle-scale drying model. They are included to test coupled formulas and explicit energy/mass unit accounting, not to predict utility cost or energy savings.')
page()
head('5  Model V2: two apparent drying populations')
p('The expanded formulation represents two mathematical populations with distinct apparent drying rates. It serves as a minimal, transparent way to test model-form uncertainty that can arise from nonuniform moisture removal. It is not calibrated to an experimentally measured particle-size distribution or a numerical population balance.')
eq('M2(t) = M_eq + (M0-M_eq)*[f*exp(-k*(1+s)*t) + (1-f)*exp(-k*(1-s)*t)]')
p('The fraction f lies strictly between zero and one. The spread s lies between zero and one, making both apparent rate constants positive. At s=0, the two-population model reduces analytically to V1. For positive time, both model versions approach the same equilibrium. These limits are useful scientific checks, but they are not evidence of industrial model validity.')
sub('Model-version and sensitivity functions')
p('Persistent paceval handles are created for both formulations. Six separate version-comparison graphs calculate the outlet-moisture difference, local drying-rate difference, latent-duty difference, product-temperature difference, score difference and intersection of both feasibility decisions. Distinct handles remain retrievable rather than silently overwriting prior formulas.')
p('The residence-time derivative and the air-temperature derivative of dry-basis moisture are also explicit paceval formulas, derived independently and checked against high-precision references. These are symbolic expressions supplied to paceval, not a claim of automatic differentiation in the SDK.')
page()
head('6  Quality margins, uncertainty, and PAT')
p('A nominal time t is expanded to an illustrative residence interval [t*(1-r), t*(1+r)]. Under the validated monotonically drying domain, the shortest duration has the highest remaining moisture, and the longest duration the lowest. Rather than approximating an industrial residence-time probability distribution, the demonstration evaluates both explicit endpoints using persistent paceval graphs.')
eq('margin_wet = wet_basis_M(t*(1+r)) - M_min')
eq('margin_dry = M_max - wet_basis_M(t*(1-r))')
p('A positive margin means that the respective mathematical condition is met. Other signed margins constrain the modeled product temperature, the liquid/solid addition ratio and deviation from a synthetic PAT observation. A composite logic graph uses relational operators and AND to return 0 or 1. The host rejects invalid inputs before any formula execution; multiplying a singular branch by a Boolean mask is not considered a safe domain guard.')
sub('A critical caveat on sensor independence')
p('The sensor column was deliberately generated from the V1 mathematical drying model plus deterministic pseudorandom perturbations. This makes parser and residual-graph testing reproducible but does **not** constitute an independently calibrated or experimentally collected PAT measurement. Interpretation of systematic V2 residuals must account for that synthetic provenance.')
sub('Meaning of a positive status')
p('A passing scenario meets only this study\'s synthetic mathematical bounds. An actual pharmaceutical product would require calibrated material-property data, identified analytical measurement uncertainty, qualified equipment, statistical and mechanistic model validation, traceability and a formal GMP control strategy. No material release or rejection is executed by this research program.')
page()
head('7  paceval functions and executed responsibilities')
p('The original header and `paceval_main.cpp` from SDK 4.25 are bundled with minimal include-path adjustment only. The supplied compatible ELF x86-64 shared library was linked externally, and is deliberately excluded from the publication ZIP. Each graph uses original `paceval_CreateComputation` with an explicit variable list. Original `paceval_dGetMultipleComputationsResultsExt` evaluates many independent samples for several graphs in one API call.')
tab([['Function family / industrial purpose','Execution responsibility','Evidence'],['Granulation balance, equilibrium and kinetic rate','paceval V1/V2','Graph manifest and batch output'],['Moisture trajectories and residence endpoints','paceval V1/V2','Output profiles and edge-case checks'],['Temperature, evaporation and mass balance','paceval V1/V2','Recorded CSV and native checks'],['Margins, Boolean guard and composed quality score','paceval V1/V2','Outcome CSV, actual logic graph'],['Air-temperature and residence sensitivities','paceval V1/V2','Analytic derivatives in graph inventory'],['Version deltas and intersection feasibility','paceval COMPARE','Six actual comparison graphs'],['Input validation, status and CSV output','C++ host + paceval conversion','Source code / independent CSV parsing'],['Independent numerical references','Native C++ and mpmath','Separate results audit']],[CW*.40,CW*.23,CW*.37])
p('The runtime includes a scalar/multi-graph layout probe and operator tests for min/max, `%` versus `mod`, logical operators, relational operators and literal parsing. The API result is checked using per-result error fields and the documented SDK return-value convention. The graph manifest and execution inventory distinguish registered functions from functions genuinely used on production input rows.')
page()
head('8  Study design and numerical verification')
p(f"The deterministic source generator uses seed 20261115 and produces {D['scenario_count']:,} distinct cases in four synthetic scenario groups. Each case is evaluated in both mathematical versions, producing {D['model_scenario_combinations']:,} model/case combinations. There are {D['unique_graphs_executed']} domain graphs executed. The logged batch/graph-point counts are captured directly from C++ API instrumentation and never confused with the number of distinct scenarios.")
p(f"Native C++ independently tests the central end values across selected cases and checks {D['native_endvalue_assertions']:,} values. A separately written 85-decimal-digit mpmath reference uses the original numeric CSV fields rather than the paceval formula strings; its run checked {H['checks']:,} values without an out-of-tolerance result. This establishes numerical consistency for the specified input cases and model, not calibration of the physical drying coefficients.")
sub('Specified edge cases and limitations')
tab([['Numerical area','Tested or bounded behavior'],['Parser and string conversion','Nonliteral CSV fields rejected; paceval conversions genuinely called'],['Batch layout','Two known analytical functions used to determine result ordering'],['Graph operators','Boolean, relational, min/max and negative modulo examples'],['Physical domains','Positive absolute temperature, time and rate; strictly finite values'],['Moisture monotonicity','Positive modeled rate, inlet dry moisture above equilibrium'],['Mass conservation','Inlet wet mass equals final wet mass plus evaporated water'],['Model-form uncertainty','Two separately maintained formula families, not a numerical-accuracy contest']],[CW*.34,CW*.66])
p('The detailed precision-related differences, their tolerance policy and any exceptional cases belong exclusively to the technical audit files, not to an engine-comparison table in this whitepaper.')
page()
head('9  Demonstrated process-window results')
p('The following values are not experimental performance measurements. They are the recorded results of mathematically defined examples with assumed parameters and moisture limits. The temperature, moisture and guard computations, including their version differences, were produced by real paceval graph evaluations.')
tab([['Result','V1: one rate','V2: two populations'],['Synthetic cases',f"{D['scenario_count']:,}",f"{D['scenario_count']:,}"],['Passing illustrative process conditions',f"{D['feasible_V1']:,}",f"{D['feasible_V2']:,}"],['CASE00000 wet-basis outlet moisture','1.4685%','1.7112%'],['CASE00000 granule temperature','350.850 K','350.913 K']],[CW*.45,CW*.27,CW*.28])
p('In the reference case, the two-population representation predicts more residual moisture than the simple single-rate model at the same air temperature and nominal residence time. It therefore changes the illustrative quality score without implying one formulation is industrially more accurate. Short residence and hot-air groups stress different constraints: moisture removal and product-temperature margin respectively.')
p('A humidity-sensitive equilibrium is an explicit mathematical extension of the original whitepaper. Real humidity models can be much more complex, depend on formulation sorption isotherms and change with process conditions. Similarly, the wetting range is a chosen test condition, not an established API- or product-specific material specification.')
page()
head('10  Scientific figures: residence time and moisture distributions')
fig(1,'Original paceval results for predicted wet-basis moisture versus nominal dryer residence time under both equation versions.',250)
fig(2,'Observed output distributions across the fixed synthetic candidate ensemble. These distributions are not measured in an industrial drying campaign.',250)
page()
head('11  Scientific figures: air equilibrium and product temperature')
fig(3,'Temperature and humidity interact in the simplified equilibrium water expression. Each point is a recorded paceval output.',250)
fig(4,'Modeled granule temperature plotted against drying-air temperature. The difference reflects the simplified product-heating and evaporation coefficients.',250)
page()
head('12  Scientific figures: residence uncertainty and water accounting')
fig(5,'Worst wet and worst dry moisture at the two assumed residence-time endpoints under V2. The lines indicate only illustrative bounds.',250)
fig(6,'Modeled evaporation water flow and nominal latent heat-load indicator. The relation checks model bookkeeping, not plant energy savings.',250)
page()
head('13  Scientific figures: PAT and model-form uncertainty')
fig(7,'Synthetic PAT residual against predicted outlet moisture. The PAT signal was generated from V1 with perturbations.',250)
fig(8,'Version V2 minus V1 moisture differences against residence time. This contrasts physical model assumptions, not numerical-engine accuracy.',250)
page()
head('14  Scientific figures: process feasibility and 3D outputs')
fig(9,'Count of scenarios meeting all assumed quality checks in the four predefined synthetic scenario groups.',250)
fig(10,'Three-dimensional sample of V2 mathematical output generated from genuine paceval evaluation records.',250)
page()
head('15  Scope, limitations, and the next experimental pilot')
p('The strongest verified conclusion is that a substantial connected family of pharmaceutical process-surrogate formulas can be stored, reused and evaluated as original paceval computation graphs, including complex Boolean decisions, version comparisons, sensitivities and conservation-related expressions. Independent numerical references support the mathematical consistency of the implemented model on the tested parameter values.')
p('The work does not support a claim of better tablet quality, improved in-line NIR accuracy, optimal dryer control, industrial energy savings, patient safety, GMP qualification or regulatory approval. A realistic industrial model must include particle-size distributions, equipment-specific residence-time distributions, drying-air humidity and enthalpy balance, product-specific sorption data, coupled temperature/moisture transport, validated PAT calibration transfer and downstream relationships to tablet CQAs. A numerical success under fictional quality limits is not a pharmaceutical process qualification.')
sub('A technically meaningful next step')
p('Obtain a documented experimental dataset for one named formulation and a known dryer, including at least wet-granulation liquid/solid ratio, air temperature, air flow and humidity, granule temperature, residence-time distribution, loss-on-drying reference and independent PAT readings. Fit physical coefficients on training campaigns, freeze model versions, and test on held-out campaigns. Compare monotonicity, moisture boundary robustness, and model uncertainty; only a separate quality-system process can decide suitability for material disposition.')
sub('Reproduction and recorded proof')
p('The provided project includes original SDK source interfaces, CMake, deterministic CSV generator, executed CSV results, graph inventory, machine-readable API counts, independent native and high-precision reference checks, Markdown math preflight and ten scientific plots as both PNG and vector PDF. The reference binary library is not redistributed. The report makes no claim that an online GitHub preview has been inspected.')
page()
head('References and source documentation')
refs=[
 ('[1]','ICH Q13, FDA final guidance, March 2023','https://www.fda.gov/regulatory-information/search-fda-guidance-documents/q13-continuous-manufacturing-drug-substances-and-drug-products'),
 ('[2]','FDA PAT framework, October 2004','https://www.fda.gov/regulatory-information/search-fda-guidance-documents/pat-framework-innovative-pharmaceutical-development-manufacturing-and-quality-assurance'),
 ('[3]','Meier et al., Continuous vibrated fluid bed dryer, 2023','https://pubmed.ncbi.nlm.nih.gov/37669728/'),
 ('[4]','Spatial heterogeneity in granular fluid bed drying, 2024','https://pubmed.ncbi.nlm.nih.gov/38643808/'),
 ('[5]','Tölle et al., Combined temperature-moisture gray-box model, IFAC 2025','https://www.sciencedirect.com/science/article/pii/S2405896325009450'),
 ('[6]','Kiricenko et al., orthogonal PAT and moisture prediction, JPS 2025','https://www.sciencedirect.com/science/article/pii/S0022354924002545'),
 ('[7]','Niu et al., Twin-screw wet granulation review, 2026','https://www.sciencedirect.com/science/article/pii/S0378517326007702'),
 ('[8]','GEA ConsiGma continuous granulation and dryer modules','https://www.gea.com/de/products/granulators/continuous-granulation-lines/consigma-granulation-drying-gd-modules/'),
 ('[9]','L.B. Bohle QbCon continuous granulation and drying','https://www.lbbohle.com/pharma-machines-processes/continuous-granulation-and-drying-qbcon-1'),
 ('[10]','paceval Mathematical Engine C/C++ API','https://paceval.com/api/'),
 ]
for tag,title,url in refs:
 p(tag+' <link href="'+html.escape(url,quote=True)+'" color="#588b7b">'+html.escape(title)+'</link>.')
sub('Source and evidence boundaries')
p('Regulatory sources and original research establish general scientific context. The original WP 23 describes an unexecuted proposed study. The newly extended model and synthetic data are explicitly this study\'s own design, and no experimental claims from the original WP are reclassified as performed. The generated numerical figures are from the saved paceval execution outputs; the cover artwork is only conceptual.')
small('Research status: original library was executed locally on Linux x86-64. This is not a release certificate for equipment, a pharmaceutical manufacturing process, or material disposition.')

def cover(c,doc):
 c.saveState();im=ImageReader(str(R/'figures/00_pharma_granulation_hero_2400x1200.png'));c.drawImage(im,0,Ht-392,width=W,height=392,preserveAspectRatio=False)
 c.setFillColor(INK);c.rect(0,0,W,Ht-392,stroke=0,fill=1);c.setStrokeColor(GOLD);c.setLineWidth(4);c.line(M,Ht-405,W-M,Ht-405)
 c.setFillColor(HexColor('#d1e1d9'));c.setFont('DB',10);c.drawString(M,Ht-436,'PACEVAL.  INDUSTRIAL RESEARCH  /  WP 23')
 c.setFillColor(colors.white);c.setFont('DB',20);c.drawString(M,Ht-477,'Continuous Pharmaceutical')
 c.drawString(M,Ht-509,'Granulation and Drying Windows')
 c.setFillColor(HexColor('#d8eae4'));c.setFont('D',10.3);c.drawString(M,Ht-549,'Model-versioned moisture kinetics, residence bounds,')
 c.drawString(M,Ht-565,'PAT consistency and independently checked paceval graphs')
 c.setFillColor(HexColor('#b7cbc4'));c.setFont('D',8);c.drawString(M,48,'Original paceval SDK 4.25  |  Independent research demonstrator  |  15 November 2026')
 c.restoreState()
def footer(c,doc):
 c.saveState();c.setStrokeColor(LINE);c.line(M,Ht-39,W-M,Ht-39);c.setFillColor(ACC);c.setFont('DB',8);c.drawString(M,Ht-28,'paceval. / Pharmaceutical granulation and drying')
 c.setFillColor(GRAY);c.setFont('D',7);c.drawString(M,27,'Synthetic model study  |  Not a GMP / PAT validation');c.drawRightString(W-M,27,f'{doc.page:02d}');c.restoreState()
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=M,leftMargin=M,topMargin=57,bottomMargin=46,title='Continuous Pharmaceutical Granulation and Drying Process Windows with paceval',author='paceval research demonstration',subject='C++ mathematical engine graph execution and independent validation')
doc.build(story,onFirstPage=cover,onLaterPages=footer)
print(OUT)
