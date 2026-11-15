#!/usr/bin/env python3
"""Author a traceable, English scientific report. Data and diagrams are generated from the executable's actual CSV output."""
from pathlib import Path
import csv,json,html,math
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether,Preformatted
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'results'/'selfplay_depth3_8plies';DEPTH4=ROOT/'results'/'selfplay_depth4_1ply'
R=list(csv.DictReader(open(DATA/'selfplay_timeline.csv')))
D4=list(csv.DictReader(open(DEPTH4/'selfplay_timeline.csv')))[0]
E=json.load(open(DATA/'run_evidence.json'))
F=ROOT/'figures'
OUT=ROOT/'JOSHUA_Chess_Research_Whitepaper_EN.pdf'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';fontbold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DVS',font));pdfmetrics.registerFont(TTFont('DVS-B',fontbold));pdfmetrics.registerFontFamily('DVS',normal='DVS',bold='DVS-B')
NAVY=HexColor('#152b3b');BLUE=HexColor('#186b82');GREY=HexColor('#566878');LIGHT=HexColor('#eef3f2');GOLD=HexColor('#bf8a43')
S=getSampleStyleSheet()
S.add(ParagraphStyle(name='BigTitleC',parent=S['Title'],fontName='DVS-B',fontSize=21,leading=28,textColor=NAVY,spaceAfter=18))
S.add(ParagraphStyle(name='HeadC',fontName='DVS-B',fontSize=14.5,leading=20,textColor=NAVY,spaceAfter=12,spaceBefore=4))
S.add(ParagraphStyle(name='SubC',fontName='DVS-B',fontSize=10.3,leading=15,textColor=BLUE,spaceBefore=9,spaceAfter=7))
S.add(ParagraphStyle(name='BodyC',fontName='DVS',fontSize=9,leading=14.4,textColor=NAVY,spaceAfter=10))
S.add(ParagraphStyle(name='SmallC',fontName='DVS',fontSize=7.4,leading=11.5,textColor=GREY,spaceAfter=7))
S.add(ParagraphStyle(name='CodeC',fontName='Courier',fontSize=7.6,leading=11,textColor=NAVY,spaceAfter=9))
S.add(ParagraphStyle(name='CenterC',fontName='DVS',fontSize=9,leading=14,textColor=NAVY,alignment=TA_CENTER))

# page header+footer; move to bottom width safer

def on_page(c,doc):
 c.setStrokeColor(HexColor('#c7d3d7'));c.setLineWidth(.5);c.line(38,45,574,45)
 c.setFont('DVS',7);c.setFillColor(GREY);c.drawString(38,30,'JOSHUA by paceval  |  November 2026  |  Experimental research')
 c.drawRightString(574,30,f'{doc.page}')

doc=SimpleDocTemplate(str(OUT),pagesize=(612,792),rightMargin=40,leftMargin=40,topMargin=37,bottomMargin=63,title='JOSHUA: the paceval Chess Research Engine: Linux Self-Play and Mathematical Search Graphs',author='paceval research demonstration',subject='Real local paceval C++ batch evaluation, complete limited-depth chess self-play and independent checks')
ST=[]
def P(t,style='BodyC'):ST.append(Paragraph(t,S[style]))
def H(t):P(t,'HeadC')
def sub(t):P(t,'SubC')
def caption(t):P(t,'SmallC')
def page():ST.append(PageBreak())
def img(name,width=7.12):
 p=F/name
 if not p.exists():raise FileNotFoundError(p)
 from PIL import Image as PIL
 im=PIL.open(p);w,h=im.size;ST.append(Image(str(p),width=width*inch,height=width*h/w*inch));ST.append(Spacer(1,7))
def pair(a,b,width=3.37):
 def i(p):
  from PIL import Image as PIL
  p=F/p;x,y=PIL.open(p).size
  return Image(str(p),width=width*inch,height=width*y/x*inch)
 t=Table([[i(a),i(b)]],colWidths=[3.5*inch,3.5*inch]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),5)]));ST.append(t)
def tbl(data,widths=None):
 rows=[[Paragraph(str(v),S['SmallC']) for v in row] for row in data]
 t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#dce8e8')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor('#f7faf9')]),('GRID',(0,0),(-1,-1),.35,HexColor('#d7dddd')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));ST.append(t);ST.append(Spacer(1,9))
def code(s):ST.append(Preformatted(s,S['CodeC'],maxLineLength=92))

