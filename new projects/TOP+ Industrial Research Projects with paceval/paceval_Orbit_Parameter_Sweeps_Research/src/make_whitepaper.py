#!/usr/bin/env python3
"""Produce a fixed-layout 12-page English whitepaper from verified WP-022 exports.
This script is not needed to run the C++ numerical pilot. Requires reportlab.
"""
from pathlib import Path
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'paceval_Orbit_Parameter_Sweeps_Whitepaper_EN.pdf'
W,H=A4;L=43;R=43;TEXT=W-L-R
NAVY=HexColor('#14263d');TEAL=HexColor('#127e9e');GREY=HexColor('#5a6978');PALE=HexColor('#eaf3f6')
fonts='/usr/share/fonts/truetype/dejavu'
pdfmetrics.registerFont(TTFont('DV',fonts+'/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVB',fonts+'/DejaVuSans-Bold.ttf'))
styles={
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.0,leading=14.2,textColor=NAVY),
 'small':ParagraphStyle('small',fontName='DV',fontSize=7.5,leading=11.2,textColor=NAVY),
 'muted':ParagraphStyle('muted',fontName='DV',fontSize=8.1,leading=12.0,textColor=GREY),
 'sub':ParagraphStyle('sub',fontName='DVB',fontSize=10.7,leading=14.0,textColor=TEAL)}
c=canvas.Canvas(str(PDF),pagesize=A4);c.setTitle('Analytical Kernels for Orbit Parameter Sweeps | paceval research demonstrator')
page=0;y=0
def new(title=None):
 global page,y
 if page:
  c.setStrokeColor(HexColor('#d4e1e6'));c.line(L,34,W-R,34)
  c.setFillColor(GREY);c.setFont('DV',6.75)
  c.drawString(L,22,'paceval. | Analytical Kernels for Orbit Parameter Sweeps | Research demonstrator | 2026')
  c.drawRightString(W-R,22,str(page));c.showPage()
 page+=1;y=H-48
 if title:
  c.setFont('DVB',15.0);c.setFillColor(NAVY);c.drawString(L,y,title);y-=19
  c.setStrokeColor(TEAL);c.setLineWidth(1.4);c.line(L,y,W-R,y);y-=21
def para(t,style='body',gap=11):
 global y
 p=Paragraph(t,styles[style]);_,ht=p.wrap(TEXT,1500)
 if y-ht<53:raise RuntimeError(f'Overflow page {page} at {t[:48]} y={y:.0f} height={ht:.0f}')
 p.drawOn(c,L,y-ht);y-=ht+gap
def pic(name,maxh=335,caption=None):
 global y
 im=ImageReader(str(ROOT/'figures'/name));w,h=im.getSize()
 factor=min(TEXT/w,maxh/h);ow,oh=w*factor,h*factor
 if y-oh<70:raise RuntimeError(f'Image overflow on page {page}: {name}')
 c.drawImage(im,L+(TEXT-ow)/2,y-oh,width=ow,height=oh,mask='auto');y-=oh+8
 if caption:para(caption,'muted',gap=7)
def table(rows):
 global y
 for i,(a,b) in enumerate(rows):
  pp=Paragraph(b,styles['small']);_,height=pp.wrap(TEXT*.68-16,150)
  h=max(31,height+14)
  if y-h<55:raise RuntimeError(f'Table overflow {page}')
  c.setFillColor(PALE if i%2==0 else HexColor('#f8fafb'));c.rect(L,y-h,TEXT,h,fill=1,stroke=0)
  c.setFillColor(NAVY);c.setFont('DVB',7.8);c.drawString(L+8,y-17,a)
  pp.drawOn(c,L+TEXT*.32+5,y-8-height);y-=h+3
 y-=12
