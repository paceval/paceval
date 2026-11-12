#!/usr/bin/env python3
"""Rebuild the 14-page English scientific PDF from executed paceval data."""
from pathlib import Path
from xml.sax.saxutils import escape
import io, math, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
root=Path(__file__).resolve().parent.parent
pdf=root/'paceval_Heat_Pump_Twin_Whitepaper_EN.pdf'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',font));pdfmetrics.registerFont(TTFont('DVB',bold))
NAVY=colors.HexColor('#122d43');TEAL=colors.HexColor('#087f86');LIGHT=colors.HexColor('#edf6f5');INK=colors.HexColor('#233341');SUB=colors.HexColor('#5c6876');LINE=colors.HexColor('#d5e3e8')
W,H=A4;LEFT=47;RIGHT=47;BW=W-LEFT-RIGHT
sty={
 'title':ParagraphStyle('PTitle',fontName='DVB',fontSize=23,leading=31,textColor=NAVY,spaceAfter=12),
 'subtitle':ParagraphStyle('PSub',fontName='DV',fontSize=11,leading=16,textColor=SUB,spaceAfter=12),
 'h':ParagraphStyle('PH',fontName='DVB',fontSize=16,leading=21,textColor=NAVY,spaceAfter=15),
 'sh':ParagraphStyle('PSH',fontName='DVB',fontSize=10.2,leading=15,textColor=TEAL,spaceBefore=12,spaceAfter=6),
 'body':ParagraphStyle('PB',fontName='DV',fontSize=9,leading=14.8,textColor=INK,spaceAfter=10),
 'small':ParagraphStyle('PSmall',fontName='DV',fontSize=8,leading=12.8,textColor=INK,spaceAfter=6),
 'caption':ParagraphStyle('PCapt',fontName='DV',fontSize=7.5,leading=11,textColor=SUB,spaceAfter=7),
 'tiny':ParagraphStyle('PTiny',fontName='DV',fontSize=7,leading=10.8,textColor=INK),
 'meta':ParagraphStyle('PMeta',fontName='DV',fontSize=9,leading=14,textColor=TEAL,spaceAfter=10),
}
story=[]
def P(t,kind='body'):
 story.append(Paragraph(t,sty[kind]))
def H(t):P(t,'h')
def SH(t):P(t,'sh')
def S(n=8):story.append(Spacer(1,n))
def PAGE():story.append(PageBreak())
def TL(rows, widths=None):
 # Avoid relying on user markdown pipe handling by constructing typed cells
 cells=[]
 for i,r in enumerate(rows):
  cells.append([Paragraph(str(c),sty['tiny']) for c in r])
 t=Table(cells,colWidths=widths or [BW/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,-1),(-1,-1),.4,LINE)]))
 # Paragraph style cannot inherit text color from cell, use white custom for headers.
 # Replace row zero cells with white text.
 for j in range(len(rows[0])):
  cells[0][j]=Paragraph(str(rows[0][j]),ParagraphStyle('header'+str(j)+str(len(story)),parent=sty['tiny'],fontName='DVB',textColor=colors.white))
 t._cellvalues=cells
 story.append(t);S(9)
def FIG(name,caption,w=BW,h=None):
 import PIL.Image
 img=root/'figures'/(name+'.png');im=PIL.Image.open(img);iw,ih=im.size
 if h is None:h=w*(ih/iw)
 story.append(Image(str(img),width=w,height=h));P(caption,'caption')
def FIGPAIR(a,b,ca,cb):
 # Wide vertically stacked plots at a legible final printed scale.
 # ReportLab preserves aspect ratios and keeps labels/legends inside the page.
 FIG(a,ca,w=BW*.61)
 S(4)
 FIG(b,cb,w=BW*.61)
 S(5)
# Math expression renders as transparent high-resolution figure to avoid raw TeX in PDF.
def EQ(tex, width=BW*.95):
 fig=plt.figure(figsize=(10, .65),dpi=200);fig.patch.set_alpha(0)
 fig.text(.02,.5,'$'+tex+'$',va='center',ha='left',fontsize=16,color='#13344a')
 output=io.BytesIO();fig.savefig(output,format='png',dpi=230,transparent=True,bbox_inches='tight',pad_inches=.12);plt.close(fig);output.seek(0)
 from PIL import Image as PILImage
 im=PILImage.open(output);iw,ih=im.size;h=width*ih/iw
 story.append(Image(output,width=width,height=h));S(7)

