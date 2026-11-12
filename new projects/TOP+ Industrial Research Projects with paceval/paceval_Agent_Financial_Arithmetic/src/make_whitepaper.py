#!/usr/bin/env python3
"""Build the English WP-011 report from the reproducible research package.

Requires reportlab, generates a stand-alone PDF at repository root.
No proprietary runtime or timing benchmarks are embedded into the document.
"""
from pathlib import Path
import csv
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

ROOT=Path(__file__).resolve().parents[1]
FIG=ROOT/'figures'; DATA=ROOT/'examples'
OUT=ROOT/'paceval_Agent_Financial_Arithmetic_Whitepaper_EN.pdf'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if Path(FONT).exists():
    pdfmetrics.registerFont(TTFont('DVS',FONT));pdfmetrics.registerFont(TTFont('DVS-Bold',BOLD))
    normal='DVS'; bold='DVS-Bold'
else:
    normal='Helvetica';bold='Helvetica-Bold'
NAVY=colors.HexColor('#10283a'); TEAL=colors.HexColor('#087d92');PALE=colors.HexColor('#eaf4f7');GRAY=colors.HexColor('#455d6c')
styles={
 'title':ParagraphStyle('title',fontName=bold,fontSize=21,leading=27,textColor=NAVY,spaceAfter=11),
 'subtitle':ParagraphStyle('subtitle',fontName=normal,fontSize=11.5,leading=18,textColor=TEAL,spaceAfter=12),
 'h1':ParagraphStyle('h1',fontName=bold,fontSize=14.5,leading=20,textColor=NAVY,spaceBefore=7,spaceAfter=12),
 'h2':ParagraphStyle('h2',fontName=bold,fontSize=10.7,leading=15,textColor=TEAL,spaceBefore=10,spaceAfter=5),
 'body':ParagraphStyle('body',fontName=normal,fontSize=9.2,leading=15.1,textColor=NAVY,spaceAfter=9),
 'small':ParagraphStyle('small',fontName=normal,fontSize=8.0,leading=12.3,textColor=GRAY,spaceAfter=7),
 'caption':ParagraphStyle('caption',fontName=normal,fontSize=8.1,leading=11.5,textColor=GRAY,alignment=TA_CENTER,spaceAfter=11),
 'cell':ParagraphStyle('cell',fontName=normal,fontSize=8.5,leading=12.5,textColor=NAVY),
 'cellhead':ParagraphStyle('cellhead',fontName=bold,fontSize=8.7,leading=12.5,textColor=NAVY),
}

def P(txt,style='body'):return Paragraph(txt,styles[style])
def fig(name,width=495,caption=None):
    p=FIG/name
    im=Image(str(p));w,h=im.imageWidth,im.imageHeight
    im.drawWidth=width;im.drawHeight=width*h/w
    result=[im]
    if caption:result.append(P(caption,'caption'))
    return result

def table(rows,widths=None):
    lines=[]
    for k,row in enumerate(rows):lines.append([P(str(c),'cellhead' if k==0 else 'cell') for c in row])
    t=Table(lines,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
      ('BACKGROUND',(0,0),(-1,0),PALE),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f9fa')]),
      ('LINEBELOW',(0,0),(-1,0),.6,TEAL),('VALIGN',(0,0),(-1,-1),'TOP'),
      ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
      ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)
    ]))
    return t

def footer(c,doc):
    c.saveState();w,h=A4
    c.setStrokeColor(colors.HexColor('#c7dae0'));c.line(45,37,w-45,37)
    c.setFont(normal,7.2);c.setFillColor(GRAY)
    c.drawString(45,24,'paceval. | Agent-Assisted Financial Scenario Arithmetic | Research demonstrator | 2026')
    c.drawRightString(w-45,24,str(doc.page));c.restoreState()


