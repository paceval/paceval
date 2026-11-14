#!/usr/bin/env python3
"""English scientific publication. Every page is rendered separately in review after export."""
import sys,math,html,json,csv
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Image,Spacer,PageBreak,Table,TableStyle,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
output=root/'paceval_Additive_Manufacturing_Thermal_Window_Whitepaper_EN.pdf'
reg='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bd='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',reg));pdfmetrics.registerFont(TTFont('DV-Bold',bd))
navy=colors.HexColor('#102f48');dark=colors.HexColor('#263744');teal=colors.HexColor('#157d8d');muted=colors.HexColor('#506376');light=colors.HexColor('#eaf2f5');orange=colors.HexColor('#bc5524')
styles={
 'title':ParagraphStyle('coverTitle',fontName='DV-Bold',fontSize=19.3,leading=25,textColor=navy,spaceAfter=12),
 'subtitle':ParagraphStyle('sub',fontName='DV',fontSize=11.0,leading=16,textColor=muted,spaceAfter=11),
 'eyebrow':ParagraphStyle('brow',fontName='DV-Bold',fontSize=8.2,leading=13,textColor=teal,spaceAfter=10),
 'h':ParagraphStyle('h',fontName='DV-Bold',fontSize=14.0,leading=19,textColor=navy,spaceAfter=12,spaceBefore=1),
 'h2':ParagraphStyle('h2',fontName='DV-Bold',fontSize=10.5,leading=15,textColor=navy,spaceBefore=13,spaceAfter=7),
 'body':ParagraphStyle('b',fontName='DV',fontSize=9.1,leading=14.0,textColor=dark,spaceAfter=10),
 'small':ParagraphStyle('sm',fontName='DV',fontSize=8.0,leading=12.6,textColor=muted,spaceAfter=9),
 'cap':ParagraphStyle('cap',fontName='DV',fontSize=8.0,leading=11.8,textColor=muted,alignment=TA_CENTER,spaceAfter=10),
 'cell':ParagraphStyle('cell',fontName='DV',fontSize=7.6,leading=11,textColor=dark),
 'thead':ParagraphStyle('thead',fontName='DV-Bold',fontSize=7.5,leading=10.8,textColor=navy),
 }
doc=SimpleDocTemplate(str(output),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=22*mm,bottomMargin=21*mm,author='paceval research demonstrator',title='Programmable Thermal Process Windows for Laser Powder Bed Fusion with paceval')
W=A4[0]-36*mm
story=[]
def para(text,style='body'):story.append(Paragraph(text,styles[style]))
def heading(text):para(text,'h')
def h2(text):para(text,'h2')
def pic(name,width_mm=169,caption='',max_height_mm=None):
    path=root/'figures'/name
    from PIL import Image as PILImage
    with PILImage.open(path) as p:ow,oh=p.size
    width=min(width_mm*mm,W);height=width*oh/ow
    if max_height_mm and height>max_height_mm*mm:height=max_height_mm*mm;width=height*ow/oh
    story.append(Image(str(path),width=width,height=height))
    if caption:para(caption,'cap')
def table(headers,rows,widths=None):
    cells=[[Paragraph(html.escape(str(h)),styles['thead']) for h in headers]]
    for row in rows:cells.append([Paragraph(html.escape(str(v)),styles['cell']) for v in row])
    t=Table(cells,colWidths=widths or [W/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),light),('GRID',(0,0),(-1,-1),0.28,colors.HexColor('#cfdde4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8fbfc')])]))
    story.append(t);story.append(Spacer(1,9))
def new():story.append(PageBreak())
def draw_page(canvas,doc):
    canvas.saveState()
    if doc.page>1:
        canvas.setStrokeColor(colors.HexColor('#d3e5e9'));canvas.line(18*mm, A4[1]-15.5*mm,A4[0]-18*mm,A4[1]-15.5*mm)
        canvas.setFont('DV-Bold',7.6);canvas.setFillColor(navy);canvas.drawString(18*mm,A4[1]-12.8*mm,'PACEVAL   /   ADDITIVE MANUFACTURING RESEARCH')
    canvas.setStrokeColor(colors.HexColor('#d3e5e9'));canvas.line(18*mm,14.2*mm,A4[0]-18*mm,14.2*mm)
    canvas.setFont('DV',7.4);canvas.setFillColor(muted);canvas.drawString(18*mm,10.2*mm,'Research demonstrator | 14 November 2026 | Synthetic data')
    canvas.drawRightString(A4[0]-18*mm,10.2*mm,f'{doc.page}')
    canvas.restoreState()
