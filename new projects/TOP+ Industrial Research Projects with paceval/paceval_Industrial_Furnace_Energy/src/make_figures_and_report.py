from pathlib import Path
import csv,json,math,os,re,hashlib,shutil,textwrap
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RImage, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

R=Path(__file__).resolve().parents[1];O=R/'results';G=R/'figures';SOURCE=R/'docs'
rows=list(csv.DictReader((O/'mcp_observed_grid_transcription.csv').open()));snap=list(csv.DictReader((O/'mcp_observed_snapshots.csv').open()));tinc=list(csv.DictReader((O/'mcp_tinc_observed.csv').open()));ref=json.loads((O/'high_precision_validation.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.labelcolor':'#193449','xtick.color':'#526b78','ytick.color':'#526b78'})
TEAL='#1d798c';ORANGE='#d77b37';INK='#123247';GREY='#6d8796';RED='#b94f5c';DARK='#16344c'

def save(fig,name):
 fig.savefig(G/(name+'.png'),dpi=205,bbox_inches='tight',facecolor='white')
 fig.savefig(G/(name+'.pdf'),bbox_inches='tight',facecolor='white')
 plt.close(fig)

# 1 Sankey-like explicit energy bars for actual MCP case F025.
f25=rows[24]; fuel=.04*45e6*.87; qload=864198.16; conv=47430;rad=float(f25['Qrad_W']);exnet=558600-195510;left=float(f25['margin_v2_W'])
fig,ax=plt.subplots(figsize=(11.5,4.5));ax.set_xlim(0,1.65);ax.set_ylim(-.15,1.6)
col=[('#235a72',qload/1e6,'Product heat'),('#39899a',conv/1e6,'Wall convection'),('#ecbb79',rad/1e6,'Wall radiation'),('#b46c46',exnet/1e6,'Net exhaust'),('#8a9ca5',left/1e6,'Unallocated margin')]
y=1.12;ax.barh(y,fuel/1e6,color='#183b51',height=.27);ax.text(fuel/2e6,y,'Fuel heat 1.566 MW',color='white',ha='center',va='center',fontweight='bold');start=0
for color,amount,label in col:
 ax.barh(.47,amount,left=start,color=color,height=.27)
 ax.annotate(label,(start+amount/2,.22),ha='center',fontsize=8,rotation=0)
 start+=amount
ax.set_title('Example F025 — where the supplied chemical energy goes',loc='left',fontweight='bold',pad=16)
ax.set_xlabel('Thermal power (MW)');ax.set_yticks([]);ax.set_xticks(np.arange(0,1.66,.2));ax.grid(axis='x',alpha=.12);save(fig,'01_furnace_energy_distribution')

# 2 and 3 constraint model outputs
for j,key in enumerate(['guard_v1','guard_v2']):
 mat=np.array([int(r[key]) for r in rows]).reshape(7,7)
 fig,ax=plt.subplots(figsize=(7.5,5.6))
 ax.imshow(mat,aspect='auto',cmap=ListedColormap(['#edd9d3','#2c937d']),vmin=0,vmax=1,origin='lower')
 for y in range(7):
  for x in range(7):ax.text(x,y,'PASS' if mat[y,x] else 'FAIL',color='#14384a' if mat[y,x] else '#8b3d42',ha='center',va='center',fontsize=9,fontweight='bold')
 ax.set_xticks(range(7),labels=['25','30','35','40','45','50','55']);ax.set_yticks(range(7),labels=['350','360','370','380','390','400','410'])
 ax.set_xlabel('Fuel flow (g/s)');ax.set_ylabel('External wall-skin temperature (K)');ax.set_title('Mathematical screening: '+('baseline v1' if j==0 else 'recuperation v2'),loc='left',fontweight='bold',pad=14)
 save(fig,'02_feasible_map_v1' if j==0 else '03_feasible_map_v2')

# 4 energy margins across wall temp and flow
fig,ax=plt.subplots(figsize=(10.5,5.5));flows=np.array([.025,.03,.035,.04,.045,.05,.055]);
for t,color in [(350,'#298f9a'),(380,'#c47a40'),(410,'#354d83')]:
 rr=[r for r in rows if int(r['Tw'])==t]; ax.plot(flows*1000,np.array([float(r['margin_v1_W']) for r in rr])/1000,linestyle='--',linewidth=1.8,color=color,alpha=.7)
 ax.plot(flows*1000,np.array([float(r['margin_v2_W']) for r in rr])/1000,marker='o',linewidth=2.5,color=color,label=f'Wall {t} K, v2')
ax.axhline(0,color='#8c5151',linestyle=':',linewidth=1.4);ax.set_xlabel('Fuel flow (g/s)');ax.set_ylabel('Heat-balance surplus / deficit (kW)');ax.set_title('Real paceval thermal margins: baseline (dashed) vs recovery (solid)',loc='left',fontweight='bold',pad=14)
ax.grid(alpha=.12);ax.legend(frameon=False,ncol=3,loc='upper left',fontsize=9);save(fig,'04_heat_balance_margins')

# 5 emissions screens: separate axes because NOx varies with wall scenario and CO2 with fuel.
fig,(ax,b)=plt.subplots(1,2,figsize=(11.8,4.9))
f=np.array([.025,.03,.035,.04,.045,.05,.055])*1000
co2=f/1000*2.75
ax.plot(f,co2,marker='o',color=RED,linewidth=2.5,label='Synthetic fuel-specific factor')
ax.axhline(.13,color=RED,linestyle='--',label='Hypothetical CO2 limit')
ax.set_ylabel('CO2 rate (kg/s)');ax.set_xlabel('Fuel flow (g/s)')
ax.set_title('CO2 factor calculation',fontweight='bold',fontsize=11);ax.grid(alpha=.14)
ax.legend(frameon=False,fontsize=8,loc='upper left')
Tw=[350,360,370,380,390,400,410]
nw=np.array([90,100,110,120,130,140,150])*2.25*1e-6
b.plot(Tw,nw,color=TEAL,marker='s',linewidth=2.5,label='Synthetic, externally supplied NOx data')
b.axhline(.00034,color=TEAL,linestyle='--',label='Hypothetical NOx limit')
b.set_ylabel('NOx rate (kg/s)');b.set_xlabel('External wall-skin scenario (K)')
b.set_title('NOx input screening (not predicted)',fontweight='bold',fontsize=11)
b.grid(alpha=.14);b.legend(frameon=False,loc='upper left',fontsize=8)
fig.suptitle('Different input variables and measurement bases: no inferred NOx temperature law',fontweight='bold',x=.01,ha='left',fontsize=12)
fig.tight_layout(rect=[0,0,1,.9]);save(fig,'05_emission_constraints')