def build():
    d=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=46,bottomMargin=50,
                        title='paceval Agent-Assisted Financial Scenario Arithmetic',author='paceval research demonstrator')
    with (DATA/'high_precision_audit.json').open() as f:audit=json.load(f)
    story=[]
    def add(*objects):story.extend(objects)
    def page():add(PageBreak())

    # PAGE 1
    add(P('Agent-Assisted Financial Scenario Arithmetic','title'),P('An executable, independently audited paceval mathematical-tool demonstrator','subtitle'))
    add(*fig('00_financial_agent_hero.png',498,'Cover illustration: agent-facing financial requests pass through typed validation before reusable paceval graph evaluation.'))
    add(P('<b>Research outcome.</b> Four predefined financial models were implemented with direct paceval C/C++ SDK calls and a persistent local tool adapter. One hundred valid research tasks and twenty intentionally malformed tasks were executed, with 1,600 sensitivity results checked independently at 100 decimal digits.'))
    add(P('<b>Scope.</b> The environment uses synthetic EUR/USD-denominated scenarios and a compatible x86-64 Linux runtime. This document reports computational feasibility and reproducible numeric agreement, not investment advice, transaction execution, a production MCP service, or a validated market model.','small'))
    page()
    # PAGE 2
    add(P('1. Research question and execution architecture','h1'))
    add(P('The originating WP-011 proposal focused on repeated cash-flow and return arithmetic. This implementation tests whether a typed agent request can be admitted, evaluated with a previously compiled paceval expression graph, repeated over an input sweep, and independently audited without delegating numeric execution to a language model.'))
    add(*fig('01_validated_agent_workflow.png',492,'Figure 1. Explicit trust boundary. Host-side policy and domain checks precede the paceval execution graph.'))
    add(P('The host rejects missing, non-finite, out-of-range, ambiguous and unapproved inputs; it owns scenario generation, output serialization and independent auditing. paceval owns the mathematical graph creation and evaluation. A graph remains available for subsequent requests rather than rebuilding its formula at every call.'))
    add(P('<b>Experimental context:</b> not an end-to-end agent trial. The JSONL adapter demonstrates the callable tool interface with synthetic agent-like requests. There is no connected LLM or remote MCP protocol endpoint.','small'))
    page()
    # PAGE 3
    add(P('2. Approved mathematical model contracts','h1'))
    rows=[['Kernel','Expression and timing convention'],
          ['Six-period NPV','NPV = Σ(C_t / (1+r)^t), t = 0...5; C_0 is undiscounted; cash flows annual.'],
          ['Future value','FV = principal × exp(years × ln(1+r)); annual compounding.'],
          ['Annuity present value','PV = payment × (1 − exp(−years × ln(1+r))) / r; year-end payments.'],
          ['CAGR','CAGR = exp(ln(final/principal)/years) − 1; decimal annual return.']]
    add(table(rows,[130,375]),Spacer(1,11))
    add(P('Each formula is registered under an exact <b>model ID and version</b>. The agent-facing input schema accepts only the parameters needed by its selected model. The C++ SDK interface uses eleven consistently named variables; unused internal slots are populated with fixed values and are not additional user requirements.'))
    add(P('Conventions and domain controls.','h2'))
    add(P('The unit contract requires one input currency (EUR or USD), annual periods, and rates expressed as decimal per year (for example 0.05 means 5%). Research-domain bounds include rates from 0.001 to 0.30; full years 1–30; strictly positive principal and final value; and finite bounded cash flows. No FX conversion, market-rate discovery, business-case interpretation or automatic parameter estimation takes place.'))
    add(P('The original WP-011 expression was notation-level NPV. Here the six-period summation is expanded into an actual expression string accepted by the tested paceval runtime.','small'))
    page()
    # PAGE 4
    add(P('3. Deterministic research workload','h1'))
    add(P('The dataset comprises <b>100 valid tasks</b> distributed equally over four mathematical models plus <b>20 deliberately invalid tasks</b>. Each valid task has 16 deterministic sensitivity scenarios. Rates are varied within an approved annual interval; CAGR tasks vary final values. These are synthetic controlled inputs with predefined assumptions, not real financial contracts.'))
    add(*fig('04_request_validation.png',476,'Figure 2. Host validation accepts valid tasks and rejects the deliberately erroneous input classes.'))
    add(P('Rejection classes include unapproved model names, unsupported formula versions, missing or ambiguous units, out-of-range rates or time horizons, currency mismatches, and invalid financial-domain values. Each accepted request has a stable ID, model ID, formula version and output unit.'))
    page()
    # PAGE 5
    add(P('4. Numerical execution and independent audit','h1'))
    add(table([['Test','Observed result'],
        ['Batch arithmetic','1,600 / 1,600 scalar values within the pre-defined tolerance'],
        ['Independent decimal calculation','1,600 / 1,600 checked with 100-digit precision'],
        ['Controlled version update','16 / 16 changed NPV values independently verified'],
        ['Native C++ reference','All 1,600 sensitivity samples passed'],
        ['Tolerance','Absolute difference ≤ 10⁻⁹ × (1 + |reference|)']], [222,283]),Spacer(1,10))
    add(*fig('06_native_reference_accuracy.png',475,'Figure 3. Distribution of arithmetic discrepancies relative to a separately coded native C++ calculation.'))
    add(P(f"The maximum absolute distance to the separate 100-digit reference in the released audit is approximately <b>{audit['max_absolute_difference']:.3g}</b> in model output units. Accuracy is assessed against the specified mathematical expressions only; it does not imply that any discount rate or cash-flow assumption is economically correct.",'small'))
    page()
    # PAGE 6
    add(P('5. Sensitivity studies and reusable graphs','h1'))
    add(P('A single computation graph is created for each approved mathematical model and reused for multiple tasks and input sweeps. The agent-facing stream keeps all four graphs alive inside one C++ subprocess. In twelve valid JSONL calls, four calls were initial uses and eight calls explicitly returned graph_reused=true.'))
    add(*fig('03_four_models_sensitivity.png',468,'Figure 4. Normalized model sensitivities from the generated, deterministic CSV examples.'))
    add(P('Model parameters and interest-rate conventions are fixed within each calculation. Derivative estimation is not part of this study; the plotted values are direct repeated evaluations of the approved formulas.'))
    page()
    # PAGE 7
    add(P('6. Version control and agent interface','h1'))
    add(P('A controlled update changes the final cash-flow term in NPV from C5 to 0.98 × C5, creating NPV v2 as a separate computation graph. All 16 revised outputs are checked against an independent calculation before any future promotion to the agent-facing approved model registry. The original NPV v1 graph remains available and the other three model graphs are not rebuilt.'))
    add(*fig('07_model_version_change.png',476,'Figure 5. A deliberately different financial assumption creates a traceable new formula version.'))
    add(P('The local JSONL tool adapter supports the approved model identifiers and model-specific parameter schemas, with explicit currency, annual rate, year and version fields. It rejects missing parameters and invalid request types before invoking the C++ core. Test responses record numeric value, output unit, status and graph-reuse indicator. This is a tool-contract demonstration, not a remote MCP or LLM deployment.'))
    page()
    # PAGE 8
    add(P('7. TINC interval evaluation: equivalent mathematical graphs','h1'))
    add(P('The baseline one-period discount equation is <b>principal / (1 + rate)</b>. Under the tested Linux runtime, its raw TINC intervals included the exact-real reference for only <b>22/24 fixed samples</b> when the numerical reference was evaluated from the actual IEEE-754 binary64 inputs. The older 23/24 count was based on the displayed decimal CSV strings, and did not fully represent the binary inputs.'))
    add(P('For the validated input domain rate &gt; -1, the mathematically identical expression <b>principal * exp(-ln(1 + rate))</b> provides an alternative computation graph. The original paceval library returned raw, unmodified TINC intervals that enclosed the independent 100-digit reference in <b>24/24 fixed samples</b> and <b>1,500/1,500 additional deterministic samples</b>. No host-side interval enlargement was used.'))
    add(*fig('08_tinc_point_audit.png',476,'Figure 6. Same mathematical discount function: direct-division TINC vs. reformulated TINC, against the exact input binary64 values.'))
    add(P('The separate sample audit reproduces both raw result sets, preserves the baseline non-inclusions, and fails automatically if any reformulated interval misses its reference. The numerical inclusion observation is specific to the tested version, input domain and samples; it is not a universal interval-proof claim. The primary NPV, annuity, future-value and CAGR evaluations are independently checked as before.'))
    page()
    # PAGE 9
    add(P('8. Reproducibility and scope','h1'))
    add(P('<b>Build:</b> Compile src/financial_agent.cpp and the unmodified official public API facade src/paceval_main.cpp with CMake, linking a compatible external Linux .so. The published repository intentionally contains no shared library and no LICENSE_NOTICE.md. The original SDK copyright and license notices remain in its two source files.'))
    add(P('<b>Run:</b> ctest from the build directory; run financial_agent --input examples/requests.csv --batch 37 --out reproduced; run python3 src/high_precision_reference.py reproduced; invoke src/agent_tool_adapter.py against the persistent C++ process with the included JSONL cases. All generated scalar results, model versions and rejection reasons can be traced to the included CSV/JSONL examples.'))
    add(table([['Responsibility','Implemented by'],['Graph creation and numeric evaluation','Official paceval C/C++ API'],
     ['Validation, sensitive-data policy, scenario sweeps','C++ host and local Python JSONL adapter'],
     ['High-precision reference and charts','Separate Python Decimal and Matplotlib scripts'],
     ['Cash-flow assumptions, rates and investment decisions','Externally supplied; not generated or endorsed by this tool']], [215,290]))
    add(P('9. External references','h1'))
    add(P('1. paceval mathematical engine, public C/C++ SDK and computation API: https://paceval.com/api/','small'))
    add(P('2. Model Context Protocol specification and typed tool contracts: https://modelcontextprotocol.io/specification/2025-11-25/server/tools','small'))
    add(P('3. OWASP LLM01 Prompt Injection and trust-boundary recommendations: https://genai.owasp.org/llmrisk/llm01-prompt-injection/','small'))
    add(P('4. U.S. SEC discussion of discounted-cash-flow valuation methodology: https://www.sec.gov/Archives/edgar/vprr/0800/08002077.pdf','small'))
    add(P('<b>Conclusion:</b> The tested architecture successfully integrates reusable paceval mathematical graphs into a typed synthetic financial-scenario workflow with numerical verification and traceable rejections. Production-grade financial suitability, market-data validity, financial advice, and full agent integration are beyond the demonstrated scope.','small'))

    d.build(story,onFirstPage=footer,onLaterPages=footer)
    print('Created',OUT)

if __name__=='__main__':build()
