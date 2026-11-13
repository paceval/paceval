#!/usr/bin/env python3
"""Generate a paginated research whitepaper from verified SDK result files."""
from pathlib import Path
import json, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.colors import HexColor,white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures';VAL=json.loads((ROOT/'results/high_precision_validation.json').read_text());RUN=json.loads((ROOT/'results/execution_summary.json').read_text());OUTPUT=ROOT/'paceval_Wind_Turbine_Digital_Twin_Whitepaper_EN.pdf'
assert RUN['paceval_graphs']==31 and VAL['status']=='passed'
for fname,path in [('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(fname,path))
NAVY=HexColor('#112a42');TEAL=HexColor('#087c91');CYAN=HexColor('#e8f5f7');GRAY=HexColor('#5a6875');ORANGE=HexColor('#d78b31');LIGHT=HexColor('#f2f7f9')
S={
 'heading':ParagraphStyle('H',fontName='DejaVu-Bold',fontSize=18,leading=24,textColor=NAVY,spaceAfter=13),
 'sub':ParagraphStyle('S',fontName='DejaVu-Bold',fontSize=11,leading=16,textColor=TEAL,spaceBefore=12,spaceAfter=6),
 'body':ParagraphStyle('B',fontName='DejaVu',fontSize=9.3,leading=14.5,textColor=NAVY,spaceAfter=8),
 'small':ParagraphStyle('Small',fontName='DejaVu',fontSize=8.1,leading=12.2,textColor=GRAY,spaceAfter=7),
 'caption':ParagraphStyle('Cap',fontName='DejaVu',fontSize=7.8,leading=11,textColor=GRAY,spaceAfter=12,alignment=TA_CENTER),
 'cover':ParagraphStyle('Cover',fontName='DejaVu-Bold',fontSize=23,leading=31,textColor=NAVY,spaceAfter=15),
 'subtitle':ParagraphStyle('Subt',fontName='DejaVu',fontSize=11,leading=18,textColor=TEAL,spaceAfter=15),
 'cell':ParagraphStyle('Cell',fontName='DejaVu',fontSize=8.1,leading=12,textColor=NAVY),
 'cellB':ParagraphStyle('CellB',fontName='DejaVu-Bold',fontSize=8.1,leading=12,textColor=NAVY)
}
STORY=[]
def p(text,kind='body'):STORY.append(Paragraph(text,S[kind]))
def h(text):p(text,'heading')
def sub(text):p(text,'sub')
def space(n=8):STORY.append(Spacer(1,n))
def page():STORY.append(PageBreak())
def tab(rows,widths=None):
 elems=[]
 for j,r in enumerate(rows):elems.append([Paragraph(str(c),S['cellB' if j==0 else 'cell']) for c in r])
 t=Table(elems,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),CYAN),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,LIGHT]),('LINEBELOW',(0,0),(-1,0),.7,TEAL),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9)]))
 STORY.append(t);space(9)
def img(name,width=460,maxh=257):
 path=FIG/(name+'.png');im=PILImage.open(path);w,hg=im.size;scale=min(width/w,maxh/hg);STORY.append(Image(str(path),width=w*scale,height=hg*scale))
def figure(name,caption, width=460,maxh=256):
 path=FIG/(name+'.png');im=PILImage.open(path);w,hg=im.size;scale=min(width/w,maxh/hg);story=[Image(str(path),width=w*scale,height=hg*scale),Paragraph(caption,S['caption'])];STORY.append(KeepTogether(story))

def formula(name,tex):
 fig=plt.figure(figsize=(9.6,.67),facecolor='white');fig.text(.02,.49,'$'+tex+'$',va='center',ha='left',fontsize=17,color='#193852');fig.savefig(FIG/(name+'.png'),dpi=180,bbox_inches='tight',pad_inches=.12);plt.close(fig)
formula('_eq_cp',r'C_{p,1}(\lambda,\beta)=0.475\exp[-((\lambda-7.6)/3.1)^2]\exp(-\beta/22)')
formula('_eq_energy',r'P_a=\frac{1}{2}\rho\pi R^2v^3C_p,\quad Q_a=\frac{P_a}{\omega},\quad F_t=\frac{1}{2}\rho\pi R^2v^2C_t')
formula('_eq_gen',r'S(e)=\frac{1}{2}[e+P_r-\sqrt{(e-P_r)^2+\epsilon^2}],\quad Q_g=\frac{S(e)}{\eta\omega}')
formula('_eq_rotor',r'J\dot\omega=Q_a-Q_g-D\omega,\qquad\omega_{n+1}=\omega_n+\Delta t\dot\omega_n')

