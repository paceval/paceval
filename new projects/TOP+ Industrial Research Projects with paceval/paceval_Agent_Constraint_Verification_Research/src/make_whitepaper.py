#!/usr/bin/env python3
"""Create WP025 English report. Each numbered experimental figure is backed by exported paceval CSV data."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from PIL import Image as PILImage
from xml.sax.saxutils import escape
R=Path(__file__).resolve().parents[1]
PDF=R/'paceval_Agent_Constraint_Verification_Whitepaper_EN.pdf'
for label,p in [('Noto','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('NotoBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(label,p))
navy=colors.HexColor('#17324d');teal=colors.HexColor('#087e8b');muted=colors.HexColor('#4f6373')
ST={
'h':ParagraphStyle('h',fontName='NotoBold',fontSize=18,leading=25,textColor=navy,spaceAfter=13),
's':ParagraphStyle('s',fontName='NotoBold',fontSize=11,leading=16,textColor=teal,spaceBefore=8,spaceAfter=6),
'b':ParagraphStyle('b',fontName='Noto',fontSize=9.05,leading=14.4,textColor=navy,spaceAfter=9),
'sm':ParagraphStyle('sm',fontName='Noto',fontSize=7.6,leading=11.6,textColor=muted,spaceAfter=6),
'cover':ParagraphStyle('cover',fontName='NotoBold',fontSize=24,leading=31,textColor=navy,spaceAfter=11),
'eq':ParagraphStyle('eq',fontName='Noto',fontSize=9.4,leading=16,textColor=navy,leftIndent=11,spaceAfter=7),
}
story=[]
def H(s):story.append(Paragraph(escape(s),ST['h']))
def S(s):story.append(Paragraph(escape(s),ST['s']))
def P(s):story.append(Paragraph(s,ST['b']))
def M(s):story.append(Paragraph(s,ST['sm']))
def E(s):story.append(Paragraph(escape(s),ST['eq']))
def fig(name,w=465,maxh=242,caption=''):
 path=R/'figures'/name
 with PILImage.open(path) as img: iw,ih=img.size
 h=min(w*ih/iw,maxh); width=h*iw/ih
 story.append(Image(str(path),width=width,height=h))
 if caption:M(caption)
def table(data,widths=[240,248]):
 rows=[[Paragraph(escape(str(c)),ST['sm']) for c in r] for r in data]
 tbl=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
 tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1f0f2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f8fa')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),1,teal),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 story.append(tbl)
def nextp():story.append(PageBreak())
def footer(canvas,doc):
 canvas.setStrokeColor(colors.HexColor('#aec5d0'));canvas.line(45,44,A4[0]-45,44)
 canvas.setFillColor(muted);canvas.setFont('Noto',7.2)
 canvas.drawString(45,31,'paceval | Automatic Verification of Agent-Generated Constraints | November 2026')
 canvas.drawRightString(A4[0]-45,31,str(doc.page))
# 1
M('PACEVAL | SCIENTIFIC WHITE PAPER | EXECUTED RESEARCH DEMONSTRATOR')
story.append(Paragraph('Automatic Verification of<br/>Agent-Generated Constraints',ST['cover']))
P('<b>Reusable nonlinear guard evaluation for controlled industrial decision workflows.</b>')
fig('00_constraint_verification_hero.png',485,305,'Cover artwork: conceptual manufacturing and computational verification illustration, not observed plant data.')
table([['Recorded experiment','Result'],['Versioned mathematical guard handles','1,001 (1,000 original + one immutable revision)'],['Adversarial guard-input decisions','100,000'],['Mathematical evaluation','Scalar + packed batch via original paceval SDK'],['Decision outcomes','ACCEPT / REJECT / REVIEW']])
M('The experiments use synthetic normalized manufacturing setpoints. No general formal correctness, deployed machine safety or live autonomous-agent behavior is claimed.')
nextp()
# 2
H('1. Industrial use case and current state of the art')
P('An industrial engineering assistant might propose a robot-workspace target, a machine setpoint or a thermal operating envelope. In an automated factory, these proposed numerical values require independent gating before any control action. A textual or model-generated claim of validity is not itself authorization, and the numerical formula is only one part of the engineering safety boundary.')
P('The illustrative use case is a hypothetical manufacturing cell. An upstream planner selects a constraint from a controlled, typed registry. A C++ application first rejects unauthorized actions, invalid units, nonfinite values and numbers outside the declared input range. The mathematical kernel then computes a signed guard margin from normalized setpoints. The host routes results to an explicit acceptance, rejection or human-review state.')
S('Present-day technical approaches')
P('Formal SMT/SAT-based tools can reason about logical conditions within particular theories, while numerical expression engines evaluate defined mathematical functions at selected arguments. These are distinct capabilities. SMT-LIB 2.7 formalizes satisfiability-modulo-theories reasoning, and the Z3 guidance documents limitations in nonlinear arithmetic. NIST AI risk guidance motivates risk-aware evaluation of AI-assisted workflows; MCP tool specifications provide a machine-readable contract and request interface, not a guarantee that an invoked mathematical decision is safe.')
M('References: SMT-LIB 2.7 (2025); Microsoft Z3 arithmetic guide; NIST AI 600-1 (2024); MCP tools specification (2026-07-28). Full links are provided on page 10.')
nextp()
# 3
H('2. Experimental question and system responsibilities')
P('Can a fixed allowlisted catalogue of 1,000 nontrivial mathematical inequalities be represented as persistent paceval computation graphs, repeatedly evaluated for boundary-focused proposed machine inputs, and safely connected to a three-way host routing mechanism that keeps authorization separate from arithmetic?')
fig('01_execution_architecture.png',469,200,'Figure 1. The actual implemented boundary from allowlisted guard definition to checked numeric execution and host-side routing.')
S('Interface ownership')
table([['paceval mathematical engine','C++ host / surrounding application'],['Create 1,001 persistent graph handles','Template registry, version control and action permissions'],['Evaluate scalar signed inequalities','Input typing, finite/range/unit validation'],['Execute packed independent input batches','Apply boundary-routing policy and manage audit records'],['Return numerical margins for decisions','C++ reference, scenario design and CSV export']])
P('The engine does not parse free-form LLM instructions, authorize a machine action or prove that a guard is valid for every possible input. The experiment also does not operate a live MCP server or physical robot.')
nextp()
# 4
H('3. Defined mathematical constraint models')
P('All quantities x, y and z are dimensionless normalized industrial setpoints admitted only on the defined finite range [-2,2]. Each admissible mathematical guard is represented by a signed margin g(x,y,z), with nonnegative values satisfying the underlying inequality.')
S('Five implemented guard families')
E('g1 = c - x                                      [upper threshold]')
E('g2 = c - (x/a)^2 - (y/b)^2                     [elliptical workspace]')
E('g3 = c - x^2 - k*y^2 - 0.1*z^2                [quadratic budget]')
E('g4 = c + a*x - b*y + k*z                       [affine envelope]')
E('g5 = c - exp(k*x) + a*cos(y) - b*z^2          [nonlinear envelope]')
P('Two hundred formula configurations are generated for each family, with explicitly frozen values of a, b, c and k in the released guard registry. A controlled second version of the first guard changes its threshold and produces an additional computation handle; the earlier handle remains accessible.')
S('Numerical decision policy')
E('ACCEPT if g > +1e-8; REJECT if g < -1e-8; REVIEW otherwise.')
P('This three-way routing is deliberate. A point extremely close to a guard boundary is not silently approved. The review band is a declared policy choice, not a mathematically certified error enclosure. All host-level schema checks precede the calculation.')
nextp()
# 5
H('4. Synthetic industrial evaluation workload')
P('The released registry contains exactly 1,000 original guard expressions and one independently created revision. A fixed xorshift-based generator produces 100 test arguments for each original guard, yielding 100,000 logged decisions. Half of the input positions are deliberately placed close to an analytically derived zero-margin surface; the remaining inputs explore a wider admitted region.')
fig('03_boundary_analysis.png',470,242,'Figure 3. Selected guard families are evaluated with explicit emphasis on the numerical switching region around the inequality boundary.')
P('The host separately tests four invalid-contract cases: mismatched units, unknown action, nonfinite numerical input, and out-of-range values. These are rejected by the host and are not presented as paceval mathematical proofs.')
M('A finite deterministic sample is appropriate for executable software evaluation, but not a proof over a continuous parameter domain.')
nextp()
# 6
H('5. Executed paceval computation and audit status')
table([['Recorded experimental quantity','Actual result'],['Original guard expressions','1,000'],['Persistently registered mathematical graphs','1,001'],['Adversarial pointwise constraint inputs','100,000'],['Scalar mathematical evaluations, including tests and surface','103,723'],['Packed batch checks','8,000'],['Independent 80-digit sample checks','632; completed successfully'],['Host schema/authorization rejection tests','4'],['CMake / CTest integration','1 / 1 passed']],[300,188])
P('The application uses the real paceval initialization, graph creation, scalar computation, packed batch evaluation, error checking and handle release routines. Exact mathematical expressions and test parameters are recorded in the project CSVs. An independent native C++ formula evaluator and a separately implemented 80-digit arithmetic check support the technical audit; details of numerical agreement reside in the machine-readable verification files, not in the industrial outcome discussion.')
P('This is evidence that a controlled mathematical kernel can compute the defined guard functions for the evaluated inputs. It is not a claim of formal satisfiability, universal numerical guarantees, equipment certification, or autonomous industrial authorization.')
nextp()
# 7
H('6. Industrial decisions and routing behavior')
fig('02_decision_distribution.png',466,225,'Figure 2. Actual application decisions across 100,000 synthetic guard-input pairs: 50,758 accept, 31,123 reject, and 18,119 boundary-review cases.')
fig('04_decision_routing_profile.png',466,225,'Figure 4. Routing outcomes across the fixed, boundary-focused input positions: explicit review behavior avoids treating near-threshold values as unconditional approvals.')
nextp()
# 8
H('7. Three-dimensional constraint geometry')
P('A 61 x 61 numerical grid is evaluated directly with paceval for a representative elliptical guard. The signed margin provides an interpretable view of a candidate two-dimensional operating region: positive and negative heights represent admissible and non-admissible sample positions under the selected mathematical model.')
fig('05_elliptical_guard_3d.png',467,248,'Figure 5. Three-dimensional mathematical margin surface from 3,721 genuinely evaluated paceval outputs.')
fig('06_elliptical_guard_contours.png',410,198,'Figure 6. Contour visualization from the same recorded numerical values, with a zero-margin ellipse.')
nextp()
# 9
H('8. Constraint families and engineering interpretation')
fig('07_family_decisions.png',460,220,'Figure 7. Decision class distribution grouped by the five mathematical model families.')
fig('08_review_pattern.png',460,202,'Figure 8. Fraction of boundary-review cases at each deterministic sample position.')
P('Different shapes give different admissible regions: affine half-spaces, elliptical work envelopes, quadratic resource limits and nonlinear response boundaries. For a manufacturing application, the selected envelope would need to be derived from the actual plant and independently validated before influencing equipment permissions.')
nextp()
# 10
H('9. Reproducibility, limitations and sources')
S('Rebuild the measured mathematical experiment')
E('cmake -S src -B build -DCMAKE_BUILD_TYPE=Release')
E('  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so')
E('cmake --build build -j')
E('ctest --test-dir build --output-on-failure')
E('./build/agent_constraints --out reproduced')
P('The repository contains the commented C++ application, the original paceval SDK C/C++ facade files, audit scripts, a frozen guard registry, 100,000 output decisions, a 3,721-point constraint surface and the scientific plots. The compatible shared paceval Linux runtime is supplied separately and is not redistributed.')
S('Scientific limits')
P('The guard expressions and samples are synthetic and dimensionless; they do not encode actual machine or robot safety limits. The program neither accepts free-form LLM code nor provides a theorem prover, SMT solver, certified interval arithmetic, a full network MCP implementation, or an industrial safety approval. The host review threshold is not a guaranteed error bound. Production use would additionally require real engineering specifications, typed schemas, authorization, physical interlocks, independent functional-safety validation and secure tool interfaces.')
S('Selected technical sources (verified November 2026)')
for title,url in [
('SMT-LIB 2.7 reference','https://smt-lib.org/papers/smt-lib-reference-v2.7-r2025-07-07.pdf'),
('Z3 guide: arithmetic theories','https://github.com/microsoft/z3guide/blob/main/website/docs-smtlib/02%20-%20theories/01%20-%20Arithmetic.md'),
('NIST Generative AI Profile','https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence'),
('MCP tools specification, 2026-07-28','https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx'),
('paceval API','https://paceval.com/api/')]:
 M(escape(title)+': '+escape(url))
S('Conclusion')
P('<b>Persistent paceval mathematical graphs successfully evaluated a large set of specified, generated inequalities inside a controlled industrial-style decision workflow.</b> The numerical results can support auditable routing decisions while authorization, hardware safety and formal universal verification remain separately defined responsibilities.')
doc=SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=48,bottomMargin=59,title='paceval | Automatic Verification of Agent-Generated Constraints',author='paceval scientific demonstrator')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(PDF)
