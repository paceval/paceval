#!/usr/bin/env python3
"""Recreate the English whitepaper from independently audited, executed paceval results.
The image on the cover is a concept illustration, never presented as calculated data.
"""
from pathlib import Path
import json, csv, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import (SimpleDocTemplate,Paragraph,Image,Spacer,PageBreak,Table,TableStyle,KeepTogether)
from reportlab.lib.colors import HexColor,white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
ROOT=Path(__file__).resolve().parent.parent
OUTPUT=ROOT/'paceval_Space_Transfer_Screening_Whitepaper_EN.pdf'
D=ROOT/'results'
props={}
for line in (D/'execution_summary.txt').read_text().splitlines():
 if '=' in line:k,v=line.split('=',1);props[k]=v
hp=json.loads((D/'high_precision_audit.json').read_text())
NAVY=HexColor('#132c46');TEAL=HexColor('#1b8391');ORANGE=HexColor('#d98b3c');INK=HexColor('#293d4d');PALE=HexColor('#eaf2f4')
base='/usr/share/fonts/truetype/dejavu/DejaVuSans'
pdfmetrics.registerFont(TTFont('Dv',base+'.ttf'))
pdfmetrics.registerFont(TTFont('DvB',base+'-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DvI',base+'-Oblique.ttf'))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='OverWP',fontName='DvB',fontSize=8.4,leading=12,textColor=TEAL,spaceAfter=9))
styles.add(ParagraphStyle(name='TitleWP',fontName='DvB',fontSize=22,leading=29,textColor=NAVY,spaceAfter=12))
styles.add(ParagraphStyle(name='DeckWP',fontName='Dv',fontSize=11,leading=17,textColor=INK,spaceAfter=12))
styles.add(ParagraphStyle(name='ChapWP',fontName='DvB',fontSize=15.5,leading=20,textColor=NAVY,spaceAfter=14,spaceBefore=5,keepWithNext=True))
styles.add(ParagraphStyle(name='SubWP',fontName='DvB',fontSize=10.4,leading=14.8,textColor=TEAL,spaceAfter=7,spaceBefore=11,keepWithNext=True))
styles.add(ParagraphStyle(name='BodyWP',fontName='Dv',fontSize=9,leading=14.3,textColor=INK,spaceAfter=9))
styles.add(ParagraphStyle(name='NoteWP',fontName='Dv',fontSize=8.1,leading=12.2,textColor=INK,spaceAfter=7))
styles.add(ParagraphStyle(name='TableWP',fontName='Dv',fontSize=7.65,leading=11.5,textColor=INK))
styles.add(ParagraphStyle(name='CaptionWP',fontName='DvI',fontSize=8.1,leading=12,textColor=INK,spaceBefore=5,spaceAfter=10))
styles.add(ParagraphStyle(name='BulletWP',fontName='Dv',fontSize=8.8,leading=13.5,leftIndent=13,firstLineIndent=-10,textColor=INK,spaceAfter=5))
S=[]
def p(x,style='BodyWP'):S.append(Paragraph(x,styles[style]))
def h(s):p(s,'ChapWP')
def sub(s):p(s,'SubWP')
def bullet(s):p('• '+s,'BulletWP')
def page():S.append(PageBreak())
def pic(stem,width=169*mm,maxh=112*mm):
 path=ROOT/stem;im=PILImage.open(path);w,h=im.size
 newh=width*h/w
 if newh>maxh:width=width*maxh/newh;newh=maxh
 S.append(Image(str(path),width=width,height=newh,hAlign='CENTER'))
def cap(s):p(s,'CaptionWP')
def table(headers,rows,widths):
 rows0=[[Paragraph('<font color="#ffffff"><b>'+str(q)+'</b></font>',styles['TableWP']) for q in headers]]
 rows0 += [[Paragraph(str(q),styles['TableWP']) for q in r] for r in rows]
 t=Table(rows0,colWidths=widths,repeatRows=1,hAlign='LEFT',spaceAfter=8*mm)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,PALE]),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),0.8,TEAL)]))
 S.append(t)
def equation(name,eqs):
 filename=ROOT/'figures'/f'_equation_{name}.png'
 n=len(eqs);fig,ax=plt.subplots(figsize=(10,.52*n+.3));ax.axis('off')
 for i,eq in enumerate(eqs):ax.text(.025,.84-i*(.8/max(1,n-1)),eq,fontsize=13.5,va='center',color='#14364f',transform=ax.transAxes)
 fig.savefig(filename,dpi=200,bbox_inches='tight',pad_inches=.1,transparent=False);plt.close(fig)
 pic('figures/'+filename.name,maxh=40*mm)

