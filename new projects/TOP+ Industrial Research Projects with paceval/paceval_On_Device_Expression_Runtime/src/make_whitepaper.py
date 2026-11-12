#!/usr/bin/env python3
"""Rebuild the English research whitepaper from included figures and audit data."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

root=Path(__file__).resolve().parents[1]
fig=root/'figures'; ex=root/'examples'
summary=json.loads((ex/'validation.json').read_text())
output=root/'paceval_On_Device_Expression_Runtime_Whitepaper_EN.pdf'
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
navy=colors.HexColor('#173b55'); teal=colors.HexColor('#008d9c'); muted=colors.HexColor('#5b6d7c'); light=colors.HexColor('#eaf3f7')
styles={
 'title':ParagraphStyle('Title',fontName='DejaVuBold',fontSize=23,leading=29,textColor=navy,spaceAfter=11),
 'h1':ParagraphStyle('H1',fontName='DejaVuBold',fontSize=16,leading=21,textColor=navy,spaceBefore=7,spaceAfter=11),
 'h2':ParagraphStyle('H2',fontName='DejaVuBold',fontSize=11,leading=15,textColor=teal,spaceBefore=10,spaceAfter=5),
 'body':ParagraphStyle('Body',fontName='DejaVu',fontSize=9.1,leading=14,textColor=navy,spaceAfter=8),
 'small':ParagraphStyle('Small',fontName='DejaVu',fontSize=7.6,leading=11,textColor=muted,spaceAfter=5),
 'caption':ParagraphStyle('Caption',fontName='DejaVu',fontSize=8,leading=11.5,textColor=muted,alignment=TA_CENTER,spaceAfter=9),
 'code':ParagraphStyle('Code',fontName='DejaVu',fontSize=8.4,leading=13,textColor=navy,spaceAfter=8),
}
def P(s,style='body'):
    return Paragraph(s,styles[style])
def F(name,caption,max_w=505,max_h=265):
    from PIL import Image as Pil
    file=fig/name
    w,h=Pil.open(file).size
    scale=min(max_w/w,max_h/h)
    return [Image(str(file),width=w*scale,height=h*scale),P(caption,'caption')]
def T(data,widths=None):
    table=Table([[P(str(c),'small') for c in row] for row in data],colWidths=widths,repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),light),('VALIGN',(0,0),(-1,-1),'TOP'),
          ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f9fb')]),
          ('LINEBELOW',(0,0),(-1,0),0.6,teal),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
          ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return table

def footer(canv,doc):
    canv.saveState()
    canv.setStrokeColor(colors.HexColor('#bfdce3'))
    canv.line(43,46,552,46)
    canv.setFont('DejaVu',7.4);canv.setFillColor(muted)
    canv.drawString(43,32,'paceval | On-Device Expression Runtime | Validated C++ research demonstrator | November 2026')
    canv.drawRightString(553,32,str(doc.page))
    canv.restoreState()

doc=SimpleDocTemplate(str(output),pagesize=A4,leftMargin=43,rightMargin=43,topMargin=42,bottomMargin=59,title='On-Device Reusable Expression Runtime with paceval',author='paceval Research Demonstrator')
S=[]
# Cover
S.append(P('On-Device Reusable<br/>Expression Runtime with paceval','title'))
S.append(P('A C++ feasibility study of approved mathematical models, reusable execution graphs and numerical validation','body'))
S+=F('00_on_device_hero.png','Figure 1. Application illustration. The pictured systems are conceptual; the executed study uses synthetic inputs.',max_w=507,max_h=290)
S.append(P('<b>Executive finding.</b> Using the official paceval C++ interface and the original x86-64 Linux runtime, the demonstrator successfully created 1,000 distinct formula-version graphs, checked 32,000 numerical outputs, verified a controlled update and performed a separate pointwise TINC audit. The independent 100-digit audit passed every regular calculation under its stated tolerance.'))
S.append(T([['Research dimension','Verified scope'],['Formula catalog','1,000 approved expressions from five mathematical structures'],['Evaluation and audit','32,000 values, native C++ plus independent mpmath oracle'],['Model maintenance','16 sample checks of an isolated version update'],['Platform','x86-64 Linux; ARM device execution not tested']],[150,355]))
S.append(PageBreak())
# 2
S.append(P('1. Motivation and execution architecture','h1'))
S.append(P('Industrial edge applications may need to evaluate repeatedly used mathematical rules for sensor transformation, engineering correction, scoring and configurable numerical logic. Separating the definition of a mathematical model from its repeated execution can help keep the host application stable when approved formula versions change. The present study tests that separation, not a deployed industrial sensor or a certified real-time runtime.'))
S+=F('01_reusable_runtime_architecture.png','Figure 2. The application host validates inputs and versions, while paceval evaluates prepared mathematical graphs.',max_h=210)
S.append(P('The host program fixes the input contract, formula catalog, version metadata and output format; it owns `paceval_CreateComputation` handles and calls `paceval_DeleteComputation` before library shutdown. It calls the official `paceval_dGetComputationResultExt` batch function for repeated values. Its return value is interpreted correctly: the boolean reports the presence of an API error; per-item error codes are also checked.'))
S.append(P('The project is intentionally in-process. It does not implement an ONNX inference engine, remote REST service, ARM emulator, RTOS, device driver or production device watchdog. The original binary paceval runtime must be supplied independently for the target CPU architecture.'))
S.append(P('<b>Research boundary:</b> 1,000 distinct approved formulas are tested, but they belong to only five analytic families. This verifies catalog and handle reuse, not unrestricted mathematical complexity or scientific model accuracy.','small'))
S.append(PageBreak())
# 3
S.append(P('2. Mathematical workload and inputs','h1'))
S.append(P('Five bounded mathematical families are parameterized by variables (x, a, b, c, d). The reference starting point from WP-008 is the damped sinusoid plus exponential term. Four further families exercise cosine, rational, polynomial, hyperbolic tangent, logarithm and square root, under strictly positive denominators and function arguments.'))
S.append(T([['Family','Expression (each also includes a version-specific constant offset)'],['0 - damped sinusoid','a*sin(b*x) + c*exp(-(d*x))'],['1 - rational/cosine','a*cos(b*x) + c/(1+d*x*x)'],['2 - polynomial/decay','a*x*x + b*x + c*exp(-(d*x))'],['3 - tanh/sine','a*tanh(b*x) + c*sin(d*x)'],['4 - logarithm/root','a*ln(1+b*x*x) + c*sqrt(1+d*x*x)']],[125,380]))
S.append(Spacer(1,10))
S+=F('02_mathematical_families.png','Figure 3. Example results on the synthetic bounded domain, from the published evaluation CSV.',max_h=235)
S.append(P('The generated inputs vary x and the four coefficients deterministically. x starts at 0.025 and moves in positive increments; coefficients remain bounded and positive. All quantities in this synthetic benchmark are dimensionless. The mathematical score is not claimed to be a physical measurement.','small'))
S.append(PageBreak())
# 4
S.append(P('3. Approved catalog and graph lifecycle','h1'))
S.append(P('The published run creates 1,000 separate paceval computation objects, distributing 200 formula versions across each of five base structures. Each version has its own nine-decimal constant embedded in the expression text. Handles are stored using C++ ownership semantics and released automatically. A fixed 32-sample input sweep is evaluated for each graph, resulting in 32,000 checked values.'))
S+=F('03_formula_catalog.png','Figure 4. Actual distribution of the prepared 1,000-formula catalog.',max_h=247)
S.append(P('For a formula update, the host first creates the replacement computation object. Only when that graph succeeds does the single-threaded host replace the selected stored handle. The test updates model 17, with an additive change of +0.125, and verifies 16 corresponding old/new output pairs. Other handles are not re-created in that operation.'))
S.append(P('The C++ demonstration rejects unknown command-line arguments, invalid negative model counts, values outside configured batch limits and nonfinite evaluation inputs before passing them to the engine. Limits used by this research CLI are operational policies, not universal restrictions imposed by paceval.'))
S.append(PageBreak())
# 5
S.append(P('4. Numerical verification','h1'))
S.append(P('Every published regular calculation was evaluated by paceval and an independent native C++ expression. Separately, a Python implementation using mpmath with 100 decimal digits recomputed all 32,000 output values from the published input CSV. The evaluator uses the exact literal version offset and the floating-point input values, ensuring the comparison is well specified.'))
S.append(T([['Numerical criterion','Observed result'],['Accepted values','32,000 of 32,000 within 2e-11 × (1 + |reference|)'],['Independent arbitrary precision','100-digit mpmath numerical oracle'],['Maximum absolute deviation','Approximately 2.988 × 10^-15'],['Batch invariance','Byte-identical result CSVs at batch sizes 1, 37 and 64']],[174,331]))
S.append(Spacer(1,12))
S+=F('04_high_precision_audit.png','Figure 5. A reproducible subset of absolute deviations against the 100-digit independent oracle.',max_h=257)
S.append(P('Small deviations from an exact real-number reference are expected when using double precision. The individual tests do not establish a global numerical error bound or justify any particular scientific model.','small'))
S.append(PageBreak())
# 6
S.append(P('5. Versioned mathematical maintenance','h1'))
S.append(P('Version management is a core part of the on-device use case. To demonstrate a safe update, one pre-approved expression is replaced by a graph whose constant term has changed, without restarting the mathematical engine or rebuilding any other graph. The 16 comparison pairs all reproduce the prescribed 0.125 difference.'))
S+=F('05_formula_version_update.png','Figure 6. The version-2 computation differs from version 1 by the approved constant shift.',max_h=278)
S.append(P('The model-update log includes model identity, input sample, source version, replacement version, old/new result and deviation from the expected change. The other 999 graph handles are retained in memory. This tests formula-scoped change management, not durable persistence across process restarts or multi-tenant configuration governance.'))
S.append(P('A useful follow-up on a real device would examine restart recovery, memory ceilings for large catalogs, corruption detection and device-level worst-case latency. No such guarantees are claimed here.','small'))
S.append(PageBreak())
# 7
S.append(P('6. Pointwise TINC and repeated-input evaluation','h1'))
S.append(P('A separate computation object enables the optional Trusted Interval Computation mode for the first mathematical family. Its returned intervals are checked against independently computed 100-digit values for 24 sampled inputs. All 24 of these specific references lie inside the corresponding reported binary64 bounds.'))
S+=F('06_tinc_sample_widths.png','Figure 7. Widths of the 24 actual reported TINC intervals.',max_h=213)
S.append(P('This is a pointwise numerical observation for selected samples and does not amount to a certified enclosure theorem for all mathematical functions or hardware platforms.'))
S+=F('07_repeated_input_sweep.png','Figure 8. One prepared computation object receives many distinct bounded inputs.',max_h=213)
S.append(PageBreak())
# 8
S.append(P('7. Deployment, architecture and reproducibility','h1'))
S.append(P('<b>Executed environment.</b> The original paceval shared library was supplied externally and linked to an executable compiled with GCC 14.2 on an x86-64 Linux environment. Both GCC and Clang 17 passed three automated CTests; sanitizer-enabled GCC testing also passed all three checks. The complete 1,000-formula scenario was run and its outputs independently audited.'))
S.append(P('<b>ARM boundary.</b> The official paceval repository and service documentation describe ARM64 deployments. This result does not establish the behavior of the current C++ executable on an ARM device. Deployment requires a compatible ARM64 runtime, ARM64 compiler/ABI configuration and full repetition of the tests on the chosen target. Cross-compiled binaries alone do not demonstrate runtime correctness or operating conditions.'))
S.append(P('<b>Reproduction.</b> The project contains `src/on_device_runtime.cpp`, `src/paceval_main.h`, `src/paceval_main.cpp`, `src/CMakeLists.txt`, `src/high_precision_reference.py`, example CSV files and `figures/`. Build from `src/` with `-DPACEVAL_RUNTIME` set to the absolute path of a compatible externally acquired binary library. Run the CTests, then execute the default 1,000-model scenario and the Python reference audit as documented in `README.md`.'))
S.append(P('No measured break-even reuse count, time advantage, p99 latency, RAM ceiling or energy reduction is reported. These quantities were proposed as future system-level evaluation factors in WP-008 and require controlled target-device measurements.'))
S.append(P('Selected sources','h2'))
S.append(P('1. paceval API, prepared computations and batch execution: https://paceval.com/api/','small'))
S.append(P('2. paceval C++ and architecture references: https://github.com/paceval/paceval','small'))
S.append(P('3. ONNX Runtime mobile deployment considerations: https://onnxruntime.ai/docs/tutorials/mobile/','small'))
S.append(P('4. Clang cross-compilation and sysroot requirements: https://clang.llvm.org/docs/CrossCompilation.html','small'))
S.append(P('5. Raspberry Pi OS 64-bit architecture documentation: https://www.raspberrypi.com/documentation/computers/os.html','small'))
S.append(P('6. Source proposal: WP-008, On-Device Reusable Expression Runtime (11 November 2026), user-supplied research proposal.','small'))
S.append(P('Scientific conclusion','h2'))
S.append(P('A reusable, versioned, application-governed mathematical expression runtime is feasible using the original paceval C++ SDK on the tested x86-64 Linux environment. The result provides a reproducible starting point for hardware-specific edge evaluations without implying measurements or qualifications that have not occurred.'))

doc.build(S,onFirstPage=footer,onLaterPages=footer)
print(output)
