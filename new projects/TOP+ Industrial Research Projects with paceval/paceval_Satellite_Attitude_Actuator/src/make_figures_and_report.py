#!/usr/bin/env python3
"""WP32 publication builder: scientific figures from transcribed *actual* remote paceval data;
whitepaper is a real PDF, never generated Markdown; title image is conceptual.
"""
import csv,math,json,os,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,TwoSlopeNorm
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image as RImage,PageBreak,KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1];RES=ROOT/'results';FIG=ROOT/'figures'
load=lambda name:list(csv.DictReader((RES/name).open()))
grid=load('mcp_observed_joint_grid.csv');aix=load('mcp_observed_axis_x_examples.csv');quat=load('mcp_observed_quaternion.csv');profile=load('mcp_observed_desaturation.csv');tinc=load('mcp_observed_tinc.csv');audit=json.loads((RES/'high_precision_validation.json').read_text())
TEAL='#00a7b3';CYAN='#1b9fc4';BLUE='#235c97';ORANGE='#f08b46';RED='#d45165';INK='#102d46';BG='#f6f9fb';GREY='#688099';DARK='#0a2945'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelcolor':INK,'axes.spines.top':False,'axes.spines.right':False,'xtick.color':'#536779','ytick.color':'#536779','figure.facecolor':'white'})

def save(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=200,bbox_inches='tight',facecolor='white')
    fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight',facecolor='white')
    plt.close(fig)

# Conceptual pipeline. Not an empirical data plot.
fig,ax=plt.subplots(figsize=(11.5,4.2));ax.set_xlim(0,12);ax.set_ylim(0,4.8);ax.axis('off')
items=[(.2,1.4,2.3,1.6,'Physical inputs\n49 x 3-axis snapshots','#d7f1f4'),(3.0,2.45,2.5,1.6,'paceval MCP\n30 axis graphs','#bde3eb'),(6.15,2.45,2.3,1.6,'paceval MCP\n8 joint graphs','#b8d6eb'),(9.25,1.4,2.4,1.6,'Audited outputs\nCSV + diagrams','#e0e9f4'),(3,.25,2.5,1.35,'12 quaternion states\n5 paceval graphs','#e3f1e5'),(6.15,.25,2.3,1.35,'90-digit mpmath\nindependent checks','#fbebd6')]
for x,y,w,h,txt,c in items:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.12,rounding_size=.12',facecolor=c,edgecolor='#99b2bf',lw=1.2))
    ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=11,fontweight='bold',color=INK)
for x,y,x2,y2 in [(2.55,2.25,2.93,3.15),(5.6,3.18,6.06,3.18),(8.53,3.15,9.15,2.32),(5.6,1.05,9.12,1.65),(8.55,.9,9.16,1.55)]:
    ax.add_patch(FancyArrowPatch((x,y),(x2,y2),arrowstyle='-|>',mutation_scale=18,color=TEAL,lw=2))
ax.set_title('Graph ownership: physical formulas run in paceval, independent reference is separate',loc='left',fontsize=13,fontweight='bold',pad=12)
save(fig,'01_execution_architecture')

# Binary state maps from actual 49 joint MCP outputs.
mat1=np.array([int(x['joint_guard_v1']) for x in grid]).reshape(7,7)
mat2=np.array([int(x['joint_guard_v2']) for x in grid]).reshape(7,7)
TX=np.array([-.9,-.6,-.3,0,.3,.6,.9]);HX=np.array([15,19,23,27,31,35,39]);
fig,(ax,bx)=plt.subplots(1,2,figsize=(11.7,5.2),sharex=True,sharey=True)
for a,m,title in [(ax,mat1,'v1 · bus inertia coupling'),(bx,mat2,'v2 · including wheel gyro')]:
    a.imshow(m,aspect='auto',origin='lower',cmap=ListedColormap(['#f2dce0','#bceade']),vmin=0,vmax=1)
    for j in range(7):
        for i in range(7):a.text(i,j,'YES' if m[j,i] else 'NO',fontsize=8.5,fontweight='bold',ha='center',va='center',color='#1d5b55' if m[j,i] else '#984f5d')
    a.set_xticks(range(7),TX);a.set_yticks(range(7),HX);a.set_xlabel('x-axis commanded body torque (mN m)');a.set_title(title,fontweight='bold',fontsize=11)
ax.set_ylabel('Initial x-axis wheel momentum (mN m s)')
fig.suptitle('Actual paceval MCP three-axis feasibility decisions',fontweight='bold',fontsize=13,x=.01,ha='left');fig.tight_layout(rect=[0,0,1,.9]);save(fig,'02_joint_feasibility_comparison')

