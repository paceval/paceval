#!/usr/bin/env python3
"""Build a standalone 15-page English scientific research paper (ReportLab)."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Image,Spacer,PageBreak,Table,TableStyle,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import math
R=Path(__file__).resolve().parents[1]
OUT=R/'paceval_Machine_Tool_Chatter_Whitepaper_EN.pdf'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',font));pdfmetrics.registerFont(TTFont('DVB',bold));pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DV',boldItalic='DVB')
NAVY=colors.HexColor('#18304D');INK=colors.HexColor('#26364C');TEAL=colors.HexColor('#087F8C');RUST=colors.HexColor('#DA754A');SLATE=colors.HexColor('#637083')
ST={
 'title':ParagraphStyle('TitlePaper',fontName='DVB',fontSize=23,leading=31,textColor=NAVY,spaceAfter=18),
 'subtitle':ParagraphStyle('SubtitlePaper',fontName='DV',fontSize=13,leading=20,textColor=TEAL,spaceAfter=18),
 'head':ParagraphStyle('PageTitle',fontName='DVB',fontSize=16,leading=22,textColor=NAVY,spaceAfter=14),
 'sub':ParagraphStyle('SectionSubtitle',fontName='DVB',fontSize=11.2,leading=16,textColor=NAVY,spaceBefore=13,spaceAfter=6),
 'body':ParagraphStyle('ResearchBody',fontName='DV',fontSize=9.2,leading=15,textColor=INK,spaceAfter=9),
 'small':ParagraphStyle('SmallText',fontName='DV',fontSize=8.15,leading=13.1,textColor=INK,spaceAfter=7),
 'cap':ParagraphStyle('CaptionText',fontName='DV',fontSize=7.6,leading=11.8,textColor=SLATE,spaceAfter=12),
 'eq':ParagraphStyle('Equation',fontName='DV',fontSize=10.9,leading=19,textColor=NAVY,alignment=TA_CENTER,spaceBefore=8,spaceAfter=12),
 'label':ParagraphStyle('TinyLabel',fontName='DVB',fontSize=8,leading=12,textColor=TEAL,spaceAfter=8),
 'refs':ParagraphStyle('References',fontName='DV',fontSize=7.6,leading=11.4,textColor=INK,spaceAfter=10),
}
doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=47,rightMargin=47,topMargin=55,bottomMargin=47,title='Programmable Regenerative Chatter Candidate Maps with paceval',author='paceval Research Demonstrator',subject='Synthetic reusable mathematical execution graphs and regenerative chatter candidate boundaries')
W=A4[0]-94
story=[]
def P(t,style='body'):story.append(Paragraph(t,ST[style]))
def T(t):P(t,'head')
def S(t):P(t,'sub')
def PB():story.append(PageBreak())
def spacer(h=7):story.append(Spacer(1,h))
def image(name,width=W,height=None,caption=None):
 path=R/'figures'/name
 from PIL import Image as PIL
 pw,ph=PIL.open(path).size
 if height is None:height=width*ph/pw
 story.append(Image(str(path),width,height))
 if caption:P(caption,'cap')
def tbl(data,widths=None):
 p=[]
 for row in data:
  p.append([Paragraph(str(a),ST['small']) for a in row])
 t=Table(p,colWidths=widths or [W/len(data[0])]*len(data[0]),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E6F2F3')),('TEXTCOLOR',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.8,TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F6F8FA')])]))
 story.append(t);spacer(10)
def page(c,title):
 T(f'{c}. {title}')

def header(canvas,document):
 canvas.saveState();n=document.page
 if n>1:
  canvas.setFillColor(NAVY);canvas.setFont('DVB',8.2);canvas.drawString(47,A4[1]-30,'PACEVAL.  |  INDUSTRIAL MATHEMATICAL RESEARCH')
  canvas.setStrokeColor(colors.HexColor('#DDE6EA'));canvas.line(47,A4[1]-36,A4[0]-47,A4[1]-36)
 canvas.setStrokeColor(colors.HexColor('#DDE6EA'));canvas.line(47,36,A4[0]-47,36)
 canvas.setFont('DV',7.2);canvas.setFillColor(SLATE);canvas.drawString(47,24,'WP 22   •   Synthetic regenerative chatter candidate-boundary research   •   15 November 2026')
 canvas.drawRightString(A4[0]-47,24,f'{n}')
 canvas.restoreState()

# 1 Cover
P('PACEVAL. / RESEARCH SERIES 22','label')
P('Programmable Regenerative Chatter Candidate Maps with paceval','title')
P('A verified mathematical demonstration for machine-tool frequency response, phase and cutting-depth margins','subtitle')
image('00_chatter_stability_cover.png',width=W,height=W/2)
P('SCIENTIFIC RESEARCH DEMONSTRATOR   |   ENGLISH EDITION   |   15 NOVEMBER 2026','label')
P('<b>Abstract.</b> Regenerative chatter can arise when a milling cutter repeatedly intersects a wavy surface created during preceding tooth contacts. This study asks whether reusable paceval mathematical graphs can evaluate single- and two-mode structural receptances, candidate depth limits, phase-consistent spindle speeds, signed machining margins and a scalar regenerative characteristic residual. Twenty-three graph formulas were actually executed using paceval MCP 4.26 on 64 synthetic frequency–lobe cases. Selected outputs passed an independent 90-decimal-digit complex-reference audit. The results illustrate a version-sensitive mathematical screening layer, not a machine-certified stability map.','small')
P('Evidence distinction: real remote MCP calculations; original local SDK C++ source syntax-checked but not runtime-executed; synthetic dynamics without measured tool-point FRFs.','small')
PB()
# 2
page('1','Industrial context: what the engineer is trying to decide')
P('A cutting tool does not behave like a perfectly rigid body. Its spindle, holder, cutter and workpiece have resonant vibration modes that react to cutting forces. During milling, each tooth may encounter the surface left by a previous tooth. A vibrating cut therefore changes the thickness of subsequent chips, creating a delayed feedback loop. The resulting self-excited vibration can harm surface finish, tool life and part quality.')
P('Industrial planning frequently compares spindle speed and axial depth of cut using a <b>stability lobe diagram</b> (SLD). Its quality depends on experimentally identified frequency response functions (FRFs), directional cutting-force coefficients, engagement geometry and the operating state of the machine. A meaningful workflow therefore begins with impact testing or a validated dynamic model, includes the intended cutter and immersion, constructs mathematically consistent candidate boundaries and checks results experimentally or in a higher-fidelity solver.')
S('Hypothetical use case')
P('A machining team has a baseline modal model and later identifies an additional flexible mode. Rather than overwrite the original model, it wishes to retain both versions and automatically compute their complex receptance, critical axial depth candidate, lobe-associated spindle speed and cutting-depth margin for a selected cut. A difference in those mathematical predictions triggers additional engineering review, not an automatic machine command.')
S('Mathematical execution responsibilities')
P('paceval evaluates the reusable scalar and composite expressions, including intermediate frequency-response components and final depth and phase calculations. The C++ host owns input validity checks, model registration, case enumeration, handle management, result serialization and candidate presentation. An independent C++ and high-precision Python path checks mathematics without replacing the engine results.')
P('This division is the subject of the experiment. Whether the resulting mathematical kernel improves manufacturing throughput, numerical robustness in real machines or economic outcomes is outside the reported evidence.')
PB()
# 3
page('2','Scientific and industrial state of the art')
P('The foundational literature distinguishes steady cutting from regenerative feedback and recognizes that tool-tip receptance, engagement and tooth-passing phase jointly affect predicted stability. NIST demonstrated tool-length-dependent stability surfaces based on tool/spindle receptance coupling (2004). ORNL presented a comprehensive overview of chatter mechanisms, frequency- and time-domain laws, multi-tooth periodicity and process damping (2020). These approaches give the physical context but are not implemented in full by the present scalar project. [1, 2]')
P('More recent research expands fidelity. A Scientific Reports paper from 2024 developed Newton–Simpson predictor–corrector methods for semi-discretized milling models and Floquet stability computation. Work published in 2025 examined interval-uncertain machine-tool chatter and online stability-lobe identification from operating signals. These methods go beyond a single reduced static FRF formula. [3–5]')
P('In 2026, published studies investigated robustness-aware lobe maps and physics-driven digital twins that adapt candidate machining parameters in response to real-time data. Robust or adaptive claims from those papers must not be transferred to this demonstrator. This study has neither measured FRFs nor online parameter identification, and it does not calculate complete Floquet multipliers or conservative small-gain stability bounds. [6, 7]')
S('Why a programmable mathematical layer may help')
P('The same fundamental algebra occurs repeatedly: complex receptance evaluation, modal variant comparisons, analytic phase branches, cut-depth margins, sensitivities and constraints. A persistent expression-graph engine can give these quantities explicit versions, variable contracts and a reusable evaluated path. The existence of those functions is experimentally testable even without making broader assertions about full machining software.')
S('Unresolved practical needs')
P('Specialist process planning still requires directional milling coefficients, time-varying cutting engagement, non-proportional damping, model uncertainty, tool-position changes and a verified physical/temporal stability solver. The reduced scalar model is useful for transparent mathematical studies and model-revision checking, not machine signoff.')
PB()
# 4
page('3','Research question, assumptions and acceptance criteria')
S('Scientific question')
P('Can one reproducible graph inventory simultaneously evaluate two distinct oriented FRF models and their linked candidate-boundary formulas across many independent synthetic cases, while retaining exact formula IDs, declared input domains and independent numerical auditability?')
S('Explicit assumptions')
P('The frequency response is constructed from viscously damped, positive-mass, positive-stiffness single-degree-of-freedom modes. Model v2 adds a weighted second modal compliance. The cutting coefficient is a constant positive effective scalar parameter, directional coefficients are condensed into it, and four equal-spaced teeth are assumed. The characteristic equation is the deliberately reduced scalar regenerative expression selected for this study; periodic immersion and multi-directional force matrices are absent.')
S('Predeclared checks')
tbl([['Acceptance item','Independent / observable criterion'],['Graph execution','Each of 23 declared formulas is registered and evaluated in the 64-case remote MCP main path.'],['Numerical correctness','Selected printed outputs agree with a separately coded 90-digit complex reference to documented transcription tolerance.'],['Phase and feedback consistency','The complex characteristic residual at constructed phase-consistent boundary points approaches zero.'],['Domain and logic','Strict negative-real compliance check; exact Boolean local cut-depth comparisons; invalid or near-singular inputs rejected by host.'],['Precision','Only printed TINC point-output bounds are tested for inclusion of exact-binary-input references.'],['Reproducibility','Versioned formulas, synthetic input CSV, observed output subsets, verification scripts, source and metadata.']],[145,W-145])
P('The design does not predeclare successful measured cutting trials, a complete time-delay solver, uncertainty certification, energy reduction or hardware advantage.')
PB()
# 5
page('4','Frequency-response models and critical depth')
P('For a damped mass–spring mode, the complex receptance (displacement per unit force, m/N) at angular frequency ω is:')
P('G₁(jω) = 1 / (k₁ − m₁ ω<super>2</super> + j c₁ ω).','eq')
P('Its real and imaginary parts are computed with separate paceval graphs using a common positive denominator:')
P('D₁ = (k₁ − m₁ ω<super>2</super>)<super>2</super> + (c₁ ω)<super>2</super>.','eq')
P('Re(G₁) = (k₁ − m₁ ω<super>2</super>) / D₁;    Im(G₁) = −c₁ ω / D₁.','eq')
P('Model v2 adds the weighted complex second-mode receptance G₂(jω) = G₁(jω) + α/[k₂ − m₂ω² + jc₂ω]. This changes the total oriented receptance without replacing any v1 graph. Both versions remain simultaneously available in the same calculation inventory.')
P('Within the explicit negative-real domain, the selected scalar regenerative critical-depth candidate is:')
P('b<sub>crit</sub>(ω) = −1 / [2 K<sub>s</sub> Re(G(jω))].','eq')
P('The coefficient K<sub>s</sub> has units of N/m² and is an illustrative effective, orientation-adjusted cutting coefficient. Thus b<sub>crit</sub> is measured in meters. This mathematical result is defined only for Re(G) below zero and cannot be extended continuously through Re(G)=0 using the reciprocal formula. At zero damping and the exact resonance the compliance denominator may also become singular.')
S('Model-version sensitivity')
P('The two-mode version also evaluates an independently verified analytic sensitivity ∂b<sub>crit,2</sub>/∂K<sub>s</sub> = −b<sub>crit,2</sub>/K<sub>s</sub>. The experiment does not claim native automatic differentiation or a physical derivative valid across arbitrary modal parameter changes.')
PB()
# 6
page('5','Regenerative phase and stability-lobe candidate branches')
P('For this particular scalar characteristic equation, the delayed cutting feedback is represented by:')
P('D(ω,b,τ) = 1 + K<sub>s</sub> b G(jω) [1 − exp(−jωτ)].','eq')
P('If Re(G) and Im(G) are both negative, the branch selected here is θ = π + 2 atan(Im(G)/Re(G)). The tooth-to-tooth period is τ = 60/(Z N), with Z teeth and N spindle revolutions per minute. Combining the phase branch with θ + 2πℓ for ℓ = 0,1,2,… gives the candidate speed:')
P('N<sub>ℓ</sub> = 60ω / {Z[θ + 2πℓ]} rev/min.','eq')
P('paceval explicitly evaluates the phase, spindle-speed coordinate, depth margin b<sub>crit</sub> − b<sub>cut</sub>, Boolean depth comparator and model-update delta. A separate complex-residual test checks D≈0 at the constructed boundary points. Its success validates the algebraic phase construction, not dynamical stability against all relevant modes.')
S('Why this is not a complete milling stability lobe diagram')
P('Classical milling can have periodically varying directional cutting coefficients, multiple teeth interacting at different immersion angles, and several coupled machine directions. Those systems require a corresponding characteristic matrix or Floquet/semi-discretization analysis, with alternative roots and possible stability pockets. The present work plots only <b>parameterized candidate branches</b> of a single scalar feedback law. The plotted points must not be interpreted as a global stability envelope between samples.')
P('This distinction is retained in every plotted caption, README entry and output field. The Boolean guard answers only whether a selected depth lies below a local candidate critical-depth value at the sampled frequency; it does not authorize physical cutting.')
PB()
# 7
page('6','Actual execution ownership and model inventory')
P('The actual main experiment used 23 reusable paceval computation handles created by the remote MCP 4.26 service. Each expression was then evaluated for 64 input vectors. The host assembled the inputs and recorded selected returned decimal results; the mathematical end values were not replaced by Python or C++ reference calculations.')
tbl([['Mathematical function / industrial purpose','Actual implementation','Graph / version'],['FRF real, imaginary, compliance magnitude','paceval remote','6 graphs, v1/v2'],['Critical axial-depth candidate','paceval remote','2 graphs, v1/v2'],['Regenerative phase and boundary spindle RPM','paceval remote','4 graphs, v1/v2'],['Depth margins and logical depth screening','paceval remote','4 graphs, v1/v2'],['Model difference, relative margin and coefficient sensitivity','paceval remote','3 additional graphs'],['Complex characteristic residual','paceval remote','2 v2 graphs'],['Reference natural frequency and damping ratio','paceval remote','2 support graphs'],['CSV validation, graph lifetime, input case enumeration','C++ source, not locally run','Host orchestration'],['Independent numerical confirmation','Python and C++ reference','Validation only']],[212,119,W-331])
P('Machine-readable evidence is in the formula manifest, graph inventory and execution evidence JSON. The local C++ source contains original SDK function calls for numerical string conversion, scalar evaluation, single-graph batch control, multi-graph batch evaluation and handle deletion. The C++ source and original SDK bridge passed a C++17 syntax-only compile; no original local binary shared library was available for a link or runtime test.')
PB()
# 8
page('7','Deterministic experimental design')
P('The synthetic material comprises 16 angular frequencies from 3900 to 6900 rad/s in steps of 200 rad/s, crossed with four lobe orders (0 to 3), yielding 64 distinct input rows. The selected axial depth is 6.5 mm. The structural and cutting parameters are fixed in both main versions. The force coefficient is an assumed constant rather than a fitted calibration.')
tbl([['Input','Synthetic value / unit'],['Primary mode','m₁ = 1 kg, k₁ = 14 MN/m, c₁ = 1200 Ns/m'],['Secondary mode','m₂ = 1 kg, k₂ = 42 MN/m, c₂ = 1800 Ns/m'],['Mode weight','α = 0.30 (dimensionless)'],['Effective cutting coefficient','K<sub>s</sub> = 1 GN/m²'],['Candidate cutting depth','b<sub>cut</sub> = 6.5 mm'],['Cutter and branch order','Z = 4; ℓ = 0, 1, 2, 3'],['Primary sample domain','ω = 3900…6900 rad/s; both Re(G) negative']],[180,W-180])
P('Each independent input vector is fully specified by the CSV file in the examples directory. A dedicated domain validator rejects nonfinite inputs, invalid physical coefficients, invalid integer fields and responses outside the negative-real compliance branch. The output data are synthetic mathematical demonstrations, not plant signals, spindle measurements or observed chatter thresholds.')
P('For scientific transparency, the selected archival CSV is identified as a <b>decimal transcription</b> of real remote MCP values. It is not the original binary JSON payload or a byte-perfect complete raw-response archive. The exact declared formulas and input generation rules allow independent reproduction when an appropriate local runtime is provided.')
PB()
# 9
page('8','Observed frequency-response behavior')
P('The two modal response models yield different negative real compliances, particularly as the chosen angular frequency approaches the region influenced by the second mode. The first model is unchanged while the second adds a weighted structural pole. These curves reflect the synthetic modal coefficients and are not identified from an actual tool-point impact test.')
image('01_modal_receptance_actual_mcp.png',W,250,'Figure 1. Real and imaginary oriented receptance values from the actual paceval MCP main batch. Dashed curves indicate imaginary components; this is not a measured modal FRF.')
P('The first-mode natural frequency from the chosen mass and stiffness is approximately 595.7 Hz. The second modal contribution influences the phase and magnitude, which then affects the subsequent depth and speed calculations. The reference frequency graph and damping ratio are executed as explicit paceval expressions.')
PB()
# 10
page('9','Depth-limit candidates and signed cutting margins')
image('02_critical_depth_actual_mcp.png',W,225,'Figure 2. Actual paceval critical-depth candidate curves, with the single synthetic 6.5 mm comparison depth.')
image('04_cutting_depth_margins_actual_mcp.png',W,225,'Figure 3. Signed margins at the sampled frequencies, not global stable/unstable classifications.')
P('The observed branch comparison changes sign between model versions at selected frequencies. At ω = 4100 rad/s the v1 candidate depth is 5.712 mm and v2 is 6.530 mm, straddling the selected depth. At ω = 4300 rad/s both model values lie below the selected depth. These are model-specific algebraic results, not cutting trials.')
PB()
# 11
page('10','Phase-consistent candidate lobe branches')
image('03_regenerative_lobe_branches_actual_mcp.png',W,310,'Figure 4. Candidate lobe coordinates generated by the actual paceval phase and spindle-RPM graphs. Segments interpolate sampled mathematical points visually; they are not a certified milling stability envelope.')
P('For each sampled frequency, four different phase aliases are assigned to the corresponding lobe indices. The depth candidate is independent of lobe order, whereas the spindle-speed coordinate changes with the additional full 2π phase periods. This is why reusing the same critical-depth graph across multiple lobe orders is mathematically legitimate, while the RPM must be evaluated with the correct branch index.')
P('The phase formulation is restricted to the sign domain described on the previous pages. Phase branch switching near zero real response requires a different numerical treatment; the present host refuses such invalid cases rather than silently producing very large depths or arbitrary RPMs.')
PB()
# 12
page('11','Model-version differences and the 3D geometry')
image('05_model_version_depth_difference_actual_mcp.png',W,210,'Figure 5. Actual two-mode minus single-mode critical-depth candidate. A positive difference is not a general increase in physical stability.')
image('06_boundary_branches_3d_actual_mcp.png',W,290,'Figure 6. Three-dimensional presentation of parameterized candidate branch points from the recorded MCP outputs, not a reconstructed machine-specific operating envelope.')
PB()
# 13
page('12','Independent verification and TINC point outputs')
P('A separately implemented 90-decimal-digit reference reconstructs complex receptance from the exact binary64 input values, rather than interpreting paceval formula strings. Selected output columns including modal real/imaginary values, the critical-depth variants, phases, all lobe RPMs, signed comparisons and the complex characteristic residual passed <b>400 recorded independent checks</b>. This is a numerical audit of the declared mathematics, not physical process validation.')
P('The second model also underwent interval-mode tests on six well-conditioned frequency inputs, for both the critical depth and signed depth margin. All 12 printed remote interval bounds were found to include the independent mathematical point reference computed from the exact binary floating-point inputs.')
image('07_tinc_point_bounds_actual_mcp.png',W,210,'Figure 7. Widths of selected actually returned paceval TINC point-output bounds. These do not represent mechanical parameter uncertainty.')
P('The observed complex characteristic residual components at the constructed boundary points are close to zero. A further seven-graph operator selftest covered 21 remote graph-point results. The local C++ version contains its own operator and string-conversion tests, but those tests are not marked as executed because the original Linux runtime library is unavailable.')
PB()
# 14
page('13','Interpretation, applicability and next investigation')
S('What this study demonstrates')
P('The tested mathematical function chain is real: persistent paceval graphs simultaneously evaluate versioned modal FRFs, candidate critical depth, phase branches, spindle speed, mathematical constraints, a model-change quantity and analytic sensitivities. Independent complex arithmetic verifies the recorded results. The explicit formula inventory and CSV contracts support reproducible further experiments.')
S('What this study does not demonstrate')
P('No tool-tip FRFs, cutting coefficients or chatter labels were measured. No real cutting operation or field deployment was performed. The single-equation regenerative feedback does not substitute for full periodically varying milling forces, multi-axis structural dynamics, time-delay root enumeration, time-domain simulation or Floquet stability analysis. A depth comparison at a sampled candidate frequency cannot prove that an arbitrary speed/depth operating point is stable.')
S('Suggested research extension')
P('The next study should obtain consented machine-specific impact-test FRFs and cutting coefficients, compare single- and multi-modal physical identification, implement a validated semi-discretization or multi-frequency solution, and evaluate candidate-versus-observed lobe boundaries on held-out machining trials. Interval input uncertainties and boundary sensitivity could then be quantified with a method capable of bounding entire specified uncertain input domains. This would be a distinct validation level beyond the present pointwise TINC output check.')
S('Local original SDK status')
P('The original paceval SDK C++ interface files are preserved with their notices. The source code compiles with g++ in syntax-only C++17 mode, but no compatible external Linux shared library was present. Accordingly, the document does not claim successful SDK linking, local execution, CTest passes, end-to-end local CSV reproduction or any hardware performance advantage.')
PB()
# 15
page('14','References, provenance and reproducibility')
references=[
'[1] Schmitz et al. Tool Length-Dependent Stability Surfaces. NIST (2004). https://www.nist.gov/publications/tool-length-dependent-stability-surfaces',
'[2] Schmitz. Chatter Stability of Machining Operations. Journal of Manufacturing Science and Engineering (2020). https://www.ornl.gov/publication/chatter-stability-machining-operations',
'[3] Newton–Simpson-based predictor–corrector methods for milling chatter stability prediction. Scientific Reports (2024). https://www.nature.com/articles/s41598-024-84329-9',
'[4] Tang et al. A non-intrusive interval analysis method for chatter stability of uncertain milling systems. Journal of Manufacturing Processes (2025). DOI: 10.1016/j.jmapro.2025.04.047',
'[5] Wang et al. Online building of milling stability lobe diagrams based on multi-feature signals. Journal of Manufacturing Processes (2025). DOI: 10.1016/j.jmapro.2025.08.024',
'[6] Kadovitz &amp; Brand. Robustness-augmented stability lobe diagrams for improved process planning in turning and milling. IJAMT (2026). https://link.springer.com/article/10.1007/s00170-026-18349-2',
'[7] Huang, Yi &amp; Guo. Physics-driven real-time, intelligent digital twin for adaptive milling chatter control. CIRP Annals (2026). DOI: 10.1016/j.cirp.2026.04.032',
'[8] paceval Mathematical Engine official API and product brief: https://paceval.com/api/ ; https://paceval.com/product-brief/'
]
for x in references:P(x,'refs')
S('Evidence and code artifacts')
P('The complete release includes original SDK interface source, a CMake project, the original two-page WP22 proposal, a reproducible 64-row input CSV, exact graph expressions and observed remote handles, a selected real-MCP decimal output CSV, pointwise TINC bounds, remote operator selftests, independent numerical and Markdown audits, and reproducible figures. The numerical output from an unexecuted local binary is intentionally absent.')
P('Research figures are derived from observed paceval MCP outputs. The cover artwork is a conceptual visualization, not a photograph or measured stability map. Full bibliographic context and computational limitations are stated in the README and accompanying research design. All research values are synthetic.')
P('Software/research status: original paceval MCP 4.26 execution verified; local C++ source syntax verified; local paceval runtime linkage, CTest, machining measurements and physical model validation not performed.','small')

doc.build(story,onFirstPage=header,onLaterPages=header)
print('PDF created:',OUT)