# 6 actual MCP snapshot lines
fig,ax=plt.subplots(figsize=(10.5,5.7));
for rec in [0,.35,.65]:
 rr=[x for x in snap if float(x['rec'])==rec];r2=np.array([float(x['margin_v2_W']) for x in rr])/1000
 ax.plot(np.array([float(x['mf']) for x in rr])*1000,r2,marker='o',linewidth=2.4,label=f'Recovery {rec*100:.0f}%')
ax.axhline(0,color=RED,linestyle='--');ax.set_xlabel('Fuel flow (g/s)');ax.set_ylabel('v2 balance margin (kW)');ax.set_title('Twelve actually executed MCP recovery scenarios',loc='left',fontweight='bold',pad=14)
ax.legend(frameon=False);ax.grid(alpha=.13);save(fig,'06_recovery_sensitivity')

# 7 sensitivity chart projected independent closed form matching paceval graph on all scenarios
fig,ax=plt.subplots(figsize=(10,5.1))
S=[350,360,370,380,390,400,410];w=[(float(x['Tw'])-295) for x in rows[::7]]
ss=[4*.78*5.670374419e-8*62*t**3 for t in S];ax.plot(S,ss,color=ORANGE,linewidth=2.7,marker='o')
ax.set_title('Analytically derived paceval graph: radiation sensitivity to wall-skin temperature',loc='left',fontweight='bold',pad=14)
ax.set_xlabel('External wall-skin temperature (K)');ax.set_ylabel('dQradiation / dTskin (W/K)');ax.grid(alpha=.15);save(fig,'07_radiation_temperature_sensitivity')

# 8 TINC results widths from actual service bounds
fig,ax=plt.subplots(figsize=(10,5.0));pos=np.arange(6)
width1=[float(x['balance_v2_upper_W'])-float(x['balance_v2_lower_W']) for x in tinc]
width2=[float(x['radiation_upper_W'])-float(x['radiation_lower_W']) for x in tinc]
ax.bar(pos-.18,np.array(width1)*1e6,width=.35,color=TEAL,label='Balance margin v2');ax.bar(pos+.18,np.array(width2)*1e6,width=.35,color=ORANGE,label='Wall radiation')
ax.set_xticks(pos,[x['case_id'] for x in tinc]);ax.set_ylabel('Returned interval width (micro-W, 10^-6 W)');ax.set_title('Actual paceval TINC point interval widths (not global parameter intervals)',loc='left',fontweight='bold',pad=12)
ax.legend(frameon=False);ax.grid(axis='y',alpha=.15);save(fig,'08_tinc_point_widths')

# 9 transparent model diagram
fig,ax=plt.subplots(figsize=(11,4.7));ax.set_xlim(0,10);ax.set_ylim(0,4);ax.axis('off')
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
boxes=[(0.1,1.45,2.3,1.2,'Inputs / provenance\n61 synthetic points','#d7eaee'),(3,2.35,3,1.1,'32 persistent paceval graphs\nthermochemistry and emissions','#b6d9db'),(3,.55,3,1.1,'Independent mpmath model\n90-digit reference','#f2dfca'),(7,1.45,2.8,1.2,'Audited outputs\nCSV, figures, decisions','#dbe5ee')]
for x,y,w,h,t,col in boxes:
 box=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.13,rounding_size=.13',facecolor=col,edgecolor='#8a9fa9',lw=1.2);ax.add_patch(box);ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=11,fontweight='bold',color=DARK)
for x1,y1,x2,y2 in [(2.4,2.04,2.95,2.75),(2.4,2.04,2.95,1.1),(6.05,2.75,6.95,2.07),(6.05,1.1,6.95,2.02)]:ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=19,color=TEAL,lw=2))
ax.set_title('Execution ownership and independent validation',loc='left',fontweight='bold',pad=18);save(fig,'09_execution_architecture')