# Scores actual MCP numerical data.
s1=np.array([float(x['joint_score_v1']) for x in grid]).reshape(7,7)
s2=np.array([float(x['joint_score_v2']) for x in grid]).reshape(7,7)
fig,(ax,bx)=plt.subplots(1,2,figsize=(12,5.25),sharex=True,sharey=True)
lo=min(s1.min(),s2.min());hi=max(s1.max(),s2.max());norm=TwoSlopeNorm(vcenter=0,vmin=lo,vmax=hi)
for a,score,title in [(ax,s1,'Version 1'),(bx,s2,'Version 2')]:
    c=a.imshow(score,cmap='RdBu',norm=norm,origin='lower',aspect='auto')
    for j in range(7):
        for i in range(7):a.text(i,j,f'{score[j,i]:.2f}',fontsize=8,ha='center',va='center',color='white' if abs(score[j,i])>.25 else '#233948')
    a.set_xticks(range(7),TX);a.set_yticks(range(7),HX);a.set_xlabel('Body torque x (mN m)');a.set_title(title,fontweight='bold')
ax.set_ylabel('Initial wheel momentum x (mN m s)');fig.colorbar(c,ax=[ax,bx],label='Joint normalized minimum margin',fraction=.024,pad=.025)
fig.suptitle('Actual paceval normalized envelope scores',x=.02,ha='left',fontweight='bold',fontsize=13);fig.subplots_adjust(left=.08,right=.87,top=.86,bottom=.16,wspace=.14)
save(fig,'03_joint_score_heatmap')

# Decision change distribution and marginal competition.
fig,(ax,bx)=plt.subplots(1,2,figsize=(11.3,4.9))
change=np.array([int(x['decision_changed']) for x in grid]).reshape(7,7)
ax.imshow(change,origin='lower',aspect='auto',cmap=ListedColormap(['#e9edf2','#ecac77']),vmin=0,vmax=1)
for j in range(7):
 for i in range(7):ax.text(i,j,'Δ' if change[j,i] else '·',fontsize=17,ha='center',va='center',color='#9f4e26' if change[j,i] else '#8da2ae')
ax.set_xticks(range(7),TX);ax.set_yticks(range(7),HX);ax.set_xlabel('Body torque x (mN m)');ax.set_ylabel('Initial wheel momentum x (mN m s)');ax.set_title('Five changed classification cells',fontweight='bold')
for idx,col,label in [(0,'#2375a9','v1'),(1,'#df804a','v2')]:
  ss=[float(r['joint_score_'+label]) for r in grid]
  bx.plot(range(len(ss)),ss,linewidth=1.7,label=label,color=col)
bx.axhline(0,ls='--',color=RED,lw=1);bx.set_xlabel('Case index (ordered 7 x 7 grid)');bx.set_ylabel('Dimensionless joint margin');bx.set_title('Modeled scenario scores',fontweight='bold');bx.grid(alpha=.12);bx.legend(frameon=False)
fig.tight_layout();save(fig,'04_model_decision_changes')

# x-axis rates actual only 8 selected samples.
fig,ax=plt.subplots(figsize=(10.5,5.1))
x=np.arange(len(aix));w1=np.array([float(r['rate_v1']) for r in aix]);w2=np.array([float(r['rate_v2']) for r in aix]);
ax.plot(x,w1,marker='o',lw=2.4,color=BLUE,label='v1 predicted angular rate')
ax.plot(x,w2,marker='s',lw=2.4,color=ORANGE,label='v2 predicted angular rate')
ax.axhline(.026,ls='--',color=RED,label='Synthetic x-axis rate limit (0.026 rad/s)')
ax.set_xticks(x,[r['case_id'] for r in aix]);ax.set_xlabel('Selected actual MCP case IDs');ax.set_ylabel('Next x-axis rate (rad/s)');ax.grid(alpha=.15);ax.set_title('Wheel gyroscopic term changes the one-step attitude rate prediction',loc='left',fontweight='bold',fontsize=12)
ax.legend(frameon=False,fontsize=9);fig.tight_layout();save(fig,'05_selected_rate_forecasts')

# Desaturation actual 12 remote evaluations.
fig,(ax,bx)=plt.subplots(1,2,figsize=(11.8,4.9))
secs=np.array([int(r['time_s']) for r in profile]);h=np.array([float(r['momentum_next_Nms']) for r in profile]);margin=np.array([float(r['momentum_margin_Nms']) for r in profile])
ax.plot(np.r_[0,secs],np.r_[.039,h]*1000,color=CYAN,linewidth=2.7,marker='o');ax.axhline(41,ls='--',color=RED,label='Illustrative x-axis wheel capacity')
ax.set_xlabel('Elapsed time (s)');ax.set_ylabel('Stored wheel momentum (mN m s)');ax.grid(alpha=.13);ax.legend(frameon=False,fontsize=8)
ax.set_title('12 actual sequential MCP updates',fontweight='bold')
bx.plot(secs,margin*1000,color=ORANGE,marker='s',linewidth=2.4);bx.set_xlabel('Elapsed time (s)');bx.set_ylabel('Remaining momentum margin (mN m s)');bx.grid(alpha=.13);bx.set_title('Margin recovered under assumed external torque',fontweight='bold')
fig.suptitle('Illustrative one-axis unloading, not a magnetorquer allocation',x=.01,ha='left',fontweight='bold',fontsize=13);fig.tight_layout(rect=[0,0,1,.9]);save(fig,'06_desaturation_sequence')

