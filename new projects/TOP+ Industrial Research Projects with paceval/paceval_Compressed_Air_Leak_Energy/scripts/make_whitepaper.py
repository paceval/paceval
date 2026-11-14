#!/usr/bin/env python3
"""Standalone scientific English PDF using actual paceval research CSVs and figures."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether,Preformatted,HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
import csv,json,statistics as stats
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'paceval_Compressed_Air_Leak_Energy_Whitepaper_EN.pdf'
FONT='/usr/share/fonts/truetype/dejavu/'
for name,file in [('DejaVu','DejaVuSans.ttf'),('DejaVu-Bold','DejaVuSans-Bold.ttf'),('DejaVuMono','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(name,FONT+file))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVu-Bold')
INK=HexColor('#173448');BLUE=HexColor('#126d84');MUTED=HexColor('#5a707f');GOLD=HexColor('#d5a32b');LINE=HexColor('#d9e2e8');PALE=HexColor('#e9f3f6')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='H',fontName='DejaVu-Bold',fontSize=17,leading=22,textColor=INK,spaceAfter=12))
styles.add(ParagraphStyle(name='Sub',fontName='DejaVu-Bold',fontSize=10.6,leading=15,textColor=BLUE,spaceBefore=9,spaceAfter=5))
styles.add(ParagraphStyle(name='BodyA',fontName='DejaVu',fontSize=9.15,leading=14.4,textColor=INK,spaceAfter=10))
styles.add(ParagraphStyle(name='Little',fontName='DejaVu',fontSize=7.8,leading=11.4,textColor=MUTED,spaceAfter=7))
styles.add(ParagraphStyle(name='Cap',fontName='DejaVu',fontSize=8,leading=11,textColor=MUTED,spaceAfter=8,spaceBefore=3))
styles.add(ParagraphStyle(name='TableHeadA',fontName='DejaVu-Bold',fontSize=8,leading=12,textColor=INK))
styles.add(ParagraphStyle(name='TableA',fontName='DejaVu',fontSize=7.8,leading=11,textColor=INK))
styles.add(ParagraphStyle(name='MonoA',fontName='DejaVuMono',fontSize=8,leading=12,textColor=INK,backColor=PALE,borderPadding=8,spaceAfter=12))
W,H=A4;M=44;WIDTH=W-2*M
story=[]
def heading(text):story.append(Paragraph(text,styles['H']))
def sub(text):story.append(Paragraph(text,styles['Sub']))
def p(text):story.append(Paragraph(text,styles['BodyA']))
def little(text):story.append(Paragraph(text,styles['Little']))
def eq(text):story.append(Paragraph(text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'),styles['MonoA']))
def fig(n,caption,width=WIDTH,height=245):
 matches=sorted((ROOT/'figures').glob(f'fig{n:02d}_*.png'))
 assert len(matches)==1,(n,matches)
 from PIL import Image as PILImage
 im=PILImage.open(matches[0]);iw,ih=im.size
 h=min(height,width*ih/iw);story.append(Image(str(matches[0]),width=width,height=h));story.append(Paragraph(f'<b>Figure {n}.</b> {caption}',styles['Cap']))
def page():story.append(PageBreak())
def tbl(data,colw=None):
 rows=[[Paragraph(str(x),styles['TableHeadA' if i==0 else 'TableA']) for x in r] for i,r in enumerate(data)]
 t=Table(rows,colWidths=colw,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,0),1,BLUE),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor('#f8fafb')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,-1),(-1,-1),.5,LINE)]))
 story.append(t);story.append(Spacer(1,9))
# PAGE 1 drawn in onFirstPage; all other page content is body story.
story.append(Spacer(1,686));page()
heading('1  Industrial problem and research question')
p('Compressed air is a common industrial utility for actuators, tools, packaging lines and automated equipment. A plant may provide sufficient supply pressure yet waste mass flow through unintentional leaks. Choosing a pressure setpoint therefore affects several connected quantities at once: leakage, productive consumption, compression work, distribution pressure and the capacity available to users.')
p('This paper investigates whether the original paceval Mathematical Engine can evaluate a connected family of these physical and operational mathematical expressions, reuse graph handles for many scenarios, distinguish alternative leak models and produce results that pass independent numerical examination. The goal is a functional mathematical demonstration, not a CPU-speed contest or a quantified industrial energy-savings claim.')
sub('Representative workflow')
p('A hypothetical plant engineer imports measured or assumed absolute upstream and ambient pressures, air temperature, demand and compressor capacity. With a leak coefficient or an equivalent orifice geometry, the engineer evaluates candidate settings and tests pressure, capacity and leakage-share limits. The mathematical evaluation can contribute to a later audit or optimization workflow, but it is not in itself a detector, a compressor controller or an audit certificate.')
sub('Conclusions at a glance')
tbl([['Question','Recorded outcome'],['Was the mathematical execution real?','53 domain-specific paceval graphs were created and exercised.'],['Were several operating conditions investigated?','3,072 synthetic scenarios were evaluated for each of two model versions.'],['Was numerical correctness checked independently?','4,360 native C++ assertions and 73,728 85-digit checks were executed.'],['Did the models produce different decisions?','2,511 cases met all illustrative limits in V1; 2,505 did so in V2.']],colw=[WIDTH*.38,WIDTH*.62])
little('The study makes no claim of experimental plant calibration, leak location or safety/regulatory approval.')
page()
heading('2  Established engineering context')
p('ISO 11011:2013 is a system-wide framework for assessing compressed-air energy use, spanning supply, transmission and demand. The published edition remained current at the research date, with a revision in development [1]. The US Department of Energy and Oak Ridge National Laboratory provide the MEASUR assessment environment and compressed-air-specific calculators and compressor models [2,3]. In an industrial workflow, the paceval kernel proposed here would be a mathematical component within such wider measurement, analysis and operational processes.')
p('The DOE sourcebook highlights the value of baselining, pressure measurement, leakage surveys and verified field data [4]. Methods to detect or localize air leaks are distinct from mathematical energy accounting. Research published in 2024 examined ultrasonic spatial mapping in factories [5]; a 2026 review compared localization and quantification techniques [6]. Acoustic, flow-meter and pressure-decay observations may supply inputs to a model, but none of these detection systems is implemented here.')
sub('Practical alternatives and complementary tools')
tbl([['Approach','Capability and role'],['DOE/ORNL MEASUR','Plant-level assessments, compressed-air calculators and modeled operating changes.'],['Ultrasonic and acoustic sensing','Field observation and potential physical identification of leaks.'],['Pneumatic network simulators','Compressible-flow networks, components and in some cases dynamic pressure.'],['This paceval study','Reusable execution of explicit leak, compressor and operating-constraint mathematics.']],colw=[WIDTH*.36,WIDTH*.64])
p('A key limitation of the source WP 19 is the empirical nature of its leak exponent and compressor-work model. We retain that baseline as Version V1 and add a separate ideal-gas orifice model, Version V2, to make model-form differences inspectable without pretending that either version has been calibrated to a real installation.')
page()
heading('3  Input data and physical conventions')
p('The model is steady-state and uses the following convention: pressure values are absolute SI pascals, the upstream gas temperature is in kelvin, leak and production flows are kilograms per second, compressor input is in kilowatts, and distribution pressure loss is calculated from an assumed lumped coefficient. All source data are explicitly synthetic and generated deterministically.')
tbl([['Parameter group','Purpose and unit'],['Upstream, ambient, reference and pressure limits','Pascals, all absolute (not gauge pressure).'],['Ambient/upstream temperature and gas properties','Kelvin; constant heat capacity and ideal-gas properties.'],['Equivalent leak geometry or reference flow','Effective mm² and discharge coefficient; or calibrated-form kg/s reference.'],['Useful demand and compressor capacity','kg/s; must remain physically positive.'],['Efficiency and quadratic network loss','Fixed efficiency and Pa/(kg/s)² coefficient.'],['Annual hours, tariff and screening constraints','Illustrative h/year, USD/kWh and dimensionless limits.']],colw=[WIDTH*.42,WIDTH*.58])
p('Pressure is validated as upstream greater than ambient. The empirical reference pressure also exceeds ambient. The assumed exponent, area, density-related parameters and all denominators have explicit finite positive ranges. This avoids interpreting a graph mask as a short-circuiting instruction that can suppress invalid mathematical subexpressions.')
sub('Sample design')
p('The deterministic 3,072-case ensemble covers ordinary operating pressure, elevated pressure, reduced pressure and peak useful demand. It also contains 96 near-atmospheric mathematical cases; these are deliberately below the illustrative plant minimum pressure and test the subcritical orifice equation rather than proposing industrial operation at those pressures. The input file, schema, seed-free deterministic enumeration rules and checksum are part of the archive.')
page()
heading('4  V1: empirical leakage and its sensitivity')
p('The source whitepaper proposed a pressure differential power law. Its dimensional coefficient is replaced in this study by an explicit reference leak mass flow, producing a more transparent calibrated-form expression.')
eq('m_leak,1 = m_ref * ((P_up - P_amb)/(P_ref - P_amb))^n')
p('Here the exponent n is a dimensionless assumed parameter, the numerator and denominator are absolute-pressure differences, and the reference flow is in kg/s. To compare model versions consistently, the synthetic input generator determines V1 reference flow from the V2 assumed orifice at a shared reference pressure. That construction is not a measured leak calibration.')
sub('Analytic sensitivity')
eq('d(m_leak,1)/d(P_up) = m_ref*n/(P_ref-P_amb) * ((P_up-P_amb)/(P_ref-P_amb))^(n-1)')
p('This derivative is registered as an actual paceval graph, not calculated only by the host. A second graph evaluates sensitivity to the reference mass-flow parameter. The native C++ calculation and high-precision reference are written separately and evaluated using the original input data.')
sub('Interpretability and limits')
p('V1 is useful where a plant has an empirical pressure-dependent estimate from a survey or meter and needs mathematically consistent scenario evaluation. It does not distinguish upstream choked flow from subcritical regimes and cannot infer leak geometry. For large pressure changes, its exponent and reference mass flow may cease to represent actual fluid mechanics.')
page()
heading('5  V2: compressible orifice flow')
p('An ideal-gas orifice approximation provides a physically different leak-flow relationship. The ratio r = P_amb/P_up is compared to the critical ratio for a specified isentropic exponent gamma. For sufficiently low downstream-to-upstream pressure, the flow chokes, meaning that further reducing downstream pressure does not raise the mass flow for fixed upstream conditions.')
eq('r_critical = (2/(gamma+1))^(gamma/(gamma-1))')
eq('m_choked = Cd*A*P_up/sqrt(R*T) * sqrt(gamma) * (2/(gamma+1))^((gamma+1)/(2*(gamma-1)))')
p('For pressure ratios above the critical value, the subcritical expression uses a square root proportional to the difference of two pressure-ratio powers: r^(2/gamma) - r^((gamma+1)/gamma). The implementation stores both exact executable formula strings in the graph manifest. Its output uses a graph-evaluated relational condition to combine them. Every mathematical branch is finite in the host-validated domain.')
sub('Model considerations')
p('The effective flow area uses a measured-in-mm² input that is converted inside paceval to m². The model holds the discharge coefficient, gas properties and upstream temperature fixed per scenario. These assumptions do not represent the leak geometry, vena-contracta effects or thermal response of every real pneumatic fitting. This is neither a complete ISO 6358 component characterization nor a verified metrology model.')
p('The research input intentionally exercises 70 subcritical V2 scenario rows to ensure this branch is more than a registered but unused expression. A complementary analytic area sensitivity is also executed by the engine.')
page()
heading('6  Compression, mass balances and operating limits')
p('Both models use the same explicitly stated compressor and distribution proxies. The host supplies input parameters; paceval evaluates the following physical equations and final margins as independently registered, reusable graphs.')
eq('m_total = m_demand + m_leak')
eq('w = cp*T_up/eta * ((P_up/P_amb)^((gamma-1)/gamma) - 1)')
eq('P_electric = m_total*w/1000    [kW]')
eq('P_end_use = P_up - k_drop*(m_total)^2    [Pa]')
p('The compression model assumes a fixed efficiency and specific heat. It does not include compressors cycling unloaded, variable-speed stages, real-gas effects or heat-transfer transients. The electrical contribution attributed to leakage is proportional to leak mass flow under this assumed steady-state operating relation. The reported annual energy and cost indicators follow from assumed operating hours and tariff, not field measurements.')
sub('Signed mathematical margins')
eq('M_pressure = P_end_use - P_min  ;  M_capacity = m_capacity - m_total')
eq('M_fraction = f_max - m_leak/m_total  ;  M_max = P_max - P_up')
p('Four explicit relational comparisons are combined with logical AND to create a 0/1 mathematical guard. The convention is “nonnegative passes.” C++ validates data, applies any external policies and assigns the human-readable decision. Passing a mathematical guard is not an operational or regulatory authorization.')
page()
heading('7  Verified paceval execution architecture')
p('The project links the original paceval 4.25 C/C++ API to a separately supplied Linux shared library. The original license/copyright headers are retained. A minimal include-path adjustment in paceval_main.cpp accommodates a local src/ directory. The runtime is intentionally excluded from the release ZIP.')
tbl([['Function / stage','Actual owner and proof'],['Leak flow, gas orifice branches','paceval V1/V2 persistent graph handles, real input batches'],['Mass balance and compressor work','paceval explicit composite formulas'],['Energy and expenditure indicators','paceval explicit formulas with versioned inputs'],['Signed pressure, capacity and leakage guards','paceval logic and relational expressions'],['Sensitivities and version deltas','paceval local derivatives and six comparison graphs'],['Data source, schema and error validation','C++ and Python host; decimal-literal filter'],['Scenario generation and workflow','C++/Python host without mathematical proxy replacement'],['Independent native and 85-digit references','Separate audit code; not the production result generator']],colw=[WIDTH*.48,WIDTH*.52])
p('Each mathematical function is listed in results/math_execution_inventory.csv. In the main run, the program first proves the SDK input/output buffer ordering with a distinct two-graph/two-point test, creates all stable model graphs once and reuses their handles in multi-graph batches. The principal program then evaluates separately versioned comparison graphs on output vectors that were genuinely computed by paceval.')
p('The execution-evidence JSON separates distinct graphs, batch calls, graph-point evaluations and unique scenario cases. Test-only expression handles are deliberately excluded from the 53 domain-graph count. Both paceval conversion routines are used in the productive numeric CSV pipeline.')
page()
heading('8  Results: operating pressure and mass flow')
fig(1,'Actual paceval output across all synthetic pressure scenarios for the two versioned leak models.',height=220)
fig(2,'Modeled specific compression work versus upstream pressure. The visible spread reflects varying temperature and assumed efficiency.',height=220)
page()
heading('9  Results: illustrative operating screening')
fig(3,'The research guard combines four distinct limits. Colors distinguish cases that meet every criterion from cases requiring review.',height=220)
fig(4,'Modeled leak-share and illustrative annual attributed electricity expenditure. These are not measured plant savings.',height=220)
page()
heading('10  Model comparison and scenario structure')
fig(5,'Counts meeting the research constraints by scenario group. Near-atmospheric edge cases are rejected by the pressure limit.',height=220)
fig(6,'Mass-flow differences between physically different models. This figure is not a comparison of numerical accuracy.',height=220)
page()
heading('11  Coupled energy and geometry results')
fig(7,'The physical relationship between required compressor mass flow and modeled electrical input.',height=220)
fig(8,'Three-dimensional view of real V2 paceval results at sampled pressure, effective area and calculated leak mass-flow coordinates.',height=220)
page()
heading('12  Model-form uncertainty in the screening outcome')
fig(9,'Relative model-form difference in flow, computed from actual V1 and V2 paceval values. This is unrelated to compiler or engine comparison.',height=220)
sub('Summary of the executed result set')
tbl([['Metric','V1 empirical','V2 orifice'],['Distinct synthetic cases','3,072','3,072'],['Cases passing four modeled constraints','2,511','2,505'],['Median leak flow (kg/s), rounded','0.0021','0.0021'],['Median leak fraction, rounded','0.0227','0.0223'],['Distinct executed domain graphs','23','24']],colw=[WIDTH*.54,WIDTH*.23,WIDTH*.23])
little('Six additional model comparison graphs are executed, for 53 distinct subject-matter graphs overall. These numbers come from stored original program results and are subject to the explicitly synthetic model assumptions.')
page()
heading('13  Independent mathematical verification')
p('The original executable completed a full CSV-to-paceval-to-CSV path with model versioning, batch execution, conversion error inspection and nonfinite-value checks. Separately implemented native C++ expressions verified full result chains and quantities such as mass conservation, downstream pressure and energy attribution. A second independent implementation using mpmath at 85 decimal digits verified numerical outputs without parsing the original paceval formula strings as a reference.')
tbl([['Validation layer','Executed result'],['Independent native C++ end-value assertions','4,360 successful assertions in the principal run'],['Independent high-precision reference','73,728 accepted numerical comparisons'],['Special gas-flow boundary branch','70 evaluated V2 subcritical scenario rows'],['Source provenance','SHA-256 input checksum saved in technical audit'],['Real paceval operator semantics','Negative modulo, min/max, relational and boolean operators tested'],['Numeric conversions','Original paceval string-to-float and float-to-string APIs exercised']],colw=[WIDTH*.45,WIDTH*.55])
p('All numerical differences, tolerances and tested error conditions reside in the technical result artifacts rather than in accuracy-competition charts. These checks support correct implementation of the defined synthetic equations. They do not validate discharge coefficients, plant leak rates, compressor capacity or any measurement-based claim.')
sub('Predeclared error and branch policy')
p('The native reference uses a mixed absolute/relative assertion policy for finite values; the high-precision script independently checks the intended mathematics with a fixed tolerance. The test generator contains conventional, overloaded and near-atmospheric operating points. Inputs with zero/negative denominators, nonfinite values or formula-bearing CSV strings are rejected, not interpreted as valid plant measurements.')
page()
heading('14  Interpretation, limitations and route to industrial validation')
p('The functional evidence is that reusable mathematical graphs can evaluate a set of linked industrial compressed-air equations under multiple parameter and model changes while retaining an independent numerical audit trail. The model difference shows why field calibration matters: an empirical pressure exponent and an idealized orifice can agree at a reference pressure yet predict different behavior elsewhere.')
sub('What cannot be claimed')
p('The study does not detect a physical leak, locate a defect, quantify actual leakage, establish compressor performance curves, guarantee energy savings, predict noise or vibration, model dynamic receiver and pipeline networks, or establish ISO 11011 compliance. Its synthetic fuel/electricity accounting is an illustrative calculation and not a plant measurement. The modeled guard does not approve pressure limits for any installation.')
sub('Most useful follow-on experiment')
p('A defensible industrial pilot would obtain timestamped absolute pressure, power, air flow and temperature measurements; classify unloaded and production demand; obtain measured compressor characteristic curves; validate the chosen leak coefficient or effective area against isolated leak measurements; and verify downstream pressure profiles. Where localization is required, acoustic methods or equivalent field techniques must supply that evidence. A process engineer could then compare the resulting reduced-order model with an established system-level tool such as MEASUR and investigate which paceval formulas remain valid under the calibrated domain.')
p('The present research therefore supports further model integration and disciplined calibration, not a claim of scientific novelty in fluid mechanics or industrial readiness.')
page()
heading('References and reproducibility')
refs=[
('[1] ISO','ISO 11011:2013, Compressed air — Energy efficiency — Assessment','https://www.iso.org/standard/46580.html'),
('[2] DOE','MEASUR: industrial energy assessment software, updated 2025','https://www.energy.gov/cmei/ito/measur'),
('[3] ORNL','MEASUR Tools Suite: Compressed Air Assessments','https://industrialresources.ornl.gov/measur/suite/docs/group__compressed__air__assessments'),
('[4] DOE','Improving Compressed Air System Performance, Third Edition','https://betterbuildingssolutioncenter.energy.gov/better-plants/compressed-air'),
('[5] Xiao et al.','Ultrasonic-based leak detection in factories with spatial mapping, Procedia CIRP (2024)','https://doi.org/10.1016/j.procir.2024.10.325'),
('[6] Hojjati &amp; Radgen','Comparison of Leak Localization and Quantification Methods, Energies (2026)','https://doi.org/10.3390/en19071658'),
('[7] Semitela &amp; Completo','Leakage detection and localization techniques, PSEP (2026)','https://doi.org/10.1016/j.psep.2025.108176'),
('[8] MathWorks','Orifice (G) mathematical documentation','https://www.mathworks.com/help/hydro/ref/orificeg.html'),
('[9] paceval','Original Mathematical Engine API and product brief','https://paceval.com/api/')]
for code,title,url in refs:
 p(f'{code}. <link href="{url}" color="#126d84">{title}</link>.')
sub('Research archive structure')
p('The GitHub ZIP includes the input generator and deterministic cases, original SDK interface source and header, compiled-project configuration, mathematical manifest, output CSVs, two independent validation paths, machine-readable evidence, scientific PNG/vector figures, Markdown syntax tests and this independent English PDF.')
little('All model result values are generated from the project’s executed paceval computations. The cover artwork is a conceptual illustration and is not a measured industrial dataset or scientific result. Copyright and license statements in the original SDK are retained.')
# Document pages and footer

def draw_cover(canvas,doc):
 canvas.saveState();image=ImageReader(str(ROOT/'figures'/'cover_2400x1200.png'));canvas.drawImage(image,0,H-390,width=W,height=390,preserveAspectRatio=False)
 canvas.setFillColor(INK);canvas.rect(0,0,W,H-392,stroke=0,fill=1)
 canvas.setStrokeColor(GOLD);canvas.setLineWidth(4);canvas.line(M,H-410,W-M,H-410)
 canvas.setFillColor(GOLD);canvas.setFont('DejaVu-Bold',10);canvas.drawString(M,H-440,'PACEVAL. INDUSTRIAL RESEARCH  /  WP 19')
 canvas.setFillColor(colors.white);canvas.setFont('DejaVu-Bold',21);canvas.drawString(M,H-487,'Industrial Compressed Air')
 canvas.drawString(M,H-520,'Leak and Energy Optimization')
 canvas.setFont('DejaVu',10.5);canvas.setFillColor(HexColor('#dbe7ed'));canvas.drawString(M,H-557,'Reusable mathematical graphs for pressure-dependent leakage,')
 canvas.drawString(M,H-575,'compressor loading and preliminary operating feasibility')
 canvas.setFont('DejaVu',8.5);canvas.setFillColor(HexColor('#b4c9d2'));canvas.drawString(M,48,'Research demonstrator  |  Original paceval SDK 4.25  |  14 November 2026')
 canvas.restoreState()
def draw_page(c,doc):
 c.saveState();c.setStrokeColor(LINE);c.line(M,H-40,W-M,H-40);c.setFillColor(BLUE);c.setFont('DejaVu-Bold',8);c.drawString(M,H-29,'paceval. / Compressed-air mathematical research')
 c.setFillColor(MUTED);c.setFont('DejaVu',7);c.drawString(M,27,'Independent functional study · Synthetic operating data · 14 November 2026');c.drawRightString(W-M,27,f'{doc.page:02d}');c.restoreState()
doc=SimpleDocTemplate(str(OUTPUT),pagesize=A4,rightMargin=M,leftMargin=M,topMargin=58,bottomMargin=46,title='Industrial Compressed Air Leak and Energy Optimization with paceval',author='paceval research demonstrator',subject='Research on verified mathematical execution graphs for compressed-air system screening')
doc.build(story,onFirstPage=draw_cover,onLaterPages=draw_page)
print(OUTPUT)
