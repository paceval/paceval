#!/usr/bin/env python3
"""Build self-contained English scientific whitepaper from original paceval result files."""
from pathlib import Path
import csv,json,html
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image as PDFImage,KeepTogether,Table,TableStyle,PageBreak,HRFlowable
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';FIG=ROOT/'figures'
E=json.loads((R/'execution_evidence.json').read_text());AUD=json.loads((R/'independent_validation.json').read_text())
with (R/'selected_models.csv').open(newline='') as f:M=list(csv.DictReader(f))
OUT=ROOT/'paceval_Automatic_Discovery_Chemical_Kinetics_Whitepaper_EN.pdf'
for tag,fn in [('DV','DejaVuSans.ttf'),('DVB','DejaVuSans-Bold.ttf'),('DVM','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(tag,'/usr/share/fonts/truetype/dejavu/'+fn))
NAVY=HexColor('#1b2843');COPPER=HexColor('#e1794c');TEAL=HexColor('#05818a');SLATE=HexColor('#58677c');PALE=HexColor('#ecf7f6');W,H=A4
sty={
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.2,leading=15.2,textColor=NAVY,spaceAfter=9),
 'small':ParagraphStyle('small',fontName='DV',fontSize=8.15,leading=12.3,textColor=NAVY,spaceAfter=6.5),
 'head':ParagraphStyle('head',fontName='DVB',fontSize=17.6,leading=23,textColor=NAVY,spaceAfter=12),
 'sub':ParagraphStyle('sub',fontName='DVB',fontSize=11.25,leading=16,textColor=TEAL,spaceBefore=6,spaceAfter=6),
 'title':ParagraphStyle('title',fontName='DVB',fontSize=27,leading=33,textColor=NAVY,spaceAfter=9),
 'subtitle':ParagraphStyle('subtitle',fontName='DV',fontSize=13,leading=20,textColor=TEAL,spaceAfter=10),
 'label':ParagraphStyle('label',fontName='DVB',fontSize=8,leading=12,textColor=COPPER,spaceAfter=6),
 'math':ParagraphStyle('math',fontName='DVM',fontSize=8.4,leading=14,textColor=NAVY,backColor=PALE,borderPadding=10,spaceBefore=7,spaceAfter=10),
 'caption':ParagraphStyle('caption',fontName='DV',fontSize=7.7,leading=10.8,textColor=SLATE,spaceAfter=10),
 'ref':ParagraphStyle('ref',fontName='DV',fontSize=8.15,leading=12.8,textColor=NAVY,spaceAfter=7),
}
story=[]
def P(s,style='body'):story.append(Paragraph(s,sty[style]))
def head(s):P(s,'head')
def sub(s):P(s,'sub')
def formula(s):P(html.escape(s),'math')
def page():story.append(PageBreak())
def figure(n,f,caption,mh=230):
 p=FIG/f;w,h=Image.open(p).size;fac=min(510/w,mh/h)
 im=PDFImage(str(p),width=w*fac,height=h*fac)
 c=Paragraph('<b>Figure '+str(n)+'.</b> '+caption,sty['caption'])
 story.append(KeepTogether([im,Spacer(1,4),c]))
def table(rows,widths,first=True):
 xx=[[Paragraph(str(x),sty['small']) for x in row] for row in rows]
 t=Table(xx,colWidths=widths,hAlign='LEFT',repeatRows=1 if first else 0)
 opts=[('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.7,TEAL)]
 if first:opts.append(('BACKGROUND',(0,0),(-1,0),PALE))
 t.setStyle(TableStyle(opts));story.append(t);story.append(Spacer(1,10))
def footer(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(HexColor('#dbe4e7'));canvas.line(42,43,W-42,43)
 canvas.setFont('DV',7.5);canvas.setFillColor(SLATE)
 canvas.drawString(43,30,'paceval. | WP 27 | Synthetic chemical kinetics research')
 canvas.drawRightString(W-43,30,str(doc.page))
 canvas.restoreState()
# Cover
story.append(PDFImage(str(FIG/'00_chemical_kinetics_hero.png'),width=W-86,height=(W-86)/2))
story.append(Spacer(1,35));P('WP 27  |  SCIENTIFIC FUNCTIONAL RESEARCH','label')
P('Automatic Discovery of Chemical Kinetic Rate Equations','title')
P('Constrained rate-law selection and stoichiometric integration with original paceval computation graphs','subtitle')
story.append(HRFlowable(width='100%',thickness=2,color=TEAL));story.append(Spacer(1,14))
P('Actual execution of 1,000 interpretable candidate rate-law formulas using original Linux paceval 4.25, with completely independent chemical-model validation.','body')
P('15 November 2026  |  Original C++17 SDK  |  Synthetic kinetic observations  |  English scientific publication','small')
P('Scope: a fixed-library model recovery experiment, not unrestricted molecular mechanism discovery, plant safety certification, or a speed/energy comparison.','small');page()
# executive
head('Executive summary')
P('Industrial kinetic model development requires interpretable rate laws that can be repeatedly evaluated under changing concentration and temperature. The pilot study tests whether original paceval execution graphs can serve as the mathematical layer inside a constrained equation-discovery workflow. The goal is functional completeness and mathematical correctness, not computational performance claims.')
P('A deterministic generator supplies synthetic noisy kinetic observations for an idealized isothermal A + B -> P reaction. A C++ controller enumerates 1,000 different candidate mathematical rate bases, obtains parameter-fit statistics and evaluation losses from paceval, ranks candidates on a separate validation set, then integrates two selected models through genuine paceval species-source and rate graphs.')
table([['Recorded element','Executed experiment'],['Unique executed graph handles',f'{E["unique_graphs_executed"]:,}'],['Actual graph outputs',f'{E["graph_point_evaluations"]:,}'],['Distinct candidate expressions',f'{E["candidate_count"]:,}'],['Training / validation / independent holdout',f'{E["training_samples"]} / {E["validation_samples"]} / {E["holdout_samples"]}'],['Independent reconstructed candidate score checks',f'{AUD["independent_candidate_scoring_checks"]:,}'],['80-digit independently verified quantities',f'{AUD["independent_high_precision_80_digit_values"]:,}']],widths=[285,210])
figure(1,'01_execution_architecture.png','Actual split between paceval function evaluation and C++ discovery orchestration. Conceptual organization chart.',mh=162)
page()
# research background
head('1 | Industrial context and current research')
P('Industrial reaction studies seek predictive rates for reactor sizing, catalyst screening and safe interpretation of observed concentration trends. Traditional kinetic fitting requires choosing a mechanism, solving parameter-estimation problems and testing the resulting rate law against new conditions. Interpretable sparse identification and symbolic regression broaden the candidate search while respecting physical laws.')
P('Palma Banos et al. (2026) introduced stoichiometrically informed symbolic regression for extracting chemical reaction mechanisms from concentration time series. de Carvalho Servia and colleagues (2026) proposed physics-informed automated kinetic model discovery with uncertainty-aware extensions. Earlier reaction discovery in dynamic plug-flow reactors (Cohen et al., 2024) demonstrated rate-law identification using coordinate transformations and symbolic regression. These contributions provide research context, but none of their proprietary results or experimental data are reused here.')
sub('Precise contribution of this demonstrator')
P('The experiment isolates the mathematical evaluation stage. It exercises registered, reusable paceval graphs for every candidate, cross-moments, fit expressions, residual costs, derivative and decision functions, plus a small integrated reaction model. The search grammar is deliberately restricted and the planted truth is an eligible candidate. This proves a well-defined mathematical workflow, not a general algorithm for inventing chemistry.')
sub('Example industrial workflow')
P('A hypothetical reaction-development engineer supplies cleaned instantaneous-rate observations under multiple feed compositions and temperatures. The software evaluates explicitly enumerated candidate rate-law families, selects parsimonious alternatives, and then uses the selected rate equations inside a batch-reactor material-balance study. The host manages experimental provenance, data filtering, model selection and numerical integration; paceval evaluates the equations.')
P('No real kinetics database, proprietary chemical recipes or direct plant instrumentation feed the numerical results. NIST chemical kinetics datasets are cited only as a possible external source for future validation, not as the origin of the synthetic test data.');page()
# math
head('2 | Mathematical specification')
P('The test reaction is the single balanced synthetic conversion A + B -> P. A known rate law generates reproducible pseudo-observations with deterministic small multiplicative fluctuations. All reaction species concentrations are positive, temperature is in kelvin and rates have units of mol L^-1 h^-1.')
formula('r_true = 0.65 * exp[-Ea/Rg * (1/T - 1/310)] * CA*CB/(1+1.1*CB)')
formula('Ea = 36000 J/mol;  Rg = 8.31446261815324 J/(mol*K)')
P('Candidate structures vary the orders of A and B, the activation energy, the temperature correction and the denominator. The saturation of B in the planted law is a mathematical response shape, not an identified elementary molecular mechanism. For a general candidate, the units of the fitted prefactor change with the orders and concentration dependence.')
formula('basis_i(T, CA, CB) = exp[-Ea_i/Rg*(1/T - 1/310)] * CA^a_i * CB^b_i / denominator_i')
formula('k_fit_i = sum_j(basis_ij * observed_j) / sum_j(basis_ij^2)')
formula('validation_loss_i = mean_j[ ((k_fit_i*basis_ij - observed_j)/(0.2+observed_j))^2 ]')
formula('selection_score_i = validation_loss_i + 0.000006 * complexity_i')
P('Moment construction and the fit quotient are original paceval graph evaluations; C++ aggregates moments over samples and selects the smallest penalized validation score. Holdout data are excluded from the candidate ranking. This distinction is essential: paceval is the numerical engine but not itself the model-search optimizer.');page()
# method and search
head('3 | Complete constrained search')
P('The finite formula grammar contains five families, five candidate orders for each reactant (0, 0.5, 1, 1.5, 2), four activation energies (24, 30, 36 and 42 kJ/mol), and two correction variants per family. This generates exactly 1,000 unique expressions. All are constructed as persistent paceval graph handles and evaluated against the same recorded observations.')
figure(2,'02_candidate_score_landscape.png','Actual validation ranking over the fixed 1,000-candidate pool; no algorithm-engine performance measurement.',mh=218)
figure(3,'03_model_family_scores.png','Score distribution grouped by rate-law family. Whiskers hide visual outliers, not candidate data.',mh=198)
page()
head('4 | Frozen model revisions and holdout data')
P('V1 is the best available restricted mass-action rate. V2 is chosen from all five kinetic families and recovers the planted B-saturation structure (candidate 301). Its fitted prefactor is about 0.650145 at the reference temperature. Neither selected model is updated after seeing the holdout results.')
table([['Recorded quantity','V1 restricted mass-action','V2 full constrained search'],['Candidate ID',M[0]['selected_id'],M[1]['selected_id']],['Concentration exponents A / B',M[0]['order_A']+' / '+M[0]['order_B'],M[1]['order_A']+' / '+M[1]['order_B']],['Activation energy',M[0]['activation_energy_J_mol']+' J/mol',M[1]['activation_energy_J_mol']+' J/mol'],['Held-out normalized loss',f'{float(M[0]["holdout_normalized_loss"]):.8g}',f'{float(M[1]["holdout_normalized_loss"]):.8g}']],widths=[219,143,133])
figure(4,'04_holdout_rate_predictions.png','Original paceval predictions against synthetic observations in an independently reserved high-temperature test set.',mh=204)
page()
head('5 | Out-of-temperature-range evaluation')
P('The training temperatures are within 287-324 K, validation cases extend to 342 K, and the locked final holdout concentrates on 341-360 K. The data are therefore intentionally challenging relative to the fit range. They still come from the same synthetic source equation and deterministic error model, so real extrapolation reliability cannot be inferred.')
figure(5,'05_holdout_residual_temperature.png','The paceval-computed signed prediction residual across the locked high-temperature holdout.',mh=237)
figure(13,'13_holdout_model_selection.png','Comparison of predictive model fit, not of mathematical execution engines or timing.',mh=204)
page()
head('6 | Chemical rate surfaces and saturation')
P('The chosen mathematical structures produce distinguishable response maps at the same specified temperature. The original paceval batch API computes every plotted rate and every sensitivity or margin value. The plot generator loads saved graph outputs and does not recompute the equations.')
figure(6,'06_rate_surfaces_3d.png','Real graph output on 41 by 41 grids at 340 K. No spatial chemical-reactor geometry is implied.',mh=248)
figure(7,'07_saturating_reactant_response.png','The B-concentration response at 310 K and constant A concentration, highlighting the selected saturating law.',mh=199)
page()
head('7 | Temperature and analytic sensitivity')
P('For all modeled candidates, the Arrhenius temperature dependence is explicit. paceval additionally evaluates the analytically derived concentration derivatives and temperature derivatives of both selected rate laws. These derivative functions are entered as separate persistent graph expressions, not misrepresented as automatically differentiated by the SDK.')
formula('dr/dT = r*[ Ea/(Rg*T^2) + thermal_exponent/T ]')
P('The thermal exponent is nonzero only for one restricted mass-action subfamily. Concentration sensitivities explicitly subtract the derivatives of any saturation denominator. Numerical comparisons with an independently written native kinetic reference and 80-digit mpmath selected points passed under the predefined study tolerances.')
figure(8,'08_arrhenius_temperature_scan.png','Raw paceval temperature-response scan, including the held-out high-temperature range.',mh=200)
figure(11,'11_rate_sensitivity_map.png','Selected model partial derivative with respect to reactant B, calculated by a persistent paceval sensitivity graph.',mh=195)
page()
head('8 | End-to-end species integration')
P('The C++ host orchestrates a four-stage Runge-Kutta step, but the reaction-rate right-hand side and the three stoichiometric source terms come from paceval. Eight initial concentration/temperature combinations are tested per version, each with 81 archived sampling points. An independently programmed native reaction model repeats each numerical trajectory.')
formula('dCA/dt = -r;   dCB/dt = -r;   dCP/dt = r')
formula('CA(t) + CP(t) = CA(0);   CB(t) + CP(t) = CB(0)')
figure(9,'09_integrated_reaction_trajectories.png','Recorded concentrations for the same synthetic batch condition under both selected rate models.',mh=209)
figure(10,'10_stoichiometric_conservation.png','Independent conservation invariants across the same paceval-driven reaction trajectories.',mh=180)
page()
head('9 | Mathematical decision envelope')
P('A further reproducible exercise builds a hypothetical maximum model rate of 1.6 mol L^-1 h^-1 into separate real paceval margin and logical guard graphs. On each concentration grid point, paceval calculates the continuous margin and the Boolean condition. The C++ host records the status. Neither threshold nor decision is a chemical process safety limit.')
formula('rate_margin = 1.6 - rate')
formula('acceptable = (rate <= 1.6) AND (CA > 0) AND (CB > 0)')
figure(12,'12_rate_envelope_margins.png','Mathematical acceptability envelope. This is not a plant operating or hazard clearance map.',mh=275)
P('The research also checks boolean 0/1 semantics, negative-modulo variants, min/max, strict numeric CSV schemas and both SDK conversion functions using their actual original signatures. Domain validity is checked in the host before any formula evaluation; a Boolean mask is not assumed to short-circuit invalid arithmetic.');page()
head('10 | Function ownership, API and reproducibility')
table([['Mathematical purpose','Actual executor','Evidence'],['1,000 candidate rate expressions','paceval batch','C0 - C999'],['Rate fitting and normalized score','paceval + host sums','Fit, moment and score handles'],['Two rate revisions, residual and sensitivity','paceval','26 versioned persistent graphs'],['Stoichiometric source terms','paceval','Rate / dA / dB / dP'],['ODE stepping and discrete model choice','C++ host','Independent integrator replay'],['Input validation and CSV orchestration','C++ + paceval converters','Strict numeric literal contract'],['80-digit mathematical reference','Independent Python','Recomputed formula family']],widths=[192,112,191])
P(f'In the primary run {E["unique_graphs_created"]:,} graph handles were created and all {E["unique_graphs_executed"]:,} were executed. The engine returned {E["graph_point_evaluations"]:,} actual formula-point outputs across {E["multi_graph_batch_calls"]:,} multi-graph batch calls and {E["scalar_calls"]:,} scalar calls. Each value has a distinct accounting definition in results/execution_evidence.json.')
P('Actual numerical CSV import and export use `paceval_dConvertStringToFloat` and `paceval_dConvertFloatToString` after a strict literal parser. Missing or nonfinite observations are rejected. The original paceval 4.25 C++ public interface is linked to a separately supplied genuine Linux shared library and is packaged without distributing that binary. Nothing executed here uses the remote paceval MCP service.')
P('The complete scientific source files and all generated result tables, including candidate formulas, are included in the GitHub ZIP. The archive-wide Markdown mathematical syntax and link gate checks every Markdown file recursively with explicit negative regression tests.');page()
head('11 | Independent numerical controls and scope')
P('The C++ reference independently evaluates the rate-law mathematical functions and the stoichiometric RK4 integration. A separate Python/Numpy program reconstructs all 1,000 fitted prefactors, training losses, validation losses and selection scores directly from the observed data and the parameter tables. mpmath also checks 450 selected outcomes at 80-digit precision. All finite tested full-reactor paths pass the declared numerical and invariant checks.')
sub('What the demonstration establishes')
P('Real paceval engine integration, persistent and repeated execution of 1,000 unique candidate formulas, numerical fit-and-rank functions, independent model versions, analytical sensitivities, explicit decision margins and a stateful integrated material-balance example are all operational and backed by test files.')
sub('What it does not establish')
P('The kinetics are simulated rather than measured. Instantaneous rates are provided directly rather than inferred from noisy time derivatives. The grammar contains the planted truth. There is one isothermal reaction event without hidden intermediates, real stoichiometric networks, reaction enthalpy, concentration measurement uncertainty, identifiability confidence regions or tested real-reactor kinetic parameters. A correct numerical model need not be a chemically correct explanation of a reactor, catalyst or reaction mechanism.')
sub('Appropriate follow-up')
P('A valuable extension would acquire a licensed real kinetic dataset with reaction and measurement provenance, identify an appropriate physical mechanism search grammar, fit against multiple batch trajectories, and validate out-of-time and out-of-condition response with independent experimental temperature and composition series. A genuine reaction-network mechanism-discovery result should also assess identifiability and hidden intermediates, rather than report only the best numerical fit.')
page()
head('12 | Scientific references and traceability')
refs=[
 ('[1] Palma Banos, Kress, Hernandez, Craven (2026)','Stoichiometrically-informed symbolic regression for extracting chemical reaction mechanisms from data; Digital Discovery 5, 2325-2341.','https://doi.org/10.1039/D5DD00470E'),
 ('[2] de Carvalho Servia et al. (2026)','Physics-informed symbolic regression for data-efficient kinetic model discovery; Computers & Chemical Engineering, published online 17 October 2026.','https://doi.org/10.1016/j.compchemeng.2026.109918'),
 ('[3] Cohen, Beykal and Bollas (2024)','Data-driven Discovery of Reaction Kinetic Models in Dynamic Plug Flow Reactors using Symbolic Regression; Computer Aided Chemical Engineering 53.','https://doi.org/10.1016/B978-0-443-28824-1.50492-0'),
 ('[4] Brunton et al., SINDy; PySINDy documentation','Sparse identification of governing dynamical systems, external scientific context, not used as the evaluated paceval data.','https://pysindy.readthedocs.io/en/stable/'),
 ('[5] NIST Chemical Kinetics Database','Reference database for documented gas-phase reaction kinetics. No NIST data are used in the synthetic output.','https://kinetics.nist.gov/kinetics/'),
 ('[6] paceval Mathematical Engine','Original C/C++ SDK and multi-graph batch API, version 4.25 documentation.','https://paceval.com/api/'),
]
for ident,desc,url in refs:
 P('<b>'+ident+'</b>','ref');P(desc,'ref');P('<link href="'+url+'" color="#077E89">'+url+'</link>','ref')
sub('Provenance of original proposal')
P('The two-page WP27 source described four proposed rate, species-residual, mismatch and complexity kernels and suggested candidate search and out-of-temperature verification. It explicitly contained no executed results. This newly completed publication adds real execution, fixed synthetic dataset, original SDK verification, high-precision independent references, mathematical traceability and figures. The source is preserved at docs/original_WP27_proposal.pdf.')
P('This is a research-only mathematical demonstrator, with no industrial qualification, chemical safety authorization or speed/energy performance assertion.','small')
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=43,leftMargin=43,topMargin=44,bottomMargin=57,title='paceval WP27 Automatic Discovery of Chemical Kinetic Rate Equations',author='paceval Industrial Research',subject='Verified functional mathematical research with original paceval SDK')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('GENERATED WHITEPAPER',OUT,'bytes=',OUT.stat().st_size)
