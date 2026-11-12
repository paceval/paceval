"""Build the English WP034 report from actually executed paceval outputs.
Explicit page-by-page layout enables rendered visual inspection after generation.
"""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PImage
import json
R=Path(__file__).resolve().parents[1]
DEST=R/'paceval_CNC_Parameter_Screening_Whitepaper_EN.pdf'
D='/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('DejaVu',D+'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold',D+'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVu-Bold')
W,H=A4
NAVY=colors.HexColor('#132638');TEAL=colors.HexColor('#1C8D86');GRAY=colors.HexColor('#526574')
STYLE={
 'cover':ParagraphStyle('cover',fontName='DejaVu-Bold',fontSize=23,leading=30,textColor=NAVY,spaceAfter=14),
 'title':ParagraphStyle('title',fontName='DejaVu-Bold',fontSize=15.4,leading=21,textColor=NAVY,spaceAfter=12),
 'sub':ParagraphStyle('sub',fontName='DejaVu-Bold',fontSize=10.5,leading=16,textColor=TEAL,spaceAfter=7,spaceBefore=9),
 'body':ParagraphStyle('body',fontName='DejaVu',fontSize=9,leading=15,textColor=NAVY,spaceAfter=10),
 'small':ParagraphStyle('small',fontName='DejaVu',fontSize=7.7,leading=12,textColor=GRAY,spaceAfter=8),
 'eq':ParagraphStyle('eq',fontName='DejaVu',fontSize=10,leading=17,textColor=NAVY,spaceBefore=7,spaceAfter=12,leftIndent=16),
 'table':ParagraphStyle('table',fontName='DejaVu',fontSize=7.8,leading=12,textColor=NAVY),
}
report=SimpleDocTemplate(str(DEST),pagesize=A4,leftMargin=46,rightMargin=46,topMargin=55,bottomMargin=65)
story=[]
def add(t,style='body'):story.append(Paragraph(t,STYLE[style]))
def title(t):add(t,'title')
def sub(t):add(t,'sub')
def new():story.append(PageBreak())
def pic(name,width=480,height=280):
 p=R/'figures'/name;w,h=PImage.open(p).size;f=min(width/w,height/h);story.append(Image(str(p),w*f,h*f));story.append(Spacer(1,8))
