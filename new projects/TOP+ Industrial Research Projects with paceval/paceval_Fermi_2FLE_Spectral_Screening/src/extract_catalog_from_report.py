#!/usr/bin/env python3
"""Extract exactly the 60 transcribed catalog rows from Appendix A of the USER'S V4 PDF.
This script does not read or pretend to reproduce the original NASA FITS binary table.
"""
from pathlib import Path
import fitz, csv, re, hashlib
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs'/'Fermi_2FLE_Research_Proposal_V4_DE.pdf'
assert SOURCE.exists(),SOURCE
p=fitz.open(SOURCE)
rows=[]
for pn in (10,11,12):
    t=p[pn].get_text('text')
    stop=t.find('Anhang B.')
    if stop>=0:t=t[:stop]
    lines=[v.strip() for v in t.splitlines()]
    for i,v in enumerate(lines):
        if not re.match(r'^2FLE J\d{4}\.\d[+-]\d{4}$',v):continue
        assert i+4<len(lines),(pn,i,v)
        ts=float(lines[i+1].replace(',',''))
        lat=float(lines[i+2]);bands=int(lines[i+3]);assoc=lines[i+4]
        group='no_ASSOC3' if pn==10 else 'has_ASSOC3'
        if group=='no_ASSOC3':assert assoc in {'—','-',''}
        rows.append((v,ts,lat,bands,'' if group=='no_ASSOC3' else assoc,group,pn+1))
assert len(rows)==60,len(rows)
assert sum(x[5]=='no_ASSOC3' for x in rows)==22
assert sum(x[5]=='has_ASSOC3' for x in rows)==38
assert sum(x[3]==3 for x in rows)==10
assert len(set(x[0] for x in rows))==60
out=ROOT/'examples'/'unidentified_60_from_user_whitepaper.csv'
out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['source_name','catalog_TS','galactic_latitude_deg','usable_band_count_TS_ge_4','ASSOC3_unconfirmed','ASSOC3_flag','user_report_page'])
  w.writerows(rows)
( ROOT/'results'/'source_provenance.txt').write_text('SOURCE: '+str(SOURCE.name)+'\nSHA256: '+hashlib.sha256(SOURCE.read_bytes()).hexdigest()+'\nTRANSCRIPTION: 60 source metadata records from Appendix A, pp. 11-13; NOT full NASA FITS or photon events\nCOUNTS: 60 total; 22 without ASSOC3; 38 with unconfirmed ASSOC3; 10 with 3 useful bands\n')
print('Extracted',len(rows),'real catalog *metadata* records from supplied PDF; none are photon spectra.')
