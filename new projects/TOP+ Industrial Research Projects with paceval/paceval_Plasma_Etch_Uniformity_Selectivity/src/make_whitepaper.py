#!/usr/bin/env python3
"""Generate the publishable English PDF from recorded genuine paceval results."""
from pathlib import Path
from xml.sax.saxutils import escape
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,Table,TableStyle,KeepTogether,HRFlowable
root=Path(__file__).resolve().parents[1];F=root/'figures';R=root/'results'
OUT=root/'paceval_Plasma_Etch_Uniformity_Selectivity_Whitepaper_EN.pdf'
e=json.loads((R/'execution_evidence.json').read_text());audit=json.loads((R/'independent_reference_audit.json').read_text());summ=pd.read_csv(R/'recipe_summary.csv')
fonts='/usr/share/fonts/truetype/dejavu/'
for name,file in [('DV','DejaVuSans.ttf'),('DVB','DejaVuSans-Bold.ttf'),('DVI','DejaVuSans-Oblique.ttf')]:pdfmetrics.registerFont(TTFont(name,fonts+file))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DVI',boldItalic='DVB')
NAVY=HexColor('#18314c');PURPLE=HexColor('#634d9d');CYAN=HexColor('#0c9aaf');GRAY=HexColor('#5f6f7c');MUTED=HexColor('#e9f2f6');LIGHT=HexColor('#f7fafc')
styles={
 'over':ParagraphStyle('over',fontName='DVB',fontSize=9,leading=14,textColor=CYAN,spaceAfter=8),
 'title':ParagraphStyle('title',fontName='DVB',fontSize=21.7,leading=28,textColor=NAVY,spaceAfter=11),
 'subtitle':ParagraphStyle('subtitle',fontName='DV',fontSize=10.6,leading=17,textColor=GRAY,spaceAfter=13),
 'h1':ParagraphStyle('h1',fontName='DVB',fontSize=15.7,leading=21,textColor=NAVY,spaceAfter=10),
 'h2':ParagraphStyle('h2',fontName='DVB',fontSize=10.6,leading=16,textColor=PURPLE,spaceBefore=8,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='DV',fontSize=8.85,leading=14.1,textColor=NAVY,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='DV',fontSize=8.0,leading=12.5,textColor=NAVY,spaceAfter=7),
 'caption':ParagraphStyle('caption',fontName='DVI',fontSize=7.75,leading=11.2,textColor=GRAY,spaceAfter=10),
 'tiny':ParagraphStyle('tiny',fontName='DV',fontSize=7.25,leading=10.8,textColor=GRAY,spaceAfter=4),
 'table':ParagraphStyle('table',fontName='DV',fontSize=7.6,leading=10.6,textColor=NAVY,spaceAfter=0),
}
doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=18.5*mm,rightMargin=18.5*mm,topMargin=17*mm,bottomMargin=19*mm,title='Semiconductor Plasma Etch Uniformity and Selectivity Mapping with paceval',author='paceval Industrial Research',subject='Genuine execution of versioned synthetic wafer etch process expressions with the original paceval SDK')
W=A4[0]-37*mm
story=[]
def p(s,sty='body'):story.append(Paragraph(s,styles[sty]))
def head(s):p(s,'h1')
def sub(s):p(s,'h2')
def pb():story.append(PageBreak())
def sp(mmval=3):story.append(Spacer(1,mmval*mm))
def picture(filename,wmm=157,hmax=85,caption=None):
 full=F/filename
 with PILImage.open(full) as im:ow,oh=im.size
 w=wmm*mm;h=w*oh/ow
 if h>hmax*mm:h=hmax*mm;w=h*ow/oh
 things=[Image(str(full),width=w,height=h,hAlign='CENTER')]
 if caption:things.append(Paragraph(caption,styles['caption']))
 story.append(KeepTogether(things))
