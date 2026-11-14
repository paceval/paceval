#!/usr/bin/env python3
"""Evidence-driven English WP07 PDF. All scientific figures from executed paceval CSV."""
from pathlib import Path
import json,html
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,Table,TableStyle,KeepTogether
from reportlab.lib.utils import ImageReader
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures';R=ROOT/'results'
E=json.loads((R/'execution_evidence.json').read_text());AUD=json.loads((R/'scientific_audit.json').read_text())
PDF=ROOT/'paceval_Advanced_Chip_Packaging_Warpage_Cure_Whitepaper_EN.pdf'
FONT='/usr/share/fonts/truetype/dejavu'
pdfmetrics.registerFont(TTFont('DV',FONT+'/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DVB',FONT+'/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DVM',FONT+'/DejaVuSansMono.ttf'))
NAVY=HexColor('#142d45');INK=HexColor('#33465b');TEAL=HexColor('#087b9b');CYAN=HexColor('#55d8e8');ORANGE=HexColor('#d77a3f');GREY=HexColor('#687b8b');PALE=HexColor('#eef5f7')
styles={
 'title':ParagraphStyle('ttl',fontName='DVB',fontSize=17,leading=24,textColor=NAVY,spaceAfter=10),
 'lead':ParagraphStyle('lead',fontName='DV',fontSize=10,leading=16.5,textColor=INK,spaceAfter=10),
 'body':ParagraphStyle('b',fontName='DV',fontSize=9.1,leading=15,textColor=INK,spaceAfter=9),
 'small':ParagraphStyle('s',fontName='DV',fontSize=8.2,leading=12.8,textColor=INK,spaceAfter=7),
 'foot':ParagraphStyle('ft',fontName='DV',fontSize=7.4,leading=11.7,textColor=GREY,spaceAfter=9),
 'head':ParagraphStyle('h',fontName='DVB',fontSize=11.1,leading=17,textColor=TEAL,spaceBefore=8,spaceAfter=5),
 'math':ParagraphStyle('m',fontName='DV',fontSize=9,leading=16,textColor=NAVY,leftIndent=15,rightIndent=10,spaceBefore=5,spaceAfter=9),
 'table':ParagraphStyle('cell',fontName='DV',fontSize=7.45,leading=11.6,textColor=INK),
 'tc':ParagraphStyle('tc',fontName='DVB',fontSize=7.7,leading=12,textColor=NAVY),
}
CONT=A4[0]-90
story=[]
def p(txt,style='body'):story.append(Paragraph(txt,styles[style]))
def h(txt):p(txt,'head')
def eq(txt):p(html.escape(txt),'math')
def new(title,kicker=None):
 if story:story.append(PageBreak())
 p(title,'title')
 if kicker:p(kicker,'lead')
def table(header,rows,widths=None):
 data=[[Paragraph(str(x),styles['tc']) for x in header]]+[[Paragraph(str(x),styles['table']) for x in row] for row in rows]
 t=Table(data,colWidths=widths or [CONT/len(header)]*len(header),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,0),.9,TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor('#f8fafc')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,10))
def fig(name,caption,w=CONT,h=None):
 from PIL import Image as PIL
 with PIL.open(FIG/name) as im:ww,hh=im.size
 height=h or w*hh/ww
 item=Image(str(FIG/name),width=w,height=height)
 cap=Paragraph(caption,styles['foot'])
 story.append(KeepTogether([item,Spacer(1,5),cap]))

