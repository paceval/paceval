#!/usr/bin/env python3
"""Generate a fixed-layout English research PDF from released figures and audit files."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'paceval_Inventory_Replenishment_Whitepaper_EN.pdf'
W,H=A4;LEFT=43;RIGHT=43;WIDTH=W-LEFT-RIGHT
INK=HexColor('#182e32');ACC=HexColor('#a95d36');SUB=HexColor('#53746c');PALE=HexColor('#f1f5ef');MUTED=HexColor('#66727a')
fontroot='/usr/share/fonts/truetype/dejavu'
pdfmetrics.registerFont(TTFont('Regular',fontroot+'/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('Strong',fontroot+'/DejaVuSans-Bold.ttf'))
styles={
 'normal':ParagraphStyle('normal',fontName='Regular',fontSize=8.7,leading=13.2,textColor=INK),
 'small':ParagraphStyle('small',fontName='Regular',fontSize=7.6,leading=11.3,textColor=INK),
 'caption':ParagraphStyle('caption',fontName='Regular',fontSize=7.35,leading=11,textColor=MUTED),
 'sub':ParagraphStyle('sub',fontName='Strong',fontSize=10.4,leading=15,textColor=SUB),
}
c=canvas.Canvas(str(DEST),pagesize=A4);c.setTitle('Inventory Replenishment Rule Scenarios | paceval research demonstrator');page=0;y=0

def finish():
 c.setStrokeColor(HexColor('#dce6e2'));c.line(LEFT,32,W-RIGHT,32);c.setFillColor(MUTED);c.setFont('Regular',6.5);c.drawString(LEFT,20,'paceval. | Inventory Replenishment Rule Scenarios | Research demonstrator | 2026');c.drawRightString(W-RIGHT,20,str(page));c.showPage()
def start(title=None):
 global page,y
 if page:finish()
 page+=1;y=H-44
 if title:
  c.setFillColor(INK);c.setFont('Strong',14.5);c.drawString(LEFT,y,title);y-=21;c.setStrokeColor(ACC);c.setLineWidth(1.5);c.line(LEFT,y,W-RIGHT,y);y-=19

def paragraph(text,style='normal',gap=11):
 global y
 p=Paragraph(text,styles[style]);_,h=p.wrap(WIDTH,1500)
 if y-h<47:raise RuntimeError(f'Page {page} overflow: {text[:50]}')
 p.drawOn(c,LEFT,y-h);y-=h+gap

def heading(text):paragraph(text,'sub',4)
def image(name,max_height=340,caption=None):
 global y
 im=ImageReader(str(ROOT/'figures'/name));w,h=im.getSize();scale=min(WIDTH/w,max_height/h);ow=w*scale;oh=h*scale
 if y-oh<58:raise RuntimeError(f'Page {page} image overflow {name} y {y}')
 c.drawImage(im,LEFT+(WIDTH-ow)/2,y-oh,width=ow,height=oh,mask='auto');y-=oh+9
 if caption:paragraph(caption,'caption',8)
def table(rows):
 global y
 for i,(l,r) in enumerate(rows):
  pp=Paragraph(r,styles['small']);_,hh=pp.wrap(WIDTH*.62-15,500);rowh=max(hh+14,31)
  if y-rowh<51:raise RuntimeError(f'Page {page} table overflow')
  c.setFillColor(PALE if i%2==0 else HexColor('#fafbf9'));c.rect(LEFT,y-rowh,WIDTH,rowh,stroke=0,fill=1)
  ll=Paragraph('<b>'+l+'</b>',styles['small']);_,hl=ll.wrap(WIDTH*.36-12,500);ll.drawOn(c,LEFT+8,y-8-hl)
  pp.drawOn(c,LEFT+WIDTH*.36+4,y-8-hh);y-=rowh+3
 y-=8

audit=json.loads((ROOT/'results'/'decimal_audit.json').read_text())
# Cover
start();c.setFillColor(SUB);c.setFont('Strong',11);c.drawString(LEFT,y,'PACEVAL  |  SCIENTIFIC RESEARCH DEMONSTRATOR');y-=43
c.setFillColor(INK);c.setFont('Strong',24);c.drawString(LEFT,y,'Inventory Replenishment');y-=30;c.drawString(LEFT,y,'Rule Scenarios');y-=26
paragraph('Versioned inventory-policy mathematics, direct reusable paceval computations, reproducible discrete-event scenarios, and independent numerical audits.', 'normal',13)
image('00_inventory_hero.png',max_height=240,caption='Cover illustration: concept artwork. All numbered charts are generated from the released paceval computation exports.')
paragraph('<b>Observed outcome.</b> Thirty registered reorder policies were implemented using 60 persistent paceval mathematical graphs. The released study evaluated 105,000 policy–SKU scenarios, independently audited 1,920 packed batch evaluations, and completed a 120-day synthetic inventory simulation for 1,440 policy–SKU combinations.',gap=13)
paragraph('<b>Scope.</b> This is a controlled numerical feasibility pilot, not a production inventory recommendation, real supplier forecast, live ERP connection or statement of commercial benefit. No time or hardware-related performance comparison is included.','caption')
# 2
start('1. Industrial problem and execution boundary')
paragraph('Manufacturing, distribution and service-parts operations continuously revise reorder parameters as demand, lead times, review intervals and service objectives change. The software must evaluate numerous alternative rules while preserving the inventory-position, outstanding-order and demand-event semantics of the host system.')
image('01_execution_architecture.png',245,'Figure 1. A fixed stateful host passes validated numeric inputs to versioned paceval computation handles, then audits results.')
heading('What paceval evaluates')
paragraph('The engine owns textual mathematical expressions, 60 persistent calculation handles, scalar double-precision calls and packed batch calls on independent inputs. Each registered policy contains an order-up-to target expression and a threshold expression.')
heading('What the C++ host evaluates')
paragraph('The host owns integer order rounding, policy gates, deterministic demand streams, fixed delivery schedules, stock arrivals, inventory position, lost-sales consumption, output files and separate native formula reference checks. Passing a mathematical evaluation does not establish that a replenishment policy is optimal.')
# 3
start('2. Mathematical policy contracts')
paragraph('Definitions: mean daily demand m [units/day], standard deviation s [units/day], lead time L [days], review interval R [days], inventory position I [units], and demand trend h [units/day]. Policy-specific z, b and k are dimensionless experimental factors, except b denotes a dimensionless equivalent of buffer days multiplied by m. The formula assumes independent daily demand only for the square-root uncertainty proxy; no fitted demand distribution or probabilistic service guarantee is asserted.')
heading('Order-up-to gap: reusable paceval expression')
paragraph('<font color="#a95d36"><b>G = m(L+R) + z s sqrt(L+R) + b m + k h L - I</b></font>')
paragraph('The candidate order is Q = ceil(max(0,G)) units. Positive-part clipping and rounding are host operations. All additions have units of inventory units when L and R are treated in days.')
heading('Conditional threshold: independent paceval expression')
paragraph('<font color="#a95d36"><b>H = m L + z s sqrt(L) + b m - I</b></font>')
paragraph('Conditional policies place an order only if H &gt; 0. Other policies compute the positive order-up-to quantity on their specified review day. Inventory position equals on-hand units plus outstanding orders, with no reserved/backordered units in the lost-sales study.')
heading('Discrete inventory dynamics')
paragraph('At each daily step t, the host receives scheduled arrivals A_t and observes demand D_t. Immediate fulfillment is F_t = min(I_t + A_t, D_t). Closing stock is max(0, I_t + A_t - D_t). New orders enter a future arrival bucket at t + L. These operations are deliberately not misrepresented as formulas executed by paceval.')
#4
start('3. Controlled test workload and reproducibility')
paragraph('The main released test contains 3,500 deterministically generated SKUs crossed with 30 versioned rules, totaling 105,000 static formula scenarios. Each policy has two separate graphs using a shared six-variable ABI; values are supplied without rebuilding the expression. Thirty-two inputs per graph are also checked through the packed SDK API.')
table([('SKU combinations','3,500 SKUs x 30 policies = 105,000 policy–SKU cases'),('Calculation graph handles','60: thirty order-up-to gaps and thirty conditional trigger gaps'),('Scalar formula audits','213,721, including the 61 x 61 formula surface'),('Packed batch audits','1,920 values: 32 inputs x 60 graphs'),('Inventory simulation','48 SKUs x 30 policies x 120 days = 1,440 synthetic runs'),('Demand construction','Frozen per-SKU deterministic pseudorandom sequence, seasonal multiplier, nonnegative demand'),('Review/lead conventions','Daily receiving and demand consumption; review only at declared integer intervals'),('No user data','Synthetic products, supplier lead times and demand values')])
paragraph('Results are exported as human-readable CSV; a separate Python high-precision oracle recomputes saved expression samples, and CTest invokes the original SDK integration path.')
# 5
start('4. Verified numerical execution')
paragraph('The original paceval_main.cpp and paceval_main.h public SDK facade is built into the C++ executable and linked to a compatible external Linux runtime. The measured result is correctness of mathematical evaluation in the stated bounded domain, not superiority to other implementations.')
table([('Scalar formula audits','213,721 calculations passed the separately coded native C++ reference'),('Batch formula audits','1,920 per-item results passed the native reference and SDK error checks'),('Independent decimal checks',f"{audit['within_tolerance']} / {audit['comparisons']} exported formula values agree within tolerance"),('Largest decimal difference',f"{float(audit['maximum_absolute_distance_units']):.3e} inventory units (CSV-decimal interpretation)"),('Inventory outcome agreement','1,440 / 1,440 paired runs had the same order counts and fill-rate outcomes'),('CMake / CTest','1 / 1 integration test passed with externally supplied paceval Linux .so'),('Reported runtime speedups','None: not a study objective in this release')])
paragraph('The external decimal reference operates on the released CSV decimal values, not bit-exact reconstruction of all binary64 inputs. The numerical tolerance is abs(error) &lt;= 1e-10 * (1 + abs(reference)). All released observations are finite and the independently regenerated results passed the coded acceptance tests. This finite sampling is not a proof for all parameter values.')
# 6
start('5. Evaluated service and inventory outcomes')
paragraph('For this synthetic lost-sales simulation, fill rate means total immediate units fulfilled divided by total requested units. A cycle service level would instead measure the probability of a no-stockout replenishment cycle; it is not inferred from fill rate. No observed future demand is read when making an earlier review decision.')
image('02_fill_rate_by_policy.png',300,'Figure 2. Different policy parameter combinations produce different realized fill-rate outcomes on identical SKU demand streams.')
paragraph('These measurements are simulation outputs from frozen, synthetic demand assumptions. They do not validate the underlying demand-generation model or guarantee a specified customer service level.')
#7
start('6. Reusable formula evaluation and safety rules')
image('03_order_gap_by_inventory.png',300,'Figure 3. Evaluated unrounded order-gap values across selected policies and initial inventory positions.')
paragraph('The host preserves the declared formula revision and does not silently substitute a new target. A conditional gate is computed by a second persistent graph. Integer order quantities are rounded upward only after validating the floating-point formula result.')
heading('Important assumptions')
paragraph('No minimum order quantity, supplier calendar, bulk discounts, perishability, multi-echelon transfers, returns, stock reservations, substitutions, transport capacity or dynamically updated forecasts are modeled. The review dates do not imply continuous monitoring between checks.')
#8
start('7. Real 3D mathematical scenario surface')
image('04_replenishment_3d_surface.png',385,'Figure 4. A 61 x 61 order-quantity surface from 3,721 direct paceval calls using one persistent graph.')
paragraph('The stair-step appearance follows from integer ceil and positive-part clipping performed by the host. The raw mathematical graph remains continuous in its inputs before rounding and policy gating.')
#9
start('8. Contours and service–inventory trade-offs')
image('05_replenishment_contours.png',280,'Figure 5. Contour projection of the same 3,721 computed order quantities.')
image('06_inventory_service_tradeoff.png',250,'Figure 6. Realized synthetic fill rate versus mean stock for each of 1,440 simulated policy–SKU combinations.')
#10
start('9. Policy versioning and research interpretation')
image('07_policy_registry.png',272,'Figure 7. Fixed policy-specific parameters and review cadence; the complete registry is machine readable.')
paragraph('Thirty distinct policy configurations are registered as transparent formula strings; both the order-up-to and optional trigger calculations can be inspected and reproduced. Future revisions should register a new policy ID, retain the previous graph, and perform the same numerical audit before activation.')
heading('Scientific interpretation')
paragraph('The demonstration establishes that paceval can manage and evaluate reusable mathematical rule kernels across many scenarios while a C++ inventory simulation handles discrete state changes. It does not establish statistical optimality, production ERP compatibility or real customer service performance.')
#11
start('10. Reproduction, limitations and references')
paragraph('<b>Build:</b> <font name="Regular">cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so</font>. Then compile with <b>cmake --build build -j</b> and run <b>ctest --test-dir build --output-on-failure</b>. The external binary is not included in the publication ZIP.')
paragraph('<b>Recompute:</b> run <b>./build/inventory_replenishment --skus 3500 --out reproduced</b>; compare or replace the released examples explicitly before regenerating charts. Python scripts regenerate figures and this PDF from the files under examples/.')
heading('Scope and limitations')
paragraph('Service levels depend on demand, lead-time and lost-sales assumptions. The project does not include real inventory transactions, forecasting, policy optimization, optimization guarantees, supplier reliability models or probabilistic coverage certification. No performance or energy advantage is claimed.')
heading('External scientific and technical resources')
paragraph('1. paceval official mathematical API: https://paceval.com/api/','small')
paragraph('2. Inventory Systems, continuous and periodic review: https://rossetti.github.io/RossettiInventoryBook/08-Chapter8.html','small')
paragraph('3. Continuous versus periodic review discussion, TUM: https://mediatum.ub.tum.de/doc/1743194/1743194.pdf','small')
paragraph('4. Inventory service metrics, NIDA: https://logistics.nida.ac.th/wp-content/uploads/2016/08/6001-11-multiperiod-performance-v2.pdf','small')
paragraph('<b>Conclusion:</b> The defined inventory rule evaluations with 60 real paceval computation graphs were executed, cross-checked against separate formulas, and integrated with a deterministic 120-day lost-sales simulator. The evidence supports numerical feasibility in this controlled research domain.','normal')
finish();c.save();print('Saved',DEST,'pages',page)