def table(headings,rows,widths=None):
 data=[[Paragraph(escape(str(x)),styles['table']) for x in headings]]+[[Paragraph(escape(str(x)),styles['table']) for x in row] for row in rows]
 t=Table(data,colWidths=widths if widths else [W/len(headings)]*len(headings),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),MUTED),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),1,CYAN),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,LIGHT]),('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7)]))
 story.append(t)
def eq(key,expr,width=151):
 fig=plt.figure(figsize=(10.5,.82),facecolor='white');fig.text(.03,.48,'$'+expr+'$',fontsize=18,va='center',ha='left',color='#18314c');fig.savefig(F/f'_equation_{key}.png',dpi=180,transparent=True,bbox_inches='tight',pad_inches=.1);plt.close(fig)
 picture(f'_equation_{key}.png',width,23)
def footer(canv,d):
 canv.saveState();width,height=A4;canv.setStrokeColor(HexColor('#ccdbe5'));canv.line(18.5*mm,15.0*mm,width-18.5*mm,15.0*mm)
 canv.setFillColor(GRAY);canv.setFont('DV',7);canv.drawString(18.5*mm,10.3*mm,'paceval | Semiconductor Plasma Etch Research | 14 November 2026');canv.drawRightString(width-18.5*mm,10.3*mm,str(d.page));canv.restoreState()

# Page 1: cover
p('paceval.  |  INDUSTRIAL RESEARCH','over')
p('Programmable Plasma Etch Uniformity and Selectivity Mapping','title')
p('Reusing mathematical execution graphs for wafer-scale film etch rates, mask selectivity, spatial uniformity, process sensitivities and constrained recipe evaluation','subtitle')
picture('00_plasma_etch_hero.png',170,85,'Concept illustration. Not a photograph of an industrial process or a computed wafer map.')
sub('Research outcome')
p(f"A genuine C++ demonstrator linked to the original paceval SDK 4.25 created and executed <b>{e['unique_graphs_executed']} persistent mathematical graphs</b>. Two controlled model versions evaluated <b>{e['recipe_count']} synthetic recipe candidates</b> at <b>{e['wafer_points_per_recipe']:,} equal-area wafer points each</b>, yielding <b>{e['total_model_point_rows']:,} model-point records</b>. Model-specific etch-rate, selectivity and compositional quality outputs passed independent analytic, aggregation and high-precision verification.")
p('This research establishes the feasibility of reusable mathematical function execution for the stated synthetic surrogate. It does not represent calibrated chamber physics, measured wafers, industrial safety certification or an approved fab process.','small')
pb()
# Page 2
head('1. Industrial use case and current state of the art')
p('Plasma etching is used to remove precisely controlled layers in semiconductor manufacturing. Reactive gas species and energetic ions interact with the wafer surface, while chamber pressure, electrode temperature, bias and gas chemistry influence the etch rate and resulting feature geometry. An engineer must balance the desired film removal against protective-mask erosion and variation between wafer positions. A nominal average etch rate alone is insufficient because excessive local removal or mask depletion can make a recipe unacceptable.')
p('In an industrial workflow, process engineers select a recipe, run test wafers, measure film steps and features, identify within-wafer gradients, then revise pressure, temperature or gas and bias conditions. A mathematical wafer-response model can help organize these alternatives and their associated quality rules. This study investigates a reusable mathematical execution layer for that workflow; it does not simulate plasma discharge or claim process qualification.')
sub('Recent research and industrial context')
p('NIST documents inductively coupled plasma (ICP) etchers with a temperature-controlled electrode, multiple reactive gases, controlled ion bombardment and substrates up to 200 mm [1]. The NIST Dektak XT contact profilometer provides one concrete example of measuring etch steps, thickness and mapped surface features [2]. A 2025 review of III-V plasma etching describes coupled effects of pressure, gas chemistry, source/bias power and temperature on rate, selectivity and aspect ratio [3]. A 2026 study examines the wafer-edge ion environment produced by focus-ring geometry [4]. Multi-objective plasma process modeling was also investigated in 2024 [5]. None of these published findings establishes the accuracy of our chosen surrogate.')
picture('01_architecture.png',161,69,'Figure 1. Executed architecture represented as a conceptual workflow: persistent paceval mathematical stages with host-managed wafer data and aggregation.')
pb()
# Page 3
head('2. Research question and mathematical approach')
p('The central question is whether two independently registered sets of mathematical expressions can produce complete wafer-scale response fields and downstream quality rules without moving the important arithmetic back into C++. Every recipe contains electrode temperature, pressure, normalized chemistry and bias indices, etch duration, target depth, initial film/mask thickness and numerical quality requirements. Every wafer point uses normalized Cartesian coordinates in the unit disk, generated deterministically on an equal-area polar grid.')
sub('Rate surrogate for film and mask')
eq('film',r'r_f(x,y)=A_f e^{-E_f/(R_g T)}(p/p_0)^{\alpha_f}\,G_f(b,c)\,S_f(x,y)')
eq('mask',r'r_m(x,y)=A_m e^{-E_m/(R_g T)}(p/p_0)^{\alpha_m}\,G_m(b,c)\,S_m(x,y)')
p('The scale coefficients, activation terms and power exponents are deliberately synthetic. The rate unit is nm/min and temperature is kelvin. Version v1 uses a quadratic spatial response with mild asymmetry; version v2 changes coefficients and adds a localized smooth radial-ring contribution. Both functions remain positive in the declared experimental domain. These are not plasma chemical kinetics or model parameters fitted to a commercial machine.')
sub('Spatial and material-level quantities')
eq('sel',r'S=\frac{r_f}{\max(r_m,\epsilon)},\quad d_f=t_e r_f,\quad M=M_0-t_e r_m')
eq('delta',r'\delta(x,y)=\frac{r_f(x,y)-r_f(0,0)}{r_f(0,0)}')
p('The mask-rate regularizer is a defined lower bound and does not substitute for checking input domains. Compound process constraints use threshold margins and Boolean 0/1 results. The complete expressions and their identifiers are stored as machine-readable source-independent text in graph_registry.csv.')
pb()
# Page 4
head('3. Mapping uniformity, selectivity and valid process windows')
p('The experiment records local film and mask etch rates, geometric gradients, pressure and temperature derivatives, etch depth, mask erosion and remaining layer thickness for both versions. A useful distinction is local deviation from the center and a global wafer nonuniformity statistic. We report the latter explicitly as the max/min rate spread divided by twice the area mean rate. Other definitions, including standard-deviation-based uniformity, exist; the coefficient of variation is reported separately.')
eq('nu',r'\mathrm{NU}_{\%}=100\frac{r_{\max}-r_{\min}}{2\,\overline{r}},\qquad \mathrm{CV}_{\%}=100\frac{\sigma_r}{\overline{r}}')
p('Mathematical gates combine a target-depth tolerance, a minimum selectivity, a minimum remaining-mask thickness, a local rate-deviation bound and a composite quality score. The host interprets the resulting mathematical outputs in terms of synthetic candidate states. ACCEPT, REVIEW and REJECT are not equipment safety decisions.')
sub('Functional ownership and audit scope')
table(['Role','Actual execution'],[
 ['paceval graph stage A','Film/mask rate, center rate, spatial gradient, temperature/pressure/chemistry derivatives'],
 ['paceval graph stage B','Film depth, erosion, residuals, quality score, selectivity and combined Boolean guards'],
 ['paceval summary graphs','Normalize aggregate max/min, mean and coefficient-of-variation statistics'],
 ['C++ host','Wafer sampling, version lifecycle, cross-point aggregation, data validation and CSV writing'],
 ['Independent Python','Separate NumPy and 80-decimal-place mpmath scientific audit only']],[W*.31,W*.69])
pb()
# Page 5
head('4. Actual paceval execution and scope of the workload')
p('Every mathematical graph was created once and reused over many independent input vectors. Each model has 8 upstream graphs and 20 dependent graphs. Three additional graphs normalize wafer summary statistics, for a total of 59 distinct graphs. The genuine multi-computation batch interface was used in both mathematical stages. C++ transfers computed values between the graphs and collects cross-wafer summaries, but does not recompute the published per-position film and mask mathematics.')
table(['Verified count','Executed experiment'],[
 ['Controlled formula versions','2 simultaneously retained graph families'],
 ['Synthetic operating recipes',str(e['recipe_count'])],
 ['Wafer sample positions per recipe',f"{e['wafer_points_per_recipe']:,}"],
 ['Model-point output rows',f"{e['total_model_point_rows']:,}"],
 ['Distinct executed paceval graphs',str(e['unique_graphs_executed'])],
 ['Successful multi-graph batch calls',f"{e['batch_calls']:,}"],
 ['Graph-point values computed by paceval',f"{e['graph_point_evaluations']:,}"],
 ['Independently checked scalar values',f"{audit['elementwise_function_checks']:,}"],
 ['Independently checked summary metrics',f"{audit['summary_checks']:,}"],
 ['High-precision reference quantities',f"{audit['high_precision_80_digit_values']:,}"],
 ],[W*.52,W*.48])
p('Every registered graph is represented in the formula inventory and the archived execution evidence. A created handle is not counted as executed unless it appears in the real production calculation path. Repeated verification runs are tracked independently and not silently added to this experiment. The study is a functionality demonstration and does not publish CPU, GPU, FPGA or C++ speed comparisons.')
pb()
# Page 6
head('5. Wafer-scale film etch-rate fields')
p('The two versioned models produce related, but numerically distinct spatial fields for the same synthetic recipe. The plots below come directly from the actual paceval CSV results and represent normalized wafer coordinates rather than measured industrial wafers.')
picture('02_film_rate_v1.png',137,78,'Figure 2. v1 film rate for synthetic recipe 15, with a smooth asymmetric quadratic spatial response.')
picture('03_film_rate_v2.png',137,78,'Figure 3. v2 film rate for the same recipe, including the additional smooth localized radial feature.')
pb()
# Page 7
head('6. Selectivity and spatial uniformity')
p('Film-to-mask etch selectivity can change over the same wafer even when the film rate is positive everywhere. A geometric average can therefore conceal local risks. The following two maps are created by the paceval rate and derived-selectivity graph chain for recipe 15, version 2.')
picture('04_selectivity_v2.png',136,78,'Figure 4. Spatially varying selectivity in the synthetic model. Higher values correspond to more film removal per unit mask loss.')
picture('05_local_uniformity.png',136,78,'Figure 5. Local rate deviation from the model center, not the global wafer nonuniformity statistic.')
pb()
# Page 8
head('7. Three-dimensional rate surface and radial structure')
p('A full wafer map can be examined as a spatial surface or grouped into radius-based profiles. The first representation shows azimuthal and radial variation together. The second reveals the angular spread within each radial ring and how it changes between formula versions. Both are graphical representations of recorded paceval rate values.')
picture('08_3d_film_rate.png',147,100,'Figure 6. A three-dimensional plot of the actually evaluated film rate, recipe 15, model v2.')
picture('09_radial_profile.png',143,77,'Figure 7. Mean film rate by radius, with colored angular minimum-to-maximum ranges, for two versions of recipe 15.')
pb()
# Page 9
head('8. Recipe response and wafer-level statistics')
p('The 25 recipe candidates vary electrode temperature, chamber pressure, bias/chemistry indices and etch duration within declared synthetic ranges. Each candidate produces 4,096 spatial data points for each version. Global summary calculations use the original paceval graph outputs. The final normalization of global nonuniformity, coefficient of variation and mean rate is itself executed through dedicated paceval summary graphs.')
picture('10_recipe_response.png',155,92,'Figure 8. Model-dependent mean etch rate across the 25 synthetic recipe candidates; color denotes the recorded electrode temperature.')
picture('14_uniformity_summary.png',155,79,'Figure 9. Area-weighted within-wafer coefficient of variation for both models. The effect arises from the defined versioned spatial response.')
pb()
# Page 10
head('9. Version-dependent quality decisions')
p('For recipe 15, the computed area-mean film etch rate is <b>%.3f nm/min</b> in v1 and <b>%.3f nm/min</b> in v2. The corresponding selectivity means are <b>%.3f</b> and <b>%.3f</b>, respectively. Both models pass the deliberately hypothetical complete quality rule at all 4,096 positions for this particular recipe. Other recipe-version pairs fail the rule partially or completely. This is an internal constraint-system test, not a statement about actual process yield.'%(summ[(summ.recipe==15)&(summ.version==1)].iloc[0].meanFilmRateNmPerMin,summ[(summ.recipe==15)&(summ.version==2)].iloc[0].meanFilmRateNmPerMin,summ[(summ.recipe==15)&(summ.version==1)].iloc[0].meanSelectivity,summ[(summ.recipe==15)&(summ.version==2)].iloc[0].meanSelectivity))
picture('11_acceptance_coverage.png',159,91,'Figure 10. Percentage of synthetic wafer sites satisfying all declared graph-based quality predicates, by recipe and version.')
picture('15_recipe_tradeoff.png',149,77,'Figure 11. Modelled depth/selectivity trade space; marker sizes reflect the fraction of accepted wafer locations.')
pb()
# Page 11
head('10. Explicit parameter sensitivities')
p('The model includes analytic derivatives with respect to normalized Cartesian wafer coordinates, pressure, temperature and the synthetic chemistry index. The derivatives are expressed as independent, persistent paceval formulas rather than being generated through a hypothetical automatic differentiation facility. Their mathematical definitions are separately checked using the independent reference model.')
picture('12_sensitivity_maps.png',163,85,'Figure 12. Wafer maps of the temperature and pressure sensitivities of the film etch rate, recipe 15, v2.')
picture('13_model_revision.png',140,80,'Figure 13. The change in film etch rate when the same synthetic recipe is evaluated using v2 rather than v1.')
pb()
# Page 12
head('11. Mask protection and composite quality maps')
p('The film etch depth and protective-mask loss are linked through the same modeled recipe conditions but have distinct spatial maps and material parameters. The synthetic decision model combines film removal, mask protection and selectivity into a continuously valued quality score, a signed quality margin and a relational/logical gate.')
picture('07_mask_remaining.png',144,77,'Figure 14. Computed remaining mask thickness after the specified recipe time, model v2, recipe 15.')
picture('06_quality_map.png',144,77,'Figure 15. The composed continuous quality score evaluated by paceval on the same wafer. Units are dimensionless; thresholds are hypothetical.')
pb()
# Page 13
head('12. Independent validation and numerical boundaries')
p('The independent verification program reconstructs the film and mask rate laws as its own NumPy calculations, without reading or evaluating paceval formula strings. It then verifies 22 pointwise mathematical result quantities over the full published dataset, including derivatives, material selectivity, depth, margins and all Boolean results. It separately reconstructs all 500 wafer summary values. A deterministic selection additionally receives 80-digit mpmath validation. The detailed numerical audit is stored in results/independent_reference_audit.json rather than presented as an engine-accuracy competition.')
table(['Check','Result'],[
 ['Independent pointwise mathematical checks',f"{audit['elementwise_function_checks']:,} passed"],
 ['Independent aggregated wafer metrics',f"{audit['summary_checks']:,} passed"],
 ['Independent 80-decimal-place values',f"{audit['high_precision_80_digit_values']:,} passed"],
 ['Boolean quality categories','All recorded pointwise outcomes matched the independent model'],
 ['Input and output conversions','Original paceval double/string conversion functions tested'],
 ],[W*.52,W*.48])
sub('Scope and validity')
p('The test is restricted to a deterministic, smooth, positive and numerically well-behaved synthetic function family. It does not test a calibrated plasma model, microscopic etch physics, sidewall damage, microloading, pattern-density dependence, chemical kinetics, experimentally qualified hard masks, long-run drift or certified intervals. Actual manufacturing requires equipment-specific qualification, independent measurement maps and process-safety review. The public results should never be used for autonomous manufacturing actuation.')
pb()
# Page 14
head('13. Reproduction and further industrial research')
p('The deliverable includes the complete C++ program, official paceval source adapter, formula inventories, original scientific proposal, 204,800 published point rows, recipe summaries, sample decision traces, high-precision validation code and every visualization script. The external compatible paceval binary is intentionally not redistributed. Use the original shared library and invoke:')
p('<font face="DVB">cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval.so</font>','small')
p('<font face="DVB">cmake --build build -j</font>','small')
p('<font face="DVB">ctest --test-dir build --output-on-failure</font>','small')
p('<font face="DVB">./build/plasma_etch --run --recipes 25 --radial 64 --angular 64 --out results/reproduced</font>','small')
p('<font face="DVB">python3 src/verify_reference.py results/reproduced</font>','small')
p('A future industrial pilot would replace synthetic coefficients with a fitted model using real measured etch depths and rates across wafer locations, hold out whole wafers or operating time intervals, and quantify physical errors and model drift. More detailed etch physics and experimentally measured selectivity may then be introduced, while retaining reusable graph versioning and process-rule definitions. This proposed next step is not part of the completed experiment.')
sub('References')
refs=[
 '[1] NIST NanoFab, Oxford PlasmaPro 100 ICP III-V etcher. https://www.nist.gov/laboratories/tools-instruments/nanofab-tool-oxford-plasmapro-100-inductively-coupled-plasma-icp-iii',
 '[2] NIST NanoFab, Bruker Dektak XT profilometer. https://www.nist.gov/laboratories/tools-instruments/nanofab-tool-bruker-dektak-xt-profilometer',
 '[3] Clarke et al., Review of plasma etching processes for III-V semiconductors, Micro and Nano Engineering (2025), DOI:10.1016/j.mne.2025.100330.',
 '[4] Hwang and Lee, Design Optimization of Focus Ring Geometry for Improved Wafer-Edge Ion Energy-Angle Distributions in Pulsed Capacitively Coupled Plasma Etching (2026), DOI:10.3390/jmmp10090338.',
 '[5] Optimizing Plasma Etching: Integrating Precise Three-Dimensional Etching Simulation and Machine Learning for Multi-Objective Optimization, IEEE Access (2024), DOI:10.1109/ACCESS.2024.3444454.',
 '[6] EPFL Center of MicroNanoTechnology, Etch definitions. https://www.epfl.ch/research/facilities/cmi/process/etching/etch-definitions/',
 '[7] paceval Mathematical Engine, official C/C++ API and product brief. https://paceval.com/api/ and https://paceval.com/product-brief/.'
]
for r in refs:p(escape(r),'tiny')
p('The completed research establishes actual execution of versioned mathematical wafer-response functions by paceval on synthetic data. It makes no claim of an equipment-specific prediction, industrial certification, customer deployment, or performance advantage.','small')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('WHITEPAPER_CREATED',OUT)