def firstPage(canvas,doc):
 W,H=A4;canvas.saveState();canvas.setFillColor(NAVY);canvas.rect(0,0,W,H,stroke=0,fill=1)
 canvas.setFillColor(HexColor('#0b617b'));canvas.rect(0,H-15,W,15,stroke=0,fill=1)
 canvas.setFillColor(CYAN);canvas.setFont('DVB',18);canvas.drawString(45,H-69,'paceval.   RESEARCH SERIES')
 canvas.setFillColor(colors.white);canvas.setFont('DVB',23);canvas.drawString(45,H-137,'ADVANCED CHIP PACKAGING')
 canvas.setFont('DVB',20);canvas.drawString(45,H-177,'WARPAGE & CURE STRESS')
 canvas.drawString(45,H-211,'SCREENING')
 canvas.setFillColor(HexColor('#d7ecf4'));canvas.setFont('DV',10.5);canvas.drawString(45,H-240,'Three-layer laminate mechanics  |  Actual paceval execution  |  Independent verification')
 # The original image is an art-directed conceptual cover. It is not scientific data.
 im=ImageReader(str(FIG/'00_chip_packaging_hero.png'));iw,ih=im.getSize();w=W-90;ht=w*ih/iw
 canvas.drawImage(im,45,H-275-ht,width=w,height=ht,mask='auto')
 canvas.setFillColor(HexColor('#9fbbc9'));canvas.setFont('DV',8.1);canvas.drawString(45,H-283-ht,'Conceptual illustration, not a simulation mesh or measured package.')
 canvas.setStrokeColor(HexColor('#4c8ea1'));canvas.line(45,155,W-45,155)
 canvas.setFillColor(HexColor('#e4eff6'));canvas.setFont('DV',10)
 canvas.drawString(45,128,'A reproducible synthetic research demonstrator for semiconductor packaging')
 canvas.drawString(45,106,f"{E['unique_domain_graphs_executed']} verified executable domain graphs  |  {E['scenario_count']:,} scenarios  |  Two scientific model versions")
 canvas.setFont('DV',8.5);canvas.setFillColor(HexColor('#8daec0'));canvas.drawString(45,60,'WP 07   •   English research whitepaper   •   14 November 2026')
 canvas.restoreState()

def laterPage(canvas,doc):
 W,H=A4;canvas.saveState();canvas.setFillColor(NAVY);canvas.rect(0,H-19,W,19,stroke=0,fill=1)
 canvas.setFillColor(TEAL);canvas.setFont('DVB',9);canvas.drawString(45,H-40,'PACEVAL  /  SEMICONDUCTOR PACKAGING RESEARCH')
 canvas.setStrokeColor(HexColor('#c8d9e0'));canvas.line(45,49,W-45,49)
 canvas.setFillColor(GREY);canvas.setFont('DV',7.5);canvas.drawString(45,33,'WP 07  |  Synthetic mathematical study  |  14 November 2026')
 canvas.drawRightString(W-45,33,f'{doc.page}')
 canvas.restoreState()

# The first page consists of canvas artwork, no duplicated flowable content.
story.append(Spacer(1,660))
new('1. Industrial challenge and workflow','Thermomechanical mismatch in advanced packaging can create stresses and global deformation during curing and thermal processing.')
p('Advanced semiconductor packages integrate dissimilar materials, including silicon, bonded layers, epoxies and substrates. When temperature changes, different coefficients of thermal expansion (CTEs) create incompatible free strains. Thermoset materials may also contract during curing and progressively stiffen. The resulting residual stresses can warp a package, contributing to assembly and reliability concerns. The exact relationship depends on the process history and material response. [1–6]')
h('Hypothetical industrial decision workflow')
p('An engineering team selects candidate layer thicknesses, materials, curing assumptions and temperature conditions. The workflow checks data units and physical domains, evaluates the layerwise eigenstrains, solves free-laminate force and moment balances, calculates signed curvature and stresses, compares two deliberately different cure models and ranks candidates against user-specified mathematical thresholds. Promising or ambiguous candidates are then sent to experimental characterization and validated nonlinear finite-element modeling.')
h('The research question')
p('<b>Can substantial packaging mechanics, cure kinetics, sensitivities, limits and model comparisons be executed as reusable original paceval graphs within a reproducible independent C++ workflow, with the principal end values checked by a separately coded mathematical reference?</b> This study evaluates functional coverage, not execution speed, manufacturing yield or qualification.')
h('Contributions beyond the original WP 07')
p('The original two-page research proposal describes a thermal mismatch strain, an elastic stress proxy and a calibrated geometry-factor curvature approximation. This implementation replaces that curvature factor with a fully specified three-layer laminate force/moment calculation. It adds post-gel cure shrinkage, illustrative cure-dependent effective modulus, explicit analytic sensitivity expressions, a time-resolved kinetic state, scalar and multi-graph execution, an independent high-precision reference, and a versioned combined screening score.')
p('The packaging geometry is simplified intentionally so mathematical graph functionality can be independently checked. All input material numbers in this first research stage are synthetic.','small')