def tbl(rows,widths):
 t=Table([[Paragraph(str(x),STYLE['table']) for x in row] for row in rows],colWidths=widths,repeatRows=1)
 t.setStyle(TableStyle([('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.HexColor('#EAF3F3'),colors.white]),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#D9E5E8')),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'TOP')]));story.append(t);story.append(Spacer(1,12))
def foot(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(TEAL);canvas.line(46,47,W-46,47);canvas.setFillColor(GRAY);canvas.setFont('DejaVu',7)
 canvas.drawString(46,34,'paceval  |  WP_034 CNC Parameter Screening  |  November 2026');canvas.drawRightString(W-46,34,str(doc.page));canvas.restoreState()
# 1
add('PACEVAL  |  SCIENTIFIC RESEARCH DEMONSTRATOR','small')
add('Formula-Based CNC<br/>Parameter Screening','cover')
add('Reusable mathematical milling-response graphs, industrial feasibility filters, immutable cost revisions and independent numerical verification.','body')
pic('00_cnc_hero.png',505,290)
add('<b>Executed result:</b> 58 real paceval computation graphs; 8,000 synthetic milling candidates; 5,388 candidates passing the declared illustrative constraints; 64,707 scalar and 12,955 batch evaluations. CMake and CTest passed.','body')
add('Cover illustration: original conceptual artwork, not a photograph or a measured industrial trial. The study concerns a hypothetical 12-mm, four-flute peripheral milling setup.','small');new()
# 2
title('1. Industrial application and current state of practice')
add('CNC process engineers select cutting speed, feed per tooth, axial engagement and radial engagement for a specific cutter, workpiece and machine. The choice affects material removal, spindle power, tool life, surface quality and operating limits. In real manufacturing these decisions combine tooling supplier data, empirical machining trials, machine constraints and process planning software. A computational screening stage can systematically reject candidate settings that violate declared mathematical limits before a qualified process engineer performs further verification.')
sub('Established technical basis')
add('Sandvik Coromant publishes milling relationships for spindle speed, table feed, material-removal rate, net cutting power and torque. Tool-life evaluation requires experimental methods, material and cutter definitions. ISO 8688-1:1989, confirmed in 2022, describes procedures for tool-life testing in face milling. These references support the physical bookkeeping used here but do not calibrate the synthetic tool-life or surface-quality proxies.')
sub('Research question')
add('Can a catalog of versioned CNC screening expressions be evaluated repeatedly through persistent paceval mathematical graphs, while a separate C++ host enforces declared feasibility thresholds and independently checks the computed outputs?')
sub('Meaningful industrial scope')
add('Potential applications include offline process-planning tools, digital machining handbooks, CAM parameter recommendation prototypes and manufacturing engineering research. Nothing in this experiment operates a CNC controller or determines real cutting parameters for an untested tool-material pair.')
new()
# 3
title('2. Mathematical model, variables and units')
add('A fixed cylindrical 12-mm tool with four effective cutting teeth is assumed; the effective cutting-force coefficient k_c = 1,850 N/mm², spindle efficiency η = 0.86 and simple corner-radius surrogate r = 0.8 mm are declared synthetic constants, not measured tool-specific parameters.')
tbl([['Symbol','Meaning','Unit'],['v_c','Cutting speed','m/min'],['f_z','Feed per tooth','mm/tooth'],['a_p, a_e','Axial and radial engagement','mm'],['n','Spindle speed','rev/min'],['v_f','Table feed','mm/min'],['Q','Material removal rate','cm³/min'],['P_m','Estimated motor power','kW']],[65,275,145])
sub('Standard milling kinematics')
add('n = 1000 v_c / (π D),     v_f = n z f_z','eq')
add('Q = a_p a_e v_f / 1000,     P_m = (Q k_c) / (60000 η)','eq')
add('The power equation distinguishes theoretical cutting power from motor input by the explicitly assumed η. The force proxy F = 60000 P_cut / v_c is derived from the tangential power relationship.')
sub('Deliberately non-calibrated exploratory proxies')
add('T_proxy = 40 (180 / v_c)^4 (0.12 / f_z)^0.25   [minutes]','eq')
add('R_proxy = f_z² / (32 × 0.8)   [mm]','eq')
add('T_proxy resembles a Taylor-style response, but its coefficients are not experimentally identified. R_proxy is an idealized feed-mark geometry surrogate, not a certified milled roughness Ra or a general physical surface finish law.');new()
# 4
title('3. paceval expression architecture and scoring versions')
add('The executable creates seven individually reusable machining-metric graphs, 50 different dimensionless cost graphs organized in five mathematical families, and one additional immutable revision: 58 actual computation handles. Each candidate passes through the metric graph family before the selected cost graph receives the five derived features.')
tbl([['Graph range','Function and application'],['1–2','Spindle rpm and table feed'],['3–4','Material-removal rate and spindle motor power'],['5–7','Tool-life, geometric surface, force proxies'],['8–57','Five score families; ten unique formulas in each family'],['58','New revision of score family 1; original retained']],[92,393])
sub('Illustrative objective construction')
add('For normalized variables q=Q/20, p=P_m/5, r=R_proxy/0.001, t=40/T_proxy and f=F/1000, one family evaluates:','body')
add('J = a p² + b r² − c q   (dimensionless)','eq')
add('Different families use logarithms, square roots, nonlinear products and inverse-life penalties. All families express modeling priorities rather than validated economics; objective values from different families are not intrinsically comparable. Coefficients are frozen and exported in formula_registry.csv. Graph 58 introduces an explicit additional force penalty without silently modifying graph 8.');new()
# 5
title('4. Deterministic synthetic screening experiment')
add('The synthetic candidate generator enumerates 8,000 deterministic choices with cutting speed from 100 to 280 m/min, feed per tooth from 0.055 to 0.165 mm, axial engagement from 0.7 to 1.75 mm and radial engagement from 2 to 8 mm. Every candidate is scored using one of 50 registered cost formulas. The host then applies exactly five independent illustrative feasibility constraints:')
tbl([['Constraint','Declared threshold'],['Spindle rotation','n ≤ 9,000 rev/min'],['Motor power','P_m ≤ 7.5 kW'],['Tool-life proxy','T_proxy ≥ 18 min'],['Geometric surface proxy','R_proxy ≤ 0.0012 mm'],['Force proxy','F ≤ 1,800 N']],[210,275])
add('<b>Observed result:</b> 5,388 of 8,000 candidate operating points pass these conditions. The thresholds are fabricated research assumptions for transparent mathematical screening. They are not manufacturer recommendations or machining safety limits.')
pic('05_screening_decisions.png',465,275)
add('Figure 1. Deterministic screening decisions and apparent material-removal / power trade-off.','small');new()
#6
title('5. True paceval-computed 3D operating surfaces')
pic('01_mrr_surface.png',480,310)
add('Figure 2. Material removal rate from 3,721 real paceval batch outputs on the cutting-speed / feed grid.','small')
pic('02_power_surface.png',480,310)
add('Figure 3. Matching calculated motor-power surface for the same fixed synthetic engagement and cutter.','small');new()
#7
title('6. Tool-life response and screening boundaries')
pic('03_tool_life_surface.png',480,300)
add('Figure 4. Synthetic Taylor-style life proxy. Values depend on assumed coefficients and do not predict a real cutter life.','small')
pic('09_tool_life_boundary.png',480,290)
add('Figure 5. Tool-life proxy contours; red marks the illustrative 18-minute threshold.','small');new()
#8
title('7. Operating maps and the industrial trade-off')
pic('04_power_contours.png',480,285)
add('Figure 6. Motor-power contour map derived from the same paceval batch-output grid.','small')
pic('06_life_tradeoff.png',480,285)
add('Figure 7. Trade-off between computed throughput and illustrative tool-life response; the threshold is a screening policy, not a machining certification.','small');new()
#9
title('8. Reconfiguration and cost-model sensitivity')
pic('07_formula_revision.png',475,280)
add('Figure 8. Original and revised analytical score graphs both remain callable after the formula change.','small')
pic('08_cost_family_distribution.png',475,285)
add('Figure 9. Distinct cost families applied to synthetic samples. Their numerical scales encode different mathematical priorities and must not be interpreted as calibrated commercial costs.','small');new()
#10
title('9. Independent audit and reproducibility')
add('The Linux executable was built with the original paceval_main.h and paceval_main.cpp source adapters linked to the external original shared library. All 58 computations were created through the official paceval API. Both scalar and batch execution paths were used; the 3,721-point grids were generated directly by the SDK batch interface.')
tbl([['Executed scientific verification','Observed evidence'],['Reusable mathematical graph handles','58'],['Synthetic CNC operating points','8,000'],['Scalar graph evaluations','64,707'],['Batch metric evaluations','12,955'],['Independent in-process reference checks','77,157'],['Separate 80-digit verification','3,384 selected metric and score values'],['CMake / CTest integration','1/1 passed']],[255,230])
add('C++ and high-precision reference differences are recorded only in the internal technical audit files, not presented as a claimed product superiority or industrial model-validation result.')
sub('Reproduce from the repository root')
add('cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so','small')
add('cmake --build build -j; ctest --test-dir build --output-on-failure; ./build/cnc_screening --out examples','small')
add('python3 src/verify_results.py; python3 src/high_precision_reference.py; python3 src/make_figures.py; python3 src/check_readme_math.py','small')
new()
#11
title('10. Scientific limitations, industrial outlook and sources')
add('The outcome demonstrates arithmetic feasibility, graph reuse, version-controlled engineering equations and an independently reproducible constrained-screening workflow. It does not establish process capability, vibration stability, cutter wear, machine safety, thermal behavior, surface finish or life for an actual cutter and workpiece. The assumptions deliberately omit tool deflection, chip thinning, chatter, coolant effects, dynamic machine response and tool-workpiece geometry beyond the declared kinematic model.')
sub('Practical validation pathway')
add('A machining partner could supply approved tool-material catalogs, measured cutting-force and tool-wear records, spindle curves and true machine limits. Coefficients could then be calibrated and uncertainty quantified on held-out machining tests. Only after this separate stage would optimization of real machining productivity become defensible.')
sub('Verified scope and conclusion')
add('In the declared synthetic experiment, the original paceval engine successfully evaluated 58 reusable CNC expression graphs and screened 8,000 manufacturing parameter candidates against explicit host-managed constraints. The results support a numerical integration feasibility claim only.')
sub('Selected traceable references')
add('1. Sandvik Coromant, Milling formulas and definitions. https://www.sandvik.coromant.com/en-gb/knowledge/machining-formulas-definitions/milling-formulas-definitions','small')
add('2. ISO 8688-1:1989, Tool life testing in milling — Part 1: Face milling, confirmed 2022. https://www.iso.org/standard/16091.html','small')
add('3. Kennametal, Milling technical information, force and power estimation. https://www1.mscdirect.com/images/solutions/kennametal/millingTechInfoFormulas.pdf','small')
add('4. paceval Mathematical Engine, original C/C++ API. https://github.com/paceval/paceval','small')
add('Research scope: synthetic CNC/milling feasibility study. No industrial customer data, production deployment, machine control, model certification or measured speed advantage.','small')
report.build(story,onFirstPage=foot,onLaterPages=foot)
print('WROTE',DEST)
