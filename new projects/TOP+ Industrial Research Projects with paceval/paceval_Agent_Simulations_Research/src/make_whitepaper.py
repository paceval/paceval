"""Produce a page-designed English scientific report from executed WP035 artifacts."""
from pathlib import Path
import csv
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from PIL import Image as PILImage
R=Path(__file__).resolve().parents[1];P=R/'paceval_Agent_Orchestrated_Mathematical_Simulations_Whitepaper_EN.pdf'
for name,path in [('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,path))
N=colors.HexColor('#123752');T=colors.HexColor('#087F86');M=colors.HexColor('#536A77');W,H=A4;ST=getSampleStyleSheet()
ST.add(ParagraphStyle(name='title35',fontName='DejaVu-Bold',fontSize=22,leading=30,textColor=N,spaceAfter=15))
ST.add(ParagraphStyle(name='h35',fontName='DejaVu-Bold',fontSize=16,leading=22,textColor=N,spaceAfter=11))
ST.add(ParagraphStyle(name='sub35',fontName='DejaVu-Bold',fontSize=10.5,leading=16,textColor=T,spaceBefore=9,spaceAfter=6))
ST.add(ParagraphStyle(name='body35',fontName='DejaVu',fontSize=8.7,leading=14.5,spaceAfter=8,textColor=colors.HexColor('#273946')))
ST.add(ParagraphStyle(name='small35',fontName='DejaVu',fontSize=7.2,leading=11.2,spaceAfter=6,textColor=M))
ST.add(ParagraphStyle(name='formula35',fontName='DejaVu',fontSize=10.5,leading=19,spaceBefore=9,spaceAfter=12,alignment=TA_CENTER,textColor=N))
story=[]
def add(t,k='body35'):story.append(Paragraph(t,ST[k]))
def title(t):add(t,'h35')
def sub(t):add(t,'sub35')
def new():story.append(PageBreak())
def picture(n,maxw=485,maxh=330):
 img=R/'figures'/n; w,h=PILImage.open(img).size;f=min(maxw/w,maxh/h);story.append(Image(str(img),width=w*f,height=h*f));story.append(Spacer(1,6))
def table(rows,widths):
 cells=[[Paragraph(str(c),ST['small35']) for c in row] for row in rows];t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.HexColor('#E4EFF2'),colors.white]),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#C9D9E2')),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'TOP')]));story.extend([t,Spacer(1,9)])
def foot(can,doc):
 can.setStrokeColor(T);can.line(40,49,W-40,49);can.setFillColor(M);can.setFont('DejaVu',7);can.drawString(42,34,'paceval | WP_035 Agent-Orchestrated Mathematical Simulations | November 2026');can.drawRightString(W-42,34,str(doc.page))
