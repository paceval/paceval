#!/usr/bin/env python3
"""Release self-audit with real file checks, markdown parsing and PDF integrity."""
from pathlib import Path
import zipfile,sys,json,subprocess,hashlib,importlib.util
root=Path(__file__).resolve().parents[1]
archive=Path(sys.argv[1]) if len(sys.argv)>1 else None
spec=importlib.util.spec_from_file_location('md',root/'scripts'/'check_markdown.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
md=module.check(root)
proof=json.loads((root/'results'/'execution_evidence.json').read_text())
hp=json.loads((root/'results'/'high_precision_audit.json').read_text())
assert proof['unique_graphs_created']==proof['unique_graphs_executed']==53
assert proof['scenario_count']==3072 and hp['independent_value_checks']==73728
assert hp['status']=='PASS' and hp['subcritical_v2_rows']>0
assert (root/'src'/'paceval_main.h').is_file() and (root/'src'/'paceval_main.cpp').is_file()
assert len(list((root/'figures').glob('fig[0-9][0-9]_*.png')))==9
assert len(list((root/'figures').glob('fig[0-9][0-9]_*.pdf')))==9
assert 'Pages:           16' in subprocess.check_output(['pdfinfo',str(root/'paceval_Compressed_Air_Leak_Energy_Whitepaper_EN.pdf')],text=True)
files=[p for p in root.rglob('*') if p.is_file()]
assert not any(p.suffix.lower()=='.so' for p in files)
if archive:
 with zipfile.ZipFile(archive,'r') as z:
  assert z.testzip() is None
  names=z.namelist();assert len(names)==len(files)
  assert all(not n.lower().endswith('.so') for n in names)
  for p in files: assert (root.name+'/'+str(p.relative_to(root))) in names
print('RELEASE AUDIT PASS: files',len(files),'markdown',md['files_checked'],'links',md['local_links_checked'],'figures',9,'graphs',53,'cases',3072,'high precision',73728)
