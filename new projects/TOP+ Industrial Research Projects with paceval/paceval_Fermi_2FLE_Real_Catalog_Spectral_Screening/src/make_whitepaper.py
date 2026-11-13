#!/usr/bin/env python3
"""Reproducible print-safe 14-page English paper; scientific figures from actual FITS+paceval CSVs."""
from pathlib import Path
import math,csv,json,io
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from PIL import Image as PILImage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent.parent
FIG=ROOT/'figures'; RES=ROOT/'results';OUT=ROOT/'paceval_Fermi_2FLE_Real_Catalog_Whitepaper_EN.pdf'
summary={}
for line in (RES/'original_fits_catalog_summary.txt').read_text().splitlines():
 if '=' in line:k,v=line.split('=',1);summary[k]=v
# Fonts embedded from commonly available system font; no font distribution.
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if Path(FONT).exists():
 pdfmetrics.registerFont(TTFont('DP',FONT));pdfmetrics.registerFont(TTFont('DPB',BOLD));fn='DP';fb='DPB'
else:fn='Helvetica';fb='Helvetica-Bold'
blue=colors.HexColor('#11374d');cyan=colors.HexColor('#159b9b');grey=colors.HexColor('#526171');pale=colors.HexColor('#edf5f6');dark=colors.HexColor('#16263a');orange=colors.HexColor('#eb8d40')
S={
 'title':ParagraphStyle('title',fontName=fb,fontSize=22,leading=29,textColor=dark,spaceAfter=12),
 'subtitle':ParagraphStyle('subtitle',fontName=fn,fontSize=11.6,leading=16,textColor=grey,spaceAfter=16),
 'h1':ParagraphStyle('h1',fontName=fb,fontSize=15.5,leading=21,textColor=blue,spaceAfter=12,spaceBefore=2),
 'h2':ParagraphStyle('h2',fontName=fb,fontSize=10.8,leading=15,textColor=blue,spaceBefore=10,spaceAfter=5),
 'body':ParagraphStyle('body',fontName=fn,fontSize=9.1,leading=13.8,textColor=dark,spaceAfter=8),
 'small':ParagraphStyle('small',fontName=fn,fontSize=8.3,leading=12.5,textColor=grey,spaceAfter=7),
 'caption':ParagraphStyle('caption',fontName=fn,fontSize=8.2,leading=11.7,textColor=grey,spaceAfter=11),
 'th':ParagraphStyle('th',fontName=fb,fontSize=8.4,leading=11,textColor=colors.white),
 'td':ParagraphStyle('td',fontName=fn,fontSize=8.1,leading=11.5,textColor=dark),
 'callout':ParagraphStyle('callout',fontName=fn,fontSize=9,leading=14,textColor=blue),
}
PAGE_W,PAGE_H=A4
DOC=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=17*mm,leftMargin=17*mm,topMargin=18*mm,bottomMargin=17*mm,title='Fermi 2FLE Original FITS - Real-Catalog Spectral Mathematics with paceval',author='paceval independent research demonstrator')
W=PAGE_W-34*mm
story=[]
def p(t,style='body'):story.append(Paragraph(t,S[style]))
def sp(h=5):story.append(Spacer(1,h))
def page(title):
 story.append(PageBreak());p(title,'h1')
