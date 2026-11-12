#!/usr/bin/env python3
"""Generate the English editorial research PDF from verified project artifacts."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import csv,json
root=Path(__file__).resolve().parents[1]
target=root/'paceval_Material_Symbolic_Regression_Whitepaper_EN.pdf'
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
ink=colors.HexColor('#14293a');teal=colors.HexColor('#168c9c');gray=colors.HexColor('#596a76');light=colors.HexColor('#eaf3f5')
s={
 'title':ParagraphStyle('title',fontName='DVB',fontSize=21.5,leading=27,textColor=ink,spaceAfter=10),
 'subtitle':ParagraphStyle('subtitle',fontName='DV',fontSize=11.5,leading=17,textColor=teal,spaceAfter=10),
 'heading':ParagraphStyle('heading',fontName='DVB',fontSize=17,leading=22,textColor=ink,spaceAfter=10),
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.1,leading=15,textColor=ink,spaceAfter=11),
 'note':ParagraphStyle('note',fontName='DV',fontSize=8,leading=12,textColor=gray,spaceAfter=9),
 'cap':ParagraphStyle('cap',fontName='DV',fontSize=8,leading=12,textColor=gray,alignment=TA_CENTER,spaceAfter=12),
 'th':ParagraphStyle('th',fontName='DVB',fontSize=8.4,leading=12,textColor=ink),
 'td':ParagraphStyle('td',fontName='DV',fontSize=8.2,leading=12,textColor=ink),
}
P=lambda value,key='body':Paragraph(value,s[key])
story=[]
def add(*items):
 for x in items:story.append(P(x))
def heading(n,name):story.append(P(f'{n}. {name}','heading'))
def page():story.append(PageBreak())
def figure(name,caption,maxh=268):
 from PIL import Image as PIL
 path=root/'figures'/name
 image=PIL.open(path);w=505;h=w*image.height/image.width
 if h>maxh:h=maxh;w=h*image.width/image.height
 story.append(Image(str(path),width=w,height=h));story.append(P(caption,'cap'))
def tab(rows,widths=(210,295)):
 data=[[P(str(c),'th' if i==0 else 'td') for c in row] for i,row in enumerate(rows)]
 t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),light),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f8f9')]),('LINEBELOW',(0,0),(-1,0),.7,teal),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
 story.append(t);story.append(Spacer(1,11))
rank=list(csv.DictReader((root/'examples/wp019_ranking.csv').open()))
selected=list(csv.DictReader((root/'examples/wp019_selected.csv').open()))
audit=json.loads((root/'results/decimal_audit.json').read_text())
chosen=min(rank,key=lambda r:(float(r['validation_rmse_GPa']),int(r['candidate_id'])))
# 1: cover
story.append(P('Material Property Symbolic-Regression Candidate Evaluation','title'))
story.append(P('An executable paceval C++ demonstration of dimensioned, reusable materials-property expressions','subtitle'))
figure('00_material_symbolic_hero.png','Cover illustration: materials, symbolic candidate equations, reusable execution and synthetic model evaluation.',maxh=265)
add('<b>Research outcome.</b> Using the supplied paceval 4.25 public C/C++ facade and a compatible Linux engine, the project constructed 1,000 reusable expression graphs. A deterministic workload executed 60,000 paceval scalar evaluations and 32,000 paceval batch evaluations, all agreeing with separately programmed native C++ formula outputs within 2 x 10<super>-9</super> GPa.')
add('<b>Independent audit.</b> The 60 exported selected-candidate predictions were also independently recomputed using 80-significant-digit decimal arithmetic, with all 60 within 2 x 10<super>-10</super> GPa. The independently coded decimal oracle checks output arithmetic; it does not imply paceval itself computes to 80-digit precision.')
add('<b>Scope.</b> The data are synthetic, the equation families are predeclared and their coefficients are not fitted. This is a mathematical candidate-evaluation demonstration, <b>not</b> scientific discovery of a new law, measured-property validation, or demonstrated superiority to existing material-science models.')
page()
# 2 architecture
heading(1,'Research question and execution architecture')
add('The originating WP-019 research proposal asks whether mathematical formulas used during material-property symbolic-regression candidate evaluation can be represented as reusable execution graphs and independently checked. This implementation tests that numerical interface with a controlled, fully specified synthetic calculation kernel.')
figure('01_research_architecture.png','Figure 1. Dimensioned input contracts, fixed candidate grammar, persistent paceval computation graphs and independent checks.')
add('The host defines the material-like descriptor x, absolute temperature T, candidate-parameter units, fixed sample splits and candidate registry. paceval receives each approved expression and evaluates new numeric input pairs through an existing graph handle. A separate native C++ evaluator checks every scalar and batch result.')
add('<b>Boundary of responsibility.</b> paceval evaluates formulas. It does not select physical descriptors, enforce general dimensional algebra, discover equations, estimate coefficients, supply experimental labels or certify a thermodynamic model. Those functions require independent scientific software and domain review.')
page()
# 3 model contracts
heading(2,'Mathematical contracts and units')
add('The original proposal illustrates E = a + b x + c exp(-d/T). Here E is a synthetic modulus-like scalar measured in GPa, x is a dimensionless material-like descriptor and T is absolute temperature (kelvin). The parameters a, b, c and optional e are in GPa, while d is in kelvin; the literal 300 in T/300 means a fixed reference temperature of 300 K. Consequently every exponential and rational argument is dimensionless and each additive term has GPa units.')
figure('02_dimensioned_formula_families.png','Figure 2. Four approved and dimensionally balanced candidate families. These formulas are not asserted to be constitutive laws.')
add('Allowed input domain: x in [0,1], T in the deterministic range 260-890 K and d greater than zero. The constructed source family is family 0 with a = 100 GPa, b = 25 GPa, c = 18 GPa and d = 500 K. A bounded sinusoidal discrepancy is added to form synthetic observations. The generator inserts this known family as candidate 0, thus successful selection is not novel equation discovery.')
add('The dimensional contract is enforced by the fixed, approved family registry and units of its coefficients. It is not a general-purpose symbolic dimensional-analysis engine; untrusted arbitrary mathematical strings are not admitted.')
page()
# 4 data
heading(3,'Synthetic samples and fixed partitions')
add('The program creates 60 synthetic samples with a deterministic integer recurrence for x and T and a deterministic small sinusoidal additive discrepancy in GPa. The chronological order of IDs defines 36 training, 12 validation and 12 held-out test samples. This split is a fixed software-testing partition, not an independent real-material test or a benchmark-approved Matbench fold.')
figure('03_synthetic_material_samples.png','Figure 3. Synthetic material-like property versus temperature, colored by predefined research partition.')
tab([['Partition','Purpose'],['Training (36 samples)','Calculate and report training RMSE for every candidate. No coefficients are optimized.'],['Validation (12 samples)','Select the candidate with the lowest validation RMSE; candidate ID resolves exact ties.'],['Held-out test (12 samples)','Report the selected candidate test RMSE only; no reselection using test results.']])
add('No published materials dataset is included and no materials measurements are claimed. For later external validation, Matbench and NIST JARVIS-DFT offer task-specific data, but property definitions, licensing, descriptor design and original official splits must be respected.')
page()
# 5 candidates
heading(4,'Evaluation of 1,000 versioned candidates')
add('Exactly 1,000 predeclared and parameterized candidate formulas are constructed using a deterministic generator. Every candidate is created as a separate paceval computation object (handle), then evaluated on all 60 feature pairs without rebuilding its expression. For each graph, 32 additional batched values are checked using the SDK extended-result API. Each expression is also evaluated by an independently coded native function with matched mathematical semantics.')
figure('04_candidate_validation_errors.png','Figure 4. Distribution of validation errors over 1,000 candidates in the synthetic experiment. The displayed x range is limited for readability.')
add('Candidate selection uses validation RMSE, not in-sample fit or test error. Candidate 0, the intentionally supplied data-generating family, was selected. No symbolic search or coefficient-fitting algorithm is part of this release. The ranking file exposes training/validation scores and a family identifier, not an opportunistically optimized test leaderboard.')
add('A general symbolic-regression framework would require candidate enumeration or mutation, parameter estimation, constraints, search complexity penalties, cross-validation and independent checks for physical validity. This package implements the reusable candidate-evaluation stage on which such a workflow could rely.')
page()
# 6 result
heading(5,'Selected candidate and arithmetic agreement')
add('The selected candidate is formula family 0 (candidate ID 0) with the same coefficients used in generating the underlying noiseless synthetic signal. It achieved a validation RMSE of approximately 0.08605 GPa and a held-out synthetic test RMSE of approximately 0.08941 GPa. These numerical quantities describe only the engineered synthetic workload and cannot be extrapolated to materials in nature.')
figure('05_selected_predictions.png','Figure 5. Selected expression outputs against synthetic observations, with the identity line as visual reference.')
figure('06_residuals_by_split.png','Figure 6. Signed residuals for the selected candidate, displayed against fixed sample identifiers.',maxh=175)
page()
# 7 audit
heading(6,'SDK execution and independent numerical audit')
tab([['Check','Reproduced observation'],['CMake and CTest','Build succeeded; 1/1 SDK integration tests passed'],['Reusable expression graphs','1,000 created and reused'],['paceval scalar versus native C++','60,000/60,000 within 2e-9 GPa'],['paceval batch versus native C++','32,000/32,000 within 2e-9 GPa'],['Selected native output versus Decimal','60/60 within 2e-10 GPa'],['Decimal working precision','80 significant decimal digits'],['Maximum selected Decimal discrepancy',f"{float(audit['max_absolute_difference_GPa']):.3e} GPa"]])
figure('07_independent_verification.png','Figure 7. Different verification scopes. Decimal checks concern the selected candidate only.')
add('The C++ program also checks the return convention of the paceval batch API, all returned per-item error flags, finite numerical outputs and handle lifecycle. The Python Decimal oracle separately reconstructs the chosen expression from printed binary64-derived decimal strings. These finite tests do not prove arithmetic correctness for all possible inputs.')
page()
# 8 sensitivity/replication
heading(7,'Sensitivity, reproducibility and extensions')
figure('08_temperature_sensitivity.png','Figure 8. Temperature sweep of the selected synthetic formula with dimensionless descriptor fixed at x=0.5.')
add('The figure shows direct reuse of the approved expression over a temperature sweep. It does not imply thermodynamic consistency, phase behavior, stability, monotonicity in all physical regimes or an observed temperature dependence in any real material.')
add('<b>Rebuild.</b> Use <font name="DVB">cmake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so</font>, followed by <font name="DVB">cmake --build build</font> and <font name="DVB">ctest --test-dir build --output-on-failure</font>. Run <font name="DVB">./build/material_candidates --candidates 1000 --out-prefix reproduced/wp019</font> after creating that output folder. Run <font name="DVB">python3 src/high_precision_reference.py reproduced/wp019_selected.csv reproduced/audit.json</font>. Matplotlib and NumPy are needed to regenerate figures, ReportLab/Pillow to regenerate this PDF.')
add('For a future real-data study, use an exact Matbench task such as log10(K/GPa) with its official folds, document the feature-engineering pipeline, and avoid applying the synthetic modulus equations directly to incompatible logarithmic targets. Alternatively, use JARVIS-DFT with carefully specified data extraction, licensing and splits. Compare candidate ranking, dimensional consistency, out-of-domain behavior and residuals independently.')
page()
# 9 evidence / sources
heading(8,'Interpretation, limitations and references')
add('<b>Supported finding.</b> A C++ program using the original paceval C/C++ facade and a compatible Linux shared engine executed 1,000 reusable material-property candidate graphs. It verified 60,000 scalar and 32,000 batch values against native C++ formulas and independently rechecked 60 selected outputs with 80-digit decimal arithmetic. This is a successful numerical feasibility result for predefined candidate evaluation.')
add('<b>Not established.</b> This program does not discover new materials laws, identify material chemical compositions, fit coefficients, enforce a complete physics grammar, use NIST or Matbench measurements, test extrapolation on real materials, or establish physical predictiveness. No performance/processor comparisons or hardware-related advantage are reported.')
add('<b>Software provenance.</b> The supplied original paceval SDK 4.25 public facade files are included as src/paceval_main.cpp and src/paceval_main.h, with only the CPP local include path normalized. Their original copyright and AGPL notices are retained. The supplied third-party/binary shared library is used as an external dependency during research testing and is not bundled in the GitHub ZIP. Verify applicable licensing before publication or distribution.')
refs=[
('paceval mathematical engine, C/C++ API','https://paceval.com/api/'),
('paceval public source repository','https://github.com/paceval/paceval'),
('Matbench official project documentation','https://docs.materialsproject.org/services/ml-and-ai-applications/matbench'),
('Dunn et al. (2020), Matbench benchmark, npj Computational Materials','https://www.nature.com/articles/s41524-020-00406-3'),
('NIST JARVIS-DFT material property repository','https://www.nist.gov/programs-projects/jarvis-dft'),
('JARVIS-DB public download overview','https://jarvis-materials-design.github.io/dbdocs/thedownloads/'),
('Physics-guided symbolic regression in constitutive modeling (2025)','https://doi.org/10.1139/cgj-2025-0201')]
for i,(name,url) in enumerate(refs,1):story.append(P(f'{i}. <b>{name}</b><br/><font color="#168c9c">{url}</font>','note'))
add('<b>Conclusion.</b> The candidate-evaluation kernel proposed in WP-019 has been implemented, directly executed with paceval, numerically audited and packaged for independent reproduction. The result supports integration of reusable mathematical expression evaluation into a future materials symbolic-regression workflow, while leaving equation search and scientific materials validation explicitly open.')

def footer(canvas,doc):
 canvas.saveState();w,h=A4
 canvas.setStrokeColor(colors.HexColor('#dbe6e9'));canvas.line(43,39,w-43,39)
 canvas.setFont('DV',7.1);canvas.setFillColor(gray)
 canvas.drawString(43,26,'paceval. | Material Property Symbolic-Regression Candidate Evaluation | Research demonstrator | 2026')
 canvas.drawRightString(w-43,26,str(doc.page));canvas.restoreState()
doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=43,rightMargin=43,topMargin=30,bottomMargin=56,title='Material Property Symbolic-Regression Candidate Evaluation',author='paceval research demonstrator')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(target)
