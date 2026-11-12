#!/usr/bin/env python3
"""Generate an English PDF only; GitHub README is maintained separately.
Every numbered scientific diagram comes from recorded paceval CSV outputs.
"""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from xml.sax.saxutils import escape
import json
R=Path(__file__).resolve().parents[1]
PDF=R/'paceval_Large_Quantitative_Model_Tools_Whitepaper_EN.pdf'
for name,path in [('Noto','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('NotoBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,path))
navy=colors.HexColor('#142e42');teal=colors.HexColor('#167d82');grey=colors.HexColor('#425b69')
styles={
 'h1':ParagraphStyle('h1',fontName='NotoBold',fontSize=19,leading=26,textColor=navy,spaceAfter=15),
 'h2':ParagraphStyle('h2',fontName='NotoBold',fontSize=12,leading=17,textColor=teal,spaceBefore=10,spaceAfter=8),
 'body':ParagraphStyle('body',fontName='Noto',fontSize=9.3,leading=15.2,textColor=navy,spaceAfter=10),
 'small':ParagraphStyle('small',fontName='Noto',fontSize=8.1,leading=12.3,textColor=grey,spaceAfter=8),
 'cover':ParagraphStyle('cover',fontName='NotoBold',fontSize=25,leading=32,textColor=navy,spaceAfter=10),
 'mid':ParagraphStyle('mid',fontName='NotoBold',fontSize=12,leading=18,textColor=navy,spaceAfter=9),
 'eq':ParagraphStyle('eq',fontName='Noto',fontSize=10.5,leading=18,textColor=navy,spaceAfter=10,leftIndent=16),
}
story=[]
def H(s):story.append(Paragraph(escape(s),styles['h1']))
def H2(s):story.append(Paragraph(escape(s),styles['h2']))
def P(s):story.append(Paragraph(s,styles['body']))
def S(s):story.append(Paragraph(s,styles['small']))
def EQ(s):story.append(Paragraph(escape(s),styles['eq']))
def F(filename,width=455,cap=None):
 from PIL import Image as PILImage
 path=R/'figures'/filename
 with PILImage.open(path) as im: w,h=im.size
 height=min(width*h/w,265)
 story.append(Image(str(path),width=width,height=height))
 if cap:S(cap)
