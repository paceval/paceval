#!/usr/bin/env python3
"""Generate the English 2FLE/paceval methods-pilot report from verified project outputs.
Figures 01-02: catalog metadata transcribed from source report. Figures 03-10:
actual paceval synthetic outputs. Concept title image is not research data.
"""
from pathlib import Path
import csv, json, math, os
import fitz
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
R=Path(__file__).resolve().parents[1]
out=R/'paceval_Fermi_2FLE_Spectral_Screening_Whitepaper_EN.pdf'
summary=dict(l.strip().split('=',1) for l in (R/'results/execution_summary.txt').read_text().splitlines() if '=' in l)
audit=json.loads((R/'results/high_precision_audit.json').read_text())
assert summary['status']=='PASS' and audit['status']=='PASS'

pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
NAVY=colors.HexColor('#17283D');TEAL=colors.HexColor('#128F9D');MUTED=colors.HexColor('#5B6874');LIGHT=colors.HexColor('#E8F3F3');AMBER=colors.HexColor('#DC9D42')
PAGE_W,PAGE_H=A4
W=PAGE_W-82
styles={
 'title':ParagraphStyle('cover_t',fontName='DejaVu-Bold',fontSize=20,leading=26,textColor=NAVY,spaceAfter=9),
 'subtitle':ParagraphStyle('cover_s',fontName='DejaVu',fontSize=11.2,leading=17,textColor=TEAL,spaceAfter=12),
 'h1':ParagraphStyle('h1',fontName='DejaVu-Bold',fontSize=16,leading=22,textColor=NAVY,spaceAfter=11),
 'h2':ParagraphStyle('h2',fontName='DejaVu-Bold',fontSize=11.5,leading=16,textColor=TEAL,spaceBefore=9,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='DejaVu',fontSize=9.2,leading=14.0,textColor=NAVY,spaceAfter=9),
 'small':ParagraphStyle('small',fontName='DejaVu',fontSize=8.4,leading=12.3,textColor=NAVY,spaceAfter=7),
 'caption':ParagraphStyle('caption',fontName='DejaVu',fontSize=7.7,leading=11,textColor=MUTED,spaceBefore=3,spaceAfter=10),
 'ref':ParagraphStyle('ref',fontName='DejaVu',fontSize=8,leading=12.5,textColor=NAVY,spaceAfter=9),
 'banner':ParagraphStyle('banner',fontName='DejaVu-Bold',fontSize=9.2,leading=15,textColor=NAVY,spaceAfter=10),
}

def P(s,style='body'):return Paragraph(s,styles[style])
def H(s):return P(s,'h1')
def SH(s):return P(s,'h2')
def para(*ss):return [P(s) for s in ss]
def tab(rows,widths=None,head=True):
 dat=[[P(str(cell),'small') for cell in row] for row in rows]
 t=Table(dat,colWidths=widths or [W/len(rows[0])]*len(rows[0]),hAlign='LEFT',repeatRows=1 if head else 0)
 cmds=[('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),1,TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F1F6F7')])]
 if head:cmds += [('BACKGROUND',(0,0),(-1,0),LIGHT)]
 t.setStyle(TableStyle(cmds));return t

def fig(name,width=463):
 path=R/'figures'/name
 im=PILImage.open(path);w,h=im.size
 return Image(str(path),width=width,height=width*h/w)

def equation(expr,name):
 p=R/'figures'/f'_eq_{name}.png'
 if not p.exists():
  f=plt.figure(figsize=(11,1.1));f.text(.03,.52,'$'+expr+'$',fontsize=30,ha='left',va='center',color='#14283D');f.savefig(p,dpi=175,transparent=True);plt.close(f)
 return Image(str(p),width=453,height=45.3)