# Quaternion normalization, genuine observed data.
fig,(ax,bx)=plt.subplots(1,2,figsize=(11.4,4.85))
idx=np.arange(1,13);pre=np.array([float(r['candidate_norm']) for r in quat]);post=np.array([math.sqrt(sum(float(r[f'next_q{k}'])**2 for k in range(4))) for r in quat]);
ax.plot(idx,pre,marker='o',color=BLUE,linewidth=2.3);ax.axhline(1,ls='--',color=GREY)
ax.set_xlabel('Quaternion input scenario');ax.set_ylabel('Unnormalized candidate norm');ax.set_title('First-order update without projection',fontweight='bold');ax.grid(alpha=.13)
bx.plot(idx,(post-1)*1e15,marker='o',color=TEAL,linewidth=1.9);bx.axhline(0,ls='--',color=GREY)
bx.set_xlabel('Quaternion input scenario');bx.set_ylabel('Returned unit-norm residual × 10¹⁵');bx.set_title('paceval-normalized quaternion',fontweight='bold');bx.grid(alpha=.13)
fig.suptitle('Twelve actually evaluated quaternion updates (not a time-propagated attitude trajectory)',x=.01,ha='left',fontweight='bold',fontsize=12.3);fig.tight_layout(rect=[0,0,1,.9]);save(fig,'07_quaternion_normalization')

# Pointwise interval evidence with distinct inconclusive/error types.
fig,(ax,bx)=plt.subplots(1,2,figsize=(11.5,4.9))
valid=[];uncert=[];errors=[]
for r in tinc:
 if int(r['error_number']):errors.append(r['case_id']);continue
 if r['lower']==r['upper']:uncert.append(r['case_id'])
 else:valid.append(r['case_id'])
labels=['Confirmed', 'Narrow text / inconclusive','Engine error 144'];counts=[7,3,2]
ax.bar(labels,counts,color=[TEAL,ORANGE,RED]);ax.set_ylabel('Point samples');ax.set_ylim(0,8);ax.set_title('Strict high-precision review of TINC text',fontweight='bold',fontsize=11);ax.tick_params(axis='x',labelrotation=15)
width=[];ids=[]
for r in tinc:
 if r['error_number']!='0':continue
 ids.append(r['case_id']);width.append(float(r['upper'])-float(r['lower']))
bx.bar(ids,width,color=BLUE);bx.tick_params(axis='x',labelrotation=45);bx.set_ylabel('Printed interval width (SI units)');bx.set_title('Returned intervals, fixed input points only',fontweight='bold',fontsize=11);bx.grid(axis='y',alpha=.13)
fig.suptitle('TINC results do not certify a full uncertain-input domain',x=.01,ha='left',fontweight='bold',fontsize=12);fig.tight_layout(rect=[0,0,1,.9]);save(fig,'08_tinc_case_outcomes')

# Version-specific predicted rate vs applied torque (actual eight x-sample results).
fig,ax=plt.subplots(figsize=(10.8,5.1))
for label,c,k in [('v1',BLUE,'rate_v1'),('v2',ORANGE,'rate_v2')]:
 # One unique rate per torque value: samples contain repeated x momentum levels.
 points={float(r['taux']):float(r[k]) for r in aix};xx=sorted(points)
 ax.plot(np.array(xx)*1000,[points[t] for t in xx],color=c,marker='o',linewidth=2.7,label=label)
ax.axhline(.026,linestyle=':',color=RED,label='Synthetic rate limit');ax.set_xlabel('Body control torque x (mN m)');ax.set_ylabel('Predicted rate x (rad/s)');ax.set_title('Coupled dynamics shifts the commanded-torque boundary',loc='left',fontweight='bold',pad=13)
ax.grid(alpha=.13);ax.legend(frameon=False);save(fig,'09_rate_coupling')

