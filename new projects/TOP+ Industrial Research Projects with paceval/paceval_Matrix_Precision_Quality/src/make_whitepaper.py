#!/usr/bin/env python3
"""Produce the independently readable English PDF research whitepaper.
All numerical claims come from execution_evidence.json and recorded numerical CSVs.
"""
from pathlib import Path
import json,csv,math
from reportlab.platypus import (SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether,HRFlowable)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'paceval_Matrix_Precision_Quality_Whitepaper_EN.pdf'
E=json.loads((ROOT/'results/execution_evidence.json').read_text())
A=json.loads((ROOT/'results/high_precision_audit.json').read_text())
assert A['status']=='PASS','Cannot claim passed independent tests without an actual passing audit.'
DARK=colors.HexColor('#122D49');TEAL=colors.HexColor('#008E91');MUTED=colors.HexColor('#526475');PALE=colors.HexColor('#E9F5F4');WHITE=colors.white
FONTP='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',FONTP));pdfmetrics.registerFont(TTFont('DejaVu-Bold',FONTB))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVu-Bold')
S={
'cover_kicker':ParagraphStyle('cover_kicker',fontName='DejaVu-Bold',fontSize=9,leading=13,textColor=TEAL,spaceAfter=10),
'cover_title':ParagraphStyle('cover_title',fontName='DejaVu-Bold',fontSize=23,leading=30,textColor=DARK,spaceAfter=11),
'cover_sub':ParagraphStyle('cover_sub',fontName='DejaVu',fontSize=12,leading=17,textColor=MUTED,spaceAfter=14),
'h1':ParagraphStyle('h1',fontName='DejaVu-Bold',fontSize=15,leading=20,textColor=DARK,spaceBefore=5,spaceAfter=12),
'h2':ParagraphStyle('h2',fontName='DejaVu-Bold',fontSize=10.4,leading=15,textColor=TEAL,spaceBefore=14,spaceAfter=7),
'body':ParagraphStyle('body',fontName='DejaVu',fontSize=9.1,leading=14.8,textColor=DARK,spaceAfter=10),
'small':ParagraphStyle('small',fontName='DejaVu',fontSize=8,leading=12.5,textColor=MUTED,spaceAfter=8),
'caption':ParagraphStyle('caption',fontName='DejaVu',fontSize=8.1,leading=12.4,textColor=MUTED,spaceAfter=10),
'eq':ParagraphStyle('eq',fontName='DejaVu',fontSize=10,leading=16,textColor=DARK,spaceBefore=6,spaceAfter=9,leftIndent=8),
'cell':ParagraphStyle('cell',fontName='DejaVu',fontSize=7.5,leading=11.2,textColor=DARK),
'cell_head':ParagraphStyle('cell_head',fontName='DejaVu-Bold',fontSize=7.7,leading=11.5,textColor=WHITE)
}

def para(s,kind='body'):return Paragraph(s,S[kind])
def h(s):return para(s,'h1')
def small(s):return para(s,'small')
def eq(s):return para(s,'eq')
def section(story,name,body):story.append(h(name));story.append(para(body))
def table(headers,rows,widths=None):
 rows=[[para(str(x),'cell_head') for x in headers]]+[[para(str(x),'cell') for x in row] for row in rows]
 t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),DARK),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F3F8FA')]),('LINEBELOW',(0,0),(-1,0),.7,TEAL),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8)]))
 return t

def fig(name,width,cap):
 path=ROOT/'figures'/(name+'.png')
 from PIL import Image as PILImage
 with PILImage.open(path) as img:
  w,hpx=img.size
 img=Image(str(path),width=width,height=width*hpx/w)
 return [img,para(cap,'caption')]

def add_fig(story,name,width,caption):story.extend(fig(name,width,caption))

def footer(canvas,doc):
 canvas.saveState();W,H=A4
 canvas.setStrokeColor(colors.HexColor('#CDDDE3'));canvas.line(44,H-37,W-44,H-37)
 canvas.setFont('DejaVu',7.1);canvas.setFillColor(MUTED)
 canvas.drawString(44,27,'paceval | Programmable Matrix Mathematics | Research 2026')
 canvas.drawRightString(W-44,27,str(doc.page))
 canvas.restoreState()

