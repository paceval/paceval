#!/usr/bin/env python3
"""One consolidated English scientific whitepaper for JOSHUA V4 (ReportLab)."""
from pathlib import Path
from xml.sax.saxutils import escape
import csv,json,math
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, Preformatted, HRFlowable
from reportlab.lib.units import inch
from PIL import Image as PIL
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'JOSHUA_Chess_Research_Whitepaper_EN.pdf'
metrics=json.loads((ROOT/'formulas/training_metrics.json').read_text())
graphs=list(csv.DictReader(open(ROOT/'formulas/v4_graph_manifest.csv')))
trace=list(csv.DictReader(open(ROOT/'results/v4_alphabeta_10ply/selfplay_timeline.csv')))
assert len(trace)==10 and len(graphs)==13
fm='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';fb='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',fm));pdfmetrics.registerFont(TTFont('DV-Bold',fb))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold')
navy=colors.HexColor('#14283b');teal=colors.HexColor('#197a85');muted=colors.HexColor('#526577');gold=colors.HexColor('#b8844e')
styles={
 'title':ParagraphStyle('title',fontName='DV-Bold',fontSize=22,leading=29,spaceAfter=11,textColor=navy),
 'subtitle':ParagraphStyle('subtitle',fontName='DV',fontSize=11.5,leading=17,spaceAfter=13,textColor=muted),
 'h1':ParagraphStyle('h1',fontName='DV-Bold',fontSize=15.5,leading=21,spaceBefore=13,spaceAfter=8,textColor=navy,keepWithNext=True),
 'h2':ParagraphStyle('h2',fontName='DV-Bold',fontSize=11.5,leading=16,spaceBefore=11,spaceAfter=5,textColor=teal,keepWithNext=True),
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.1,leading=14.1,spaceAfter=7,textColor=navy),
 'small':ParagraphStyle('small',fontName='DV',fontSize=7.5,leading=11,spaceAfter=6,textColor=navy),
 'caption':ParagraphStyle('caption',fontName='DV',fontSize=7.5,leading=10.4,spaceAfter=9,textColor=muted,alignment=TA_CENTER),
 'formula':ParagraphStyle('formula',fontName='DV',fontSize=9.2,leading=15,spaceAfter=8,textColor=navy,leftIndent=12),
 'code':ParagraphStyle('code',fontName='DV',fontSize=7.4,leading=10,spaceAfter=5,textColor=navy),
 'bib':ParagraphStyle('bib',fontName='DV',fontSize=7.6,leading=11.2,spaceAfter=5,textColor=navy,wordWrap='CJK'),
}
doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=48,bottomMargin=44,author='paceval Research / JOSHUA',title='JOSHUA V4 - Trained Neural Support with the Local paceval Mathematical Engine')
W=A4[0]-84;story=[]
def para(s,style='body'):
 story.append(Paragraph(s,styles[style]))
def h1(s):para(escape(s),'h1')
def h2(s):para(escape(s),'h2')
def text(s):para(escape(s),'body')
def formula(s):para(escape(s),'formula')
def caption(s):para(escape(s),'caption')
def add_image(filename,width=W,caption_text=None):
 f=ROOT/'figures'/filename
 with PIL.open(f) as im: rw,rh=im.size
 im=Image(str(f),width=width,height=width*rh/rw)
 im.hAlign='CENTER';story.append(im)
 if caption_text:caption(caption_text)
def tab(header,rows,widths=None):
 t=Table([[Paragraph(escape(str(c)),styles['small']) for c in header]]+[[Paragraph(escape(str(c)),styles['small']) for c in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dceaf0')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f8fa')]),('LINEBELOW',(0,0),(-1,0),.6,teal),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
 story.append(t);story.append(Spacer(1,9))
def footer(c,document):
 c.saveState();c.setFont('DV',7);c.setFillColor(muted);c.drawString(42,25,'JOSHUA V4 | Local paceval SDK | Scientific research demonstrator | 15 November 2026');c.drawRightString(A4[0]-42,25,str(document.page));c.restoreState()