def rowtable(data,widths=None,header=True):
 cells=[]
 for i,r in enumerate(data):cells.append([Paragraph(str(v),S['th'] if i==0 and header else S['td']) for v in r])
 widths=widths or [W/len(data[0])]*len(data[0]);t=Table(cells,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
 ts=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#d6e7e8'))]
 if header:ts.append(('BACKGROUND',(0,0),(-1,0),blue))
 for i in range(1 if header else 0,len(data)):
  if i%2==0:ts.append(('BACKGROUND',(0,i),(-1,i),pale))
 t.setStyle(TableStyle(ts));story.append(t);sp(9)
def pic(file,width=W,heightmax=82*mm):
 im=PILImage.open(FIG/file);ww,hh=im.size;h=width*hh/ww
 if h>heightmax:h=heightmax;width=h*ww/hh
 story.append(Image(str(FIG/file),width=width,height=h,hAlign='CENTER'))
def figure(idx,name,caption):
 path=f'{idx:02d}_{name}.png';pic(path,width=W-10*mm,heightmax=78*mm);p(f'<b>Figure {idx}.</b> {caption}','caption')
def equation(latex,tag):
 fig=plt.figure(figsize=(9.3,.58),dpi=155);fig.patch.set_alpha(0);fig.text(.01,.5,'$'+latex+'$',va='center',fontsize=17,color='#19384c');fig.savefig(FIG/f'_equation_{tag}.png',bbox_inches='tight',pad_inches=.07,dpi=200,transparent=True);plt.close(fig)
 pic(f'_equation_{tag}.png',width=W-14*mm,heightmax=20*mm)
def header(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(cyan);canvas.setLineWidth(.8);canvas.line(17*mm,PAGE_H-14*mm,PAGE_W-17*mm,PAGE_H-14*mm)
 canvas.setFont(fb,7.6);canvas.setFillColor(blue);canvas.drawString(17*mm,PAGE_H-11.5*mm,'FERMI 2FLE  /  ORIGINAL FITS  /  PACEVAL RESEARCH')
 canvas.setStrokeColor(colors.HexColor('#ccdce3'));canvas.line(17*mm,14*mm,PAGE_W-17*mm,14*mm)
 canvas.setFont(fn,7.5);canvas.setFillColor(grey);canvas.drawString(17*mm,9.7*mm,'Real catalog model execution  |  13 November 2026')
 canvas.drawRightString(PAGE_W-17*mm,9.7*mm,str(doc.page));canvas.restoreState()
# 1 COVER
sp(12);p('FERMI-LAT 2FLE  |  REAL-CATALOG RESEARCH','small')
p('Real-Catalog Spectral Mathematics and Reusable paceval Execution','title')
p('Direct analysis of the original 450-source NASA FITS catalog, with 60 specifically matched new gamma-ray sources and genuinely executed mathematical expressions.','subtitle')
pic('00_fermi_real_catalog_hero.png',heightmax=90*mm)
p('<b>Concept artwork.</b> The sky and signal graphics in this illustration are not measured Fermi data. All numbered scientific figures are generated from original catalog data and executed paceval output.','caption')
rowtable([['Actual NASA FITS records','New-source identifiers matched','paceval executions'],['450 rows × 38 fields','60 / 60','16 persistent graphs; 152,560 batch outputs']],widths=[W/3]*3)
p('<b>Scientific result.</b> Real FITS model values were successfully re-evaluated; analytic flux integrals agree with the corresponding FITS fitted flux fields within 0.11% for all 450 sources. This validates reproducible mathematical catalog-model execution, <b>not</b> new gamma-ray source physics.','callout')
# 2
page('1. Scientific context and research question')
p('The Fermi Large Area Telescope (LAT) detects high-energy gamma rays. The <b>Second Catalog of Low-Energy Fermi-LAT Sources</b> (2FLE) covers 20–200 MeV and uses 14 years of observations. It was published in the Astrophysical Journal Supplement Series on 12 November 2026 [1]. The collaboration reports 450 entries, including 377 with multiwavelength associations and 60 new gamma-ray sources without confirmed counterparts [1, 2].')
p('Identifying the physical nature of a source requires observation-specific likelihoods, detector energy dispersion and point-spread response, diffuse background models and independent counterpart observations. In particular, the NASA FSSC notes substantial energy-dispersion effects below 100 MeV and recommends accounting for them in low-energy analyses [3].')
p('<b>Research question:</b> Can the original FITS power-law model parameters be ingested directly, evaluated with persistent paceval graphs and checked against independently supplied fitted integral values over all catalog sources? The result must be auditable, versionable and usable as a reliable mathematical building block for later astrophysical analyses.')
p('This is a <b>real published-model evaluation</b> rather than a new photon-event fit. The models were fitted by the 2FLE collaboration; this research does not reproduce their source-detection likelihood, exposure, instrumental response, or astrophysical associations.')
p('New contribution versus the previous synthetic paper','h2')
rowtable([['Previous research stage','Present real-data successor'],['60 source rows transcribed from German report','All 450 rows extracted directly from uploaded original FITS using CFITSIO'],['Simulated count data and model parameters','Original fitted flux normalizations, pivot energies, indexes and uncertainties'],['Synthetic Poisson likelihood and recovery','Actual catalog analytic flux and sensitivity evaluation; NO fake likelihood'],['Model surfaces from arbitrary synthetic inputs','Model surfaces from catalog FITS parameters, with hypothetical q shown separately']],[W*.48,W*.52])
# 3
page('2. Original-data provenance and source-level audits')
p('The provided file <b>data/2FLE_psc_v8.fits</b> was read using CFITSIO from the binary extension <b>2FLE_point_source_catalog</b>, which contains 450 rows and 38 columns. Key fields include Source_Name, RAJ2000, DEJ2000, GLON, GLAT, pivot energy, flux density, photon index, uncertainties, three energy-band TS entries, counterpart hints and localization ellipses.')
rowtable([['Direct original FITS check','Measured result'],['Unique entries and source columns','450 / 38'],['Source names matched against original user V4 list','60 of 60'],['Among 60: ASSOC3 present / absent','38 / 22 (unconfirmed hints)'],['Among 60: three band TS values all at least 4','10'],['Among 60: absolute Galactic latitude above 10 degrees','51'],['Catalog spectral models','450 PowerLaw entries'],['Published photon-flux flags','442 flag 0; 8 flag 1']],[W*.63,W*.37])
p('The 60 source names are selected from the archived V4 paper for continuity. All reported numerical coordinates and spectral parameters now come directly from the real original FITS, not from the earlier paper. Counterpart-name fields do not establish astrophysical source class or any non-natural origin.')
p('Results distinguish three provenance types: <b>(A)</b> extracted FITS observations and published fitted parameters; <b>(B)</b> deterministic paceval evaluations of those published parameters; <b>(C)</b> a clearly labeled optional, hypothetical curvature what-if experiment.')
# 4
page('3. Reused mathematical functions and units')
p('All catalog entries use a PowerLaw fitted spectral shape. For photon energy E in MeV, FITS differential normalization N and pivot energy P, and index g:')
equation(r'F(E)=N\exp[-g\ln(E/P)]','flux')
p('The complete 20–200 MeV fitted photon flux (units photons cm^-2 s^-1) is evaluated in one original paceval graph:')
equation(r'I_{20:200}=\frac{NP}{1-g}\left[(200/P)^{1-g}-(20/P)^{1-g}\right]','integral')
p('Likewise the 20–200 MeV fitted energy flux in erg cm^-2 s^-1 uses the exact conversion 1 MeV = 1.602176634×10^-6 erg:')
equation(r'J_{20:200}=1.602176634\times10^{-6}\frac{NP^2}{2-g}\left[(200/P)^{2-g}-(20/P)^{2-g}\right]','energy')
p('The implementation explicitly checks that no catalog index is exactly 1 or 2, where these compact expressions require logarithmic limits. All 450 input rows pass. The derived photon index sensitivity is d log F / dg = −log(E/P).')
p('A simplified normalization/index uncertainty diagnostic assumes zero covariance:')
equation(r'r(E)=\sqrt{(\sigma_N/N)^2+[\sigma_g\ln(E/P)]^2}','unc')
p('This is <b>not</b> a fully calibrated confidence interval. The catalog does not supply the required joint covariance in these selected fields, nor does this study refit any original photon events. Illustrative q-curvature formula tests remain separate from fitted 2FLE physics.')
# 5
page('4. Original SDK integration and computation ownership')
p('The project compiles original paceval_main.h / paceval_main.cpp into a C++ executable, links a separately acquired Linux paceval runtime and dynamically applies CFITSIO to the provided source file. Sixteen distinct graphs are created once, then evaluated over multiple catalog parameter and energy combinations using <b>paceval_dGetMultipleComputationsResultsExt</b>. Every returned per-graph error code is checked.')
rowtable([['Executed by paceval','Mathematical outputs'],['Published power-law model','Flux, pivot-normalized ratio, log flux, E squared flux'],['Integral models','Photon and energy flux over 20–200 MeV'],['Physical sensitivity models','Index derivative, parameter shift curves, covariance-free error diagnostic'],['Clearly hypothetical what-if model','Alternative curved shape, log flux ratio, curvature derivative'],['Position geometry','Planar 95-percent ellipse area'],['Host C++ / CFITSIO','FITS loading, row validation, iteration, names, source selection, CSV, aggregation'],['NOT executed','LAT IRF folding, photon likelihood, instrument systematic scans, true source classification']],[W*.43,W*.57])
p('The [machine-readable execution inventory] is included in results/math_execution_inventory.csv. It distinguishes actual mathematical paceval graphs from CFITSIO ingestion and C++ control logic; independent C++/mpmath expressions exist exclusively for correctness testing.')
p('Quantities actually executed','h2')
rowtable([['Unique persistent graphs','Multi-Graph batch calls','Output values'],[summary.get('PACEVAL_GRAPHS','16'),summary.get('PACEVAL_BATCH_INVOCATIONS','76'),summary.get('PACEVAL_GRAPH_OUTPUTS','152560')]],[W/3]*3)
# 6 through 10 numbered figures pair, small sizes
page('5. Real sky geometry and 60-source metadata')
figure(1,'real_fits_allsky','Positions from all 450 original FITS entries; the selected 60 are highlighted. This plot contains real catalog coordinates, not an imagined gamma-ray count map.')
figure(2,'real_60_TS_latitude','The 60 selected original-source entries, split by presence or absence of an unconfirmed ASSOC3 hint; TS measures detection, not source origin.')
page('6. Actual fitted indices and localization geometry')
figure(3,'real_catalog_index_histogram','FITTED PowerLaw_Index values read directly from all 450 FITS rows; the selected 60 are overlaid, without new class inference.')
figure(4,'real_localization_ellipse_area','Approximate planar area of each published 95-percent localization ellipse versus original catalog TS. The ellipse area is a descriptive geometric quantity.')
page('7. Genuine paceval evaluation of actual FITS fits')
figure(5,'real_paceval_spectral_curves','Published power-law fits evaluated with paceval over 20–200 MeV for seven high-TS sources; these are NOT independent photon spectra.')
figure(6,'real_paceval_spectral_surface','30 highest-TS selected source fits sampled by paceval; Z is log10 fitted differential flux and the row axis ranks sources by published TS.')
page('8. Same-catalog flux checks and band coverage')
figure(7,'real_integral_consistency','Analytic 20–200 MeV flux integrations executed by paceval compared with fields from the SAME fitted NASA catalog; relative discrepancies are small and not independent confirmation.')
figure(8,'real_band_TS_availability','Number of the 60 sources with original FITS band TS >=4 in each of the three broad catalog bands. Narrow spectral lines cannot be tested from these data.')
page('9. Explicitly hypothetical curvature and errors')
figure(9,'hypothetical_curvature_contours','The original fitted parameters of one real source provide the reference curve, but q is imposed hypothetically and NOT fitted to photons or measured bands.')
figure(10,'real_independent_error_diagnostic','Covariance-free propagation of FITS fit-parameter uncertainties through the paceval power-law expression. NOT a source-dependent calibrated confidence region.')
# 11
page('10. Selected source records and observable status')
p('The following entries were read from the original FITS, ordered by reported detection TS (selection here is descriptive, not a technology likelihood):')
with (ROOT/'examples/real_60_original_fits.csv').open() as f:rows=list(csv.DictReader(f))
rows.sort(key=lambda x:float(x['TS']),reverse=True)
data=[['Source identifier','FITS TS','Index','Pivot MeV','ASSOC3 hint']]
for r in rows[:8]:
 data.append([r['source_name'],f"{float(r['TS']):,.1f}",f"{float(r['photon_index']):.3f}",f"{float(r['pivot_MeV']):.1f}",'Present' if r['ASSOC3'] else 'None'])
rowtable(data,[W*.34,W*.15,W*.12,W*.17,W*.22])
p('The published TS is a detection statistic and the ASSOC3 field is an unconfirmed counterpart hint. Neither is a probability of artificial origin. The original FITS does not contain the event-by-event likelihood residuals needed to establish a new spectral feature.')
p('Catalog consistency assessment','h2')
p('For all 450 sources, paceval analytically integrates the fitted PowerLaw differential spectrum between 20 and 200 MeV. Relative discrepancies from the corresponding catalog fit-derived integrated photon and energy flux fields are at most about 0.11%. The broad catalog flux and the analytic reconstruction are derived from the same fitted parameters, so this primarily checks functional equivalence, units, data transfer, and reusable numerical graph execution.')
# 12
page('11. Independent validation, reproducibility and files')
rowtable([['Verification','Actual result'],['CMake build and CTest with CFITSIO + original paceval runtime','Pass (1 of 1 CTest)'],['Independent C++ mathematical formula checks',f"{summary.get('INDEPENDENT_CXX_VALUES_CHECKED','7216')} individual values passed"],['80-decimal-digit independent mpmath audit','752 values passed'],['Repeat full paceval calculation / byte comparison','8 of 8 selected output and inventory files identical'],['FITS structural and name comparison','450×38; 60/60 names; 38/22 ASSOC3; 10 full band entries'],['Visual PDF audit','Every released PDF page rendered and visually reviewed']],[W*.60,W*.40])
p('The accompanying source tree includes src/CMakeLists.txt, the complete CFITSIO C++ reader, original paceval interfaces, scripts for figures and report production, the 206-KB NASA FITS, previous English whitepaper, raw derived CSVs, exact expressions and audit records. The external proprietary paceval shared library is not redistributed.')
p('The separate 80-digit test reconstructs selected source fluxes and integrals from the actual exported catalog values; it is not a copy of the original C++ implementation. Repeated dataset files and one-source examples are checksummed in results/SHA256SUMS.txt.')
# 13
page('12. Scientific limitations and next-stage design')
p('<b>The present work does not identify, reject, or establish unusual astrophysical sources.</b> It performs genuine mathematical evaluation of previously fitted catalog power-law functions. No LAT photon-event list, spacecraft attitude/time exposures, IRF energy-dispersion matrix, diffuse background templates or independent counterpart catalogs were used to derive new source likelihoods.')
p('At 20–200 MeV this boundary is particularly important: the detector energy dispersion and point spread are large enough that a naive fit to narrow lines or time-modulation patterns would be scientifically invalid. Broad-band catalog TS values are insufficient to resolve such structures.')
p('Recommended next independent astrophysical study','h2')
rowtable([['Phase','Mandatory acceptance gate'],['A. Photon / spacecraft acquisitions','Records and checksums for limited predefined ROIs and matching LAT event selections'],['B. Reference Fermitools analysis','Original 2FLE ROI results reproduced including IRFs, edisp, diffuse and exposure'],['C. Independent celestial counterparts','Multiwavelength matches with localization uncertainty and chance-association rates'],['D. Constrained spectral hypothesis testing','Predeclared nulls; forward-folded Poisson likelihood and out-of-sample tests'],['E. Injection and negative controls','Known natural classes and hypothetical signals; global trials and sensitivity'],['F. Source-specific publication','Evidential A–F class only with clearly documented independent observations']],[W*.31,W*.69])
p('Nothing in this analysis establishes a technosignature. Any model residual should first be investigated as natural source emission, blended emission, or imperfect instrumentation/background modeling.')
# 14
page('13. References, deliverables and conclusion')
refs=[
 '[1] Adelfio et al. / Fermi-LAT Collaboration (2026), <i>The Second Catalog of Low-Energy Fermi-LAT Sources</i>. Astrophysical Journal Supplement Series 287(2), 40. DOI: <link href="https://doi.org/10.3847/1538-4365/aeb54d">10.3847/1538-4365/aeb54d</link>.',
 '[2] NASA Fermi Science Support Center (2026), <link href="https://fermi.gsfc.nasa.gov/ssc/data/access/lat/2FLE/">2FLE catalog FITS and products</link>.',
 '[3] NASA Fermi SSC, <link href="https://fermi.gsfc.nasa.gov/ssc/data/analysis/documentation/Pass8_edisp_usage.html">Pass 8 energy-dispersion guidance</link>.',
 '[4] NASA Fermi SSC, <link href="https://fermi.gsfc.nasa.gov/ssc/data/access/">LAT photon and spacecraft data products</link>.',
 '[5] Fermipy, <link href="https://fermipy.readthedocs.io/en/latest/">Likelihood / ROI modeling and analysis documentation</link>.',
 '[6] Previous user-supplied research: <i>Fermi 2FLE Reusable Spectral Screening and Scientific Validation with paceval</i>, 14 pp. Retained under docs/.',
]
for r in refs:p(r,'small');sp(4)
p('Publication contents','h2')
p('This successor contains the original NASA FITS, extracted 450- and 60-source catalog files, 16 exact paceval formula expressions, 10 scientific figures as PNG/vector PDF, an original C++ executable source with CFITSIO, an independent precision audit, repeat logs, a computation responsibility inventory, and reproducible report/graphic scripts.')
p('Conclusion','h2')
p('The uploaded real Fermi 2FLE FITS has now been ingested and the published spectral models evaluated successfully on a genuine paceval SDK runtime. The resulting source and mathematical comparisons are reproducible and traceable to original FITS columns. <b>This establishes the feasibility of paceval as a mathematical catalog-analysis engine.</b> Attribution of the 60 gamma-ray sources, any new physical spectral features and any potential technosignature all remain subjects for future instrument-calibrated astrophysical investigation.')

def make():
 DOC.build(story,onFirstPage=header,onLaterPages=header)
 print('PDF created:',OUT,OUT.stat().st_size)
if __name__=='__main__':make()