# README and supporting docs use GitHub dollar math, no raw TeX \( delimiters.
README='''# Industrial Furnace Energy Balance and Emission Constraint Maps with paceval

**WP 30 | Mathematical Engineering Research Demonstrator | 15 November 2026**

![Industrial furnace energy model](figures/00_industrial_furnace_hero.png)

An industrial furnace converts chemical energy into useful heat while losing energy through the exhaust, wall convection and surface radiation. For a steel reheating or heat-treatment line, engineers must repeatedly test combinations of fuel flow, load, external wall temperature, waste-heat recovery and emissions-related limits. This repository demonstrates **programmable, persistent paceval computation graphs** for a reproducible mathematical screening workflow; it is not a furnace safety controller, an emissions-compliance service or a combustion-CFD model.

The project was expanded from the four mathematical kernels in the [original WP 30 proposal](docs/Original_WP30_Proposal_2026-11-13.pdf). Its complementary research method follows the US Department of Energy's [MEASUR](https://www.energy.gov/cmei/ito/measur) / [Process Heating Systems](https://www.energy.gov/cmei/ito/process-heating-systems) methodology, while retaining substantially smaller, fully disclosed equations. ISO 13577-2:2023 concerns safety of furnace combustion systems; **this software does not demonstrate conformity**.

## What the demonstrator computes

A synthetic example represents a furnace heating a stream of material. The operator supplies fuel and material flow, temperatures, wall area and emissivity, exhaust-flow properties, an optional recovery fraction, and carbon/NOx screening inputs. The same input vector is evaluated by two independent model versions using reusable paceval graph handles.

* **Version 1:** constant effective product heat capacity with unrecovered stack heat.
* **Version 2:** linearly temperature-dependent product heat capacity and a hypothetical exhaust heat-recovery fraction.
* **Both versions:** consistent fuel input, external wall convection, thermal radiation, source-heat margin, carbon-factor mass rate, NOx rate based on supplied concentration and dry-normal volume flow, guard decisions and sensitivities.

### Thermal model (SI units)

The first model follows the proposal:

$$
Q_{fuel}=\\dot m_f LHV\\,\\eta_b,\\qquad Q_{load,1}=\\dot m_p c_{p0}(T_{out}-T_{in})
$$

$$
Q_{conv}=h_c A(T_w-T_a),\\qquad Q_{rad}=\\varepsilon\\sigma A(T_w^4-T_a^4)
$$

Temperatures **must be in kelvin** in the radiation calculation; $h_c$ describes external wall convection only and is not a combined overall heat-transfer coefficient. $\\eta_b$ is defined here as the fraction of fuel chemical power released into the chosen furnace control volume **before** the explicitly modeled wall/stack losses; otherwise double counting would result.

The revised model adds an exhaust recovery fraction and a linearized heat-capacity assumption:

$$
Q_{ex,net}=(1-\\rho_r)\\dot m_{ex} c_{p,ex}(T_{ex}-T_a)
$$

$$
Q_{load,2}=\\dot m_p c_{p0}\\left[\\Delta T+\\frac{\\beta}{2}(\\Delta T)^2\\right]
$$

The net balances are $M_1=Q_{fuel}-Q_{load,1}-Q_{conv}-Q_{rad}-Q_{ex,gross}$ and $M_2=Q_{fuel}-Q_{load,2}-Q_{conv}-Q_{rad}-Q_{ex,net}$. Positive $M$ denotes model-calculated heat surplus; it **does not establish energy-balance closure** unless further sinks, storage, or operating adjustments are accounted for.

### Emission-related screening

Carbon mass rate is $\\dot m_{CO_2}=\\dot m_f e_{CO_2}$, with a supplied fuel-specific factor. NOx mass rate is calculated only from the **provided** concentration and a **consistent** normalized exhaust volumetric rate:

$$
\\dot m_{NO_x}=C_{NO_x,mg/Nm^3}\\,\\dot V_{dry,Nm^3/s}\\,10^{-6}
$$

NOx concentrations require independently determined correction/reference-oxygen, wet/dry and reference-temperature conventions before real compliance use. The illustrative caps are **synthetic user-defined constraints, not legal thresholds**. No temperature-based NOx forecast is asserted.

### Compound decisions and sensitivities

The two guard graphs test five independent inequalities: nonnegative thermal margin, CO2 and NOx mass-rate margins, fuel-flow capacity and upper process temperature. All are evaluated by the actual paceval engine, **not** replaced by native C++ decisions. The dimensionless score is the minimum of the five appropriately normalized margins. Separate persistent graphs calculate sensitivities such as $\\partial M_2/\\partial\\rho_r=Q_{ex,gross}$ and $\\partial Q_{rad}/\\partial T_w=4\\varepsilon\\sigma AT_w^3$.

## Actual paceval results

The connected **paceval MCP 4.26 service** actually created and evaluated **32 different model graphs over 49 grid scenarios plus 12 recovery cases**: 1,952 main graph-point evaluations, with zero reported errors. Six further cases were evaluated using two interval-enabled graphs (12 TINC results) and seven operator graphs were tested for three scenarios each (21 operator evaluations). These are **remote MCP evaluations**, not a benchmark of the local SDK executable.

| Comparison on 49 synthetic grid points | v1 | v2 |
|---|---:|---:|
| Algebraically eligible under all defined illustrative constraints | **14** | **21** |
| Algebraically ineligible | 35 | 28 |

Seven point decisions changed because the two model formulations give different thermal margins. At the test case **F025**, $\\dot m_f=0.04\\,kg/s$, $T_w=380\\,K$ and recovery $\\rho_r=0.35$: the observed v1 margin was **92,759.13 W** and the v2 margin **254,870.97 W**. The numerical evidence is in [`results`](results/README_DATA.md), including the fact that the grid CSV is a transcription of actual numerical output rather than a raw MCP payload.

![Energy balance](figures/01_furnace_energy_distribution.png)
![Baseline constraint map](figures/02_feasible_map_v1.png)
![Recovered-energy constraint map](figures/03_feasible_map_v2.png)
![Observed heat balance margins](figures/04_heat_balance_margins.png)
![Emissions constraints](figures/05_emission_constraints.png)
![Recovery scenarios](figures/06_recovery_sensitivity.png)
![Radiation sensitivity](figures/07_radiation_temperature_sensitivity.png)
![TINC widths](figures/08_tinc_point_widths.png)

## How paceval owns the computation

The original `paceval_main.h` and `paceval_main.cpp` are provided **unchanged** in `src/`. The full formulas are defined in [`src/formula_manifest.json`](src/formula_manifest.json) and the corresponding actual C++ graph registry [`src/generated_formulas.h`](src/generated_formulas.h). The application creates a persistent paceval computation object per graph, reuses it for all rows, and calls `paceval_dGetMultipleComputationsResultsExt` for batch evaluation where supported.

The C++ host owns CSV syntax and dimensional validation, safe use of `paceval_dConvertStringToFloat` and `paceval_dConvertFloatToString`, graph cleanup, result mapping, execution diagnostics, and independent native checks. It does **not** replace the 32 domain expressions with native equations in its published output. A true CSV output is generated only if the compatible local SDK program successfully runs.

### Local C++ reproduction (not executed in this release)

```bash
cmake -S src -B build -DPACEVAL_SHARED_LIB=/absolute/path/to/compatible/libpaceval.so
cmake --build build --config Release
ctest --test-dir build --output-on-failure
./build/industrial_furnace_paceval examples/synthetic_operating_points.csv build/local_results.csv
```

The original SDK header and bridge were syntax-checked with C++17. **No compatible Linux shared library was available here**, so linking and local CTest were not executed. No local latency, throughput, speedup or energy benchmark is claimed. The external shared library is deliberately **not bundled**.

### Independent numerical reproduction

```bash
python -m pip install mpmath matplotlib markdown-it-py PyMuPDF
python validation/high_precision_reference.py
python validation/check_project.py
```

The independent 90-decimal-digit mpmath reference tested **329** archived numeric/boolean cells and **12** interval point inclusions successfully. The interval results bound **point evaluations**, not uncertainties over entire input intervals. The operator selftests distinguish `%` from `mod` for negative operands.

The archive-wide GitHub Markdown preflight checks both inline and stand-alone display mathematics, forbids raw TeX math delimiters and `\\operatorname`, checks relative image/file links and runs negative regression examples. Actual rendering in the GitHub.com web UI was not inspected; it is not claimed as proven.

## Limits and go / no-go decision

This study uses only **synthetic operating values and assumed physical coefficients**. It has no measured furnace gas balance, time-dependent thermal storage, temperature-profile validation, burner chemistry, radiation view-factor model, real NOx measurement or energy-use benchmark. It therefore demonstrates only the actual programmable algebra and logical screening. A pilot is a technical *go* only after independently measured accuracy criteria and either at least 15% measured end-to-end performance/energy benefit or at least 25% measured reduction in formula-update/integration effort (without a quality regression); those are predeclared **future acceptance thresholds**, not achieved benefits.

See [research validation](RESEARCH_VALIDATION.md) and the [English whitepaper](paceval_Industrial_Furnace_Energy_Whitepaper_EN.pdf).

## Sources and scope

* US Department of Energy: [Process Heating Systems](https://www.energy.gov/cmei/ito/process-heating-systems), [MEASUR tool](https://www.energy.gov/cmei/ito/measur), [Waste Heat Recovery Basics](https://www.energy.gov/cmei/ito/waste-heat-recovery-basics).
* ORNL: [MEASUR Process Heating Assessment documentation](https://industrialresources.ornl.gov/measur/suite/docs/group__process__heating__assessments).
* US EPA: [emissions estimates and source test hierarchy](https://www.epa.gov/general-conformity/general-conformity-training-modules-appendix-sample-emissions-calculations).
* ISO: [ISO 13577-2:2023 combustion-system safety scope](https://www.iso.org/standard/80533.html); it is *not* a performance-validation standard for these equations.

**No measured performance, efficiency saving, emission-reduction claim, control-system certification, or deployment evidence is asserted.**
'''
(R/'README.md').write_text(README)
(R/'LICENSE_NOTICE.md').write_text('''# License and source provenance

Original `src/paceval_main.h` and `src/paceval_main.cpp` were copied byte-for-byte from the user-provided original paceval SDK material in the preceding research project; their embedded original copyright/license notices are retained. They are not an authorization to redistribute or modify any external binary. The compatible shared library is intentionally **not** included; obtain permissions and the correct runtime independently.

All newly authored explanatory diagrams, synthetic examples, independent validation programs and WP30 prose are research examples. They do not change the licensing of the original paceval SDK or third-party sources; no upstream license is invented here.
''')
(R/'RESEARCH_VALIDATION.md').write_text('''# Research validation and audit boundary

* **Execution:** real paceval MCP service version 4.26. Thirty-two domain graphs were registered and evaluated on 49 + 12 synthetic rows, giving 1,952 actual graph-point evaluations without returned errors. Additional TINC 2 x 6 and operator 7 x 3 tests passed.
* **Numeric reference:** 90-decimal-digit independent mpmath direct translation for all 61 input rows. Exactly 329 recorded cells independently compared within absolute tolerance 1e-6 (W or stated units) and relative tolerance 1e-11; 12 pointwise TINC bounds contained independent point references.
* **Decision proof:** 14 baseline and 21 recovery-version candidates eligible across the 49-row grid, with 7 status changes. No industrial evidence is implied by these synthetic counts.
* **Original SDK:** original unmodified `paceval_main.h/.cpp` and new C++ demonstration compiled in syntax-only C++17 tests. Linking, `ctest`, live batch SDK execution, runtime metrics and SDK string-conversion execution are **not completed** because the matching library was unavailable.
* **Physical assumptions:** steady quasi-static balances, externally supplied temperatures and flows, simplified wall losses, no stored heat and no chemical reaction kinetics. `eta` represents the heat input within the chosen boundary prior to explicitly enumerated losses. Positive heat margin is not a completed measured furnace energy balance.
* **Emissions:** assumed fuel CO2 factor and synthetic NOx concentration, not a temperature-to-NOx prediction. No local permit limits or oxygen-reference corrections are asserted. No emission compliance claim.
* **Validation risk:** the 14-digit grid transcription is derived from displayed real MCP values and known constant fuel increments, not an archived byte-identical server JSON response. The 12-case additional scenario CSV contains the recorded visible remote values. `results/independent_reference_all_61.csv` is newly calculated independently, not passed off as paceval output.
* **Precision:** TINC confirms only individual point boundaries in the remote return format; there is no proof covering ranges of uncertain inputs.
* **Go/no-go:** require measured errors and measured full-pipeline advantage (15%) or integration effort reduction (25%), as a prospective acceptance criterion only.
''')
(R/'results/README_DATA.md').write_text('''# Dataset provenance

* `mcp_observed_grid_transcription.csv`: all 49 grid cases actually evaluated through MCP 4.26; selected result columns transcribed at up to 14 significant digits from returned output and reconstructed using the observed linear fuel increment for each wall row. **Not a raw JSON payload.**
* `mcp_observed_snapshots.csv`: actual 12-case MCP batch selected values recorded to the displayed precision.
* `mcp_tinc_observed.csv`: 12 actual returned interval-enabled point outputs and bounds.
* `operator_mcp_selftest.json`: actual SDK-compatible operator semantics returned by the remote 4.26 engine.
* `independent_reference_all_61.csv`: independent 90-digit mpmath reference values, *not* remote paceval data.
* `high_precision_validation.json`: numerical comparisons/point inclusion, including recorded maximum error and failure log.
* `execution_evidence.json`: counts, version, scope, negative claims.
* `math_execution_inventory.csv`: all owned mathematical functions with execution status and units.
''')
(R/'examples/DATA_SCHEMA.md').write_text('''# SI data schema

All inputs are synthetic, not actual measurements. The CSV header has `case_id` followed by the 25 variables in `src/formula_manifest.json`, in precisely that order. `mf` and `mp` are kg/s, `LHV` J/kg, `eta` 0..1, `cp`,`cpe` J/(kg*K), `Tin`,`Tout`,`Tw`,`Tamb`,`Tex`,`Tmax` K, `beta` 1/K, external convection `U` W/(m^2*K), `A` m^2, `eps`,`rec` 0..1, `sigma` W/(m^2*K^4), `mex` kg/s, `efco2` kg CO2/kg fuel, `cNOx` mg/Nm^3 on a consistent dry/reference basis, `qflue` Nm^3/s on that same basis, `capco2`,`capnox` kg/s, `fuelcap` kg/s. Host enforces positive temperatures and denominators. Caps are hypothetical, not legal requirements.

The 49-grid variation is fuel mass flow 0.025..0.055 kg/s x external wall skin 350..410 K; assumed NOx concentration covaries with wall test index for sampling coverage only and is NOT a generated physical NOx prediction. Twelve snapshots vary recovery fraction at three values and fuel at four values.
''')

