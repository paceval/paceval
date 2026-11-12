#!/usr/bin/env python3
"""Reproduce publication PDF from deterministic actual paceval output/figures.
All page placement checked against layout bounds and final PDF should be visually rendered.
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
import csv
ROOT=Path(__file__).resolve().parents[1];F=ROOT/'figures';D=ROOT/'examples';OUT=ROOT/'paceval_Electric_Propulsion_Whitepaper_EN.pdf'
W,H=A4;navy=HexColor('#153450');teal=HexColor('#0A8995');gray=HexColor('#EFF3F6');muted=HexColor('#5B7080')
c=canvas.Canvas(str(OUT),pagesize=A4);c.setTitle('paceval Electric Propulsion Performance Surface Sweeps - English research whitepaper')
normal=ParagraphStyle('body',fontName='Helvetica',fontSize=10.25,leading=15.5,textColor=navy,spaceAfter=0)
small=ParagraphStyle('small',parent=normal,fontSize=9,leading=13.5)
pageid=0

def init(title=None):
 global pageid
 pageid+=1;c.setStrokeColor(teal);c.setLineWidth(1.3);c.line(39,44,W-39,44)
 c.setFillColor(muted);c.setFont('Helvetica',7.7);c.drawString(39,31,'paceval | electric propulsion research | November 2026')
 c.drawRightString(W-39,31,str(pageid))
 if title:
  c.setFillColor(navy);c.setFont('Helvetica-Bold',17.3);c.drawString(39,H-66,title)
  c.setStrokeColor(teal);c.line(39,H-78,W-39,H-78)
 return H-102

def para(text,y,compact=False):
 st=small if compact else normal
 p=Paragraph(text,st);aw,ah=p.wrap(W-82,680)
 if y-ah < 65:raise RuntimeError(f'Text overflow on page {pageid}: {text[:50]}')
 p.drawOn(c,41,y-ah);return y-ah-(8 if compact else 12)

def head(text,y):
 if y<104:raise RuntimeError('heading overflow')
 c.setFillColor(teal);c.setFont('Helvetica-Bold',11);c.drawString(41,y-12,text);return y-29

def figure(stem,y,maxh=280):
 ir=ImageReader(str(F/(stem+'.png')));iw,ih=ir.getSize()
 ww=W-88;hh=ww*ih/iw
 if hh>maxh:hh=maxh;ww=hh*iw/ih
 if y-hh<70:raise RuntimeError('Figure overflow on page '+str(pageid)+' '+stem)
 c.drawImage(ir,(W-ww)/2,y-hh,width=ww,height=hh)
 return y-hh-10

def table(rows,y,widths=(390,118)):
 for index,(k,v) in enumerate(rows):
  if y-26<68:raise RuntimeError('table overflow')
  c.setFillColor(gray if index%2==0 else white);c.rect(41,y-25,W-82,26,stroke=0,fill=1)
  c.setFillColor(navy);c.setFont('Helvetica',9.3);c.drawString(49,y-17,k)
  c.setFont('Helvetica-Bold',9.2);c.drawRightString(W-49,y-17,v);y-=27
 return y-10

def done():c.showPage()
# cover
init();c.setFillColor(teal);c.setFont('Helvetica-Bold',10);c.drawString(40,H-73,'PACEVAL | SCIENTIFIC RESEARCH DEMONSTRATOR')
c.setFillColor(navy);c.setFont('Helvetica-Bold',23.5);c.drawString(40,H-115,'Electric Propulsion')
c.drawString(40,H-147,'Performance Surface Sweeps')
c.setFont('Helvetica',11.5);c.setFillColor(muted);c.drawString(41,H-175,'Reusable mathematical maps for analytical thruster characterization')
c.drawImage(ImageReader(str(F/'00_electric_propulsion_hero.png')),39,H-485,width=W-78,height=284,mask='auto')
y=H-510
y=para('<b>Executed research outcome.</b> Fifty original analytical expressions, one immutable formula revision, 10,000 synthetic power-and-flow requests, 28,767 paceval scalar evaluations, 1,600 independently checked batch results and five complete 3,721-point surfaces.',y)
y=para('<b>Scientific scope.</b> Reproducible mathematical evaluation of physically related propulsion performance metrics. Efficiency coefficients are deliberately synthetic; no real thruster calibration, measured lifetime or flight operation is claimed.',y)
y=para('<i>The cover is a conceptual illustration, not an observed engine or a measured performance map.</i>',y,True);done()
# introduction
y=init('1. Industrial use case and current practice')
y=para('Electric propulsion systems provide low thrust over extended operating periods for satellite station keeping, electric orbit raising and many deep-space mission concepts. Engineers characterize how useful operating performance changes when electrical input power and total propellant mass flow vary. The key quantities are thrust, specific impulse, total electrical efficiency and thrust produced per unit electrical power.',y)
y=head('What engineers actually do',y)
y=para('A real Hall-thruster characterization campaign measures thrust on an instrumented test stand, electrical input power including subsystem power, and propellant flows including the cathode. A laboratory can interpolate those measured operating points, build analytical fits or use surrogate models for further exploration. This project deliberately tests only the mathematical expression-evaluation layer of such a workflow.',y)
y=head('Scientific and industrial state of the art',y)
y=para('NASA/JPL Fundamentals of Electric Propulsion (second edition, 2025) provides the relevant definitions and system context. A 2026 6-kW-class Hall-thruster study reports total-efficiency and specific-impulse measurements; 2025 experiments explored thruster-in-the-loop optimization; work in 2026 developed surrogate-model-based optimization. These approaches require real propulsion data or physical testing, which are not supplied by this demonstrator.',y)
y=head('Hypothetical engineering example',y)
y=para('Given an electrical supply range of 0.5-3 kW and total xenon-like propellant flow between 2 and 8 mg/s, an engineering group might request maps of predicted thrust and specific impulse from a version-controlled efficiency fit. The C++ host checks the requested values and keeps scenario state, while paceval evaluates the same registered expressions for different operating points.',y)
y=para('Source references and direct URLs are listed on the final page. No actual laboratory measurements are represented in the released CSV data.',y,True);done()
# defined model
y=init('2. Defined mathematical model')
y=para('The mathematical variables are electric input power P in watts and total propellant flow m in mg/s. The flow in SI mass units is mdot = 1e-6 * m kg/s. Standard gravity g0 = 9.80665 m/s2. All five model families use the same synthetic total efficiency eta(P,m), with the domain 500 <= P <= 3000 W and 2 <= m <= 8 mg/s.',y)
y=head('Fundamental physically derived performance identities',y)
y=figure('10_physics_equations',y,178)
y=head('Explicitly synthetic, not empirically fitted efficiency surface',y)
y=figure('11_synthetic_equation',y,92)
y=para('For j = 0,...,9: b_j = 0.33 + 0.005*j and a_j = 0.17 - 0.003*j. All evaluated efficiencies lie strictly between zero and one. The coefficients and Gaussian operating-region shape are selected for an interpretable mathematical graph test, not inferred from measurements.',y)
y=head('Five distinct, dimensioned mathematical output families',y)
y=table([('Family 1: total electrical efficiency','dimensionless'),('Family 2: thrust T','mN'),('Family 3: specific impulse Isp','seconds'),('Family 4: thrust / electrical power','mN/kW'),('Family 5: P * (1 - eta), non-jet power balance','watts')],y)
y=para('Family 5 is a complementary electrical-energy bookkeeping proxy, not a measured thruster heat load or radiation model. The ideal jet-power identity omits plasma and beam details. Total flow and total power must be defined consistently.',y,True);done()
# architecture
y=init('3. paceval graph architecture and host duties')
y=para('The implementation registers ten different coefficient versions of each of five related mathematical functions, creating fifty original computation objects. One revised thrust-efficiency coefficient is registered under a separate 51st handle. The old and revised versions remain simultaneously callable.',y)
y=figure('09_execution_architecture',y,190)
y=head('Functions executed inside the original paceval runtime',y)
y=para('paceval_InitializeLibrary starts the SDK. paceval_CreateComputation parses each source expression. paceval_dGetComputationResult evaluates one operating point, and paceval_dGetComputationResultExt evaluates packed multi-point input arrays. paceval_DeleteComputation frees all graph handles at shutdown.',y)
y=head('C++ host responsibilities and what is excluded',y)
y=para('The host creates the deterministic synthetic test cases, enforces finite positive input ranges, orchestrates graph selection and immutable formula updates, writes CSV outputs and calculates independent reference values. Neither paceval nor the host implements an ion kinetic solver, vacuum-chamber calibration, mission trajectory optimizer, hardware controller, lifetime assessment or experimentally validated interpolation.',y)
y=head('Engineering motivation',y)
y=para('A versioned mathematical execution layer makes it possible to keep the definition of a particular analytical model explicit while varying its operating inputs. The present experiment verifies this capability numerically, without assuming any particular processing-time or hardware advantage.',y);done()
# tests
y=init('4. Executed workload and independent verification')
y=para('The deterministic workload replays 10,000 synthetic operating points using a fixed seed (20261112). Fifty versioned expression graphs are reused throughout. Each of the five principal outputs is evaluated at 61 by 61 grid points, and 32 packed batch cases are evaluated for each of fifty original expressions.',y)
y=table([('Original mathematical expressions','50'),('Graph handles including one immutable revision','51'),('Synthetic operating-point evaluations in replay','10,000'),('Total scalar paceval SDK evaluations','28,767'),('Independent packed batch results','1,600'),('Computed surface points per physical quantity','3,721'),('Independent 80-digit reference checks','500 / 500 PASS'),('Invalid host-domain inputs rejected','4 / 4'),('CMake / CTest SDK integration','1 / 1 PASS')],y)
y=para('The scientific numerics audit separately checks the stated analytical expressions using native C++ arithmetic and a 500-case independent 80-digit Decimal reference. A further cross-surface test verifies the thrust/efficiency/Isp/power identities at all 3,721 operating-grid points. Detailed numerical diagnostics are retained in the technical result files, rather than displayed as a comparison between computing technologies.',y)
y=para('These results establish repeatable execution of the declared mathematical map. They do not constitute a calibration or prediction-accuracy study for a flight article.',y,True);done()
# six pages science
def figpage(title,intro,first,caption,second=None,secondcap=None):
 y=init(title);y=para(intro,y)
 y=figure(first,y,305 if second is None else 234);y=para(caption,y,True)
 if second:
  y=figure(second,y,220);y=para(secondcap,y,True)
 done()
figpage('5. Synthetic electrical efficiency map',
 'This operating map explicitly visualizes the smooth synthetic efficiency function that drives all derived output metrics. Values are bounded and respond continuously to electrical power and total propellant flow.',
 '01_efficiency_surface','Figure 1. The plotted surface contains 3,721 output values evaluated using the original paceval SDK.',
 '04_efficiency_contours','Figure 4. Contour projection of those same evaluated efficiency-map data. This is not a measured laboratory map.')
figpage('6. Analytical thrust and specific impulse',
 'The same input operating grid is passed to separate persistent thrust and specific-impulse expression handles, producing two linked outputs with physical units. The formulas enforce the chosen jet-power identities.',
 '02_thrust_surface','Figure 2. Derived thrust in millinewtons over the declared 0.5-3 kW and 2-8 mg/s research domain.',
 '03_specific_impulse_surface','Figure 3. Specific impulse in seconds. Both are simulated consequences of the declared efficiency function, not measured Hall-thruster data.')
figpage('7. Electrical-power performance trade-offs',
 'An engineer selecting an operating point may need to consider thrust per kilowatt together with propellant efficiency. The two quantities are related through power, total mass flow and the synthetic efficiency surface.',
 '05_thrust_to_power_surface','Figure 5. Thrust per electrical kilowatt, computed directly from a separate reusable paceval expression.',
 '07_tradeoff_cross_section','Figure 7. A fixed-total-mass-flow cross-section of the calculated specific-impulse and thrust/power responses.')
figpage('8. Electrical power balance and revisions',
 'A non-jet power quantity is included for an energy-accounting illustration. It is the complement of modeled jet power, not the thermal power dissipated in a physical thruster. Controlled revisions are assessed without invalidating old handles.',
 '06_nonjet_power_surface','Figure 6. P*(1-eta) is the electrical power absent from the ideal kinetic jet-power term.',
 '08_formula_revision','Figure 8. Original and revised thrust expressions remain accessible at the same power and mass-flow inputs.')
# limitations
y=init('9. Industrial interpretation and scientific limits')
y=head('Demonstrated successfully',y)
y=para('The C++ application compiled and ran against the original compatible paceval Linux runtime. The SDK evaluated mathematical expressions for five dimensioned propulsion performance outputs, reused fifty persistent graphs, supported an immutable revision and verified both scalar and packed batch calculations. The released CSV results drive every scientific performance surface included in this report.',y)
y=head('What this does not demonstrate',y)
y=para('The selected Gaussian efficiency function is a synthetic mathematical test fixture. There are no experimental thrust-stand measurements, cathode / discharge calibration records, plasma transport calculations, uncertainty-corrected chamber effects, beam divergence estimates, or thruster life tests. Therefore, numerical correctness of the expressions is not evidence of real-world electric-thruster performance accuracy.',y)
y=head('Useful next research experiment',y)
y=para('After obtaining a permitted, adequately described measured performance table, a subsequent study could freeze the calibration set, fit clearly constrained positive efficiency functions, test out-of-sample performance, quantify measurement uncertainty and compare physically meaningful outputs across unseen operating regimes. Such an experiment would distinguish model fidelity from mathematical execution correctness.',y)
y=head('Technical reproducibility',y)
y=para('Run the documented CMake build with a compatible external libpaceval runtime; then execute the deterministic replay. The supplied audit scripts recompute the analytical identities and independent decimal reference; the visualization and PDF scripts reproduce the published surfaces and whitepaper. All local paths are linked in README.md.',y);done()
# bibliography
y=init('10. Reproducibility and technical references')
y=para('Build command: cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so. Then cmake --build build -j; ctest --test-dir build --output-on-failure; ./build/electric_propulsion --out examples --updates 10000. The README lists the Python audit, figure and PDF reproduction commands.',y)
y=head('Reviewed external scientific and technical sources',y)
refs=[
 ('[1] Goebel and Katz (2025), Fundamentals of Electric Propulsion, second edition, NASA/JPL.',
  'https://descanso.jpl.nasa.gov/SciTechBook/series4/Electric_Propulsion_2nd_edition.pdf'),
 ('[2] Thoreau et al. (2025), Rapid thruster-in-the-loop optimization for Hall thrusters.',
  'https://link.springer.com/article/10.1007/s44205-025-00159-5'),
 ('[3] Thoreau et al. (2026), Surrogate modeling and real-time optimization of propellant mixtures.',
  'https://link.springer.com/article/10.1007/s44205-026-00188-8'),
 ('[4] 2026 study, Characterization of a 6-kW-class Hall-thruster subsystem.',
  'https://link.springer.com/article/10.1007/s44205-026-00178-w'),
 ('[5] NASA Hall-thruster characterization and electrical jet-power definitions.',
  'https://ntrs.nasa.gov/api/citations/20190001137/downloads/20190001137.pdf'),
 ('[6] paceval public API and C++ interface.', 'https://paceval.com/api/'),
]
for title,url in refs:
 y=para(title,y,True)
 # URL as clickable link and shortened visible domain/path, helps preserve width
 label=url.replace('https://','');
 if len(label)>76:label=label[:73]+'...'
 c.setFont('Helvetica',7.5);c.setFillColor(teal);c.drawString(42,y-5,label)
 c.linkURL(url,(40,y-9,W-40,y+7),relative=0)
 y-=21

y=head('Interpretation and publication integrity',y)
y=para('The original source proposal is a research hypothesis. This completed publication reports only calculations executed with the available SDK in the precisely defined synthetic model. The installed paceval runtime is not redistributed in the GitHub package; the original SDK source-file copyright and license notices are preserved. No measured speed comparison, hardware superiority, or industrial deployment claim is asserted.',y)
done();c.save();print(f'Created {OUT} with {pageid} pages')
