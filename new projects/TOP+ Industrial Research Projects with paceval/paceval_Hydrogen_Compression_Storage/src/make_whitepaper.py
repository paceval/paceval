#!/usr/bin/env python3
"""Create a standalone, cited scientific English PDF from verified WP24 results."""
from pathlib import Path
import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,PageBreak,Paragraph,Spacer,Image as PDFImage,Table,TableStyle,KeepTogether,HRFlowable
from reportlab.lib.utils import ImageReader
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures';R=ROOT/'results'
proof=json.loads((R/'execution_evidence.json').read_text());audit=json.loads((R/'independent_validation.json').read_text())
OUT=ROOT/'paceval_Hydrogen_Compression_Storage_Whitepaper_EN.pdf'
for name,path in [('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('DejaVuBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),('DejaVuMono','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(name,path))
NAVY=HexColor('#112A41');TEAL=HexColor('#0E8F9B');ORANGE=HexColor('#E87949');MUTE=HexColor('#4F6477');LIGHT=HexColor('#EEF6F7')
W,H=A4
styles={
 'body':ParagraphStyle('body',fontName='DejaVu',fontSize=9.25,leading=15.5,textColor=NAVY,spaceAfter=9),
 'small':ParagraphStyle('small',fontName='DejaVu',fontSize=8.05,leading=12.7,textColor=NAVY,spaceAfter=7),
 'caption':ParagraphStyle('caption',fontName='DejaVu',fontSize=8,leading=11.2,textColor=MUTE,spaceAfter=10),
 'head':ParagraphStyle('head',fontName='DejaVuBold',fontSize=18,leading=24,textColor=NAVY,spaceAfter=12),
 'subhead':ParagraphStyle('subhead',fontName='DejaVuBold',fontSize=11.5,leading=16,textColor=TEAL,spaceBefore=9,spaceAfter=7),
 'cover':ParagraphStyle('cover',fontName='DejaVuBold',fontSize=26,leading=32,textColor=NAVY,spaceAfter=7),
 'covermid':ParagraphStyle('covermid',fontName='DejaVu',fontSize=13,leading=21,textColor=TEAL,spaceAfter=7),
 'equation':ParagraphStyle('equation',fontName='DejaVuMono',fontSize=9.1,leading=14,textColor=NAVY,backColor=LIGHT,borderPadding=11,spaceBefore=8,spaceAfter=11),
 'label':ParagraphStyle('label',fontName='DejaVuBold',fontSize=8,leading=12,textColor=ORANGE,spaceAfter=4),
 'ref':ParagraphStyle('ref',fontName='DejaVu',fontSize=8.2,leading=13,textColor=NAVY,spaceAfter=8)
}
story=[]
def P(s,style='body'):story.append(Paragraph(s,styles[style]))
def heading(s):P(s,'head')
def sub(s):P(s,'subhead')
def eq(s):P(s,'equation')
def fig(n,name,caption,width=498,maxheight=252):
    path=FIG/name
    w,h=Image.open(path).size;sz=min(width/w,maxheight/h)
    im=PDFImage(str(path),width=w*sz,height=h*sz)
    story.append(KeepTogether([im,Spacer(1,5),Paragraph(f'<b>Figure {n}.</b> {caption}',styles['caption'])]))
def new():story.append(PageBreak())
def block(rows,widths=None,head=True):
    cells=[]
    for r in rows:cells.append([Paragraph(str(x),styles['small']) for x in r])
    t=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1 if head else 0)
    ts=[('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.65,TEAL)]
    if head:ts.extend([('BACKGROUND',(0,0),(-1,0),LIGHT)])
    t.setStyle(TableStyle(ts));story.append(t);story.append(Spacer(1,10))
def footer(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(HexColor('#D4E1E8'));canvas.line(43,44,W-43,44)
    canvas.setFont('DejaVu',7.5);canvas.setFillColor(MUTE)
    canvas.drawString(43,30,'paceval. | WP 24 | Functional research on synthetic hydrogen conditions')
    canvas.drawRightString(W-43,30,f'{doc.page}')
    canvas.restoreState()

# Page 1 -- strong cover image and title.
story.append(PDFImage(str(FIG/'00_hydrogen_compression_hero.png'),width=W-86,height=(W-86)/2))
story.append(Spacer(1,40));P('WP 24 | SCIENTIFIC FUNCTIONAL RESEARCH','label')
P('Hydrogen Compression and Storage Thermal Envelope','cover')
P('Reusable Mathematical Execution Graphs for Staged Compression and Ideal-Gas Storage Screening','covermid')
story.append(HRFlowable(width='100%',thickness=2,color=TEAL));story.append(Spacer(1,18))
P('An experimentally executed, independently checked C++ demonstrator using the original paceval Mathematical Engine.','body')
P('15 November 2026  |  Original local SDK, not MCP  |  Research-grade synthetic conditions  |  English publication','small')
P('Research scope: mathematical and numerical functionality. No physical plant qualification, safety certification, forecast or speed benchmark.','small')
new()
# Page 2
heading('Executive summary')
P('Hydrogen compression and pressurised-gas storage connect thermodynamic state equations, equipment constraints and repeated engineering choices. Engineers need to calculate stage discharge temperatures, compressor energy proxies, intercooler duties and storage temperature/pressure envelopes across many candidate operating points. This study shows how the central explicit mathematics can be executed as persistent, versioned paceval computation graphs while C++ retains stateful orchestration and input governance.')
P(f'The original Linux paceval runtime executed <b>{proof["executed_unique_graphs"]} different mathematical graphs</b> across <b>{proof["compressor_model_cases"]:,} model-point evaluations</b> and <b>{proof["compressor_stage_visits"]:,} stage visits</b>. The recorded results include <b>{proof["graph_point_evaluations"]:,} actual paceval graph outputs</b>. The separately implemented native reference checked {proof["independent_native_checks"]:,} mathematical quantities and the independent 80-digit reference checked {audit["independent_high_precision_checks"]:,} selected values. All figures are drawn from archived paceval CSV results.')
sub('What has been demonstrated')
block([['Function group','What was actually calculated'],['Multi-stage compressor','Two model revisions; stage temperature, exponent, power, cooling, cumulative work, limit margins and derivatives'],['One-zone rigid storage','Temperature and mass updates, ideal-gas pressure, wall heat loss, guard expressions, 4-second time stepping'],['Independent checks','Native C++ per-stage and per-step references, plus high-precision sample checks'],['Production data flow','Numeric CSV read/write through the original SDK string converters after strict input validation']],widths=[147,348])
P('Research evidence must be interpreted narrowly: the numerical results show correct evaluation of the **defined synthetic mathematical model**, not suitability of that model for real hydrogen tank design. The later conversion to accurate hydrogen property models and measured equipment maps remains separate work.')
new()
# Page 3
heading('1 | Industrial problem and state of the art')
P('Hydrogen is commonly produced or handled at pressures that differ from transport and storage requirements. The U.S. Department of Energy describes diaphragm, reciprocating, rotary, centrifugal and alternative compression technologies, highlighting the particular challenges of high compression ratios and low molecular weight. A real compression project evaluates equipment duty, heat rejection, gas quality, leakage and operating limits jointly, not in isolation.')
P('The physical simplifications of an ideal-gas, constant-property model become important for high-pressure storage. Leachman and co-authors established fundamental hydrogen equations of state for normal hydrogen, orthohydrogen and parahydrogen, providing an appropriate scientific foundation for subsequent real-gas extensions. More recent studies of fast filling show that vessel temperature can be spatially nonuniform and may depend on tank geometry and cooling strategies. This study intentionally does not reproduce those spatially distributed methods.')
P('For gaseous hydrogen fueling stations, ISO 19880-1:2020 describes general design, installation and safety requirements. Its relevance is contextual; the current demonstrator has no approval authority and is not an implementation of the standard.')
sub('Proposed industrial workflow')
P('A hydrogen-system planner supplies inlet pressure and temperature, mass-flow target, compressor pressure target, number of stages and intercooler design options. paceval evaluates mathematical compression and cooling kernels. Selected conditioned gas temperatures feed a synthetic storage vessel model, again using paceval for its explicit state-update equations. The C++ host organises steps and reports the resulting numerical margins for engineering review.')
P('Other professional tools, such as real-gas property packages, process simulators and compressor OEM sizing applications, are appropriate for detailed sizing. This study neither replaces them nor compares computation speed or energy performance of software engines.')
new()
# Page 4
heading('2 | Mathematical model: staged hydrogen compression')
P('The stage model uses the polytropic ideal-gas approximation with constant heat capacity. Pressure ratios are distributed equally across one to four stages. Compressor stage outlet temperature and specific enthalpy-rise work are calculated directly by paceval.')
eq('a = (gamma - 1) / (gamma * eta_poly)')
eq('T_out = T_in * (P_out / P_in)^a')
eq('w_stage = cp * (T_out - T_in)     [J/kg]')
P('An intercooler recovers part of the outlet/inlet temperature difference. Its effectiveness is applied as a mathematical expression. If the pressure ratio equals one, the temperature increase and stage-work proxy both approach zero, and this limiting case is included in the SDK self-tests.')
eq('T_cool_out = T_cool + (1 - effectiveness) * (T_out - T_cool)')
eq('Q_cool = mdot * cp * (T_out - T_cool_out)')
sub('Two immutable model versions')
P('V1 uses the supplied constant effective polytropic efficiency. V2 applies a small deliberately synthetic efficiency penalty depending on stage pressure ratio and stage inlet temperature. It is not fitted to manufacturer data. Each version has an independent set of 17 stage graphs with their handles preserved for the full experiment.')
eq('eta_V2 = eta_in - 0.027 * (r-2.5)^2 / (1+(r-2.5)^2)')
eq('                - 0.00016 * (T_in - 300);     r=P_out/P_in')
P('Additional paceval graphs return stage-validity Boolean values, continuous temperature/power/cooling/pressure margins, and explicit analytical sensitivities. The host checks all dimensional and physical domains before graph evaluation; it cannot rely on a Boolean mask to hide a singular expression.')
new()
# Pages 5-8
heading('3 | Recorded compressor stage characteristics')
fig(2,'02_specific_work_by_stage.png','Average specific-work proxy across one to four compressor stages, separately for both hypothetical graph versions.')
fig(3,'03_peak_stage_temperature.png','Peak-stage thermal response derived from actually calculated stage temperatures. The dashed 445 K line is illustrative rather than a uniform case limit.',maxheight=232)
new()
heading('4 | Screening decisions and stage-count sensitivity')
fig(4,'04_quality_decisions.png','ACCEPT, REVIEW and REJECT proportions under explicitly synthetic screening limits. Red scenarios are not real equipment faults.')
fig(13,'13_accept_fraction_by_stages.png','Stage-count dependence of the synthetic ACCEPT classification, evaluated over all recorded compressor cases.',maxheight=218)
new()
heading('5 | Operating envelope and model revision')
fig(5,'05_thermal_margin_surface.png','Four-stage V1 thermal screening envelope as a function of initial temperature and overall pressure ratio, populated from actual cases.')
fig(6,'06_model_revision_energy.png','Paired V2 minus V1 specific-work responses from identical synthetic input scenarios. This is a model-formulation comparison, not a software performance benchmark.',maxheight=230)
new()
heading('6 | Heat-rejection coupling and sensitivities')
fig(7,'07_cooling_and_power.png','The same cases produce compressor duty and intercooler heat loads; the mathematical graph definitions preserve separate units and roles.')
fig(8,'08_pressure_sensitivities.png','Explicit analytic derivative of stage outlet temperature with respect to outlet pressure, computed by original paceval graphs.',maxheight=226)
new()
# Page 9
heading('7 | Lumped rigid-vessel temperature and pressure model')
P('A separate one-zone ideal-gas model calculates thermodynamic energy balances during filling. For a fixed-volume vessel with current mass M and gas temperature T, the open-system enthalpy balance is represented by the following explicitly defined screening equation. It is not a full real-gas mixing model.')
eq('M*cv*dT/dt = mdot*(cp*T_fill - cv*T) - UA*(T - T_amb)')
eq('M_next = M + mdot*dt;    T_next = T + dt*(dT/dt)')
eq('P_next [bar] = M_next * R_H2 * T_next / (V * 100000)')
P('The host advances states in fixed steps of four seconds. A pressure initialization graph derives tank mass from the specified initial tank pressure. The compressor graph chain independently supplies the synthetic storage inlet temperature. Fourteen storage graphs then compute enthalpy input, wall heat transfer, mass, temperature, pressure, sensitivities and logical guards. Crossing a synthetic temperature or pressure threshold is recorded, not used to command an actuator.')
fig(1,'01_execution_architecture.png','Actual responsibility split: paceval executes physics-screening mathematics, the C++ host orchestrates state and decisions, and independent references verify outputs.',maxheight=200)
new()
heading('8 | Numerical storage thermal trajectories')
fig(9,'09_storage_temperature_profiles.png','Selected time series from the one-zone gas-temperature calculations. Each profile has its own synthetic temperature limit.')
fig(10,'10_storage_pressure_profiles.png','The corresponding ideal-gas pressure rises during inflow in the fixed-volume synthetic vessel.',maxheight=230)
new()
heading('9 | Storage feasibility as evaluated by paceval')
fig(11,'11_storage_guard_outcomes.png','Per-step Boolean outcomes from the actual storage guard graphs. Synthetic violations remain in the mathematical replay to expose the envelope.')
fig(12,'12_storage_endpoint_envelope.png','The final one-zone pressure/temperature points. Each point has its own documented limit; the colors show its actual Boolean result.',maxheight=225)
new()
heading('10 | Execution audit and independent verification')
block([['Quantity','Recorded verification'],['Model versions / executed graph handles',f'2 / {proof["executed_unique_graphs"]}'],['Compression scenarios / model cases',f'{proof["compressor_scenarios_per_version"]:,} / {proof["compressor_model_cases"]:,}'],['Actual stage evaluations / storage steps',f'{proof["compressor_stage_visits"]:,} / {proof["storage_step_evaluations"]:,}'],['Multi-graph batches / graph outputs',f'{proof["multi_graph_batch_calls"]:,} / {proof["graph_point_evaluations"]:,}'],['Independent native mathematical checks',f'{proof["independent_native_checks"]:,}'],['Independent 80-decimal-place checks',f'{audit["independent_high_precision_checks"]:,}'],['Storage ideal-gas identity checks',f'{audit["storage_ideal_gas_identity_checks"]:,}']],widths=[270,225])
P('The original paceval C/C++ SDK is linked to a compatible separately provided Linux shared library. All counts come from the machine-generated execution manifest. Its `graph_point_evaluations` metric counts one graph output for one input row. Scalar calls, batch API calls, total outputs, scenarios and unique handles are never conflated.')
P('Independent native C++ evaluates equivalent physics-screening equations from independently written code, with checks after actual paceval API outputs. A second, separately formulated mpmath reference checks selected results at 80 decimal digits. Exact numerical differences remain in technical audit files, not in this public discussion. The CSV pipeline uses genuine paceval floating-point/string conversion functions after strict numeric-literal validation.')
new()
heading('11 | Interpretation and scientific limits')
P('In the recorded synthetic scenario set, the acceptance fraction is much higher for three and four compressor stages than for a single stage. That follows from the defined equal-ratio polytropic model, intercooling assumptions and specific operating limits. The V2 efficiency perturbation increases the modelled enthalpy-rise work over most of this grid. Neither observation predicts that a particular real compressor or storage plant will behave identically.')
P(f'The storage trajectories record {proof["storage_limit_exceedance_steps"]:,} steps at which a case-specific screening margin becomes negative. These points are intentionally retained in the synthetic integration. A real operator must apply independent physical protection systems and certified review policies; mathematical graph outputs alone are not approval evidence.')
sub('Model boundaries')
P('The ideal-gas relation at high pressure, fixed specific heats, uniform tank temperature, constant heat conductance, fixed-stage efficiency, absent pressure drops and perfect inventory mixing are deliberate simplifications. The model does not evaluate hydrogen leak/fire risk, compressor sealing, fatigue, materials embrittlement, relief device sizing, transient line hydraulics, fuel quality or temperature in vessel walls. These limits cannot be repaired merely by increasing arithmetic precision or model size.')
sub('Next steps')
P('Replace fixed gas properties with a validated hydrogen equation-of-state property interface; fit compressor efficiency models to legitimate manufacturer or laboratory measurements; independently validate temperature and pressure against instrumented filling trajectories; use a more spatially resolved vessel heat-transfer model; and only then establish an industrial decision policy under appropriate standards. The explicit mathematical functions would remain candidates for paceval graph execution when the updated SDK supports their semantics.')
new()
heading('12 | References and data provenance')
refs=[
 ('[1] US Department of Energy (updated 8 June 2026)','Gaseous Hydrogen Compression','https://www.energy.gov/cmei/fuels/gaseous-hydrogen-compression'),
 ('[2] Leachman et al., J. Phys. Chem. Ref. Data 38 (2009)','Fundamental Equations of State for Parahydrogen, Normal Hydrogen, and Orthohydrogen','https://www.nist.gov/publications/fundamental-equations-state-parahydrogen-normal-hydrogen-and-orthohydrogen'),
 ('[3] International Journal of Hydrogen Energy, 2 December 2025','Thermal and heat transfer dynamics in high pressure, high aspect ratio hydrogen tank filling processes','https://doi.org/10.1016/j.ijhydene.2025.152513'),
 ('[4] International Journal of Hydrogen Energy, 2025','Thermal behavior in a Type IV hydrogen storage tank under different charging conditions','https://www.sciencedirect.com/science/article/pii/S0360319924054570'),
 ('[5] ISO 19880-1:2020','Gaseous hydrogen — Fuelling stations — Part 1: General requirements','https://www.iso.org/standard/71940.html'),
 ('[6] paceval Mathematical Engine','Official C/C++ API reference and batch evaluation','https://paceval.com/api/'),
]
for number,title,url in refs:
    P(f'<b>{number}</b><br/>{title}<br/><link href="{url}" color="#087B92">{url}</link>','ref')
sub('Original and derived sources')
P('The two-page uploaded WP24 document proposed only four first-order formula kernels and explicitly contained no measured results. This research separately executed two model versions, 100,000 synthetic input scenarios, stateful storage profiles, independent high-precision controls and derived figures. The original proposal is archived as `docs/original_WP24_proposal.pdf`; all new output files and their generation scripts are contained in this project.')
P('This report is intended for scientific reproducibility and discussion, not for operation of hydrogen machinery. The external paceval runtime binary is intentionally excluded from the distributed repository.')

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=43,leftMargin=43,topMargin=45,bottomMargin=61,title='Hydrogen Compression and Storage Thermal Envelope - paceval WP24',author='paceval Industrial Research',subject='Scientific functional feasibility of paceval graph execution')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('PASS generated',OUT,OUT.stat().st_size,'bytes')
