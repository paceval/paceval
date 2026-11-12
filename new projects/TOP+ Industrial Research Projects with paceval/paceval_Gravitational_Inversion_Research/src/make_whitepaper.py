"""Regenerate the English, page-designed research report from actual exported files."""
import csv
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import A4
ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'paceval_Gravitational_Inversion_Whitepaper_EN.pdf'
fonts=[('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','DejaVu'),('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','DejaVuBold')]
for f,n in fonts:
 if Path(f).exists():pdfmetrics.registerFont(TTFont(n,f))
F='DejaVu'; B='DejaVuBold'
navy=colors.HexColor('#173552');teal=colors.HexColor('#0C8596');muted=colors.HexColor('#536879')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='H1x',fontName=B,fontSize=17,leading=24,textColor=navy,spaceAfter=13))
styles.add(ParagraphStyle(name='H2x',fontName=B,fontSize=10.5,leading=16,textColor=teal,spaceBefore=9,spaceAfter=6))
styles.add(ParagraphStyle(name='Bodyx',fontName=F,fontSize=8.6,leading=14.5,textColor=colors.HexColor('#273744'),spaceAfter=8))
styles.add(ParagraphStyle(name='Smallx',fontName=F,fontSize=7.2,leading=11,textColor=muted,spaceAfter=6))
styles.add(ParagraphStyle(name='Coverx',fontName=B,fontSize=25,leading=31,textColor=navy,spaceAfter=14))
styles.add(ParagraphStyle(name='Formula',fontName=F,fontSize=9,leading=16,textColor=navy,spaceBefore=10,spaceAfter=13,alignment=TA_CENTER))
W,H=A4
story=[]
def p(s,sty='Bodyx'):story.append(Paragraph(s,styles[sty]))
def h(s):p(s,'H1x')
def sh(s):p(s,'H2x')
def img(path,w=470,maxh=325):
 r=ImageReader(str(ROOT/path));iw,ih=r.getSize();factor=min(w/iw,maxh/ih);story.append(Image(str(ROOT/path),width=iw*factor,height=ih*factor));story.append(Spacer(1,8))