# 1 Cover
p('PACEVAL  |  MATHEMATICAL RESEARCH DEMONSTRATOR','sub')
p('Wind-Turbine Digital Twin<br/>Coefficient Functions<br/>with paceval','cover')
p('A verified original-SDK C++ study of reusable aerodynamic coefficients, power, torque, sensitivities and reduced-order rotor dynamics.','subtitle')
img('00_wind_turbine_hero',475,238)
p('Cover artwork: original conceptual illustration. The scientific figures in this report are generated from actual paceval execution output, not measurements of a commercial turbine.','small')
space(12)
tab([['Evidence from actual run','Scope'],['31 reusable expression graphs and 308,791 paceval batch outputs','Real library execution'],['3,721 coefficient-map points, 4,800 operating samples and 720 time steps for each of two versions','Synthetic and deterministic'],['1,760 independent high-precision checks; CTest passed','Mathematical verification, not turbine certification']],[230,255])
p('13 November 2026  |  Full original-SDK execution  |  English research whitepaper','small')
page()
#2
h('1. Industrial use case and current research context')
p('Wind-turbine digital twins help investigate how the incident wind field, rotor speed, blade pitch, drivetrain loading and electrical constraints jointly influence operating performance. A reusable mathematical evaluation layer may let a researcher switch coefficient-function versions without rewriting the outer state integrator, and may offer a clear audit trail for changes to physical assumptions.')
p('Modern reference environments such as NREL/OpenFAST combine aerodynamic, structural, control, electrical and, where relevant, hydrodynamic models. IEC 61400-12-1:2022 defines procedures for measuring wind-turbine power performance and evaluating uncertainty. These capabilities are broader than the mathematical submodel investigated here.')
sub('What this research project actually demonstrates')
tab([['Part of industrial workflow','Implemented and verified in this package'],['Aerodynamic coefficient lookup','Two smooth, versioned synthetic Cp functions and one Ct function'],['Rotor and generator mathematical kernels','Aerodynamic torque, thrust, generated power and rating-consistent generator torque'],['Reduced-order temporal state','Rotor angular-velocity derivative and Euler update executed in paceval'],['Numerical scenario management','C++ provides wind, pitch, time-step ordering and output aggregation'],['Full aeroelastic coupled machine twin','Not implemented: requires dedicated data and validated tools']],[220,265])
p('The practical contribution is a reproducible mathematical kernel suitable for subsequent substitution with real, licensed or measured coefficient tables; no field-measured power curve or turbine performance certification is claimed.','small')
page()
#3
h('2. Defined research model and provenance')
p('The original WP_042 proposal suggested the relationship P = 0.5 rho A v^3 Cp(lambda,beta) and a fixed rotor simulation with tabulated coefficient maps. The present implementation expands that starting point into explicit, independently testable functions and adds an interpolation baseline. Every numerical wind profile and coefficient used here is deliberately synthetic.')
tab([['Parameter','Declared synthetic reference value / units'],['Rotor radius R','63 m, illustrative reference-scale rotor'],['Air density rho','1.225 kg/m³, constant'],['Rotor inertia J','4.0 × 10^7 kg m²'],['Drivetrain drag coefficient D','1.2 × 10^5 N m s'],['Generator reference torque and speed','2.3 MN m at 1.12 rad/s'],['Electrical efficiency and rated power','0.95, 5 MW'],['Euler time increment','1 s; dynamics integrated by C++ using a paceval next-state graph'],['Sweep domain','3 ≤ lambda ≤ 14 and 0° ≤ pitch ≤ 20°'],['Actual simulation wind speed','5.52 to 12.88 m/s over 720 seconds']],[210,275])
p('These values are not a calibrated NREL 5-MW model; nominal size and rating alone do not reproduce a validated turbine. Some experimental operating points deliberately cover combinations outside normal turbine supervisory-controller schedules, because the purpose is mathematical function testing.')
page()
#4
h('3. Aerodynamic coefficient mathematics')
p('Tip-speed ratio is the nondimensional ratio of blade-tip speed to incoming wind speed. The rotor area is circular. The synthetic power coefficient uses a bounded Gaussian dependence on tip-speed ratio and an exponential decrease with blade pitch. Its second version adds a small, explicit, independently registered shape modification.')
sub('Explicit power coefficient')
img('_eq_cp',470,80)
p('Version 2: Cp2 = Cp1 × [1 + 0.015 sin(0.5 lambda) exp(-beta/25)]. The thrust coefficient is Ct = 0.03 + 0.78 exp[-((lambda-7)/6)^2] exp(-beta/30). Both formulas are provided verbatim in the formula registry and as distinct paceval computation handles.')
sub('Bounds, sensitivities and what they mean')
p('The two Cp models remain below the ideal Betz upper bound 16/27 throughout the tested domain. This is only a physical screening criterion. The model does not solve blade-element aerodynamics or guarantee realistic lift, drag, dynamic stall, tower shadow or yaw sensitivity.')
p('The explicit analytical derivatives dCp/dlambda and dCp/dbeta are computed with the original paceval engine. The chain rule yields aerodynamic-power sensitivities at fixed omega, including dP/dv = (0.5 rho A v²) [3 Cp - lambda dCp/dlambda]. Avoiding a numerical derivative inside the runtime makes the mathematical assumptions auditable.')
page()
#5
h('4. Power, thrust and generator-energy balance')
sub('Physical quantity definitions')
img('_eq_energy',475,80)
p('Aerodynamic rotor torque is obtained by dividing aerodynamic power by positive rotor angular speed. Axial force uses a separately declared thrust coefficient. The tested domain excludes zero wind speed and zero rotor speed, where these simplified relations would require explicit treatment of startup, zero torque and aerodynamic nonlinearities.')
sub('Rating-consistent electrical extraction')
img('_eq_gen',475,80)
p('The generator reference law first produces an unconstrained electrical power proxy. A smooth rated-power limit S then determines both the delivered power and the corresponding shaft reaction torque. This is important: separately clipping output power while retaining the unconstrained shaft torque would violate the declared energy balance.')
p('The smooth rating proxy uses epsilon = 1,500 W and is not an inverter or brake controller. The generator electrical loss is S(e) × (1/eta - 1) and is computed in a separate paceval graph. Rated-power margins are also independently available as reusable expression outputs.')
sub('State equation and explicit Euler update')
img('_eq_rotor',475,80)
p('The full analytical Euler next-state expression is executed with paceval for both coefficient versions; C++ only advances the state, validates the domain, and sums electrical energy over chronological time steps.')
page()
#6
h('5. Original paceval SDK: architecture and execution')
p('The application compiles the original paceval_main.cpp and paceval_main.h files, links an independently supplied original shared library, and creates 31 persistent computation handles from literal expressions. On each evaluated input block it invokes paceval_dGetMultipleComputationsResultsExt and checks per-result errors and finite outputs.')
tab([['Graph family','Real paceval graph outputs'],['Coefficients and geometry','lambda, Cp v1, Cp v2, Ct, rotor area, wind incident power'],['Aerodynamic force and power','rotor power v1/v2, rotor torque v1/v2, thrust'],['Analytical sensitivities','dCp/dlambda, dCp/dbeta, dP/dv, dP/domega, dP/dbeta'],['Generator and operating envelope','reaction torque, mechanical/electrical power, smooth rating, losses, Betz/rated/wind margins'],['Dynamics and versioning','angular acceleration v1/v2, Euler next-state v1/v2, delta Cp and delta power']],[210,275])
p('The mandatory machine-readable results/math_execution_inventory.csv lists each executed expression, owner and API path. The C++ host retains responsibility for stateful integration, wind and pitch profile generation, numeric aggregation, input validation and data export.')
p('Because the dynamical system is stateful, batch evaluation does not make the entire simulation simultaneous: 31 graphs are still batch-evaluated per step, while the time update is deliberately sequential. The coefficient maps and operating sweeps use contiguous batched parameter arrays.')
page()
#7
h('6. Actually executed and independently validated results')
tab([['Executed metric','Verified run result'],['Original paceval persistent mathematical graphs','31'],['Successful multi-graph batch calls',f"{RUN['batch_calls']:,}"],['Successfully evaluated batch graph outputs',f"{RUN['batch_graph_outputs']:,}"],['Coefficient-map mesh','61 × 61 = 3,721 points'],['Additional parameter sweep',f"{RUN['operating_sweep_points']:,} points"],['Sequential rotor traces','2 versions × 720 samples'],['Independent C++ oracle values',f"{RUN['native_audit_values']:,} passed"],['Independent 80-digit mpmath reference values',f"{VAL['high_precision_values']:,} passed"],['Finite-difference / dynamical reference checks','80 / 7,200 passed'],['Version 1 generated energy',f"{RUN['energy_version1_kWh']:.3f} kWh (synthetic)"],['Version 2 generated energy',f"{RUN['energy_version2_kWh']:.3f} kWh (synthetic)"],['Build and integration test','CMake succeeded; CTest 1/1 passed']],[260,225])
p('The numeric run proves that the specified reusable formula registry executes consistently. It does not establish the validity of any real turbine production forecast, power curve, safety envelope, fatigue loading or aerodynamic model.','small')
page()
#8
h('7. Computed aerodynamic Cp and rotor-power surfaces')
figure('01_cp_surface_3d','Figure 1. Power coefficient Cp over tip-speed ratio and pitch, calculated with paceval.')
figure('02_rotor_power_surface_3d','Figure 2. Rotor power at 10 m/s, directly from the same paceval aerodynamic graph family.')
page()
#9
h('8. Coefficient and thrust operating envelopes')
figure('03_cp_contour','Figure 3. Cp isolines and model operating region; synthetic coefficient, not a measured curve.')
figure('04_ct_contour','Figure 4. Axial-thrust coefficient Ct as a function of the two controlled inputs.')
page()
#10
h('9. Analytical derivatives and formula versioning')
figure('05_analytical_sensitivity_3d','Figure 5. Analytical dCp/dlambda surface, evaluated as a reusable paceval graph.')
figure('09_formula_revision_difference','Figure 9. Explicitly versioned coefficient difference Cp(v2) minus Cp(v1).')
page()
#11
h('10. Reduced-order dynamic rotor experiment')
figure('06_wind_rotor_dynamics','Figure 6. Reproducible synthetic wind speed and two corresponding angular-velocity traces.')
figure('07_versioned_electrical_power','Figure 7. Rate-limited electrical power proxies evaluated by paceval during sequential rotor integration.')
page()
#12
h('11. Energy accumulation and operating-point survey')
figure('08_cumulative_energy','Figure 8. Host-accumulated energy from actual paceval electrical-power time series (two versions).')
figure('10_operating_sweep','Figure 10. Four-thousand-eight-hundred synthetic wind, pitch and rotor-speed combinations.')
page()
#13
h('12. Independent coefficient table and error audit')
figure('11_tabulated_lookup_interpolation','Figure 11. Independent bilinear coefficient-map interpolation versus the explicitly declared synthetic Cp formula.')
p(f"The comparison evaluates 576 off-grid points against the 61 × 61 pre-tabulated paceval Cp surface. The maximum absolute interpolation difference is {VAL['lookup_abs_difference_max']:.6f}, and the mean difference is {VAL['lookup_abs_difference_mean']:.6f}. This is a numerical approximation check of a smooth surrogate, not measured aerodynamics.")
p(f"An independent 80-decimal-digit oracle passed {VAL['high_precision_values']:,} values; numerical checks of 80 analytical finite differences and 7,200 dynamic relations also passed. The maximum reported scaled reference discrepancy in the 80-digit sample was {VAL['high_precision_max_scaled_error']:.2e}.")
page()
#14
h('13. Scientific interpretation and limitation boundaries')
sub('What the executable demonstrator establishes')
p('The original paceval engine evaluates reusable nonlinear mathematical coefficient functions and composite quantities across a large synthetic parameter domain, and it can be used inside a stateful C++ integrator. The two versioned coefficient functions remain available as independently stored expression graphs. Mathematical responsibilities are traceable and the results are reproducible.')
sub('What remains outside the tested scope')
p('The numerical study omits real SCADA data, measured or BEM-derived coefficient tables, turbulence and wake fields, blade deformation, dynamic stall, drivetrain nonlinearities, certified protection functions, structural loads, fatigue damage and uncertainty propagation. Simplified Cp and Ct functions and a smooth generator cap cannot substitute for an OpenFAST aero-hydro-servo-elastic simulation.')
p('The reference IEC 61400-12-1:2022 is a power-performance measurement standard, not a certification achieved by this work. These simulation outputs have neither statistical uncertainty bands from physical measurements nor extrapolation guarantees. A smaller difference between two formula versions does not demonstrate a useful real-world improvement.')
sub('Next realistic research milestone')
p('Replace the explicitly synthetic coefficient curves with correctly licensed NREL/OpenFAST BEM or turbine-specific measured coefficient data, freeze a valid operating envelope, and test independent wind and pitch profiles with uncertainty-aware verification against the same rotor integrator. Any claim about operational improvement requires appropriate real measurements and reproducible comparisons.')
page()
#15
h('14. Reproducibility, references and conclusion')
p('Build the C++ executable using a compatible original external paceval Linux runtime, keeping the included original header and interface source. Execute the 720-step study and 61-by-61 coefficient map, regenerate the independent Python numerical audit, scientific figures and this PDF, then run the README link and archive checks.')
p('Build: <font color="#087c91">cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/libpaceval_linux_sharedLIB.so</font>')
p('Execute: <font color="#087c91">cmake --build build -j; ctest --test-dir build --output-on-failure; ./build/wind_turbine_twin --out . --steps 720 --surface 61 --sweep 4800</font>')
p('Reproduction files include examples/formula_registry.csv, the full coefficient and operating surfaces, versioned dynamic traces, results/math_execution_inventory.csv, high_precision_validation.json and SDK execution log. The complete original library binary is not redistributed.')
sub('Selected scientific sources')
p('[1] NREL / OpenFAST v5.0.0 (November 6, 2026), multi-physics turbine dynamics; https://openfast.readthedocs.io/en/dev/','small')
p('[2] IEC 61400-12-1:2022, power performance measurements; https://webstore.iec.ch/en/publication/68499','small')
p('[3] NLR Wind Systems WISDEM reference turbine 5MW YAML; https://github.com/NLRWindSystems/WISDEM/blob/master/examples/02_reference_turbines/nrel5mw.yaml','small')
p('[4] Original paceval C++ mathematical engine and public SDK, https://github.com/paceval/paceval','small')
p('[5] FMI standard documentation, https://fmi-standard.org/docs/main/','small')
p('[6] WP_042 original independent five-page user proposal (reproduced in the project).','small')
sub('Conclusion')
p('<b>Successful mathematical execution proof:</b> 31 real original-SDK graphs, more than 300,000 verified batch outputs, an energy-consistent reduced-order rotor update, and independent high-precision checks demonstrate reusable mathematical turbine coefficient functions. Physical turbine validation and a full operational digital twin remain future work.')

