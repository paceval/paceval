#!/usr/bin/env python3
"""Publication-quality PDF generated only from checked original-SDK result files."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from PIL import Image as PIL
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures'
RUN=json.loads((ROOT/'results/execution_summary.json').read_text());PREC=json.loads((ROOT/'results/high_precision_validation.json').read_text())
assert RUN['paceval_graphs']==86 and PREC['status']=='passed'
OUTPUT=ROOT/'paceval_Hydraulic_Pump_Twin_Whitepaper_EN.pdf'
for n,f in [('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(n,f))
DARK=HexColor('#23423B');GREEN=HexColor('#34735D');GOLD=HexColor('#B96A29');GRAY=HexColor('#52655e');LIGHT=HexColor('#edf5f1');CREAM=HexColor('#faf8f2')
ST={
'h1':ParagraphStyle('h1',fontName='DejaVu-Bold',fontSize=18,leading=25,textColor=DARK,spaceAfter=13),
'h2':ParagraphStyle('h2',fontName='DejaVu-Bold',fontSize=11,leading=16,textColor=GREEN,spaceBefore=11,spaceAfter=7),
'p':ParagraphStyle('p',fontName='DejaVu',fontSize=9.1,leading=14,textColor=DARK,spaceAfter=9),
'small':ParagraphStyle('small',fontName='DejaVu',fontSize=7.85,leading=12.2,textColor=GRAY,spaceAfter=8),
'cap':ParagraphStyle('cap',fontName='DejaVu',fontSize=7.6,leading=11,textColor=GRAY,spaceAfter=12,alignment=TA_CENTER),
'cover':ParagraphStyle('cover',fontName='DejaVu-Bold',fontSize=24,leading=32,textColor=DARK,spaceAfter=15),
'subtitle':ParagraphStyle('subtitle',fontName='DejaVu',fontSize=10.6,leading=16.5,textColor=GREEN,spaceAfter=14),
'cell':ParagraphStyle('cell',fontName='DejaVu',fontSize=8,leading=11.5,textColor=DARK),
'cellhead':ParagraphStyle('cellhead',fontName='DejaVu-Bold',fontSize=8,leading=11.5,textColor=DARK),
}
STORY=[]
def p(t,style='p'):STORY.append(Paragraph(t,ST[style]))
def h(t):p(t,'h1')
def sub(t):p(t,'h2')
def gap(n=10):STORY.append(Spacer(1,n))
def page():STORY.append(PageBreak())
def tab(rows,widths=(235,265)):
 data=[[Paragraph(str(c),ST['cellhead' if idx==0 else 'cell']) for c in row] for idx,row in enumerate(rows)]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,CREAM]),('LINEBELOW',(0,0),(-1,0),0.7,GREEN),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP')]))
 STORY.append(t);gap(7)
def fig(name,caption,w=465,hmax=224):
 path=FIG/(name+'.png'); im=PIL.open(path);w0,h0=im.size;scale=min(w/w0,hmax/h0)
 STORY.append(KeepTogether([Image(str(path),width=w0*scale,height=h0*scale),Paragraph(caption,ST['cap'])]))
def hero():
 path=FIG/'00_hydraulic_pump_hero.png';im=PIL.open(path);STORY.append(Image(str(path),width=500,height=250))
def equation(name,tex,height=.83):
 figx=plt.figure(figsize=(10,height),facecolor='white');figx.text(.02,.50,'$'+tex+'$',va='center',ha='left',fontsize=15.5,color='#244b3f');figx.savefig(FIG/(name+'.png'),dpi=170,bbox_inches='tight',pad_inches=.09);plt.close(figx)
 im=PIL.open(FIG/(name+'.png'));w0,h0=im.size;s=min(475/w0,71/h0);STORY.append(Image(str(FIG/(name+'.png')),width=w0*s,height=h0*s));gap(4)
# COVER
p('PACEVAL  |  SCIENTIFIC RESEARCH DEMONSTRATOR','subtitle')
p('Hydraulic Digital Twin:<br/>Pump-Efficiency and<br/>Network Formula Modules','cover')
p('A reproducible C++ investigation of reusable paceval graphs for pump curves, parallel-network equilibrium, electrical input power and synthetic water-quality functions.','subtitle')
hero()
p('Cover illustration is conceptual. The twelve scientific figures are produced from the executed original paceval SDK outputs.','small')
gap(6)
tab([['Executed numerical outcome','Scope / provenance'],['86 persistent mathematical graphs and 1,164,440 batch graph outputs','Genuine paceval Linux runtime'],['6,000 parameter sweep points and 3,721 operating points','Synthetic, analytical hydraulic network'],['20 versioned efficiency, power and cost graph families','20 interchangeable model definitions'],['3,559 independent 80-digit validation values','Mathematical verification, not a calibrated pump']])
p('13 November 2026 | WP_043 | English research whitepaper','small')
page()
# 2
h('1. Industrial use case and current modeling context')
p('Industrial pump systems, water-distribution networks and process plants often require many repeated evaluations of a pump curve, an efficiency map and the electrical power needed to maintain a specified flow. A mathematical digital twin can make these model expressions traceable and replaceable while the larger simulator continues to handle topology, equipment states, feedback and measured data.')
p('The U.S. EPA EPANET 2.2 framework represents pumps through head-versus-flow curves, variable-speed settings and associated efficiency curves. Its full pressure-network and water-quality calculations are much wider in scope than the controlled analytical kernel presented here [1]. U.S. Department of Energy resources similarly emphasize matching pump operation to the system rather than assessing the pump in isolation [2].')
sub('Why the single original equation is not enough')
p('The original WP_043 research proposal starts with P = rho g Q H / eta(Q), while explicitly leaving hydraulic network equations and water-quality transport to separate solvers. For an industrially meaningful demonstration, delivered head H must first follow from the pump and network curves. We therefore implement a small reproducible two-branch network, not just a stand-alone power calculator.')
tab([['A real pumping digital twin needs','Implementation and boundary'],['Pump and parallel-pipe curves','Analytic steady network and affinity-style speed scaling'],['Speed and efficiency variants','20 interchangeable synthetic maps registered as paceval graphs'],['Electrical power and cost','Formula-derived per-point energy and cost functions'],['Flow conservation and tracer quantities','Both branch flows and steady exponential attenuation surrogate'],['Transient network and validated water-quality transport','Not implemented; EPANET-type solvers and field measurements are required']])
page()
#3
h('2. Mathematical definition of the hydraulic network')
p('A single centrifugal pump feeds two parallel pipes that share a common static-head rise. Flow Q is measured in m³/s and hydraulic head H in meters. Pump speed n is a dimensionless ratio to the declared nominal speed. Hydraulic resistance coefficients k have the units required for head loss to equal kQ². All values are deliberately synthetic.')
sub('Speed-dependent pump curve and quadratic network')
equation('_eq_pump',r'H_p(Q,n)=H_0n^2-aQ^2,\qquad H_s(Q)=H_{static}+k_{eq}Q^2')
equation('_eq_network',r'k_{eq}=\left(\frac{1}{\sqrt{k_A}}+\frac{1}{\sqrt{k_B}}\right)^{-2}')
sub('Operating point, a reusable paceval graph')
equation('_eq_qstar',r'Q_*=\sqrt{\frac{H_0n^2-H_{static}}{a+k_{eq}}}')
p('The operating point is the unique positive zero of H_p - H_s in the declared domain. An explicit paceval graph evaluates the closed-form root; C++ checks the network head residual rather than replacing the mathematical calculation with a native root solver. The approach is valid for this deliberately limited quadratic network, not a generic looped pipe network.')
sub('Two branch flows and matching head losses')
equation('_eq_branches',r'Q_A=Q\frac{k_A^{-1/2}}{k_A^{-1/2}+k_B^{-1/2}},\quad Q_B=Q-Q_A')
p('Independent paceval graphs verify Q_A + Q_B = Q and k_A Q_A² = k_B Q_B². The same computations are reused in all sweep, surface and schedule modes.')
page()
#4
h('3. Pump efficiency, power and operating expenditure')
p('The demonstrator separates hydraulic pump efficiency from motor efficiency. The quadratic efficiency approximation is evaluated only over its bounded input domain. It is not a measured manufacturer curve and cannot be extrapolated to cavitation, reverse-flow operation, motor switching or actual wear.')
sub('Base synthetic hydraulic efficiency')
equation('_eq_eta',r'\eta_0(Q,n)=0.78-0.20\left(\frac{Q/n-0.145}{0.12}\right)^2')
sub('Twenty independently versioned mathematical maps')
equation('_eq_variants',r'\eta_j=\eta_0[1+0.0006(j-11)\sin(12Q/n)],\quad j=1,\ldots,20')
p('There are 20 persistent efficiency expressions, 20 corresponding electrical-power expressions and 20 cost expressions, in addition to the 26 general physical and diagnostic graphs. Version changes are formula definitions, not runtime edits to hidden C++ constants.')
sub('Hydraulic power, electrical input and hourly cost')
equation('_eq_power',r'P_{hyd}=\frac{\rho g Q H_p}{1000},\qquad P_{elec,j}=\frac{P_{hyd}}{\eta_j\eta_m}')
equation('_eq_cost',r'C_j(t)=p(t)P_{elec,j}(t),\quad E_j=\sum_t P_{elec,j}(t)\Delta t')
p('Powers are in kW, the tariff p(t) is in arbitrary currency/kWh and the discrete time interval is one hour. paceval computes the hourly mathematical costs; C++ sums values over time. No industrial tariff or energy saving has been established.')
page()
#5
h('4. Quality surrogate, sensitivities and model limits')
p('To demonstrate the reuse of mathematical formulas across multiple plant variables, the two pipe branches transport an illustrative dissolved tracer with a fixed first-order attenuation coefficient k_d. The volume-over-flow ratio is treated as a residence-time proxy; there is no transient advection, dispersion, variable tank mixing or reaction-network calibration.')
sub('Steady attenuation and flow-weighted mixing')
equation('_eq_quality',r'c_i=c_{in}\exp(-k_d V_i/Q_i),\quad c_{mix}=\frac{Q_Ac_A+Q_Bc_B}{Q}')
p('The tracer equations are implemented as three independent paceval graphs. The user should not interpret the resulting curve as a validated disinfectant, contamination or drinking-water exposure prediction.')
sub('Analytical sensitivities are also evaluated by paceval')
equation('_eq_deriv',r'\frac{\partial H_p}{\partial Q}=-2aQ,\quad \frac{\partial(H_p-H_s)}{\partial Q}=-2(a+k_{eq})Q')
p('Further graphs implement d(eta)/dQ and d(P_elec)/dQ. The derivative values are independently checked in the technical audit, not presented as evidence that the surrogate matches the sensitivity of an actual commercial pump.')
sub('Declared domain and inputs')
tab([['Parameter','Fixed synthetic reference value'],['Nominal pump shutoff head H0','58 m'],['Pump head-loss coefficient a','1,250 (consistent quadratic units)'],['Reference network static head','15 m'],['Parallel pipe coefficients kA, kB','2,800 and 3,700'],['Water density and gravitational acceleration','998.2 kg/m³ and 9.81 m/s²'],['Motor efficiency','0.94'],['Inlet tracer / attenuation coefficient','1.0 mg/L and 0.012 s⁻¹'],['Branch residence-volume parameters','3.5 m³ and 5.0 m³']])
page()
#6
h('5. Original paceval SDK architecture and data provenance')
p('The C++ program compiles the original paceval_main.h and paceval_main.cpp SDK interface files and dynamically links a separately acquired original Linux runtime. The 86 expression handles are created once and reused. Large, contiguous combinations of flow, speed, static head and tariff are evaluated with paceval_dGetMultipleComputationsResultsExt; all returned per-expression error codes are checked.')
tab([['Execution responsibility','Actually executed by'],['86 efficiency, pump, network, cost and sensitivity formulas','86 original paceval computation graphs'],['6,000 prescribed parameter sweep candidates','C++ host input generation; paceval evaluation'],['3,721 physical operating points','paceval closed-form network root plus graph re-evaluation'],['48 sequential hourly input schedules','C++ host orchestration; paceval evaluates all instantaneous functions'],['Energy and tariff aggregation over the schedule','C++ host deterministic sums of paceval outputs'],['Independent numerical reference checks','C++ native oracle and Python mpmath'],['Transient solver / actual water-quality network','Not implemented; not claimed']])
p('Machine-readable results/math_execution_inventory.csv lists every graph and the division of responsibilities. examples/formula_registry.csv stores the actual mathematical expression registered with the original engine, including all 20 formula versions and units.')
sub('The project is not an EPANET implementation')
p('The hydraulic network intentionally uses a two-branch analytical topology. EPA EPANET evaluates general pressurized water systems through full network solvers, controls, tank states and water-quality transport [1]. No connection, endorsement or direct equivalence is implied.')
page()
#7
h('6. Independently verified mathematical results')
tab([['Actually executed or checked','Observed result'],['Persistent original-SDK paceval graphs',f"{RUN['paceval_graphs']:,}"],['Multi-Graph-Batch output values',f"{RUN['paceval_batch_outputs']:,}"],['Real Multi-Graph-Batch invocations',f"{RUN['paceval_batch_calls']:,}"],['Parameter sweep points',f"{RUN['sweep_points']:,}"],['Operating head-balance surface points',f"{RUN['operating_surface_points']:,}"],['Hourly operating samples',f"{RUN['hourly_trace_points']:,}"],['Independent native C++ checks',f"{RUN['native_audit_values']:,} passed"],['Independent 80-digit mpmath values',f"{PREC['checked_values']:,} passed"],['Base-model 48-hour synthetic energy',f"{RUN['energy_base_kWh']:.2f} kWh"],['Synthetic electricity cost, unspecified currency',f"{RUN['cost_base_currency']:.2f}"],['CMake / real SDK CTest','1/1 passed']])
p('The recorded time profile applies fixed deterministic speed and price functions. It is neither an optimal pump dispatch nor a comparison against actual process measurements. The electricity values reflect the declared synthetic pump, its assumed efficiency and the toy hydraulic network only.')
p('Technical numerical tolerances and independent high-precision tests are retained in the repository for reproducibility. This whitepaper intentionally focuses on mathematical feasibility, not publicly benchmarking the C++ and paceval implementations.')
page()
#8–13
figpages=[
 ('7. Pump and efficiency response functions',[('01_pump_and_system_head_sweep','Figure 1. Direct original paceval output across variable-speed pump and network head scenarios.'),('02_efficiency_scatter','Figure 2. Pump-efficiency values from the 6,000-point actual batch sweep.')]),
 ('8. Hydraulic operating-point geometry',[('03_operating_flow_3d','Figure 3. True pump-network operating-flow surface from paceval, 61 × 61 grid.'),('04_electric_power_surface_3d','Figure 4. Electrical input-power surface evaluated at the paceval-derived operating points.')]),
 ('9. Water quality and hydraulic residual',[('05_mixed_tracer_surface_3d','Figure 5. Explicitly synthetic steady tracer attenuation and branch mixing.'),('06_operating_residual_map','Figure 6. Independent paceval pump- and system-head expressions coincide at the selected operating points.')]),
 ('10. Parallel-pipe operation and real batch execution',[('07_branch_flow_time_trace','Figure 7. Actual paceval parallel-branch flows versus pump speed at fixed network static head.'),('11_sweep_residuals','Figure 8. General candidate sweep: pump minus system head at points not necessarily in equilibrium.')]),
 ('11. Hourly input power and accumulated energy',[('08_power_versions_time_trace','Figure 9. Two versioned paceval electric-power functions and the base model on the fixed trace.'),('09_cumulative_energy_versions','Figure 10. Time-integrated paceval power output; chronological accumulation is hosted by C++.')]),
 ('12. Formula versioning and model interactions',[('10_versioned_efficiency_power','Figure 11. All twenty independent graph versions applied to an identical hydraulic operating point.'),('12_quality_vs_power','Figure 12. Mathematical relationship between steady tracer surrogate and electrical power.')]),
]
for title,imgs in figpages:
 h(title)
 if title.startswith('9.'):p('Both quantities are mathematical demonstrator outputs. A low residual verifies the constructed equation, not the accuracy of the actual pump or a water-quality forecast.','small')
 for f,c in imgs:fig(f,c)
 page()
#14
h('13. Scientific interpretation and industrial applicability')
sub('What this experiment establishes')
p('This project demonstrates that paceval can execute a relatively large family of replaceable, explicit mathematical pump and network expressions within a consistent C++ workflow. It computes the pump–system intersection, pipe flows, delivered hydraulic head, electrical demand, costs and tracer surrogates with graph reuse and real batch execution. The entire numerical experiment can be reproduced from the included sources and machine-readable data.')
sub('What it does not establish')
p('The pump parameters are synthetic and are not fitted to laboratory curves. The hydraulic system has no complex loops, elevated tanks, pressure-dependent demand, valves with changing status, transient water-hammer, thermal/viscous effects, cavitation margin, maintenance degradation or closed-loop controller. The quality surrogate is not a water transport simulator. These exclusions are fundamental to interpreting the results.')
sub('Sensible industrial follow-up')
p('A production-oriented extension should import tested pump head and efficiency curves, model an actual branch network with EPANET 2.2 or another independently verified solver, validate measured flow and differential pressure against instrument uncertainties and evaluate representative pump schedules. The reusable paceval expression graphs could then serve as modular mathematical callbacks for specific coefficients, efficiency corrections and diagnostics.')
sub('Scientifically motivated failure conditions')
p('If efficiency curves become nonphysical outside the declared envelope, or head-balance solutions cannot be reconciled with an independent hydraulic solver and measured pressures, that model version must be rejected. Faster formula evaluation, if ever measured, would not repair such domain-model discrepancies.')
page()
#15
h('14. Reproducibility, citations and conclusions')
sub('Build and rerun with the original library')
p('Configure CMake from src/CMakeLists.txt with an externally supplied original paceval Linux runtime, compile the original SDK wrapper with hydraulic_pump_twin.cpp, run CTest and then run the full program:')
p('cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so','small')
p('cmake --build build -j; ctest --test-dir build --output-on-failure','small')
p('./build/hydraulic_pump_twin --out . --surface 61 --sweep 6000 --hours 48','small')
p('python3 src/high_precision_reference.py; python3 src/verify_results.py; python3 src/make_figures.py; python3 src/make_whitepaper.py','small')
sub('Scientific and technical reference basis')
p('[1] U.S. EPA, EPANET 2.2 User Manual, pump curves, efficiency curves, variable-speed settings and network hydraulics. https://usepa.github.io/EPANET2.2/','small')
p('[2] U.S. Department of Energy, Pump Systems, pumping-system assessment and operating-point matching. https://www.energy.gov/cmei/ito/pump-systems','small')
p('[3] UNIDO, Manual for Industrial Pump Systems Assessment and Optimization, affinity relationships and system-curve warnings. https://www.imeep-eg.org/wp-content/uploads/2022/08/9-UNIDO-PSO-Manual_optimized.pdf','small')
p('[4] User-supplied WP_043 Hydraulic Twin Pump-Efficiency Functions, original five-page research proposal, November 2026 (retained in inputs/).','small')
p('[5] paceval SDK documentation and C++ source. https://github.com/paceval/paceval','small')
sub('Conclusion')
p('A mathematically complete, synthetic two-branch pumping-network kernel was successfully implemented with 86 persistent original paceval graphs and independently checked output. The result is a reproducible mathematical feasibility demonstration suitable for future integration into a calibrated hydraulic digital twin; it is not an accredited pump-efficiency study or a validated water-quality prediction.')
p('This release contains no performance superiority claims and does not redistribute the separately licensed original paceval runtime.','small')

def decorate(canvas,doc):
 canvas.saveState();w,h=A4
 canvas.setStrokeColor(GREEN);canvas.setLineWidth(.45);canvas.line(17*mm,h-19*mm,w-17*mm,h-19*mm)
 canvas.setFont('DejaVu-Bold',7);canvas.setFillColor(GREEN);canvas.drawString(18*mm,h-15.5*mm,'PACEVAL  |  HYDRAULIC PUMP DIGITAL TWIN')
 canvas.setStrokeColor(HexColor('#c6d6cd'));canvas.line(17*mm,16*mm,w-17*mm,16*mm)
 canvas.setFont('DejaVu',7);canvas.setFillColor(GRAY);canvas.drawString(18*mm,11.5*mm,'WP_043  |  Original SDK research demonstrator  |  13 November 2026');canvas.drawRightString(w-18*mm,11.5*mm,str(doc.page))
 canvas.restoreState()
doc=SimpleDocTemplate(str(OUTPUT),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=25*mm,bottomMargin=23*mm)
doc.build(STORY,onFirstPage=decorate,onLaterPages=decorate)
print('created',OUTPUT)