def headerFooter(canv,doc):
 canv.saveState();i=doc.page
 if i>1:
  canv.setStrokeColor(TEAL);canv.setLineWidth(.65);canv.line(41,PAGE_H-39,PAGE_W-41,PAGE_H-39)
  canv.setFont('DejaVu-Bold',7.3);canv.setFillColor(TEAL);canv.drawString(41,PAGE_H-31,'PACEVAL  |  SCIENTIFIC RESEARCH DEMONSTRATOR')
 canv.setStrokeColor(colors.HexColor('#D3DEDF'));canv.line(41,35,PAGE_W-41,35)
 canv.setFont('DejaVu',7);canv.setFillColor(MUTED)
 canv.drawString(41,23,'2FLE / paceval  |  Synthetic spectral methods pilot  |  13 November 2026')
 canv.drawRightString(PAGE_W-41,23,str(i))
 canv.restoreState()

doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=41,leftMargin=41,topMargin=51,bottomMargin=49,title='Fermi-LAT 2FLE Spectral Screening with paceval: A Reproducible Methods Pilot',author='Independent mathematical research demonstrator',subject='Real 2FLE metadata and synthetic paceval spectral computations')
s=[]
# PAGE 1 cover
s+=[Spacer(1,7),P('FERMI-LAT 2FLE','subtitle'),P('Reusable Spectral Screening<br/>and Scientific Validation<br/>with paceval','title'),P('A reproducible C++ mathematical research demonstrator using real catalog metadata and explicitly synthetic spectral experiments','subtitle'),fig('00_fermi_2fle_hero.png',W),Spacer(1,10),P('<b>Research outcome.</b> 17 verified reusable paceval graphs; 1,566,545 Multi-Graph-Batch outputs; 60 source metadata records transcribed from the supplied V4 report; 60 independent synthetic spectral mock datasets.','banner'),P('<b>Scientific boundary:</b> no original FITS file or LAT photon data were available here. No astrophysical source classification, calibrated Fermi likelihood or technosignature test was performed.','small'),P('The title artwork is a concept illustration, not a measured gamma-ray sky image. All model figures are identified by their actual data provenance.','caption'),PageBreak()]
# PAGE 2
s += [H('1. Introduction: the scientific use case and current state of the art')]
s += para('The Fermi Large Area Telescope (LAT) observes gamma rays from the sky. The Second Catalog of Low-Energy Fermi-LAT Sources (2FLE), released as preliminary catalog data in October 2026 and published in a peer-reviewed journal on 12 November 2026, analyzes 14 years of observations from 20 to 200 MeV and reports 450 detected sources. The collaboration identifies multi-wavelength associations for 377 sources; 73 lack confirmed multi-wavelength identifications, including 60 newly cataloged gamma-ray sources. These totals come from the NASA/Fermi catalog publication, not from a newly executed FITS query in this research package [1, 2].',
'An unidentified gamma-ray source does not imply anomalous physics or intelligent technology. Standard astrophysical explanations include active galactic nuclei, pulsars, supernova remnants, unresolved populations, time-variable sources and imperfect background or instrument modeling. The central scientific question is which source explanations remain compatible with calibrated photon data, independently matched multi-wavelength observations and stringent statistical tests.',
'Current Fermi analysis uses event and spacecraft data, response functions, diffuse background templates, and forward-folded Poisson likelihoods over instrument-aware regions of interest. Fermipy provides a documented interface for model fitting, spectral energy distributions, residual maps and related LAT analyses [3, 4]. The 2FLE paper follows a modern maximum-likelihood catalog approach, rather than source identification by a few broad-band ratios.',
'Here we intentionally investigate a narrower, complementary computational kernel: evaluate reusable mathematical spectral models, positive synthetic count expectations, Poisson log-likelihood contributions, spectral differences and analytic sensitivities for a controlled synthetic workload. Those numerical functions are useful building blocks for a future physics-based research pipeline, but cannot replace real instrument calibration or source identification.')
s += [SH('Practical example'),P('A research engineer explores different mathematical spectral curves over the same energy range. The C++ program generates a fixed set of independent trial parameters; paceval executes the registered formulas in batches; the host sums likelihood contributions and selects the maximum on the specified grid. The result is a reproducible synthetic methods check, not an interpretation of a real gamma-ray source.'),PageBreak()]
# PAGE 3
s += [H('2. Data integrity and explicit provenance boundaries')]
s += [P('The user supplied a 13-page German V4 research paper including Appendix A with 60 source metadata rows. The original NASA FITS file, previously executed fermi_filter.cpp, historical CSVs and Pass-8 event files were not present as accessible inputs. This project extracts only the source names, catalog TS values, Galactic latitudes, usable broad-band counts and unconfirmed ASSOC3 text from those Appendix A tables.')]
s += [tab([['Data family','Status and source'],['450 total / 377 identified / 73 without associations','Published NASA / Fermi-LAT 2026 catalog paper; not recounted from FITS here'],['60 metadata entries','User V4 appendix, transcribed and checked for 60 unique records'],['22 without, 38 with ASSOC3 hints','Reconstructed from user V4 Appendix A; hints are not identifications'],['10 rows with three usable broad bands','V4 metadata under its TS-band criterion'],['Historical 110,700 batch results','Mentioned in the user V4 paper but not reproducible here without original accompanying artifacts'],['New synthetic spectra','60 model-generated independent Poisson mock datasets; no Fermi photons'],['Cross-survey and photon analyses','Not performed; no astrophysical source classifications']],[W*.39,W*.61])]
s += [Spacer(1,9),P('The original 2FLE FITS revision is separately available from the NASA Fermi Science Support Center as a source for follow-up revalidation [2]. The presently included CSV may be regenerated from the user PDF and must not be silently relabeled as a direct extraction from the NASA FITS table.'),P('A 60-by-29 hypothesis matrix is included as a structured roadmap: all 1,740 cells are explicitly marked NOT_TESTED. They are placeholders for future evidence and carry no support/exclusion semantics.'),PageBreak()]
# PAGE 4
s += [H('3. Natural explanations and falsifiable technical hypotheses')]
s += [P('The supplied V4 research design enumerates 22 natural or non-technological explanation groups, N01-N22, and seven hypothetical technical signatures, T01-T07. A source-specific identification is valid only after independent data are evaluated under a declared statistical decision procedure.')]
s += [tab([['Natural/model class','Necessary external evidence'],['Active galaxies and jets (N01-N05)','Radio, optical, infrared, X-ray and GeV/TeV source counterparts and temporal consistency'],['Pulsars and nebulae (N06-N11)','Barycentric timing, pulsations, radio/X-ray structure, extended emission'],['Transients and source mixtures (N12-N18)','Event timing, spatial deblending, ephemerides and multiwavelength monitoring'],['Alternative physics and artifacts (N19-N22)','Physical morphology, diffuse template variants, IRFs, event-class and null-region controls']],[W*.44,W*.56])]
s += [SH('Why a gamma-ray peculiarity is not a technosignature')]
s += para('The seven technological models are hypothetical, not inferences from the catalog. Plausible tests might seek a narrowly specified line, robust periodic modulation, repeated transient patterns or independently confirmed correlations. Each requires distinct natural null hypotheses, instrument response effects, a predeclared detection statistic, trials correction and an injection-recovery sensitivity curve.',
'The frequently cited 511 keV annihilation line lies at 0.511 MeV, outside the 2FLE energy interval of 20-200 MeV. It is therefore not something a three-band 2FLE catalog summary can directly test. No generic "alien score" is defined or justified by this package.',
'The candidate-source list may guide observation planning, but neither a missing counterpart nor a statistically significant gamma-ray detection determines whether a source is natural, artificial or merely inadequately modeled.')
s += [PageBreak()]
# PAGE 5
s += [H('4. Defined analytical spectral models')]
s += [P('E is the photon energy in MeV and E0 is fixed to 100 MeV. N is a positive synthetic spectral normalization; gamma is the spectral slope, and q is a controlled curvature parameter. All model outputs below are in arbitrary synthetic units and are not a calibrated physical flux measurement.')]
s += [SH('Power law and log-parabolic family'),equation(r'F_{\rm PL}(E)=N\,\exp[-\gamma\,\ln(E/E_0)]','pl'),equation(r'F_{\rm LP}(E)=N\,\exp[-\gamma\,\ln(E/E_0)-q\,\ln^2(E/E_0)]','lp')]
s += [P('The library additionally defines simplified exponential-cutoff and smooth-bend reference curves and an independently preserved cubic-logarithmic second formula version. The chosen definitions are documented as literal paceval expressions in the formula registry. Algebraic compatibility is not a claim that any source follows these models.')]
s += [SH('Synthetic counting model, not a real LAT instrument response'),equation(r'\mu_i=b_i+A\,w_i\,F_{\rm LP}(E_i)','mu'),equation(r'\ell_i=n_i\ln\mu_i-\mu_i','ll')]
s += [P('The factor A, bin weight w and background b are toy model inputs. No LAT exposure, energy dispersion, point-spread function, diffuse sky model or telescope live-time is included. A factorial-free Poisson contribution is valid for comparisons on the same synthetic count sample but has no observational detection significance in this experiment.'),SH('Analytic spectral sensitivity'),equation(r'\frac{\partial\ln F_{\rm LP}}{\partial q}=-\ln^2(E/E_0)','sens'),PageBreak()]
# PAGE 6
s += [H('5. Original paceval SDK execution architecture')]
s += [P('The actual C++ executable links the original paceval_main.cpp/paceval_main.h interface to the separate original Linux runtime. 17 functions are registered exactly once and stored as reusable computation handles. The workload calls the Multi-Graph-Batch API to evaluate the mathematical functions across the trial energy/curvature arrays; scalar calls verify a representative set of handles.')]
s += [tab([['Mathematical or workflow task','Execution owner'],['Power law, log parabola and alternate spectral curves','paceval: five persistent expression graphs'],['Logarithmic flux ratio and explicit curvature sensitivity','paceval: two persistent expression graphs'],['Synthetic count expectations for several model families','paceval: four persistent expression graphs'],['Toy Poisson log-likelihood, deviance and residual','paceval: six persistent expression graphs'],['Stochastic count sampling, CSV, metadata validation','C++ host: deterministic seed, I/O and guard policy'],['Log-likelihood sum over bins; maximize across trial q','C++ host: stateful reduction and discrete selection'],['Instrument response folding and astrophysical model inference','Not implemented: requires Fermitools and physical observational inputs']],[W*.60,W*.40])]
s += [Spacer(1,8),P('The machine-readable results/math_execution_inventory.csv lists the exact expression, version, units, actual API path and execution owner. The run also tested invalid values and independent native mathematical references. It would be scientifically incorrect to count host-only stochastic sampling as a paceval capability.'),SH('Version control'),P('Both log-parabola formula versions remain independent registered handles. The second introduces a declared cubic logarithmic term; it does not overwrite the first. Every changed function is separately available for audit and comparison.'),PageBreak()]
# PAGE 7
s += [H('6. Deterministic workload and independently checked outcomes')]
s += [tab([['Executed and checked quantity','Result'],['Appendix-A metadata rows transcribed and checked','60 (22 / 38 ASSOC3 groups; 10 rows with three usable bands)'],['Genuine persistent paceval mathematical graphs','17'],['Synthetic spectral mock sources / bins','60 / 24'],['Grid trial curvature parameters per source','61'],['Synthetic source-parameter candidates','3,660'],['Full response-surface points','4,225 (65 × 65)'],['Verified real paceval batch graph outputs','1,566,545'],['Real paceval Multi-Graph batch invocations','378'],['Native reference comparison checks','11,062 values passed'],['Independent 80-decimal-digit checks','1,096 values passed'],['Recovered injected curvature within 0.05','59 of 60 synthetic cases'],['Complete replay (byte identical)','8 of 8 tracked files'],['CMake and CTest','Build succeeded; 1 / 1 passed']],[W*.58,W*.42])]
s += [Spacer(1,10),P('The result of 59/60 is valid only within a specified synthetic toy detector, its generated counts and the fixed grid. It is neither a source association rate, astrophysical discovery power nor an estimate of false-positive rate on Fermi data.'),P('A separate historical analysis described in the user V4 report claims 110,700 batch values against the NASA FITS catalog. That historical claim is not presented here as newly reproduced, because the historical input files and C++ program were not supplied with the present attachment.'),PageBreak()]