def tbl(rows,widths=None):
 t=Table([[Paragraph(str(x),styles['Smallx']) for x in row] for row in rows],colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#EEF5F7')]),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#CED9DF'))]))
 story.append(t);story.append(Spacer(1,10))
def page():story.append(PageBreak())
def footer(c,doc):
 c.setStrokeColor(teal);c.setLineWidth(.9);c.line(42,49,W-42,49)
 c.setFont(F,7);c.setFillColor(muted);c.drawString(42,35,'paceval | WP_033 Gravitational Inversion | research demonstrator | November 2026');c.drawRightString(W-42,35,str(doc.page))
obs=list(csv.DictReader((ROOT/'examples/synthetic_observations.csv').open()))
fit={r['fit']:r for r in csv.DictReader((ROOT/'examples/inversion_summary.csv').open())}
# 1 Cover
p('PACEVAL | SCIENTIFIC RESEARCH DEMONSTRATOR','H2x')
p('Forward Expressions in<br/>Gravitational Inversion','Coverx')
p('A reproducible degree-2 gravity forward model, mathematical sensitivities, and synthetic two-parameter inverse recovery using original paceval C++ execution graphs.','Bodyx')
img('figures/00_gravity_hero.png',505,258)
p('<b>Executed research outcome.</b> Eight persistent mathematical computations; 960 deterministic synthetic observations; 3,721 evaluated surface locations; an independently verified host-side inverse solution. The figure above is a conceptual visualization, not an observation or calculated field.','Bodyx')
p('Scope: two model parameters, geocentric spherical coordinates, frozen reference constants and deterministic synthetic perturbations. No operational Earth gravity-field inversion is claimed.','Smallx')
page()
# 2
h('1. Industrial application and current state of the art')
p('Gravitational inversion transforms a measured gravity response into information about a model. Geodetic users analyze the Earth gravity field for global reference models and orbit-support applications; geophysical users investigate mass-density contrasts beneath survey sites. Each application repeatedly predicts a gravity observable from candidate model parameters, compares it with survey data, and adjusts the model.')
p('The full industrial chain contains measurement geometry, corrections, instrument calibration, forward computation, sensitivity calculation, data weighting, inverse-model optimization and uncertainty assessment. This demonstration isolates only a scientifically transparent forward kernel plus a small inverse step.')
sh('Established methods')
p('International gravity reference resources such as ICGEM represent Earth fields by spherical harmonics and distinguish potential, gravity disturbance and gravity anomaly. Geophysical codes such as SimPEG compute gravity responses of 3D discretized density distributions and solve larger inverse problems with explicit sensitivity operators. A newly published 2026 combined gravity model extends to very high degree, illustrating the large gap between a research kernel and modern global models.')
sh('Where paceval fits')
p('paceval stores the explicit mathematical expressions once, then reevaluates them for new radii, colatitudes and model parameters. In this demonstration the host supplies the synthetic observation survey, solves a two-parameter least-squares problem and owns all file and validation logic. paceval does not perform a density-contrast inversion, survey corrections, uncertainty calibration or general optimization.')
tbl([['Input','Mathematical step','Output'],['r, cos(colatitude), μ, J2','Reusable gravity potential and field graphs','Predicted potential, radial field'],['Repeated survey samples','Fixed-graph evaluation and analytical sensitivities','Observation response and derivatives'],['Synthetic observations','Host-side two-parameter least squares','Recovered μ and J2']], [115,185,192])
page()
# 3
h('2. Mathematically defined potential and radial field')
p('The project starts from a degree-2 axisymmetric synthetic gravitational potential, not from the simplified acceleration expression in the proposal as an independently specified potential. By deriving the radial observable from the potential, the sign convention and factor of three are fixed and consistent.')
p('<b>Potential:</b> V(r,θ) = μ/r · [1 − J2 · (R/r)² · P2(cos θ)], with P2(c) = (3c² − 1)/2.','Formula')
p('<b>Radial inward gravity magnitude:</b> g(r,θ) = μ/r² · [1 − 3 J2 · (R/r)² · P2(cos θ)].','Formula')
p('Here r and R are in km, μ in km³/s², g in km/s² and V in km²/s². The frozen model inputs R = 6378.137 km, μ0 = 398600.4418 km³/s², J2,0 = 0.00108262668 are numeric reference parameters, not a time-specific operational gravity standard.')
sh('Sensitivity expressions executed as paceval graphs')
p('∂g/∂μ = [1 − 3J2(R/r)²P2(c)] / r².','Formula')
p('∂g/∂J2 = −3μR²P2(c) / r⁴.','Formula')
p('∂g/∂θ = 9μJ2R² cos θ sin θ / r⁴.','Formula')
p('The θ derivative is a sensitivity of the *radial component*. It is not by itself the tangential component of the gravitational acceleration vector. The valid domain used for all exported numerical plots is r &gt; R and −1 &lt; cos θ &lt; 1.')
page()
# 4
h('3. C++ architecture and reusable graph execution')
p('The project compiles the unmodified official paceval_main.h and paceval_main.cpp adapter files with the demonstrator. The supplied compatible Linux shared library is linked externally, and is not bundled. An RAII wrapper creates and later deletes eight computational objects. Formula expressions and a version indicator are exported to a machine-readable registry.')
tbl([['Graph','Mathematical meaning'],['1–2','Positive potential V and inward radial field g'],['3–5','Analytical derivatives ∂g/∂μ, ∂g/∂J2, ∂g/∂θ'],['6–7','Monopole comparison and a demonstration squared-residual expression'],['8','Explicit, retained revised version with J2 perturbation ×1.1']], [70,420])
p('The radial field graph is used for the deterministic synthetic observation survey. All eight graphs are reused in an independent 61 × 61 surface batch, and 2,048 additional scalar/batch results are checked against the declared corresponding expressions. The C++ host computes ordinary least squares; inversion is not misrepresented as a paceval optimization primitive.')
img('figures/08_versioned_forward_models.png',467,245)
p('Figure 1. Original, revision, and monopole forward formula versions evaluated for the same input set.','Smallx')
page()
# 5
h('4. Deterministic observations and inverse recovery')
p('For the controlled inverse experiment, the frozen truth differs slightly from the reference values: μ = 1.0007 μ0 and J2 = 1.035 J2,0. The survey contains 32 radii and 30 colatitude-cosines (960 input pairs). A bounded, deterministic trigonometric perturbation is added solely to demonstrate sensitivity to an imperfect dataset.')
p('The host estimates the reparameterized coefficients m = μ/μ0 and b = μJ2/(μ0 J2,0). With locations fixed, the radial field is linear in m and b. A scaled two-column least-squares system is solved and converted back into μ and J2. This analytical property does not generalize to arbitrary 3D density inversion.')
tbl([['Model run','Recovered μ (km³/s²)','Recovered J2'],['Ground truth',format(float(fit['true']['mu_km3_s2']),'.9f'),format(float(fit['true']['j2']),'.12f')],['Perturbed observations',format(float(fit['noisy']['mu_km3_s2']),'.9f'),format(float(fit['noisy']['j2']),'.12f')],['Clean observations',format(float(fit['noiseless']['mu_km3_s2']),'.9f'),format(float(fit['noiseless']['j2']),'.12f')]], [160,162,170])
img('figures/06_synthetic_observations.png',466,205)
p('Figure 2. Deterministic simulated observations, not an instrument dataset.','Smallx')
page()
# 6
h('5. Calculated 3D field and potential surfaces')
img('figures/01_radial_gravity_surface.png',476,270)
p('Figure 3. Actual paceval radial gravity field over the defined 61 × 61 elevation–latitude grid.','Smallx')
img('figures/03_potential_surface.png',476,265)
p('Figure 4. The corresponding potential from an independent persistent paceval expression.','Smallx')
page()
# 7
h('6. Spatial effects of the quadrupole')
img('figures/02_gravity_contours.png',478,260)
p('Figure 5. Radial field magnitude contours from 3,721 paceval calculations.','Smallx')
img('figures/04_quadrupole_contours.png',478,260)
p('Figure 6. Modeled degree-2 contribution relative to the monopole field.','Smallx')
page()
# 8
h('7. Sensitivity and inverse-model interpretation')
img('figures/05_j2_sensitivity.png',479,270)
p('Figure 7. Analytical J2 derivative evaluated directly by paceval.','Smallx')
img('figures/07_recovered_j2.png',479,260)
p('Figure 8. Recovery of the coefficient from separate synthetic perturbed and clean surveys.','Smallx')
page()
# 9
h('8. Numerical verification, reproduction and scope')
p('The original paceval SDK was executed under Linux with the project CMake configuration. CTest passed; the experiment exported 960 observations, a complete 3,721-point numerical surface, 3,008 scalar calls, 2,048 checked additional batch outputs and 32 analytical derivative spot checks. A separate Python high-precision program validated 202 selected outputs using 80-digit arithmetic. The detailed numerical comparison files remain in the technical results folder, rather than being presented as a C++/paceval performance or precision competition.')
p('The clean survey recovers the defined ground-truth parameters. The perturbed survey demonstrates the effect of an artificial observation perturbation and the geometry of this particular inverse model. Independent holdout points test whether the recovered parametric model reproduces the synthetic truth at locations excluded from fitting.')
sh('Important scientific boundaries')
p('This is a two-parameter, degree-2, radial-component demonstration. It is not a full vector gravity model, geoid, density inversion, measured gravity anomaly, certified interval calculation, or operational physical geodetic product. Identifiability depends on the frozen model form and spatial sampling. A small residual on synthetic data does not establish correctness for real satellite or terrestrial measurements.')
sh('Reproduction from the project root')
p('cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/compatible/library.so<br/>cmake --build build -j<br/>ctest --test-dir build --output-on-failure<br/>./build/gravity_inversion --out examples<br/>python3 src/verify_results.py<br/>python3 src/high_precision_reference.py<br/>python3 src/make_figures.py','Smallx')
page()
# 10
h('9. Research interpretation and technical references')
p('The original pilot question asked whether mathematical forward expressions for gravitational inversion can be prepared, reused and independently checked. The executed study supports that specific feasibility claim: a coherent potential and radial-gravity family was calculated with persistent paceval graphs, its sensitivities were checked, and an inverse problem using its outputs recovered known parameters on synthetic samples. The host-side inverse solver remains an independently implemented component.')
sh('Current state of practice and next experiments')
p('The next scientifically useful step is to replace the synthetic degree-2 response with a clearly licensed gravity field or controlled geophysical survey, define observational and model covariance, use appropriate higher-degree harmonics or 3D density contrast forward modeling, and assess regularization and identifiability. A partner-grade application would also need validated coordinate systems and gravity conventions, instrument correction pipelines, uncertainty budgets, and external ground truth.')
sh('Selected primary technical sources')
for s in [
 'ICGEM, International Centre for Global Earth Models: gravity theory and functionals. https://icgem.gfz.de/theory',
 'ICGEM, model conventions and observables. https://icgem.gfz.de/faq',
 'SimPEG, gravity integral forward and inverse modeling. https://github.com/simpeg/simpeg/blob/main/simpeg/potential_fields/gravity/simulation.py',
 'GFZ Data Services (2026), WHU-CASM-UGM2025 combined global gravity model, DOI:10.5880/icgem.2026.002.',
 'paceval Mathematical Engine, official C/C++ API, version 4.25. https://paceval.com/api/'
]:p(s,'Smallx')
sh('Delivered package')
p('README.md; src/gravity_inversion.cpp; src/CMakeLists.txt; src/paceval_main.h; src/paceval_main.cpp; reference, figure and document generator scripts; CSV observations/field values; reproducibility audits; eight genuine PNG and PDF scientific figures; one conceptual hero illustration. No bundled runtime binary, speed comparisons or separate LICENSE_NOTICE.md.')
p('Conclusion: a positive, reproducible mathematical feasibility result with strict separation between gravity-model arithmetic, the host inverse algorithm and unvalidated real-world geodesy.','Bodyx')
SimpleDocTemplate(str(PDF),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=48,bottomMargin=63,title='WP_033 Forward Expressions in Gravitational Inversion',author='paceval research demonstrator').build(story,onFirstPage=footer,onLaterPages=footer)
print('Created',PDF)