def footer(c,doc):
 c.saveState();c.setStrokeColor(LINE);c.setLineWidth(.6);c.line(LEFT,44,W-RIGHT,44)
 c.setFont('DV',7);c.setFillColor(SUB);c.drawString(LEFT,31,'paceval  |  WP_038  |  Heat-Pump Twin Performance Expressions  |  2026')
 c.drawRightString(W-RIGHT,31,str(doc.page));c.restoreState()

# p1
P('PACEVAL  |  SCIENTIFIC RESEARCH DEMONSTRATOR  |  WP_038','meta')
P('Reusable Heat-Pump Twin Performance Expressions','title')
P('A reproducible, batch-driven C++/paceval study of synthetic heating performance maps, composite system metrics and formula versioning','subtitle')
S(8)
hero=root/'figures'/'00_heat_pump_twin_hero.png'
story.append(Image(str(hero),width=BW,height=BW/2))
P('Concept illustration; not a computed equipment diagram or measurement.','caption')
S(10)
P('<b>Executed research outcome.</b> Twenty-three persistent mathematical graph definitions and 6,000 synthetic operating candidates were evaluated using the original paceval Linux engine. Their composite thermal, electrical, economic and constraint expressions were independently audited.','body')
P('<b>Scientific boundary.</b> The results show expression-execution feasibility, not physical calibration of a specific heat pump, validated frost behavior, measured seasonal efficiency or certification to EN 14511 / EN 14825.','body')
PAGE()
# p2
H('1. Introduction: industrial use case and state of the art')
P('Buildings increasingly rely on electric heat pumps for low-carbon heating. Equipment developers and building-energy engineers must estimate how heating capacity and electricity consumption vary with the outdoor source temperature, the sink-water delivery temperature, partial loading and building heat demand. A digital twin may use these performance maps repeatedly for planning, supervisory analysis and operational what-if studies.')
P('A heat pump transfers heat from a source to a higher-temperature sink. Its coefficient of performance (COP) is the ratio of useful heating to input electrical power at a defined operating point. Unlike an idealized thermodynamic cycle, real equipment also depends on compressor speed, heat exchangers, auxiliaries, frost and cycling, and cannot be certified by a synthetic algebraic map.')
SH('Established and recent methods')
P('EnergyPlus documents equipment performance relationships based on temperature-dependent capacity and energy-input-ratio curves. Modelica and FMI support physical modeling and co-simulation. A 2026 Applied Energy systematic review found that digital-twin model choice must account for robustness, generalizability and integration, while a 2026 IEA Heat Pumping Technologies experimental comparison highlighted how dynamic cycling and defrost behavior can differ from selected standard test points.')
SH('Research question')
P('Can the full set of repeatable algebraic performance-map calculations, not only a small COP equation, be registered as reusable and versioned paceval graphs, evaluated through authentic scalar and batch API calls, and independently verified in an industrially interpretable workflow?')
SH('Experiment input and output')
TL([['Operating inputs','Model outputs'],['Source and sink temperatures, load ratio, nominal capacity','COP, available and delivered heat, electricity'],['Thermal demand, auxiliary power, tariff, time','Heat margins, electrical bounds, costs, sensitivities']], [BW*.49,BW*.51])
P('All coefficients and operating profiles in this report are synthetic. No actual manufacturer or client equipment supplied calibration or monitoring data.','small')
PAGE()
# p3
H('2. Research architecture and mathematical ownership')
P('The host C++ application generates validated operating points, manages the real paceval library, retains calculation handles, executes official Multi-Graph-Batch calls and writes deterministic result tables. It also evaluates explicit acceptance rules and ranks the computed candidate scores. No external numerical engine generates the reported scientific outputs.')
TL([['Processing stage','Actual executor'],['Input parsing, permitted ranges, deterministic scenarios','C++ host'],['COP V1/V2, heating capacity, delivered heat','paceval'],['Part-load and synthetic cold-weather factors','paceval'],['Power, system COP, source heat, energy, electricity cost','paceval'],['Three signed operating margins and two policy scores','paceval'],['Two analytical raw-COP sensitivities','paceval'],['Select lowest score, write CSV, aggregate replay energy','C++ host'],['Independent reference mathematics','Native C++ / mpmath only for verification']], [BW*.69,BW*.31])
SH('Reusable computation graphs')
P('Twenty-two operating-map functions and one aggregate replay energy-ratio function are each created once and preserved as live SDK handles while a large sequence of inputs is evaluated. The graph registry and a function-level execution inventory are included, establishing an auditable distinction between paceval mathematics and host orchestration.')
SH('Why this division matters')
P('The host does not recompute significant domain results after receiving arbitrary intermediary graph values: the full delivered-heat, electric-power, system-COP, constraint and cost expressions are submitted directly to paceval. Stateful candidate ranking and temporal summation remain host tasks.')
PAGE()
# p4
H('3. Defined synthetic mathematical operating model')
P('Temperatures in degrees Celsius; all heat and electrical rates in kW. The coefficients define a hypothetical heating-mode example within -15 to +20 °C source, +30 to +60 °C sink and 0.25 to 1.0 load ratio. No claimed parameter set belongs to an actual heat pump.')
SH('3.1 Temperature-dependent reference COP')
EQ(r'C_1=4.4+0.065T_s-0.045(T_k-35)-0.0006(T_k-35)^2+0.002T_s(T_k-35)',BW*.97)
P('Version 2 changes the base, source-temperature and interaction coefficients. Both versions remain registered simultaneously and are sampled at the same inputs.')
SH('3.2 Capacity and part-load models')
EQ(r'F_{cap}=1+0.014T_s-0.005(T_k-35)',BW*.72)
EQ(r'Q_{avail}=Q_{rated}F_{cap},\quad Q_{heat}=\lambda Q_{avail}',BW*.76)
EQ(r'F_{PLR}=0.82+0.18\lambda-0.06(1-\lambda)^2',BW*.80)
SH('3.3 Declared hypothetical cold-weather modifier')
EQ(r'F_{cold}=1-0.08\exp\left(-\left(\frac{T_s-1}{3}\right)^2\right)',BW*.81)
P('The cold-weather modifier is deliberately synthetic. Its shape is useful for demonstrating nonlinear expression reuse but is not a measured defrost penalty. The model contains no dynamic frost, refrigerant, heat-exchanger or control state.')
PAGE()
# p5
H('4. Heat balance, power, margins and sensitivities')
P('The model returns complete system-side algebraic results using paceval, not merely the COP polynomial.')
EQ(r'C_{eff}=C_1F_{PLR}F_{cold}',BW*.62)
EQ(r'P_{comp}=Q_{heat}/C_{eff},\quad P_{el}=P_{comp}+P_{aux}',BW*.83)
EQ(r'C_{system}=Q_{heat}/P_{el},\quad Q_{source}=Q_{heat}-P_{comp}',BW*.91)
EQ(r'E_{heat}=Q_{heat}\Delta t,\quad Cost=P_{el}\Delta t\,c_{el}',BW*.82)
SH('4.1 Example screening margins')
P('The three mathematically computed signed guards are <b>heating margin</b> = delivered heat minus requested load, <b>electrical margin</b> = 4.8 kW minus electric input, and <b>COP margin</b> = system COP minus 2.5. The host interprets nonnegative margins as satisfying the <i>illustrative</i> screening rule; this is not physical equipment protection logic.')
SH('4.2 Explicit derivatives of the raw polynomial')
EQ(r'\frac{\partial C_1}{\partial T_s}=0.065+0.002(T_k-35)',BW*.74)
EQ(r'\frac{\partial C_1}{\partial T_k}=-0.045-0.0012(T_k-35)+0.002T_s',BW*.92)
P('These derivatives are sensitivities of the stated COP map only. They are not derivatives of a time-dependent digital-twin system. Weighted composite policy scores V1/V2 are also registered mathematical expressions, with the independent host choosing the minimum.')
PAGE()
# p6
H('5. Deterministic research workload and method')
TL([['Workload dimension','Actual executed coverage'],['Synthetic operating candidates','6,000 validated cases'],['Distinct retained graphs','23 mathematical functions'],['Multi-graph candidate outputs','132,000 values'],['Temperature performance surface','3,721 (61 x 61) points'],['Seven-day operating replay','168 hourly points'],['Simultaneous formula version sweep','101 matched points'],['Host invalid-input regression','5 / 5 correctly rejected']], [BW*.59,BW*.41])
SH('Operating data and declared domains')
P('Deterministic pseudorandom generation produces source temperatures between -13 and +18 °C and sink temperatures between +31 and +57 °C. Part-load, declared rated capacity, thermal demand, tariff, interval length and auxiliary input vary within the documented input contract. Surface and time-series data are generated by separate fixed sweeps, and every outcome is written to CSV at 17-significant-digit precision.')
SH('Batch correctness and lifecycle')
P('The application checks graph construction and the result layout of the Multi-Graph-Batch API using a one-point scalar probe before executing independent batches. Handles remain alive for the full experiment and are deleted on shutdown; error flags and nonfinite results are checked. CTest runs a separate smaller workload with the original shared library, without any simulated replacement.')
SH('Independent checks')
P('The released reference scripts separately calculate selected results using native C++ and 80-decimal-digit mpmath arithmetic, check the full composite output chain and validate domain and physical accounting identities. Detailed technical numerical differences reside in audit files, not in this published report.')
PAGE()
# p7
H('6. Executed results and scientific status')
TL([['Verified result','Recorded outcome'],['paceval retained mathematical graphs','23'],['Independent native scalar results','4,963 checked'],['Independent 80-decimal-digit calculations','880 checked'],['Synthetic candidates inside three example margins','2,613 of 6,000'],['Seven-day delivered heat','1,080.19 kWh'],['Seven-day electrical consumption','331.20 kWh'],['Seven-day scenario energy ratio','3.2615'],['Real-SDK CMake/CTest','1 / 1 passed']], [BW*.64,BW*.36])
P('The energy ratio is calculated from the aggregated synthetic replay values. It is not a measured seasonal performance factor, a manufacturer COP claim or an EN 14825 SCOP result. It must not be applied outside the stated artificial scenario.')
FIG('05_cop_distribution','Figure 5. Distribution of system COP calculated at 6,000 deterministic synthetic operating points; the line marks an illustrative numerical threshold.',w=BW*.77)
PAGE()
# p8
H('7. Industrial operating maps: COP and capacity')
P('The temperature performance maps demonstrate a reusable algebraic representation that an external building simulation or equipment application could sample at alternative operating conditions. The surfaces are generated from paceval batch values; they are not laboratory performance maps.')
FIGPAIR('01_system_cop_surface','02_system_cop_contours','Figure 1. Three-dimensional system-COP surface, source and sink temperature inputs.','Figure 2. Matching two-dimensional COP contours, fixed part-load and auxiliaries.')
S(13)
P('At a fixed part-load setting, the hypothetical map generally favors warmer sources and lower sink-water temperature. The graph reveals the model specification rather than a universal behavioral law: real performance depends on actual equipment and its control strategy.')
PAGE()
# p9
H('7. Industrial operating maps: capacity and electricity')
P('Separating available heating capacity from electrical input helps a screening tool assess whether a model can satisfy load and power constraints at a declared operating point.')
FIGPAIR('03_available_capacity_surface','04_electric_power_surface','Figure 3. Declared capacity modifier and synthetic rated heating capacity across temperatures.','Figure 4. Electrical input, including the specified auxiliary power, derived by paceval.')
S(13)
P('Both quantities come from their own complete reusable paceval expressions. The C++ host does not substitute an unrelated performance calculation during visualization. No compressor map or device test specification is inferred from the plotted numbers.')
PAGE()
# p10
H('7. Industrial scenarios: temporal replay and screening')
P('The seven-day profile is a deterministic operating-point sequence, not a time-integrated physical heat-pump state. Each hour is evaluated independently from its input conditions, and the host aggregates the returned paceval energy and power results.')
FIGPAIR('06_seven_day_replay','09_screening_decisions','Figure 6. Hourly thermal delivery and electricity demand over a synthetic 168-hour replay.','Figure 9. Which sampled input cases satisfy the three illustrative paceval guard margins.')
S(12)
P('A real supervisory system would also evaluate start/stop losses, transient building loads, refrigerant limits and safety interlocks. The current study verifies the mathematical policy and replay arithmetic, not operational safety.')
PAGE()
# p11
H('8. Formula versions and analytical sensitivities')
P('Two COP map variants and two weighted policy scores are preserved in independently accessible paceval graph handles. This demonstrates controlled mathematical model changes, while the host maintains version identifiers and candidate selection logic.')
FIGPAIR('07_formula_versions','08_analytical_sensitivities','Figure 7. Both system-COP model versions evaluated at the same input sweep.','Figure 8. Two explicit derivatives of the raw COP polynomial, as paceval graphs.')
S(13)
P('These formulas offer a transparent basis for model-update regression tests and engineering what-if studies. They do not constitute automatic differentiation of an arbitrary algorithm, nor prove an industrial improvement over competing simulation engines.')
PAGE()
# p12
H('9. Validation, source code and reproducibility')
P('The original SDK interface files are distributed in <b>src/</b> with their upstream notices intact. The runtime shared library is intentionally external. CMake uses the original headers and implementation, and the C++ program executes paceval graph creation, scalar checking and Multi-Graph-Batch evaluation before exporting five CSV result artifacts.')
SH('Release inventory')
TL([['File or location','Reproducibility role'],['src/heat_pump_twin.cpp','Original SDK C++ workflow, formula graph registry and input contract'],['src/CMakeLists.txt','External shared-library build with actual integration CTest'],['examples/*.csv','Inputs, complete paceval outputs and formula-version sweeps'],['results/math_execution_inventory.csv','Function-level actual math-execution responsibility'],['src/high_precision_reference.py','Separate independent 80-digit numerical audit'],['src/verify_results.py','Composite energy and operating-margin consistency'],['src/make_figures.py / src/make_whitepaper.py','Regenerate plotted scientific figures and final PDF'],['src/check_readme_math.py','Static GitHub math and relative-link regression checks']], [BW*.44,BW*.56])
SH('Reproduction commands')
P('Configure with <b>cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=&lt;absolute-library-path&gt;</b>; compile with <b>cmake --build build -j</b>, execute <b>ctest --test-dir build --output-on-failure</b>, then run <b>./build/heat_pump_twin --out . --cases 6000</b>. Execute the included Python verification and plotting scripts as shown in the README.')
PAGE()
# p13
H('10. Industrial interpretation and scientific limitations')
SH('What has been demonstrated')
P('The research demonstrates the reuse of persistent mathematical expressions for physical-like operating maps and compound performance quantities. It confirms successful scalar and Multi-Graph-Batch execution, independent verification of the released results, explicit unit/domain contracts, temperature sensitivity formulas and simultaneous versioned model handling.')
SH('What has not been demonstrated')
P('The synthetic coefficients are not fitted to real equipment. No measured refrigerant properties, compressor map, system storage, transient defrost physics, building control feedback, equipment degradation, electrical-grid interaction or independent certification experiment is included. A seven-day energy quotient is not a standards-based SCOP. The declared guards are research policies, not validated hardware or regulatory limits.')
SH('From kernel to industrial digital twin')
P('A future application would need permitted test-bench and field datasets, documented model identification and uncertainty, measured frost/cycling behavior, a transient building/system solver, and model exchange or integration through an FMI/Modelica or EnergyPlus interface. A validation protocol should separate training/calibration points from unseen operation and quantify the errors of the entire operating process.')
SH('Research contribution')
P('The contribution is intentionally modest and verifiable: comprehensive reuse of an algebraic calculation layer for a transparent engineering heat-pump scenario. No computational-speed advantage, reduced emissions, energy savings or guaranteed physical prediction accuracy is asserted.')
PAGE()
# p14
H('11. Conclusion and external references')
P('<b>Conclusion.</b> The defined heat-pump mathematical performance kernel was implemented with the original paceval engine and executed for 6,000 synthetic operating points. The study confirmed 23 persistent formulas, multi-graph batch reuse, composite thermal/electrical and cost evaluation, independent verification and version-controlled modifications. Its scientific interpretation is limited to the specified mathematical model, not the prediction of a particular manufacturer device.')
SH('Selected technical and scientific sources')
refs=[
('1. Applied Energy, 2026','Modeling methods for chiller and heat pump systems in buildings: systematic review in the context of digital twins. doi:10.1016/j.apenergy.2026.127632'),
('2. Renewable and Sustainable Energy Reviews, 2026','State-of-the-art of digital twin HVAC+R systems for buildings. doi:10.1016/j.rser.2025.116601'),
('3. EnergyPlus Engineering Reference','Plant Loop Heat Pumps: performance temperature curves, capacity and electric-power calculations. energyplus.readthedocs.io'),
('4. IEA Heat Pumping Technologies, 2026','Experimental comparison of seasonal efficiency using EN 14825 and dynamic load emulation, May 2026.'),
('5. Functional Mock-up Interface','Specification for simulation and model exchange. fmi-standard.org/docs/main/'),
('6. Modelica Association','Modelica Language Specification. specification.modelica.org'),
('7. paceval SDK','Official open-source repository and C/C++ interface. github.com/paceval/paceval')]
for title,desc in refs:
 P('<b>'+escape(title)+'</b>: '+escape(desc),'small')
SH('Release boundaries')
P('All plotted values are generated from synthetic model inputs and authentic paceval output files. The broad cover visualization is conceptual. The external shared library is not included. Independent checks and exact formula definitions are supplied so results can be independently reproduced and extended.')
S(16)
P('paceval | Reusable Heat-Pump Twin Performance Expressions | Research package WP_038 | 13 November 2026','meta')

def build():
 doc=SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=LEFT,rightMargin=RIGHT,topMargin=56,bottomMargin=58,
                        title='Reusable Heat-Pump Twin Performance Expressions — paceval WP_038',author='paceval research demonstrator')
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 print('Wrote',pdf,round(pdf.stat().st_size/1024,1),'KiB')
if __name__=='__main__':build()
