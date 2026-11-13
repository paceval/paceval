#!/usr/bin/env python3
"""A reusable research plan / data-coverage matrix. NOT an inference engine."""
from pathlib import Path
import csv
R=Path(__file__).resolve().parents[1]
N=[
('N01','FSRQ / blazar','radio WISE optical variability and GeV'),('N02','BL Lac / unknown blazar','radio X-ray IR GeV'),('N03','Other AGN or quasar','optical spectra redshift SED'),('N04','Radio galaxy jets lobes','resolved radio jets GeV'),('N05','Star-forming galaxy','radio infrared star-formation'),('N06','Young pulsar','barycentric timing gamma and radio'),('N07','Millisecond pulsar','radio gamma timing'),('N08','Pulsar-wind nebula','X-ray radio spatial extension'),('N09','Supernova remnant','radio shell CO HI gamma'),('N10','Gamma-ray binary microquasar','orbital periodicity optical X-ray'),('N11','Magnetar transient','bursts timing X-ray'),('N12','Gamma-ray burst afterglow','GBM Swift temporally localized event'),('N13','Compact object accretion','X-ray timing and spectral evidence'),('N14','Star cluster multiple MSPs','clusters X-ray radio timing'),('N15','Cosmic rays interstellar gas','CO HI diffuse templates'),('N16','Inverse-Compton or bremsstrahlung','gas radiation field templates'),('N17','Unresolved source population','PSF spatial source deblending'),('N18','Solar lunar moving source','ephemeris and event filtering'),('N19','Dark matter natural alternative','spatial halo templates and systematic studies'),('N20','New natural particle plasma emission','multimodal predictive physical model'),('N21','Diffuse foreground mismatch','alternate diffuse models ROI fits'),('N22','Detector reconstruction artifact','IRF event-class and null region controls')]
T=[
('T01','Narrow energetic line pattern','photon energy-dispersion and natural-line controls'),('T02','Precisely periodic modulation','photon times barycentric timing red noise'),('T03','Directional narrow gamma beam','repeatability position broadband flux'),('T04','Antimatter engine byproducts','physical model broadband energy budget'),('T05','Engineered compact object energy extraction','natural compact-source alternatives'),('T06','Cross-band encoded correlation','radio X-ray optical gamma trials corrected'),('T07','Artificial repetitive transient burst','temporal injection recovery transient controls')]
with (R/'docs/hypothesis_library.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['hypothesis_id','hypothesis_family','description','required_test']);w.writerows([(a,'natural',b,c) for a,b,c in N]+[(a,'hypothetical_technology',b,c) for a,b,c in T])
with (R/'examples/source_hypothesis_matrix_not_tested.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['source_name','hypothesis_id','test_status','evidence_basis','interpretation'])
 sources=list(csv.DictReader((R/'examples/unidentified_60_from_user_whitepaper.csv').open()))
 for s in sources:
  for a,_,_ in N+T:w.writerow([s['source_name'],a,'NOT_TESTED','no_photon_IRF_or_crosssurvey_data','DO_NOT_INFER_SOURCE_CLASS'])
print('Created 29 hypotheses x',len(sources),'sources =',29*len(sources),'unperformed tests')