def pair(title,desc,a,ca,b,cb):
 return [H(title),P(desc,'small'),fig(a,410),P(ca,'caption'),fig(b,410),P(cb,'caption'),PageBreak()]
# PAGES 8..12
s += pair('7. Results I: the 60 real source metadata entries','The following plots visualize published metadata transcribed from the user-provided V4 paper. They are NOT independent observed spectral fits.',
 '01_catalog_TS_vs_latitude.png','Figure 1. Published TS versus absolute Galactic latitude, colored by whether the V4 appendix includes an unconfirmed ASSOC3 hint.',
 '02_catalog_band_availability.png','Figure 2. Only three broad-band counts at most are available; 10 sources have three bands under the V4 selection rule.')
s += pair('8. Results II: high-dimensional synthetic model behavior','Both graphics originate from the executed paceval surface CSV. They are synthetic mathematical response functions, not LAT measurements.',
 '03_synthetic_logparabola_surface.png','Figure 3. 3D log-parabola surface over photon energy and synthetic curvature q, computed on a 65 × 65 grid by paceval.',
 '04_synthetic_curvature_contours.png','Figure 4. Analytical log flux ratio of log parabola to power law, evaluated by paceval over the same parameter domain.')
s += pair('9. Results III: alternate model families and sensitivity','Model comparisons show how reusable mathematical expressions vary, without implying that one astrophysical source class is established.',
 '05_synthetic_model_families.png','Figure 5. Three analytically specified synthetic spectral families for one fixed trial curvature.',
 '10_analytical_curvature_sensitivity.png','Figure 6. The explicit derivative of log flux with respect to curvature; the curve is mathematically defined and batch-evaluated by paceval.')
