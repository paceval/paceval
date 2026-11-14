#!/usr/bin/env python3
"""Generate a scientific English PDF from verified paceval outputs (no invented results)."""
from pathlib import Path
import csv,json
from collections import defaultdict
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
P=Path(__file__).resolve().parents[1];G=P/'figures';Q=P/'results'
source=json.loads((Q/'execution_evidence.json').read_text())
prec=json.loads((Q/'high_precision_audit.json').read_text())
records=list(csv.DictReader((Q/'screening.csv').open(newline='')))
report=P/'paceval_Composite_Cure_Autoclave_Whitepaper_EN.pdf'
regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',regular));pdfmetrics.registerFont(TTFont('DejaVuBold',bold))
navy=colors.HexColor('#142536');teal=colors.HexColor('#087b84');gold=colors.HexColor('#c48133');pale=colors.HexColor('#eef5f5');gray=colors.HexColor('#526271')
pageW,pageH=A4
styles={
 'h1':ParagraphStyle('H1',fontName='DejaVuBold',fontSize=19,leading=25,textColor=navy,spaceAfter=14),
 'h2':ParagraphStyle('H2',fontName='DejaVuBold',fontSize=11,leading=16,textColor=teal,spaceBefore=8,spaceAfter=7),
 'text':ParagraphStyle('Txt',fontName='DejaVu',fontSize=9.45,leading=15.5,textColor=navy,spaceAfter=10),
 'small':ParagraphStyle('Sml',fontName='DejaVu',fontSize=8.3,leading=13,textColor=navy,spaceAfter=7),
 'caption':ParagraphStyle('Cap',fontName='DejaVu',fontSize=8.25,leading=12,textColor=gray,spaceAfter=13),
 'coverTitle':ParagraphStyle('CvrTitle',fontName='DejaVuBold',fontSize=26,leading=33,textColor=navy,spaceAfter=16),
 'coverSub':ParagraphStyle('CvrSub',fontName='DejaVu',fontSize=12.5,leading=19,textColor=teal,spaceAfter=13),
 'tiny':ParagraphStyle('Tiny',fontName='DejaVu',fontSize=7.9,leading=11.2,textColor=navy),
}
def para(s,kind='text'):return Paragraph(s,styles[kind])
def addtitle(story,title):story.append(para(title,'h1'))
def fig(story,name,caption,width=492):
 path=G/(name+'.png');from PIL import Image as PIL
 with PIL.open(path) as im:w,h=im.size
 story.append(Image(str(path),width=width,height=width*h/w))
 story.append(para(caption,'caption'))
def tab(story,head,rows,widths=None):
 data=[[para(str(v),'tiny') for v in head]]+[[para(str(v),'tiny') for v in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),pale),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.8,teal),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7fafa')]),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8)]))
 story.append(t);story.append(Spacer(1,10))
def page(c,doc):
 c.setStrokeColor(colors.HexColor('#d7e1e4'));c.setLineWidth(.6);c.line(45,pageH-47,pageW-45,pageH-47)
 c.setFont('DejaVu',7.5);c.setFillColor(gray);c.drawString(46,pageH-40,'PACEVAL.  /  RESEARCH  /  ADVANCED MANUFACTURING')
 c.line(45,43,pageW-45,43);c.drawString(46,30,'WP 21  •  14 November 2026  •  Synthetic research demonstration')
 c.drawRightString(pageW-45,30,f'{c.getPageNumber():02d}')
def cover(c,doc):
 c.setFillColor(teal);c.rect(45,pageH-60,90,5,stroke=0,fill=1)
 page(c,doc)