new('2. State of the art and industrial context')
h('Recent experimental and modeling progress')
p('NIST’s CHIPS AWACKSM program, active since November 2023 and updated on 2 October 2026, focuses on quantitative cure kinetics, thermomechanical properties, residual stresses and warpage for polymeric packaging materials. The associated data portal makes measurement descriptions and published datasets discoverable [1,2]. A 2025 ECTC contribution links residual stress evolution to polymer cure and shrinkage measurements [3].')
p('A 2024 Materials & Design study combines cure shrinkage and viscoelasticity in post-mold cure optimization [4]. A 2026 multiphysics study treats process-induced warpage in fan-out wafer-level packages with experimentally characterized cure and viscoelastic behavior [5]. NIST work presented at ECTC 2026 reports that the thermoset processing pathway changes final material properties [6]. Such results motivate explicit post-gel terms, while also making clear that true packaging predictions need measured, history-dependent properties.')
h('Current industrial methods and metrology')
p('Engineering workflows use established finite-element and multiphysics platforms. Siemens documents thermo-mechanical warpage analysis for electronic packaging, and Ansys includes a substrate-warpage structural example [7,8]. These tools can account for detailed geometry, interfaces, constraints and stress distributions that are intentionally absent in this lightweight screening calculation.')
p('JEDEC JESD22-B112C, issued in November 2023, defines an elevated-temperature package-warpage measurement method covering the thermal range of surface-mount soldering [9]. Neither a calculated curvature nor a simple center-to-edge parabolic deflection is automatically equivalent to such a measured result.')
h('Where paceval fits')
p('The proposed role is an explicit mathematical evaluation engine inside a larger application. paceval evaluates the formulas for repeatable parameter sets; C++ manages the data and any time-dependent state and an independent toolchain checks results. Process simulation, material-model calibration, manufacturing metrology and fracture/reliability qualification remain outside the demonstrated engine scope.')

new('3. Defined model and assumptions')
h('Free, three-layer equi-biaxial elastic laminate')
p('The nominal stack consists of a silicon-like substrate (layer 1), a representative compliant die/bond region (layer 2) and a polymer encapsulant region (layer 3). Each layer is homogeneous, isotropic and perfectly bonded; the temperature and effective degree of cure are spatially uniform. The free laminate is modeled in the small-strain, small-curvature regime. No edge, corner, bump, die-pattern or anisotropy resolution is attempted.')
p('Layer thickness boundaries are z₀ = 0, z₁ = h₁, z₂ = h₁ + h₂ and z₃ = h₁ + h₂ + h₃. The plane-stress equi-biaxial modulus is Ēᵢ = Eᵢ/(1 − νᵢ). The in-plane mechanical stress proxy is σᵢ(z) = Ēᵢ[ε₀ + zκ − ε*ᵢ]. The sign convention places the origin at the lower substrate surface and defines positive signed curvature with increasing strain towards increasing z.')
h('Material numbers, provenance and dimensions')
table(['Quantity','Synthetic fixed parameter','Interpretation'],[
 ('Stress-free reference','Tᵣ = 423.15 K','An assumed effective model reference, not a measured gel temperature'),
 ('Layer thicknesses','h₁ = 500 µm; h₂ = 70 µm','h₃ varied over 250 to 700 µm'),
 ('Young moduli','E₁ = 130; E₂ = 2.5; E₃ = 8 GPa','Illustrative, uncalibrated values'),
 ('Poisson ratios','ν₁ = 0.28; ν₂ = 0.35; ν₃ = 0.32','Biaxial elastic material reduction'),
 ('Thermal expansion','α₁ = 2.6; α₂ = 45 µK⁻¹','α₃ varied from 10 to 25 µK⁻¹'),
 ('Cure assumptions','a = 0.85, aᵍ = 0.4, gᴱ = 0.8','Illustrative stationary screening state')],[CONT*.27,CONT*.32,CONT*.41]);