# 3D result surface, 49 real MCP grid values.
from mpl_toolkits.mplot3d import Axes3D
XX,YY=np.meshgrid(TX,HX);ZZ=s2
fig=plt.figure(figsize=(10.8,6.0));ax=fig.add_subplot(111,projection='3d')
surf=ax.plot_surface(XX,YY,ZZ,cmap='coolwarm',linewidth=.3,edgecolor='#4b6678',alpha=.95)
ax.set_xlabel('x torque (mN m)',labelpad=9);ax.set_ylabel('Initial x momentum (mN m s)',labelpad=10);ax.set_zlabel('Normalized joint score',labelpad=7)
ax.set_title('Three-axis v2 envelope: 49 actual paceval aggregate outputs',fontweight='bold',pad=20);ax.view_init(elev=25,azim=-57);fig.colorbar(surf,ax=ax,shrink=.57,pad=.12,label='Joint score');save(fig,'10_joint_score_3d')

# Limits plot of real aggregate data.
fig,ax=plt.subplots(figsize=(10.9,5.1))
for j,hx in enumerate(HX):
 rr=grid[7*j:7*(j+1)];xx=TX
 ax.plot(xx,[float(z['joint_score_v2']) for z in rr],linewidth=2,marker='o',label=f'{hx:.0f} mN m s')
ax.axhline(0,ls='--',color=RED);ax.set_xlabel('Body x torque (mN m)');ax.set_ylabel('Version 2 normalized joint margin')
ax.set_title('Momentum-dependent constraint activation in the actual v2 grid',fontweight='bold',pad=12)
ax.legend(frameon=False,ncol=2,fontsize=8);ax.grid(alpha=.12);save(fig,'11_momentum_torque_envelope')

# Page styling and body framework.
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',FONT));pdfmetrics.registerFont(TTFont('DejaVuBold',BOLD))
S=getSampleStyleSheet()
S.add(ParagraphStyle(name='WTitle',fontName='DejaVuBold',fontSize=22,leading=29,textColor=HexColor(INK),spaceAfter=12))
S.add(ParagraphStyle(name='WSub',fontName='DejaVu',fontSize=10.3,leading=16,textColor=HexColor('#46657a'),spaceAfter=14))
S.add(ParagraphStyle(name='WHead',fontName='DejaVuBold',fontSize=15,leading=20,textColor=HexColor(INK),spaceAfter=12,spaceBefore=3))
S.add(ParagraphStyle(name='WBody',fontName='DejaVu',fontSize=9.35,leading=15.4,textColor=HexColor('#253b4c'),spaceAfter=10))
S.add(ParagraphStyle(name='WCaption',fontName='DejaVu',fontSize=8,leading=12.5,textColor=HexColor('#617a8b'),spaceBefore=6,spaceAfter=7))
S.add(ParagraphStyle(name='WEqn',fontName='DejaVuBold',fontSize=9.6,leading=15,textColor=HexColor('#0877a1'),spaceBefore=6,spaceAfter=12))
S.add(ParagraphStyle(name='WSmall',fontName='DejaVu',fontSize=8.1,leading=13,textColor=HexColor('#607483'),spaceAfter=9))

def par(t,sty='WBody'):
    # HTML escaped user-provided sources have already been authored; formulas shown as clean Unicode/plain text.
    return Paragraph(t,S[sty])

def img(name,w=160):
    from PIL import Image
    fp=FIG/name
    with Image.open(fp) as x:ww,hh=x.size
    return RImage(str(fp),width=w*mm,height=w*mm*hh/ww)

def figblock(name,caption,w=163):return [img(name,w),par(caption,'WCaption')]

pages=[]
def page(title,paras,figure=None,caption='',w=163):
    p=[par(title,'WHead')]
    for t in paras:
        if isinstance(t,tuple):p.append(par(*t))
        else:p.append(par(t))
    if figure:p.extend(figblock(figure,caption,w))
    pages.append(p)

pages.append([
 Spacer(1,8*mm),par('SATELLITE ATTITUDE<br/>ACTUATOR TORQUE &amp;<br/>MOMENTUM ENVELOPES','WTitle'),
 par('Research WP 32 | Actual paceval MCP 4.26 mathematical execution | 15 November 2026','WSub'),
 img('00_Satellite_Attitude_Cinematic_Cover.png',166),Spacer(1,12*mm),
 par('<b>Scientific aim.</b> Evaluate versioned three-axis spacecraft rate predictions and wheel torque/momentum feasibility using reusable paceval graphs, explicit physical assumptions and independently checked inputs.'),
 par('<b>Observed execution.</b> 43 unique mathematical graphs. 4,922 main stage and sequential profile graph-point evaluations. 49 candidate three-axis snapshots, 12 quaternion samples and a 12-step unloading illustration.'),
 par('Status: reproducible synthetic mathematics demonstrator. Not a flight-qualified controller, pointing-accuracy validation, certified momentum limit, or actual hardware performance benchmark.','WSmall')])