with open(ROOT/'examples'/'audit_summary.txt') as f:metrics=dict(line.strip().split(': ',1) for line in f if ': ' in line)
with open(ROOT/'examples'/'scenario_summary.csv',newline='') as f:SC={r['scenario']:r for r in csv.DictReader(f)}
# 1 cover
new();c.setFont('DVB',22);c.setFillColor(NAVY)
c.drawString(L,y,'Analytical Kernels for Orbit');y-=30;c.drawString(L,y,'Parameter Sweeps');y-=30
c.setFont('DV',11);c.setFillColor(TEAL);c.drawString(L,y,'An executable paceval orbital-dynamics research demonstrator');y-=22
pic('00_orbit_hero.png',maxh=298,caption='Cover artwork: a conceptual rendering of satellites and gravity fields. All numbered scientific figures use actual exported numerical data.')
para('<b>Research outcome.</b> Three persistent paceval mathematical graphs evaluate Earth-centered acceleration components in a fixed-step C++ orbit propagator. Ten orbit scenarios and 49 additional parameter combinations were completed and independently checked against separately implemented native acceleration and integration.',gap=10)
para('<b>Numerical evidence.</b> '+metrics['Scalar acceleration component audits']+' scalar and '+metrics['Batch component audits']+' packed paceval components were audited. The largest component discrepancy was '+metrics['Largest absolute component discrepancy (km/s^2)']+' km/s². The included fixed-step two-body analytic position check was '+metrics['Circular two-body analytic position oracle max difference (km)']+' km at most.','muted')
para('<b>Scope.</b> This is a deterministic synthetic orbital calculation, not a validated operational orbit-prediction service, navigation product, satellite ephemeris or flight-dynamics certification.','muted')
# 2
new('1. Research question and execution architecture')
para('Can one set of version-pinned mathematical acceleration expressions be reused for multiple orbit states, force-model parameters and independently checked propagations, without delegating the numerical time integrator to paceval?')
pic('01_execution_architecture.png',257,'Figure 1. Trust and computation boundary for the executable C++/paceval pilot.')
para('The host sets units, initial states and orbital parameters, executes a classical fixed-step fourth-order Runge–Kutta (RK4) integrator, checks physical domains and compares an independently coded native right-hand side. The paceval engine creates exactly three persistent expression graphs for the x, y and z acceleration components, reused for each RK4 stage and scenario.')
para('A separate packed-data test invokes the original paceval double-precision extended evaluation API with 32 different state vectors for each component. SDK error flags are checked per sample. No hidden external propagator is used.','muted')
# 3
new('2. Mathematical force model: gravity and J2')
para('<b>State:</b> r = (x,y,z) in km and v = (vx,vy,vz) in km/s in a fixed-axis Earth-centered inertial frame. The host computes dr/dt = v and the paceval graphs compute dv/dt = a.')
para('<b>Point-mass acceleration:</b> a<sub>0</sub> = -μr/|r|³, where μ = 398600.4418 km³/s² (declared model parameter).')
para('<b>J2 perturbation:</b> with q = z²/|r|² and g = 3μJ2 Re² / (2|r|⁵),')
para('a<sub>J2,x</sub> = gx(5q-1), &nbsp; a<sub>J2,y</sub> = gy(5q-1), &nbsp; a<sub>J2,z</sub> = gz(5q-3).')
para('Re = 6378.137 km and J2 = 1.08262668 × 10⁻³. The chosen coefficients are explicit approximations to commonly used reference constants, not an epoch-specific gravity-field realization.')
para('<b>Conservative specific potential:</b> U(r) = -μ/|r| + μ J2 Re² P2(z/|r|)/|r|³, with P2(u) = (3u²-1)/2. This is the potential consistent with the reported J2 acceleration. For drag-free trajectories it yields an energy-conservation diagnostic.')
para('<b>Parameterization:</b> μ and J2 are multiplied by independent scenario scales. Expressions do not need to be recompiled when input scale factors change. The model omits J3+, tesseral harmonics, polar motion and third-body gravitation.','muted')
# 4
new('3. Exponential drag and variable contracts')
para('<b>Illustrative atmosphere:</b> ρ(h) = ρ400 exp[-(h-400 km)/H], with h=|r|-Re, ρ400=4 × 10⁻¹² kg/m³, H=60 km. These are frozen research assumptions, <b>not</b> a calibrated thermospheric density forecast.')
para('<b>Rotating-atmosphere-relative velocity:</b> vrel = v - ω × r, where ω = (0,0,7.2921150 × 10⁻⁵ rad/s). Components in the inertial frame are (vx+ωy, vy-ωx, vz).')
para('<b>Aerodynamic acceleration:</b> a<sub>D</sub> = -0.5 (CdA/m) ρ |vrel| vrel. The fixed ballistic coefficient CdA/m = 0.02 m²/kg. With velocities represented in km/s the component formula contains the exact SI-to-km conversion factor 1000, yielding a numerical prefactor of 500 after the 1/2.')
para('<b>Input ABI:</b> x, y, z, vx, vy, vz, mu, re, j2, ball, rho, scale, omega, in this exact order (13 variables). The same paceval handles accept 0, 1, 10 or 100 atmosphere-density scaling, and varying J2 or μ, without rebuilding expression graphs.')
para('<b>Validity domain:</b> altitude must remain greater than 100 km above the spherical reference radius. Density scale factors up to 100 are stress-test parameters, not actual atmospheric observations. Aerodynamic drag exchanges energy with the co-rotating atmosphere; inertial-frame mechanical energy conservation is not asserted for drag scenarios.','muted')
# 5
new('4. Computed 3D orbital trajectories')
pic('02_3d_orbits.png',390,'Figure 2. Three computed Earth-centered trajectories for point-mass, J2 and illustrative amplified-drag force variants.')
para('All trajectories start at geocentric radius Re+500 km, with a circular two-body speed derived from their selected μ and an inclination of 51.6°. They are integrated for six hours at a 60-second fixed RK4 step. The 3D lines show actual exported positions, not a stylized artist prediction.')
para('The drag-amplified case is provided to visualize model sensitivity; it is not a flight prediction for an identified spacecraft.','muted')
# 6
new('5. Orbital-plane sensitivity to Earth oblateness')
pic('03_j2_node_evolution.png',350,'Figure 3. Osculating right ascension of ascending node (RAAN) for four J2 values.')
para('An inclined orbit under the axisymmetric J2 field exhibits node regression. The model records the osculating node from the angular-momentum vector at every saved step. Because no Earth orientation, frame precession or real ephemeris is applied, this is a controlled fixed-axis inertial-frame mathematical result.')
para('For the six-hour experiment, nominal J2 produces approximately '+f'{float(SC["nominal_J2"]["final_raan_deg"]):.4f}'+'° of final osculating RAAN, while the two-body reference remains approximately 0°.','muted')
# 7
new('6. Altitude dynamics across force variants')
pic('04_altitude_history.png',345,'Figure 4. Geocentric altitude histories for the stated 500-km initial circular orbit.')
para('The curves illustrate how a J2-distorted osculating trajectory differs from the circular point-mass solution. Geocentric radius oscillations under J2 are not evidence of atmospheric orbital decay. True dissipative effects must be separated from conservative periodic effects when interpreting altitude.')
para('The atmosphere in these cases is co-rotating and exponentially stratified. No measured density series or atmospheric-drag model such as NRLMSISE is claimed.','muted')
# 8
new('7. Reusable graph parameter sweep')
pic('05_parameter_surface.png',355,'Figure 5. Every plotted mesh vertex is a separate paceval-propagated scenario, 7 × 7 combinations after one hour.')
para('The parameter surface varies J2 scale in [0, 1.5] and an illustrative density multiplier in [0, 100]. The initial state, integration algorithm, step size, units, expression graph definitions and numerical checks are unchanged. The 49 cases provide a controlled basis for evaluating reusable analytical force kernels.')
# 9
new('8. Independent 2D map and scenario summary')
pic('06_parameter_raan_map.png',310,'Figure 6. Osculating node-angle variation across the fixed parameter grid.')
pic('09_scenario_node_comparison.png',210,'Figure 7. Comparison of the ten six-hour orbit model cases (quantities are angles, not performance metrics).')
# 10
new('9. Conservation and numerical integrity')
pic('07_energy_audit.png',285,'Figure 8. Consistent specific potential plus kinetic energy is nearly conserved in no-drag cases and not required to be constant under drag.')
pic('08_position_difference.png',270,'Figure 9. Difference between paceval-based RK4 and independent native C++ RK4, computed from every recorded state.')
# 11
new('10. Verification results and reproducibility')
table([('Graph lifecycle','Three paceval expression handles created once per process; deleted before library cleanup.'),
('Scalar checks',metrics['Scalar acceleration component audits']+' component evaluations, all passing the independent arithmetic criterion.'),
('Batch checks',metrics['Batch component audits']+' results across three graphs and 32 packed state vectors per graph.'),
('Component discrepancy',metrics['Largest absolute component discrepancy (km/s^2)']+' km/s² observed maximum.'),
('Independent propagator','10 six-hour cases + 49 one-hour grid cases compared stage-by-stage with a separate native implementation.'),
('Two-body oracle',metrics['Circular two-body analytic position oracle max difference (km)']+' km max in the additional 4-hour circular two-body analytic check.'),
('Regression automation','CMake Release build with official paceval_main.h/.cpp; CTest integration test passed.')])
para('<b>Strict limitations of the evidence:</b> matching two codes and one analytical check on selected scenarios does not establish global accuracy, rigorous interval bounds, uncertainty quantification, or suitability for operational navigation. Finite-step RK4 accuracy and the simplifying force model remain independent issues.','muted')
para('<b>Reproducibility:</b> all source code, exact constants, deterministic initial states, raw CSVs, SDK execution log, CTest result and figure rebuilding scripts are included in the accompanying repository. An architecture-compatible external paceval shared library is required at build/run time.')
# 12
new('11. Industrial relevance and external references')
para('<b>Industrial workflow.</b> Satellite-operations software, mission-design firms and constellation-simulation services routinely explore many hypothetical spacecraft configurations: inclination, gravitational harmonics, atmospheric-density assumptions, mass-to-area ratios and timing. A reusable expression engine may provide an auditable mathematical layer for the repeated force-law evaluations inside an existing solver.')
para('<b>Reasonable next research step.</b> Replace illustrative density with a traceable published atmosphere model; add solar/lunar gravity, solar radiation pressure and Earth-orientation transformations; compare externally against independently generated reference ephemerides; test integrator convergence and event handling. The value of the mathematical engine should be assessed without claiming it is a certified flight-dynamics system.')
para('<b>What paceval demonstrated:</b> nontrivial nested expressions; reusable graph handles; scalar evaluation; packed 32-state batch evaluation; parameter changes without graph rebuilding; direct numerical coupling to a host RK4 propagator; independent component, trajectory and conservation audits.')
para('<b>References</b>','sub')
for item in [
 'NASA GSFC, Earth Fact Sheet (gravity, radius, Earth J2): https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html',
 'ESA, Earth Observation Mission CFI Conventions, orbit-propagation model discussion: https://eop-cfi.esa.int/Repo/PUBLIC/DOCUMENTATION/SYSTEM_SUPPORT_DOCS/Mission%20Convention%20Documents/MCD_conventions_v4_27.pdf',
 'ESA Space Debris Conference, orbit propagation and atmospheric drag assumptions: https://conference.sdo.esoc.esa.int/proceedings/sdc7/paper/399/SDC7-paper399.pdf',
 'JPL NAIF, SPICE toolkit (ephemeris and frame comparison context): https://naif.jpl.nasa.gov/naif/toolkit.html',
 'paceval C/C++ API: https://paceval.com/api/'
]:para(item.replace('&','&amp;'),'small',gap=8)
para('Conclusion: The supplied synthetic experiment supports the technical feasibility of repeatedly evaluating orbital acceleration kernels with paceval inside a native numerical orbit propagator. This is not a validation against real spacecraft observations.','muted')
new()
c.save()
print('PDF created:',PDF,'pages:',page-1)
