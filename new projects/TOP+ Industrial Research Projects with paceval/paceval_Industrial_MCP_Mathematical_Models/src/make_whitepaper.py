#!/usr/bin/env python3
"""Build the completed English whitepaper from recorded actual paceval calculations.
Pages are deliberately authored one at a time for precise figure placement.
"""
from pathlib import Path
import sys,json,html
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
filename=root/'paceval_Industrial_MCP_Mathematical_Models_Whitepaper_EN.pdf'
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DV-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
W,H=A4;LEFT=47;RIGHT=47;CW=W-LEFT-RIGHT
INK=HexColor('#162F49');TEAL=HexColor('#007E99');MUTED=HexColor('#63788A');LGRAY=HexColor('#E5EEF3')
c=canvas.Canvas(str(filename),pagesize=A4,pageCompression=1);c.setTitle('Industrial Mathematical Models via the paceval MCP Server');c.setAuthor('paceval | research demonstrator')
page=0;y=0

def footer():
 c.setStrokeColor(LGRAY);c.line(LEFT,49,W-RIGHT,49)
 c.setFont('DV',7.4);c.setFillColor(MUTED)
 c.drawString(LEFT,35,'paceval  |  Industrial Mathematical Models via MCP  |  2026')
 c.drawRightString(W-RIGHT,35,str(page))

def new_page(heading='',sub=''):
 global page,y
 if page:footer();c.showPage()
 page+=1;y=H-50
 if heading:
  c.setFont('DV-Bold',17);c.setFillColor(INK);c.drawString(LEFT,y,heading);y-=12
  c.setStrokeColor(TEAL);c.setLineWidth(1.8);c.line(LEFT,y-2,W-RIGHT,y-2);y-=25
 if sub:paragraph(sub,size=9.5,leading=14,space_after=12)

def paragraph(txt,size=9.4,leading=14.3,space_after=10,bold=False):
 global y
 style=ParagraphStyle('B' if bold else 'normal',fontName='DV-Bold' if bold else 'DV',fontSize=size,leading=leading,textColor=INK,spaceAfter=0)
 f=Paragraph(txt,style);_,h=f.wrap(CW,760);f.drawOn(c,LEFT,y-h);y-=h+space_after
 if y<57:raise RuntimeError(f'Page {page} content exceeded bottom at y={y}: {txt[:60]}')

def h2(text):
 global y
 y-=6;c.setFillColor(TEAL);c.setFont('DV-Bold',11.5);c.drawString(LEFT,y,text);y-=17

def bullet(text):paragraph('• '+text,size=9.0,leading=13.6,space_after=5)

def figure(name,caption,max_h=270,w=CW):
 global y
 p=root/'figures'/name;im=PILImage.open(p);iw,ih=im.size;scale=min(w/iw,max_h/ih);sw,sh=iw*scale,ih*scale
 c.drawImage(str(p),LEFT+(CW-sw)/2,y-sh,width=sw,height=sh,mask='auto',preserveAspectRatio=True)
 y-=sh+7
 paragraph('<i>'+caption+'</i>',size=8.0,leading=11.6,space_after=12)

def table(rows,widths=None,size=8.1):
 global y
 styles=[ParagraphStyle('hdr',fontName='DV-Bold',fontSize=size,leading=11,textColor=INK),ParagraphStyle('cell',fontName='DV',fontSize=size,leading=11.8,textColor=INK)]
 data=[[Paragraph(html.escape(str(x)),styles[0 if i==0 else 1]) for x in row]for i,row in enumerate(rows)]
 tbl=Table(data,colWidths=widths or [CW/len(rows[0])]*len(rows[0]),hAlign='LEFT',repeatRows=1)
 tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#E7F0F4')),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#FFFFFF'),HexColor('#F6F9FB')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.8,HexColor('#80AFC1')),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7)]))
 _,h=tbl.wrap(CW,y-60);tbl.drawOn(c,LEFT,y-h);y-=h+12
 if y<57:raise RuntimeError(f'Page {page} table exceeds bottom {y}')