page('Executive summary and research result',[
 'An attitude-control system must move a satellite accurately while preventing its reaction wheels from reaching command torque, wheel momentum or body angular-rate limits. This reproducible example uses three ideal orthogonal reaction wheels, positive diagonal body inertias and synthetically chosen disturbances to make this question mathematically transparent.',
 'Two versions of the dynamical model are simultaneously available as persistent formula handles. Version 1 includes the body inertial cross-product; version 2 also includes the cross-coupling between body rates and stored wheel momentum. Each version produces a one-step predicted body rate, normalized margins and a Boolean screen.',
 '<b>Real engine results:</b> 20 of 49 scenarios satisfied all defined version-1 margins, compared with 15 for version 2; five status decisions differ. These are observations from an actual paceval MCP 4.26 execution, not numbers inferred from simulated software behavior.',
 'The accompanying original-SDK C++ source includes the complete mathematical registration, input validation and batch orchestrator. Its C++17 syntax passes; local linking and runtime execution are not claimed because no matching shared library is available.'
], '01_execution_architecture.png','Figure 1. Graph ownership: paceval evaluates the physical formulas; the host handles inputs, stages, reference comparison and reporting.')

page('1. Operational problem: attitude and wheel saturation',[
 'Small satellites routinely use three-axis reaction-wheel actuators for precision pointing. Reaction wheel momentum is finite and ultimately must be unloaded when disturbances and repeated commands accumulate excessive wheel speed. This is a physical envelope problem, not simply a geometric attitude-angle problem.',
 'The NASA Small Spacecraft Technology State of the Art 2026 review describes reaction-wheel sizing, torque and stored-momentum requirements, gyro disturbances and momentum desaturation using external actuators. Those observations motivate the variables and boundaries chosen in this reduced mathematical experiment.',
 'This study investigates a feasible pre-screen rather than a complete attitude determination and control system. It does not estimate sensor errors, track stars, solve wheel allocation for skewed axes, optimize a feedback controller or provide flight-proven hardware commands.',
 'The key industrial opportunity for paceval is programmable and repeatable evaluation of many explicit mathematical constraint functions while preserving the exact model version and the calculation provenance.'
],'02_joint_feasibility_comparison.png','Figure 2. The actual 49-point paceval constraint screens for v1 and v2. Green cells satisfy all hypothetical one-step torque, momentum and rate boundaries.')

page('2. Three-axis dynamics and sign convention',[
 'All rates and moments are expressed in a body-fixed orthogonal x/y/z frame. I = diag(Ix,Iy,Iz) is positive and constant. The body-frame momentum is H = I·omega + h_w, where h_w is the signed wheel axial momentum summed by aligned axes.',
 'The commanded variable tau_rw is the torque exerted on the spacecraft body by the wheels, while wheel momentum changes with hdot_w = −tau_rw. External torque is added to the body equation, not to wheel momentum directly.',
 ('I·omega_dot = tau_rw + tau_ext − omega × (I·omega + h_w).','WEqn'),
 'Model v1 neglects the last wheel-gyro part omega × h_w, but retains omega × I omega. Model v2 includes both. The distinction is strictly about these explicit reduced-order equations, not a high-fidelity wheel actuator simulation.',
 'When all external torques vanish, total inertial angular momentum is conserved continuously by this equation; a numerical one-step integrator only approximates that invariant. The independent audit includes the corresponding residual identity.'
],'09_rate_coupling.png','Figure 3. Actual sampled paceval x-axis rate outputs exhibit a shifted rate-limit crossing due to wheel gyro coupling.')

page('3. One-step actuator and rate envelopes',[
 'The discrete screening update is omega_next = omega + dt × omega_dot and h_next = h − tau_rw × dt. Each row is supplied with positive limits on torque, wheel angular momentum and body angular rate. No formula is evaluated on invalid physical or nonfinite inputs.',
 'Axis margins are M_torque = tau_max − |tau_rw|, M_momentum = h_max − |h_next| and M_rate = omega_max − |omega_next|. An axis guard is true only if all three margins are nonnegative.',
 'The dimensionless per-axis score is the minimum of M_torque / tau_max, M_momentum / h_max and M_rate / omega_max; the three-axis score is the minimum among the axis scores. This avoids comparing unlike physical units.',
 'The host groups the actual paceval axis-stage outputs into three-axis inputs. Eight further paceval graphs calculate joint scores, Boolean guards, selected raw SI margins and whether a candidate changes status between model versions. The C++ host does not replace these comparisons with hidden native logic.'
],'03_joint_score_heatmap.png','Figure 4. Actual normalized three-axis scores, side by side, for identical synthetic candidate inputs.')