def main():
 doc=SimpleDocTemplate(str(D),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=48,bottomMargin=47,title='Programmable Matrix Mathematics for Industrial Quality Monitoring with paceval',author='paceval mathematical research demonstrator',allowSplitting=1)
 story=[]
 # Cover, page 1.
 story.append(Spacer(1,18));story.append(para('PACEVAL  |  SCIENTIFIC RESEARCH &amp; VERIFIED MATHEMATICS','cover_kicker'))
 story.append(para('Programmable Matrix Mathematics for Industrial Quality Monitoring','cover_title'))
 story.append(para('Dense SPD matrix models, reusable quality functions, independently audited execution graphs and TINC rounding enclosures','cover_sub'))
 story.extend(fig('00_matrix_precision_hero',507,'Concept illustration; not a computed research result. Original source image: 2400 × 1200 pixels (2:1).'))
 story.append(Spacer(1,5))
 story.append(para('<b>Research outcome.</b> Previously recorded full-dimensional 512 × 512 and 1024 × 1024 SPD inverses form the mathematical baseline. A new paceval MCP 4.26 execution evaluates versioned quality scores and TINC bounds on synthetic multichannel residuals. Independent numerical checks on the stored data passed.'))
 story.append(para('<b>Scope.</b> Mathematical functionality and traceability only. No industrial sensor data, certified tolerance decision, full measurement-uncertainty budget or newly executed local SDK binary test is claimed.','small'))
 story.append(small('13 November 2026  |  English whitepaper  |  User-provided original matrix research expanded with a new industrial quality use case.'))
 story.append(PageBreak())
 # Page 2.
 section(story,'1. Introduction: industrial use case and current state of the art',
 'Precision manufacturing, industrial metrology and sensor-based machine monitoring depend on consistent interpretation of multiple measurements. Temperature fluctuations, geometric motion, vibration and related machine effects can create correlated deviations. A high-dimensional covariance representation describes those relationships more faithfully than treating every sensor channel in isolation. The central industrial question is whether a newly observed residual vector is compatible with a defined multichannel mathematical model and a justified decision policy. This research uses a <b>hypothetical 512-channel quality-monitoring scenario</b> to demonstrate that functional chain.')
 story.append(para('Well-established algorithms handle the core numerical algebra. Cholesky factorization decomposes a symmetric positive-definite matrix into triangular factors. LAPACK provides standard factorizations and direct linear-system solvers. A quadratic form of the inverse covariance can summarize a correlated residual; related statistics appear in multivariate process-control and sensor-fusion applications. The 2025 machinery condition-monitoring literature continues to address correlations, covariate effects, robust covariance estimates and outlier sensitivity [4, 5].'))
 story.append(para('A separate metrological context is essential. The BIPM guides JCGM 102 and JCGM 106 concern multivariate measurement uncertainty and conformity assessment [2, 3]. A floating-point rounding enclosure is <b>not</b> a substitute for an uncertainty model covering sensors, calibration, model drift and operational risk. The paceval-specific TINC facility is examined solely for the arithmetic component of numerical evaluation [6].'))
 story.append(h('Practical hypothetical workflow'))
 story.append(para('A machine test cell provides a full covariance model for hundreds of dimensionless condition indicators. A validated inverse matrix is available from a prior paceval research computation. A new batch of observations is transformed into residuals. The mathematical engine evaluates an explicit quality formula, optional revision penalties, signed margins and sensitivities. A host program then selects review or acceptance actions according to a policy. Every input, model version and result can be recorded.'))
 story.append(para('<b>Research contribution.</b> This paper combines an existing full-size matrix experiment with newly executed, independently checked paceval mathematical graphs. It examines functional programmability and model governance. It does not assert a new matrix algorithm or an industrially certified decision rule.'))
 story.append(PageBreak())
 # Page 3.
 story.append(h('2. Research question and experimental architecture'))
 story.append(para('Can full-size covariance-related matrix results be integrated into a reusable and version-controlled sequence of mathematical quality functions? Can several graph outputs be applied to consistent input scenarios and independently checked? Can selected rounding enclosures be inspected without confusing them with measurement uncertainty?'))
 add_fig(story,'01_architecture_schematic',505,'Figure 1. Workflow schematic. The recorded full inverse provides precision coefficients; the new real paceval MCP graphs supply score values and sensitivities; the host retains decisions. This figure is an architectural illustration, not a numerical calculation.')
 story.append(h('Execution responsibilities'))
 story.append(table(['Component','Responsibility','Evidence'],[
 ('Archived original local paceval SDK','Complete dense SPD Cholesky, inverse and matrix-related kernels','Preserved original full 512D/1024D numerical results and source'),
 ('New paceval MCP 4.26','Persistent quadratic scores, versioned margins, sensitivity functions and TINC','Graph handles and returned batch data recorded in the evidence manifest'),
 ('Host and independent validation','Input checks, scenario loops, classification, files and independent numerical reference','C++ source and mpmath / NumPy reference scripts')],[146,212,149]))
 story.append(PageBreak())
 # Page 4.
 story.append(h('3. Defined mathematical model'))
 story.append(para('Let A be a synthetic, real, symmetric positive-definite 512 × 512 covariance-like matrix. Its full inverse P = A<super>-1</super> was previously computed through persistent paceval matrix graphs and saved as IEEE-754 binary64. The new residual vector has precisely three potentially nonzero entries. All quantities are dimensionless.'))
 story.append(eq('<b>A = LL<super>T</super>, &nbsp; P = A<super>-1</super>, &nbsp; r = (x, y, z, 0, ..., 0)<super>T</super>.</b>'))
 story.append(para('For this sparse vector, the complete 512-dimensional quadratic form r<super>T</super>Pr depends exactly on the 3 × 3 leading precision block. This identity does not reduce the stored matrix inverse itself to a three-dimensional inverse. Denote its six independent upper-triangular coefficients by a, b, c, d, e and f.'))
 story.append(eq('<b>q<sub>1</sub> = a x² + 2bxy + 2cxz + d y² + 2eyz + f z².</b>'))
 story.append(para('The controlled second model introduces an explicitly specified nonnegative engineering penalty h. The signed margin is positive below the illustrative threshold t. These are mathematical screening scores, not a process-specific quality acceptance standard.'))
 story.append(eq('<b>q<sub>2</sub> = q<sub>1</sub> + h(x² + y² + z²), &nbsp; m<sub>1</sub> = t - q<sub>1</sub>, &nbsp; m<sub>2</sub> = t - q<sub>2</sub>.</b>'))
 story.append(eq('<b>∂q<sub>2</sub>/∂x = 2ax + 2by + 2cz + 2hx; &nbsp; ρ<sub>1</sub> = √q<sub>1</sub>.</b>'))
 story.append(table(['Model input','Defined role','Value / provenance'],[
 ('P coefficients a,b,c,d,e,f','Leading subblock of archived 512D full inverse','Read from recorded full paceval binary output'),
 ('x, y, z','Only three active residual channels','Deterministic synthetic grid and selected examples'),
 ('h','Version 2 extra diagnostic penalty','0.08, chosen hypothetically'),
 ('t','Illustrative signed-margin threshold','7.815, not a calibrated industrial limit')],[106,180,221]))
 story.append(Spacer(1,13));story.append(para('A conventional chi-square interpretation requires additional distribution assumptions and estimated-parameter treatment. In particular, q<sub>2</sub> is a deliberately revised engineering score and does not automatically follow the same distribution as a Mahalanobis statistic.'))
 story.append(PageBreak())
 # Page 5.
 story.append(h('4. Actual paceval execution architecture'))
 story.append(para('The new study registered nine ordinary mathematical graphs and two additional TINC-enabled graph variants with the genuine paceval 4.26 MCP connection. Each graph was created once and then evaluated for multiple input scenarios. The recorded server outputs are retained without modification of the underlying formulas. The additional locally compiled C++ source uses the original paceval C/C++ interface, but this release does not assert successful execution of that source: a separately supplied compatible Linux runtime was unavailable.'))
 story.append(table(['Mathematical group','Actual execution','Provenance'],[
 ('Full 512D/1024D SPD inverse','Recorded original local paceval SDK','Archived complete matrix binaries'),
 ('q1 and q2','New paceval MCP persistent graphs','Two separate simultaneously callable versions'),
 ('q2 minus q1','New paceval MCP persistent graph','A third graph evaluated over the same 81 grid inputs'),
 ('m1 and m2','New paceval MCP persistent graphs','Signed threshold-margin computations'),
 ('Residual sensitivities','New paceval MCP persistent graphs','Explicit analytical derivatives'),
 ('Normalized radial score','New paceval MCP persistent graph','Square root of base quadratic statistic'),
 ('TINC q1 and m1','New paceval MCP interval graphs','Recorded upper and lower rounding bounds'),
 ('Scenario classification','Host responsibility','Uses graph-computed margins; no paceval certification claimed')],[160,160,187]))
 story.append(Spacer(1,12));story.append(para('The provided `src/matrix_precision_paceval.cpp` is configured to use <b>paceval_CreateComputation</b>, <b>paceval_dGetComputationResultExt</b> and <b>paceval_dGetMultipleComputationsResultsExt</b> on persistent model handles. In particular, it includes an actual programmatic batch-layout cross-check against individual graph results. This code path remains subject to future execution on a compatible external SDK runtime.'))
 story.append(PageBreak())
 # Page 6.
 story.append(h('5. Deterministic workload and verification methodology'))
 story.append(para('The full-size matrix source is the previously recorded dense 512D/1024D SPD research package. The new workload spans a 9 × 9 Cartesian grid of residual channels x and y, with z fixed to 0.75, plus five distinct selected scenarios. All coefficients come from the previously recorded full inverse matrix. The new paceval service ran eight mathematical functions on the selected cases, two interval-enabled functions on those cases and three quality functions on the grid.'))
 story.append(table(['Recorded activity','Count or status'],[
 ('New persistent computation handles','11, of which 2 are TINC-enabled'),
 ('New bulk evaluation requests','4'),
 ('Distinct new input scenarios','86'),
 ('Successfully returned graph-point pairs','293'),
 ('Independent reference check','Passed for recorded new results and preserved full matrices'),
 ('New local C++ SDK execution','Not run. Original compatible shared library unavailable')],[260,247]))
 story.append(Spacer(1,11));story.append(para('The numerical evidence manifest prevents confusion between graph count, requests and graph-point evaluations. The independent high-precision reference uses the exact binary64 model inputs, evaluating the quadratic functions and sensitivities independently at high precision. TINC endpoint strings are reconstructed as binary64 for the sample inclusion checks. The preserved complete matrix A and inverse P are also checked through full matrix multiplication with NumPy. Detailed numerical differences and tolerances remain in the technical audit, not in this public whitepaper.'))
 story.append(para('<b>Result scope:</b> The reported tests passed for the stated synthetic values and source files. This does not certify arbitrary positive-definite conditioning regimes, metrological uncertainty propagation or real production acceptance decisions.'))
 story.append(PageBreak())
 # Page 7 recorded matrix figures.
 story.append(h('6. Recorded full-size matrix evidence'))
 add_fig(story,'02_recorded_inverse_matrix',388,'Figure 2. Leading block of the complete 512-dimensional original paceval inverse. Binary matrix data came from the prior research package and were independently checked again.')
 add_fig(story,'03_inverse_diagonal_models',388,'Figure 3. Previously recorded inverse diagonal coefficients for the two full-size SPD models. These are distinct deterministic synthetic instances.')
 story.append(PageBreak())
 # Page 8 q surface and version penalty.
 story.append(h('7. New quality-score and versioning results'))
 add_fig(story,'04_mcp_quality_surface',360,'Figure 4. Actual new paceval MCP version 1 quadratic scores for 81 independent grid points. The 3D surface is based on recorded engine results.')
 add_fig(story,'05_model_revision_surface',360,'Figure 5. Actual paceval MCP difference between model versions. The additional penalty is deliberately specified, not learned or industrially calibrated.')
 story.append(PageBreak())
 # Page 9 decision boundaries.
 story.append(h('7.1 Quality screening regions and boundaries'))
 add_fig(story,'06_decision_regions_v1',300,'Figure 6. Illustrative version 1 threshold regions using recorded paceval scores. This is a synthetic mathematical screening limit, not a metrological acceptance test.')
 add_fig(story,'09_versioned_quality_boundaries',300,'Figure 9. The independent model versions yield different score boundaries when evaluated by paceval over the same input grid.')
 story.append(PageBreak())
 # Page 10 precision and derivatives.
 story.append(h('7.2 Arithmetic precision and sensitivities'))
 add_fig(story,'07_tinc_enclosure_width',380,'Figure 7. Widths of five TINC arithmetic rounding enclosures returned by paceval MCP. The widths do not include sensor or calibration uncertainty.')
 add_fig(story,'08_mcp_model_sensitivity',380,'Figure 8. New paceval-computed explicit analytical sensitivities across the recorded example scenarios. The parameterization of version 2 remains separately available.')
 story.append(PageBreak())
 # Page 11 interpretation.
 story.append(h('8. Reusable expressions and controlled changes'))
 story.append(para('A principal operational advantage of a reusable formula model is that a precise and versioned mathematical rule can be inspected and re-evaluated on consistent input vectors. The new paceval MCP research registers q1, q2, their decision margins and their derivatives separately. Neither new formula silently overwrites the original score; both versions are evaluated on the same synthetic residuals. The recorded outputs support a direct and auditable mathematical comparison of changed engineering rules.'))
 story.append(h('9. Industrial interpretation and important limits'))
 story.append(para('The combined project establishes a reproducible functional chain from a previously computed dense matrix inverse to newly executed score, margin, derivative and interval graphs. It illustrates a feasible architecture for a manufacturing quality-monitoring or multisensor research prototype. The natural industrial division is between optimized matrix routines, a reusable domain-mathematics layer and a host-managed decision policy. Such an architecture also accommodates the original paceval matrix kernels when mathematical programmability of the matrix step itself is the research goal.'))
 story.append(para('Several boundaries should remain explicit. The previous large SPD matrices are synthetic and well-conditioned. The new residuals activate only three of 512 mathematical channels. Input covariances were not estimated from real sensors. There was no study of near-singular, indefinite, or severely mis-scaled matrices, nor of statistically estimated false-alarm rates. The decision threshold and version 2 penalty are illustrative. The recorded TINC tests concern rounding enclosures and finite sample inclusion only. No general interval theorem, global numerical certification, industrial measurement uncertainty assessment, production deployment or regulator approval follows from these examples.'))
 story.append(para('An evidence-led industrial continuation would use actual sensor datasets and traceable calibration, compare appropriate covariance estimators, explicitly handle drift and changing conditions, define independent validation datasets and then introduce a justified guard-banded acceptance rule. JCGM 106 is relevant to the final decision policy. Any assertion of general reliability must be evaluated against the resulting instrument, data and statistical model rather than inferred from arithmetic output alone.'))
 story.append(PageBreak())
 # Page 12 reproduction and references.
 story.append(h('10. Reproduction, source material and references'))
 story.append(para('The package includes original SDK header/implementation source files, the earlier full-size matrix source and recorded binaries, the new C++ program, independent numerical Python checks, exact model and scenario metadata, reproducible visualization scripts and this PDF. The original paceval Linux shared library is intentionally excluded.'))
 story.append(para('<b>Verification commands</b>', 'h2'))
 story.append(para('python3 src/high_precision_reference.py .<br/>python3 src/make_figures.py<br/>python3 src/check_readme_math.py .', 'small'))
 story.append(para('<b>Native local SDK build, once original runtime is supplied</b>','h2'))
 story.append(para('cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so<br/>cmake --build build -j<br/>ctest --test-dir build --output-on-failure','small'))
 story.append(para('The newly provided C++ source passed a compile-time syntax check in the current environment; local link/execution and CTest remain not run. The new paceval numerical results come from successful real MCP requests. Full 512D and 1024D numerical matrices are reused as recorded upstream research evidence, not falsely described as new calculations.'))
 story.append(para('<b>Primary references</b>','h2'))
 refs=[
 '[1] Netlib, LAPACK DPOTRS and Cholesky-based SPD solves. www.netlib.org/lapack/.',
 '[2] BIPM, JCGM 102:2011. Extension to any number of output quantities. doi:10.59161/JCGM102-2011.',
 '[3] BIPM, JCGM 106:2012. Role of measurement uncertainty in conformity assessment. doi:10.59161/JCGM106-2012.',
 '[4] Auxiliary covariate-assisted condition monitoring for machinery (2025). Reliability Engineering &amp; System Safety, ScienceDirect S0951832025011573.',
 '[5] A robust covariance matrix-based Hotelling T-squared control chart (2025). Quality and Reliability Engineering International, doi:10.1002/qre.70025.',
 '[6] paceval developers, TINC and original C/C++ API. paceval.com/developers/; paceval.com/api/.',
 '[7] Previous research, <i>Programmable Matrix Mathematics for Industrial Systems with paceval</i>, user-provided original PDF in docs/.'
 ]
 for r in refs:story.append(para(r,'small'))
 story.append(para('Research status: genuine paceval execution verified for the indicated recorded examples; industrial validation remains a separate future research step.','small'))
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 print('Wrote PDF',D,D.stat().st_size)
if __name__=='__main__':main()
