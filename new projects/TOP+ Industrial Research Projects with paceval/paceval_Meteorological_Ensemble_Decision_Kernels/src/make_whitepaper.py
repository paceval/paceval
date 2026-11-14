#!/usr/bin/env python3
"""Publish the English metrology-grade synthetic weather research report, never claims weather skill."""
from pathlib import Path
import json, csv, sys, math
from xml.sax.saxutils import escape
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
ROOT=Path(__file__).resolve().parent.parent
FIG=ROOT/'figures';RES=ROOT/'results'
OUT=ROOT/'paceval_Meteorological_Ensemble_Decision_Kernels_Whitepaper_EN.pdf'
evidence=json.loads((RES/'execution_evidence.json').read_text());validation=json.loads((RES/'validation_evidence.json').read_text())
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',FONT));pdfmetrics.registerFont(TTFont('DejaVu-Bold',BOLD))
WHITE=colors.white;DARK=colors.HexColor('#102943');TEAL=colors.HexColor('#0f9097');PURPLE=colors.HexColor('#7350a5');MID=colors.HexColor('#34536c');SUB=colors.HexColor('#647487');PALE=colors.HexColor('#eef5f7');BORDER=colors.HexColor('#d8e2eb')
styles={
 'body':ParagraphStyle('body',fontName='DejaVu',fontSize=8.35,leading=12.6,textColor=DARK,spaceAfter=7),
 'small':ParagraphStyle('small',fontName='DejaVu',fontSize=7.6,leading=11.4,textColor=MID,spaceAfter=5),
 'fine':ParagraphStyle('fine',fontName='DejaVu',fontSize=7.05,leading=10.5,textColor=SUB,spaceAfter=4),
 'title':ParagraphStyle('title',fontName='DejaVu-Bold',fontSize=21,leading=27,textColor=DARK,spaceAfter=10),
 'subtitle':ParagraphStyle('subtitle',fontName='DejaVu',fontSize=10.2,leading=16,textColor=MID,spaceAfter=9),
 'h1':ParagraphStyle('h1',fontName='DejaVu-Bold',fontSize=14.8,leading=20,textColor=DARK,spaceAfter=10,spaceBefore=2),
 'h2':ParagraphStyle('h2',fontName='DejaVu-Bold',fontSize=9.8,leading=14,textColor=TEAL,spaceAfter=6,spaceBefore=7),
 'cap':ParagraphStyle('cap',fontName='DejaVu',fontSize=7.4,leading=10.9,textColor=SUB,spaceAfter=8,alignment=TA_CENTER),
 'tablehead':ParagraphStyle('tablehead',fontName='DejaVu-Bold',fontSize=7.2,leading=10,textColor=WHITE),
 'table':ParagraphStyle('table',fontName='DejaVu',fontSize=7.1,leading=10.7,textColor=DARK),
 'brand':ParagraphStyle('brand',fontName='DejaVu-Bold',fontSize=14,leading=21,textColor=TEAL,spaceAfter=20),
}
doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,topMargin=21*mm,bottomMargin=18*mm,title='Meteorological Ensemble Postprocessing and Site-Level Extreme Weather Decision Kernels with paceval',author='paceval Mathematical Research Demonstrator',subject='Synthetic functionality study; not operational meteorological guidance')
W=174*mm;story=[]
def p(t,sty='body'):story.append(Paragraph(t,styles[sty]))
def h(t):p(t,'h1')
def hh(t):p(t,'h2')
def sp(n=5):story.append(Spacer(1,n*mm))
def page():story.append(PageBreak())
def addtable(rows,widths=None):
 vals=[]
 for j,row in enumerate(rows): vals.append([Paragraph(str(x),styles['tablehead'] if j==0 else styles['table']) for x in row])
 if widths is None:widths=[W/len(rows[0])]*len(rows[0])
 t=Table(vals,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),DARK),('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,PALE]),('GRID',(0,0),(-1,-1),.35,BORDER),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
 story.append(t);sp(3)
def fig(number,slug,cap,maxheight=76,width=174):
 path=FIG/f'{number:02d}_{slug}.png';assert path.exists(),path
 with PILImage.open(path) as im:w,h=im.size
 scale=min(width*mm/w,maxheight*mm/h)
 f=Image(str(path),width=w*scale,height=h*scale,hAlign='CENTER')
 story.append(f);p(f'Figure {number}. {cap}','cap')
def footer(c,document):
 c.saveState();num=document.page
 if num>1:
  c.setStrokeColor(BORDER);c.line(18*mm,A4[1]-17.5*mm,A4[0]-18*mm,A4[1]-17.5*mm)
  c.setFont('DejaVu-Bold',7.3);c.setFillColor(TEAL);c.drawString(18*mm,A4[1]-14.1*mm,'paceval.   |   Meteorological Mathematical Research')
  c.setFont('DejaVu',7.0);c.setFillColor(SUB);c.drawRightString(A4[0]-18*mm,A4[1]-14.1*mm,'14 November 2026')
 c.setStrokeColor(BORDER);c.line(18*mm,15.6*mm,A4[0]-18*mm,15.6*mm)
 c.setFont('DejaVu',6.7);c.setFillColor(SUB);c.drawString(18*mm,11.4*mm,'Synthetic computational research. Not operational weather guidance.')
 c.drawRightString(A4[0]-18*mm,11.4*mm,str(num));c.restoreState()
# cover
p('paceval.  MATHEMATICAL RESEARCH DEMONSTRATOR','brand')
p('Meteorological Ensemble Postprocessing and Site-Level Extreme Weather Decision Kernels','title')
p('Reusable mathematical execution graphs for defined heavy-rain, extreme-wind-gust and air-frost events','subtitle')
with PILImage.open(FIG/'00_weather_risk_hero.png') as hero:hero_w,hero_h=hero.size
story.append(Image(str(FIG/'00_weather_risk_hero.png'),width=174*mm,height=87*mm,hAlign='CENTER'))
p('Concept illustration. It is not a computed research result, a real weather map or a forecast product.','cap')
sp(6)
addtable([['RESEARCH STATUS','MAIN VERIFIED SCOPE'],['Executed with original paceval Linux SDK 4.25','10,000 synthetic sites; 3 weather hazards; 4 lead horizons; 2 model versions'],['Independent mathematical reference: passed','60 executed graphs; 7,460,172 graph-point outputs; 80-digit verification']],[W*.42,W*.58])
p('Research publication prepared 14 November 2026. This experimental project evaluates mathematical feasibility, not meteorological predictive skill, financial savings, authorised weather alerts or certified safety actions.','small')
page()
# page 2
h('Executive summary')
p('Industrial asset operators must convert time-bounded ensemble weather guidance into transparent local event probabilities and explicit decisions about optional protective actions. Numerical weather prediction and observational verification are specialist domains. This study tests the distinct mathematical layer: persistent paceval graphs for feature transformation, nonlinear probability models, probability-score components, sensitivity functions, asset-specific net-benefit expressions and mathematically correct bounds for joint events.')
p('Two simultaneously available model versions are applied to exactly the same deterministic synthetic features. The fixed coefficient vectors are illustrative; the study does not present them as fitted to historical observations. The synthetic binary outcomes are generated by a deterministic data-generating process rather than observed by meteorological stations.')
addtable([['Executed measure','Recorded value'],['Distinct graphs created and evaluated',str(evidence['unique_graphs_executed'])],['Synthetic feature records / evaluated model cases',f"{evidence['synthetic_feature_rows']:,} / {evidence['model_point_rows']:,}"],['Real paceval graph-point outputs',f"{evidence['graph_point_evaluations']:,}"],['Independent C++ formula checks',f"{evidence['native_cpp_independent_model_checks']:,}"],['80-decimal reference results independently verified',f"{validation['high_precision_individual_values_verified']:,}"],['Distinct synthetic hazard pairs bounded',f"{evidence['compound_pairs_evaluated']:,}"]],[W*.56,W*.44])
fig(1,'concept_architecture','Conceptual division of ensemble preparation, paceval mathematical evaluation and host-owned decision policy.',maxheight=57)
p('<b>Principal result.</b> The versioned mathematical chains have been executed and numerically verified with the original paceval SDK. No actual forecast-skill benefit or industrial decision reliability is asserted.','small')
page()
# page 3
h('1. Industrial use case and current scientific state')
p('Example: an infrastructure operator manages many exposed industrial sites. On each forecast update, the operator may need to prepare for heavy rainfall, temporarily secure equipment before extreme gusts or reschedule outdoor activity for a defined air-temperature threshold. Each risk calculation depends on the valid forecast window, local site metadata, the actual ensemble members, and explicit protection costs and effectiveness. An independent qualified operator must govern any real action.')
p('Meteorological ensemble processing is established practice. ECMWF, NOAA and DWD provide specialized forecasts and data services. Statistical postprocessing and Ensemble Model Output Statistics (EMOS) are existing methods; this research does not claim their discovery. A 2026 article by Bonavita and Geer highlights the importance of separating calibration and resolution when judging real probabilistic forecasts [R4].')
hh('What changed in 2026?')
p('The ECMWF open IFS publication gained a 0.1-degree tier on 20 October 2026, alongside the earlier 0.25-degree output [R1]. The public forecast portal retains only a short rolling archive of recent forecasts. A credible longitudinal study therefore requires separate archived model cycles and observations, potentially using GEFSv12 reforecasts with their own ensemble-size and parameter-availability constraints [R2].')
addtable([['Data source','Relevance and limitation'],['ECMWF open IFS and AIFS [R1]','Contemporary forecast products; short rolling archive is not a years-long hindcast.'],['NOAA GEFSv12 reforecast [R2]','Historical retrospective member sets from 2000 to 2019; different temporal and member coverage.'],['DWD ICON-EPS / station CDC','Potential German live replay and station evidence; model issues and observation QC must match.'],['ECMWF verification guidance [R3, R4]','Observed reliability, Brier scores and lead-time stratification need actual independent verifying observations.']],[W*.35,W*.65])
p('The published numerical experiment instead uses synthetic ensemble members and synthetic event labels. Thus its statistical plots check implementation behaviour, not operational skill.','small')
page()
# page 4
h('2. Exactly defined weather events and data contract')
addtable([['Hazard class','Synthetic event contract','Not inferred'],['24-hour heavy rain','At least 20 mm accumulated precipitation within one defined 24-hour interval.','Flood depth, drainage or inundation'],['6-hour extreme gust','At least 25 m/s peak wind gust during a specified 6-hour interval.','Structural wind load or failure'],['Overnight frost','Minimum 2-metre air temperature below 0 °C within a defined overnight window.','Surface icing or road traction']],[W*.28,W*.43,W*.29])
p('The synthetic host transforms frost temperatures into the hazard-oriented scalar minus air-temperature in degrees Celsius, so the same member-exceedance operator can evaluate all three events. This sign convention is explicit in the C++ generator and in the CSV schema. It must be reversed and documented when real temperature fields are ingested.')
hh('Real meteorological input prerequisites')
p('A future live or historical import needs the model and cycle identification, UTC issue and valid times, member identifiers, GRIB step range and accumulation semantics, physical units, coordinates, interpolation and elevation metadata, station observation windows and quality control, and model-version fingerprints. Missing members must be excluded explicitly, not silently entered as zero. The current dataset does not claim this genuine source provenance.')
hh('Synthetic experiment metadata')
addtable([['Quantity','Research setup'],['Sites / forecast leads','10,000 independent synthetic site IDs / 24, 48, 72 and 96 nominal lead hours'],['Hazards per site-lead','3 distinct physical event definitions'],['Ensemble members','51 deterministic synthetic member values per feature record'],['Input/output','Strict CSV literal validation; paceval double-to-string and string-to-double routines'],['Evidence files','input feature CSV; formula inventory; action summary; sensitivity and surface outputs']],[W*.3,W*.7])
page()
# page 5
h('3. Mathematical postprocessing model')
hh('3.1 Member frequencies and finite logit')
p('For k events among N valid simulated members, the raw exceedance is q<sub>raw</sub> = k/N. The smoothed frequency q = (k + 0.5)/(N + 1) provides a finite logit even for zero or all members exceeding the threshold. Its logit is u = ln[(k + 0.5)/(N - k + 0.5)]. Smoothing is a numerical design choice, not proof that members are independent draws from the weather-generating process.')
hh('3.2 Versioned probability formulas')
p('Each version evaluates z = b<sub>0</sub> + b<sub>1</sub>u + b<sub>2</sub>(mean - threshold)/scale + b<sub>3</sub>spread/scale + b<sub>4</sub>(height/1000) + b<sub>5</sub>sin(2πd/365.25) + b<sub>6</sub>cos(2πd/365.25) + b<sub>7</sub>(lead/72). Model v2 adds b<sub>8</sub>a²/(1+a²), where a denotes the standardized mean anomaly. The candidate probability is p = sig(z). Each mathematical expression is compiled into reusable paceval computation graphs. No coefficient fitting on station data has occurred.')
p('The analytic derivative with respect to the hazard-oriented ensemble mean is (∂p/∂mean) = p(1-p)(∂z/∂mean). For v1 the derivative of z is b<sub>2</sub>/scale; v2 includes the derivative of the bounded nonlinear correction. Both are explicit paceval formulas checked against an independent mathematical implementation.')
hh('3.3 Statistical verification and action-value kernels')
p('For a synthetic binary label y, the per-record Brier contribution is B = (p-y)². For asset loss L, mitigation fraction e and action cost C, the net benefit of an optional action is M = peL - C. Its break-even threshold is C/(eL), defined only when eL is strictly positive. The demonstration keeps the categorical policy in C++ and evaluates its mathematical margins and probability guards with paceval.')
hh('3.4 Joint-event uncertainty')
p('For two event probabilities p<sub>A</sub> and p<sub>B</sub>, the Fréchet lower and upper bounds are max(0, p<sub>A</sub> + p<sub>B</sub> - 1) and min(p<sub>A</sub>, p<sub>B</sub>). Matched synthetic site-window pairs are evaluated in actual paceval graphs. This is not a joint calibrated probability estimate, and no event independence is assumed.')
page()
# page 6
h('4. Genuine paceval execution architecture')
p('The software uses the original public C/C++ SDK 4.25 and a separately supplied compatible Linux shared library. C++ validates the input contract, generates the deterministic member data, controls graph-handle lifetimes, manages the CSV files and aggregates action statuses. paceval evaluates the substantive scalar and compound mathematical functions. Independently programmed native C++ and high-precision Python are only validation paths.')
addtable([['Production function family','Actual owner','Executed graph allocation'],['Raw exceedance, smoothing, logit, predictors','paceval','12 primary graphs per model version'],['Probability, analytic gradients, entropy','paceval','Included in primary stage per version'],['Brier, expected loss, decision margins, guards','paceval','17 secondary graphs per version'],['Fréchet bounds for joint-event probabilities','paceval','2 shared compound graphs'],['Member synthesis, timing metadata, status categories','C++ host','Stateful/categorical orchestration'],['Independent mathematical verification','C++ and mpmath','Outside productive paceval evaluation']],[W*.40,W*.20,W*.40])
p('There are exactly 60 distinct executed persistent graphs. The C++ host transports outputs from primary paceval graphs into secondary paceval graphs; it does not replace the evaluated probability, cost or risk expressions with its own reference calculations.')
hh('Actual API operations')
p('The code validates each numeric CSV field before calling paceval_dConvertStringToFloat, evaluates real computation handles through paceval_dGetMultipleComputationsResultsExt, checks returned per-element error codes and converts numerical results for CSV with paceval_dConvertFloatToString. Scalar-graph and multi-graph output ordering, logical and relational operators, min/max, and the signed-vs-mathematical modulo distinction are exercised in the automated tests.')
p('Unlike a theoretical hardware estimate, all reported counts refer to the execution already recorded with the local original paceval runtime. No MCP or remote execution is claimed.','small')
page()
# page 7
h('5. Reproducible deterministic research workload')
p('The main dataset contains 10,000 synthetic sites, four nominal lead horizons, three hazards and two immutable model versions. The member arrays are constructed deterministically from documented pseudo-random transformations. Binary labels are sampled from a synthetic latent event-probability process. Their relationship to the predictors is designed, so sample reliability charts must not be read as real-world weather verification.')
addtable([['Evidence source','Files / result definition'],['Primary input','results/synthetic_ensemble_features.csv; written and then actually reread before evaluation'],['Versioned formula inventory','results/formula_registry.csv and results/math_execution_inventory.csv'],['Case-level sampled audit','results/audit_samples.csv and results/end_to_end_trace.csv'],['Group output','results/hazard_window_summary.csv; 24 hazard × lead × version categories'],['Additional grid evaluations','results/paceval_probability_surfaces.csv; 10,086 paceval graph-input points'],['Compound-event bounds','results/compound_bounds_samples.csv; sampled paired-model bounds'],['Independent verification','results/validation_evidence.json and validation/verify_weather_reference.py']],[W*.33,W*.67])
p('The two parameterizations are deliberately retained side by side. Changed coefficients therefore correspond to independently re-evaluated formula versions, not retrospective mutation of an existing computation handle.')
p('All plots in the following pages use these archived paceval-result files. Statistical conclusions are restricted to this synthetic data-generating process. External validation on archived issued forecasts and independent observations remains an uncompleted research extension.','small')
page()
# page 8
h('6. Computed probabilities and lead-time dependence')
p('The following model results are means over 10,000 synthetic sites per hazard and forecast-lead combination. Different hazard scales and event prevalences prevent treating probabilities of rainfall, wind and frost as directly interchangeable measures of severity.')
fig(2,'event_probabilities','Mean candidate probabilities from actual paceval outputs, grouped by hazard and immutable model version.',maxheight=78)
fig(3,'lead_probability','Synthetic model probability across nominal lead horizons; forecast skill is not inferred.',maxheight=75)
page()
# page 9
h('7. Synthetic outcomes and probability verification')
p('Brier loss is meaningful here as a mathematical function and a test of the synthetic generator. Since the binary labels and ensembles were generated by the same controlled research design, this is <b>not</b> a credible measurement of forecast-system skill. In particular, it does not establish improvements over ECMWF, DWD or NOAA forecasts.')
fig(4,'synthetic_brier','Synthetic-label Brier contributions for raw exceedance and both candidate model versions; not an external forecasting benchmark.',maxheight=76)
fig(7,'synthetic_reliability','Reliability bins formed from real paceval probabilities but compared only with synthetic event outcomes.',maxheight=75)
page()
# page 10
h('8. Transparent asset-level action logic')
p('For the same event probability, a low-cost action with high mitigation effectiveness can have a positive expected net benefit while an expensive or weak intervention cannot. The host interprets each paceval margin using an explicitly hypothetical policy: positive margin and probability at least 0.25 gives ACTION_CANDIDATE; positive margin at lower probability gives REVIEW; all other cases give NO_ACTION. This illustrative policy has no operational authority.')
fig(5,'action_categories','Counts of hypothetical policy statuses derived from paceval probability and action-margin results.',maxheight=75)
fig(6,'action_margins','Average synthetic action-value margins by hazard, lead and mathematical model version.',maxheight=75)
page()
# page 11
h('9. Reusable graph response surfaces')
p('As an additional numerical stress and interpretation experiment, each model is evaluated over a synthetic grid of ensemble exceedance fraction and standardized mean anomaly. These 10,086 model-input points are calculated with the genuine paceval probability and sensitivity graphs, not by re-plotting an independent C++ model.')
fig(8,'probability_surface_v1','Nonlinear probability response of model v1 to two controlled heavy-rain input features.',maxheight=80)
fig(9,'probability_surface_v2','The concurrently registered model v2 produces a distinct surface without replacing v1.',maxheight=80)
page()
# page 12
h('10. Sensitivities and illustrative site decisions')
p('The analytic gradients produced by paceval quantify the local response of a fixed candidate probability model to a defined input change. They do not quantify uncertainty about the original weather forecast, the station observation or the underlying atmospheric state. Such questions require a separate physical/statistical model.')
fig(10,'sensitivity_surface','Computed analytical change in candidate gust probability per unit of hazard-oriented mean, model v2.',maxheight=77)
fig(11,'asset_action_scatter','Sampled rain-event action margins vary with local cost and mitigation assumptions even at similar probabilities.',maxheight=73)
page()
# page 13
h('11. Dependence limits and model-version transparency')
p('Two severe-weather hazards at the same site and issue can be dependent. A product of marginal probabilities would add an untested independence assumption. The implemented Fréchet interval instead provides universally valid probability bounds for the given marginals; narrowing that interval requires genuine joint-event information.')
fig(12,'compound_frechet_bounds','Executed Frechet upper and lower bounds for matched heavy-rain and extreme-gust synthetic events.',maxheight=73)
fig(13,'model_version_calibration','Matched versioned model probabilities versus raw ensemble member exceedance.',maxheight=75)
page()
# page 14
h('12. Stratification and relevant numerical limits')
p('The role of forecast lead and hazard class is central to real meteorological verification. This synthetic demonstration retains that metadata and reports separate averages, allowing the same software architecture to be extended to archived issued forecasts. True external verification must respect event counts, observation quality control, geographic representativeness, forecast-cycle dependencies and held-out seasons.')
fig(14,'stratified_metrics','Synthetic v2 probability and Brier matrices stratified by hazard and nominal lead.',maxheight=100)
hh('Limitations of the model')
p('The coefficient vectors are fixed illustrative parameters, not estimates from past independent stations. The ensemble member count of 51 is an artificial scenario choice, not an assertion about a specific forecast stream in this experiment. Frost uses a hazard-oriented sign convention; the input windows must not be mixed. The study does not model flood impacts, storm-induced physical failure, surface icing, correlated compound-event probability, or actual asset losses.')
page()
# page 15
h('13. Independent numerical verification and acceptance')
p('The production C++ application independently computes every published primary and secondary mathematical quantity in a separate native reference path. For the executed dataset, the recorded native reference checks cover 6,960,000 model values and 480,000 compound-event bound values. Numerical tolerances, input domains, failure handling and graph-major batch ordering are directly tested.')
addtable([['Independent evidence','Verified checks'],['Native mathematical checks for main model cases',f"{evidence['native_cpp_independent_model_checks']:,}"],['Independent compound-event checks',f"{evidence['compound_independent_checks']:,}"],['Independent 80-digit mpmath rows',f"{validation['high_precision_audit_rows_verified']:,}"],['Independent 80-digit individual mathematical values',f"{validation['high_precision_individual_values_verified']:,}"],['Independently checked compound-bound samples',f"{validation['high_precision_compound_pair_samples_verified']:,}"],['Synthetic category and summary groups',str(validation['summary_categories_verified'])]],[W*.65,W*.35])
p('Numerical disagreements and precise tolerances are documented in the executable validation scripts and machine-readable artifacts. The public report does not compare the computational speed or numerical accuracy of paceval with competing engines. Passing these numerical tests shows the evaluated expressions work for the covered finite cases; it does not certify all future parameter domains.')
hh('Domain policy and genuinely untested questions')
p('All inputs must be finite; member count and thresholds must be valid; probability outputs must lie in [0,1]; the action denominator must be positive before calculating a threshold. The host rejects invalid numeric literals in CSV fields, even when they could be interpreted as valid arithmetic expressions by a more permissive parser. TINC is not presented as a confidence interval for a meteorological forecast. No formal global enclosure or production weather-warning authorization is claimed.')
page()
# page 16
h('14. Reproduction, provenance and research extensions')
p('The repository includes the original public SDK headers, C++ source, deterministic synthetic dataset generator, formula inventory, sampled trace and reference tools, scientific plots (PNG and vector PDF), README and original proposal. It deliberately excludes the externally provided binary paceval shared library.')
addtable([['Step','Reproducible procedure'],['Configure','cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/library.so'],['Build','cmake --build build -j'],['Tests','ctest --test-dir build --output-on-failure'],['Regenerate','./build/weather_kernels --run --sites 10000 --out results/reproduced'],['Reference','python validation/verify_weather_reference.py results/reproduced']],[W*.24,W*.76])
hh('Research extensions')
p('The next evidence level is a held-out retrospective forecast test using a legitimately acquired model archive, aligned station data and correct event windows. Fit coefficients only to prior training cycles; then evaluate independent forecast seasons, stations, rare-event reliability, Brier reference scores, dependency structure and credible action costs. DWD live replay or ECMWF contemporaneous data can subsequently test the ingestion and version-control workflow, but cannot replace a multi-year retrospective skill study.')
hh('Selected primary sources')
p('[R1] ECMWF. <i>Open data: IFS and AIFS forecasts</i>, updated 2026. https://www.ecmwf.int/en/forecasts/datasets/open-data','fine')
p('[R2] NOAA. <i>GEFSv12 Reforecast, 2000-2019</i>. https://registry.opendata.aws/noaa-gefs-reforecast/','fine')
p('[R3] ECMWF Forecast User Guide. <i>Using Verification Metrics alongside the Forecast</i>. https://confluence.ecmwf.int/pages/viewpage.action?pageId=363864334','fine')
p('[R4] Bonavita, M. and Geer, A. J. (2026). <i>Forecast verification using information and noise</i>. Q. J. R. Meteorol. Soc. https://doi.org/10.1002/qj.70109','fine')
p('[R5] paceval. <i>Official Mathematical Engine API</i>. https://paceval.com/api/','fine')
p('The sources establish the scientific and data-access context. They do not validate the invented dataset, imply institutional endorsement or qualify this demonstrator as an early-warning product.','small')

doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('GENERATED PDF:',OUT,'bytes',OUT.stat().st_size)