page('4. Synthetic satellite inputs and parameter domain',[
 'The illustrative diagonal inertias are 0.085, 0.105 and 0.075 kg m². Initial body rates are (0.023, −0.015, 0.017) rad/s. Fixed y/z wheel momentum is −0.018 and +0.026 N m s. The x-axis sweep varies initial wheel momentum from +0.015 to +0.039 N m s and commanded torque from −0.0009 to +0.0009 N m.',
 'The forecast time step is 1.8 s. The x-axis wheel momentum limit is 0.034 N m s, and its body-rate limit is 0.026 rad/s; the other axes have their own declared positive limits. These numbers are chosen as synthetic test parameters, not as vendor-qualified performance characteristics.',
 'The host enforces strict positivity of inertia, actuator capacities and step duration. Values near zero are important for actual studies because small denominators or exact capacity boundaries can magnify numerical uncertainty or Boolean classification sensitivity.',
 'The full 147 axis rows are published as a literal-only CSV with explicit columns, original input decimals and unchanged ordering. The formula registry records all variables, expression strings and output units.'
],'04_model_decision_changes.png','Figure 5. The five model-specific decision changes lie at a rate prediction boundary. The right plot displays remote scores for the complete 49-case grid.')

page('5. Results: coupling changes eligible maneuver commands',[
 'The actual remote MCP evaluation covered 30 distinct axis formulas across 147 axis input vectors, producing 4,410 graph-point results without reported errors. Eight aggregate graphs operated on 49 grouped three-axis vectors, producing 392 more results without reported errors.',
 'Under the declared mathematical margins, 20 candidate snapshots qualify using the simplified v1 dynamics and 15 qualify using the wheel-coupled v2 dynamics. Five candidates change from eligible to ineligible because the additional wheel gyroscopic cross-product shifts the predicted body angular rate just outside the chosen rate cap.',
 'At a representative x-axis zero-torque candidate, the actual v1 predicted rate was 0.02474388 rad/s while v2 returned 0.02652271 rad/s; the synthetic x-axis upper rate limit is 0.026 rad/s. This is an algebraic screening difference, not a measured satellite attitude error.',
 'In realistic use, the model selection should follow a validated attitude dynamics specification. The same real graph handles remain accessible for side-by-side model evaluation and sensitivity analysis.'
],'10_joint_score_3d.png','Figure 6. Three-dimensional view of 49 actually recorded version-2 paceval normalized joint scores.')

page('6. Torque and momentum constraint activation',[
 'A reaction-wheel command must remain within both instantaneous motor torque and remaining angular-momentum storage. A torque that is permissible now may make the next wheel momentum exceed the capacity even if the predicted body rate remains acceptable.',
 'The project separately calculates signed torque, momentum and rate margins on every axis, together with normalized utilization, a mechanical wheel power proxy and the sensitivity of predicted body acceleration to commanded torque.',
 'For the selected x-axis model, the torque limit is 0.0009 N m and stored momentum cap is 0.034 N m s. In the recorded grid, high initial momentum cases become ineligible independently of the wheel coupling. This creates two distinct limiting factors across the operating envelope.',
 'Mechanical power is represented only by the arithmetic proxy |tau × (h/Jw)|. Actual electrical power would require motor constants, driver efficiency, friction and wheel speed models, none of which is supplied by the project.'
],'11_momentum_torque_envelope.png','Figure 7. Actual v2 paceval dimensionless joint margin across torque and the seven initial x-axis wheel momentum levels.')

page('7. Quaternion state update',[
 'For a scalar-first quaternion q = (q0,q1,q2,q3) representing body-to-inertial attitude, the selected Hamilton sign convention gives qdot = 0.5 × q ⊗ (0,omega). Each of the four scalar derivative equations is embedded in a paceval normalization graph.',
 'The discretized candidate is qtilde = q + dt × qdot. Four persistent paceval graphs compute q_next = qtilde / ||qtilde||; a fifth calculates the candidate norm, all on the same declared variable list.',
 'Twelve newly constructed quaternion cases were actually run through these five graphs, producing 60 successful remote graph-point evaluations. Independent 90-decimal-digit calculations reproduce all archived output components and confirm the normalized quaternion length.',
 'The twelve cases are a parametric snapshot test, not sequential propagation. A real flight implementation should use accurate rotational propagation, reference-frame reconciliation, stable normalization and pointing-error validation.'
],'07_quaternion_normalization.png','Figure 8. Actual candidate quaternion norms and the independently derived normalized-norm residual for twelve observed paceval outputs.')

