#!/usr/bin/env python3
"""Create a machine-readable inventory and counts from preserved MCP records.
Do not use these derived counts as independent proof of a local SDK run.
"""
import csv,json,pathlib
r=pathlib.Path(__file__).resolve().parents[1]
m=json.loads((r/'src/formula_manifest.json').read_text())
def read(fn):
 with open(r/fn,newline='') as f:return list(csv.DictReader(f))
grid=read('results/mcp_corner_grid_recorded_81.csv');snap=read('results/mcp_path_snapshots_recorded_16.csv');tinc=read('results/mcp_tinc_recorded_24.csv');ops=read('results/mcp_operator_selftest_record.csv');high=json.loads((r/'results/high_precision_audit.json').read_text());
assert len(m['graphs'])==22 and len(grid)==81 and len(snap)==16 and len(tinc)==24 and len(ops)==21
assert all(int(v['error_code'])==0 for v in tinc+ops)
handles=['1690336128','1691478496','1690908752','1690395456','1690295616','1691283328','1691388160','1691005056','1691045568','1690419840','1690825040','1690808912','1690814288','1094354656','1691272576','1690619360','934036544','1019804304','1691462368','1039927136','1690632800','1691465056']
interval_handles=['1689945264','972693728','1690980672']
op_handles=['1167707040','1691818720','1093747104','1582471696','1692338080','973250336','1093690656']
with (r/'results/math_execution_inventory.csv').open('w',newline='') as f:
 writer=csv.writer(f);writer.writerow('function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason'.split(','))
 for k,g in enumerate(m['graphs']):
  writer.writerow([g['id'],g['industrial_purpose'],g['formula'],'see manifest', 'paceval',f'MCP handle {handles[k]}',g['version'],'MCP v4.26 create_computation / evaluate_multiple_many','recorded snapshot + native mpmath reference','MCP_EXECUTED_AND_VERIFIED','Local SDK runtime not available, C++ compiled syntax only'])
 for id,why in [('input_validation','CSV grammar, units, domain and finite checks before API call'),('path_scenario_generation','Host constructs synthetic scenario paths and immutable operating points'),('worst_corner_selection','Host chooses worst-case row after evaluated paceval score and slack'),('csv_serialization','Original SDK converter used when local runtime becomes available'),('independent_reference','Native C++ and 90-digit mpmath references are independent audit paths'),('corner_interpolation','Chart interpolation is a presentation aid, not a computed paceval result')]:
  writer.writerow([id,id,'host orchestration or nonproductive scientific reference','context','host','','n/a','host or plotting, not paceval production graph','audited design','IMPLEMENTED_OR_DOCUMENTED',why])
meta={'project':'WP08 Integrated Circuit Timing and Leakage Corner Sweeps','remote_engine':'original paceval MCP reported version 4.26',
'actual_remote_graphs':{'main_distinct_expressions_created':len(handles),'main_distinct_expressions_executed':len(handles),'additional_interval_enabled_handles':len(interval_handles),'additional_operator_handles':len(op_handles),'total_remote_create_successes':len(handles)+len(interval_handles)+len(op_handles)},
'actual_remote_calls':{'main_multi_graph_batch_calls':2,'interval_multi_graph_batch_calls':1,'operator_multi_graph_batch_calls':1,'main_grid_scenarios':81,'main_snapshot_scenarios':16,'interval_cases':8,'operator_cases':3,'main_graph_point_evaluations':len(handles)*(len(grid)+len(snap)),'interval_graph_point_evaluations':len(tinc),'operator_graph_point_evaluations':len(ops),'total_all_remote_graph_point_evaluations':len(handles)*(len(grid)+len(snap))+len(tinc)+len(ops)},
'archived_values':{'grid_recorded_main_graphs_per_case':10,'grid_main_recorded_values':81*10,'snapshot_recorded_main_graphs_per_case':22,'snapshot_main_recorded_values':16*22,'main_recorded_values':81*10+16*22,'high_precision_checks':high['regular_graph_point_checks'],'tinc_checks':len(tinc),'tinc_inclusions':high['tinc_printed_interval_inclusions'],'operator_checks':len(ops),'operator_passes':sum(x['actual']==x['expected'] for x in ops)},
'files':{'grid':'results/mcp_corner_grid_recorded_81.csv','snapshots':'results/mcp_path_snapshots_recorded_16.csv','tinc':'results/mcp_tinc_recorded_24.csv','operators':'results/mcp_operator_selftest_record.csv','validation':'results/high_precision_audit.json','formulas':'src/formula_manifest.json'},
'important_provenance_notes':['All results are from actual remote paceval MCP v4.26 calls, not an executed C++ program.','All 22 formulas executed across all grid and snapshot scenarios; the grid file preserves a specified subset of 10 returned outputs per grid point.','MCP handles are opaque session identifiers; new handles must be obtained during reproduction.','The recorded decimal values were transferred from the tool output, then independently checked.','No runtime speed/energy results, no Liberty timing tables, no STA signoff and no real silicon measurements.','Local SDK C++ source compiled with C++17 syntax only; no CTest success is asserted.'],
'local_sdk_tests':{'cpp_syntax_checked':True,'sdk_runtime_library_available':False,'local_graph_evaluation_executed':False,'local_conversion_tests_executed':False,'ctest_passed':0,'ctest_total_executed':0},
'error_status':{'main_mcp_graph_point_error_codes':'all 0','operator_error_codes':'all 0','tinc_error_codes':'all 0'},
'limitations':'Finite printed interval inclusions are not whole-domain certification.'}
(r/'results/execution_evidence.json').write_text(json.dumps(meta,indent=2)+'\n')
print('Generated evidence with',meta['actual_remote_calls']['total_all_remote_graph_point_evaluations'],'actual remote graph-points')