p('V1 is thermal-only. V2 adds post-gel encapsulant shrinkage and a phenomenological cure-modulus multiplier. The solid-mechanics equations are intentionally independent of any unverified supplier modulus, cure experiment or JEDEC acceptance criterion.','small')

new('4. Constitutive equations and model versions')
h('Thermal and cure eigenstrains')
eq('ε*ᵢ(T) = αᵢ (T − Tᵣ);  Ēᵢ = Eᵢ/(1 − νᵢ)')
eq('V1: ε*₃ = α₃ (T − Tᵣ);  Ē₃ = E₃/(1 − ν₃)')
eq('V2: ε*₃ = α₃ (T − Tᵣ) − β max(a − aᵍ, 0)/(1 − aᵍ)')
eq('V2: Ē₃ = E₃ [1 + gᴱ (a − aᵍ)]/(1 − ν₃)')
p('β is the dimensionless effective linear shrinkage scale and a is the degree of cure. The gel switch is a crude representation of when a polymer begins to accumulate constrained stress. The V2 modulus multiplier is a synthetic algebraic sensitivity model, not an independently measured temperature–cure constitutive relation. The scanned domain assumes a ≥ aᵍ, positive moduli, and positive laminate determinant.')
h('Force and moment closure')
p('Integrating the layer stress through its thickness yields the extensional stiffness A (N/m), extension–bending coupling B (N), bending stiffness D (N·m), effective eigenstrain force N* (N/m), and effective eigenstrain moment M* (N):')
eq('A = Σ Ēᵢ (zᵢ − zᵢ₋₁);       B = ½ Σ Ēᵢ (zᵢ² − zᵢ₋₁²)')
eq('D = ⅓ Σ Ēᵢ (zᵢ³ − zᵢ₋₁³)')
eq('N* = Σ Ēᵢ ε*ᵢ (zᵢ − zᵢ₋₁);  M* = ½ Σ Ēᵢ ε*ᵢ (zᵢ² − zᵢ₋₁²)')
p('The free laminate has zero externally applied net in-plane force and moment, so A ε₀ + Bκ = N* and B ε₀ + Dκ = M*. The unique solution requires Δ = A D − B² > 0. Every reported stiffness integral and the resulting curvature are actually evaluated via paceval graphs.')

new('5. Signed deformation and sensitivities')
h('Closed-form laminate solution')
eq('Δ = A D − B² > 0;   ε₀ = (D N* − B M*)/Δ;   κ = (A M* − B N*)/Δ')
eq('w_edge = κ W²/8;   w(x,y) = κ(x² + y²)/2')
p('Here w_edge is the one-dimensional signed deflection between the center and an edge at x = ±W/2 under a parabolic small-slope assumption. The separate w(x,y) expression is an idealized equi-biaxial 2D visualization and is not an actual package surface, full peak-to-valley metric or finite-element solution. W is the assumed lateral package width in metres.')
h('Interface endpoint stress')
p('The program evaluates the stress at the top and bottom of each of the three layers, producing six linearly elastic endpoint stress values. The maximum of their absolute values is a transparent screening proxy for a simple homogeneous laminate; it is not an interfacial fracture energy or a measure of solder-joint damage.')
h('Analytic sensitivities actually executed by paceval')
p('At fixed cure degree and effective moduli, temperature enters the model through CTE eigenstrains. With N*ₜ and M*ₜ the temperature derivatives of their respective eigenstrain resultants:')
eq('∂κ/∂T |ₐ = (A M*ₜ − B N*ₜ)/Δ')
p('In V2, the additional shrinkage parameter enters only the layer-3 eigenstrain at fixed degree of cure and model stiffness:')
eq('∂ε*₃/∂β = −(a − aᵍ)/(1 − aᵍ)')
eq('∂κ/∂β |ₐ,T = [A(∂M*/∂β) − B(∂N*/∂β)]/Δ')
p('Both derivative formulas are explicitly derived and independently controlled against high-precision references. No automatic differentiation capability is claimed for the SDK.')