# Cover
add('PACEVAL  |  SCIENTIFIC RESEARCH DEMONSTRATOR','sub35');add('Agent-Orchestrated<br/>Mathematical Simulations','title35')
add('Reusable simulation expressions, deterministic workflow decisions, recorded retries, independent validation and controlled mathematical versioning.','body35')
picture('00_workflow_hero.png',505,255)
add('<b>Executed result:</b> 100 deterministic scenarios; 6 persistent paceval graphs; 38,562 scalar evaluations; 5,257 batch evaluations; 52 observed-triggered retries; 79 accept and 21 review decisions. Original paceval Linux SDK execution and CTest passed.','body35')
add('Cover visual: conceptual editorial illustration of workflow stages. It is not a measured simulation result. The study uses synthetic models, not a live AI agent or a network MCP server.','small35');new()
# 2
title('1. Industrial application and state of practice')
add('Industrial simulation workflows repeatedly evaluate physical or mathematical models, compare simulated outputs with recorded targets, and decide whether to approve a candidate or reconfigure and rerun it. This pattern appears in digital-twin model assessment, process engineering, software-in-the-loop validation and engineering design studies. The practical need is not simply arithmetic: it includes repeatable orchestration, input contracts, provenance, result interpretation and controlled model changes.')
sub('Research context in 2026')
add('The Model Context Protocol (MCP) formalizes typed tool interfaces and structured tool outputs. The July 28, 2026 specification highlights explicit tool schemas, versioning and security controls. Scientific workflow research increasingly examines dynamic orchestration, reproducibility, execution provenance and responsible autonomous control. These are distinct requirements from evaluating an explicit mathematical expression.')
sub('Specific contribution of WP_035')
add('This experiment implements a deterministic offline analogue of the application layer: a scripted controller selects one of three simulation functions, invokes paceval through persistent mathematical graphs, computes an objective, optionally retries under a declared policy, and records an auditable final decision. It is a <b>mathematical-workflow feasibility demonstration</b>. It does not use a language model or implement MCP transport, authorization or autonomous scientific discovery.')
picture('01_workflow.png',475,185)
add('Figure 1. Demonstrated division of responsibility between scripted controller, paceval kernel and independent validation.','small35');new()
# 3
title('2. Defined mathematical simulation models')
add('Three dimensionless and deliberately simple ordinary differential-equation families provide meaningfully different operator combinations. The host uses fixed-step explicit Euler time integration (h = 0.025), while each right-hand side is an immutable paceval expression graph.')
sub('Family A: relaxation analogue')
add('dx/dt = −p (x − q)','formula35')
add('Illustration: relaxation of a controlled process state toward its target q, with positive response coefficient p.')
sub('Family B: damped periodic forcing')
add('dx/dt = −p x + q sin(t)','formula35')
add('Illustration: a forced response with damping coefficient p, input amplitude q and known synthetic forcing coordinate t.')
sub('Family C: logistic evolution')
add('dx/dt = p x (1 − x/q)','formula35')
add('Illustration: growth with saturation q. The controller uses q &gt; 0 and positive initial state in the simulated study.')
sub('Residual and squared objective')
add('r = sqrt((x − y)²) / (σ + 10⁻⁶),    J = ((x − y)/(σ + 10⁻⁶))²','formula35')
add('The observation y is deterministic and generated from the same model family with a hidden fixed parameter. The small additive constant avoids a zero denominator. It is not a probabilistic uncertainty guarantee. The host averages J across 64 observations for its scenario decision.');new()
# 4
title('3. paceval graph architecture and version control')
add('Six computations are created using the unchanged vendor adapter files paceval_main.h and paceval_main.cpp, linked to a compatible external shared library. The scalar evaluation API is used inside every simulation time step, and the SDK batch API evaluates the residual surface and additional reference samples.')
table([['Graph identifier','Actual computation and role'],['1–3','Three dimensionless model RHS expressions'],['4','Normalized absolute residual'],['5','Normalized squared residual'],['6','Thermal model revision with a cubic term']], [125,367])
sub('Controlled formula revision')
add('Original: f1 = −p(x − q). Revised: f2 = −p(x − q) − 0.02(x − q)³. Both graphs are created independently. Neither expression is silently overwritten; both remain available throughout the run.')
picture('08_versioned_models.png',465,245)
add('Figure 2. Retained original and revised thermal expressions evaluated with paceval. No claims are made about model superiority.','small35');new()
# 5
title('4. Deterministic workload and orchestration policy')
add('A total of 100 scenarios selects model family via scenario identifier modulo three. Each case generates 64 clean synthetic observations with a declared parameter, deterministic starting state and step size. A candidate parameter is selected by a fixed perturbation function. The graph evaluates the candidate state and squared normalized objective.')
add('The controller performs one additional attempt only when the first average objective exceeds 0.005. The retry parameter is obtained from the <b>first observed numerical derivative</b> using the known selected model equation, then averaged with the initial candidate. The controller never reads the hidden true parameter in this decision. Such one-step estimation works unusually well for these noise-free, directly identifiable demonstrations; it does not generalize to arbitrary engineering inverse problems.')
add('A final average squared objective at or below 0.005 receives ACCEPT; all other results receive REVIEW. These statuses are synthetic workflow labels without real-world safety significance.')
table([['Recorded execution property','Observed output'],['Scenarios and saved step traces','100 scenarios / 6,400 step records'],['Initial-score-triggered retries','52'],['Final policy decisions','79 ACCEPT / 21 REVIEW'],['Immutable formula definitions','6 distinct mathematical graph handles']], [220,272])
picture('04_decisions.png',470,175)
add('Figure 3. Workflow outcomes for the declared synthetic threshold.','small35');new()
# 6
title('5. Three simulated model families and scored behavior')
picture('02_model_trajectories.png',475,418)
add('Figure 4. Synthetic observations and paceval-integrated states for one representative scenario per model family. The host owns the explicit Euler step; paceval owns the evaluated model right-hand side.','small35');new()
# 7
title('6. Retry policy and per-model differences')
picture('03_retry_scores.png',478,280)
add('Figure 5. Scenario scores before and after the deterministic retry policy; the dashed horizontal line is the chosen demonstration acceptance threshold.','small35')
picture('05_model_scores.png',478,235)
add('Figure 6. Distribution of final objective values by model family. Different scales and conditions can affect interpretation.','small35');new()
# 8
title('7. True numerical response surfaces produced by paceval')
picture('06_residual_surface_3d.png',478,300)
add('Figure 7. Three-dimensional normalized residual response surface; 3,721 locations were evaluated using the paceval batch API.','small35')
picture('07_residual_contour.png',468,235)
add('Figure 8. Two-dimensional contours from the same output grid.','small35');new()
# 9
title('8. Independent scientific audit and reproduction')
add('The actual Linux CMake build and SDK integration passed CTest. The C++ program independently checks every evaluated right-hand-side output and derived score against separately implemented numerical expressions. Its audit file records 38,562 scalar evaluations, 5,257 batch evaluations and 43,657 internal numerical reference checks. No unpublished speed or precision advantage is claimed.')
add('A separate Python program evaluates 449 selected exported values with 80-digit mpmath reference arithmetic and passes its configured tolerance. Dataset verification checks the count of 100 scenarios, 6,400 trace values, 3,721 residual grid points, unique formula registry, final policy status logic and retry logs. All published numerical plots are regenerated from the exact CSV outputs.')
sub('Build and reproduce (from repository root)')
add('cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/compatible/libpaceval_linux_sharedLIB.so','small35')
add('cmake --build build -j<br/>ctest --test-dir build --output-on-failure<br/>./build/agent_simulations --out examples<br/>python3 src/verify_results.py<br/>python3 src/high_precision_reference.py<br/>python3 src/make_figures.py<br/>python3 src/check_readme_math.py','small35')
sub('Evidence and scientific limitations')
add('All observations are synthetic, clean, dimensionless and produced by the frozen reference model. Fixed-step integration has discretization error, and the scenario model is not calibrated against measured physical data. The retry estimator has access to the first observation and a known analytical model but not to the hidden generating parameter. Finite numerical validation cannot establish global error guarantees or safe decisions in untested operating regions.')
add('The original paceval runtime binary is external and intentionally not distributed in the ZIP. Its upstream redistribution conditions must be checked independently.');new()
# 10
title('9. Industrial interpretation, future research and sources')
add('The central scientific result is that mathematical execution graphs from paceval can be combined into a reproducible, policy-directed simulation workflow without reconstructing the underlying expressions for each scenario. Separate result logs preserve model choice, parameter revision, mathematical residual and final decision. This is an appropriate prototype for the calculation layer of an AI-agent tool system.')
sub('Next industrial step')
add('A follow-on study should integrate this calculation layer into a controlled MCP tool service with input/output schemas, authorization, approval for sensitive operations, resource quotas, provenance, model version hashes, and real external simulator or observational datasets. Only then could a real AI-agent orchestrator be tested for planning quality, error recovery, security and operational reliability. Closed-loop simulations should be checked for convergence, parameter identifiability and observation noise under realistic conditions.')
sub('Selected external references')
for s in [
 'Model Context Protocol, Tools specification 2026-07-28. https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx',
 'Model Context Protocol, official 2026-07-28 release announcement. https://blog.modelcontextprotocol.io/posts/2026-07-28/',
 'Alnasir (2026), AI-Driven Scientific Computing Workflows: A Systems Review of Orchestration, Execution, Reproducibility and Provenance, preprint. https://arxiv.org/abs/2609.21162',
 'NIST AI Risk Management Framework. https://www.nist.gov/itl/ai-risk-management-framework',
 'paceval Mathematical Engine, official source and API. https://github.com/paceval/paceval'
]:add(s,'small35')
sub('Conclusion')
add('The specified deterministic orchestration, six persistent mathematical graphs and audited synthetic scientific calculations provide a positive feasibility result for reusable paceval computation within an agent-like simulation workflow. They do not establish a live LLM-agent system, MCP conformance, industrial simulation validity or a safety certification.')
SimpleDocTemplate(str(P),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=52,bottomMargin=65,title='WP_035 Agent-Orchestrated Mathematical Simulations',author='paceval Scientific Research Demonstrator').build(story,onFirstPage=foot,onLaterPages=foot)
print('Created PDF:',P)