def footer(canvas,doc):
 canvas.saveState();w,height=A4
 canvas.setStrokeColor(TEAL);canvas.setLineWidth(.6);canvas.line(20*mm,16*mm,w-20*mm,16*mm)
 canvas.setFont('Dv',7);canvas.setFillColor(INK)
 canvas.drawString(20*mm,11.5*mm,'paceval  |  WP_037 Space Transfer Screening  |  November 2026')
 canvas.drawRightString(w-20*mm,11.5*mm,str(doc.page));canvas.restoreState()

# 1 — COVER
p('PACEVAL  /  SCIENTIFIC RESEARCH WHITEPAPER  /  WP_037','OverWP')
p('Analytical Costs for Space Transfer Screening','TitleWP')
p('Reusable mathematical execution graphs for impulsive transfer costs, orbital-plane sensitivity and preliminary mission trade studies','DeckWP')
pic('figures/00_space_transfer_hero.png',maxh=88*mm)
cap('Concept illustration; not an executed orbit, propagated ephemeris or computed research result.')
p(f'<b>Executed research result.</b> {int(props["reusable_graphs"])} persistent paceval computation graphs, {int(props["candidates"]):,} deterministic transfer candidates, {int(props["multi_graph_batch_results"]):,} actual multi-graph batch results and {hp["independent_values"]:,} independent 80-digit checks.')
p('<b>Scientific scope.</b> Two-body circular-to-circular Hohmann transfers, prescribed arrival velocity-plane angle, ideal rocket equation, separate coplanar bi-elliptic comparison, and two versioned screening policies. No real mission optimization, ephemeris targeting or flight qualification.')
page()
# 2
h('1. Introduction: industrial use case and current state of the art')
p('Mission design begins with trade-space exploration. A spacecraft team might examine thousands of notional radius changes, inclination requirements, propulsion systems and time budgets before committing to detailed integration and numerical targeting. Preliminary cost screening asks how much impulsive delta-v and ideal propellant a candidate would require under explicit idealized assumptions. It does not replace high-fidelity propagation.')
p('A Hohmann transfer links two circular coplanar orbits through half of an ellipse and two velocity impulses. The first changes the orbit and the second circularizes it; when the required final velocity direction differs, the arrival impulse can be treated as a vector difference under a prescribed endpoint geometry. The transferable mathematical expressions are straightforward, but realistic mission evaluation adds launch epochs, orbital nodes, perturbations and finite thrust.')
sub('Existing industrial and scientific approaches')
p('NASA GMAT R2026 supports mission design, optimization and spacecraft propagation [3]. ESA pykep 3.1 includes Lambert solvers, trajectory methods and interplanetary research workflows [4]. JPL NAIF SPICE supplies time-dependent spacecraft and planetary geometry [5], and Orekit provides impulsive and continuous maneuver modeling [6]. These are established approaches, not competitors whose entire function can be reduced to formula evaluation.')
sub('Why a paceval mathematical component?')
p('A larger mission-analysis program may want to store, change, audit and repeatedly execute numerous analytical cost expressions over different input vectors. This study tests precisely that mathematical component. paceval owns graph construction and numeric evaluation; C++ handles candidate generation, validation, policy application and data export. The results justify a small, falsifiable feasibility claim rather than an unmeasured performance or propulsion advantage.')
page()
# 3
h('2. Research question and experimental architecture')
p('The question is whether the original paceval C/C++ interface can create and reuse physically defined transfer-cost expressions, run scalar and grouped batch evaluations, retain independent policy versions, and provide mathematical outputs for a reproducible parameter study.')
pic('figures/01_orbital_transfer_geometry.png',maxh=112*mm)
cap('Figure 1. Geometrical reconstruction by the C++/Python host for circular-orbit transfer radii; this is not a paceval-produced ephemeris or an orbital propagator output.')
sub('Responsibility split')
table(['paceval mathematical engine','Independent C++ host and offline scripts'],[
 ['17 persistent mathematical graphs','Deterministic candidate generator, seed and validity constraints'],
 ['Scalar evaluation of one input vector','Independent physical-reference formulas and quality checks'],
 ['17-graph concurrent evaluation of batched candidates','Preliminary policy decisions and ranking'],
 ['Single-graph batched surfaces and graph version retention','CSV exports, scientific charts and PDF construction']],[84*mm,86*mm])
