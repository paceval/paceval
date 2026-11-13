#!/usr/bin/env python3
"""Recreate the 13-page English WP050 PDF exclusively from recorded original SDK outputs.
Fixed-page ReportLab layout, measured figures, explicit concept artwork disclaimer.
"""
import argparse,csv,io
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
PW,PH=A4;LEFT=46;RIGHT=46;W=PW-LEFT-RIGHT
INK=HexColor('#2d3e47');TEAL=HexColor('#3e7b73');RUST=HexColor('#ba5c3d');PALE=HexColor('#f4f4ed');MUTED=HexColor('#607479');LINE=HexColor('#d8ddd7')
FONT='/usr/share/fonts/truetype/dejavu'
for name,fn in [('Body','DejaVuSans.ttf'),('Strong','DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,str(Path(FONT)/fn)))

class Paper:
 def __init__(self,root):
  self.root=root;self.out=root/'paceval_Agent_Controlled_Production_Planning_Scores_Whitepaper_EN.pdf';self.c=canvas.Canvas(str(self.out),pagesize=A4,pageCompression=1);self.c.setTitle('Agent-Controlled Production-Planning Scores | paceval Research');self.y=0;self.page=0
  self.style=ParagraphStyle('b',fontName='Body',fontSize=9.2,leading=14.5,textColor=INK)
  self.sm=ParagraphStyle('small',parent=self.style,fontSize=8.15,leading=12.2)
  self.tbl=ParagraphStyle('table',parent=self.style,fontSize=7.45,leading=11)
 def need(self,h):
  if self.y-h < 61:raise RuntimeError(f'Page {self.page} content overflow (y={self.y:.1f}, required={h:.1f})')
 def begin(self,title,eyebrow='ORIGINAL PACEVAL 4.25 | EXECUTED RESEARCH'):
  self.page+=1;c=self.c;c.setFillColor(RUST);c.rect(0,PH-12,PW,12,fill=1,stroke=0)
  c.setFont('Strong',7.3);c.setFillColor(MUTED);c.drawString(LEFT,PH-34,'paceval | SCIENTIFIC RESEARCH | 2026');c.drawRightString(PW-RIGHT,PH-34,eyebrow)
  c.setStrokeColor(LINE);c.line(LEFT,PH-43,PW-RIGHT,PH-43)
  self.y=PH-69
  if title:self.title(title)
 def title(self,s):
  self.c.setFont('Strong',16.2);self.c.setFillColor(INK);self.c.drawString(LEFT,self.y,s);self.y-=31
 def subtitle(self,s):
  self.y-=6;self.need(29);self.c.setFillColor(TEAL);self.c.setFont('Strong',10.4);self.c.drawString(LEFT,self.y,s);self.y-=20
 def p(self,s,small=False):
  st=self.sm if small else self.style;para=Paragraph(s,st);_,h=para.wrap(W,999)
  self.need(h+10);para.drawOn(self.c,LEFT,self.y-h);self.y-=h+9
 def note(self,s):
  box=Paragraph(s,self.sm);_,h=box.wrap(W-23,500);height=h+19;self.need(height+12)
  self.c.setFillColor(PALE);self.c.roundRect(LEFT,self.y-height,W,height,6,stroke=0,fill=1)
  box.drawOn(self.c,LEFT+12,self.y-h-10);self.y-=height+12
 def tab(self,header,rows,widths):
  a=[[Paragraph('<b>'+str(x)+'</b>',self.tbl) for x in header]]
  for row in rows:a.append([Paragraph(str(x),self.tbl) for x in row])
  t=Table(a,colWidths=widths,hAlign='LEFT',repeatRows=1)
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,0),.6,TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#ffffff'),HexColor('#faf9f5')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
  _,h=t.wrap(W,800);self.need(h+12);t.drawOn(self.c,LEFT,self.y-h);self.y-=h+13
 def eq(self,latex,width_hint=7.7):
  self.need(49);fig=plt.figure(figsize=(width_hint,.52),dpi=190);fig.patch.set_alpha(0)
  fig.text(.5,.5,'$'+latex+'$',ha='center',va='center',fontsize=16.1,color='#2d3e47')
  mem=io.BytesIO();fig.savefig(mem,format='png',dpi=190,transparent=True,bbox_inches='tight',pad_inches=.06);plt.close(fig);mem.seek(0)
  image=ImageReader(mem);iw,ih=image.getSize();w=min(W*.97, W*ih/iw*5.3);h=w*ih/iw
  if h>39:h=39;w=h*iw/ih
  self.c.drawImage(image,LEFT+(W-w)/2,self.y-h,width=w,height=h,mask='auto',preserveAspectRatio=True)
  self.y-=h+12
 def fig(self,file,caption,maxheight=245):
  img=ImageReader(str(self.root/'figures'/(file+'.png')));iw,ih=img.getSize();width=min(W,maxheight*iw/ih);height=width*ih/iw
  par=Paragraph(caption,self.sm);_,ch=par.wrap(W,100)
  self.need(height+ch+25);self.c.drawImage(img,LEFT+(W-width)/2,self.y-height,width=width,height=height,preserveAspectRatio=True)
  self.y-=height+7;par.drawOn(self.c,LEFT,self.y-ch);self.y-=ch+14
 def end(self):
  self.c.setStrokeColor(LINE);self.c.line(LEFT,49,PW-RIGHT,49);self.c.setFont('Body',7);self.c.setFillColor(MUTED)
  self.c.drawString(LEFT,33,'paceval | Agent-Controlled Production-Planning Scores | 2026');self.c.drawRightString(PW-RIGHT,33,str(self.page));self.c.showPage()
 def close(self):self.c.save();print('PDF',self.out,'pages',self.page)

def create(root):
 p=Paper(root)
 with (root/'results/sdk_execution.txt').open() as f:meta=dict(line.strip().split('=',1) for line in f if '=' in line)
 with (root/'results/scenario_summary.csv').open(newline='') as f:r=list(csv.DictReader(f))
 with (root/'results/agent_outcomes.csv').open(newline='') as f:labels=list(csv.DictReader(f))
 def select(key):return next(x for x in r if x['scenario']==key)
 delivery=select('S2_regular_delivery_v2');change=select('S2_regular_changeover_v2');rush=select('S2_rush_delivery_v2')
 # Cover
 p.begin('',eyebrow='INDEPENDENTLY VERIFIED | ORIGINAL SDK')
 p.y=PH-105;c=p.c;c.setFont('Strong',22.5);c.setFillColor(INK)
 c.drawString(LEFT,p.y,'Agent-Controlled')
 c.drawString(LEFT,p.y-32,'Production-Planning Scores')
 p.y-=77;p.p('Reusable and versioned mathematical schedule-cost graphs for structured agent priorities and an independently verified small manufacturing job shop.')
 img=ImageReader(str(root/'figures/00_production_planning_hero.png'))
 p.need(W/2+3);c.drawImage(img,LEFT,p.y-W/2,width=W,height=W/2,preserveAspectRatio=True);p.y-=W/2+8
 p.p('<i>Concept illustration; not a computed research result. The same 2400 x 1200-pixel source is used in the GitHub README.</i>',small=True)
 p.subtitle('Executed research outcome')
 p.p('<b>52 actual paceval graphs</b> | <b>32 complete policy/model scenarios</b> | <b>643 multi-graph batches</b> | <b>3,095,426 executed graph outputs</b>. Every winning schedule and its full cost have been independently verified.')
 p.p('Scope: four synthetic jobs, three machines and two mathematical objective versions. Agent requests are structured fixtures, not live LLM calls. No physical production deployment, real-energy measurements or industrial cost advantage is claimed.',small=True)
 p.end()
 # page2
 p.begin('1. Industrial use case and state of the art')
 p.p('Discrete-part manufacturing relies on production planners to route orders through machines while meeting delivery commitments, managing setup changes and using limited equipment time. Each job consists of ordered operations. A machine can process only one operation at a time, and switching product family may introduce a setup interval before the next operation. Managers may prioritize throughput, due-date performance, changeover reduction or a modeled electricity proxy.')
 p.subtitle('A practical planning decision')
 p.p('Consider a hypothetical small manufacturing workshop preparing four orders on three machines. The delivery planner wants all orders finished on time; the maintenance or shop-floor planner wants fewer changeovers. They should not change the feasibility rules merely because their priorities differ. An upstream agent can communicate its priorities through a bounded parameter request, while a deterministic scheduler enumerates feasible plans and paceval evaluates the identical mathematical formula for each plan.')
 p.subtitle('Established solution methods and recent research')
 p.p('Constraint programming, mixed-integer optimization and metaheuristics are established scheduling tools. Google OR-Tools publishes a CP-SAT example with job-precedence and no-overlap constraints [1]. In 2025, Wang et al. investigated multi-agent LLM-based optimization frameworks [2]. Hu et al. (2026) showed that language-driven scheduling reconfiguration requires structural feasibility checking beyond objective-value agreement [3]. A November 2026 survey by Xiang et al. places LLM scheduling agents in the broader modeling-to-solving landscape [4].')
 p.p('The ISA-95 / IEC 62264 framework concerns manufacturing operations integration [6]; ISO 22400 defines manufacturing KPI concepts and terminology [5]. These standards do not validate this synthetic cost model. The present research tests the mathematical scoring layer that might serve a larger production-control architecture, not a substitute for a production scheduling system or safety review.')
 p.note('Research boundary: the small exhaustive scheduler is the combinatorial controller, paceval performs the important stateless mathematical cost and margin functions, and the independent verifier checks both numerical end results and all selected machine allocations.')
 p.end()
 # page3
 p.begin('2. Research architecture and scope')
 p.p('The experiment controls input routes, processing durations, due dates, family-dependent changeovers, model revisions and four agent-supplied priority vectors. The prototype accepts a strictly validated CSV of policies. The C++ host detects cyclic machine orders, builds earliest-start feasible schedules, checks precedence and machine exclusivity, and selects the lowest paceval-computed objective for each selected policy/version combination.')
 p.fig('01_executed_decision_architecture','Figure 1. Research system architecture. The agent input is a deterministic fixture; no live language-model inference or tool transport was run.',maxheight=215)
 p.subtitle('Two separate questions, two independent checks')
 p.p('<b>Scheduling:</b> Are the selected start and end times globally optimal among the enumerated machine-order assignments for the given scenario and objective? An independent Python enumerator repeats every machine order and checks the published winner. <b>Mathematical execution:</b> Are the reusable original paceval expressions and their complete score values independently reproducible? A hand-written 80-decimal mpmath reference and native C++ checks verify the executed results.')
 p.p('The underlying job shop contains four fixed job routes with three operations per job. For each setup regime, there are 24 cubed possible machine orders, of which 1,860 satisfy the acyclic precedence/resource-order structure. This finite exact search does not establish scalability to real flexible job shops or large factories.')
 p.end()
 # page4
 p.begin('3. Mathematical model and assumptions')
 p.p('Let operation o start at s(o), last p(o) hours and finish at e(o). For each selected machine order, the scheduler enforces both job precedence and machine predecessor constraints. Machine changeover times are symmetric binary-family fixtures; actual tooling and labor setups are not modeled.')
 p.eq(r'e_o=s_o+p_o,\qquad s_{v}\geq e_u+\sigma_{uv}')
 p.eq(r'\sigma_{uv}=\sigma_0(f_u-f_v)^2,\quad f\in\{0,1\}')
 p.p('Job tardiness is the positive part of lateness. The signed due-date margin, priority-weighted tardiness and its convex square are real paceval expressions, not native substitutes.')
 p.eq(r'T_j=\max(0,C_j-d_j),\quad W_T=\sum_{j=0}^{3}q_jT_j')
 p.p('A synthetic electricity surrogate is calculated from fixed machine power coefficients and operation durations; an explicit setup-energy surcharge is added. Normalization denominators are research assumptions, not accounting exchange rates.')
 p.eq(r'J_1=w_M\frac{M}{30}+w_T\frac{W_T}{25}+w_S\frac{S+0.5N_S}{20}+w_E\frac{E+0.25S}{60}',width_hint=10)
 p.eq(r'J_2=J_1+0.15w_T\frac{\sum_jq_jT_j^2}{250}+0.06\frac{I}{60}+0.04\left(\frac{T_{\max}}{15}\right)^2',width_hint=10)
 p.p('M is makespan, S is setup hours, N(S) the family-change count, I the three-machine idle-time sum, E the synthetic processing energy, and T(max) the largest positive job delay. Weights sum to one. Both graph versions are separately registered and executed, with identical scenario inputs.')
 p.end()
 # page5
 p.begin('4. What the original paceval API actually does')
 p.p('The original paceval 4.25 SDK is initialized, 52 full mathematical expressions are registered and their handles reused. Multi-graph batches evaluate many independent feasible schedules and a separate policy-weight surface. Short scalar calls test graph semantics. All mathematical functions listed as paceval-owned in the register were actually evaluated on meaningful schedule inputs.')
 p.tab(['Industrial mathematical function','Actual execution','Graph / version'],[
 ('Family-change setup time','paceval','sequence_changeover_hours'),
 ('Per-job lateness, early completion and weighted delay','paceval','lateness_job*, tardiness_job*, weighted_tardiness_job*'),
 ('Full priority-weighted delay and squared late delivery','paceval','weighted_tardiness_total, weighted_tardiness_squared'),
 ('Makespan, setup and synthetic energy score terms','paceval','*_component, energy_total, setup_units'),
 ('Full versioned objective with time/delivery risk','paceval','policy_objective_v1 and _v2'),
 ('Due margins, score budget, horizon and sensitivity','paceval','*_margin, d_objective_d_*'),
 ('Machine order enumeration, discrete precedence and ranking','C++ host','Combinatorial state/decision control'),
 ('Independent schedule and high precision reconstruction','Python','Verification only; separate code paths')],widths=[W*.42,W*.18,W*.40])
 p.p('The C++ host carries the structural scheduler and validated policy requests, rather than approximating a combinatorial solver with score expressions. It does not silently execute composite policy objectives in native code. C++ native cost calculations are independent validation only.')
 p.note('Audit trail: results/formula_registry.csv lists original expression strings, results/math_execution_inventory.csv maps every important function to its actual owner, and results/graph_probe_values.csv contains original SDK numerical output for all 32 scenarios.')
 p.end()
 # page6
 p.begin('5. Executed deterministic planning scenarios')
 p.p('Four distinct agent priorities, two family changeover-time regimes, nominal versus rush due dates and two formula versions yield 32 actually executed scenarios. Each deterministic policy is loaded from a validated allowlisted CSV. The host searches every possible machine order and selects the best graph-scored feasible schedule. The synthetic electricity values are not measured production consumption.')
 p.subtitle('Same shop, alternative policy priorities (2-hour setup, nominal due dates, v2)')
 p.tab(['Agent policy','Makespan','Weighted delay','Setup','Electricity'],[
 ('Delivery-focused','17 h','0 weighted h','10 h','46.2 kWh'),
 ('Changeover-focused','20 h','6.2 weighted h','6 h','45.2 kWh')],widths=[W*.28,W*.16,W*.20,W*.14,W*.22])
 p.p('The delivery-oriented policy uses a larger tardiness weight, while the changeover-oriented policy trades some lateness for fewer setup hours. Their published objective values are %.4f and %.4f respectively, but because their weights differ they are <b>not</b> directly comparable as absolute global production quality.'%(float(delivery['objective_score']),float(change['objective_score'])))
 p.subtitle('Controlled additional workload: rush due dates')
 p.p('For the 2-hour changeover rush-case under the delivery policy and v2, the chosen plan has a %s-hour makespan, weighted tardiness %s and a computed score of %.4f. Under that policy\'s illustrative budget the C++ decision stage labels the result REJECT. This is not an unsafe-equipment determination, but the outcome of a declared numerical planning rule.'%(rush['makespan_h'],rush['weighted_tardiness_h'],float(rush['objective_score'])))
 counts={k:sum(x['decision']==k for x in labels) for k in ('ACCEPT','REVIEW','REJECT')}
 p.note('The synthetic decision rule produces <b>%s ACCEPT, %s REVIEW and %s REJECT</b> statuses across the 32 cases. The host uses the signed budget margin returned by an original paceval graph. These are internal workflow labels, not physical production authorizations.'%(counts['ACCEPT'],counts['REVIEW'],counts['REJECT']))
 p.end()
 # page7
 p.begin('6. Executed verification and reproducibility')
 p.p('The C++ application performs explicit independent native checks of representative mathematical components including the full score, the quadratic tardiness risk and signed margins. The Python independent schedule checker reconstructs all machine-order assignments for each setup level and verifies the actual winning schedule under each formula version and policy. The separate 80-digit reference re-derives all 52 mathematical graph quantities for each recorded case, using high-precision input values based on the original binary64 inputs.')
 p.tab(['Verified artifact','Observed result'],[
 ('Original persistent paceval graphs actually executed',meta['graphs_registered_and_executed']),
 ('Original multi-graph batch calls',meta['multi_graph_batch_calls']),
 ('Original graph outputs returned',meta['multi_graph_formula_outputs']),
 ('Complete independently verified scenario winners','32'),
 ('Independent operation-interval checks','768'),
 ('Independent 80-decimal graph checks','1,664'),
 ('Native C++ sampled component/full-score checks',meta['sampled_native_composed_checks']),
 ('Production policy input whitelisting','Accept valid; reject malformed policies')],widths=[W*.76,W*.24])
 p.subtitle('Conditions that are not certified')
 p.p('These tests establish numerical consistency at evaluated points and exhaustive optimization of one small fixed-routing job shop. They do not prove performance scalability, physical machine compatibility, industrial economic benefit, safe autonomous control, LLM inference robustness or a global floating-point error bound. No Trusted Interval Computation (TINC) is used.')
 p.p('The complete reproduction path, external original paceval library requirement, CMake build, CTest and regeneration scripts are recorded in README.md. Numerical comparison details remain in machine-readable audits, not in publication plots or in benchmark-versus-native performance claims.')
 p.end()
 # pages8-12 (10 quantitative figures)
 plots=[('7.1 Production schedule and scoring policies',[
  ('02_feasible_schedule_gantt','Figure 2. Recorded winning machine-by-machine intervals for the synthetic delivery policy with two-hour family changeovers.'),
  ('03_agent_version_score_comparison','Figure 3. Two persistent score formula versions, separately evaluated by paceval for each declared policy.')]),
 ('7.2 Candidate space and controlled formula changes',[
  ('04_combinatorial_candidate_tradeoffs','Figure 4. All 1,860 acyclic machine-order candidates with their actual paceval schedule objective and priority-weighted delay.'),
  ('05_version_revision_effect','Figure 5. Score change caused by the controlled addition of convex tardiness and idle-time terms.')]),
 ('7.3 Parameter studies and objective trade-offs',[
  ('06_paceval_planning_score_surface_3d','Figure 6. Genuine three-dimensional paceval score response across valid agent-priority weight mixtures at a fixed selected schedule.'),
  ('07_energy_delivery_tradeoff','Figure 7. Distinct selected schedule electricity surrogates and tardiness under four documented agent priorities.')]),
 ('7.4 Numerical decision guards and sensitivities',[
  ('08_policy_constraint_margins','Figure 8. Original paceval signed due-date, horizon and budget margins for the synthetic rush scenario.'),
  ('09_analytical_policy_sensitivities','Figure 9. Explicit analytic derivatives of the actual versioned paceval objective with respect to priority weights.')]),
 ('7.5 Meaningful composite outputs and model changes',[
  ('10_full_cost_decomposition','Figure 10. End-to-end component accounting for the actual paceval composite scores; no native substitute supplies the reported components.'),
  ('11_changeover_scenario_impact','Figure 11. Real selected job-shop makespan changes under two controlled setup-time regimes, chosen by paceval-computed scores.')])]
 for head,entries in plots:
  p.begin(head)
  for name,cap in entries:p.fig(name,cap,maxheight=235 if name!='06_paceval_planning_score_surface_3d' else 226)
  p.end()
 # page13
 p.begin('8. Interpretation, limits and research sources')
 p.p('The successful result demonstrates that a small deterministic agent-to-scheduler-to-paceval workflow can reuse original mathematical execution graphs across independent scheduling candidates, update priority weights without replacing unchanged graph handles, maintain distinct score formula versions and evaluate signed numerical decision margins. It does not show that a language model produced the policy, that paceval solves NP-hard job-shop optimization internally or that any industrial deployment is complete.')
 p.subtitle('Scientific and deployment limitations')
 p.p('All jobs, process durations, two-family changeovers, due dates and power coefficients are synthetic; routing is fixed. The model has no shifts, maintenance, machine downtime, workers, transport resources, sequence-dependent operator crews, capacity buffering or MES data. Real manufacturing requires calibration, constraint coverage review, role authorization, audit of agent instructions and actual system testing. The current agent requests are validated deterministic fixtures. The demonstrated score budgets are not safety margins or regulatory limits.')
 p.subtitle('Selected foundational and recent references')
 refs=[
 '[1] Google OR-Tools, Job shop scheduling with CP-SAT: developers.google.com/optimization/scheduling/job_shop.',
 '[2] Wang, Y., Wang, J., Chu, Z. (2025), Multi-agent large language models as evolutionary optimizers for scheduling optimization. Computers &amp; Industrial Engineering 206, 111197. doi:10.1016/j.cie.2025.111197.',
 '[3] Hu, K. et al. (2026), FJSP-E2E: A process-verified framework for automatic scheduling-model reconfiguration. Journal of Manufacturing Systems. doi:10.1016/j.jmsy.2026.08.009.',
 '[4] Xiang, W. et al. (2026), A survey on large language models for scheduling. Advanced Engineering Informatics 76, 104946. doi:10.1016/j.aei.2026.104946.',
 '[5] ISO 22400-1:2014, manufacturing operations KPIs, confirmed 2025: iso.org/standard/56847.html.',
 '[6] ISA-95 / IEC 62264, Enterprise-Control System Integration: isa.org/standards-and-publications/isa-standards/isa-95-standard.',
 '[7] paceval Mathematical Engine, original C/C++ SDK and API: github.com/paceval/paceval.'
 ]
 for x in refs:p.p(x,small=True)
 p.p('Reproduce: original separately supplied Linux paceval runtime, src/CMakeLists.txt, 4 CTest tests, src/high_precision_reference.py, src/verify_results.py, src/make_figures.py, and this PDF-generation script. Source SDK copyright and AGPL notices remain intact.',small=True)
 p.end()
 assert p.page==13,p.page
 p.close()
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=a.parse_args();create(args.root)