new('6. Cure kinetics and parameter screening')
h('A special-case autocatalytic model')
eq('da/dt = [k₁(T) + k₂(T)a] (1 − a)')
eq('kⱼ(T) = kⱼ,ref exp{ −Eₐⱼ/R [1/T − 1/Tₖᵢₙ] }')
p('The post-gel illustrative thermal sequence uses a 423.15 K hold, cooldown to 298.15 K and a final room-temperature period. Its degree-of-cure derivative is evaluated as a persistent paceval graph for each integrator stage; the explicit fourth-order Runge–Kutta solver and time/temperature scheduling are orchestrated by C++. This is a controlled synthetic simulation; it does not identify a real resin reaction pathway or a process-dependent stress-free reference.')
h('Full-factorial scenario design')
table(['Independent input','Evaluated values','Unit'],[
 ('Layer-3 thickness','250, 400, 550, 700','µm'),('Package width','12, 16, 20, 24, 28','mm'),('Layer-3 CTE','10, 15, 20, 25','µK⁻¹'),('Shrinkage coefficient β','0.6, 1.2, 1.8, 2.4','per mille'),('Temperature','298, 328, 358, 388','K')],[CONT*.32,CONT*.49,CONT*.19]);
p('Together these five factors produce 1,280 distinct, synthetically generated inputs. Both V1 and V2 evaluate every input, producing 2,560 model/scenario combinations. This factorial design explores model sensitivity and constraint behavior; the values are not a probabilistic representation of foundry manufacturing lots.')

new('7. Real paceval execution architecture')
p('The C++ program uses the original version-4.25 header and library. Persistent graph handles are registered once and evaluated in actual scalar and multi-graph batch calls. Intermediate outputs are passed numerically from graph stage to graph stage; C++ does not silently replace essential constitutive mathematics with native arithmetic.')
table(['Stage / mathematics','Owner','Graph family or host rationale'],[
 ('S1: Arrhenius kinetics, cure rate, moduli, eigenstrains','paceval','KIN1/KIN2, CURE_RATE, EBAR1/2, V1/V2_EBAR3, V1/V2_EIGEN3'),
 ('S2: laminate integral resultants A, B, D, N*, M*','paceval','EXTENSION_A, COUPLING_B, BENDING_D, EIGEN_FORCE_N, EIGEN_MOMENT_M'),
 ('S3: curvature, strain, six endpoint stresses, derivatives','paceval','SIGNED_CURVATURE, MEMBRANE_STRAIN, STRESS1/2/3, D_CURV_D_T, V2_D_CURV_D_BETA'),
 ('S4: continuous margins, limit guard and score','paceval','WARP_MARGIN, STRESS_MARGIN, SCREEN_GUARD, SCREEN_SCORE'),
 ('S5: model change and idealized 2D mesh deflection','paceval','DELTA_CURVATURE, DELTA_WARPAGE, RELATIVE_WARPAGE, SHAPE_DEFLECTION'),
 ('RK4 state, CSV safety, scenario generation, orchestration','C++ host','Stateful procedures and external file I/O, not scalar graph evaluation'),
 ('Reference control','independent','Native C++ / 90-digit Python, not substituted for paceval')
 ],[CONT*.39,CONT*.17,CONT*.44]);
p('The actual run recorded <b>'+str(E['unique_domain_graphs_executed'])+' executed domain graphs</b>, '+str(E['scenario_count'])+' parameter cases, '+str(E['batch_calls'])+' batch calls and '+str(E['scalar_calls'])+' scalar calls. The separate output file records the graph-point count without confusing it with distinct scenarios. Its graph inventory and formula manifest preserve exact graph IDs, formulas, units, version labels and execution owners. The original external Linux .so is not bundled with the public package.')

new('8. Measured software output, not measured hardware')
p('All numbers below originate from running the real C++/paceval application on deterministic synthetic inputs. They are calculated physical-model observables, not observations from semiconductor fabrication or metrology. Their independent high-precision tests are described separately, without public engine-vs-native error tables.')
table(['Reference configuration at 298.15 K','V1: thermal','V2: thermal + cure'],[
 ('Signed curvature (1/m)','−1.942268','−3.456160'),
 ('Signed center-to-edge deflection (µm)','−97.1134','−172.8080'),
 ('Maximum sampled elastic stress (MPa)','102.325','181.606'),
 ('Illustrative combined guard (0/1)','1','0')
 ],[CONT*.52,CONT*.24,CONT*.24]);