new_page()
c.setFillColor(TEAL);c.setFont('DV-Bold',9.0);c.drawString(LEFT,y,'PACEVAL  |  SCIENTIFIC RESEARCH & VERIFIED INTEGRATION');y-=35
paragraph('Industrial Mathematical Models<br/>via the paceval MCP Server',size=25,leading=34,space_after=12,bold=True)
paragraph('Reusable mathematical execution graphs for precision manufacturing, AI agents and digital twins',size=11.4,leading=17,space_after=15)
figure('00_mcp_industrial_hero.png','Concept illustration; not a computed research result.',max_h=246)
h2('Research outcome')
paragraph('Actual mathematical computations were executed through the connected <b>paceval MCP server 4.26</b> and independently reproduced through the <b>original paceval C++ SDK 4.25</b>. Two versioned analytical models, modular graph batches, sensitivities, and quality functions were verified on deterministic synthetic manufacturing cases.',size=10.0,leading=15.5)
paragraph('13 November 2026  |  Functionality and feasibility report  |  No performance comparisons',size=8.6,leading=13)

new_page('1. Industrial use case and current state of the art')
paragraph('Precision machine tools and metrology systems respond to temperature, load and geometric position. Changes in their internal thermal state can create positioning errors across an operating volume. Engineering teams therefore record temperatures and geometric measurements, fit a correction model and evaluate that model repeatedly when machine conditions or calibration parameters change.')
paragraph('A practical supervisory application is the preparation of a machine-fleet quality report. An engineer selects a calibrated model version, submits measurement records containing machine coordinates and temperature, receives a predicted correction and evaluates defined quality margins. The calculation supports analysis and a proposed correction; it does not directly control actuators or certify a measuring instrument.')
h2('Relevant established and emerging methods')
paragraph('Iñigo and colleagues (2024) describe a combined volumetric geometric and thermal compensation approach. Lang and colleagues (2025) use digital-twin ensembles to identify useful thermal sensor locations. A 2025 review discusses robust thermal error reduction, and work published in 2026 examines mechanisms for updating digital-twin thermal models for machine-tool feed systems. These studies provide the industrial context for the present experiment, not performance evidence for paceval itself. [1–4]')
h2('Where paceval and MCP fit')
paragraph('A mathematical model is approved and serialized as an expression. A connected AI agent invokes the paceval MCP tool to create a graph once and retains the returned opaque handle. It then evaluates the graph with multiple new inputs and can pass numerical results into further versioned paceval functions. The client handles orchestration and the final supervisory policy.')
paragraph('The experiments use synthetic coordinates, temperatures and Gaussian model coefficients. No real production calibration or physical unit of correction is claimed.')

new_page('2. Research question and system architecture')
paragraph('<b>Research question.</b> Can a connected agent create and reuse full mathematical models through the paceval MCP protocol, maintain distinct formula versions, process independent records and evaluate downstream quality functions through genuine paceval graphs?')
figure('01_executed_architecture.png','Figure 1. Verified graph orchestration and supervisory decision flow; factory deployment remains a proposed future use.',max_h=170)
h2('Separation of responsibilities')
table([['Component','Responsibility'],['AI agent / MCP client','Select approved models, prepare call inputs, preserve handles and sequence tools.'],['paceval Mathematical Engine','Create persistent graphs; compute fields, sensitivity expressions and mathematical quality/guard scores.'],['Local C++ reference demonstrator','Reproduce the same formula family via the original SDK and manage data, batches, errors and policies.'],['Independent Python oracle','Recalculate mathematical outputs and audit the full field and decision path.']],[163,CW-163])
paragraph('Remote service tool calls and the local SDK replay are distinct verified experiments. The previously published 16,384-component test is cited only as historical research context.')

new_page('3. Defined mathematical models')
paragraph('Let (x,y,z) be normalized position coordinates in the unit cube, and let T be an illustrative operating temperature in degrees Celsius. The synthetic correction field contains 256 Gaussian radial-basis components, a linear thermal term and a geometric baseline:')
paragraph('<b>Correction.</b>  δᵥ(x,y,z,T) = b₀,ᵥ + bT,ᵥ(T−20) + bx,ᵥx + by,ᵥy + bz,ᵥz + Σₖ aₖ,ᵥ exp(−dₖ²/sₖ) [1 + cₖ(T−20)/20], where dₖ² = (x−μx,ₖ)²+(y−μy,ₖ)²+(z−μz,ₖ)² and k = 0,…,255.',size=9.0,leading=16)
paragraph('All synthetic coefficients are serialized to fixed decimal places and versioned with SHA-256 hashes. The two model versions differ in baseline and radial-basis amplitudes; the variable order remains fixed. The experimental coordinate domain is [0,1]³, and the checked temperature range is 0–50 °C.')
h2('Sensitivity functions executed in paceval')
paragraph('Analytical derivative graphs are generated for ∂δ/∂T and ∂δ/∂x. They contain the derivative of each Gaussian component and the corresponding baseline derivative. A high-precision independent implementation evaluates the same mathematical definitions without parsing the paceval expression text.')
h2('Downstream mathematical output')
paragraph('The second stage consumes the <b>two paceval-calculated model outputs</b>, synthetic target and tolerance, measurement value and temperature. It computes a revised correction, normalized quality score, residual, revision delta, quality margin, version margin, temperature guard and governance score. The policy then classifies each synthetic case as ACCEPT, REVIEW or REJECT from these graph results.')
paragraph('Quality criteria in this report are research-only thresholds. They are not calibration acceptance criteria for a physical machine and are not metrological uncertainty budgets.')