# cover
para('PACEVAL  /  SCIENTIFIC RESEARCH &amp; VERIFIED MATHEMATICAL EXECUTION','eyebrow')
para('Programmable Thermal Process Windows for Laser Powder Bed Fusion with paceval','title')
para('A reusable execution-graph study of thermal screening, versioned heat-source surrogates, process margins, model sensitivities and sampled numerical enclosures','subtitle')
pic('00_additive_thermal_window_hero.png',174,'Concept illustration; not a computed thermal field, real melt-pool observation, or industrial certification.')
para('<b>Research outcome.</b> Twelve real paceval MCP 4.26 formula graphs were executed at 81 parameter combinations (972 graph-point evaluations); three TINC-enabled graphs supplied nine numerical enclosures, independently checked at 90-decimal precision. This is a synthetic, two-probe mathematical functionality demonstration, not industrial process validation.','body')
para('Scope: regularized moving-source conduction proxy, controlled isotropic and anisotropic model versions, reusable scalar and composite graphs, and a separately provided original-SDK C++ reproduction pathway.','small')
new()
heading('1. Introduction: industrial use case and current state of the art')
para('Metal powder bed fusion (PBF-LB/M) produces parts by selectively melting metallic powder with a scanning laser. In candidate process planning, laser power, scanning speed, absorptivity, thermal conduction and geometric location jointly affect the predicted thermal field. Process engineers require reliable ways to compare many parameter combinations before undertaking detailed simulation and experimental qualification.')
para('The proposed use case in the original WP 02 is thermal process-window screening, not a substitute for a full thermal-fluid multiphysics solver. The working question is whether the paceval mathematical engine can execute versioned heat-source expressions and their process constraints reproducibly while keeping the application, measurement inputs and engineering decisions outside the mathematical graph.')
h2('Current scientific and industrial practice')
para('Analytical moving-source equations of Rosenthal-type describe conduction-dominated temperature distributions under simplified conditions. More complete methods include finite-element and finite-volume thermal models, computational fluid dynamics and models of keyhole behaviour and powder morphology. Recent reviews (2026) emphasize combining appropriately calibrated low-order methods with higher-fidelity simulations. A good algebraic numerical result is not, by itself, evidence of a valid physical melt-pool prediction.')
para('NIST AM Bench 2022 and 2025 challenge programmes provide independent measurement and modeling targets for metal additive manufacturing, including track and pad melt-pool geometry, thermal histories and cooling or solidification behaviour. A NIST overview published July 2026 highlights the availability and relevance of controlled benchmark datasets. The 2025 challenges include adjacent laser tracks and powder-layer scenarios. These sources motivate a later calibrated model-to-measurement comparison, but this study does not import or fit their measurements.')
h2('Concrete industrial workflow')
para('Hypothetical engineering example: a process development team proposes combinations of commanded laser power and scan speed for a new material. A screening system computes temperature proxies at a near-surface and a subsurface observation point. It reports positive or negative margins relative to declared lower and upper temperature limits, retaining separate mathematical model versions. A real organization would use the output to select candidates for metrology, experiments, higher-fidelity simulation and process qualification.')
new()
heading('2. Research question, architecture and evidence classes')
para('Can an unmodified paceval execution engine represent the complete, regularized source temperature, alternative effective-radius geometry, combined thermal process-window margin, logical flag, analytic parameter sensitivity and model-version difference with persistent graph handles and independent numerical verification?')
pic('01_workflow_schematic.png',168,'Figure 1. Conceptual workflow and division of responsibilities. This image is a schematic, not a computed temperature field.')
table(['Layer','Responsible implementation','What was actually tested'],[
 ['Thermal expressions and constraints','12 paceval mathematical graph handles','Executed via real MCP 4.26, 81 input sets'],
 ['TINC for sampled values','Three additional paceval graph handles','Three points per graph, actual interval output'],
 ['Input schema, decisions and CSV','C++ host, not graph mathematics','Source syntax checked; local library not executed'],
 ['Independent verification','mpmath 90-digit reference, explicit arithmetic','324 reconstructed numerical checks plus nine TINC inclusions'],
], [39*mm,77*mm,58*mm])
para('The delivered project contains the original SDK header and bridge implementation, a C++ entry point, a strict numeric CSV schema, and CMake/CTest instructions. A compatible Linux shared library was not available in the authoring environment, so local C++ linking and runtime results must not be inferred from the remotely executed MCP calculations.','small')
new()
heading('3. Defined mathematical models and assumptions')
para('The following formulas are the mathematical specification of the original WP 02, with an explicit research-only model extension. All physical variables use SI base units: power P in W, scan speed v in m/s, length x,y,z,r0 in m, temperature in K, conductivity k in W/(m K), density rho in kg/m3, heat capacity cp in J/(kg K), absorptivity eta dimensionless.')
# render math via matplotlib for reliable formula typography
fig,ax=plt.subplots(figsize=(11,3.9));ax.axis('off')
lines=[r'$\alpha=\frac{k}{\rho c_p},\quad r_1=\sqrt{x^2+y^2+z^2+r_0^2}$',r'$T_1=T_0+\frac{\eta P}{2\pi k r_1}\exp\!\left[-\frac{v(x+r_1)}{2\alpha}\right]$',r'$r_2=\sqrt{x^2+(y/\beta)^2+(z/\gamma)^2+r_0^2}$',r'$g_{\rm window}=\min\!\left(T_{\rm depth}-T_{\rm liquidus},\ T_{\rm upper}-T_{\rm surface}\right)$']
for j,line in enumerate(lines):ax.text(.03,.91-j*.24,line,fontsize=18,transform=ax.transAxes,va='center')
fig.savefig(root/'figures/model_equations.png',dpi=230,bbox_inches='tight',pad_inches=.1);plt.close(fig)
pic('model_equations.png',165,'Mathematical specification. V2 substitutes the exploratory anisotropic radius r2 into the same temperature formula.')
para('V1 uses the regularized isotropic radius. V2 introduces dimensionless lateral and depth scaling parameters beta and gamma, without claiming a corresponding exact heat-equation solution. Both versions share a surface probe at (0,0,0) and a designated depth probe at (-15,10,45) micrometres. The independent host validates all positive material parameters, finite values, nonzero effective radius, physical ordering of temperature thresholds and allowable input ranges.')
para('The two-probe flag is (depth temperature >= illustrative liquidus) AND (surface temperature <= illustrative upper limit). This is an intentionally limited proxy. It does not establish a melt-pool boundary or demonstrate that all relevant locations are simultaneously within limits.','small')
new()
heading('4. Inputs, scenario parameters and model versions')
para('A deterministic 9 by 9 parameter grid contains 81 thermal-screening scenarios. The original WP 02 proposes a much larger 100 by 100 by 100 workload for future study; that large experiment has not been carried out in the current research release. The present scope prioritizes verified mathematical paths and documented scientific limits.')
table(['Input quantity','Research value / range','Interpretation'],[
 ['Laser power P','120 to 440 W, 9 values','Commanded optical power, hypothetical'],
 ['Scan speed v','0.15 to 0.75 m/s, 9 values','Positive movement along the x direction'],
 ['k, rho, cp','35 W/(m K); 8200 kg/m3; 500 J/(kg K)','Illustrative fixed thermal properties'],
 ['eta, T0','0.3; 300 K','Illustrative absorptivity and baseline temperature'],
 ['r0, liquidus, upper','60 micrometres; 1600 K; 3100 K','Illustrative regularization and thermal limits'],
 ['V2 beta, gamma','0.85 and 1.4','Exploratory anisotropic effective-radius scaling'],
 ['Surface and depth probes','(0,0,0) and (-15,10,45) micrometres','Two locations, not volumetric melt-pool geometry'],
], [45*mm,58*mm,71*mm])
h2('Version control and sensitivity')
para('Separate long-lived computation handles implement V1 and V2 simultaneously. The model comparison computes T2 at the depth probe minus T1 at that probe. The analytic V1 sensitivities dTdepth/dP and dTsurface/dv are independently derived and included as executed paceval graphs; no undocumented automatic differentiation is claimed. The model-to-model differences reflect assumptions and require future calibration against physical measurements.')
new()
heading('5. paceval execution architecture and functionality')
para('Each of the twelve function groups was registered through real paceval MCP 4.26 and executed at every scenario point in the recorded 81-point multi-graph batch. The original SDK C++ program contains equivalent formula registrations and calls to its native scalar, batch and multi-graph interfaces, but actual local execution remains a pending reproducibility step.')
table(['Industrial mathematical purpose','Actual engine owner','Graph families / strategy'],[
 ['Temperature at two independent probes','paceval MCP','V1 and V2 surface/depth expressions'],
 ['Thermal diffusivity','paceval MCP','k/(rho*cp) as a separate reusable graph'],
 ['Conservative process margin','paceval MCP','Infix min of two physical-temperature margins'],
 ['Discrete process-window conditions','paceval MCP','Relational comparisons combined with AND'],
 ['Analytic sensitivity to power and speed','paceval MCP','Explicit derivative formula graphs'],
 ['Version-dependent temperature delta','paceval MCP','Direct composition of both model expressions'],
 ['Candidate generation and CSV reading/writing','C++ host (unexecuted SDK)','Validated literal grammar, paceval conversion calls'],
 ['Independent reference and TINC audit','Python mpmath','No native reference is represented as engine execution'],
],[67*mm,37*mm,70*mm])
para('A distinct operator self-test also exercised signed remainder versus mathematical modulo, infix min/max, mixed relational and logical operations, and XOR. Its MCP result cannot certify the local SDK build. The local C++ implementation contains tests for these operators and both original paceval floating-point/string conversion routines, including an explicit numeric-literal whitelist to prevent expression interpretation from untrusted CSV cells.')
new()
heading('6. Executed calculations, numerical verification and provenance')
table(['Recorded evidence','Actual executed or verified outcome'],[
 ['Main paceval MCP calculation','12 created and executed graphs; 81 scenarios; 972 graph-point evaluations; no per-value errors'],
 ['Additional TINC calculation','3 additional graphs and 9 concrete intervals; actual lower and upper bounds returned'],
 ['Independent high-precision audit','90 decimal digits; 324 reconstructed grid checks; all 9 sampled TINC inclusions passed'],
 ['Operator self-test','6 graph registrations with 3 input sets per graph, actual MCP execution'],
 ['C++ compiler check','g++ C++17 syntax check succeeded; no local SDK binary execution'],
 ['Large WP 02 proposed study','Not performed; public experimental AM Bench measurement comparison not performed'],
],[55*mm,119*mm])
para('<b>Data provenance qualification.</b> All 81 scenario combinations were actually evaluated through the paceval MCP batch API. The complete machine-readable response, however, was not directly exported to the local artifact container. The publication CSV instead reconstructs intermediate power values from transcribed actual engine outputs at the two power endpoints and the mathematically affine dependence on P. Additional intermediate returned results are independently cross-checked. The resulting CSV is a carefully documented derived record, not an unchanged engine output file.')
para('Independent verification codes, scenarios, formula strings, evidence metadata and detailed numeric audit records are included in the GitHub package. Numerical difference tables comparing paceval with native calculations are intentionally restricted to technical audit files, not the public narrative of this report.')
new()
heading('7. Executed temperature surfaces and process screening')
para('The following surfaces illustrate the fixed material/geometry parameter set across the executed laser-power and scan-speed grid. The axes and colors are thermal model values, not measured melt-pool temperatures. Values are regenerated from returned engine endpoints under the exact affine power rule.')
pic('02_surface_temperature_v1.png',153,'Figure 2. Model V1 surface-temperature surrogate across the operating grid.',max_height_mm=90)
pic('03_depth_temperature_v1.png',153,'Figure 3. Model V1 subsurface thermal-probe response across the same grid.',max_height_mm=90)
new()
heading('8. Versioned thermal process-window interpretation')
para('Model V2 changes the effective-radius geometry, demonstrating controllable formula revision while preserving common candidate inputs and independent graph handles. The following maps show mathematical two-probe threshold conditions only. Neither map predicts actual lack of fusion or keyhole formation.')
pic('05_versioned_process_window.png',161,'Figure 5. V1 and V2 two-probe threshold classifications. Green is a surrogate condition, not machine acceptance.',max_height_mm=75)
pic('06_conservative_margin.png',156,'Figure 6. V1 conservative signed thermal margin. The zero contour separates these two artificial constraints.',max_height_mm=88)
new()
heading('9. Model sensitivity and controlled revisions')
para('An explicit sensitivity graph for dTdepth/dP and an independent graph for dTsurface/dv have been executed by paceval. The temperature-change fields are shown as scientific scenario illustrations. V2 is not assumed superior to V1: it introduces an uncalibrated anisotropic parameterization whose validity depends on future measurements.')
pic('07_power_sensitivity.png',158,'Figure 7. Thermal sensitivity to power at the synthetic depth probe.',max_height_mm=85)
pic('08_model_revision_delta.png',158,'Figure 8. Controlled depth-temperature delta between the two independently retained model versions.',max_height_mm=85)
new()
heading('10. Numerical interval checks and reproducibility')
para('Three additional TINC-enabled paceval computations were used for surface temperature, depth temperature and conservative V1 margin at three selected power-speed settings. For each of nine values the actual paceval service returned lower and upper numerical limits; independent high-precision reference values were checked to lie inside the supplied bounds. These are finite sample checks for the explicitly represented floating-point inputs, not a global guarantee for arbitrary uncertain input sets.')
pic('09_tinc_interval_widths.png',156,'Figure 9. Actual sampled paceval TINC enclosure widths; shown in units of 10^-10 K.',max_height_mm=92)
para('The TINC experiment does not address uncertainty from the imposed liquidus, absorptivity, conductivity, heat-source regularization, model choice, instrument calibration or thermal-fluid physics. A true interval uncertainty analysis of material properties would require validated input bounds and whole-domain interval methods, not merely these pointwise numerical enclosures.')
new()
heading('11. Industrial interpretation, limitations and future validation')
pic('10_probe_profiles.png',152,'Figure 10. Synthetic surface/depth probe trajectories versus laser power at a fixed scan speed.',max_height_mm=88)
para('The practical result is a reusable expression-based thermal screening chain with transparent model versions and interpretable marginal quantities. A high-fidelity thermal-fluid simulation, material laboratory testing and geometry measurements remain indispensable. The simplified source formula omits phase-change enthalpy, powder packing, melt convection, dynamic absorptivity, evaporation, recoil pressure, spatter and keyhole formation. V2 further modifies the radius without deriving an anisotropic heat-equation solution.')
para('A sensible industrial continuation would start by identifying a specific alloy and machine, selecting the correct NIST AM Bench single-track or pad dataset with a fully documented DOI and data usage rights, calibrating heat-source parameters on a separated training subset and evaluating predeclared melt-pool and thermal-history residuals on withheld measurements. Only following independent model-to-experiment agreement could a process engineer use the outcome to prioritize physically meaningful candidates. No process or safety certification is asserted here.')
new()
heading('12. Reproducibility, technical boundaries and scientific sources')
para('The release contains the C++ source and original paceval bridge/header files, a CMake build definition, the complete versioned formula manifest, deterministic numeric input CSV, explicit data schema, recorded MCP endpoint and TINC files, a provenance-qualified derived grid CSV, independent 90-digit Python verification, source scripts for all diagrams and the present English PDF.')
para('<b>Linux reproduction.</b> Supply a compatible, original paceval shared library separately and run:')
para('<font name="DV"><b>cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so</b></font>','small')
para('<font name="DV"><b>cmake --build build -j</b></font> and <font name="DV"><b>ctest --test-dir build --output-on-failure</b></font>. The CTest includes operator and conversion self-tests, a real numeric CSV-to-graph-to-CSV path, and independent Python checks. These local tests could not be run during this authoring session because the binary runtime was absent.','small')
h2('Selected primary sources')
for s in [
 'NIST AM Bench (2026), benchmark programme and datasets: https://www.nist.gov/ambench',
 'NIST (2026), Enabling Modelers to Test Their Simulations against Rigorous, Highly Controlled AM Benchmark Data: https://www.nist.gov/publications/enabling-modelers-test-their-simulations-against-rigorous-highly-controlled-additive',
 'NIST AM Bench measurement data and referencing guidance (updated 6 November 2026): https://www.nist.gov/ambench/direct-am-bench-data-links-and-referencing-guidance',
 'NIST-hosted paper on uncertainty sources in laser powder bed fusion: https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=928087',
 'Advanced Numerical Modeling of Powder Bed Fusion (2026): https://pmc.ncbi.nlm.nih.gov/articles/PMC12843373/',
 'ISO/ASTM 52900:2021, confirmed 2025: https://www.iso.org/standard/74514.html',
 'paceval API and operator documentation: https://paceval.com/api/ and https://paceval.com/product-brief/',
]:para(s,'small')
para('Conclusion: the study provides a successful real MCP numerical functionality demonstration with independently checked models and interval samples, plus an unexecuted but syntax-checked local C++ reproduction pathway. Model validity and industrial usefulness remain open scientific questions.','body')
doc.build(story,onFirstPage=draw_page,onLaterPages=draw_page)
print(output)