add_image('JOSHUA_Chess_Research_Cover_2400x1200.png',W)
para('JOSHUA V4: Trained Neural Support for a Mathematical Chess Research Engine','title')
para('Single consolidated English scientific whitepaper | Linux C++ | Original local paceval SDK | Reproducible test evidence','subtitle')
para('Research release: 15 November 2026. JOSHUA plays White and Black against itself. No remote MCP server, Stockfish or Leela inference is used.','small')
para('<b>Executive result.</b> A genuinely trained 48–12–1 residual network is now executed in 13 reusable local paceval graphs alongside the existing V3 mathematical position score. In the fixed held-out synthetic dataset, residual mean absolute error against JOSHUA’s own shallow search teacher decreased from 123.04 cp (V3 only) to 105.06 cp (V4). This measures imitation of a weak internal teacher, not stronger chess play. A separate 110-position audit verified all neural graph results with 85-decimal-digit reference arithmetic.','body')
para('<b>Falsifiable core claim.</b> At an equal fixed search depth with quiescence disabled, full-width graph-search and Alpha-Beta modes produce the same root move scores and selected moves. A three-halfmove V4 comparison passed 62 independent root-move score checks.','body')
story.append(PageBreak())

h1('1. Research question and scope')
text('The research question is whether explicitly defined chess evaluation functions and an automatically exported neural network can be combined in one transparent, reusable mathematical execution layer. Chess is a practical stress test because every evaluation takes place inside a rapidly growing tree of legal moves. The experiment is not an attempt to solve chess and does not claim playing strength comparable with Stockfish or Leela Chess Zero.')
h2('What is included, what remains separate')
tab(['Responsibility','Actual implementation'],[
 ['Legal move generation, castling, en passant, promotion','Native C++ chess rules; independently checked with perft'],
 ['Fixed-depth complete game tree','C++ research mode; internal decisions via paceval min/max graphs'],
 ['Selective search / Alpha-Beta control','C++ iterative deepening with transposition table'],
 ['Manual classical evaluation','Persistent paceval SCORE and component graphs (V1/V2/V3)'],
 ['Trained neural support','Twelve sigmoid paceval graphs and one fused residual graph'],
 ['Training and optimizer','Reproducible Python/scikit-learn supervised regression'],
 ['High precision','Independent Python/mpmath audit; not paceval training']
],[185,W-185])
add_image('v4_02_architecture.png',W,'Figure 1. Functional boundaries are explicit. The engine does not try to represent chess legality as a single neural formula.')

h1('2. Why introduce a neural network?')
text('V3 is a deterministic, hand-designed linear score. It compresses millions of different positions to 32 handcrafted numbers. This is useful for transparency and stable paceval batching, but it cannot distinguish two boards with identical feature vectors. A small neural model adds nonlinear interactions among the features; it does not recover information the feature extractor discarded. We therefore also add sixteen board-derived tactical proxy inputs in V4.')
text('The network is deliberately an additive support signal rather than a replacement for chess rules, material accounting or a final search. Its correction is clipped to ±150 centipawns. The cap limits single-model influence but cannot prevent poor chess decisions. Strong engines such as Stockfish use specialized NNUE representations designed for sparse, incrementally updated inputs. Our dense V4 experiment is not an NNUE reproduction.')

h1('3. Chessboard examples: only real legal positions')
add_image('v4_01_legal_board_sequence.png',W,'Figure 2. These three positions come directly from the recorded JOSHUA V4 self-play FEN chain. Arrows indicate actual legal moves 1.Nc3 and 1...Na6. White is at the bottom; the a8 square is light.')
text('The first move, Nc3, means that the White knight goes from b1 to c3; Na6 means that the Black knight goes from b8 to a6. SAN (Standard Algebraic Notation) uses N for knight because K already means king. UCI notation, such as b1c3, specifies both source and destination squares.')
text('All ten moves in the recorded V4 game have been verified against their before/after FEN records. Each computation begins from the actual current position, not from an idealized board drawn independently from the search data.')

h1('4. Classical evaluation: explicit mathematical graphs')
text('For each side c (White w, Black b), let p,n,B,r,q denote pawn, knight, bishop, rook and queen counts. In centipawn units:')
formula('E_material = 100(wp−bp) + 320(wn−bn) + 330(wB−bB) + 500(wr−br) + 900(wq−bq).')
text('This graph has 61 characters in the actual paceval source. The coefficients express a fixed material convention, not values learned from data. Position and pawn activity are scored separately so their assumptions can be inspected.')
formula('E_center = wc−bc;     E_development = wd−bd;     E_advance = wa−ba;     E_king = wk−bk.')
formula('E_structure = −16(wdoub−bdoub) − 12(wisolated−bisolated) + 22(wpassed−bpassed) + 28(wbpair−bbpair).')
formula('E_activity = wpsq−bpsq;     E_shelter = 9(wshield−bshield);     E_tempo = 7t.')
formula('E3 = E_material + 13E_center + 17E_development + 3E_advance + 18E_king + E_activity + E_structure + E_shelter + E_tempo.')
text('Why these graphs? Material accounts for durable piece advantages; center and development are opening activity proxies; pawn structure penalizes doubled and isolated pawns while rewarding passed pawns and bishop pairs; piece-square activity captures limited square preferences; king shelter measures friendly pawn coverage; tempo distinguishes whose turn it is. They are heuristics with explicit units and assumptions, not guarantees of game outcome.')
text('The exact current V3 SCORE expression occupies 235 characters; the old V1 SCORE occupies 61, and the V2 SCORE 106. All legacy graph strings are preserved in the source. V4 does not modify their definitions.')

