#!/usr/bin/env python3
"""Generate the eleven-page research PDF from verified data and scientific images."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
R=Path(__file__).resolve().parents[1]
OUTPUT=R/'paceval_Quality_Scrap_Scores_Whitepaper_EN.pdf'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('QRegular',FONT));pdfmetrics.registerFont(TTFont('QBold',BOLD))
W,H=A4; NAVY=HexColor('#152F46'); TEAL=HexColor('#138B9A'); DARK=HexColor('#283747'); GREY=HexColor('#657888'); LIGHT=HexColor('#EAF3F4')
c=canvas.Canvas(str(OUTPUT),pagesize=A4);c.setTitle('paceval | Mathematical Quality and Scrap Scores | Scientific Research Report')
styles={
 'body':ParagraphStyle('body',fontName='QRegular',fontSize=9.1,leading=15,textColor=DARK,spaceAfter=0),
 'small':ParagraphStyle('small',fontName='QRegular',fontSize=8.0,leading=12.5,textColor=DARK),
 'note':ParagraphStyle('note',fontName='QRegular',fontSize=8,leading=12.5,textColor=GREY),
 'bullet':ParagraphStyle('bullet',fontName='QRegular',fontSize=8.7,leading=15,textColor=DARK),
}
page=0

def new_page(section=None):
 global page
 if page:c.showPage()
 page+=1;c.setFillColor(NAVY);c.setFont('QBold',8.5);c.drawString(44,H-34,'PACEVAL | INDUSTRIAL MATHEMATICAL RESEARCH')
 c.setStrokeColor(TEAL);c.setLineWidth(1.1);c.line(44,H-43,W-44,H-43)
 c.setStrokeColor(HexColor('#D5E2E5'));c.line(44,46,W-44,46)
 c.setFont('QRegular',7.2);c.setFillColor(GREY);c.drawString(44,32,'paceval | Mathematical Quality and Scrap Scores | November 2026')
 c.drawRightString(W-44,32,str(page))
 if section:c.setFillColor(NAVY);c.setFont('QBold',16);c.drawString(44,H-82,section)
 return H-104 if section else H-65

def p(txt,y,style='body',width=W-88):
 para=Paragraph(txt,styles[style]);ww,hh=para.wrap(width,800)
 if y-hh<68:raise RuntimeError('PDF content overflow: page %s, y=%s'%(page,y))
 para.drawOn(c,44,y-hh);return y-hh-13

def head(txt,y):
 c.setFont('QBold',11.5);c.setFillColor(TEAL);c.drawString(44,y,txt);return y-20

def image(stem,y,height=305):
 path=R/'figures'/(stem+'.png');im=Image.open(path);iw,ih=im.size
 width=min(W-96,height*iw/ih);actual_h=width*ih/iw
 if actual_h>height:actual_h=height;width=actual_h*iw/ih
 if y-actual_h<73:raise RuntimeError('Image overflow page %s'%page)
 c.drawImage(str(path),(W-width)/2,y-actual_h,width,actual_h,mask='auto')
 return y-actual_h-11

def caption(text,y):return p('<i>'+text+'</i>',y,'note')

def rows(items,y):
 for k,v in items:
  c.setFillColor(LIGHT if int(y)//29%2==0 else HexColor('#F8FAFB'));c.roundRect(44,y-26,W-88,28,3,fill=1,stroke=0)
  c.setFillColor(DARK);c.setFont('QRegular',8.6);c.drawString(54,y-17,k);c.setFont('QBold',8.6);c.drawRightString(W-54,y-17,str(v));y-=29
 return y-11

new_page()
y=H-81;c.setFillColor(TEAL);c.setFont('QBold',10);c.drawString(44,y,'SCIENTIFIC RESEARCH REPORT | WP_027');y-=52
c.setFillColor(NAVY);c.setFont('QBold',23);c.drawString(44,y,'Mathematical Quality');y-=31;c.drawString(44,y,'and Scrap Scores');y-=27
y=p('Reusable mathematical execution graphs for industrial process-quality monitoring and controlled inspection routing',y,'body')
# Distinct industrial photorealistic cover artwork
path=R/'figures/00_quality_hero.png';im=Image.open(path);rw=W-88;rh=rw*im.height/im.width;c.drawImage(str(path),44,y-rh,rw,rh);y-=rh+23
y=head('Verified research outcome',y)
y=p('<b>50</b> versioned score definitions; <b>51</b> retained paceval computation graphs; <b>10,000</b> deterministic synthetic observations; <b>13,843</b> scalar evaluations; <b>1,600</b> batch checks; <b>3,721</b> 3D surface values. Independent numerical samples passed the declared audit. No real-plant yield or calibrated scrap-risk claim is made.',y)
y=p('Cover image: conceptual rendering of automated inspection. Scientific figures in the following pages use actual paceval-generated numerical datasets.',y,'note')

new_page('1. Industrial use case and state of the art');y=H-105
y=p('Industrial quality engineering seeks to detect nonconforming manufacturing conditions before material progresses downstream. In an automated machining or semiconductor process, temperature, pressure, speed, vibration, and wear may vary across time and products. Engineers combine statistical process control, product specifications, sensor validity checks, predictive models, and inspection policies. A mathematical quality score can organize the evaluation, but cannot by itself certify quality or identify physical defects.',y)
y=head('Concrete application scenario',y)
y=p('A hypothetical manufacturing cell continuously produces five normalized sensor deviations. For each item, a registered score rule generates a dimensionless risk proxy. An independent host policy routes a score of at least 0.60 to additional inspection. The inspection flag is not an automatic scrap decision. Technical validation, safety permissions, and product conformance decisions remain external to the formula engine.',y)
y=head('Research context and alternatives',y)
y=p('The UCI SECOM collection is an example of manufacturing pass/fail records with hundreds of sensor variables and missing observations. AI4I 2020 contains 10,000 deliberately synthetic machine-operating records and machine-failure labels, not manufactured-part scrap labels. Neither external dataset was used to generate the numerical results in this paper. Industry-grade use requires leakage-resistant validation, measurement-system analysis, uncertainty treatment, class-imbalance handling and observed quality outcomes.',y)
y=head('Research question',y)
y=p('Can fifty different, explicitly versioned mathematical scoring rules be executed and repeatedly reused through persistent paceval computation graphs, integrated with an inspection-routing host, and subjected to independent numerical verification using deterministic synthetic inputs?',y)
y=p('The study answers that bounded execution question. It does not assess manufacturing model calibration or real scrap-reduction effectiveness.',y,'note')

new_page('2. Mathematical definition and model scope');y=H-105
y=p('Let <b>t, p, s, v, w</b> denote dimensionless standardized process deviations for temperature, pressure, rotational speed, vibration, and tool wear. The explicit demonstration input contract is [-2,2] per component; the generated records occupy [-1.6,1.6]. For each registered model, a nonlinear latent score is transformed by a logistic function.',y)
y=head('Common logistic transformation',y)
y=p('<font color="#138B9A"><b>S = 1 / (1 + exp(-z))</b></font>. The output lies between 0 and 1 for finite valid inputs. That range alone does not establish probabilistic calibration.',y)
y=head('Five family-level nonlinear expressions',y)
y=p('Family 1: z = a*t + b*p + c*s + 0.35*v + 0.25*w.',y)
y=p('Family 2: z = a*t² + b*p² + c*s² + 0.30*v - 0.70.',y)
y=p('Family 3: z = a*t*p + b*s*v + c*w + 0.12*t² - 0.15.',y)
y=p('Family 4: z = a*sin(t) + b*cos(p) + c*s*w + 0.30*v.',y)
y=p('Family 5: z = a*ln(1+t²) + b*sqrt(1+p²) + c*v*w + 0.15*s - 0.45.',y)
y=p('Ten declared coefficient choices (a,b,c) per family yield fifty distinct expressions. A separately registered version of family 1 modifies coefficient a without replacing the previous paceval handle. Exact expression strings and coefficient values are published in examples/score_registry.csv.',y)
y=head('Decision function is owned by the C++ host',y)
y=p('For a score S, inspect(S) = 1 when S is at least 0.60, and 0 otherwise. This value is an illustrative process-routing threshold, not an optimized or validated industrial release criterion. The host validates input ranges, manages synthetic labels, routes decisions, and writes the audit records.',y)

new_page('3. paceval execution architecture');y=H-105
y=p('The original paceval_main.h and paceval_main.cpp facade is built with C++17 and linked to a separately supplied compatible Linux runtime. No substitute mathematical engine is included. Graphs are registered once and reused across multiple input vectors.',y)
y=head('Verifiable software boundaries',y)
y=rows([('Persistent graph creation','paceval_CreateComputation'),('Scalar mathematical evaluation','paceval_dGetComputationResult'),('Packed batch evaluation','paceval_dGetComputationResultExt'),('Graph destruction','paceval_DeleteComputation'),('Library lifecycle','InitializeLibrary / FreeLibrary')],y)
y=head('Controlled change management',y)
y=p('A 51st computation graph is created from a changed coefficient of family 1. The original graph remains present and callable. This demonstrates the separation between changing an input value and creating a new expression version. Formula strings are externally inspectable rather than silently replaced.',y)
y=head('Independent application-layer controls',y)
y=p('C++ generates deterministic records using a fixed integer seed, checks finite normalized input domains, selects the registered model, applies the inspection threshold, and records the synthetic observation and label. Pointwise evaluation is not a proof of a score model over every possible input, and no paceval interval certification is asserted.',y)

new_page('4. Executed deterministic workload');y=H-105
y=p('The executed experiments use 10,000 synthetic five-feature observations and fifty independently declared formulas. An additional 61-point comparison of two persistent formula versions demonstrates update traceability. An independently generated synthetic defect-label mechanism is not trained on any score model.',y)
y=rows([('Distinct mathematical score definitions','50'),('Persistent graphs including formula version 2','51'),('Synthetic observations','10,000'),('Scalar paceval mathematical evaluations','13,843'),('Verified packed batch results','1,600'),('Three-dimensional surface values','3,721'),('Independent 80-digit reference checks','500 / 500 PASS'),('SDK integration CTest','1 / 1 PASS')],y)
y=head('Published research evidence',y)
y=p('The accompanying machine-readable files preserve registry formulas, input features, scores, routing decisions, surface points, model-version trajectories, SDK execution records, and independent audit reports. The samples are a deliberately limited mathematical execution benchmark and do not represent measured manufacturing yield.',y)

new_page('5. Inspection decisions and score families');y=H-105
y=p('Across 10,000 synthetic observations, 2,046 exceed the demonstration threshold and are routed to inspection. Separately, 3,710 observations have a synthetic positive defect label created using an independent data-generation mechanism. These are not industrial production quantities.',y)
y=image('03_inspection_by_model',y,295)
y=caption('Figure 3. Fraction of synthetic records flagged for inspection for each of fifty registered paceval score formulas.',y)
y=image('04_family_profile',y,235)
y=caption('Figure 4. Inspection decisions by formula family and the independently generated synthetic labels.',y)

new_page('6. Process-score distribution');y=H-105
y=p('The distribution of computed scores and the threshold-based routing profile illustrate how different mathematical forms lead to different inspection workloads. No inference about actual part quality is justified without production-labeled calibration and validation.',y)
y=image('02_score_distribution',y,325)
y=caption('Figure 2. Distribution from 10,000 actual paceval score outputs; the dashed line is the declared inspection threshold.',y)
y=image('01_executed_scope',y,240)
y=caption('Figure 1. Numbers of executed graphs, process observations, tested packed evaluations, and surface samples.',y)

new_page('7. Three-dimensional quality-score surface');y=H-105
y=p('A fixed version of formula family 1 is evaluated on a 61-by-61 grid of temperature and pressure deviations with other inputs fixed. The surface is constructed from 3,721 actual paceval mathematical results, not a generated numerical illustration.',y)
y=image('05_quality_surface_3d',y,410)
y=caption('Figure 5. Reusable logistic response surface for two normalized process features, evaluated through paceval.',y)
y=p('The plot is a sensitivity illustration for an uncalibrated synthetic model; it is not a manufacturing process-window specification.',y,'note')

new_page('8. Contours and formula revision');y=H-105
y=p('The contour map projects the same paceval score surface into two dimensions. Such graphics could help engineers inspect the internal behaviour of a controlled formula before it is considered for a product-specific quality workflow.',y)
y=image('06_quality_contours',y,290)
y=caption('Figure 6. Process-operating contour map of the evaluated mathematical surface.',y)
y=image('07_versioned_scores',y,240)
y=caption('Figure 7. Immutable original graph and a separately registered second formula version.',y)

new_page('9. Interpretability and limitations');y=H-105
y=p('The synthetic label-generation function differs from the fifty tested score models. Consequently, diagnostic agreement between scores and synthetic labels must not be interpreted as a fitted model performance result. A score bounded by zero and one is not automatically a probability.',y)
y=image('08_label_diagnostics',y,330)
y=caption('Figure 8. Exploratory label frequency by score bin. The diagnostic explicitly does not establish calibration.',y)
y=head('Scope of the research conclusion',y)
y=p('Successfully demonstrated: mathematical graph construction, repeated evaluation of five nonlinear families, persistent expression versioning, packed batch calls, auditable decisions, reproducible CSV exports, and an independent numerical audit. Not established: predictive manufacturing quality, measurement traceability, site-specific scrap reduction, financial savings, robust handling of missing real sensors, or production certification.',y)

new_page('10. Reproducibility and external references');y=H-105
y=head('Build and verification',y)
y=p('Build from src/CMakeLists.txt with the C++17 compiler, CMake and an externally provided ABI-compatible paceval Linux shared library; run the quality_scores executable with --out; execute CTest. The project includes Python verification scripts, a high-precision reference, figure rendering, and a README mathematics and local-link checker.',y)
y=head('Included project evidence',y)
y=p('The project-root README provides exact commands and relative links. Data: examples/score_registry.csv, quality_records.csv, quality_surface.csv, score_summary.csv and formula_versions.csv. Audits: results/sdk_execution.txt, ctest_sdk.txt, decimal_audit.json and result_audit.json. Graphics: eight numbered pairs of PNG and vector-PDF files.',y)
y=head('Selected scientific and technical references',y)
y=p('1. UCI Machine Learning Repository. SECOM manufacturing dataset. https://archive.ics.uci.edu/dataset/179/secom',y,'small')
y=p('2. UCI Machine Learning Repository. AI4I 2020 Predictive Maintenance Dataset, DOI: 10.24432/C5HS5C. Synthetic machine-failure observations; CC BY 4.0.',y,'small')
y=p('3. NIST Engineering Laboratory, manufacturing measurement and process engineering context. https://www.nist.gov/el',y,'small')
y=p('4. paceval Mathematical Engine C/C++ API documentation. https://paceval.com/api/',y,'small')
y=head('Conclusion',y)
y=p('The executed synthetic research demonstrator confirms that reusable paceval mathematical graphs can power a versioned catalogue of nonlinear manufacturing quality scores in a controlled C++ application. The work substantiates mathematical execution functionality while preserving a clear boundary between numeric scoring and industrial quality validation.',y)
c.save();print('Created',OUTPUT,'pages:',page)
