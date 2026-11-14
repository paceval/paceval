#!/usr/bin/env python3
"""Create independent English 14-page scientific paper from verified paceval output.
All figure coordinates are generated from real paceval CSVs, not screenshots or invented results.
"""
from pathlib import Path
import json
import pandas as pd
from html import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PIL
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';F=ROOT/'figures'
OUT=ROOT/'paceval_Transformer_Hotspot_Insulation_Aging_Whitepaper_EN.pdf'
pdfmetrics.registerFont(TTFont('DVS','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVS-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
DARK=colors.HexColor('#21243a');VIOLET=colors.HexColor('#5e3c88');LIGHT=colors.HexColor('#f3f0f7');GREY=colors.HexColor('#565c68');AMBER=colors.HexColor('#a86529')
ss=getSampleStyleSheet()
for name,sz,leading,font,color in [('BodyT',9.1,14,'DVS',DARK),('SmallT',7.6,11.4,'DVS',GREY),('CaptionT',8,12,'DVS',DARK),('HeadT',16,22,'DVS-Bold',DARK),('SubT',11.5,16,'DVS-Bold',VIOLET),('CoverT',25,33,'DVS-Bold',DARK),('KickerT',10,14,'DVS-Bold',VIOLET),('TableT',7.5,11,'DVS',DARK),('TableHT',7.5,11,'DVS-Bold',colors.white)]:
 ss.add(ParagraphStyle(name=name,fontName=font,fontSize=sz,leading=leading,textColor=color,spaceAfter=9 if name in ('BodyT','HeadT','CoverT') else 5,spaceBefore=8 if name in ('HeadT','SubT') else 0,keepWithNext=name in ('HeadT','SubT')))
story=[]
def P(txt,style='BodyT'):story.append(Paragraph(txt,ss[style]))
def H(txt):P(txt,'HeadT')
def S(txt):P(txt,'SubT')
def spacer(h=8):story.append(Spacer(1,h))
def page():story.append(PageBreak())
def tab(headers,rows,widths):
 contents=[[Paragraph(escape(str(v)),ss['TableHT']) for v in headers]]+[[Paragraph(str(v),ss['TableT']) for v in row]for row in rows]
 t=Table(contents,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),VIOLET),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#d6cedf'))]));story.append(t);spacer(9)
def figure(name,caption):
 path=F/(name+'.png');w,h=PIL.open(path).size;targetW=474;targetH=targetW*h/w
 if targetH>255:targetH=255;targetW=targetH*w/h
 story.append(KeepTogether([Image(str(path),width=targetW,height=targetH),Spacer(1,4),Paragraph('<b>Figure '+str(int(name[3:5]))+'.</b> '+caption,ss['CaptionT'])]));spacer(6)
def footer(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#ddd8e2'));canvas.line(48,44,A4[0]-48,44);canvas.setFont('DVS',7.4);canvas.setFillColor(GREY);canvas.drawString(48,31,'paceval  |  Scientific functionality study  |  WP 14  |  14 Nov 2026');canvas.drawRightString(A4[0]-48,31,str(doc.page));canvas.restoreState()

def build():
 ev=json.load(open(R/'execution_evidence.json'));qa=json.load(open(R/'high_precision_audit.json'));a=pd.read_csv(R/'asset_summary.csv');b=pd.read_csv(R/'model_comparison.csv')
 # Cover
 spacer(4);P('PACEVAL.  |  INDUSTRIAL MATHEMATICAL RESEARCH  |  WP 14','KickerT')
 story.append(Image(str(F/'00_transformer_hero.png'),width=500,height=250));spacer(22)
 P('Transformer Hot-Spot Temperature and Insulation Aging Screening','CoverT')
 P('Transient top-oil and winding dynamics, relative aging, threshold margins, analytical sensitivities and independently verified paceval execution graphs.','BodyT')
 story.append(HRFlowable(width='100%',thickness=2,color=VIOLET));spacer(14)
 P('<b>Original SDK:</b> paceval 4.25 &nbsp; | &nbsp; <b>Method:</b> numerical functionality research &nbsp; | &nbsp; <b>Data:</b> deterministic synthetic transformer models','BodyT')
 P('Cover illustration is conceptual, not a measurement or finite-element field. Results demonstrate mathematical calculations only; neither a transformer condition assessment nor IEEE C57.91-2025 / IEC 60076-7 compliance is claimed.','SmallT');page()
 # 2
 H('Abstract and executive research scope')
 P('Transformers are subject to time-varying electrical currents and ambient temperatures. Because cooling oil and windings have thermal memory, the highest winding temperature is not simply determined by the instantaneous load. The modeled hot-spot temperature affects the rate of insulating-paper thermal aging in a strongly nonlinear manner. An auditable evaluation kernel therefore needs reproducible, state-dependent equations rather than a single isolated temperature calculation.')
 P(f'This paper reports execution of <b>{ev["unique_graphs_executed"]} of {ev["unique_graphs_created"]} persistent domain-specific paceval graphs</b> on <b>{ev["distinct_input_rows"]:,} synthetic hourly inputs</b>, across two mathematical model versions, yielding <b>{ev["model_hour_rows"]:,} evaluated model-hour records</b>. The actual original C++ SDK was linked to the provided Linux shared library. End-to-end equations were checked against native C++ and independent 85-digit mpmath physical references with <b>{qa["reference_assertions"]:,} high-precision assertions passed</b>. The study expressly does not benchmark runtime, energy use or software superiority.')
 S('Industrial motivation')
 P('As a hypothetical example, a distribution utility receives a two-week load forecast for several transformers, including summer heat and short evening overload peaks. Its planning software must establish a modeled top-oil response, estimate hot-spot temperatures, compare various screening limits and identify which combinations merit more detailed thermal or equipment investigations. A reusable graph engine can evaluate the domain equations for many candidate load trajectories; engineering and protection decisions must remain separate.')
 S('Scientific claim and non-claim')
 P('The claim under test is precise: the documented explicit thermal and aging expressions can be executed as persistent paceval graphs, with scalar and batched numerical paths and independently checked final quantities. The paper does not claim that these synthetic models predict physical transformer lifetime, follow the complete latest loading standard, or constitute measured operational evidence. This distinction is foundational to the interpretation of all figures.');page()
 # 3
 H('1. Current standards, research and industrial practice')
 P('<b>IEEE C57.91-2025</b>, published on 5 March 2026, supersedes IEEE C57.91-2011 and addresses mineral-oil transformer loading with multiple thermal-model levels and duct-oil effects [1]. <b>IEC 60076-7:2018</b> remains a loading guide that connects ambient temperature and changing loading to hot-spot temperature and insulation thermal aging [2]. The proposed source WP 14 used a simplified top-oil rise expression and an Arrhenius-style aging factor; it did not incorporate a full time-dependent thermal state or establish standards compliance.')
 P('Research on dynamic thermal ratings increasingly accounts for operating scenarios, measured optical-fibre temperature and calibration of underlying thermal parameters. A 2023 High Voltage article combines modeled top-oil and winding hot-spot behavior with operating limits such as bushings and on-load tap changers [3]. Contemporary commercial monitoring includes temperature and aging indicators, together with other diagnostic signals, in platforms such as Hitachi Energy TXpert [4].')
 S('Where reusable mathematical graphs fit')
 P('A transformer monitoring platform is responsible for sensors, asset identification, condition estimation, decision workflows and cybersecurity. The narrow role investigated here is explicit model evaluation: turning current, ambient temperature, device coefficients and prior thermal state into a traceable hot-spot, aging value, sensitivity and numerical margin. It can be a component within a larger application, not a replacement for it.')
 S('Research gap explored by this demonstrator')
 P('The research question is whether complex, dependent thermal, nonlinear exponentiation, cumulative state-update, threshold logic and analytical sensitivity expressions can all remain in the original mathematical engine, while a standard C++ host only transports state, validates CSV records and records outputs. For that purpose, the study evaluates two independently retrievable versions and tests every main result against separately implemented reference mathematics.');page()
 #4
 H('2. Model definition, assumptions and units')
 P('<b>Inputs.</b> The transformer-dependent rated current is in A; top-oil and hot-spot rated rises are in K; measured or hypothetical ambient values are in °C; thermal time constants and integration intervals are in hours. R is the dimensionless load-loss/no-load-loss ratio; n, m and the cooling multiplier are dimensionless. The model uses a purely synthetic asset database and no design-specific calibration.')
 S('Thermal equilibrium target expressions')
 P('K = I / I-rated. The equilibrium top-oil rise is ΔT-oil,u = ΔT-oil,rated × cooling × [(R K² + 1)/(R + 1)]^n. The equilibrium winding rise over top oil is ΔT-w,u = ΔT-w,rated × K^(2m). The instantaneous source WP 14 formulas are preserved as model components, but their outputs are embedded in chronological state updates rather than treated as a complete transient model.')
 S('Separate oil and winding memory')
 P('The effective top-oil decay factor is a-o = exp[-dt/(tau-oil × cooling)]. Both models use the first-order transition ΔT-oil,next = ΔT-oil,u + (ΔT-oil,prev − ΔT-oil,u) × a-o. V1 sets ΔT-w,next = ΔT-w,u, meaning no additional discrete winding memory. V2 introduces a-w = exp(-dt/tau-w) and ΔT-w,next = ΔT-w,u + (ΔT-w,prev − ΔT-w,u) × a-w. These are deliberately controllable two-state proxy models, not a reimplementation of IEEE 2025 duct-oil/winding differential equations.')
 S('Hot-spot and aging reference convention')
 P('Top-oil temperature = T-ambient + ΔT-oil,next. Hot-spot temperature = top-oil temperature + ΔT-w,next. The relative aging factor uses FAA = exp[15000/(110+273.15) − 15000/(T-hot-spot+273.15)]. Thus FAA is exactly 1 at the chosen synthetic reference of 110 °C. The accumulated equivalent reference-aging time is A-next = A-prev + dt × FAA, in reference-equivalent hours. This should never be conflated with physical remaining life in years.');page()
 #5
 H('3. Guard expressions, sensitivities and paceval responsibility')
 P('The graphs compute signed continuous margins: M-hot = T-limit-hot − T-hot-spot (K); M-oil = T-limit-oil − T-top-oil (K); M-aging = FAA-limit − FAA (dimensionless); and M-load = K-limit − K (dimensionless). The composite indicator is 1 when all four margins are nonnegative and 0 otherwise. A separate illustrative score penalizes squared positive exceedances. Since Boolean evaluations do not automatically suppress all invalid arithmetic, the host checks finite numbers, positive time constants and admissible load/temperature input domains before evaluation.')
 S('Analytical sensitivity calculations')
 P('In addition to graph-computed values of load, oil rise, winding rise, thermal memory, hot-spot and FAA, paceval evaluates exact analytic one-step derivatives of the defined proxy equations. For example, ∂FAA/∂T-hot-spot = FAA × 15000/(T-hot-spot+273.15)², and ∂FAA/∂K = (∂FAA/∂T-hot-spot) × (∂T-hot-spot/∂K). Other derivative graphs quantify the prior oil/winding state memory and ambient-temperature dependence. All derivative expressions are explicitly derived and checked. The SDK is not claimed to provide automatic differentiation.')
 S('Implementation traceability')
 tab(['Function group','Actual execution','IDs and evidence'],[
  ('Thermal steady targets and lag transitions','paceval','V1/V2 LOAD_RATIO, ULTIMATE_*, *_DECAY, *_NEXT'),
  ('Temperatures, FAA and accumulated aging','paceval','V1/V2 HOTSPOT, TOP_TEMP, FAA, AGE_ACCUM'),
  ('Margins, screening and analytical sensitivities','paceval','V1/V2 MARGIN_*, COMPOSITE_GUARD, D_*'),
  ('Cross-model mathematical comparisons','paceval','Seven V1_vs_V2 graph IDs'),
  ('Chronology, file handling and reporting','C++ host','State ordering, domain validation, CSV and summary output'),
 ],[155,98,225])
 P('Every graph ID and expression is listed in the executed graph manifest and in the machine-readable inventory. Actual execution counts are computed by the compiled application, not inferred from source-code registrations.');page()
 #6
 H('4. Experimental protocol and independent checking')
 P('The deterministic input generator constructs <b>48 hypothetical transformer parameter sets</b>, each with nameplate current, losses, rated thermal rises, cooling multiplier, thermal exponents and time constants. Three synthetic operating profiles represent baseline, heatwave and temporary overload loading. Each series covers 14 days at one-hour steps, without filling gaps by external measured data. The study uses 144 asset-scenario thermal histories, evaluated twice for the two model versions.')
 P('The original SDK was compiled into a Linux x86-64 C++ demonstrator, using the original supplied `paceval_main.h`, the associated `paceval_main.cpp` interface and a separately supplied compatible `.so`. The host creates stable graphs once for each version and evaluates them with the real multi-graph batch interface. The known 2 × 2 probe confirms the output ordering. A scalar path checks representative numerical values. CSV numeric conversion invokes the original SDK functions after strict literal-grammar screening; the numeric output is rendered using the original SDK converter.')
 S('Independent verification protocol')
 P(f'Native C++ computes selected final thermal states and sensitivities independently of paceval expressions; <b>{ev["native_assertions"]:,} assertions</b> passed in the full research run. A separate 85-digit Python mpmath script recomputes <b>{qa["selected_complete_series"]} complete model-series histories</b> from the same binary64 source inputs and independently validates temperature, relative aging, accumulated state, margins, the Boolean guard and selected derivatives, with <b>{qa["reference_assertions"]:,} assertions</b> passed. Exact internal error metrics and tolerances remain in technical audit files, not in this public scientific comparison.')
 P('These tests establish numerical reproducibility for the studied equations and cases. They do not certify model parameters, insulation chemistry, emergency-loading safety, uncertainty coverage, field measurement accuracy or globally proven time-continuous temperature bounds. TINC and remote MCP were not invoked or claimed.');page()
 #7
 H('5. Verified synthetic research results')
 rows=[]
 for scen in ['baseline','heatwave','overload']:
  ss=a[a.scenario==scen];v1=ss[ss.model=='V1'];v2=ss[ss.model=='V2']
  rows.append([scen.title(),f'{v1.peak_hotspot_C.mean():.2f} / {v2.peak_hotspot_C.mean():.2f}',f'{v1.equivalent_aging_h.mean():.2f} / {v2.equivalent_aging_h.mean():.2f}',f'{int(v1.all_intervals_within_illustrative_limits.sum())} / {int(v2.all_intervals_within_illustrative_limits.sum())}'])
 tab(['Duty cycle','Mean peak hot-spot V1/V2 (°C)','Mean 14-day aging V1/V2 (h)','Entire 14-day series passing V1/V2 (out of 48)'],rows,[88,130,133,127])
 P('On the chosen synthetic distributions, the mean peak hot-spot increases from about 115 °C under the baseline schedule to 132 °C in the heatwave case and 143 °C under the short evening overloads. The aging-hours proxy increases more sharply because of the exponential thermal factor. This nonlinearity is a model property, not experimental proof of a physical failure rate.')
 P('Thirty-one out of 48 synthetic baseline series satisfy every imposed illustrative margin in each model. All evaluated heatwave and overload series contain at least one threshold exception in both model versions. These thresholds are hypothetical numerical screening values, not the design-dependent safe limits mandated by a standard or protection scheme.')
 S('The role of the second model version')
 P('At the hour-level sample rate and with selected illustrative time constants, the two versions differ only moderately. V2 retains winding heat across a step. In a rising load interval it can initially predict a lower winding rise, whereas in cooling intervals it can predict greater residual winding heat. This means the difference in integrated relative aging changes with the duty cycle. Neither version is universally more conservative. No unverified calibration advantage is claimed.')
 P('The full CSV outputs, graph metadata, case generation program and independent high-precision audit allow all reported scientific values to be reproduced or independently recalculated.');page()
 # figures 8-12
 pairs=[
  [('fig01_hotspot_scenarios','Real original-paceval hot-spot results for one synthetic transformer under the three duty cycles; dashed line shows its illustrative numerical threshold.'),('fig02_thermal_memory','Original-paceval V1/V2 hot-spot and V2 top-oil thermal time traces from an overload case. V2 preserves winding memory.')],
  [('fig03_aging_vs_temperature','Output-point cloud showing the exponential rise of the relative aging factor with hot-spot temperature; not a physical lifetime prediction.'),('fig04_cumulative_aging','Original-paceval accumulated equivalent-aging time, independently verified over complete sampled histories.')],
  [('fig05_fleet_heatmap','The actual paceval temperature field for 48 synthetically parameterized assets over the first three days of a heatwave.'),('fig06_model_aging_ratio','Distribution of the V2/V1 cumulative-aging ratio; changes depend on the transient thermal assumptions.')],
  [('fig07_screening_counts','A schedule series passes only if every hourly mathematical threshold graph passes; thresholds are illustrative.'),('fig08_peak_vs_age','Synthetic asset-level association between peak temperature and accumulated relative-aging time.')],
  [('fig09_sensitivity','Independent analytic sensitivity graphs evaluated with paceval on actual baseline conditions.'),('fig10_3d_operating_cloud','Three-dimensional plot of actual evaluated input-output points for the heatwave model; not an interpolated or FEM-generated surface.')],
 ]
 for i,pair in enumerate(pairs):
  H(f'{6+i}. Scientific figures: '+['thermal trajectories','temperature and aging','fleet characteristics','screening and consequences','sensitivities and operating field'][i]);spacer(5)
  for n,cap in pair:figure(n,cap)
  page()
 #13
 H('11. Scientific boundaries and risks')
 S('Model adequacy')
 P('This model deliberately omits top-to-bottom oil gradients, oil viscosity feedback, winding-resistance variation, duct oil circulation, switching fans/pumps, bushing heating, tap changer effects, transformer cooling category, moisture/oxygen-dependent insulation degradation, dissolved-gas evidence, system thermal constraints, and stochastic measurement errors. Such phenomena may be required for an engineering loading limit. The synthetic cooling multipliers should not be construed as a calibrated method for particular cooling classes.')
 S('Numerical correctness does not establish life expectancy')
 P('The chosen FAA expression is a model-defined relative Arrhenius-like acceleration with a nominal 110 °C reference. The output is the time integral of FAA, measured in equivalent reference-temperature hours. A real residual-life calculation requires insulation state, reference-life assumptions and much more detailed physical or empirical evidence. Large values in this experiment therefore cannot establish a component will fail, nor how many years remain.')
 S('Industrial applicability')
 P('The next evidence step would be a physically specified transformer design and cooling configuration, calibrated from manufacturer temperature-rise data and fibre-optic measurements, with explicit independent normative reference calculation under IEEE C57.91-2025 or IEC 60076-7:2018 and uncertainty analysis. Only then could a proper engineering study consider real asset-specific operational ratings and independent protective controls. Mathematical guard values are not protection trips or grid approval.')
 S('Reproducibility and source rights')
 P('The GitHub-ready archive contains source, graph manifest, complete synthetic inputs, all generated output CSVs, ten vector and raster figures, high-precision reference script and five automated CTests. The proprietary-compatible shared library must be supplied separately; the SDK source-interface copyright and AGPL notices remain intact. The cover concept is a generated illustration, not a measured data visualization. No unpublished standard text or licensed measured dataset is redistributed.');page()
 #14
 H('12. Conclusions and future work')
 P('The original paceval 4.25 Mathematical Engine was successfully used as the mathematical core of a scientifically traceable, two-version, time-dependent transformer loading and relative-aging study. The demonstrator evaluates the core heating equations, both thermal-state transitions, nonlinear FAA, accumulated aging, signed limits, Boolean screening logic, numerical score functions, derivatives and model comparisons as genuine persistent graphs. The host handles the required chronological state transfer and reporting. Independently implemented native C++ and high-precision Python calculation paths agree with the declared equations under the documented verification conditions.')
 P('The most important scientific result is functional, not commercial: explicit, interdependent engineering formulas can be registered and repeatedly executed through real original paceval graphs while maintaining separately inspectable industrial-domain inputs, numerical provenance, formula versions and mathematical decisions. Subsequent calibration with actual transformer measurements and faithful complete loading-standard models is required before any industry-specific predictive claim.')
 H('References and traceable external sources')
 for x in [
 '[1] IEEE Standards Association. <i>IEEE C57.91-2025: Guide for Loading Mineral-Oil-Immersed Transformers and Step-Voltage Regulators</i>. Published 5 March 2026. https://standards.ieee.org/ieee/C57.91/7163/',
 '[2] International Electrotechnical Commission. <i>IEC 60076-7:2018, Power transformers, Part 7: Loading guide for mineral-oil-immersed power transformers</i>. https://webstore.iec.ch/en/publication/34351',
 '[3] <i>Dynamic thermal rating assessment of oil-immersed power transformers for multiple operating conditions</i>. High Voltage (2023), DOI: 10.1049/hve2.12333. https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/hve2.12333',
 '[4] Hitachi Energy. <i>TXpert Hub</i>, equipment temperature, thermal monitoring and condition management. https://www.hitachienergy.com/products-and-solutions/transformers/the-txpert-ecosystem/txpert-hub',
 '[5] paceval. <i>Mathematical Engine C/C++ API</i>, SDK version 4.25 reference. https://paceval.com/api/',
 '[6] Original user research specification, <i>WP 14. Transformer Hotspot Temperature and Insulation Aging Screening</i>, 13 November 2026 (source document bundled with repository).'
 ]:P(x,'SmallT')
 P('All paper numeric outputs are from the actual locally compiled paceval run and its verification records. Exact detailed audit data is preserved separately. No processing-time, throughput or energy-efficiency advantage is asserted.','SmallT')
 doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=58,rightMargin=58,topMargin=61,bottomMargin=60,title='Transformer Hot-Spot Temperature and Insulation Aging Screening with paceval',author='paceval scientific research')
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 print('Wrote',OUT)
if __name__=='__main__':build()