h1('5. Trained neural support: the mathematics')
text('The input is x(s) in R^48: the unchanged V3 feature vector (32 values) followed by 16 additional inputs. Each input is normalized with training-set statistics only; sigma is the scale derived from the training subset, not a learned neural parameter.')
formula('z_i(s) = [x_i(s) − μ_i] / σ_i,  i=1,...,48.')
formula('a_j(s) = b_j + Σ_{i=1}^{48} W_{ji} z_i(s),  j=1,...,12.')
formula('h_j(s) = 1 / [1 + exp(−a_j(s))].')
formula('R(s) = 100 [c + Σ_{j=1}^{12} v_j h_j(s)].')
formula('E4(s) = E3(s) + clip(R(s), −150, +150).')
text('W, b, v and c are frozen, trained coefficients saved as exact decimal literals in the versioned graph files. Only the board features are variable inputs. JOSHUA exports one symbolic formula for each sigmoid neuron, then a separate final graph that combines the twelve hidden outputs with the paceval V3 baseline. The technique follows the user-supplied paceval neural-expression whitepaper, especially its intermediate-layer factorization proposal (pages 7–11).')
text('The local paceval output graph uses the exact clipping identity clip(R,−C,C) = [|R+C| − |R−C|]/2, with C=150, avoiding reliance on an ambiguous conditional expression. No function is claimed to provide calibrated winning probability.')

h2('The sixteen additional inputs and why they matter')
tab(['Feature pair','Mathematical interpretation / purpose'],[
 ['wmob, bmob','Pseudo-legal move counts for each side, a low-cost activity proxy'],
 ['wcaps, bcaps','Pseudo-legal capture counts, potential tactical contact'],
 ['wcheck, bcheck','Indicator for the king being currently in check'],
 ['whanging, bhanging','Pieces attacked without a same-side defender'],
 ['wattacked, battacked','All pieces under attack, including defended pieces'],
 ['wqueenThreat, bqueenThreat','Queens presently attacked'],
 ['wrookThreat, brookThreat','Rooks presently attacked'],
 ['wkingDanger, bkingDanger','Attacked neighboring squares around each king']
],[175,W-175])
text('For mobility and captures the alternate side is evaluated counterfactually, so these are deliberately pseudo-legal features, not claims that both players can move simultaneously. Threat counts use actual geometric attack detection. The spatial information remains heavily compressed and cannot encode complex multi-move tactics on its own.')

h1('6. Graph representations and generated function lengths')
text('The graph exporter produced twelve 48-input hidden formulas and one fused output. The complete exact source strings are in formulas/v4_graph_expressions.tsv and are compiled in the C++ executable through src/v4_graph_formulas.h. The following numbers refer to string character counts, not to internal optimized execution-node counts:')
tab(['Graph','Input variables','Exact length'],[[r['graph'],r['input_variables'],r['formula_characters']] for r in graphs],[220,120,W-340])
text(f"Total exported V4 expression length is {sum(int(g['formula_characters']) for g in graphs):,} characters. The largest individual neural formula contains {max(int(g['formula_characters']) for g in graphs):,} characters. Graph creation is performed once at startup; the same handles are reused across many board positions. The final graph also receives an input named base, which is the already executed V3 SCORE graph result.")
add_image('v4_04_graph_lengths.png',W,'Figure 3. Exact formula-string lengths of the compiled V4 graph set, computed from the actual generated manifest.')