new_page('4. Actual remote MCP execution, version 4.26')
paragraph('Two independently maintained 256-component correction models were submitted to <b>paceval_create_computation</b>. Both registrations returned success and opaque handles, and <b>paceval_evaluate_multiple_many</b> produced 32 model outputs for 16 common input vectors in graph-major layout. The agent reused the same graph references without resending the formulas for the numerical batch.')
figure('10_actual_remote_mcp_results.png','Figure 2. Actual connected paceval MCP 4.26 results: two different synthetic formula versions on a common 4 × 4 input grid.',max_h=285)
h2('Modular representation and composed scores')
paragraph('The updated model was independently registered as eight 32-component graphs and evaluated through one multiple-graph batch on four records, producing 32 module outputs. The per-record sums matched the direct graph values. Eight separate downstream graphs were also created and executed on 16 records, producing <b>128 mathematical score and margin outputs</b> without reported MCP errors.')
paragraph('These results were obtained by genuine connected MCP tool calls, not a local emulation. Raw observation summaries and exact formula texts are included under results/ and generated/.')

new_page('5. Original local paceval SDK research demonstrator')
paragraph('For standalone reproduction, the C++ program uses the original paceval_main.h and paceval_main.cpp files from SDK 4.25, with an externally supplied ABI-compatible Linux shared library. The only SDK source adjustment is the relative header include path. No replacement mathematical engine is introduced.')
table([['Executed mathematical component','Number of graphs'],['Two versioned correction fields','2'],['Temperature and X-position sensitivity graphs','4'],['Eight modular pieces of the updated model','8'],['Composite score, output, and constraint/quality margin functions','8'],['Total persistent graphs','22']],[CW*.77,CW*.23])
paragraph('The source processes <b>520 deterministic synthetic records</b>, with 22 graph outputs per record and <b>11,440 actual graph outputs</b> across 27 graph-major batch calls. Main graph outputs are transported to a second layer of graph computations, preserving the separation between mathematical evaluation and C++ orchestration.')
h2('Independent numerical audit')
paragraph('The independent oracle verified <b>3,120 core mathematical values</b>, <b>4,680 composite quantities and decisions</b>, and <b>144 results using 80-decimal-place arithmetic</b>. The precision details remain in the technical audit; this publication reports the successful correctness outcome without performance or C++-versus-paceval accuracy comparison tables.')
paragraph('The local C++ runtime demonstrates the mathematical model independently of a live network connection. Remote MCP usage, including server-authentication details, must be tested separately by each new MCP client.')

new_page('6. Versioned industrial correction surface')
figure('02_correction_surface_3d.png','Figure 3. Three-dimensional synthetic machine correction surface at 25 °C, based on executed local paceval SDK outputs.',max_h=430)
paragraph('The surface illustrates how the same mathematical model can be evaluated repeatedly for different machine positions. Input coordinates are normalized and plotted against a synthetic correction quantity. The surface is not a measured deformation field, and no physical compensation accuracy can be inferred from its shape.')

new_page('7. Model changes and spatial response')
figure('03_corrected_field.png','Figure 4. Evaluated version-2 correction field over a fixed-position plane.',max_h=250)
figure('04_model_revision.png','Figure 5. Difference between the two independently preserved mathematical correction versions.',max_h=250)

new_page('8. Explicit mathematical sensitivities')
figure('05_temperature_sensitivity.png','Figure 6. Temperature derivative calculated through a persistent paceval graph.',max_h=245)
figure('06_position_sensitivity.png','Figure 7. Analytical X-direction derivative calculated through a persistent paceval graph.',max_h=245)