# Report generation with deliberate page breaks and platform-independent paragraph styles.
fontroot='/usr/share/fonts/truetype/dejavu'
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('DejaVu',fontroot+'/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuBold',fontroot+'/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVuBold',italic='DejaVu',boldItalic='DejaVuBold')
STYLE=getSampleStyleSheet()
STYLE.add(ParagraphStyle(name='WPTitle',fontName='DejaVuBold',fontSize=22,leading=28,textColor=HexColor('#183f51'),spaceAfter=15))
STYLE.add(ParagraphStyle(name='WPSubtitle',fontName='DejaVu',fontSize=11.5,leading=17,textColor=HexColor('#4e7b86'),spaceAfter=16))
STYLE.add(ParagraphStyle(name='WPHeader',fontName='DejaVuBold',fontSize=15,leading=20,textColor=HexColor('#153b4e'),spaceBefore=7,spaceAfter=12))
STYLE.add(ParagraphStyle(name='WPBody',fontName='DejaVu',fontSize=9.45,leading=15.2,spaceAfter=9,textColor=HexColor('#243a44')))
STYLE.add(ParagraphStyle(name='WPCaption',fontName='DejaVu',fontSize=7.9,leading=12,textColor=HexColor('#607781'),spaceBefore=5,spaceAfter=10))
STYLE.add(ParagraphStyle(name='WPEquation',fontName='DejaVuBold',fontSize=10.0,leading=16,spaceBefore=7,spaceAfter=10,textColor=HexColor('#13677b')))
STYLE.add(ParagraphStyle(name='WPSmall',fontName='DejaVu',fontSize=8,leading=13,spaceAfter=8,textColor=HexColor('#455b62')))
def para(s,style='WPBody'):return Paragraph(s,STYLE[style])
def chart(file,caption,width=166):
 path=G/file; im=__import__('PIL').Image.open(path);ratio=im.height/im.width
 return [RImage(str(path),width*mm,width*ratio*mm),para(caption,'WPCaption')]
