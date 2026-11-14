#!/usr/bin/env python3
"""Typeset the independent scientific publication from verified result files."""
from pathlib import Path
from html import escape
import json, pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]; R=ROOT/'results'; F=ROOT/'figures'
OUT=ROOT/'paceval_Microgrid_Storage_Dispatch_Whitepaper_EN.pdf'
pdfmetrics.registerFont(TTFont('DVS','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVS-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
DARK=colors.HexColor('#173653');TEAL=colors.HexColor('#147c8a');LIGHT=colors.HexColor('#edf4f7');GREY=colors.HexColor('#536b78');GOLD=colors.HexColor('#dcb274')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='CoverKickerX',fontName='DVS-Bold',fontSize=10.2,leading=14,textColor=TEAL,spaceAfter=12))
styles.add(ParagraphStyle(name='CoverTitleX',fontName='DVS-Bold',fontSize=24.5,leading=31,textColor=DARK,spaceAfter=17))
styles.add(ParagraphStyle(name='CoverSubX',fontName='DVS',fontSize=11.2,leading=16,textColor=GREY,spaceAfter=17))
styles.add(ParagraphStyle(name='HeadX',fontName='DVS-Bold',fontSize=16,leading=21,textColor=DARK,spaceBefore=17,spaceAfter=11,keepWithNext=True))
styles.add(ParagraphStyle(name='SubHeadX',fontName='DVS-Bold',fontSize=11.2,leading=16,textColor=TEAL,spaceBefore=11,spaceAfter=6,keepWithNext=True))
styles.add(ParagraphStyle(name='BodyX',fontName='DVS',fontSize=8.7,leading=13.65,textColor=DARK,spaceAfter=9))
styles.add(ParagraphStyle(name='SmallX',fontName='DVS',fontSize=7.2,leading=11.4,textColor=GREY,spaceAfter=6))
styles.add(ParagraphStyle(name='CaptionX',fontName='DVS',fontSize=7.9,leading=11.5,textColor=DARK,spaceAfter=11))
styles.add(ParagraphStyle(name='TableHeadX',fontName='DVS-Bold',fontSize=7.6,leading=10.5,textColor=colors.white))
styles.add(ParagraphStyle(name='TableX',fontName='DVS',fontSize=7.55,leading=11,textColor=DARK))
styles.add(ParagraphStyle(name='ReferenceX',fontName='DVS',fontSize=7.45,leading=11,textColor=DARK,spaceAfter=8,wordWrap='CJK'))

s=[]
def P(t,style='BodyX'):s.append(Paragraph(t,styles[style]))
def H(t):P(t,'HeadX')
def S(t):P(t,'SubHeadX')
def tab(head,rows,widths):
 rows=[[Paragraph(str(v),styles['TableHeadX']) for v in head]]+[[Paragraph(str(v),styles['TableX']) for v in row] for row in rows]
 t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),DARK),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#d0dade')),('VALIGN',(0,0),(-1,-1),'TOP')]));s.append(t);s.append(Spacer(1,12))
def fig(name,caption,width=484):
 path=F/(name+'.png');from PIL import Image as PILImage
 with PILImage.open(path) as im:ww,hh=im.size
 height=width*hh/ww
 if height>280:height=280;width=height*ww/hh
 s.append(KeepTogether([Image(str(path),width=width,height=height),Spacer(1,5),Paragraph(caption,styles['CaptionX'])]))