page('8. Momentum desaturation: a narrow illustrative maneuver',[
 'The extra test profile examines an intentionally simple one-axis unloading case. The spacecraft has zero angular rate on all axes; an assumed accessible external body torque of −0.00015 N m is balanced by wheel body torque +0.00015 N m. There is no gyroscopic cross-term at zero body rate.',
 'Twelve sequential remote paceval steps of 10 s each reused five already created axis graphs, generating 60 further results without reported errors. The wheel momentum decreased from 0.039 to 0.021 N m s while the computed body acceleration remained zero. The momentum margin increased accordingly.',
 'The external countertorque is an input assumption, not the output of a magnetic-torquer model. For magnetic control the achievable torque direction is limited by the local geomagnetic field, and wheel unloading can be constrained by orbit, power and pointing requirements.',
 'The demonstration therefore verifies mathematical state handoff and momentum change sign conventions only. It is not a completed magnetic momentum-management control algorithm.'
],'06_desaturation_sequence.png','Figure 9. Actually executed sequential remote paceval wheel momentum and remaining margin over twelve assumed unloading steps.')

page('9. Sensitivities and model extension',[
 'Instead of claiming automatic differentiation, the study registers explicitly derived sensitivities as independent paceval graphs. For both versions, d(omega_dot)/d(tau_rw) = 1/I and d(h_next)/d(tau_rw) = −dt. Under the coupled version, the acceleration derivatives with respect to transverse wheel momentum are d(omega_dot_i)/d(h_j) = omega_k / I_i and d(omega_dot_i)/d(h_k) = −omega_j / I_i, using cyclic body indices.',
 'The graph inventory additionally includes angular momentum residual checks, wheel speed, torque utilization, the model version delta and a weighted cost function combining normalized torque, wheel momentum and acceleration error.',
 'These expressions demonstrate that a programmable mathematical graph can hold not only one physics equation but also a consistent collection of compound constraints and explicit sensitivity functions. Physical usefulness remains dependent on the underlying model fidelity.'
],'05_selected_rate_forecasts.png','Figure 10. Selected actually recorded paceval x-axis angular rates for the two dynamics formulations.')

page('10. TINC pointwise precision evidence',[
 'Two additional interval-enabled paceval graphs were executed for the wheel momentum margin and the coupled x-axis rate margin at six selected inputs. This provided twelve TINC point outcomes in total.',
 'Of the twelve, seven returned decimal lower/upper bounds that strictly contained the independent 90-digit point reference; three returned decimal endpoint strings too narrow to establish strict inclusion of the decimal-reconstructed input; two generated remote paceval error number 144. These cases are preserved as explicitly unresolved.',
 'A separate attempt to rewrite the positive-rate branch without an absolute-value operator still generated error 144 for the same two samples. This is a technical input/precision limitation needing further local SDK investigation, not evidence that any proposed satellite maneuver is safe.',
 'Pointwise TINC on fixed inputs is fundamentally different from certified interval propagation over a box of uncertain inertia, torque, rate or momentum parameters. The study does not claim the latter.'
],'08_tinc_case_outcomes.png','Figure 11. Audited TINC status and displayed interval widths. Inconclusive and error-144 cases are explicitly separated from confirmed pointwise inclusions.')

page('11. Independent numerical verification',[
 'The observed remote values were transcribed and compared with a separate model using 90 decimal digits of mpmath precision. The audit covers 343 aggregate outputs, 96 selected axis outputs, 60 quaternion graph values, 12 quaternion unit norms, 72 sequential momentum-profile values and two dynamic invariants.',
 'All 585 regular comparisons pass their prespecified absolute and relative numerical criteria. The TINC uncertainty categories are reported separately because a successful ordinary point evaluation does not resolve an interval-boundary issue.',
 'The check program independently reconstructs the Euler rigid-body and wheel equations instead of calling the paceval graph definitions or reusing graph output arrays as expected values. Invalid input, nonfinite numeric strings, zero inertia and actuator-limit domains are also explicitly covered by the C++ validation contract.',
 'No full remote protocol dump was saved for the 4,410-value axis batch. Selected actual axis outputs and all 49 actual aggregate rows are archived separately from independently generated reference CSVs. This provenance limitation is disclosed for reproducibility.'
],'01_execution_architecture.png','Figure 12. Independent reference calculations are never used in place of real paceval graph execution.')

page('12. Software execution architecture',[
 'The deliverable includes complete C++17 source, original unchanged paceval_main.h and paceval_main.cpp files, CMake configuration, all registered formulas as generated headers, input CSVs, actual remote result transcriptions, numerical check scripts and plot/PDF generation code.',
 'The local C++ application is designed to reject expression-like CSV input before calling the original paceval string-to-float converter, register persistent graph handles for both model versions, execute suitable independent input rows with the official multiple-graph batch routine, and use the official float-to-string converter for CSV outputs.',
 'The host hands axis graph outputs to separate aggregate graph inputs, processes the quaternion submodel and sequences the one-axis momentum example. An independent native check tests physical formulas and Boolean results; the local operator test verifies the semantics of negative remainder, mathematical modulo, relational conjunctions, min/max, NOT/OR and XOR.',
 '<b>Critical evidence boundary:</b> C++17 syntax checks were actually performed and passed. No compatible libpaceval.so was present; local binary linking, execution and CTest are not reported as completed. Likewise, no CPU, GPU, FPGA, throughput, energy or speedup benchmark is asserted.'
])

