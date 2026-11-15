#!/usr/bin/env python3
"""Generate input CSV and independent references, and transcribe the observed MCP outputs.
Observed values are literal records from actual remote paceval MCP 4.26 calls in this research turn;
they are not raw JSON protocol payloads. High-precision reference values are separate.
"""
import csv, json, math, hashlib, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import independent_model as model
ROOT=HERE.parent
EX=ROOT/'examples';RES=ROOT/'results';SRC=ROOT/'src'
for p in [EX,RES,SRC]:p.mkdir(parents=True,exist_ok=True)

def csvfile(name,headers,rows):
    with (RES/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(headers);w.writerows(rows)

def header(name,modelvars,formulas,prefix):
    with (SRC/name).open('w',encoding='utf-8') as f:
        f.write('// Research graph manifest, actual remote paceval MCP 4.26 successful registration.\n#pragma once\n#include <cstddef>\n')
        f.write(f'static const char* {prefix}_variable_list = R"pv({" ".join(modelvars)})pv";\n')
        f.write(f'static constexpr size_t {prefix}_variable_count = {len(modelvars)};\n')
        f.write(f'static const ModelGraph {prefix}_graphs[] = {{\n')
        for name,expr,units in formulas:
            f.write(f'    {{R"pv({name})pv", R"pv({expr})pv", R"pv({units})pv"}},\n')
        f.write('};\n')
        f.write(f'static constexpr size_t {prefix}_graph_count = sizeof({prefix}_graphs)/sizeof({prefix}_graphs[0]);\n')

for group,prefix,variables,formulas in [('axis','sat_axis',model.AXIS_VARS,model.AXIS_FORMULAS),('aggregate','sat_agg',model.AGG_VARS,model.AGG_FORMULAS),('quaternion','sat_quat',model.Q_VARS,model.QUAT_FORMULAS)]:
    header('generated_'+group+'_formulas.h',variables,formulas,prefix)
manifest={'project':'WP32 Satellite Attitude Actuator Torque and Momentum Envelopes','remote_engine':'paceval MCP 4.26','model_versions':['v1 (rigid inertia coupling without wheel gyroscope)','v2 (rigid and wheel gyroscopic coupling)'],'axis_domain':'I,Ij,Ik,Jw,dt,torque/momentum/rate limits strictly positive; orthogonal wheel geometry; finite values','graph_groups':[]}
for group,vars,formulas in [('axis',model.AXIS_VARS,model.AXIS_FORMULAS),('aggregate',model.AGG_VARS,model.AGG_FORMULAS),('quaternion',model.Q_VARS,model.QUAT_FORMULAS)]:
    manifest['graph_groups'].append({'group':group,'variables':vars,'remote_registration':'successful for each expression, reported error 0','graphs':[{'id':id,'expression':ex,'units':units,'owner':'paceval persistent mathematical graph'} for id,ex,units in formulas]})
(SRC/'formula_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

cases=model.cases()
with (EX/'axis_snapshots.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['case_id','axis',*model.AXIS_VARS]);
    for cid,rows in cases:
        for axis,v in zip('xyz',rows):w.writerow([cid,axis,*[format(x,'.17g') for x in v]])

with (EX/'quaternion_snapshots.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['case_id',*model.Q_VARS]);
    for i in range(12):
        ang=.05*i;sp=.012+.001*i;x=[math.cos(ang/2),math.sin(ang/2),0,0,sp,-.007+.0002*i,.005,1.8]
        w.writerow([f'Q{i+1:03d}',*[format(v,'.17g') for v in x]])

csvfile('independent_axis_reference_all.csv',['case_id','axis']+[id for id,_,_ in model.AXIS_FORMULAS],(
    [cid,ax,*[format(model.axis_ref(vals)[id],'.17g') for id,_,_ in model.AXIS_FORMULAS]]
    for cid,rows in cases for ax,vals in zip('xyz',rows)))
csvfile('independent_joint_reference_grid.csv',['case_id','hx','taux']+[id for id,_,_ in model.AGG_FORMULAS],(
 [cid,rows[0][6],rows[0][9],*[format(model.agg_ref(model.agg_inputs([model.axis_ref(v) for v in rows]))[id],'.17g') for id,_,_ in model.AGG_FORMULAS]]
 for cid,rows in cases))

# These are explicit transcriptions of the 49 actual MCP aggregate results; not recomputed reference outputs.
JOINT_REMOTE='''
S001,.015,-.0009,1,1,0,0,0,0,.011676
S002,.015,-.0006,1,1,.307263157894737,.307263157894737,0,.0003,.011676
S003,.015,-.0003,1,1,.292656108597285,.224239819004525,0,.00058,.011676
S004,.015,0,1,0,.0483122171945702,-.0201040723981901,1,.00058,.011676
S005,.015,.0003,0,0,-.196031674208145,-.264447963800905,0,.00058,.011676
S006,.015,.0006,0,0,-.44037556561086,-.50879185520362,0,.0003,.011676
S007,.015,.0009,0,0,-.684719457013575,-.753135746606335,0,0,.011676
S008,.019,-.0009,1,1,0,0,0,0,.011676
S009,.019,-.0006,1,1,.307263157894737,.307263157894737,0,.0003,.011676
S010,.019,-.0003,1,1,.292656108597285,.224239819004525,0,.00058,.011676
S011,.019,0,1,0,.0483122171945702,-.0201040723981901,1,.00058,.011676
S012,.019,.0003,0,0,-.196031674208145,-.264447963800905,0,.00058,.011676
S013,.019,.0006,0,0,-.44037556561086,-.50879185520362,0,.0003,.011676
S014,.019,.0009,0,0,-.684719457013575,-.753135746606335,0,0,.011676
S015,.023,-.0009,1,1,0,0,0,0,.00938
S016,.023,-.0006,1,1,.291764705882353,.291764705882353,0,.0003,.00992
S017,.023,-.0003,1,1,.292656108597285,.224239819004525,0,.00058,.01046
S018,.023,0,1,0,.0483122171945702,-.0201040723981901,1,.00058,.011
S019,.023,.0003,0,0,-.196031674208145,-.264447963800905,0,.00058,.01154
S020,.023,.0006,0,0,-.44037556561086,-.50879185520362,0,.0003,.011676
S021,.023,.0009,0,0,-.684719457013575,-.753135746606335,0,0,.011676
S022,.027,-.0009,1,1,0,0,0,0,.00538
S023,.027,-.0006,1,1,.174117647058824,.174117647058824,0,.0003,.00592
S024,.027,-.0003,1,1,.19,.19,0,.00058,.00646
S025,.027,0,1,0,.0483122171945702,-.0201040723981901,1,.00058,.007
S026,.027,.0003,0,0,-.196031674208145,-.264447963800905,0,.00058,.00754
S027,.027,.0006,0,0,-.44037556561086,-.50879185520362,0,.0003,.00808
S028,.027,.0009,0,0,-.684719457013575,-.753135746606335,0,0,.00862
S029,.031,-.0009,1,1,0,0,0,0,.00138000000000001
S030,.031,-.0006,1,1,.0564705882352943,.0564705882352943,0,.0003,.00192000000000001
S031,.031,-.0003,1,1,.0723529411764707,.0723529411764707,0,.00058,.00246
S032,.031,0,1,0,.0483122171945702,-.0201040723981901,1,.00058,.003
S033,.031,.0003,0,0,-.196031674208145,-.264447963800905,0,.00058,.00354
S034,.031,.0006,0,0,-.44037556561086,-.50879185520362,0,.0003,.00408
S035,.031,.0009,0,0,-.684719457013575,-.753135746606335,0,0,.00462
S036,.035,-.0009,0,0,-.0770588235294117,-.0770588235294117,0,0,-.00262
S037,.035,-.0006,0,0,-.0611764705882352,-.0611764705882352,0,.0003,-.00208
S038,.035,-.0003,0,0,-.0452941176470588,-.0452941176470588,0,.00058,-.00154
S039,.035,0,0,0,-.0294117647058824,-.0294117647058824,0,.00058,-.001
S040,.035,.0003,0,0,-.196031674208145,-.264447963800905,0,.00058,-.000460000000000002
S041,.035,.0006,0,0,-.44037556561086,-.50879185520362,0,.0003,.0000799999999999967
S042,.035,.0009,0,0,-.684719457013575,-.753135746606335,0,0,.000619999999999996
S043,.039,-.0009,0,0,-.194705882352941,-.194705882352941,0,0,-.00662
S044,.039,-.0006,0,0,-.178823529411765,-.178823529411765,0,.0003,-.00608
S045,.039,-.0003,0,0,-.162941176470588,-.162941176470588,0,.00058,-.00554
S046,.039,0,0,0,-.147058823529412,-.147058823529412,0,.00058,-.005
S047,.039,.0003,0,0,-.196031674208145,-.264447963800905,0,.00058,-.00446
S048,.039,.0006,0,0,-.44037556561086,-.50879185520362,0,.0003,-.00392
S049,.039,.0009,0,0,-.684719457013575,-.753135746606335,0,0,-.00337999999999999
'''
rows=list(csv.reader(x for x in JOINT_REMOTE.strip().splitlines()));assert len(rows)==49
csvfile('mcp_observed_joint_grid.csv',['case_id','hx_Nms','taux_Nm','joint_guard_v1','joint_guard_v2','joint_score_v1','joint_score_v2','decision_changed','min_torque_margin_Nm','min_momentum_margin_Nms'],rows)

# Selected x-axis actual MCP outputs (S001, S003, S004, S025, S031, S036, S040, S049).
AXIS_REMOTE='''
S001,.015,-.0009,.0056850588235294,.0074638823529412,.01662,.01738,.020314941176471,.018536117647059,0,0,1,1,-.0086311764705882,-.000084
S003,.015,-.0003,.018390941176471,.020169764705882,.01554,.01846,.0076090588235294,.0058302352941176,.29265610859729,.22423981900452,1,1,-.0015723529411765,-.000084
S004,.015,0,.024743882352941,.026522705882353,.015,.019,.0012561176470588,-.00052270588235294,.04831221719457,-.02010407239819,1,0,.0019570588235294,-.000084
S025,.027,0,.024743882352941,.026522705882353,.027,.007,.0012561176470588,-.00052270588235294,.04831221719457,-.02010407239819,1,0,.0019570588235294,-.000084
S031,.031,-.0003,.018390941176471,.020169764705882,.03154,.00246,.0076090588235294,.0058302352941176,.072352941176471,.072352941176471,1,1,-.0015723529411765,-.000084
S036,.035,-.0009,.0056850588235294,.0074638823529412,.03662,-.00262,.020314941176471,.018536117647059,-.077058823529412,-.077058823529412,0,0,-.0086311764705882,-.000084
S040,.035,.0003,.031096823529412,.032875647058824,.03446,-.00046,-.0050968235294118,-.0068756470588235,-.19603167420814,-.26444796380091,0,0,.0054864705882353,-.000084
S049,.039,.0009,.043802705882353,.045581529411765,.03738,-.00338,-.017802705882353,-.019581529411765,-.68471945701357,-.75313574660633,0,0,.012545294117647,-.000084
'''
csvfile('mcp_observed_axis_x_examples.csv',['case_id','hx','taux','rate_v1','rate_v2','wheel_h_next','momentum_margin','rate_margin_v1','rate_margin_v2','score_v1','score_v2','guard_v1','guard_v2','acceleration_v2','gyro_coupling'],list(csv.reader(AXIS_REMOTE.strip().splitlines())))

QUAT_REMOTE='''
Q001,1,0,0,0,.012,-.007,.005,1.00008828610278,.999911721690966,.0107990465942624,-.00629944384665309,.00449960274760935
Q002,.9996875162757026,.02499739591471233,0,0,.013,-.0068,.005,1.00009729246709,.999297822592985,.0366901701779636,-.00622996975209644,.00434518700627882
Q003,.9987502603949663,.04997916927067833,0,0,.014,-.0066,.005,1.0001071410604,.998013594627337,.0625567201583222,-.00615682315990213,.00419705022989735
Q004,.9971888181122075,.07492970727274235,0,0,.015,-.0064,.005,1.00011783185783,.996059899475564,.0883813421795109,-.00608027482497493,.00405527672682322
Q005,.9950041652780258,.09983341664682815,0,0,.016,-.0062,.005,1.00012936483237,.993438048131745,.11414671005682,-.00600059735089169,.00391994117632864
Q006,.992197667229329,.1246747333852277,0,0,.017,-.006,.005,1.00014173995489,.990149800020543,.139835537411071,-.00591806487702318,.00379110859069111
Q007,.9887710779360422,.1494381324735992,0,0,.018,-.0058,.005,1.00015495719413,.986197361813921,.165430589276225,-.00583295276496336,.00366883428693316
Q008,.9847265389049334,.174108137593596,0,0,.019,-.0056,.005,1.00016901651671,.981583385947331,.190914693672357,-.00574553728455359,.00355316386822018
Q009,.9800665778412416,.1986693307950612,0,0,.020,-.0054,.005,1.00018391788711,.976310968836384,.216270753136244,-.0056560952997894,.00344413321491779
Q010,.9747941070689433,.2231063621317455,0,0,.021,-.0052,.005,1.00019966126769,.97038364879519,.241481756201781,-.00556490395489731,.00334176848530158
Q011,.9689124217106447,.2474039592545229,0,0,.022,-.005,.005,1.0002162466187,.963805403657779,.266530788822531,-.0054722403608685,.00324608612590381
Q012,.962425197628238,.2715469369561129,0,0,.023,-.0048,.005,1.00023367389825,.956580648104209,.291401045728706,-.00537838128273586,.00315709289147356
'''
csvfile('mcp_observed_quaternion.csv',['case_id','q0','q1','q2','q3','wx','wy','wz','candidate_norm','next_q0','next_q1','next_q2','next_q3'],list(csv.reader(QUAT_REMOTE.strip().splitlines())))

PROFILE='''
1,10,.039,.0375,.0035,0,1,.045
2,20,.0375,.036,.005,0,1,.0432692307692308
3,30,.036,.0345,.00650000000000001,0,1,.0415384615384615
4,40,.0345,.033,.008,0,1,.0398076923076923
5,50,.033,.0315,.0095,0,1,.0380769230769231
6,60,.0315,.03,.011,0,1,.0363461538461538
7,70,.03,.0285,.0125,0,1,.0346153846153846
8,80,.0285,.027,.014,0,1,.0328846153846154
9,90,.027,.0255,.0155,0,1,.0311538461538462
10,100,.0255,.024,.017,0,1,.0294230769230769
11,110,.024,.0225,.0185,0,1,.0276923076923077
12,120,.0225,.021,.02,0,1,.0259615384615385
'''
csvfile('mcp_observed_desaturation.csv',['step','time_s','momentum_in_Nms','momentum_next_Nms','momentum_margin_Nms','body_acceleration_rad_s2','guard_v2','wheel_mechanical_power_proxy_W'],list(csv.reader(PROFILE.strip().splitlines())))

TINC='''
T01,-.0006,.015,rate_margin_v2,0,.0121831764705882,.0121831764705882,.0121831764705883
T02,-.0003,.023,rate_margin_v2,144,,,
T03,0,.027,rate_margin_v2,0,-.000522705882352942,-.000522705882352968,-.000522705882352913
T04,.0003,.027,rate_margin_v2,0,-.00687564705882352,-.0068756470588236,-.00687564705882345
T05,-.0006,.035,rate_margin_v2,0,.0121831764705882,.0121831764705882,.0121831764705883
T06,-.0003,.039,rate_margin_v2,144,,,
T07,-.0006,.015,momentum_margin,0,.01792,.01792,.01792
T08,-.0003,.023,momentum_margin,0,.01046,.01046,.01046
T09,0,.027,momentum_margin,0,.007,.007,.007
T10,.0003,.027,momentum_margin,0,.00754,.00754,.00754
T11,-.0006,.035,momentum_margin,0,-.00208,-.00208000000000001,-.00207999999999999
T12,-.0003,.039,momentum_margin,0,-.00554,-.00554,-.00554
'''
csvfile('mcp_observed_tinc.csv',['case_id','tau_x_Nm','h_x_Nms','formula','error_number','value','lower','upper'],list(csv.reader(TINC.strip().splitlines())))

EXEC={'date_utc':'2026-11-15','source_proposal':'WP 32 uploaded PDF, research plan only','remote_engine':'paceval MCP 4.26','registered_graphs':{'axis':30,'aggregate':8,'quaternion':5},'successful_graph_point_evaluations':{'axis_147x30':4410,'aggregate_49x8':392,'quaternion_12x5':60,'desaturation_12x5':60},'primary_total':4922,'primary_errors':0,'main_cases':49,'axis_vectors':147,'quaternion_cases':12,'desaturation_steps':12,'aggregate_results':{'v1_eligible':20,'v2_eligible':15,'changed':5},'observed_csv_types':'Selected transcriptions of real MCP response values, not complete raw protocol payload','tinc':{'unique_interval_graphs':2,'evaluations':12,'no_error':10,'error_144':2,'input_interval_certification':False},'local_sdk_execution':'not performed; compatible libpaceval.so absent','performance':'not benchmarked','assumptions':'hypothetical 3-axis reaction-wheel geometry, synthetic values, first-order time step and quaternion normalized Euler update'}
(RES/'execution_evidence.json').write_text(json.dumps(EXEC,indent=2)+'\n',encoding='utf-8')
(RES/'README_DATA.md').write_text('''# Data provenance and reproduction

The `mcp_observed_*.csv` files are **literal transcriptions of actual remote paceval MCP 4.26 responses** produced for this study, not an unmodified wire-format export. The independent files are generated from a separately implemented mathematical reference and must **not** be treated as MCP output. The full 30 x 147 graph-point response was checked for reported errors in the remote execution but not saved as a complete raw dump; selected axis values and all 49 aggregate scenarios were archived here.

The model grid, quaternion inputs, formula IDs, remote evaluation totals, scientific assumptions, TINC outcomes (including errors 144) and local execution limitations are specified in JSON and code. All datasets are synthetic. For the actual local SDK numerical output, build and execute `src/satellite_attitude_paceval.cpp` with the original matching shared library, which is not included in this archive.
''',encoding='utf-8')

if __name__=='__main__':
    print('generated',len(cases),'cases,',sum(len(v) for _,v in cases),'axis vectors; 43 graphs')
    print('observed grid',len(rows),'observed quaternion 12; observed profile 12; observed TINC 12')