page()
# 4
h('3. Defined mathematical model: the two-impulse transfer')
p('All radii are Earth-centered distances, not orbital altitudes. The model assumes a central inverse-square gravitational potential, positive r1 &lt; r2, an initially circular orbit, an exactly impulsive maneuver at each ellipse endpoint, and a prescribed final velocity-direction change. The gravitational parameter is frozen at 398600.4418 km³/s².')
equation('h',['$a=(r_1+r_2)/2, \\quad v_{c,i}=\\sqrt{\\mu/r_i}$',r'$v_{t,i}=\sqrt{\mu\,(2/r_i-1/a)}$',r'$\Delta v_1=|v_{t,1}-v_{c,1}|,\quad \Delta v_2=|v_{c,2}-v_{t,2}|$'])
p('The original research proposal gave only the first transfer impulse. The actual screening must include the arrival circularization impulse. A prescribed arrival plane-velocity angle is incorporated into the same vector change, rather than charging a separate plane maneuver and double-counting the arrival cost.')
equation('plane',[r'$\Delta v_{2,\theta}=\sqrt{(v_{c,2}-v_{t,2})^2+4v_{c,2}v_{t,2}\sin^2(\theta/2)}$',r'$\Delta v_{\rm total}=\Delta v_1+\Delta v_{2,\theta}$'])
p('The sum-of-squares expression avoids direct subtraction of nearly equal velocity-squared terms when the two speeds and the angle are small. It remains a mathematical endpoint condition: actual nodal alignment and reachable phasing are not assessed.')
sub('Time and propellant')
equation('time',[r'$t_H=\pi\sqrt{a^3/\mu}$',r'$m_p=m_0\left[1-\exp\left(-\frac{1000\,\Delta v_{\rm total}}{I_{\rm sp}\,g_0}\right)\right]$'])
p('The transfer time is converted from seconds to days for export. Here g0 = 9.80665 m/s², specific impulse is seconds, and the factor 1000 explicitly converts delta-v in km/s to m/s. The ideal rocket equation excludes non-ideal maneuver losses, tanks, reserves and dynamic mass constraints.')
page()
# 5
h('4. Defined mathematical model: bi-elliptic alternative')
p('For r1 &lt; r2 &lt; rb, a bi-elliptic candidate first raises apoapsis to rb, changes periapsis at rb, then circularizes at r2. All three impulses use the same vis-viva formula with the relevant semi-major axes a1=(r1+rb)/2 and a2=(r2+rb)/2. Each delta-v contribution is an absolute velocity difference at its impulse radius.')
equation('bi',[r'$\Delta v_{B}=\Delta v_{B,1}+\Delta v_{B,2}+\Delta v_{B,3}$',r'$t_B=\pi\left(\sqrt{a_1^3/\mu}+\sqrt{a_2^3/\mu}\right)$'])
p('The bi-elliptic calculation is deliberately coplanar. Consequently, comparisons are made only to the coplanar Hohmann sum, never to the Hohmann value with a prescribed arrival plane change. The intermediate apoapsis is sampled, not optimized; bi-elliptic delta-v advantages must be judged together with the potentially much longer flight time.')
sub('Versioned mathematical policies')
p('Policy version 1 uses P1 = delta-v/4 + 0.10·(time in days)/0.5 + 0.35·fuel fraction. Version 2 uses P2 = delta-v/4 + 0.35·(time in days)/0.5 + 0.12·fuel fraction. Both are dimensionless, consciously illustrative weighted scores. The normalization and weights are policy assumptions rather than physical constants. Their existing computation handles are held separately and never silently mutated.')
sub('Input contract and validity')
table(['Input','Units and contract'],[['mu','km³/s², strictly positive'],['r1, r2, rb','km, r1 greater than Earth reference radius, r2 > r1, rb > r2'],['theta','radians, 0 to 60 degrees'],['Isp, initial mass','seconds and kg; both strictly positive']],[65*mm,105*mm])
page()
# 6
h('5. Deterministic research workload and execution')
p('The executable creates 8,000 deterministic outward-transfer candidates using a fixed SplitMix64 pseudo-random sequence. Their radius ratios, assumed arrival velocity-vector angles, specific impulses, starting masses and intermediate bi-elliptic apoapses cover intentionally broad synthetic ranges. Every numerical column is recorded at 17 significant digits; each result can be reproduced by rebuilding with the supplied original SDK interface.')
p('C++ first creates and retains 17 expression graphs and validates the returned layout with independent scalar calculations. The program then uses paceval_dGetMultipleComputationsResultsExt for all main candidate batches. Separately, paceval_dGetComputationResultExt evaluates 3,721-point parameter surfaces. The same graph handles are reused; no graph construction occurs within the main candidate evaluation loop.')
table(['Executed and independently checked item','Observed result'],[
 ['Persistent paceval mathematical handles',props['reusable_graphs']],
 ['Synthetic candidate inputs and screening rows',f"{int(props['candidates']):,}"],
 ['paceval multi-graph batch output values',f"{int(props['multi_graph_batch_results']):,}"],
 ['paceval single-graph surface batch results',f"{int(props['single_graph_surface_batch_results']):,}"],
 ['Native independently checked mathematical values',f"{int(props['independent_native_checked_values']):,}"],
 ['80-decimal-place reference values',f"{hp['independent_values']:,} across {hp['independent_cases']} cases"],
 ['Invalid input cases rejected by the host',props['invalid_inputs_rejected']],
 ['Actual integration test','CMake and CTest: 1/1 passed']],[105*mm,65*mm])