h1('7. Reproducible training and the teacher problem')
text('Training positions were generated by deterministic, seeded legal chess games from the starting position, with diverse exploratory moves. The label is the V3 search score after two further legal halfmoves, obtained from a native reference recursion. For each position, a residual target is formed by subtracting the static V3 score and clipping that difference to [-220,+220] cp.')
formula('y(s) = clip[V3_depth2(s) − E3(s), −220, +220].')
text('Training uses a single-hidden-layer logistic MLP regressor, standardized inputs, L2 regularization and a deterministic random seed. Candidate hidden widths 12 and 16 and two regularization strengths were compared using only held-out validation games. The architecture was selected before test-set evaluation. A native C++ teacher is intentionally independent from paceval, so it does not merely reproduce a paceval formula during validation.')
tab(['Subset','Whole games','Position rows'],[
 ['Train',metrics['train_game_count'],metrics['train_rows']],
 ['Validation',metrics['validation_game_count'],metrics['validation_rows']],
 ['Test (no model selection)',metrics['test_game_count'],metrics['test_rows']]
],[170,130,W-300])
text('Splitting by complete game identity avoids leakage from near-neighbor positions of the same played line. However, all games are generated by a synthetic move policy and therefore do not approximate the distribution of master-level chess. The teacher itself inherits all V3 weaknesses. It can be wrong in both tactical and strategic judgments.')
text('The inherited V3 bias input is constant in these samples and becomes a zero-valued normalized input; it contributes no extra information to the neural model. The scikit-learn L-BFGS fitting procedure was stopped at its preset 280-iteration limit for the tried architectures, so optimization convergence is not claimed. The recorded fitted coefficients were nonetheless selected on held-out validation data and are fully reproducible in the stated environment.')

h1('8. Measured results on held-out synthetic games')
tab(['Quantity','Observed value'],[
 ['V3 test MAE relative to internal teacher',f"{metrics['test_zero_residual_mae_cp']:.3f} centipawns"],
 ['V4 test MAE relative to internal teacher',f"{metrics['test_mae_residual_cp']:.3f} centipawns"],
 ['V4 training MAE',f"{metrics['train_mae_residual_cp']:.3f} centipawns"],
 ['V4 validation MAE',f"{metrics['validation_mae_residual_cp']:.3f} centipawns"],
 ['Held-out test rows',metrics['test_rows']],
 ['Selected hidden neurons',metrics['model_hidden_units']],
 ['Model regularization parameter',metrics['alpha']]
],[310,W-310])
add_image('v4_03_holdout_error.png',W,'Figure 4. This is model imitation error relative to JOSHUA’s internal weak teacher, not an Elo gain or an outcome against Stockfish.')
text('The gap between the training and test errors signals a serious generalization limit. The correction may still harm real chess decisions. The experiment establishes technical integration and measurable reduction of teacher imitation error, not superiority to V3 in head-to-head chess.')

h1('9. Why paceval batching matters')
add_image('v4_06_batch_graph_reuse.png',W,'Figure 5. Batch reuse of the twelve hidden graphs on many position vectors, followed by a fused paceval graph. Graph-creation cost is paid once per stable model.')
text('The full-width research mode first reduces repeated feature vectors, evaluates the V3 classical graph set via paceval_dGetMultipleComputationsResultsExt, then evaluates all twelve hidden graphs with the same local API. The fused output graph is evaluated over the resulting layer values using paceval_dGetComputationResultExt. Each iteration reuses persistent handles, with optional batches of up to 65,536 rows configured by the software (not an optimality claim).')
text('The Alpha-Beta mode has a different data dependency: it requires leaf values immediately to decide whether a branch may be pruned. V4 therefore uses on-demand local paceval calls, cached for repeated feature vectors. Root min/max reduction still goes through a paceval graph; internal Alpha-Beta inequalities are implemented by C++. This is a deliberate, documented boundary rather than a claim that the whole engine is compiled into one graph.')

h1('10. Exact Minimax decisions: illustrated with real results')
formula('V(s,d) = max over a in L(s) [−V(T(s,a),d−1)] when the score is from the side-to-move perspective.')
text('In JOSHUA the stored root values are conventionally expressed from White’s perspective, so White takes max and Black takes min. At the fixed full-width horizon, every legal move is included. In the Alpha-Beta mode, mathematical bounds allow some branches to be excluded without changing the exact fixed-horizon result, as long as the same evaluation model and terminal rules are used.')
add_image('v4_07_actual_minimax_root.png',W,'Figure 6. This root comparison is generated from the actual V4 research-mode root_move_rankings.csv, not illustrative or invented values.')
text('The three-halfmove search comparison across V4 full-width and V4 Alpha-Beta checked all 62 root move scores, with identical selected moves and identical values. This does not compare searches with quiescence activated, which can change the horizon semantics.')

