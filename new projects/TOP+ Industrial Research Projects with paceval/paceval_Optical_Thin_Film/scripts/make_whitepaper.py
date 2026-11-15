#!/usr/bin/env python3
"""English scientific publication generated from actual numerical evidence and figures."""
from pathlib import Path
import json,math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor,white
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from xml.sax.saxutils import escape
P=Path(__file__).resolve().parents[1];proof=json.loads((P/'results/execution_evidence.json').read_text());hp=json.loads((P/'results/high_precision_audit.json').read_text());inv=json.loads((P/'results/inverse_reference_audit.json').read_text());W,H=A4
file=P/'paceval_Optical_Thin_Film_Whitepaper_EN.pdf';c=canvas.Canvas(str(file),pagesize=A4,pageCompression=1);c.setTitle('Optical Thin-Film Inspection and Inverse Thickness Kernels with paceval');c.setAuthor('paceval. Industrial Research Demonstrator');c.setSubject('Executed and independently checked mathematical optics research with original paceval SDK')
ink=HexColor('#20364d');accent=HexColor('#216b87');dim=HexColor('#56687b');soft=HexColor('#e9f1f5');margin=52;page=0
styles={
 'body':ParagraphStyle('body',fontName='Helvetica',fontSize=9.45,leading=14.5,textColor=ink,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Helvetica',fontSize=8.1,leading=12.3,textColor=dim),
 'caption':ParagraphStyle('caption',fontName='Helvetica-Oblique',fontSize=8.4,leading=12.3,textColor=dim),
 'reference':ParagraphStyle('reference',fontName='Helvetica',fontSize=8.1,leading=12.4,textColor=ink,wordWrap='CJK'),
}
def begin(kicker,title,subtitle=''):
 global page
 page+=1;c.setFillColor(HexColor('#f5f8fa'));c.rect(0,H-69,W,69,stroke=0,fill=1)
 c.setFillColor(accent);c.setFont('Helvetica-Bold',10);c.drawString(margin,H-28,kicker.upper())
 c.setFillColor(ink);c.setFont('Helvetica-Bold',15);c.drawString(margin,H-50,title)
 c.setStrokeColor(HexColor('#dbe5eb'));c.line(margin,51,W-margin,51)
 c.setFillColor(dim);c.setFont('Helvetica',8);c.drawString(margin,36,'paceval.  |  WP 31  |  Synthetic scientific demonstrator  |  15 Nov 2026');c.drawRightString(W-margin,36,f'{page:02d}')
 if subtitle:c.setFillColor(dim);c.setFont('Helvetica',9);c.drawString(margin,H-90,subtitle)
 return H-(112 if subtitle else 94)
def para(text,y,kind='body',space=9):
 p=Paragraph(text,styles[kind]);w,h=p.wrap(W-2*margin,700);p.drawOn(c,margin,y-h);return y-h-space
def sub(text,y):
 c.setFillColor(accent);c.setFont('Helvetica-Bold',11);c.drawString(margin,y-12,text);return y-26
def fig(id,y,maxHeight=290,caption='',width=None):
 f=P/'figures'/f'{id}.png';img=ImageReader(str(f));w,h=img.getSize();maxWidth=width or (W-2*margin);ratio=min(maxWidth/w,maxHeight/h);dw=w*ratio;dh=h*ratio
 c.drawImage(img,margin+(W-2*margin-dw)/2,y-dh,width=dw,height=dh,mask='auto');y-=dh+7
 if caption:y=para(escape(caption),y,'caption',11)
 return y

def tbl(headers,rows,y,colWidths=None):
 width=W-2*margin
 tt=Table([headers]+rows,colWidths=colWidths or [width/len(headers)]*len(headers),hAlign='LEFT',repeatRows=1)
 tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),accent),('TEXTCOLOR',(0,0),(-1,0),white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('LEADING',(0,0),(-1,-1),11),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#f7f9fb'),white]),('GRID',(0,0),(-1,-1),.35,HexColor('#d4dfe7')),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
 w,h=tt.wrap(width,700);tt.drawOn(c,margin,y-h);return y-h-15

def end():c.showPage()
# COVER
page+=1;cover=P/'figures'/'00_optical_thin_film_cover.png';c.drawImage(ImageReader(str(cover)),0,H-313,width=W,height=313);c.setFillColor(ink);c.setFont('Helvetica-Bold',22);c.drawString(53,H-365,'Optical Thin-Film Inspection')
c.drawString(53,H-396,'and Inverse Thickness Kernels');c.setFillColor(accent);c.setFont('Helvetica-Bold',12);c.drawString(53,H-438,'A functional research demonstrator with original paceval mathematical graphs')
c.setFillColor(dim);c.setFont('Helvetica',10);c.drawString(53,H-480,'Industry domain: precision metrology and semiconductor quality inspection')
c.drawString(53,H-505,'Model scope: absorption transmission and lossless single-layer reflectance')
c.drawString(53,H-530,'Verification: original SDK execution, mpmath and independent inverse fitting')
c.drawString(53,H-555,'Research date: 15 November 2026')
c.setFillColor(HexColor('#eaf2f5'));c.roundRect(53,93,W-106,125,10,fill=1,stroke=0)
y=196;y=para('<b>Important:</b> This publication describes reproducible mathematical research on synthetic film spectra. It does not claim traceable thickness measurements, real wafer qualification, commercial product accuracy or safety approval.',y)
c.setFillColor(dim);c.setFont('Helvetica',8);c.drawString(53,54,'Concept art: purpose-created illustration. Scientific figures: computed from original paceval results.');end()
# 2
Y=begin('Research overview','The industrial use case','From wafer inspection spectra to a thickness decision');Y=para('A deposited dielectric coating must remain within a manufacturing thickness specification over many sites. Optical inspection obtains wavelength-dependent measurements and estimates thickness by fitting the response of a physical model. Deviations may indicate spatial non-uniformity, deposition changes or potential downstream quality risk. In production, such decisions also require a calibrated measurement instrument and validated material model.',Y)
Y=sub('A hypothetical, clearly scoped application',Y);Y=para('Consider a 12-by-12 synthetic inspection grid. At each location the demonstrator receives nine wavelengths and known, fixed optical coefficients, computes a transmission channel and a reflective interference channel, and independently reconstructs a latent thickness. It compares the fitted result with an illustrative 235 ± 35 nm requirement. This is an explanatory synthetic workflow, not a real semiconductor manufacturer dataset.',Y)
Y=sub('Which part is executed by paceval?',Y);Y=para('The original mathematical engine parses and retains formula execution graphs, calculates attenuation and reflectance, derivatives and normalized residuals, converts accepted numeric CSV literals, and produces numeric fit-quality margins. The C++ host groups observations by site, explores global candidate thicknesses, refines the selected minimum, reduces spectral terms and writes output. Neither a built-in solver nor an automatic symbolic differentiator is claimed.',Y)
Y=sub('Research question',Y);Y=para('Can reusable paceval graphs represent a meaningful optical forward/inverse computation chain and expose transparent, independently checked results at every stage, including the limiting case of non-unique single-wavelength inversion?',Y)
Y=fig('fig01_synthetic_optical_spectra',Y,215,'Figure 1. Synthetic observations for two distinct optical measurement channels, computed by paceval.');end()
#3
Y=begin('Research and industry','Current state of the art');Y=para('NIST documents the Filmetrics F40-UV reflectometer for thickness and optical-constant characterization across common device films, including oxides, nitrides and polymers. Its spectroscopic ellipsometer provides a separate, more comprehensive polarization-sensitive measurement capability across many wavelengths and angles. The devices and their modeling software address calibrated metrology tasks beyond this research exercise.',Y)
Y=para('Classical transfer-matrix optics is well established for interference and multiple reflections, including optically absorbing, dispersive and multilayer stacks. The open-source Byrnes tmm implementation offers a practical reference for future work. The current project deliberately restricts the optical stack to one nonabsorbing dielectric film and a nonabsorbing substrate, and uses a compact real-valued expression.',Y)
Y=para('Recent metrology literature gives further reasons to state limits carefully. A 2025 Metrologia investigation discusses optical metrology uncertainty evaluation. Rastgou and colleagues (published February 2026) compare reflectometry and ellipsometry for uniform samples; Wilbrandt and Stenzel (May 2026) discuss incidence-angle choices and parameter ambiguity for absorbing thin films. These results motivate future measured calibration, not claims that this synthetic experiment reproduces their results.',Y)
Y=sub('Current competitive and complementary capabilities',Y)
Y=tbl(['Technique','What it contributes','Outside this demonstrator'],[['Spectral reflectometry','Intensity-dependent interference spectra','Real instrument calibration and complex refractive indices'],['Spectroscopic ellipsometry','Polarization phase and amplitude at varied angles','Full optical polarimetry and flexible multilayer models'],['Transfer-matrix software','Layered coherent/incoherent optics','Arbitrary multilayer inversion'],['paceval demonstration','Reusable scalar expressions, guards and batch execution','Instrument driver or full optimizer']],Y,[125,180,186])
Y=para('The proposed place for paceval is therefore a reusable formula layer inside a broader measurement system. The present study is a controlled numerical feasibility exercise, not a replacement claim.',Y);end()
#4
Y=begin('Physics','V1: absorption transmission and direct inversion');Y=para('The deliberately simplified Beer-Lambert channel models normalized intensity through a film of thickness d. The coefficient alpha is scaled with wavelength. An additive offset represents a synthetic sensor baseline. All units are declared: d and lambda in nm, alpha in inverse nm, optical intensities dimensionless.',Y)
Y=tbl(['Formula','Meaning'],[['alpha_eff = alpha0 * (550 / lambda)','Wavelength-scaled attenuation coefficient'],['I = I0 * exp(-alpha_eff * d) + offset','Synthetic transmission signal'],['d = -ln((I-offset)/I0) / alpha_eff','Analytical inverse thickness, valid on domain'],['dd/dI = -1 / (alpha_eff * (I-offset))','Analytic inverse sensitivity'],['m = tolerance - abs(d - target)','Signed screening margin']],Y,[235,256])
Y=para('The paceval execution builds separate persistent graph handles for attenuation, forward intensity, synthetic sensor output, analytical inversion, derivatives, residual, local uncertainty, tolerance and a composite logical guard. The C++ host rejects non-finite values, invalid decimal literals and nonpositive inverse arguments before evaluation.',Y)
Y=sub('Why this is not a complete wafer reflectance model',Y)
Y=para('The Beer-Lambert relation does not describe coherent reflections at multiple film interfaces. It can be useful as a transparent baseline where an absorption-based transmission approximation is physically justified, but must not be used as a general inversion model for reflective multilayer semiconductor stacks.',Y)
Y=fig('fig08_local_uncertainty',Y,210,'Figure 2. Model-local uncertainty indicators under declared synthetic sensor uncertainty parameters.');end()
#5
Y=begin('Physics','V2: coherent single-layer interference');Y=para('For real positive optical indices n0, nf, ns at normal incidence, the air/film and film/substrate Fresnel amplitude coefficients are r01 = (n0 - nf)/(n0 + nf) and r12 = (nf - ns)/(nf + ns). The roundtrip phase is phi = 4*pi*nf*d/lambda.',Y)
Y=tbl(['Graph expression','Interpretation'],[['R = (r01²+r12²+2*r01*r12*cos(phi)) / (1+(r01*r12)²+2*r01*r12*cos(phi))','Coherent reflectance from one lossless dielectric film'],['dR/dd = (4*pi*nf/lambda) * B*sin(phi)*(A-C) / (C+B*cos(phi))²','Analytic derivative with A=r01²+r12², B=2*r01*r12, C=1+(r01*r12)²'],['Fisher_j = (dR/dd / sigmaR)²','Wavelength-local thickness information'],['residual_j = ((R(d,lambda_j)-observed_j)/sigmaR)²','Actual paceval spectral objective term']],Y,[244,247])
Y=para('The denominator represents coherent internal reflections in a compact real expression. The experimental model assumes a single planar homogeneous transparent layer, constant refractive indices across the nine wavelengths and a semi-infinite lossless substrate. Absorption, dispersion, interface roughness and backside reflections are not included.',Y)
Y=fig('fig06_reflectance_sensitivity_map',Y,255,'Figure 3. Executed paceval reflectance derivatives over all observed synthetic sites and nine wavelengths.');end()
#6
Y=begin('Inverse methods','Global search, local uncertainty and aliasing');Y=para('The C++ host uses a 3 nm thickness grid between 88 and 460 nm to identify a candidate objective basin, then refines the best candidate by bounded golden-section iterations. For every candidate wavelength, the normalized squared residual is evaluated by an original paceval execution graph. The host only sums the nine independent terms and manages the search state.',Y)
Y=para('An essential ambiguity follows from the periodic interference phase: at one fixed wavelength, R(d,lambda) equals R(d + lambda/(2*nf),lambda). This is not a floating-point artifact. It is an exact identity of the declared ideal optical model. An actual counterexample is recorded by the original paceval library in alias_case.csv and alias_curve.csv.',Y)
Y=para('Under the assumed diagonal constant sensor-noise weights, local Fisher information adds across wavelengths. A paceval summary graph transforms the aggregate into an inverse-square-root local uncertainty proxy. This is not a calibrated uncertainty budget, not a confidence interval for uncertain refractive indices, and not proof that every multi-wavelength inverse is unique.',Y)
Y=fig('fig05_one_wavelength_alias',Y,255,'Figure 4. Executed one-band reflectance curve with two exactly aliased thicknesses.');end()
#7
Y=begin('Software architecture','Actual original-SDK graph execution');Y=para('All graph construction, evaluation, conversion, handle lifetime and error paths use the provided original paceval 4.25 SDK. A tested probe determines real multi-graph batch output ordering. The program also invokes the single-graph batch interface for inverse residual landscapes, alongside scalar evaluations for controls and counterexamples.',Y)
Y=tbl(['Execution layer','Specific responsibility','Observed evidence'],[['paceval BEER','Transmission, inverse thickness, sensitivity, normalized residual and tolerance','BEER graph group, spectral CSV'],['paceval FILM','Fresnel coefficients, phase, reflectance, derivative, spectral loss and guards','FILM graph group, objective CSV'],['paceval SUMMARY','Information-to-uncertainty, objective and thickness margins','SUMMARY graphs, site summary'],['paceval COMPARE','Cross-channel thickness delta and combined guards','COMPARE group, comparison CSV'],['C++ host','Global grid, local refinement, nine-term reduction, CSV grouping','optical_film_main.cpp'],['Independent audit','Separate mpmath and SciPy physical references','Two independent JSON audits']],Y,[110,225,156])
Y=para(f'The main executed run generated <b>{proof["unique_graphs_executed"]} distinct domain-specific graphs</b>, evaluated <b>{proof["site_count"]} sites</b> at <b>{proof["wavelengths_per_site"]} wavelengths</b>, and recorded <b>{proof["graph_point_evaluations"]:,} graph-point evaluations</b>. These are different counting categories and have not been conflated into a speed or performance claim.',Y)
Y=para('The detailed graph inventory and the source-level execution trace are included in the final archive. The external Linux runtime remains outside the distributed ZIP.',Y);end()
#8
Y=begin('Scientific figures','Wafer thickness: truth and optical reconstruction');Y=fig('fig02_truth_thickness_map',Y,285,'Figure 5. Deterministically generated true thickness field, included in the input data as synthetic truth.');Y=fig('fig03_reconstructed_thickness_map',Y,285,'Figure 6. Independently fitted thickness map, obtained from paceval spectral residuals.');end()
#9
Y=begin('Scientific figures','Inverse objective and phase sensitivity');Y=fig('fig04_spectral_objective_profiles',Y,290,'Figure 7. Executed multi-wavelength inverse objective profiles for three representative synthetic sites.');Y=fig('fig06_reflectance_sensitivity_map',Y,285,'Figure 8. Real paceval derivative map across sites and wavelength channels.');end()
#10
Y=begin('Scientific figures','Recovered thickness and uncertainty');Y=fig('fig07_thickness_recovery_errors',Y,285,'Figure 9. Thickness reconstruction residuals for two distinct assumed measurement channels.');Y=fig('fig08_local_uncertainty',Y,280,'Figure 10. Local uncertainty proxies, conditioned on the specified synthetic noise parameters.');end()
#11
Y=begin('Scientific figures','3D thickness and screening classifications');Y=fig('fig09_3d_wafer_thickness',Y,295,'Figure 11. Three-dimensional representation of the reconstructed synthetic wafer thickness.');Y=fig('fig10_illustrative_quality_window',Y,278,'Figure 12. Output classification from the illustrative thickness tolerance, not an approved production limit.');end()
#12
Y=begin('Results','What the executed synthetic experiment shows');Y=para('The two channels were applied to the same synthetic thickness field with separately introduced intensity and reflectance perturbations. Both required known optical material constants. The absorption inverse operates wavelength by wavelength, whereas the coherent reflectance inverse accumulates spectral residuals and uses a host-level numerical search.',Y)
Y=tbl(['Reproducible result','Actual executed value'],[['Unique executed persistent paceval graphs',str(proof['unique_graphs_executed'])],['Synthetic wafer sites',str(proof['site_count'])],['Spectral observations (9 per site)',str(proof['spectral_sample_rows'])],['Beer transmission channel: within illustrative tolerance',f'{proof["beer_tolerance_pass"]} / {proof["site_count"]}'],['Coherent film channel: within illustrative tolerance',f'{proof["film_tolerance_pass"]} / {proof["site_count"]}'],['Both optical reconstructions within 3 nm of synthetic truth',f'{proof["joint_recovery_within_3nm"]} / {proof["site_count"]}'],['Mean absolute reconstruction difference from synthetic truth: Beer',f'{proof["mean_absolute_thickness_recovery_error_beer_nm"]:.3f} nm'],['Mean absolute reconstruction difference from synthetic truth: FILM',f'{proof["mean_absolute_thickness_recovery_error_film_nm"]:.3f} nm']],Y,[317,174])
Y=para('These are *in-model numerical recovery outcomes*, not real instrument calibration metrics. The reference thickness is known and the index/absorption coefficients are supplied correctly to the fit, which removes important real-life sources of uncertainty. A single-wavelength case remains mathematically ambiguous even with exact arithmetic.',Y)
Y=sub('Interpretation for a possible industrial pilot',Y);Y=para('A realistic extension should fit dispersion and film thickness jointly, include measured instrument spectral response, use calibration samples to resolve model ambiguity, and propagate thickness uncertainty before any production-level tolerance classification.',Y);end()
#13
Y=begin('Verification','Independent accuracy and reproducibility controls');Y=para('The independently written 90-decimal mpmath reference evaluates the original source-input values as exact binary doubles and recomputes Beer intensities, inverse thickness, sensitivities, single-layer Fresnel reflectance, analytical derivatives, information and final nine-band composite objective/uncertainty. It does not interpret the paceval expression strings as its mathematical source.',Y)
Y=para('An independent SciPy implementation repeats the global and local inverse search with separately written optical physics. The checks include the exact single-wavelength alias, thickness recovery from known synthetic truth, and test cases with changing optical coefficients and wavelength. A native C++ physical reference is used inside the executable to check selected complete forward results and derivatives.',Y)
Y=tbl(['Evidence stage','Recorded result'],[['High precision mpmath checks',f'{hp["checks"]:,} passed, 90 decimal digits'],['Independent SciPy inverse and alias checks',f'{inv["independent_inversion_checks"]} passed'],['Native C++ reference assertions',f'{proof["native_reference_assertions"]:,} passed'],['Original SDK scalar, single-graph and multi-graph paths','Actual compiled-and-executed test paths'],['Markdown math and local links','Archive-wide checker and negative regression suite'],['Datasets','Deterministic generator; repeat-run comparison documented in release logs']],Y,[242,249])
Y=para('Technical numerical tolerance data remain in internal machine-readable JSON files. This report intentionally avoids presenting accuracy or speed comparisons against native C++ as a product advantage.',Y);end()
#14
Y=begin('Limitations','Where this mathematical model must stop');Y=para('<b>Material properties.</b> Real semiconductor substrates, especially silicon, often have wavelength-dependent complex refractive indices. This demonstration uses a lossless dielectric surrogate instead; a compelling reconstruction on it cannot validate a silicon-wafer metrology application.',Y)
Y=para('<b>Optical physics.</b> Real instruments use nonzero angular apertures, polarization, multiple layers, finite coherence, nonideal surfaces, calibration standards and possible backside effects. The Beer-Lambert approximation and the single-layer coherent reflectance formula address different restricted optical channels.',Y)
Y=para('<b>Inverse identifiability.</b> A single wavelength admits exact thickness aliases. Nine-band inversion worked on the present constrained synthetic collection; a global grid is not a proof of uniqueness or a universal guarantee of global minimum. Joint uncertainty in thickness and optical constants remains unmodeled.',Y)
Y=para('<b>Measurement uncertainty.</b> The local information-based value depends on synthetic assumed independent noise and known optical coefficients. A full traceable uncertainty budget, model discrepancy and physical calibration are absent.',Y)
Y=para('<b>Operational applicability.</b> There is no wafer data acquisition, machine interface, deployment qualification, process-control acceptance or regulatory metrology certification. TINC is not claimed to bound the entire parameter domain: finite point checks do not constitute such a proof.',Y)
Y=sub('Practical next experiments',Y);Y=para('First add a complex-valued multilayer transfer-matrix reference with measured dispersive n and k, then test independently measured standards. Next evaluate joint estimation of thickness and material constants, vary incidence angle and polarization, quantify uncertainty correlations and assess quality windows jointly with an industrial metrology owner.',Y);end()
#15
Y=begin('References','Sources and final scientific conclusion');sources=[
 ('1. NIST Filmetrics F40-UV reflectometer','https://www.nist.gov/laboratories/tools-instruments/nanofab-tool-filmetrics-f40-uv-reflectometer'),
 ('2. NIST Woollam M-2000 DI spectroscopic ellipsometer (updated 2025)','https://www.nist.gov/laboratories/tools-instruments/nanofab-tool-j-woollam-m-2000-di-spectroscopic-ellipsometer'),
 ('3. J. A. Woollam, Ellipsometry FAQ','https://www.jawoollam.com/resources/ellipsometry-faq'),
 ('4. S. J. Byrnes, transfer-matrix optics software and notes','https://github.com/sbyrnes321/tmm'),
 ('5. Rastgou et al., Metrologia 2026, reflectometry vs ellipsometry','https://doi.org/10.1088/1681-7575/ae3964'),
 ('6. Wilbrandt and Stenzel, Solids 2026, angle selection and ambiguity','https://doi.org/10.3390/solids7030027')]
for name,link in sources:
 Y=para('<b>'+escape(name)+'</b><br/>'+escape(link),Y,'reference',13)
Y=sub('Conclusions',Y);Y=para('This research establishes an actual, reproducible **mathematical functionality demonstration**: the original paceval SDK executed reusable optics graphs across forward models, inverse residual landscapes, analytically derived sensitivities, and engineering screening margins. Independent native C++, 90-digit mpmath and SciPy references were used to validate the numerical results.',Y)
Y=para('The observed recovery results are scientifically interpretable under the explicit ideal-model assumptions, but they do not validate instrument accuracy or real-wafer metrology. The deliberately demonstrated wavelength alias is central evidence that reliable inverse thickness estimation requires both appropriate physics and explicit identifiability analysis.',Y)
Y=para('<b>Released files.</b> Complete C++ integration, formula manifest, graph execution inventory, deterministic inputs, scientific result CSVs, independent audit scripts and ten source-derived figures (PNG and vector PDF) are bundled with this English PDF and the GitHub README.',Y);end()
c.save();print('WHITEPAPER',file,'pages',page,'bytes',file.stat().st_size)