pages=[]
def page(header,body=[],chart_name=None,cap='',picture_width=166):
 x=[]
 if header:x.append(para(header,'WPHeader'))
 for t in body:
  if isinstance(t,list):x+=t
  else:x.append(para(t))
 if chart_name:x+=chart(chart_name,cap,picture_width)
 pages.append(x)

# Page 1 cover
pages.append([Spacer(1,15*mm),para('INDUSTRIAL FURNACE<br/>ENERGY BALANCE AND<br/>EMISSION CONSTRAINT MAPS','WPTitle'),
 para('Research WP 30 | Actual mathematical execution with the paceval Engine | 15 November 2026','WPSubtitle'),
 RImage(str(G/'00_industrial_furnace_hero.png'),166*mm,83*mm),Spacer(1,10*mm),
 para('<b>Research objective.</b> Test reproducible, versioned thermal balances and supplied emission margins for fuel-fired industrial process heating using persistent paceval calculation graphs.'),
 para('<b>Execution evidence.</b> Thirty-two distinct graphs; 49 grid cases and 12 recovery cases evaluated remotely on paceval MCP 4.26. No measured industrial furnace data and no local SDK runtime benchmark.'),
 para('Study status: mathematical research demonstrator, not a furnace safety, performance, emissions, or regulatory compliance qualification.','WPSmall')])
