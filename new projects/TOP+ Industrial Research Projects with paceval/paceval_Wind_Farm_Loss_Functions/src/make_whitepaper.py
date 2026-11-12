#!/usr/bin/env python3
"""Create the English publication PDF from the repository's checked CSV/figures.
Use after make_figures.py; reportlab and Pillow required.
"""
import argparse, csv, json
from pathlib import Path
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.')
root=Path(ap.parse_args().root).resolve(); fig=root/'figures'; ex=root/'examples'; output=root/'paceval_Wind_Farm_Loss_Functions_Whitepaper_EN.pdf'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if Path(font).exists():
    pdfmetrics.registerFont(TTFont('DV',font)); pdfmetrics.registerFont(TTFont('DV-Bold',bold)); fontname='DV'; boldname='DV-Bold'
else: fontname='Helvetica';boldname='Helvetica-Bold'
NAVY=colors.HexColor('#10314a'); CYAN=colors.HexColor('#00a7b5'); GREY=colors.HexColor('#607583'); PALE=colors.HexColor('#eef6f8'); BLUELINE=colors.HexColor('#ccdde5')
styles={
 'title':ParagraphStyle('T',fontName=boldname,fontSize=22,leading=28,textColor=NAVY,spaceAfter=9),
 'subtitle':ParagraphStyle('S',fontName=fontname,fontSize=12,leading=17,textColor=CYAN,spaceAfter=14),
 'section':ParagraphStyle('H',fontName=boldname,fontSize=15,leading=19,textColor=NAVY,spaceAfter=11),
 'sub':ParagraphStyle('H2',fontName=boldname,fontSize=10.7,leading=15,textColor=NAVY,spaceBefore=9,spaceAfter=5),
 'text':ParagraphStyle('Body',fontName=fontname,fontSize=9.1,leading=14.1,textColor=NAVY,spaceAfter=8),
 'small':ParagraphStyle('Small',fontName=fontname,fontSize=8.2,leading=12.2,textColor=GREY,spaceAfter=6),
 'caption':ParagraphStyle('Cap',fontName=fontname,fontSize=8.2,leading=11.8,textColor=GREY,spaceAfter=10),
 'mono':ParagraphStyle('Formula',fontName=fontname,fontSize=9.1,leading=15,textColor=NAVY,backColor=PALE,borderPadding=9,spaceBefore=6,spaceAfter=10),
}
D=SimpleDocTemplate(str(output),pagesize=(595.276,841.89),rightMargin=45,leftMargin=45,topMargin=53,bottomMargin=52,title='paceval | Reusable Wind-Farm Loss Functions',author='paceval research demonstrator')
usable=595.276-90
story=[]
def p(text,sty='text'):story.append(Paragraph(text,styles[sty]))
def title(t):p(t,'section')
def para(t):p(t)
def image(name,width=475):
    path=fig/name; w,h=PILImage.open(path).size
    story.append(Image(str(path),width=width,height=width*h/w))