# Cover
P('JOSHUA: the paceval Chess Research Engine','BigTitleC')
P('Full-width limited-depth chess self-play with executable mathematical decision graphs','HeadC')
img('JOSHUA_Chess_Research_Cover_2400x1200.png',width=7.1)
P('<b>Executable research edition, 15 November 2026.</b> Linux / C++17 / local paceval Mathematical Engine. Two evaluation models, automatic White and Black decisions, persistent feature graphs and batched min/max reductions.','BodyC')
P('This document reports measured, reproducible execution of a fixed, transparent mathematical kernel. It does not claim professional chess-playing strength, a solved game, deployment qualification, or improvements over Stockfish or Leela Chess Zero.','SmallC')
P('<b>Project name:</b> JOSHUA is named in tribute to the fictional computer in the film <i>WarGames</i>, which inspired this project. The research engine is independent and not affiliated with the film or its owners. In the present release JOSHUA only plays against another instance of its own move selector.','SmallC')
P('<b>Local paceval only.</b> No MCP server requests and no remote calculation dependencies. The compatible shared runtime is supplied separately and not included in the archive.','SmallC')
page()
# Summary
H('1. Executive summary and verified outcomes')
P('The program starts with a standard or user-supplied FEN, enumerates <b>every legal move</b> within a user-selected finite search depth, evaluates all distinct numerical feature vectors through persistent local paceval graphs, and performs all grouped min/max reductions through additional paceval graphs. It chooses the maximizer (White) or minimizer (Black) and repeats the procedure after applying the chosen move.')
tbl([['Observed item','Verified depth-3 auto-selfplay'],['Automatically played half-moves',str(len(R))],['Local paceval graph objects (including API layout probes)',str(E['paceval_graphs_created'])],['Graph-point evaluations',str(E['paceval_graph_point_evaluations'])],['Local paceval batch calls',str(E['paceval_batch_calls'])],['Total elapsed seconds (observed)',f"{E['elapsed_seconds']:.6f}" if isinstance(E['elapsed_seconds'],float) else str(E['elapsed_seconds'])],['Search mode','Complete fixed-depth tree, no alpha-beta pruning'],['Remote MCP used','No']], [3.15*inch,3.85*inch])
P('The independent checker verifies the sequence of chess positions, the origin and destination of each selected move, the side-to-move ordering, the root ranking and the output timing invariants. The original source test suite also verifies known starting-position Perft counts and special-move behavior.')
P('The current console executable additionally identifies the <b>moving piece by its German name</b>, origin and destination, and conventional English SAN. For example, a separate verified depth-2 self-play logged: <b>JOSHUA BEST WHITE b1c3 | Figur=Springer (Pferd) b1 -&gt; c3 | SAN=Nc3</b>. This ensures a human reader can identify the actual chess piece without interpreting UCI coordinates. The new CSV fields preserve the moving piece, SAN, origin, destination, capture and promotion; the historical timing table in Section 11 remains historical evidence from its original run.')
P('The root decision is optimal only with respect to the chosen <b>finite-depth, simplified heuristic</b>. It is not a game-theoretic proof of the best chess move.')
page()
# Boards
H('2. Understanding the decision on a real chessboard')
P('The first experiment starts from the normal chess initial position. White has 20 legal choices. The current V2 heuristic and exhaustive depth-3 tree choose <b>1. Nc3</b> (UCI <b>b1c3</b>). The following figures are rendered directly from the FEN states written by the executable, not from manually invented arrangements.')
pair('01_initial_position.png','02_white_b1c3.png',width=3.18)
caption('Left: normal initial position. Right: after the evaluated first move b1c3. The highlighted squares are the source b1 and destination c3. The board orientation is White below, Black above.')
P('For this move, the program generated 9,323 search nodes: the initial root, 20 first moves, 400 second moves and exactly 8,902 third-move leaves. These are full legal sequences from the initial position, not a sample of two candidate moves.')
page()
H('3. Black chooses its response to the actual position')
P('After White plays b1c3, it is Black to move. The program builds a completely new depth-3 tree from the resulting position. Black chooses <b>1... Nc6</b> (UCI <b>b8c6</b>) under the same simplified evaluation model. The new position now has White to move.')
pair('02_white_b1c3.png','03_black_b8c6.png',width=3.18)
caption('Two consecutive states from the executed console trace. The right board highlights b8 to c6; all remaining pieces retain their appropriate places.')
P('The initial Black reply tree contained 10,216 nodes and 9,755 terminal-horizon leaves. It required its own batch evaluations, whereas all 20 mathematical feature graphs created before the game remained reusable.')
P('Every new turn keeps all legal replies as alternatives. The demonstration does not discard surprising defensive moves by arbitrarily selecting only two candidate branches.')
page()
H('4. Optional opening scenario: the explicitly requested 1. e4')
P('For comparison, a separate executed run uses <b>--first-move e2e4</b>. This input is explicitly forced by the user and is <b>not</b> claimed as a move chosen by the engine. The first search of this run begins with Black to move after 1. e4 and selects <b>1... Nf6</b> (g8f6).')
pair('04_forced_e2e4.png','05_black_g8f6.png',width=3.18)
caption('Left: correctly reconstructed position after 1. e4. Right: the legal Black reply g8f6, reconstructed directly from the independent run. The rook, kings, other knights and castling rights remain in their correct states.')
P('The purpose of a forced opening is reproducibility and controlled A/B comparison. Without this option, White and Black always choose their own best-scoring moves under the research algorithm.')
page()
# architecture
H('5. Architecture: chess rules versus mathematical graphs')
img('10_architecture.png',width=7.05)
P('The C++ layer owns legal move generation, FEN transitions, finite tree construction, history bookkeeping, grouping, input validation and I/O. The <b>real local paceval library</b> owns the evaluation of explicit formulas, the 20 persistent mathematical feature and scoring graphs, and the dynamically generated min/max reduction expressions. All numerical graph outputs are checked against a separate native arithmetic calculation.')
P('In a full search tree the same numeric feature vector may occur at many different leaves. We can evaluate each such vector once. This is <b>feature-vector memoization</b>, not a game-state transposition table; positions with different castling or repetition histories must not be treated as the same game state.')
page()
# math
H('6. Mathematical evaluation graphs: explicit expressions')
P('The current demonstrator deliberately uses transparent inputs rather than a proprietary trained network. Nineteen input values describe piece counts, central-square occupancy, development, pawn advancement, a minimal king-zone indicator and a constant bias input.')
code('V1_SCORE = 100*(wp-bp) + 320*(wn-bn) + 330*(wb-bb)\n         + 500*(wr-br) + 900*(wq-bq)\n\nV2_SCORE = V1_SCORE + 13*(wc-bc) + 17*(wd-bd)\n         + 3*(wa-ba) + 18*(wk-bk)')
P('These expressions are printed in standard mathematical notation; the actual persistent SDK expressions include the corresponding parentheses and names. The V1 and V2 SCORE graphs are part of a total set of ten computations per model, including material and other component scores, finite sanity margins and sensitivities.')
P('The scores are expressed from White\'s perspective. White maximizes the propagated value, while Black minimizes the propagated value. A terminal checkmate is assigned a large signed value and a draw is assigned zero. Mate score magnitudes are separate from the heuristic scoring domain.')
code('MINMAX_3 = (v0 min v1 min v2)    # Black to move\nMINMAX_3 = (v0 max v1 max v2)    # White to move\n\nNode_value = paceval_MIN_OR_MAX(child_value_0, ..., child_value_k)')
P('The number k of legal alternatives is determined by the actual position, not a fixed two-move truncation. Each distinct pair (player to move, k) uses a persistent reduction graph that is reused for other nodes with the same fanout.')
page()
H('7. How a full-depth tree becomes grouped paceval batches')
P('The first depth-3 search from the starting position has exact ply counts 1, 20, 400, 8,902. The engine first calculates all leaf input features; then it deduplicates identical <b>19-component mathematical input vectors</b>. Only 154 different vectors were needed for all 8,902 leaves in this initial experiment. All 20 persistent mathematical graphs were evaluated for the 154 unique vectors.')
tbl([['Stage','Data / method'],['Leaf input generation','One 19-variable vector per nonterminal leaf; each vector checked'],['Input-vector deduplication','Map identical numeric vectors to one ID; does not merge chess states'],['Maximum configured batch','1 to 65,536 rows; demo used 8,192 upper row limit'],['Multi-graph output','20 graph values per unique vector, produced in one grouped API call when rows fit'],['Bottom-up reductions','Group identical min/max arity at each depth and process many parent nodes as a single batch'],['Independent verification','Every used SCORE result and every min/max reduction checked numerically']], [2.35*inch,4.65*inch])
P('The 65,536 row maximum is a safety bound in this host application, <b>not a published universal maximum of the paceval SDK</b>. The SDK can impose other limits depending on process memory, formula complexity and runtime settings.')
page()
H('8. Why the graph can be much smaller than the move tree')
img('07_feature_reuse.png',width=6.9)
P('The search tree must preserve the full chess position and path-dependent rules. A feature score does not: it depends only on the extracted numerical values. Consequently several different positions can map to the same evaluation input.')
P('This reduces repeated numerical evaluation. It does not prove the move tree can be replaced by 154 fully equivalent chess states. That distinction is especially important for en passant, castling, checkmate, fifty-move claims and repetition rules.')
page()
H('9. The back-propagated root score')
img('08_first_turn_rankings.png',width=6.95)
P('At the root, each legal move has already received its backed-up response value, taking the opponent\'s counterplay into account within the fixed search horizon. The root player chooses the largest White score if White is to move and the smallest White score if Black is to move.')
img('11_minmax_example.png',width=6.8)
caption('The numbers and move labels in the example diagram come from the actual first-turn root ranking; the diagram displays a selected subset for readability. The executable evaluated all 20 legal root choices, not only these three.')
page()
H('10. Full-width chess tree depth and correctness')
img('09_perft_depths.png',width=6.9)
P('Known complete perft counts for the standard initial position are 20, 400, 8,902 and 197,281 at depths 1 through 4. The original move generator passed these exact regression tests. In the separate depth-4 stress run the executable generated <b>206,604 total nodes</b> and <b>197,281 leaves</b> in the root search tree.')
P('The generated perft counts test legal move generation, not chess playing strength. Perft does not imply that a position can be won or drawn.')
page()
H('11. Actual self-play results: recorded moves and time stamps')
P('These values are the direct console measurements from the Linux execution of C++17 code using the local paceval shared library and the same compile configuration. They are observational run times, not forecasts for other hardware.')
rows=[['Halfmove','Side','Selected UCI','Decision at +seconds','Tree nodes','Score (white cp)']]
for r in R:rows.append([r['halfmove'],r['side'],r['chosen_uci'],f"{float(r['decision_s']):.3f}",f"{int(r['tree_nodes']):,}",f"{float(r['white_score_cp']):+.0f}"])
tbl(rows,[.75*inch,.7*inch,1.05*inch,1.45*inch,1.4*inch,1.65*inch])
img('06_measured_stage_durations.png',width=6.85)
P('The program prints absolute seconds since process start, including graph creation/lookup and batch execution. The aggregate chart reports time spent generating the complete tree, preparing and evaluating leaf batches, and building/evaluating the min/max reductions. No extrapolation of engine throughput or energy savings is implied.')
page()
H('12. Depth-4 stress test: observed trace')
P('A single full-width depth-4 root search was executed. Exactly 197,281 leaf nodes were enumerated from the normal initial board. The run was not limited to two candidate moves, and the complete internal minimax reduction was performed by paceval batch graphs.')
tbl([['Actual measurement','Observed value'],['Root tree total nodes',f"{int(D4['tree_nodes']):,}"],['Leaf nodes',f"{int(D4['leaf_nodes']):,}"],['Unique numerical feature vectors',str(D4['unique_feature_vectors'])],['Batched min/max node comparisons','9,319'],['New arity-specific reduction graphs',str(D4['new_paceval_reduction_graphs'])],['Tree generation stage',f"{float(D4['tree_generation_s']):.6f} s"],['Leaf deduplication and evaluation stage',f"{float(D4['score_batch_s']):.6f} s"],['Min/max reduction stage',f"{float(D4['reduction_s']):.6f} s"],['Decision reached after startup',f"{float(D4['decision_s']):.6f} s"],['Observed best model-V2 move',str(D4['chosen_uci'])+' (1. Nc3)']], [3.55*inch,3.45*inch])
P('These times are from one measured Linux run. They are not a matched benchmark against Stockfish, Leela, native optimized search, or any other system, and do not demonstrate a paceval speedup. The full-width tree generation dominates this particular implementation.')
page()
H('13. Validation, limitations and falsifiable conclusions')
P('<b>Direct technical checks:</b> exact starting-position perft regressions; executable SDK layout probe; finite scalar result validation; native independent V1/V2 score checks; independent min/max results checked for every computed node; output-record FEN transitions and rank ordering; CTest integration; UTF-8 text and relative README link validation.')
P('<b>Important limitations:</b> The leaf score uses a deliberately small handcrafted evaluation and is not trained against high-level chess play. In-tree threefold repetition is not fully path-adjudicated. The program permits a research-policy claim at the root for drawn positions. It uses a complete unpruned tree to a small depth and can be overwhelmed by deeper search. A capped 6 additional quiescence plies are implemented only in the separate inherited search prototype, not in this full-width self-play mode. A configured half-move limit can stop a game before it finishes.')
P('<b>Scientific outcome:</b> It is demonstrated that a complete finite chess search can be coupled to persistent paceval evaluation graphs and batched dynamic min/max graph reductions, with both sides selecting a move automatically. This is an integration result, not a result about improved Elo or the solved value of chess.')
page()
H('14. Future opponents: Stockfish and Leela Chess Zero')
P('Stockfish 19, released on 5 September 2026, uses a highly optimized neural evaluation (NNUE) and selective alpha-beta search. Its search includes quiescence and many advanced pruning mechanisms. Leela Chess Zero uses neural value/policy models in a Monte Carlo tree search framework, with batched inference on supported hardware [1-4].')
P('<b>Current mode:</b> JOSHUA controls both colors; there is no UCI opponent adapter, no external-engine process, no network opponent, no MCP server and no Stockfish/Lc0 binary or third-party source in this release. Stockfish and Leela Chess Zero are research context only. A future experimental edition may implement a UCI bridge and optional match runner once dependencies, licenses, reproducible settings and proper evaluation are available.')
P('The present program intentionally does not claim to recreate either engine. It is a transparent experimental baseline in which the local paceval numerical role can be demonstrated and audited. A meaningful strength comparison would require UCI play, controlled time conditions, opening suites, both colors, many games, and statistical confidence intervals.')
P('A useful future experiment would replace this simple V2 heuristic with an explainable, automatically generated function or a calibrated network exported as a paceval graph, while implementing a strong legal search layer with transposition-safe state handling. All gains would need measured ablation studies.')
sub('Selected references')
P('[1] Stockfish 19 release, 2026-09-05, https://stockfishchess.org/blog/2026/stockfish-19/','SmallC')
P('[2] Stockfish engine search sources, https://github.com/official-stockfish/Stockfish/blob/master/src/search.h','SmallC')
P('[3] Stockfish NNUE technical documentation, https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue.html','SmallC')
P('[4] Leela Chess Zero architecture overview, https://lczero.org/dev/overview/','SmallC')
P('[5] paceval developer interface, https://paceval.com/developers/','SmallC')
page()
H('15. Reproducibility and package contents')
P('JOSHUA is currently self-play only. Stockfish and Leela Chess Zero are not included as opponents and are not invoked by any released executable. Any later cross-engine match mode must be developed, reviewed and separately validated.')
P('The GitHub package includes the exact C++ source, original paceval SDK interface files, CMake setup, the deterministic result CSVs, measured console transcript, Python verification scripts, illustrative chessboards reconstructed from recorded FEN states, mathematical graphs and the present English whitepaper.')
sub('Linux build (compatible licensed local paceval library required)')
code('cmake -S src -B build \\\n  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so\ncmake --build build -j4\nctest --test-dir build --output-on-failure\n\n./build/joshua --depth 3 --plies 8 --batch-rows 8192 \\\n    --output results/new_run\n\n./build/joshua --first-move e2e4 --depth 3 --plies 8 \\\n    --output results/opening_e4')
P('In both runs, JOSHUA controls every automatically selected move. The first command lets White and Black select all moves automatically; the second intentionally forces the very first move to e2e4 and records that it was not engine-selected. Use --help for all flags. The maximum search depth supported by this demonstrator is four full-width half-moves per turn; a configurable node-count budget protects the process.')
P('All paths in this publication refer to the separately tested research package. The external executable shared library is not included and must be supplied under its applicable terms. No remote paceval MCP communication occurs.')
P('Release scope: computational research only. A deeper or faster chess system requires independently validated search heuristics, more accurate evaluation, draw-history handling and adversarial play tests.')

# Render

doc.build(ST,onFirstPage=on_page,onLaterPages=on_page)
print('WHITEPAPER_READY',OUT,OUT.stat().st_size)