page('Executive summary and verified findings',[
'The original WP 30 proposal specified fuel heat, product sensible heat, external wall convection and radiation. This completed demonstrator extends these four reusable mathematical kernels into 32 actual paceval expressions, including stack sensible heat, a hypothetical recovery device, an assumed temperature-dependent heat capacity, rate-based emission constraints, score functions and analytic sensitivities.',
'Two stable mathematical versions remain accessible without replacing previously created graph handles. The baseline retains all gross exhaust loss; version 2 uses a recovery fraction and a linear heat-capacity law. All required arithmetic and logical constraint combinations are computed as explicit paceval graphs.',
'<b>Actual recorded execution:</b> 1,568 grid graph-point evaluations and 384 recovery-snapshot evaluations, all returned without engine error. Fourteen of 49 grid points satisfy the version 1 mathematical guard; 21 satisfy version 2; seven status decisions differ. In independent 90-digit reference testing, 329 archived values and Boolean cells and 12 pointwise TINC inclusions passed.',
'This is a functional result on synthetic inputs. No measured thermodynamic benefits, fuel savings, emissions performance, CPU speedups or regulatory certifications are claimed.'
], '09_execution_architecture.png','Figure 1. Distinct execution ownership. Remote paceval executed the mathematical graphs; the host controls data and independent checking.')
page('1. Why this use case matters in process heating',[
'A steel-reheating or heat-treatment furnace burns fuel, heats a moving material load and releases unwanted energy through external walls and hot flue gas. Operators compare many operating conditions while managing thermal throughput, fuel capacity and environmental requirements. An energy-balance screen is useful only when its physical boundary and missing terms are explicit.',
'The US Department of Energy\'s MEASUR and its earlier PHAST methodology support heat-balance and what-if studies for industrial furnaces, accounting for the many potential loss categories. The present demonstrator focuses on a much smaller equation set and does not reproduce MEASUR or validated plant performance models.',
'Waste-heat recovery can reduce the unrecovered flue-gas energy leaving a defined furnace balance. However, a thermal net-benefit conclusion requires verified temperatures, flow, air/fuel ratio, recovery hardware, pressure drop, safety controls, process dynamics and real fuel consumption. A positive score from synthetic coefficients does not prove such a benefit.',
'ISO 13577-2:2023 defines relevant combustion-system safety scope. This project only screens algebraic thermal and emission-related constraints; it does not implement any safety interlock or prove conformity.'
], '01_furnace_energy_distribution.png','Figure 2. Energy allocation for synthetic case F025, computed from the remote paceval results. Positive residual is unallocated model power, not a closed measured heat balance.')
page('2. Physical assumptions and dimensional definitions',[
'<b>Control volume.</b> The fuel heat enters the defined furnace control volume as released chemical power. The parameter eta represents burner release into this volume before separately assessed wall and exhaust losses. Using a net furnace efficiency instead would double-count these losses.',
'<b>Power units.</b> Fuel mass flow mf in kg/s and LHV in J/kg produce W. Material mass flow in kg/s times cp in J/(kg K) times temperature rise in K also produce W. The external skin convection coefficient has units W/(m² K); emissivity is dimensionless; the Stefan-Boltzmann constant is W/(m² K⁴).',
'<b>Exterior wall.</b> Tw is external wall skin temperature, not chamber gas temperature. The coefficient U stands for external convective loss only; the radiation term is added independently. Internal wall resistance, radiation view factors and aperture losses are outside this reduced model.',
'<b>Exhaust.</b> The net stack loss assumes an external enthalpy-flow reference and a hypothetical recuperator fraction; chemical flue composition, dilution, dewpoint and heat-exchanger pinch constraints are not calculated.',
'<b>Thermal storage.</b> Quasi-steady operation is assumed; heat stored by refractory lining or delayed load changes is absent.'
])
page('3. Baseline model v1: direct furnace heat balance',[
'Fuel power: Q_fuel = mf × LHV × eta_b. Product heat: Q_load1 = mp × cp0 × (Tout − Tin). External convective loss: Q_conv = U × A × (Tw − Tamb). Surface radiation: Q_rad = eps × sigma × A × (Tw^4 − Tamb^4).',
'Gross exhaust loss: Q_ex = mex × cpe × (Tex − Tamb). The baseline balance residual is M1 = Q_fuel − Q_load1 − Q_conv − Q_rad − Q_ex.',
'All temperatures used in radiation calculations are absolute kelvin temperatures. Operating points with nonpositive temperatures, nonpositive heat capacities or other singular input domains are rejected before graph evaluation; Boolean masks are never used as a substitute for domain validation.',
'A negative residual is a heat deficit under the stated simplified assumptions. A positive residual indicates that additional unmodeled sinks, storage or controller adjustments must account for unused heat in a genuine closed balance; it is not a physical energy-creation phenomenon.'
], '04_heat_balance_margins.png','Figure 3. Actual recorded paceval thermal residuals for selected wall temperatures; baseline dashed, recovered version solid.')
page('4. Extended model v2: cp(T) and stack recuperation',[
'To make the model change explicit and scientifically falsifiable, we assume cp(T) = cp0 [1 + beta (T − Tin)] on the product interval. Integrating this law yields Q_load2 = mp cp0 [ΔT + beta (ΔT)^2 / 2]. This is a hypothetical local approximation, not a tabulated material property model.',
'With recovery fraction r between 0 and 1, Q_rec = r × Q_ex and Q_ex,net = (1 − r) Q_ex. The revised residual is M2 = Q_fuel − Q_load2 − Q_conv − Q_rad − Q_ex,net.',
'Thus M2 − M1 = Q_rec − (Q_load2 − Q_load1). Recuperation can improve the balance, but positive cp-slope increases useful heat demand. The change is not universally favorable. When r = 0 the second model can have a worse thermal margin than v1; when r is larger it can improve.',
'The expressions are registered as separate persistent paceval handles, including a combined delta and the fuel flow needed to balance modeled heat demand.'
], '06_recovery_sensitivity.png','Figure 4. Twelve actual remote paceval recovery-scenario outputs show heat margin changes for three different recuperation fractions.')
page('5. Emissions and boundary predicates',[
'The CO2 expression uses an <b>externally supplied fuel-specific carbon factor</b>: mCO2 = mf × eCO2. The selected illustrative factor is not evidence of measured plant emissions.',
'For NOx, only an explicitly supplied normalized dry exhaust volumetric flow and concentration are combined: mNOx = C_NOx × V_dry × 10^−6, where concentration is mg/Nm³ and rate is Nm³/s. These synthetic inputs are not derived from flame temperature. Before actual compliance calculations, oxygen-reference corrections, wet/dry basis and reference conditions must be reconciled.',
'Both model versions combine the thermal residual (≥0), CO2 cap margin (≥0), NOx cap margin (≥0), fuel-capacity margin (≥0) and upper material-temperature margin (≥0). Caps are chosen as synthetic exercise parameters, not as regulations.',
'Scores combine dimensionless normalized margins using the minimum operator. A negative score identifies the most restrictive synthetic inequality; it must not command an industrial actuator.'
], '05_emission_constraints.png','Figure 5. Distinct fuel-carbon and supplied NOx constraints, deliberately shown with different abscissae and units. Neither is a combustion chemistry prediction.')
page('6. Actual 49-point process-window results',[
'The independent experimental grid used seven fuel flows between 25 and 55 g/s and seven exterior wall temperatures between 350 and 410 K. NOx concentration was explicitly supplied as a separate synthetic input that covaries with wall scenario only for data coverage; it is not generated by the heat equation.',
'From the actual remote engine responses, 14 of 49 points satisfy all five baseline constraints and 21 satisfy the second model; seven decisions changed. No model graphs reported a computation error.',
'For the example F025 (fuel 40 g/s, exterior skin 380 K), v1 thermal margin is +92.76 kW; v2 thermal margin is +254.87 kW. This difference consists of recovered stack enthalpy minus the increase in assumed product sensible heat.',
'The scenario labels, inputs, table-transcription details and independent references are in the ZIP. Because the server batch payload was not stored byte-identically, the archived 49-row selected-value CSV is explicitly identified as a transcription/reconstruction, not a raw RPC record.'
], '02_feasible_map_v1.png','Figure 6. Baseline model v1 algebraic eligibility on the executed synthetic 7×7 grid.')
page('7. Versioned constraint map: recovery model',[
'Model v2 is not automatically preferable in all conditions. The effect of recovering exhaust heat must be weighed against the alternative heat-capacity assumption. The model provides explicit margins and logical guard values so that differences can be traced to a formula version instead of hidden postprocessing.',
'Among the 49 synthetic points, exactly seven status values change, in the direction observed here from ineligible baseline to eligible version v2. That result depends on the chosen illustrative energy and emission constraints; it is not an empirical energy efficiency improvement.',
'At 350 K external wall skin and 35 g/s fuel, the model v1 margin is about −70.22 kW while v2 is about +91.89 kW. At fuel flows above the deliberately low CO2 cap, both versions reject the candidate even if they are thermally positive.'
], '03_feasible_map_v2.png','Figure 7. Version 2 actual paceval guard outputs; green denotes satisfaction of every illustrative algebraic constraint.')
page('8. Original paceval execution ownership and reuse',[
'A manifest includes every one of 32 nontrivial mathematical functions, its full expression, units and the precise execution owner. Core temperature and fuel arithmetic, emissions rates, version-specific demands, cost/score margins and analytic sensitivity formulas are evaluated in real paceval computation graphs. The C++ host does not substitute its own numeric engine for user-facing results.',
'In the archived run, 32 distinct formulas were registered through the remote paceval MCP 4.26 service and applied in a bulk 49-row evaluation and a separate 12-row batch. This gives 1,568 + 384 = 1,952 main graph-point evaluations, all with returned error code zero. This is a calculation count only and not a measured performance benchmark.',
'The accompanying C++ program registers the same formulas with the original `paceval_CreateComputation`, reuses handles for input rows, and intends to call `paceval_dGetMultipleComputationsResultsExt`. Original SDK float/string conversions, batch layout checks, operator tests and independent numeric reference checks are included. The compatible local shared library was not available, so only syntax compilation was performed for C++.'
], '09_execution_architecture.png','Figure 8. Mathematical execution and independent validation paths. The original C++ SDK path is available as source but unexecuted locally.')
page('9. Sensitivities and physically meaningful limits',[
'Analytic, separately registered paceval graphs give dM2/dmf = LHV eta, dM2/dr = Q_ex,gross, and dQ_rad/dTw = 4 eps sigma A Tw^3. These are exact derivatives of the chosen explicit expressions within their smooth domains; paceval was not claimed to perform automatic differentiation.',
'Likewise, the fuel-rate sensitivity to the recovery fraction is −Q_ex,gross/(LHV eta). The product temperature derivative is mp cp0 [1+beta (Tout−Tin)]. Each is directly reference-checkable without a nonlinear numerical solver.',
'The radiation derivative increases with skin temperature because of the fourth-power law. Its magnitude is meaningful only when Tw is a measured exterior surface temperature and emissivity/area are sufficiently characterized; otherwise it describes the chosen hypothetical equation.'
], '07_radiation_temperature_sensitivity.png','Figure 9. Temperature derivative of the explicitly implemented paceval radiation-loss graph for the synthetic skin-temperature sweep.')
page('10. Independent high precision and TINC',[
'An independent implementation in 90-decimal-digit mpmath, not generated by the paceval engine, evaluates all 61 scenarios and compares 329 archived numeric and Boolean outputs to the actual remote observations. Every one passes the declared absolute tolerance 10^−6 and relative tolerance 10^−11 on the chosen units.',
'Two additional interval-enabled paceval graphs were created for v2 thermal residual and wall radiation. Six distinct input vectors produced 12 interval outputs with zero returned errors. Each returned lower/upper interval bound encloses the independently computed point reference for the represented binary input values.',
'These are <b>pointwise</b> numerical checks. They do not show that an uncertain input *range* maps into a certified output range. The observed interval widths cannot be interpreted as sensor uncertainty or a 95% confidence interval.',
'A separate seven-graph operator test covers signed `%` remainder, mathematical `mod` for negative operands, `min`, `max`, relational conjunctions, `NOT`, `OR` and `XOR` over three input sets. All 21 executions returned error zero and expected results.'
], '08_tinc_point_widths.png','Figure 10. Point-result interval widths directly transcribed from actual TINC outputs. No global uncertainty guarantee is inferred.')
page('11. Independent reference cases and failure modes',[
'Key numerical edge cases include: recovery fraction zero and one; kelvin temperature validation; equality of skin and ambient temperature (zero wall loss); very large exterior wall temperature triggering high radiative losses; nonpositive denominators and heat capacities; negative fuel flows; negative emissions concentration; and score boundaries where a tiny numerical rounding difference could change a Boolean state.',
'The C++ host rejects nonphysical input domains before graph evaluation, with no assumption that `(condition AND expression)` skips unsafe expressions. The score is normalized, but not a physical optimization objective. The implementation avoids nonfinite inputs and checks per-element batch error codes.',
'The archived actual remote scenarios exercise 49 regular inputs, 12 recovery cases, 12 TINC evaluations and 21 operator checks. Nonphysical test inputs were not submitted to a real furnace or passed off as operationally meaningful.',
'One notable observation is that with r = 0, v2 has a higher product heat term and therefore a smaller thermal margin than v1. Any claim that model v2 always saves fuel would be contradicted by this example.'
])
page('12. Software reproducibility and evidence hierarchy',[
'Input schema: 25 values per row plus a stable case ID; each formula consumes the declared common vector. All raw candidate inputs are available as `examples/synthetic_operating_points.csv`, with 49 grid rows and 12 recovery rows. The model registry is defined in `src/formula_manifest.json` and a generated C++ header.',
'All actually observed selected outputs are recorded with provenance. `mcp_observed_grid_transcription.csv` preserves tabulated values to about 14 significant digits; the full RPC JSON was not preserved. `mcp_observed_snapshots.csv` records the visible server values for 12 recovery variants. `independent_reference_all_61.csv` is separately generated by 90-digit mpmath and is not mislabeled as paceval output.',
'The original `paceval_main.h` and `paceval_main.cpp` are included without source modifications. The shared binary library is not bundled. Local C++ sources and the SDK bridge passed a C++17 syntax-only compiler test; local CMake linkage, executable runs and CTest are not claimed because a compatible runtime library is unavailable.',
'The project supplies unit/domain validation, original SDK conversion procedures, operator selftests, a manifest and test logs. A Markdown parser checks GitHub-compatible math delimiters across the ZIP and detects deliberately invalid regression cases.'
])
page('13. Interpretation, decision criteria and limits',[
'The demonstrator verifies the mathematical consistency, real paceval execution and reproducible scenario dependence of its chosen formula graphs. It does not confirm stable physical furnace operation, stack-emissions compliance, actual energy efficiency, safety interlocks, environmental performance, process metallurgy, maximum throughput or calibration.',
'An industrial pilot needs real furnace flow and temperature sensors, verified material and flue-gas properties, measured emissivity, calibrated carbon emission factors, NOx source testing with appropriate reference oxygen and conditions, a sufficiently complete energy balance and matched comparison with DOE MEASUR or a trusted specialist thermodynamic workflow.',
'Before a positive technology claim, independently predeclare acceptable application errors, test the whole pipeline, and measure median/p95/p99 latency and energy with actual repeated runs. The proposal sets a possible go threshold of 15% measured full-pipeline latency or energy improvement or 25% measured formula update/integration effort reduction. These are prospective criteria, <b>not results of this project</b>.',
'The strongest supported conclusion is that paceval MCP 4.26 actually evaluates a wide, versioned collection of furnace energy and emission-constraint formulas with independent pointwise verification on synthetic datasets.'
])
page('14. Sources and traceability',[
'<b>[1] US Department of Energy.</b> Process Heating Systems; MEASUR; Waste Heat Recovery Basics (public pages, checked November 2026).',
'<font color="#1b6b84">https://www.energy.gov/cmei/ito/process-heating-systems</font><br/><font color="#1b6b84">https://www.energy.gov/cmei/ito/measur</font><br/><font color="#1b6b84">https://www.energy.gov/cmei/ito/waste-heat-recovery-basics</font>',
'<b>[2] Oak Ridge National Laboratory.</b> MEASUR Process Heating Assessment documentation. <font color="#1b6b84">https://industrialresources.ornl.gov/measur/suite/docs/group__process__heating__assessments</font>',
'<b>[3] United States Environmental Protection Agency.</b> General Conformity Training Modules: sample emissions calculations; source tests and factors. <font color="#1b6b84">https://www.epa.gov/general-conformity/general-conformity-training-modules-appendix-sample-emissions-calculations</font>',
'<b>[4] ISO 13577-2:2023.</b> Industrial furnaces and associated processing equipment — Safety — Part 2: Combustion and fuel handling systems. <font color="#1b6b84">https://www.iso.org/standard/80533.html</font>',
'<b>[5] paceval.</b> Developer architecture and original C/C++ SDK interfaces. <font color="#1b6b84">https://paceval.com/developers/</font>',
'<b>[6] WP 30 original proposal, 13 Nov 2026.</b> Supplied in the project as `docs/Original_WP30_Proposal_2026-11-13.pdf`.',
'All references inform the model scope and limitations. None certifies the new synthetic paceval results. Research release version 1.0, 15 November 2026.'
])