page('13. Physical interpretation, future experiments and limitations',[
 'This demonstrator is deliberately a mathematical first-step feasibility screen, not a reaction wheel flight controller. It assumes fixed diagonal inertias, orthogonal independent wheels, ideal torque and momentum sensing, algebraic saturation limits, simple external disturbance inputs and forward-Euler forecast states.',
 'A credible industrial pilot should obtain wheel inertia, torque-speed and momentum limits from actual vendor documentation, model wheel friction and cross-coupling, apply realistic disturbance torques, and validate against a full dynamics reference such as Basilisk. A general four-wheel skewed configuration needs a separate allocation matrix and pseudoinverse/saturation treatment.',
 'Further necessary steps include accurate numerical attitude integration, magnetic torque direction allocation, wheel desaturation scheduling, input uncertainty bounds, star tracker and gyro error models, closed-loop robustness testing and hardware-in-the-loop tests. Certification and flight use require their own independent process.',
 'The substantive positive conclusion is limited: paceval MCP 4.26 actually executed a versioned body/wheel mathematical envelope, reproduced 49 complete three-axis screening results, 12 quaternion cases and an idealized unloading sequence, with independent numerical checks. Performance and spacecraft correctness are separate, unmeasured questions.'
])

page('14. Research sources and traceability',[
 '<b>[1] NASA Small Spacecraft Systems Virtual Institute, State-of-the-Art Small Spacecraft Technology, Guidance, Navigation, and Control, May 2026.</b><br/><font color="#16779a">https://www.nasa.gov/smallsat-institute/sst-soa/guidance-navigation-and-control/</font>',
 '<b>[2] NASA, Small Spacecraft Technology 2026 report landing page.</b><br/><font color="#16779a">https://www.nasa.gov/smallsat-institute/sst-soa/</font>',
 '<b>[3] Basilisk documentation, spacecraft dynamics module.</b><br/><font color="#16779a">https://avslab.github.io/basilisk/Documentation/simulation/dynamics/spacecraft/spacecraft.html</font>',
 '<b>[4] Basilisk documentation, reactionWheelStateEffector.</b><br/><font color="#16779a">https://avslab.github.io/basilisk/Documentation/simulation/dynamics/reactionWheels/reactionWheelStateEffector.html</font>',
 '<b>[5] Suboptimal attitude control of nadir-pointing satellites using magnetic torquers and reduced reaction wheels.</b> Control Engineering Practice, July 2026, Article 106892. <font color="#16779a">https://www.sciencedirect.com/science/article/pii/S096706612600136X</font>',
 '<b>[6] paceval API and developer documentation.</b> <font color="#16779a">https://paceval.com/developers/</font>',
 '<b>[7] WP 32 original proposal, 13 November 2026.</b> Included in this repository under docs/Original_WP32_Proposal_2026-11-13.pdf.',
 'The references frame the physical model and its limitations. They do not certify the new synthetic paceval results. Technical reproduction status: 15 November 2026.'
])

class Footer:
 def __call__(self,canvas,doc):
  canvas.saveState();w,h=A4
  canvas.setStrokeColor(HexColor('#bfcbd3'));canvas.line(21*mm,19*mm,w-21*mm,19*mm)
  canvas.setFont('DejaVu',7.3);canvas.setFillColor(HexColor('#627989'))
  canvas.drawString(21*mm,12.5*mm,'PACEVAL  |  WP 32  |  Mathematical Satellite Attitude Research')
  canvas.drawRightString(w-21*mm,12.5*mm,f'Page {doc.page}')
  canvas.restoreState()

output=ROOT/'paceval_Satellite_Attitude_Actuator_Whitepaper_EN.pdf'
doc=SimpleDocTemplate(str(output),pagesize=A4,leftMargin=21*mm,rightMargin=21*mm,topMargin=20*mm,bottomMargin=23*mm,
 title='Satellite Attitude Actuator Torque and Momentum Envelopes with paceval',author='paceval research demonstrator',subject='WP32 mathematical research report')
story=[]
for i,p in enumerate(pages):
 if i:story.append(PageBreak())
 story.extend(p)
doc.build(story,onFirstPage=Footer(),onLaterPages=Footer())
print('Figures:',len(list(FIG.glob('*.png')))-1,'PDF intended pages:',len(pages),'written:',output)