def figure(name,caption,width=465):image(name,width);p(caption,'caption')
def page():story.append(PageBreak())
def table(rows,widths=None):
    wrapped=[[Paragraph(str(v),styles['small'] if r else styles['sub']) for v in row] for r,row in enumerate(rows)]
    t=Table(wrapped,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,0),.8,CYAN),('LINEBELOW',(0,1),(-1,-1),.3,BLUELINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.append(t);story.append(Spacer(1,10))

def frame(canvas,doc):
    canvas.setStrokeColor(BLUELINE);canvas.setLineWidth(.5);canvas.line(45,810,551,810)
    canvas.setFont(boldname,8);canvas.setFillColor(NAVY);canvas.drawString(45,817,'paceval  |  SCIENTIFIC RESEARCH DEMONSTRATOR')
    canvas.setFont(fontname,8);canvas.setFillColor(GREY);canvas.drawString(45,32,'Reusable Wind-Farm Loss Functions  |  November 2026')
    canvas.drawRightString(550,32,str(doc.page))
    canvas.line(45,43,550,43)
# 1 COVER
p('Reusable Wind-Farm Loss Functions','title')
p('A reproducible numerical demonstrator with paceval execution graphs','subtitle')
image('00_wind_farm_hero.png',500)
story.append(Spacer(1,14))
p('Research contribution','sub')
para('The WP-015 research proposal is implemented as a working C++ study of three synthetic eight-turbine wind-farm layouts. One hundred parameterized wake expressions are compiled into reusable paceval computation graphs and evaluated across 32 wind conditions per layout. Aerodynamic power is computed by an additional reused graph; numerical outputs are checked against independent C++ and high-precision references.')
table([['Study size','Verification'],['100 wake models; 3 layouts; 32 wind cases','240,000 native wake checks; 153,600 power checks'],['384 high-precision expression samples','All within specified tolerance'],['24 raw TINC interval samples','24 reference inclusions on a separate smooth control kernel']],widths=[220,285])
p('The experiment demonstrates repeatable mathematical evaluation, not independently validated wind-farm physics, site yield predictions or a claimed performance advantage.','small')
page()
# 2 SCIENTIFIC BOUNDARY
title('1. Research question and execution boundary')
para('Can many explicit wind-wake loss expressions be compiled, versioned and evaluated repeatedly while preserving known mathematical semantics and reproducible wind-farm scenarios? This demonstration answers the execution-feasibility question for a precisely defined synthetic model.')
p('What paceval executes','sub')
para('Exactly 100 parameterized nonlinear wake-deficit functions containing square roots, rational terms and exponentials are instantiated through <b>paceval_CreateComputation</b>. A separate graph evaluates cubic turbine power. Batch evaluation uses <b>paceval_dGetComputationResultExt</b>; graph deletion and runtime lifecycle use the original SDK facade.')
p('What the C++ host executes','sub')
para('The host rotates turbine coordinates into the wind direction, finds upwind/downwind pairs, applies square-sum wake superposition, computes effective rotor inflow, caps rated power, aggregates farm power and manages model versions and outputs. No hidden optimization or calibrated physical solver is claimed.')
figure('01_wind_farm_layouts.png','Figure 1. Three eight-turbine layouts in rotor-diameter units, generated directly from the source coordinates.',470)
para('The layouts are deliberately designed for a transparent mathematical comparison. Their relative losses should not be extrapolated to a real wind project.')
page()
# 3 EQUATIONS
title('2. Explicit wind-energy model')
p('Rotor power and units','sub')
p('P_raw [MW] = 0.5 * rho [kg/m3] * A [m2] * Cp * v_eff^3 / 1,000,000','mono')
para('The rotor diameter is 140 m, swept area A = pi * (70 m)^2, reference density 1.225 kg/m3, model Cp approximately 0.40 to 0.428, and the illustrative power cap is 5 MW per turbine. A bounded synthetic inflow range of 6–12 m/s is tested.')
p('Pairwise deficit function (simplified wake surrogate)','sub')
p('delta(dx,dy) = (1 - sqrt(1-Ct)) * [D/(D+2*k*dx)]^2 * exp[-0.5*(dy/(D/2+k*dx))^2]','mono')
para('Here dx is strictly positive streamwise separation, dy is signed crosswind separation, D is rotor diameter, Ct is a coefficient of turbine thrust and k is wake expansion. The equation combines a Jensen-inspired radial expansion factor with a smooth Gaussian crosswind taper; it is <b>not</b> the exact Jensen top-hat, PyWake NOJ or FLORIS Gaussian model.')
p('Superposition and delivered turbine power','sub')
p('v_eff = v_inf * max(0.20, 1 - sqrt(sum_j delta_j^2)); P = min(5 MW, P_raw)','mono')
para('The square-sum overlap rule, 20% lower inflow floor, static Ct and power cap are explicit host assumptions. The raw power loss caused by velocity deficit is accounted for by computing power from v_eff rather than by separately multiplying by another loss coefficient.')
figure('02_wake_deficit_surface.png','Figure 2. Analytical wake deficit for one selected coefficient set; not a CFD flow field or measured wake.',468)
page()
# 4 EXPERIMENT
title('3. Defined workload and versioned graphs')
table([['Component','Controlled configuration'],['Turbines and layouts','Eight turbines per layout; inline, staggered and wide-spaced'],['Wind conditions','4 free-stream speeds x 8 directions = 32 conditions'],['Graph variations','100 coefficient versions with distinct Ct and k; Cp also varies'],['Wake and power execution','Pairwise deficits, effective inflow, gross and delivered MW'],['Graph update','Model 17: Ct is changed; model 18 retained and re-evaluated unchanged']],widths=[154,352])
para('Wind conditions, rotor geometry and all formula parameters are deterministic. The experiment contains no imported SCADA or wind-resource measurements, no annual-energy extrapolation and no site-specific frequency weighting.')
figure('03_directional_wake_loss.png','Figure 3. Directional losses for a selected model at 10 m/s, calculated from published farm_results.csv.',475)
page()
# 5 QUANTITATIVE
title('4. Farm power and model sensitivity')
para('Under the deliberately simplified model, the effect of layout and prevailing direction is evident without invoking a neural network or an external CFD package. For model 0 at 10 m/s and a 0-degree wind direction, net illustrative power is 14.190 MW for inline rows, 17.747 MW for staggered turbines and 17.388 MW for the wide-spaced layout.')
figure('04_farm_power_by_wind_speed.png','Figure 4. Net farm power versus free-stream speed at 0 degrees; dashed reference is hypothetical no-wake gross power.',465)
figure('05_model_variant_sensitivity.png','Figure 5. Spread of synthetic wake losses across the 100 separately compiled parameter variations.',465)
page()
# 6 EFFECTS AND CHANGES
title('5. Per-turbine effects and controlled changes')
para('The 100 graphs are not one static formula re-evaluated 100 times. Each uses a unique coefficient set and is compiled into a distinct paceval computation handle. The mathematical kernels are then reused across all layouts, wind directions and wind speeds. Model 17 is deliberately updated to version 2 while model 18 continues unchanged.')
figure('06_turbine_inflow_comparison.png','Figure 6. Effective inflow for each of eight turbines across the three layouts at 10 m/s and 0 degrees.',462)
figure('08_model_version_update.png','Figure 7. Replacing one versioned graph changes only the targeted model; the other graph handles remain live.',462)
page()
# 7 NUMERICAL
title('6. Numerical validation and independent audit')
table([['Validation layer','Measured study result'],['Native C++ reference for wake pairs','240,000 / 240,000 within tolerance'],['Native C++ reference for cubic power','153,600 / 153,600 within tolerance'],['Independent 110-digit samples','384 / 384 within tolerance'],['Max absolute error in 384 independent samples','3.58 x 10^-16 (dimensionless or MW depending on kernel)'],['Aggregation consistency','9,600 / 9,600 farm summaries validated'],['Raw paceval TINC control intervals','24 / 24 contain the exact binary-input reference']],widths=[264,242])
para('The audit script reconstructs input doubles from their 17-digit CSV representation and computes the mathematical reference independently with mpmath (110 decimal digits). A separate smooth polynomial TINC graph cp*v^3, with dyadic binary-exact inputs, verifies 24 raw intervals. These observations do not establish universal outward-rounding or a formal bound over arbitrary input domains.')
figure('07_numerical_audit_residuals.png','Figure 8. Absolute native comparison differences in selected outputs; the plotted small offset visualizes exact-zero residuals on the logarithmic axis.',470)
page()
# 8 REPRO AND SOURCES
title('7. Reproducibility and scientific interpretation')
p('Build and execution','sub')
p('cmake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/paceval.so<br/>cmake --build build -j<br/>ctest --test-dir build --output-on-failure<br/>./build/wind_farm --variants 100 --batch 128 --out results<br/>python3 src/high_precision_reference.py results','mono')
para('The project contains src/wind_farm.cpp, src/CMakeLists.txt, the official SDK facade src/paceval_main.h/cpp, replayable input and output CSV files, high_precision_reference.py, make_figures.py and make_whitepaper.py. A compatible external Linux library is required; it is not included. The exact tested setup was Linux x86-64 with GCC 14.2 and Clang 17, alongside AddressSanitizer/UndefinedBehaviorSanitizer runs. Each compiler build passed six CTest checks.')
p('Interpretation','sub')
para('A successful mathematical graph-execution test does not validate the underlying wake model, a wind farm annual energy yield, turbulence, rotor averaging, yaw deflection, optimization or grid dispatch. The present evidence is sufficient for a controlled proof of repeatable mathematical loss-function evaluation. An independent PyWake/FLORIS model and site observations would be necessary for an application-level physics comparison.')
p('Selected sources','sub')
for item in [
 '1. paceval C/C++ mathematical engine and examples: https://github.com/paceval/paceval',
 '2. DTU PyWake engineering wind farm models, including NOJ/Jensen: https://topfarm.pages.windenergy.dtu.dk/pywake/api/PredefinedEngineeringWindFarmModels.html',
 '3. DTU PyWake wake superposition methods: https://topfarm.pages.windenergy.dtu.dk/pywake/notebooks/SuperpositionModels.html',
 '4. NREL FLORIS wind farm modeling tutorial: https://www.nrel.gov/docs/libraries/wind-docs/systems-engineering-workshop-2019-floris.pdf',
 '5. Source proposal: WP_015_Reusable_Wind_Farm_Loss_Functions.pdf (not republished in this GitHub package).'
]:p(item,'small')
p('Publication statement','sub')
para('No execution-time comparisons, energy savings, customer benefits or turbine farm forecasts are asserted. This report describes a tested synthetic research demonstrator using a controlled explicit mathematical model. Original SDK license notices are preserved; use of the external runtime remains subject to its own terms.')
D.build(story,onFirstPage=frame,onLaterPages=frame)
print('Created',output)