S=[]
# PAGE 1
S.append(Spacer(1,24));S.append(para('WP 21  |  Scientific industrial research', 'coverSub'))
S.append(para('Composite Cure Kinetics and Autoclave Process Constraints','coverTitle'))
S.append(para('A numerical functional demonstrator using the original paceval Mathematical Engine','coverSub'))
S.append(Spacer(1,15))
S.append(Image(str(G/'00_composite_cure_hero.png'),width=497,height=248.5))
S.append(Spacer(1,16))
S.append(para('A connected mathematical study of autocatalytic thermoset curing, temperature gradients, vitrification-limited kinetics and deterministic recipe screening.','text'))
S.append(Spacer(1,14))
S.append(para('<b>Publication status:</b> Original paceval 4.25 execution with independently checked formula results. All thermal recipes and material coefficients are synthetic research inputs. This document is not a qualified manufacturing specification.','small'))
S.append(para('<b>Research artifact:</b> C++ source, independent validation programs, numerical results, formula manifest and ten reproducible scientific figures are included in the accompanying GitHub package.','small'))
S.append(PageBreak())
# PAGE 2
addtitle(S,'1. Introduction: industrial use case and current state of the art')
S.append(para('A cured carbon-fiber composite component is made by laying resin-impregnated reinforcement into tooling, applying vacuum and consolidation pressure, and following an autoclave temperature cycle. The cure process cannot be described by autoclave air temperature alone: the part heats and cools with finite thermal inertia, while chemical cross-linking releases heat inside the laminate. A thick region can therefore exhibit a delayed temperature response, an internal exotherm and a conversion history that differs from its exposed surfaces.'))
S.append(para('Industrial cure schedules include ramps, intermediate and final dwells, controlled cooling and pressure/vacuum sequences. Material suppliers such as Hexcel publish product-specific windows; their documentation explains the role of heat-up rate, temperature uniformity and cure-time initiation at the slowest thermocouple. These supplier requirements depend on resin formulation, laminate thickness, tooling and cure cycle [1].'))
S.append(para('Engineers already use finite-element composite cure tools and experimentally calibrated kinetic laws to assess temperature overshoot and internal conversion. Current academic research extends this to spatially nonuniform autoclave boundary conditions, airflow, tooling, thermal-fluid-solid coupling and tool-part contact [2–5]. The present demonstrator targets one smaller but reusable computational unit in that workflow: evaluation of many local mathematical material functions and screening margins while a separate host integrates the evolving spatial state.'))
S.append(para('<b>Illustrative manufacturing question.</b> Given candidate air temperature ramps and dwell temperatures for panels of several thicknesses, which mathematical recipes satisfy a chosen minimum conversion and peak-temperature margin? How does a vitrification-limited kinetic model change this answer relative to a standard autocatalytic model? The screening thresholds here are illustrative and must not be used for shop-floor release.'))
S.append(para('Inputs are recipe ramps, dwell temperatures and durations, thickness, heat transfer conditions, assumed material coefficients and pressure. Outputs include conversion profiles, reaction heat, local and peak temperatures, thermal gradients, signed constraints and version-specific mathematical acceptance.'))
S.append(PageBreak())
# PAGE 3
addtitle(S,'2. Research background and experimental objective')
S.append(para('The Kamal-Sourour phenomenological model is a common starting point for thermoset resin curing. It combines non-autocatalytic and autocatalytic terms with a declining remaining reaction fraction. This is not a first-principles chemistry model; its coefficients must be fitted to the specific material, commonly from differential scanning calorimetry (DSC) [6, 7].'))
S.append(para('As polymer conversion increases, molecular mobility can become diffusion-limited. A glass-transition correlation such as DiBenedetto provides one way to represent an increasing glass transition during cure [8]. The smooth diffusion factor implemented here is an illustrative correction, rather than a uniquely validated kinetic closure. The actual onset and severity of vitrification depend on resin chemistry and measurement history.'))
S.append(para('The 2025 study of Yang and colleagues addressed multidomain thermal-fluid-solid coupling in autoclave curing [2]. A July 2026 study examined how varying heat-transfer coefficients and component geometry affect curing [3]. A 2026 investigation of real-time CFRP autoclave control included tool-part interaction and experimental comparison [4]. A 2026 review summarizes the difficulty of coupling cure, heat and mechanics across scales [5]. These advances establish a clear limit for a reduced one-dimensional screening model.'))
S.append(para('<b>Research objective:</b> demonstrate that the original paceval runtime can create, retain and execute both versions of the local cure/thermal graph set; evaluate persistent graphs repeatedly in genuine multi-graph batches; and produce end-of-recipe mathematical constraints and version comparisons, with separate native and high-precision verification. The study makes no claims about runtime, energy savings, control-system deployment or material certification.'))
S.append(para('<b>Declared validation boundary:</b> numeric agreement with independently implemented equations and invariants is a functional mathematical result. It does not establish real thermal conductivity, resin DSC coefficients, pressure-induced void content, residual stresses or manufacturing quality for a specific laminate.'))
S.append(PageBreak())
# PAGE 4
addtitle(S,'3. Mathematical kinetic model')
S.append(para('The original WP 21 specifies two Arrhenius terms, the Kamal-Sourour autocatalytic cure rate, volumetric heat release and a required degree-of-cure margin. These four kernels remain intact within a broader network of executable graphs.'))
S.append(para('<b>Arrhenius coefficients:</b> k<sub>i</sub>(T) = A<sub>i</sub> exp(−E<sub>i</sub> / (R T)), i = 1,2. Temperature T is expressed in kelvin; E<sub>i</sub> is in joules per mole; A<sub>i</sub> is in reciprocal seconds.'))
S.append(para('<b>Baseline model V1:</b> dα/dt = [k<sub>1</sub>(T) + k<sub>2</sub>(T) α<super>m</super>] (1−α)<super>n</super>. Here 0 ≤ α ≤ 1 is the degree of conversion. Irreversible forward integration and an upper projection at unity are controlled in the C++ host.'))
S.append(para('<b>Diffusion-corrected model V2:</b> the V1 reaction term is multiplied by f<sub>diff</sub> = 1 / {1 + exp[(T<sub>g</sub>(α) − T)/ΔT<sub>g</sub>]}. The variable ΔT<sub>g</sub> is a positive model transition width.'))
S.append(para('<b>Glass-transition correlation:</b> T<sub>g</sub>(α) = T<sub>g,0</sub> + (T<sub>g,∞</sub> − T<sub>g,0</sub>) λα / [1 − (1−λ)α]. The synthetic material assumption uses λ = 0.68, T<sub>g,0</sub> = 260.15 K and T<sub>g,∞</sub> = 455.15 K.'))
S.append(para('<b>Exothermic source:</b> q̇ = ρ<sub>resin</sub> H<sub>c</sub> dα/dt, with units W/m³ of composite volume. The cumulative reacted enthalpy per unit volume at a state is ρ<sub>resin</sub> H<sub>c</sub> α. Both functions are executed in paceval; the host spatially aggregates the graph-derived end values.'))
S.append(para('paceval also evaluates the independently derived local temperature and prefactor sensitivities. These are explicit stored formulas, not a claim of automatic differentiation by the SDK. Versions coexist with independent handles and are compared only at equivalent input recipes.'))
S.append(PageBreak())
# PAGE 5
addtitle(S,'4. Thermal state and autoclave process constraints')
S.append(para('Ten finite-volume cells describe an effective one-dimensional laminate. For each layer, the model combines conduction, heat exchange at exposed faces, and reaction heat. In discrete form the original paceval graph returns the heat balance:'))
S.append(para('<b>ρc<sub>p</sub> dT/dt = k(T<sub>L</sub> − 2T + T<sub>R</sub>)/Δz² + b h(T<sub>air</sub> − T)/Δz + ρ<sub>resin</sub>H<sub>c</sub> dα/dt.</b> The boundary indicator b equals 1 at the outside cells and zero inside. Missing outer neighbors are assigned the boundary cell temperature for the discrete conductive term.'))
S.append(para('The spatially local thermal coefficients, boundary source, conduction source, heat-release forcing, local dT/dt diagnostic and chemical sensitivity are paceval graph outputs. The time-dependent heat equation is advanced by an implicit Euler tridiagonal solve in C++, while the conversion is integrated by a bounded forward step. The explicit dT/dt graph is retained as an auditable diagnostic; the implicit thermal solver is the actual temperature update.'))
S.append(para('The host must aggregate extrema over time and space because these are stateful reductions, not just scalar expressions. paceval evaluates the final per-recipe signed conversion, peak-temperature, thermal-gradient and pressure margins, their combined 0/1 quality indicator and a nonnegative soft violation score. A margin of exactly zero is accepted for these illustrated mathematical conditions.'))
S.append(para('The autoclave pressure input is used **only** in the mathematical acceptance margin. It does not couple to consolidation, void formation, viscosity, tool friction or the thermal equations; pressure-based product quality would require a separate validated materials model. The synthetic 10-cell discretization has not been proven converged for any actual component.'))
S.append(PageBreak())
# PAGE 6
addtitle(S,'5. Original paceval execution architecture')
S.append(para('All mathematical expression families listed below are registered once, evaluated through the original SDK version 4.25 and repeatedly reused. The actual application does not replace paceval with a stand-in evaluator. The host handles graph lifetimes, input schema, time integration, the spatial solve, state limits and file I/O.'))
rows=[('Arrhenius + baseline kinetics','paceval','V1_K1, V1_K2, V1_BASE_RATE / corresponding V2'),('Glass transition / diffusion','paceval','V1_TG, V2_TG, V2_DIFF_FACTOR'),('Reaction rate / heat / enthalpy','paceval','V*_CURE_RATE, V*_HEAT_SOURCE, V*_INTEGRATED_HEAT'),('Conduction / convection / temperature rate','paceval','V*_CONDUCTION_SOURCE, V*_BOUNDARY_SOURCE, V*_TEMPERATURE_RATE'),('Temperature and prefactor sensitivity','paceval','V*_SENS_T, V*_SENS_A1'),('Local margins / quality conditions','paceval','V*_MARGIN_*, V*_LOCAL_GUARD'),('Final process margins and score','paceval','G1_*, G2_*'),('Version differences and joint gate','paceval','CMP_*'),('Temporal state solver / extrema search','C++ host','Implicit Euler, Thomas solve, state and spatial management'),('Independent reference','C++ / Python','Separate native equations and 90-digit mpmath')]
tab(S,['Functional component','Actual owner','Graph IDs or rationale'],rows,[200,95,202])
S.append(para('<b>Data flow:</b> a validated numeric CSV recipe is parsed with the original paceval number-conversion function. The native library computes the local reaction and thermal coefficients in genuine multi-graph batches. C++ advances the state; end-of-cycle margins and model differences return to paceval for calculation. The C++ host then makes the publication-level screening classification and writes output using the original paceval float-to-string conversion.'))
S.append(PageBreak())
# PAGE 7
addtitle(S,'6. Deterministic workload and independent numerical checks')
S.append(para('This study executes <b>36 separate synthetic autoclave recipes</b>. Each model has 10 through-thickness cells and 841 sampled state times (including the initial state), corresponding to a 210-minute process simulation with a 15-second update. Both mathematical model versions are evaluated independently. The original WP 21 mentioned 1,000 possible candidate recipes as an experimental plan; this implementation makes no claim that 1,000 full transient recipes were executed.'))
rows=[('Parameter varied','Executed synthetic values'),('Laminate thickness','10, 14, 18 mm'),('Heating slope','1, 2, 3 °C/min'),('Autoclave dwell set point','145, 155, 165, 175 °C'),('Dwell duration','80, 95 or 110 min'),('Surface heat transfer','55 to 91 W/(m² K), recipe-specific'),('Illustrative process pressure','4.0 to 5.3 bar'),('Minimum conversion','0.88'),('Maximum part temperature','196 °C'),('Maximum thermal gradient','32 K')]
tab(S,['Input or model limit','Value'],rows,[245,252])
S.append(para('The C++ program checks every finite input, documented unit range, graph-creation result and batch result. The multi-graph layout is tested independently against analytically identifiable values. The native reference recalculates selected full local end values. A separate 90-digit mpmath program independently implements the equations, checks executed sample rows, material enthalpy and result margins and confirms monotonically increasing cure across stored trajectories. An additional independent dense-matrix solver verifies 880 temperature and conversion samples along a complete 10-layer trajectory. It does not represent a 90-digit time-trajectory re-integration.'))
S.append(PageBreak())
# PAGE 8
addtitle(S,'7. Executed results and evidence')
rows=[('Distinct domain graphs executed',str(source['unique_graphs_executed'])),('Synthetic recipes',str(source['scenario_count'])),('Model-recipe combinations',str(source['scenario_count']*2)),('Local state-node-time combinations',f"{source['model_node_time_evaluations']:,}"),('Native C++ end-value assertions',f"{source['native_endvalue_assertions']:,}"),('Independent 90-digit formula/end-value checks',f"{prec['high_precision_endvalue_checks']:,}"),('Recorded monotonic-state checks',f"{prec['state_monotonicity_checks']:,}"),('Independent full-trajectory state comparisons','880'),('Recipes passing in V1',f"{source['feasible_V1']} of {source['scenario_count']}"),('Recipes passing in V2',f"{source['feasible_V2']} of {source['scenario_count']}")]
tab(S,['Recorded result','Executed value'],rows,[326,171])
S.append(para('Across the specified synthetic recipe grid, the diffusion-limited V2 chemistry lowers conversion in many cases because its additional factor suppresses reaction when T<sub>g</sub> approaches the current part temperature. For the selected baseline equations, <b>26 recipes satisfy the illustrative V1 screen</b> and <b>25 recipes satisfy the V2 screen</b>. Those counts are conditional on the prescribed conditions, rather than measured process yields or a general prediction of industrial plant performance.'))
S.append(para('All scientific curves in the following pages originate from `results/cure_profiles.csv`, `results/screening.csv` or `results/model_comparison.csv` generated by the executed original paceval application. The high-detail title illustration is not a scientific simulation result. There are no claimed CPU, FPGA or energy-consumption comparisons.'))
S.append(PageBreak())
# PAGE 9
addtitle(S,'8. Thermal lag and conversion history')
fig(S,'fig01_temperature_cycle','Figure 1. Air temperature and three finite-volume layer histories for one actually simulated synthetic recipe in model V2.')
fig(S,'fig02_cure_evolution','Figure 2. The same recipe shows different central conversion histories under V1 and diffusion-limited V2 kinetics. The dashed requirement is illustrative.')
S.append(PageBreak())
# PAGE 10
addtitle(S,'9. Heat-release and vitrification indicators')
fig(S,'fig03_reaction_heat','Figure 3. Recorded original-paceval volumetric chemical heat-release rates, using the actual evolving central temperature and conversion.')
fig(S,'fig07_vitrification_transition','Figure 4. Estimated resin glass transition versus central part temperature for the same V2 recipe; this simplified relation is not experimental Tg data.')
S.append(PageBreak())
# PAGE 11
addtitle(S,'10. Dwell temperature and laminate thickness')
fig(S,'fig04_cure_vs_hold_temperature','Figure 5. Actual model-specific final minimum conversion grouped by synthetic hold temperature at 14 mm nominal thickness.')
fig(S,'fig05_peak_temperature_by_thickness','Figure 6. Peak temperatures grouped by thickness. Ranges reflect different synthetic recipes, not measurement uncertainty.')
S.append(PageBreak())
# PAGE 12
addtitle(S,'11. Screening and through-thickness gradients')
fig(S,'fig06_feasibility_windows','Figure 7. Fraction of the generated recipes passing all explicitly defined mathematical cutoffs, grouped by hold set point.')
fig(S,'fig08_cure_gradient_tradeoff','Figure 8. Conversion and spatial temperature-gradient relationships within the executed process cases.')
S.append(PageBreak())
# PAGE 13
addtitle(S,'12. Formula version effects and a 3D process surface')
fig(S,'fig09_model_difference','Figure 9. Difference in final minimum degree of cure, V2 minus V1, grouped by temperature and laminate thickness.',width=440)
fig(S,'fig10_3d_process_surface','Figure 10. Three-dimensional operating surface from real V2 results for 14 mm thickness. It is a sparse grid, not a calibrated optimizer or interpolated guarantee.',width=328)
S.append(PageBreak())
# PAGE 14
addtitle(S,'13. Interpretation, scientific limits and reproducibility')
S.append(para('The main positive outcome is an independently checked, reusable mathematical execution path: Arrhenius coefficients, cure rate, diffusion correction, exothermic source, thermal transport coefficients, sensitivities, quality margins and version comparison are truly calculated by paceval. The host carries numerical state evolution and file operations. Local agreement and physical monotonicity were checked separately, and all source and machine-readable evidence are included in the release.'))
S.append(para('<b>Important limitations.</b> The material coefficient table is synthetic, not DSC-fitted. The 1D heat-transfer coefficients and ten-node grid are reduced approximations; the demonstration does not include tool contact, anisotropy, resin flow, porosity, pressure-driven consolidation, cure shrinkage, viscoelastic stresses or a convergence/uncertainty study. The V2 glass-transition limiter is a scenario assumption. The reported mathematical pass flag cannot certify a real part, its process recipe or its structure.'))
S.append(para('<b>Reproduce the study.</b> Compile `src/composite_cure_main.cpp` and the original `src/paceval_main.cpp` against the separately supplied matching Linux shared library. Run the deterministic recipes from `input/recipes.csv`, verify with `scripts/verify_high_precision.py`, generate figures with `scripts/make_figures.py`, and execute CTest plus the archive-wide Markdown math/link checker. The external runtime is not redistributed. See `results/execution_evidence.json` for graph accounting and `results/high_precision_audit.json` for reference-check scope.'))
S.append(para('<b>Selected external sources:</b> [1] Hexcel, Prepreg Technology (2026), hexcel.com; [2] Yang et al., Materials 18, 1471 (2025); [3] Composites Part A 206, 109802 (2026); [4] Chinese Journal of Aeronautics 39, 103948 (2026); [5] Composites Part A 207, 109799 (2026); [6] NETZSCH Kinetics Neo, Kamal-Sourour model documentation; [7] Polymers 11, 127 (2019); [8] Polymers 11, 1804 (2019). Exact stable URLs are given in `docs/RESEARCH_SOURCES.md`.'))
S.append(para('<b>Next research directions.</b> Parameterize actual commercial resin from DSC and dielectric analysis, calibrate time-dependent boundary heat transfer and tooling contact, test both time/space convergence, add anisotropic heat conduction and resin rheology, and independently compare calculated temperature fields and degree of cure with thermocouple and DSC measurements under product-specific cure schedules.'))
doc=SimpleDocTemplate(str(report),pagesize=A4,topMargin=68,bottomMargin=57,leftMargin=46,rightMargin=46,title='Composite Cure Kinetics and Autoclave Process Constraints | paceval',author='paceval Research Demonstrator')
doc.build(S,onFirstPage=cover,onLaterPages=page)
print('Whitepaper',report,'size=',report.stat().st_size)