p('Reference inputs are a 20 mm width, 550 µm encapsulant thickness, 20 µK⁻¹ encapsulant CTE and 0.0018 shrinkage coefficient. The numerical guard uses an illustrative 100 µm absolute edge-deflection threshold and 150 MPa absolute sampled-stress limit. It does not represent a design sign-off or an industry-standard threshold.')
fig('fig01_curvature_temperature.png','Figure 1. Signed model curvature versus temperature, fixed effective degree of cure. Both curves are actual paceval-computed end values.',w=CONT*.93)

new('9. Thermal loading and model dependence')
fig('fig02_warpage_temperature.png','Figure 2. Signed center-to-edge deflection from the executed laminate equations. Dashed lines represent an illustrative mathematical guard.',w=CONT*.83)
fig('fig03_stress_temperature.png','Figure 3. Maximum absolute sampled layer-endpoint elastic stress. This indicator is not an experimentally validated failure measure.',w=CONT*.83)

new('10. Matching candidates and design map')
fig('fig04_matched_model_scenarios.png','Figure 4. Matched scenario outcomes reveal the effect of adding cure shrinkage and effective modulus changes, not a comparison of numerical software engines.',w=CONT*.81)
fig('fig05_cure_design_map.png','Figure 5. Encapsulant thickness and synthetic shrinkage sensitivity at a fixed selected temperature, package width and encapsulant CTE.',w=CONT*.81)

new('11. Time-dependent cure process')
fig('fig06_cure_degree_profile.png','Figure 6. Degree-of-cure history from a C++ RK4 state integrator whose nonlinear kinetic RHS is evaluated by the original paceval graph.',w=CONT*.81)
fig('fig07_time_resolved_warpage.png','Figure 7. V2 signed edge displacement over the same dwell and cooling program. The trajectory is an illustrative calculation, not a measured curing run.',w=CONT*.81)

new('12. Surface deformation and analytic sensitivity')
fig('fig08_warpage_surface_3d.png','Figure 8. 3D visualization from separately evaluated paceval graph w(x,y) = κ(x²+y²)/2. This is a small-slope conceptual surface, not a finite-element package.',w=CONT*.71)
fig('fig09_temperature_sensitivity.png','Figure 9. Explicitly derived fixed-cure partial curvature sensitivities, independently checked. Their nearly constant values follow the fixed-coefficient laminate assumptions.',w=CONT*.79)

new('13. Mathematical guard outcomes')
fig('fig10_screen_guard_counts.png','Figure 10. Counts of mathematical threshold conditions satisfied on the same synthetic factorial design; no yield or reliability inference is warranted.',w=CONT*.84)
p('The executable produces '+str(E['V1_screen_guard_passes'])+' passing V1 cases and '+str(E['V2_screen_guard_passes'])+' passing V2 cases out of '+str(E['scenario_count'])+' examined in each version. The number is conditioned on synthetic values, fixed model limitations and chosen illustrative bounds. It cannot be used to estimate manufacturing yield, supplier material quality or package acceptability.')