# Layout and per-page navigation
from reportlab.lib import colors
w,h=A4

def drawPage(canvas,doc):
 canvas.saveState();page_no=canvas.getPageNumber()
 canvas.setFillColor(NAVY);canvas.rect(0,h-9, w,9,stroke=0,fill=1)
 canvas.setFillColor(TEAL);canvas.rect(44,h-45,w-88,1.3,stroke=0,fill=1)
 canvas.setFont('DejaVu-Bold',7.3);canvas.setFillColor(TEAL);canvas.drawString(44,h-32,'PACEVAL  /  WIND-TURBINE DIGITAL TWIN  /  RESEARCH')
 canvas.setStrokeColor(HexColor('#d3dfe4'));canvas.line(44,43,w-44,43)
 canvas.setFont('DejaVu',7.2);canvas.setFillColor(GRAY);canvas.drawString(44,30,'WP_042  •  mathematical execution feasibility  •  13 November 2026')
 canvas.drawRightString(w-44,30,str(page_no))
 canvas.restoreState()

DOC=SimpleDocTemplate(str(OUTPUT),pagesize=A4,rightMargin=52,leftMargin=52,topMargin=66,bottomMargin=54,title='Wind-Turbine Digital Twin Coefficient Functions with paceval',author='paceval mathematical research demonstrator')
DOC.build(STORY,onFirstPage=drawPage,onLaterPages=drawPage)
print(OUTPUT)