h1('11. Actual English self-play output and timings')
text('A separate local Linux test completed ten halfmoves at depth 2 with V4 as the evaluator. Each chosen move has a SAN description and before/after FEN. Runtime numbers depend on hardware and are not advertised as general engine speed or a benchmark against Stockfish.')
tab(['Ply / side','SAN','UCI','Elapsed from launch (s)'],[[r['halfmove']+' / '+r['side'],r['chosen_san'],r['chosen_uci'],f"{float(r['decision_s']):.3f}"] for r in trace],[90,80,100,W-270])
add_image('v4_05_real_selfplay.png',W,'Figure 7. Actual V4 White-perspective heuristic scores across the ten halfmoves. Scores at different positions are not directly comparable as engine-strength evidence.')

h1('12. Independent validation')
text('Chess legality is tested with established perft values, reversible board make/unmake, en passant, promotions, castling, FEN-chaining, SAN labels and a separate CSV auditor. The original V3 formulas and 32-source feature extraction are preserved for model selection 3.')
text('The V4 numerical release audit separately evaluated 110 held-out test positions with the local original SDK. It executed all twelve hidden formulas and the fused graph and compared outputs with an independent native C++ network. An 85-decimal-digit mpmath calculation reconstructed every hidden sigmoid, output weight, residual clip and resulting V3-plus-NN value. The largest observed absolute difference was 4.27 × 10^(-13) centipawns, well within the prespecified 5 × 10^(-7) cp acceptance threshold.')
text('The high-precision check establishes numerical agreement for these test inputs. It does not establish semantic correctness of the teacher, certify interval bounds, prove generalization to unseen professional positions, or verify behavior under all possible input values. No untested speedup or win-rate assertions are made.')

h1('13. Competing architectures and a realistic roadmap')
text('Stockfish NNUE is optimized for sparse, incrementally updated input features and low-latency CPU inference. Leela Chess Zero relies on neural policy/value models with a very different search system. Replacing either system with plain text formulas does not automatically improve inference speed, accuracy or practical playing strength. Larger exported networks may produce impractically long expressions unless layers or shared subgraphs are factored.')
text('The next meaningful step is to train on higher-quality teacher labels, e.g. openly available Lichess computer evaluations subject to their licensing and quality checks, with independent held-out positions and no overlapping game history. Extend board representation beyond 48 handcrafted inputs, include direct tactical and policy supervision, and test losses and Elo under controlled hardware and time limits. Investigate incremental feature updates and quantized graph evaluation only after establishing an accuracy baseline. None of these future studies are part of the present executed release.')

h1('14. Reproduction and data provenance')
para('Build:','h2')
para('cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so','code')
para('cmake --build build --target joshua joshua_v4_audit -j','code')
para('ctest --test-dir build --output-on-failure','code')
para('Self-play: ./build/joshua --mode alphabeta --model 4 --depth 2 --plies 10 --no-board --output results/my_game','code')
text('The single ZIP contains the original SDK interface source, C++ engine, generated trained model header, all exact exported formulas, model weights, synthetic dataset generator, training program, split IDs, training metrics, independent high-precision scripts, source board diagrams, real CSV outputs and this single PDF report. The proprietary runtime .so is not redistributed.')

h1('15. Sources and caution on interpretation')
for line in [
 '1. paceval, Conversion of neural networks to closed-form expressions as human-readable mathematical functions (user-supplied PDF, twelve pages; particularly pages 7–11).',
 '2. Stockfish NNUE technical documentation: https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue.html',
 '3. Lichess openly released computer evaluations and games, CC0: https://database.lichess.org/ (NOT used for V4 model training).',
 '4. paceval Mathematical Engine developer information: https://paceval.com/developers/',
 '5. Project-local generated logs, model weights, formula manifest, deterministic teacher positions and independent test scripts (all included in this GitHub archive).'
]:para(escape(line),'bib')
text('Scientific bottom line: The paceval neural-conversion principle works for this trained 48-12-1 support model. The engine is a correct technical research demonstrator within its tested configuration. Evidence for stronger chess play, safe pruning beyond fixed-horizon Alpha-Beta, or advantage over NNUE/MCTS engines has not yet been established.')

doc.build(story,onFirstPage=footer,onLaterPages=footer)
from pypdf import PdfReader
print('Whitepaper',OUT,'pages',len(PdfReader(str(OUT)).pages),'bytes',OUT.stat().st_size)
