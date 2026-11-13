#!/usr/bin/env python3
"""Cross-file execution-provenance, graph-inventory and high-precision audit."""
import argparse,csv,hashlib,json,re
from pathlib import Path
from high_precision_reference import audit

def verify(root):
    exec_path=root/'results/sdk_execution.txt';inv=root/'results/math_execution_inventory.csv'
    if not exec_path.is_file() or not inv.is_file():raise RuntimeError('Missing original paceval execution results')
    log=exec_path.read_text();assert 'original paceval SDK execution SUCCESS' in log
    counts=dict(re.findall(r'^([^=\n]+)=([^\n]+)$',log,re.M))
    with inv.open() as f: rows=list(csv.DictReader(f))
    with (root/'results/formula_registry.csv').open() as f:registry=list(csv.DictReader(f))
    graph_rows=[r for r in rows if r['execution_owner']=='paceval']
    assert len(registry)==int(counts['graphs_registered_and_executed'])==len(graph_rows)
    assert {r['function_id'] for r in registry}=={r['paceval_graph_id'] for r in graph_rows}
    assert all(r['status']=='executed_verified' for r in graph_rows)
    assert int(counts['batch_calls'])>1 and int(counts['batch_graph_outputs'])>len(graph_rows)
    assert int(counts['independent_native_checks'])>100
    stats=audit(root)
    sdk_dir=Path(__file__).resolve().parent
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (sdk_dir/'paceval_main.h',sdk_dir/'paceval_main.cpp')}
    # Mark the independent reference only after the high-precision audit truly ran.
    for r in rows:
        if r['function_id']=='high_precision_reference': r['status']='executed_verified'
    with inv.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    result={'status':'PASS','original_paceval_graph_count':len(graph_rows),'multi_graph_batch_calls':int(counts['batch_calls']),
            'batch_graph_outputs':int(counts['batch_graph_outputs']),
            'independent_native_checks':int(counts['independent_native_checks']),
            'independent_high_precision_comparisons':stats['independent_high_precision_comparisons'],
            'source_sha256':hashes}
    (root/'results/verification_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));a=p.parse_args();verify(a.root)