s += pair('10. Results IV: synthetic likelihood and recovery','For synthetic Poisson counts, the host sums actual paceval per-bin objective values and selects the best curvature on the declared fixed grid.',
 '06_synthetic_curvature_likelihood_scans.png','Figure 7. Difference from each maximum of the toy objective for three known injected curvature values.',
 '07_synthetic_injection_recovery.png','Figure 8. Injected versus selected synthetic curvature. There is no observational source classification in this plot.')
s += pair('11. Results V: recovery distribution and toy photon counts','These outputs demonstrate method reproducibility only. They are not calibrated detection sensitivity or real photon observations.',
 '08_synthetic_recovery_by_group.png','Figure 9. Recovered curvature distributions for three declared synthetic injection levels.',
 '09_synthetic_photon_bin_example.png','Figure 10. Poisson-drawn toy count samples and the actual paceval-computed expectation for one synthetic source identifier.')
# PAGE 13
s += [H('12. Scientific interpretation and limitations')]
s += para('The demonstrated result is a working mathematical expression engine for spectral candidates and synthetic likelihood contributions. It can help support a larger scientific workflow by making formula versions explicit, batch evaluation reproducible and mathematical responsibility auditable. It has not detected or classified any unusual or technological object.',
'A full gamma-ray source study requires the original 2FLE FITS data, LAT event and spacecraft products, calibrated instrument response, source-dependent backgrounds and multi-wavelength observations. The original 2FLE band is 20-200 MeV and the catalog contains only a limited set of broad energy bands; narrow spectral lines and precise temporal modulations cannot be established from these catalog metadata alone.',
'Any future anomaly statistic must be calibrated using background and instrument variations, pre-registered trial corrections, negative controls, injected natural and hypothetical signals, independent observation intervals and ideally independent instruments. A failure of conventional toy models to fit a source is not a license to infer technology.')
s += [SH('Prioritized research phases inherited from the V4 whitepaper')]
s += [tab([['Phase','Required gate before promoting science claims'],['P0–P1','Reacquire FITS + historical code; hash files and verify 450/60 and legacy 110,700 if possible'],['P2','External multiwavelength catalogs with positional uncertainty and chance associations'],['P3–P4','Validate pilot LAT ROIs, photon likelihood and diffuse/IRF systematic checks'],['P5','Physically constrained expression search on properly calibrated count expectations'],['P6','Predeclared T01–T07 falsification and blinded injection-recovery'],['P7','Evidence-based source-by-source 60-object scientific report']],[W*.21,W*.79])]
s += [PageBreak()]
# PAGE 14
s += [H('13. Reproducibility, external references and conclusion')]
s += para('To reproduce the executable result, configure CMake with an independently acquired compatible paceval Linux shared library, build from src/CMakeLists.txt, run the executable and execute CTest. The provided C++ program is deterministic under the stated seed; source data, formula registry, mathematical execution inventory, original results, independent Python checks and all figure generators are included in the GitHub project.',
'Build example: cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so; cmake --build build -j; ctest --test-dir build --output-on-failure; ./build/fermi_2fle_demo --out . --sources 60 --bins 24 --grid 61.',
'The scientific plots are generated from examples/*.csv by src/make_figures.py, the whitepaper by src/make_whitepaper.py, and the numerical checks by src/high_precision_reference.py and src/verify_results.py. No external runtime binary is redistributed. The original paceval SDK interfaces retain their copyright notices.')
s += [SH('Selected original and official sources')]
ref=[
'[1] Adelfio et al. / Fermi-LAT Collaboration (2026), The Second Catalog of Low-Energy Fermi-LAT Sources. Astrophysical Journal Supplement Series 287(2), 40. DOI: 10.3847/1538-4365/aeb54d. https://doi.org/10.3847/1538-4365/aeb54d',
'[2] NASA Fermi Science Support Center, 2FLE data products and FITS catalog. https://fermi.gsfc.nasa.gov/ssc/data/access/lat/2FLE/',
'[3] Fermi Science Support Center, photon/spacecraft products and catalogs. https://fermi.gsfc.nasa.gov/ssc/data/access/',
'[4] Fermipy collaboration, Fermipy documentation and likelihood workflow. https://fermipy.readthedocs.io/en/latest/',
'[5] NASA FSSC LAT background models. https://fermi.gsfc.nasa.gov/ssc/data/access/lat/BackgroundModels.html',
'[6] NASA / HEASARC, Fermi 4FGL-DR4 source catalog. https://heasarc.gsfc.nasa.gov/W3Browse/fermi/fermilpsc.html',
'[7] User-supplied German V4 research whitepaper, 13 November 2026, Appendix A and methodological hypothesis inventory.'
]
for r in ref:s.append(P(r,'ref'))
s += [Spacer(1,9),P('<b>Conclusion.</b> The original paceval engine successfully executed 17 persistent analytical graph functions at scale and passed independent validation on a clearly defined synthetic spectral workload. The astrophysical 2FLE problem itself remains unresolved. Real photon likelihoods and independent counterpart tests are essential prerequisites to any new scientific source attribution.','banner')]

doc.build(s,onFirstPage=headerFooter,onLaterPages=headerFooter)
p=fitz.open(out);print('PDF generated:',out,'pages',len(p),'size MiB',round(out.stat().st_size/2**20,2));assert len(p)>=14