def T(rows,widths=None):
 t=Table([[Paragraph(escape(str(x)),styles['small']) for x in row] for row in rows],colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e0eff2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f8fa')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),1,teal),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8)]));story.append(t)
def page():story.append(PageBreak())
def footer(c,d):
 c.setStrokeColor(colors.HexColor('#aec5d0'));c.line(44,43,A4[0]-44,43)
 c.setFont('Noto',7.4);c.setFillColor(grey);c.drawString(44,30,'paceval | Reusable Large Quantitative Model Tools | November 2026');c.drawRightString(A4[0]-44,30,str(d.page))
# PAGE 1
story.append(Paragraph('PACEVAL | SCIENTIFIC WHITE PAPER | EXECUTED RESEARCH DEMONSTRATOR',styles['small']))
story.append(Paragraph('Reusable Large<br/>Quantitative Model Tools',styles['cover']))
P('<b>Fifty mathematical tool definitions, persistent paceval computation graphs, deterministic invocation and independently audited composition.</b>')
F('00_quantitative_tools_hero.png',485,'Conceptual illustration of a mathematical tool catalogue. Not an experimental plot.')
T([['Recorded research outcome','Value'],['Unique tool definitions','50 across five mathematical families'],['Persistent paceval handles','51 (including an immutable formula revision)'],['Scripted requests','10,000'],['Numerical reference','Native C++ and an independent 80-digit sample audit']],[190,300])
S('Evidence type: actual local C++/paceval SDK execution on synthetic dimensionless mathematical models. No claim is made about a live MCP endpoint, independent AI reasoning, or industrial deployment.')
page()
# PAGE 2
H('1. Introduction: Industrial use case and current state of the art')
P('Industrial analytics platforms increasingly expose narrowly defined computational capabilities to applications and language-model agents. A manufacturing engineering assistant, for example, may need several nonlinear response calculations in a fixed sequence; the required mathematical functions should be deterministic, individually versioned, and independently testable. The key engineering challenge is preserving mathematical contracts while tools are repeatedly invoked and recombined.')
P('The Model Context Protocol (MCP) provides a standard interface for describing and invoking tools. Its 28 July 2026 release introduces a stateless protocol core and updated authorization capabilities; the current tools specification describes named tools, JSON Schema input/output declarations and structured results. These are protocol-level concepts, distinct from the numerical execution layer examined here.')
H2('Research boundary')
P('This experiment implements the local C++ mathematical execution layer using the official paceval facade. Fifty function definitions persist as computation graphs and can be invoked repeatedly by a deterministic dispatcher. The work neither runs a network MCP server nor evaluates the quality of a language model selecting the correct tools. Tool authorization, request routing, JSON Schema validation and user consent remain future system concerns.')
S('References: MCP 2026-07-28 specification and release; paceval public API; NIST AI Risk Management Framework. Full URLs appear on the final page.')
page()
# PAGE 3
H('2. Scientific research question and execution boundary')
P('Can a diverse catalogue of quantitative formula tools be represented as persistent paceval mathematical expressions, executed across many scripted requests and composed deterministically, while retaining native and independent numerical agreement?')
F('01_execution_architecture.png',465,'Figure 1. The implemented boundary: host orchestration and validation; paceval expression graphs; independently implemented reference.')
H2('Separation of responsibilities')
T([['Executed by paceval','Executed by C++ / Python host'],['Graph creation and handle reuse','Tool registration, request dispatch, domain checking'],['Scalar double-precision formula evaluation','Synthetic dataset construction and composition routing'],['Packed batch formula evaluation','CSV export, native reference, 80-digit sample audit']],[232,255])
P('The dispatcher does not interpret arbitrary untrusted expressions. Each formula is frozen before execution. A formula update creates a new computation object and retains the original version.')
page()
# PAGE 4
H('3. Mathematical tool definitions')
P('Each model takes five dimensionless inputs x, y, a, b and c. The frozen experimental domain is x in [0.1,2.9], y in [-1,1] and a,b,c in [0.2,1.4]. Each of five distinct families has ten coefficient values k_j = 0.11 + 0.07j, j = 0,...,9.')
H2('Five independently implemented formula families')
EQ('A: f = a*x^2 + b*ln(1+x) + k*c*y')
EQ('B: f = a*exp(-k*x) + b*sin(x+y) + c*x*y')
EQ('C: f = a/(1+k*x^2) + b*sqrt(1+x) + c*cos(y)')
EQ('D: f = (a*x+b*y+c)/(1+k*x^2) + sin(x*y)')
EQ('E: f = a*ln(1+x^2) + b*exp(-x*y^2) + k*c*x^2')
P('These expressions provide polynomial, logarithmic, exponential, trigonometric, rational and square-root operations, with distinct nonlinear composition. The paceval strings use ln(); the independent C++ reference uses std::log(). All denominators and special-function domains are defined over the admitted input set.')
F('04_tool_registry.png',430,'Figure 4. Version-1 registry of fifty expressions, categorized into five non-equivalent mathematical families.')
page()
# PAGE 5
H('4. Workload and immutable mathematical versions')
P('A deterministic xorshift-derived generator produces 10,000 scripted local requests assigned cyclically to fifty tools. Every fifth request is followed by another actual paceval formula invocation. The host supplies tanh(first_output) as the second function\'s y input, producing 2,000 deterministic two-stage compositions. This is model composition, not a demonstration of autonomous tool discovery.')
EQ('u = f_i(x,y,a,b,c);   v = f_j(x,tanh(u),a,b,c)')
P('The model registry records each exact formula, its coefficient and an immutable version identifier. The demonstration creates a new version-2 formula for tool 1 while retaining the original graph. The version comparison evaluates both on identical inputs and independently checks the modified result.')
F('07_model_versioning.png',430,'Figure 7. Same inputs evaluated by preserved version 1 and independently created version 2 of a mathematical tool.')
S('The updated version is an explicit change of formula definition, not an in-place mutation of a cached calculation handle.')
page()
# PAGE 6
H('5. Actual SDK execution and independent numerical audit')
T([['Verified quantity','Recorded value'],['Distinct frozen mathematical tools','50'],['Persistent graph handles','51'],['Scripted requests','10,000'],['Two-stage compositions','2,000'],['Scalar paceval evaluations','15,723'],['Batch-comparison samples','1,600'],['3D surface evaluation points','3,721'],['Maximum absolute difference vs native C++','1.7763568394002505e-15'],['Independent 80-digit checks','250 / 250 passed'],['CMake/CTest','1 / 1 passed']],[307,181])
P('The C++ program creates each paceval handle once; each request supplies fresh numerical arguments to the same computation. Batch checks pack thirty-two independent input records per graph and compare all results with a separately coded C++ reference. The numeric audit rejects nonfinite values and discrepancies exceeding 1e-10*(1+|reference|).')
P('A separate mpmath-based program independently reimplements the five families at 80-digit precision and checks every fortieth exported request. Its maximum sampled absolute discrepancy was about 2.07e-15. Neither the finite native reference nor this finite multiprecision sample establishes a global error bound.')
page()
# PAGE 7
H('6. Mathematical diversity and numerical accuracy')
F('02_tool_family_outputs.png',465,'Figure 2. Recorded outputs of five mathematically distinct tool families on deterministic input sequences.')
F('03_numerical_audit.png',465,'Figure 3. Maximum observed absolute difference between actual paceval results and the independently implemented native equations, grouped by family.')
P('The plotted discrepancies characterize the executed input samples only. They are not evidence of performance superiority or a proof of correctness for arbitrary function strings.')
page()
# PAGE 8
H('7. Three-dimensional mathematical response visualization')
P('A separately recorded parameter sweep evaluates tool 23 on a 61 x 61 mesh, keeping a=0.9, b=0.8 and c=0.7 fixed while varying x and y across the declared input range. Each displayed height is an actual paceval computation result saved to response_surface.csv.')
F('05_response_surface_3d.png',465,'Figure 5. 3D mathematical response surface: 3,721 real paceval evaluation values, not AI-generated surface geometry.')
F('06_response_contours.png',430,'Figure 6. Contour map from the same exported 3,721 values.')
page()
# PAGE 9
H('8. Result distribution and implementation limits')
F('08_request_distribution.png',460,'Figure 8. Distribution of the 10,000 scripted request outputs produced by the reusable paceval computation graphs.')
H2('Scientific and industrial limitations')
P('The expressions use controlled dimensionless synthetic inputs. They are not calibrated material laws, approved finance models or deployed industrial digital twins. The software demonstrates reusable mathematical execution, graph versioning, and deterministic local tool chaining. It has not exercised networked MCP transport, AI selection correctness, real user input authorization, adversarial injection defense, service load balancing or production security controls.')
P('The experiment does not use paceval Trusted Interval Computation, and it makes no interval certification claim. A production mathematical tool platform would additionally require schemas, safe resource budgets, validation, failure reporting, authentication, authorization and monitoring.')
page()
# PAGE 10
H('9. Reproduction and current technical references')
H2('Build and re-run')
EQ('cmake -S src -B build -DCMAKE_BUILD_TYPE=Release')
EQ('  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so')
EQ('cmake --build build -j; ctest --test-dir build --output-on-failure')
EQ('./build/quant_tools --out reproduced')
P('The actual source code, model registry, 10,000-request CSV, 3,721-point surface, formula version audit, independent native C++ reference, 80-digit mpmath verification script and all generated scientific graphics are included. The original paceval C/C++ SDK facade is included under its original upstream notices; its external shared runtime is not redistributed.')
H2('Selected current sources')
for t,u in [
 ('MCP tools specification (2026-07-28)','https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx'),
 ('MCP specification release (2026-07-28)','https://blog.modelcontextprotocol.io/posts/2026-07-28/'),
 ('MCP security and trust considerations','https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/index.mdx'),
 ('paceval public API','https://paceval.com/api/'),
 ('NIST AI Risk Management Framework','https://www.nist.gov/itl/ai-risk-management-framework')]:
 S(escape(t)+': '+escape(u))
H2('Final scientific conclusion')
P('<b>The defined 50-tool mathematical library has been successfully executed with 51 reusable paceval computation objects and independently verified on the stated synthetic workload.</b> The demonstrated achievement is the numerical foundation of a future agent-accessible tool catalogue, not a verified production MCP server, an AI model or an operational industrial decision system.')

doc=SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=49,bottomMargin=60,title='paceval | Reusable Large Quantitative Model Tools',author='paceval research demonstrator',pageCompression=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(PDF)