new('14. Independent verification and limitations')
h('Real SDK, independent implementation')
p('A compiled Linux C++ executable has successfully invoked the supplied original paceval library for graph creation, scalar evaluation, verified multi-graph batch input/output ordering, graph cleanup, finite numerical outputs and bidirectional text/number conversion. Unit tests cover arithmetic, relational and composite logical conditions, infix min/max, negative remainder and mathematical mod, zero mismatch, and strict numeric-only CSV schemas. All graph expressions listed as executed are evaluated on the main data path or its real scientific output surface, not only registered as dormant test strings.')
p('Independent native C++ computes closed-form laminate force and moment equilibria and six endpoint stresses. A separate Python reference uses 90 decimal digits and exact binary-double decoding of the input numbers. The final audit includes '+str(E['native_reference_endvalue_checks'])+' native C++ end-value checks and '+str(AUD['high_precision_checks'])+' Python checks over '+str(AUD['high_precision_endvalue_rows'])+' sampled end-value rows, plus independent model comparison, surface deflection and RK4 cure-state tests. Exact details, any outlying cases and machine-readable numerical diagnostics are published in technical audit files. The public report deliberately does not tabulate engine-versus-native error values.')
h('Scientific boundaries')
p('The laminate is homogeneous, isotropic, elastic, thin and perfectly bonded. It ignores cure exotherm, gel-history reset, nonlinear viscoelastic or plastic behavior, stress relaxation, moisture, temperature gradients, die and bump patterns, 3D package supports, interfacial fracture and detailed geometry. Material parameters are not experimentally fitted. V2 modulus and shrinkage dependence is illustrative. The signed center-edge number is not a JEDEC-compliant warpage measurement, nor is the maximum endpoint stress a validated crack predictor. Hardware acceleration, economic value and industrial acceptance are outside the research scope.')

new('15. Outlook and reference literature')
h('Suggested next steps')
p('An experimentally grounded extension would fit cure kinetics, CTE, viscoelasticity and stress-free reference states to public NIST CHIPS-AWACKSM data or appropriately licensed supplier measurements. The screened cases could then be transferred to independent geometry-resolved FEM with calibrated temperature/cure memory, compared against measured whole-package warpage under JESD22-B112C-relevant temperature histories, and tested against actual product tolerances. A separate statistical uncertainty study would propagate credible measurement confidence intervals rather than treating a uniform synthetic grid as probabilistic evidence.')
h('Selected technical references')
refs=[
 '[1] NIST. Accurate Cure Kinetics, Stress, Mechanical Properties and Warpage. Updated 2 October 2026. https://www.nist.gov/programs-projects/accurate-cure-kinetics-stress-mechanical-properties-and-warpage',
 '[2] NIST. CHIPS-AWACKSM Data and Research Metrology Portal. 2025–2026. https://pages.nist.gov/CHIPS-AWACKSM-data/',
 '[3] Centellas et al. Advanced Metrology Suite for Linking Residual Stress to Fundamental Properties of Thermoset Packaging Materials. IEEE ECTC 2025. DOI:10.1109/ECTC51687.2025.00078',
 '[4] Um et al. Reduced warpage in semiconductor packages: Optimizing post-cure temperature profile considering cure shrinkage and viscoelasticity. Materials &amp; Design 245 (2024). DOI:10.1016/j.matdes.2024.113265',
 '[5] Baek et al. Multi-physics coupled modeling of process-induced warpage in advanced fan-out wafer-level semiconductor packages. J. Manufacturing Processes (2026). DOI:10.1016/j.jmapro.2026.07.036',
 '[6] NIST/Centellas et al. Controlling the Reaction Pathway to Tune Packaging Epoxy Properties. IEEE ECTC 2026. https://www.nist.gov/publications/controlling-reaction-pathway-tune-packaging-epoxy-properties',
 '[7] Siemens. Simcenter Simlab, PCB and electronic packaging mechanical modeling. https://www.siemens.com/en-us/products/simcenter/simulation-modeling-visualization/simlab/',
 '[8] Ansys. Mechanical Help 2025 R2. Structural example: Substrate Warpage. https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v252/en/PDFs/Mechanical.pdf',
 '[9] JEDEC JESD22-B112C. Package Warpage Measurement of Surface-Mount Integrated Circuits at Elevated Temperature, Nov 2023. https://standards.globalspec.com/std/14647106/jesd22-b112c',
 '[10] paceval. SDK/API documentation, version 4.25. https://paceval.com/api/'
]
for x in refs:p(x,'foot')

DOC=SimpleDocTemplate(str(PDF),pagesize=A4,topMargin=58,bottomMargin=63,leftMargin=45,rightMargin=45,title='Advanced Chip Packaging Warpage and Cure Stress Screening | paceval',author='paceval Research Demonstrator',pageCompression=1)
DOC.build(story,onFirstPage=firstPage,onLaterPages=laterPage)
print('PDF CREATED',PDF)