class PageNumbers:
 def __call__(self,canvas,doc):
  canvas.saveState();w,h=A4;canvas.setStrokeColor(HexColor('#d6e2e5'))
  canvas.line(22*mm,18.5*mm,w-22*mm,18.5*mm)
  canvas.setFont('DejaVu',7.5);canvas.setFillColor(HexColor('#59727d'))
  canvas.drawString(22*mm,12.5*mm,'PACEVAL  |  WP 30  |  Synthetic Research Demonstrator')
  canvas.drawRightString(w-22*mm,12.5*mm,f'Page {doc.page}')
  canvas.restoreState()

pdf=R/'paceval_Industrial_Furnace_Energy_Whitepaper_EN.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=22*mm,rightMargin=22*mm,topMargin=20*mm,bottomMargin=24*mm,
 title='Industrial Furnace Energy Balance and Emission Constraint Maps with paceval',author='paceval industrial research demonstrator',subject='WP 30 reproducible numerical research')
story=[]
for idx,p in enumerate(pages):
 if idx:story.append(PageBreak())
 story+=p
try:doc.build(story,onFirstPage=PageNumbers(),onLaterPages=PageNumbers())
except Exception as e:
 print('PDF BUILD ERROR',e);raise

print('PDF written',pdf,'intended sections',len(pages))