new_page('9. Mathematical quality gates and decisions')
figure('07_quality_decision_regions.png','Figure 8. Illustrative quality categories derived by the host from genuine paceval margin values.',max_h=250)
figure('08_temperature_decisions.png','Figure 9. Counts of synthetic classifications across four temperature scenarios.',max_h=220)

new_page('10. Model governance and temperature profiles')
figure('09_governance_cross_section.png','Figure 10. Composite governance score over a machine position cross-section, computed through paceval.',max_h=230)
figure('11_temperature_version_profiles.png','Figure 11. Original two-version paceval correction results as a function of temperature.',max_h=235)

new_page('11. Interpretation, service governance and scope')
h2('Newly verified technical capabilities')
bullet('Actual remote MCP graph creation, handle reuse, versioned multi-graph batches and a second mathematical processing stage.')
bullet('A reproducible local graph execution program using the original paceval C++ SDK and external runtime.')
bullet('Distinct versioned formula objects, independently tested mathematical derivatives and controlled quality/constraint scores.')
bullet('Validated graph-major result ordering, an execution inventory, archived remote observations and versioned input/formula manifests.')
h2('Industrial interpretation')
paragraph('The strongest practical architectural demonstration is the ability to separate client/agent orchestration and industrial workflow control from the mathematical expression engine. A change in a mathematical model is a deliberate new version, and the same approved version can be evaluated repeatedly for different machine configurations or data records.')
paragraph('A production system would still require measurement traceability, engineering approval, versioned physical calibration data, access controls, service authentication, backup, expiry and renewal of remote handles, recovery after service interruptions and compliance with applicable plant control requirements.')
h2('Scientific limitations')
paragraph('All coefficient fields and input records are synthetic. This report does not establish measured machine accuracy, uncertainty calibration, production-grade service reliability, cybersecurity approval, hard-real-time suitability, clinical validity or a certified interval guarantee. TINC was not used. The predecessor report documented a 16,384-component graph; that historical result was not re-executed here. This publication intentionally excludes performance comparisons.')

new_page('12. Reproduction and references')
h2('Build and verification')
paragraph('1. Supply the original compatible Linux shared library externally. The shared library is not included in the GitHub ZIP. The C++ program uses the unmodified original public API and the original SDK sources with a minimal relative-include adjustment.')
paragraph('2. Build from the package root using CMake: <font face="DV-Bold">cmake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so</font>, then <font face="DV-Bold">cmake --build build</font>, run <font face="DV-Bold">./build/industrial_mcp_paceval .</font> and <font face="DV-Bold">ctest --test-dir build --output-on-failure</font>.')
paragraph('3. Regenerate and independently audit results using the Python scripts included in src/. To repeat live MCP experiments, establish a fresh authorized connection to https://mcp.paceval-service.com/mcp and create new opaque handles. See docs/REPRODUCIBILITY.md.')
h2('Selected sources')
for t in [
 '[1] Iñigo et al. Digital Twin for Volumetric Thermal Error Compensation of Large Machine Tools. Sensors (2024). DOI: 10.3390/s24196196.',
 '[2] Lang et al. Sensor placement utilizing a digital twin for thermal error compensation of machine tools. Journal of Manufacturing Systems 80 (2025). DOI: 10.1016/j.jmsy.2025.03.003.',
 '[3] A review of robust thermal error reduction of machine tools. International Journal of Machine Tools and Manufacture 209 (2025). DOI: 10.1016/j.ijmachtools.2025.104298.',
 '[4] Yang et al. Digital Twin-Enabled thermal error prediction and compensation system for CNC Machine tool feed systems. MSSP 250 (2026). DOI: 10.1016/j.ymssp.2026.114192.',
 '[5] paceval. Now available as an MCP Server for AI Agents and LLMs. August 2026. https://paceval.com/news/',
 '[6] paceval public repository, interface and Streamable HTTP specification. https://github.com/paceval/paceval',
 '[7] MCP tools specification. https://modelcontextprotocol.io/specification/2025-11-25/server/tools',
 '[8] OpenAI Help Center. Connecting custom MCP servers in ChatGPT.']:
 paragraph(html.escape(t),size=8.15,leading=11.9,space_after=7)
paragraph('Research status: executed remote and local paceval mathematical functionality; synthetic models; numerical verification successful; no production deployment.',size=8.5,leading=13)

footer();c.showPage();c.save()
print('PDF created',filename,'pages',page,'size',filename.stat().st_size)