p('The independent C++ oracle is structurally separate from paceval graph construction. A second Python implementation uses 80-digit mpmath and derives the endpoint vector difference from the law of cosines. Technical numeric-difference details remain in the machine-readable audit rather than in the published model discussion.')
page()
# 7
h('6. Executed orbital transfer response surface')
p('This response surface is constructed from 3,721 evaluated parameter points, using the real paceval batch API, not interpolated synthetic labels. The varied inputs are target/initial radius and prescribed arrival vector angle, while Earth gravitational parameter, reference initial radius and propulsion assumptions are fixed.')
pic('figures/02_deltav_surface_3d.png',maxh=125*mm)
cap('Figure 2. Total ideal two-impulse delta-v as a function of target radius ratio and prescribed arrival velocity-direction difference; paceval-computed values.')
p('The surface is not a multi-body orbital-feasibility map. It records only the defined analytical two-body cost under a specified endpoint geometry, and thus remains suitable for early-stage mathematical screening rather than mission targeting.')
page()
# 8
h('7. Plane-change sensitivity and contour interpretation')
pic('figures/03_deltav_contours.png',maxh=94*mm)
cap('Figure 3. Contour map of the executed paceval total delta-v response surface.')
pic('figures/05_plane_change_sensitivity.png',maxh=94*mm)
cap('Figure 5. Cross-sections at five distinct prescribed plane-change angles, computed from the same recorded paceval surface.')
p('The contours help analysts identify parameter regions meriting higher-fidelity study. Actual orbital-plane changes require nodal and phasing considerations beyond this defined two-impulse calculation.')
page()
# 9
h('8. Propellant requirements and illustrative mission scenario')
pic('figures/04_propellant_surface_3d.png',maxh=105*mm)
cap('Figure 4. Ideal rocket-equation propellant mass for the 1,200 kg and 340 s example spacecraft, based on actual paceval-evaluated costs.')
p('For a separate illustrative circular transfer from 7,000 km to 42,164 km Earth-centered radius, with a 5-degree arrival vector-angle change, initial mass of 1,200 kg and Isp = 340 s, the analytical result is approximately 3.784 km/s total delta-v, 5.33 hours transfer duration and 814 kg ideal propellant.')
p('These numbers are self-contained mathematical results, not spacecraft-performance claims. They do not account for tank masses, additional burns, launch vehicle delivery, losses, changing propulsion performance or real rendezvous conditions.')
page()
# 10
h('9. Coplanar bi-elliptic alternatives: delta-v versus time')
pic('figures/06_bielliptic_trade.png',maxh=125*mm)
cap('Figure 6. Executed paceval results for two-impulse Hohmann and three-impulse bi-elliptic transfers, each fully coplanar; the dashed time curves expose the long-duration cost of a large intermediate apoapsis.')
p('For the declared rb = 20 × r2 parameter path, the bi-elliptic option begins to require less ideal delta-v in part of the large-radius-ratio domain. Its transfer duration grows sharply because of the very large apoapsis. The diagram establishes neither an optimized r_b choice nor a more appropriate operational mission.')
page()
# 11
h('10. Candidate screening under a stated host policy')
pic('figures/07_candidate_screening.png',maxh=100*mm)
cap('Figure 7. Recorded paceval cost values and host decisions for 8,000 synthetic candidates.')
p(f'Under the illustrative limits of 5 km/s total two-impulse delta-v, 650 kg ideal propellant and 1.5 days half-ellipse flight time, {int(props["passed_screen"]):,} candidates pass all three conditions. The conditions are synthetic screening parameters, not spacecraft technical requirements or an accepted mission design envelope.')
pic('figures/09_fuel_fraction_distribution.png',maxh=82*mm)
cap('Figure 9. Ideal rocket-equation fuel fraction across the same deterministic paceval-evaluated candidate set.')
page()
# 12
h('11. Reusable expressions and controlled model changes')
pic('figures/08_policy_versions.png',maxh=113*mm)
cap('Figure 8. Two unchanged, independently retrievable paceval computation handles encode different policy weights over the same underlying physical transfer formulas.')
p('In a real mission-analysis environment, screening weights may change as engineering priorities change. This experiment demonstrates storing a new expression as a separate computation graph while preserving the older handle and its numeric meaning. The C++ application controls the version identities, the input set and the policy interpretation; paceval executes the defined expressions.')
p('The two weighted-policy formulas are not claims of an optimum trajectory. Their purpose is to demonstrate transparent mathematical change management and the ability to audit which expression produced which early-stage ranking.')
page()
# 13
h('12. Scientific limitations, reproducibility and references')
p('This study proves execution of reusable mathematical expressions in the specified two-body screening kernel. It does not establish real mission feasibility, global optimality, operational safety, flight performance, ephemeris accuracy, numerical propagation fidelity or computation-speed advantage. Orbit phasing, rendezvous geometry, perturbations, finite thrust, fuel margins and mission constraints require an appropriate downstream solver and independently verified spacecraft inputs.')
sub('Reproduce the exact workload')
p('With a licensed compatible Linux paceval shared library, build using CMake -S src -B build -DPACEVAL_RUNTIME=/absolute/path/to/runtime.so, run CTest, then execute ./build/space_transfer --out . --cases 8000. Execute the Python scripts high_precision_reference.py, make_figures.py, make_whitepaper.py and verify_results.py. The root README supplies the complete commands, dependencies and file links. The project does not redistribute the external runtime library.')
sub('Referenced methods and current industrial ecosystem')
p('[1] JPL, Fundamentals of Orbital Mechanics, Chapter 7: spsweb.fltops.jpl.nasa.gov/portaldataops/mpg/MPG_Docs/MPG Book/Release/Chapter7-OrbitalMechanics.pdf','NoteWP')
p('[2] Ansys STK, Hohmann Transfer Technical Notes: help.agi.com/stk/12.7.1/Content/training/tq-hohmann.htm','NoteWP')
p('[3] NASA GMAT Version R2026, NASA Software Catalog: software.nasa.gov/software/GSC-19640-1','NoteWP')
p('[4] ESA Advanced Concepts Team, pykep 3.1 documentation: esa.github.io/pykep/','NoteWP')
p('[5] JPL NAIF SPICE: naif.jpl.nasa.gov/','NoteWP')
p('[6] Orekit 13, Maneuver Architecture: test.orekit.org/site-orekit-13.0/architecture/maneuvers.html','NoteWP')
p('[7] paceval mathematical engine API: paceval.com/api/','NoteWP')
sub('Research conclusion')
p('The actual SDK experiment successfully demonstrates persistent paceval execution graphs for the two-impulse circular transfer model, independent batch verification, coplanar bi-elliptic comparison and controlled cost-policy revisions. The actionable follow-up is an identical-candidate test against mission dynamics tools using realistic geometry and mission constraints, not an unsupported production-readiness claim.')

D0=SimpleDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=20*mm,rightMargin=20*mm,topMargin=17*mm,bottomMargin=19*mm,title='WP_037 Analytical Costs for Space Transfer Screening',author='paceval scientific research')
D0.build(S,onFirstPage=footer,onLaterPages=footer)
print('CREATED',OUTPUT)