def create():
 ev=json.load(open(R/'execution_evidence.json'))
 audit=json.load(open(R/'high_precision_audit.json'))
 summaries=pd.read_csv(R/'schedule_summary.csv');comp=pd.read_csv(R/'model_comparison.csv')
 p=ROOT/'input'/'parameters.csv'
 # COVER
 s.append(Spacer(1,10));P('PACEVAL.  |  INDUSTRIAL SCIENTIFIC RESEARCH  |  WP 12','CoverKickerX')
 s.append(Image(str(F/'00_microgrid_hero.png'),width=504,height=252));s.append(Spacer(1,20))
 P('Microgrid Storage Dispatch and Feasibility Evaluation','CoverTitleX')
 P('Multi-period energy balance, battery reserve, island-mode constraints and reusable execution graphs','CoverSubX')
 s.append(HRFlowable(width='100%',thickness=2,color=TEAL));s.append(Spacer(1,15))
 P('<b>Independent numerical functionality research</b> | 14 November 2026 | Original paceval SDK 4.25','BodyX')
 P('Study inputs are deterministic and synthetic. The cover image is a conceptual rendering, not a visualization of measured electrical-network data. The research software is not a utility control system, certified resilience solution or microgrid optimization solver.','SmallX')
 s.append(PageBreak())
 H('Abstract')
 P('Energy dispatch in a microgrid is intrinsically sequential. Battery charging today changes the availability of stored energy for subsequent intervals, while every candidate operating schedule must respect electricity balance, local generation limits, grid interface constraints and minimum reserve. This study tests whether an original paceval Mathematical Engine C/C++ integration can evaluate a substantial set of such interconnected mathematical expressions, reuse them across many periods and deliver independently verifiable results. It deliberately separates graph computation from host-side state propagation and discrete schedule enumeration.')
 P(f'The compiled demonstrator executes <b>{ev["unique_domain_graphs_executed"]} of {ev["unique_domain_graphs_created"]} domain graphs</b>, investigates <b>{ev["schedule_count"]:,} synthetic 24-hour schedules</b> under three resource modes, and evaluates two persistent model versions, producing <b>{ev["version_step_count"]:,} model-period records</b>. Independent high-precision validation passed <b>{audit["reference_assertions"]:,} reference assertions</b> for complete sampled model chains. These are results of original local paceval computation, not an MCP measurement or a native C++ simulation relabeled as paceval.')
 H('1. Industrial problem and practical motivation')
 P('Imagine an industrial campus with a photovoltaic array, a battery energy storage system (BESS), a dispatchable backup generator and a utility connection. Operators need a credible 24-hour plan for supplying critical electrical loads. During ordinary conditions, utility import can cover shortfalls and PV surpluses may be exported or curtailed. Under an outage, import and export become unavailable and battery reserve becomes important. A schedule that looks affordable at one hour may become infeasible later when stored energy falls below the specified floor.')
 P('The mathematical function explored here is not a new energy market, optimization algorithm or power-system model. It is a reusable, auditable evaluation kernel for existing or proposed schedules. Real energy-management software can produce candidate controls; a calculation engine can independently evaluate their energy, margin and cost consequences before a separate supervisory controller and appropriate protection system makes an operational decision.')
 S('A worked data path')
 P('For each hourly CSV record, the host validates PV availability, demand, local generation, battery charge/discharge, grid transfers, curtailment and the tariff. paceval calculates power balance, the next battery energy state and constraint margins. C++ passes the returned battery state to the following hour, accumulates period costs and records the final 24-hour classification. A separate Python program independently checks the output against an 85-digit reference implementation.')
 H('2. Current scientific and industrial context')
 P('The US Department of Energy defines microgrids by their coordinated local power resources and their capacity to operate interconnected or islanded. IEEE 2030.7-2017 specifies controller-level functions, IEEE 2030.8-2018 describes testing of those controller functions, and IEEE 1547-2018 addresses distributed-resource interconnection. Compliance with those standards cannot be inferred from energy-balance arithmetic alone. [1, 4–6]')
 P('The REopt platform provides mixed-integer sizing, dispatch and resilience assessment for distributed energy systems. The open oemof.solph ecosystem offers optimization models, including a 2026 feature for SOC-dependent battery charging constraints. Recent research (2024–2025) studies reserve uncertainty and tradeoffs between economic scheduling and battery degradation. This is the appropriate state-of-the-art context for a specialized mathematical evaluation layer, rather than a claim that paceval replaces these optimization platforms. [2, 3, 7, 8]')
 P('This project makes two controlled extensions to the source WP 12: one-way battery efficiency depends on SOC in model V2, and a simple throughput cost is added to the modeled stage objective. Both modifications remain illustrative. They do not account for temperature-dependent electrochemistry, detailed aging, nonlinear converter operating maps or risk-sensitive optimization.')
 H('3. Explicit model and sign conventions')
 P('<b>Active-power balance (kW):</b> PV available minus curtailment plus generator production plus battery discharge plus grid import minus battery charging minus export minus served demand must equal zero. Served demand is original demand less allowed noncritical shedding. The verified graph returns the signed residual. All reported power terms are kW at a single abstracted bus; no network losses are included.')
 P('<b>Battery transition (kWh):</b> E(next) = E(now) + dt × [eta_charge(E) × Pcharge − Pdischarge / eta_discharge(E)]. The battery has an illustrative 650 kWh upper capacity, 60 kWh minimum energy, 145 kWh operational reserve threshold and 350 kWh initial state. The final hour additionally requires 205 kWh. The hourly step is 1 h. A power of 1 kW sustained for an hour corresponds to 1 kWh.')
 P('<b>V1:</b> Charge efficiency = 0.95 and discharge efficiency = 0.93, independent of battery state. V1 uses no throughput cost term. <b>V2:</b> Charge efficiency = 0.95 × [1 − 0.26 × (E/650 − 0.5)^2]; discharge efficiency = 0.93 × [1 − 0.13 × (E/650 − 0.5)^2]. V2 adds an illustrative 0.035 USD/kWh term for the sum of charge and discharge throughput. Both models use physically identical candidate schedules, allowing a transparent model assumption comparison.')
 P('<b>Stage cost (USD):</b> Hour length multiplied by generator-fuel cost, utility purchase cost, negative export revenue, curtailed PV penalty, shedding penalty, optional battery throughput cost and the absolute generator ramp penalty. The local tariff, generator fuel cost and other coefficients are synthetic, not actual commercial prices or realized savings.')
 S('Important feasibility conventions')
 P('Each period must satisfy power balance within the defined mathematical tolerance; nonnegative energy lower, upper and reserve margins; generator, battery power, grid exchange and ramp limits; PV curtailment no greater than available PV; and a served critical-load minimum equal to 62% of the original demand. A battery cannot charge and discharge simultaneously. During the island scenario, utility import and export must both be zero. Final schedule feasibility additionally requires the terminal battery energy goal.')
 tab(['Model assumption','V1','V2'],[
 ('One-way storage efficiency','Constant charge/discharge factors','SOC-dependent bounded functions'),
 ('Battery throughput term','Excluded from modeled stage cost','Included as simple linear penalty'),
 ('Schedule candidates','Identical synthetic set','Identical synthetic set'),
 ('Inter-hour propagation','Host transports paceval E(next)','Host transports paceval E(next)'),
 ('Physical validation','Single-bus screening only','Single-bus screening only')],[165,145,185])
 H('4. Engine architecture and tested mathematical responsibility')
 P('Actual graph registration uses <b>paceval_CreateComputation</b>. Short scalar tests use <b>paceval_dGetComputationResult</b>. The main workflow evaluates multiple persistent graphs and independent candidates through <b>paceval_dGetMultipleComputationsResultsExt</b>. The 4.25 interface was checked against the user-provided header and the supplied Linux runtime; output ordering was established through an exact analytical layout probe, and API error types were checked for each graph-point result.')
 P('The actual calculation chain is: validated CSV → original graph values for E(next), electricity balance, physical margins and economic quantities → C++ passes E(next) to the next period → original graphs evaluate the subsequent interval → host aggregates verified period outputs → original comparison graphs calculate inter-model cost, terminal-state and conservative margin differences. This prevents an isolated trivial mathematical call from masquerading as a complete paceval workflow.')
 tab(['Mathematical function family','Execution owner','Graph IDs or rationale'],[
 ('PV utilization, supply/demand and power balance','paceval','V1/V2_PV_USED, SERVED_LOAD, POWER_BALANCE'),
 ('Storage efficiency and energy transition','paceval','V1/V2_ETA_CH, ETA_DIS, E_NEXT, SOC_NEXT'),
 ('Energy, reserve, power, critical load and ramp margins','paceval','V1/V2_MARGIN_*'),
 ('Non-simultaneous and island-only constraints','paceval','V1/V2_NO_SIMULTANEOUS, ISLAND_GRID_GUARD'),
 ('Operating cost and stage screening score','paceval','V1/V2_STAGE_COST, SCREENING_SCORE and component costs'),
 ('Explicit energy-transition sensitivity derivatives','paceval','V1/V2_D_ENEXT_DCH, DDIS, DE'),
 ('Composite per-interval feasible/infeasible gate','paceval','V1/V2_STEP_FEASIBILITY'),
 ('Two-version deltas and conservative margins','paceval','DELTA_*, MIN_RESERVE_ACROSS_MODELS, JOINT_FEASIBILITY'),
 ('Next-hour state carry-forward and schedule aggregation','C++ host','Stateful orchestration, no local mathematical graph'),
 ('Independent precision reference','Python + native C++','Verification only, not production results')
 ],[193,80,222])
 H('5. Experiment setup and reproducible data')
 P('A deterministic generator creates 360 candidate schedules per scenario. The scenarios are sunny grid-connected operation, reduced-PV grid-connected operation and islanded operation with zero utility flows. Each schedule comprises 24 hourly records, for 25,920 unique candidate-hour records and 51,840 version-hour evaluations. The generation includes deliberately invalid combinations to make the negative testing meaningful, including excess battery charge, simultaneous charge and discharge, and electric-balance mismatches.')
 P('The research data are wholly synthetic. They are generated from fixed formulaic PV/load curves, deterministic candidate variation and documented control definitions. No customer meter, inverter or generator dataset is represented, and no probabilistic out-of-sample reliability claim is made. The program and complete data files allow an exact replay with the original SDK runtime.')
 tab(['Evidence from actual execution','Observed count'],[
 ('Domain graphs registered and executed',f'{ev["unique_domain_graphs_executed"]} / {ev["unique_domain_graphs_created"]}'),
 ('Distinct 24-hour candidate schedules',f'{ev["schedule_count"]:,}'),
 ('Model-schedule chains',f'{ev["version_schedule_count"]:,}'),
 ('Version-hour records',f'{ev["version_step_count"]:,}'),
 ('Native C++ reference assertions',f'{ev["independent_native_reference_checks"]:,}'),
 ('Independent 85-digit assertions',f'{audit["reference_assertions"]:,}')
 ],[330,165])
 H('6. Main feasibility outcomes')
 P('For each candidate and each version, the 24-hour classification combines the complete sequence of per-period graph guards with the independent terminal stored-energy target. Passing these tests is a mathematical statement about the explicitly assumed single-bus model, not a grid operating permit.')
 rows=[]
 for scenario,label in [('grid_sunny','Sunny grid'),('grid_cloudy','Cloudy grid'),('island_outage','Islanded')]:
  a=summaries[(summaries.scenario==scenario)&(summaries.model=='V1')];b=summaries[(summaries.scenario==scenario)&(summaries.model=='V2')];rows.append((label,f'{int(a.full_schedule_feasible.sum())} / 360',f'{int(b.full_schedule_feasible.sum())} / 360',f'{float(a.total_cost_USD.median()):.2f}',f'{float(b.total_cost_USD.median()):.2f}'))
 tab(['Resource scenario','Feasible V1','Feasible V2','Median cost V1 (USD)','Median cost V2 (USD)'],rows,[117,85,85,104,104])
 P(f'Across the entire deliberately generated sample, {ev["v1_feasible_schedules"]:,} schedules pass the V1 model and {ev["v2_feasible_schedules"]:,} pass V2. This is not a measured grid reliability success rate. Some V2 configurations avoid violating the upper battery energy bound because their SOC-dependent efficiency reduces energy uptake, even though their final energy tends to be lower. The median final-energy model difference is {comp.delta_final_energy_kWh.median():.3f} kWh and the median modeled cost difference is {comp.delta_cost_USD.median():.3f} USD. These are changes between <b>assumptions about the same schedules</b>, not comparisons of mathematical engines.')
 P('For one fully feasible synthetic example, sunny-grid schedule 0001, V1 finishes at 337.428 kWh with 752.071 USD model cost, while V2 finishes at 336.430 kWh with 761.167 USD. In island mode the same schedule must meet its demand entirely through local resources, with no external grid exchange. This is a mathematical illustration of coupled dispatch effects over a complete horizon.')
 H('7. Independent validation and numerical safeguards')
 P(f'The executable checks 7,452 native end-value assertions against a separately coded C++ reference across sampled schedule periods. A second validator independently reconstructs complete battery state chains with 85-digit mpmath arithmetic and checks {audit["reference_assertions"]:,} values and conditions covering energy, balance, cost, efficiencies, sensitivities, composite guards and full-horizon aggregation. All configured high-precision checks passed. Audit detail, including any textual decimal conversion effects, remains in the machine-readable technical reports rather than in a public engine-versus-engine accuracy table.')
 P('The CSV reader explicitly accepts decimal literals, forbids formula expressions as numeric records, checks row widths, units and domains, and uses the original paceval double/string conversion API for numeric inputs and exports. Algebraic controls include independently verified negative-remainder semantics, logical and relational operators, min/max, and equality at boundaries. The scientific figures are based on actual output files from original paceval runs, rather than host-recalculated substitute physics.')
 P('No general interval-arithmetic proof or verified robust optimization theorem is claimed. The evidence is a finite execution and reference-validation sample. The mathematical model does not account for inverter fault response, AC voltage, frequency, thermal constraints, protective relays, uncertain weather, battery electrochemistry or verified service continuity.')
 s.append(PageBreak());H('8. Application-relevant research figures')
 captions=[
  ('fig01_power_flows','Figure 1. Hourly PV, demand, generator and utility import for the grid-connected synthetic reference schedule. Values come from the executed experimental CSV input/output chain.'),
  ('fig02_battery_energy','Figure 2. Successive paceval battery energy states in both persistent mathematical models, with reserve and final-energy reference lines.'),
  ('fig03_island_operation','Figure 3. In the islanded reference schedule, generation, PV and battery discharge jointly serve the load while utility transfers are constrained to zero.'),
  ('fig04_feasible_schedules','Figure 4. Complete 24-hour feasibility counts under the two model versions, not equipment reliability or measured field success.'),
  ('fig05_cost_distributions','Figure 5. Distribution of model operating-cost outputs across all synthetic schedules and three resource scenarios.'),
  ('fig06_cost_vs_energy','Figure 6. Candidate-level relationship between final energy and modeled cost. Feasibility cannot be determined from a terminal-energy threshold alone.'),
  ('fig07_energy_heatmap','Figure 7. Collection of state trajectories. Each pixel is a stored-energy output from the original paceval transition graphs.'),
  ('fig08_efficiency_variation','Figure 8. SOC-dependent charge and discharge efficiencies in model V2; the assumed functional form is not a fitted manufacturer characteristic.'),
  ('fig09_model_differences','Figure 9. Changes in terminal energy and modeled cost between version V2 and V1 for identical dispatch inputs.'),
  ('fig10_3d_schedule_landscape','Figure 10. Three-dimensional visualization of evaluated schedule candidates. This is a discrete scatter of model results, not a certified continuous optimization surface.')
 ]
 for i,(name,caption) in enumerate(captions):
  fig(name,caption,480 if i!=9 else 400)
  if i in [1,3,5,7]:s.append(PageBreak());H(f'8.{(i+1)//2+1} Additional application results')
 s.append(PageBreak())
 H('9. Interpretation, engineering boundaries and future studies')
 P('<b>What was demonstrated:</b> a true local paceval calculation engine can store multiple nontrivial formula versions, evaluate large numbers of independent input vectors with the original multi-graph batch API, propagate the resulting state over a real 24-hour C++ control loop, produce interpretable power/energy/cost results and support independent mathematical verification.')
 P('<b>What was not demonstrated:</b> an optimized economic dispatch solution, a prediction of real battery lifetime, a power-system feasibility certificate, a protection/relay strategy, grid-forming capabilities, AC transient stability, real-world customer benefit, system safety or compliance with IEEE 2030.7/2030.8/1547. A control implementation additionally needs protection and inverter testing, rigorous uncertainty handling, commissioned electrical equipment and validated power-flow and dynamics models.')
 P('<b>High-value research extensions:</b> supply a calibrated conversion-efficiency map; couple the paceval analytical constraint kernel to an independent Pyomo or oemof MILP/MPC optimizer; model uncertainty in PV and critical load using explicit reserve scenarios; connect to an AC load-flow solver; develop a battery health model supported by a full experimental dataset. These would be additional research milestones, not capabilities proven here.')
 P('The value of paceval in this architecture is mathematical formula reuse and versioned, auditable evaluation. The study neither measures nor claims a CPU/GPU/FPGA/ASIC performance advantage, energy savings from the engine, system-level latency improvement or investment break-even.')
 H('10. Build, evidence package and verification')
 P('The accompanying GitHub-ready package includes the original SDK source interface, C++17 host, CMake build file under src/, source proposal, synthetic input and exact generator, original computed result files, formula manifest, machine-readable execution inventory, independent 85-digit reference script, ten scientific figures as PNG and vector PDF, and README with Linux commands. The external binary runtime is excluded by design. Test outcomes, negative input-check cases and README syntax/link validation are documented in the package audit.')
 H('References and current technological context')
 refs=[
 ('[1]','U.S. Department of Energy. Microgrid Systems.','https://www.energy.gov/oe/microgrid-systems'),
 ('[2]','National Laboratory of the Rockies. REopt Capabilities and Dispatch Modeling.','https://www.nlr.gov/reopt/about/capabilities'),
 ('[3]','oemof.solph. Version 0.6.4, SOC-dependent charging feature (2026).','https://oemof.org/2026/04/17/solph-v0-6-4-saturating-storage/'),
 ('[4]','IEEE 2030.7-2017: Microgrid controller specifications.','https://standards.ieee.org/ieee/2030.7/5941/'),
 ('[5]','IEEE 2030.8-2018: Testing of microgrid controllers.','https://standards.ieee.org/ieee/2030.8/6169/'),
 ('[6]','IEEE 1547-2018: Interconnection/interoperability of DER.','https://standards.ieee.org/ieee/1547/5915/'),
 ('[7]','Nguyen et al. 2024. Microgrid optimal scheduling with battery degradation and renewable uncertainty. Journal of Energy Storage.','https://www.sciencedirect.com/science/article/pii/S2352152X2404249X'),
 ('[8]','Schade 2024. Battery degradation: impact on economic dispatch. Energy Storage.','https://doi.org/10.1002/est2.588'),
 ('[9]','paceval. Mathematical Engine API 4.25 and Product Brief.','https://paceval.com/api/')
 ]
 for a,b,url in refs:P(a+' '+escape(b)+' <link href="'+url+'" color="#147c8a">'+escape(url)+'</link>','ReferenceX')
 P('External literature citations establish the industrial and scientific context. They do not validate the synthetic paceval model or its output. Source access checked on 14 November 2026.','SmallX')
 doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=47,leftMargin=47,topMargin=42,bottomMargin=50,title='Microgrid Storage Dispatch and Feasibility Evaluation with paceval',author='paceval Industrial Research',subject='Reproducible mathematical functionality study, original SDK 4.25')
 def page(c,d):
  c.saveState();W,Hh=A4
  c.setStrokeColor(GOLD);c.setLineWidth(1);c.line(47,35,W-47,35)
  c.setFont('DVS',7);c.setFillColor(GREY);c.drawString(47,24,'paceval.  |  Industrial mathematical research  |  WP 12');c.drawRightString(W-47,24,f'14 Nov 2026  •  {d.page}')
  c.restoreState()
 doc.build(s,onFirstPage=page,onLaterPages=page)
 print('WHITEPAPER:',OUT)
if __name__=='__main__':create()
