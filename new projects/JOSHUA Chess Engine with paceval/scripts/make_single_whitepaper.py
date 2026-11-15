#!/usr/bin/env python3
"""One source-driven report for the JOSHUA 2026 local paceval chess engine."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether,Preformatted,HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import csv,json
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'JOSHUA_Chess_Research_Whitepaper_EN.pdf'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';BFONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf';MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',FONT));pdfmetrics.registerFont(TTFont('DejaVuBold',BFONT));pdfmetrics.registerFont(TTFont('DejaVuMono',MONO))
navy=colors.HexColor('#173546');teal=colors.HexColor('#167d88');gray=colors.HexColor('#51616b');gold=colors.HexColor('#c07d35');light=colors.HexColor('#f0f4f3')
doc=SimpleDocTemplate(str(P),pagesize=A4,leftMargin=43,rightMargin=43,topMargin=57,bottomMargin=53,title='JOSHUA Chess Research Engine | Consolidated Study',author='paceval research demonstrator',subject='Local paceval graphs, alpha-beta, depth-10 controlled validation')
W=A4[0]-86
sty={
 'Title':ParagraphStyle('T',fontName='DejaVuBold',fontSize=24,leading=30,textColor=navy,spaceAfter=16),
 'H1':ParagraphStyle('H1',fontName='DejaVuBold',fontSize=17,leading=22,textColor=navy,spaceBefore=12,spaceAfter=10),
 'H2':ParagraphStyle('H2',fontName='DejaVuBold',fontSize=11.7,leading=15.5,textColor=teal,spaceBefore=13,spaceAfter=6),
 'Body':ParagraphStyle('B',fontName='DejaVu',fontSize=9.1,leading=14.2,textColor=navy,spaceAfter=9),
 'Small':ParagraphStyle('S',fontName='DejaVu',fontSize=8,leading=11.5,textColor=gray,spaceAfter=6),
 'Caption':ParagraphStyle('C',fontName='DejaVu',fontSize=8.0,leading=11.4,textColor=gray,spaceBefore=6,spaceAfter=11),
 'Code':ParagraphStyle('Code',fontName='DejaVuMono',fontSize=7.7,leading=11,textColor=navy,spaceAfter=8),
}
story=[]
def pg(title):
 if story:story.append(PageBreak())
 story.append(Paragraph(title,sty['H1']))
def p(t):story.append(Paragraph(t,sty['Body']))
def small(t):story.append(Paragraph(t,sty['Small']))
def h(t):story.append(Paragraph(t,sty['H2']))
def fig(name,cap,width=W):
 path=ROOT/'figures'/name
 from PIL import Image as PILImage
 with PILImage.open(path) as im: ratio=im.height/im.width
 height=min(width*ratio,395)
 if width*ratio>395:width=height/ratio
 story.append(Image(str(path),width=width,height=height))
 story.append(Paragraph(cap,sty['Caption']))
def table(columns,body,widths=None):
 data=[[Paragraph(str(c),sty['Small']) for c in columns]]+[[Paragraph(str(x),sty['Small']) for x in row] for row in body]
 tb=Table(data,colWidths=widths or [W/len(columns)]*len(columns),repeatRows=1,hAlign='LEFT')
 tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),light),('TEXTCOLOR',(0,0),(-1,0),navy),('GRID',(0,0),(-1,-1),.28,colors.HexColor('#d6dfe0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]))
 story.append(tb);story.append(Spacer(1,12))
def code(txt):story.append(Preformatted(txt,sty['Code'],maxLineLength=95,splitChars=' '))
def footer(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#d5dee0'));canvas.line(43,43,A4[0]-43,43)
 canvas.setFont('DejaVu',7);canvas.setFillColor(gray);canvas.drawString(43,31,'JOSHUA | Mathematical Chess Search with the local paceval Engine | 15 Nov 2026');canvas.drawRightString(A4[0]-43,31,str(doc.page));canvas.restoreState()

# 1 COVER
story.append(Spacer(1,25));story.append(Paragraph('JOSHUA',sty['Title']))
story.append(Paragraph('Mathematical Chess Search and Position Evaluation with the Local paceval Engine',ParagraphStyle('sub',parent=sty['H1'],fontSize=16,leading=21)))
story.append(Spacer(1,15))
fig('JOSHUA_Chess_Research_Cover_2400x1200.png','Preferred original title illustration. Artistic concept, not a record of a specific legal chess position.',W)
p('<b>Single consolidated research whitepaper.</b> A reproducible Linux console engine that controls White and Black, builds bounded decision searches, executes real local paceval numerical graphs and reports elapsed seconds since startup.')
small('Status: executable research demonstrator. Neither top-engine parity nor certified chess optimality is claimed. No MCP calls, Stockfish engine, Lc0 engine, or neural weights are included.')

# 2
pg('1. Executive summary')
p('JOSHUA is an experimental chess engine written in C++17 that plays against itself. Its mathematics is performed using a separately supplied original local paceval shared library. The central distinction is between <b>the actual legal chess search, managed by C++</b>, and <b>reusable mathematical position-score and reduction graphs, managed by paceval</b>.')
p('The existing V1 and V2 score models are preserved. New model V3 uses 32 deterministic position facts and ten persistent paceval graphs, including material, positional activity, pawn structure, king cover, tempo, a composite score, margins, and selected sensitivity expressions. Two search modes provide complementary evidence.')
table(['Search mode','Key property','paceval ownership'],[
('Research full-width','All legal paths to depth 1–4, subject to a node budget','Batched leaf scores AND grouped internal min/max graphs'),
('Alpha-Beta','Iterative deepening up to depth 10; optional bounded quiescence','Scalar on-demand leaf scores AND final root min/max graph')],[103,178,W-281])
p('Actual depth-10 evaluation was completed on a constrained king-and-pawn position, while the standard opening position was tested to depth 6; a separate depth-4, q1 run completed ten halfmoves. These different positions must not be conflated. An independent V3 test rebuilt feature vectors and mathematical scores with 80-digit Python Decimal precision and passed 420 cross-checks. Full-width and Alpha-Beta agreed on all 62 tested root move scores at depth 3 when the tactical extension was disabled.')

# 3
pg('2. Industrial and scientific motivation')
p('The purpose is to investigate <b>automatic construction and reuse of deterministic mathematical decision graphs</b>. Chess is a useful experimental environment because the move legality and fixed-horizon minimax problem can be checked independently, and many positions expose tactical weaknesses of simplified scoring methods.')
h('Why depth alone does not determine chess strength')
p('A chess engine does not become equivalent to Stockfish or Leela Chess Zero at a universal minimum depth. Stockfish combines a learned NNUE evaluation with deeply optimized alpha-beta variants and tactical search. Leela Chess Zero supports neural-network backends and multiple search algorithms, including Monte Carlo Tree Search with PUCT and a DAG variant. JOSHUA currently implements neither Stockfish NNUE nor Lc0 training.')
h('Questions the demonstrator can answer')
p('Does paceval actually compile and reuse the proposed score expressions? Do the numerical graph results match independent arithmetic? Does Alpha-Beta return the same fixed-depth root values as full-width minimax when both have identical leaf functions? What is the practical search depth on specified positions? Which mathematical tasks remain outside the local paceval graph?')
small('Context references: stockfishchess.org/documentation; github.com/official-stockfish/Stockfish/blob/master/src/search.cpp; lczero.org/dev/overview/. These are architectural context sources, not independent validation of JOSHUA.')

# 4
pg('3. System architecture and execution ownership')
fig('03_actual_architecture.png','The diagram follows the implemented C++ and local SDK API boundaries. “Research mode” and “Alpha-Beta mode” deliberately have different internal reduction ownership.',W)
p('The C++ host owns state parsing, legal move generation, castling, en passant, promotions, check detection, reversible make/unmake, search history, pruning decisions, transposition cache, result ranking and I/O. The paceval SDK creates persistent computation handles for explicit numerical expressions and evaluates them for distinct positions.')
p('In full-width mode the host groups sibling scores by node fan-out and side, and asks paceval to evaluate those generated min/max expressions. In Alpha-Beta mode, intermediate pruning requires immediate values; the host controls these decisions in C++, with paceval still evaluating the leaf score and the final root reducer. Reporting both modes simply as “all search done by paceval” would be incorrect.')

# 5
pg('4. Real chessboard examples')
p('The following positions come from the recorded V3 depth-3 self-play CSV. They are actual legal transitions, not artist-generated chessboards. The board data are reconstructed from the complete Forsyth–Edwards Notation fields saved before and after each selected move.')
fig('01_real_chess_positions.png','Standard start, followed by 1. Nc3 (white knight b1–c3) and 1... Nc6 (black knight b8–c6). The figures, side to move, highlighted squares and notation are consistent with the recorded program output.',W)
p('A chess decision tree is formed by legal continuations from each of these positions. White seeks the highest white-centric score and Black the lowest. The score is only a heuristic unless the search reaches a game-theoretically terminal state such as a proven checkmate.')

# 6
pg('5. Position features in V3')
p('The real V3 input vector has 32 named components. The first 19 reproduce V1/V2 material counts and simplified positional descriptors. Additional components encode piece-square activity, pawn formation, passed pawns, bishop-pair presence, pawn cover in front of each king and the side to move.')
table(['Group','Input identifiers','Interpretation'],[
('Material','wp, wn, wb, wr, wq / bp, bn, bb, br, bq','White and Black piece counts'),
('Baseline position','wc, bc, wd, bd, wa, ba, wk, bk','Central occupancy, minor development, pawn advance, castled-zone indicator'),
('Position activity','wpsq, bpsq','Handcrafted square-centering contributions by piece type'),
('Pawn structure','wdoub, bdoub, wisolated, bisolated, wpassed, bpassed','Doubled/isolated/passed pawn counts'),
('Other structure','wbpair, bbpair, wshield, bshield','Bishop-pair indicator and adjacent pawn cover in front of king'),
('Side and constant','tempo, bias','Side-to-move sign and reference constant')],[103,184,W-287])
p('The constants are explicitly illustrative and were not learned from expert games. Features called “piece-square” or “king shelter” are narrow operational definitions, not full strategic evaluation. C++ extracts the counts; their numerical weighting is a real paceval graph calculation.')

# 7
pg('6. Exact mathematical graph expressions')
h('V3 composite white-centric score, in centipawns')
code('''M  = 100*(wp-bp) + 320*(wn-bn) + 330*(wb-bb)
   + 500*(wr-br) + 900*(wq-bq)
P  = 13*(wc-bc) + 17*(wd-bd) + 3*(wa-ba)
   + 18*(wk-bk) + (wpsq-bpsq)
S  = -16*(wdoub-bdoub) - 12*(wisolated-bisolated)
   + 22*(wpassed-bpassed) + 28*(wbpair-bbpair)
K  = 9*(wshield-bshield)
T  = 7*tempo
E3 = M + P + S + K + T''')
p('This is the documented content of the actual persistent `V3 SCORE` graph. It operates on 32 numeric variables. Separate paceval graphs compute M, piece-square activity, S, K, T, a score margin, a guard and selected sensitivities. The exact parser expression is stored as `v3_score` in `src/paceval_math.h`.')
h('Minimax reduction graphs')
code('''White chooses MAX:  (v0 max v1 max ... max vn)
Black chooses MIN:  (v0 min v1 min ... min vn)''')
p('Each graph uses the actual number of legal root alternatives, and each input is a score returned from the search. At a fixed horizon, if scores are expressed from White’s point of view, the reduction direction must follow the side to move. The two search implementations were tested to agree under the shared fixed-depth model.')

# 8
pg('7. What the decision graph really contains')
fig('05_actual_root_reduction.png','Real recorded V3 depth-5, q2 root alternatives from the opening. Scores are the already searched root-move scores; this does not pretend the four scores are direct leaf evaluations.',W)
p('The diagram shows White’s root choice. Because the two highest sampled alternatives both score 16 cp, JOSHUA’s deterministic lexicographic UCI tie-break selects c2c4. The underlying position evaluation is not a claim that 1. c4 is objectively better than every other move with an expert engine.')
p('In full-width Research mode each internal node uses a persistent paceval graph with an arity equal to its number of children. An internal graph is created once for each unique pair of fan-out and player to move and then reused in large numerical batches. In Alpha-Beta mode this internal search logic is controlled by C++ to permit immediate pruning, while the final root reducer remains a genuine paceval graph.')

# 9
pg('8. Search algorithms and tactical horizon')
h('Reference search')
p('Research mode enumerates every legal line to a bounded fixed depth, provided the configured maximum node count is not exceeded. At the leaves, it deduplicates 19- or 32-element feature vectors, calls the local multi-graph API on reusable formula handles, and groups all internal min/max nodes into separately batched paceval evaluations. This is a deliberately exact fixed-depth search under the chosen leaf heuristic and terminal-state convention.')
h('Alpha-Beta search')
p('Alpha-Beta uses recursive make/unmake, move ordering, iterative deepening, a conservative hash table with bound types and a full search window for each legal root alternative. Its intermediate search nodes are not batch-reduced in paceval. The mathematical leaf score and final root maximum/minimum remain actual local paceval graph calls.')
h('Bounded quiescence')
p('The optional `--quiescence N` investigates captures, promotions and legal check evasions below the nominal depth up to a finite tactical budget. This is a selective estimate. When that additional budget is exhausted, the engine can still evaluate a tactically unstable position. Unlike a full tactical solver or tablebase, this does not prove safety or optimality.')
p('Game-level repetition and 50-move claims are represented in the playable state. Full path-dependent repetition semantics are not propagated to every cached internal search branch, so a future strength-oriented engine must add more careful repetition/history handling before claiming equivalence to established search engines.')

# 10
pg('9. Reproducible experiments and actual search depths')
data=[]
for folder,desc in [
 ('v3_research_depth3_3ply','Standard start, full-width'),
 ('v3_ab_depth3_3ply','Standard start, Alpha-Beta'),
 ('v3_ab_depth4_4ply','Standard start, q2'),
 ('v3_ab_depth5_q2_2ply','Standard start, q2'),
 ('v3_ab_depth6_initial','Standard start, no q'),
 ('v3_ab_depth8_q1_endgame','Constrained endgame, q1'),
 ('v3_ab_depth10_endgame','Constrained endgame, no q'),
 ('v3_ab_depth4_q1_10ply','Standard start, 10-ply self-play q1')]:
 j=json.load(open(ROOT/'results'/folder/'run_evidence.json'))
 data.append((desc,str(j['depth_each_move']),str(j['played_halfmoves']),str(j['paceval_graph_point_evaluations']),f"{j['elapsed_seconds']:.3f}"))
table(['Run','Depth','Plies','paceval graph-points','Elapsed (s)'],data,[177,45,45,115,W-382])
p('The measurements are wall-clock observations from this Linux environment. Different positions, quiescence budgets and numbers of played halfmoves make these rows <b>not directly comparable as performance benchmarks</b>. The depth-10 case has only two legal White alternatives at its root, whereas the opening has twenty and a much broader tree.')
fig('04_observed_runs.png','Observed total duration of each genuinely executed experiment. The plot is descriptive only; it is not a controlled speed or strength ranking.',W)

# 11
pg('10. Opening decisions and move output')
fig('02_actual_root_scores.png','The actual depth-5 with q2 white-root alternatives, directly read from root_move_rankings.csv.',W)
p('The console reports English names, the exact start and destination squares, SAN, white-centric score and the resulting FEN. This information is generated from the board before each chosen move.')
code('''[+5.451066s] JOSHUA BEST WHITE c2c4
    Piece=Pawn c2 -> c4 | SAN=c4 | score_white=16cp
[+12.227797s] JOSHUA BEST BLACK d7d6
    Piece=Pawn d7 -> d6 | SAN=d6 | score_white=-8cp''')
p('The actual run prints one line per move, including the complete resulting FEN. The line breaks above are purely editorial. The timestamps are seconds since the start of that program execution. The sample is the recorded depth-5, V3, q2 run and is not constructed from a separate chess database.')

# 12
pg('11. Numerical verification and reproducibility')
h('Actual original paceval calls')
code('''paceval_CreateComputation(...)
paceval_dGetComputationResult(...)          // Alpha-Beta leaf
paceval_dGetMultipleComputationsResultsExt(...) // Research batch
paceval_dGetComputationResultExt(...)       // Batched min/max
paceval_GetIsError(...)''')
p('The SDK batch output layout was checked with a two-expression/two-case probe before the engine issued data batches. Every formula result can be compared with a native C++ reference. The independent audit also reconstructs the underlying position inputs from FEN rather than trusting the extracted feature CSV.')
table(['Independent test','Actual finding'],[
 ('Opening Perft','Known 20 / 400 / 8,902 / 197,281 counts through depth 4 verified'),
 ('Reversible state transitions','9,364 make/unmake comparisons against the independent copy implementation'),
 ('V3 numeric graph batch','10 FEN positions x 32 features plus 10 outputs = 420 independent checks'),
 ('High precision','Python Decimal with 80 decimal digits, same declared weighting and feature definitions'),
 ('Research vs Alpha-Beta','All 62 root move scores and three played plies agreed at depth 3, q0'),
 ('Tactical extension','Executed in live self-play at depth 4 and 5, q2; not asserted to equal q0')],[150,W-150])
p('Checks also cover English piece labels, SAN, castling, en passant and promotion. All tests have run on actual compiled C++ and the actual local paceval library. The source release has a CTest suite and a repeatable JSON/CSV evidence path.')

# 13
pg('12. Limitations, deployment boundary and next study')
p('<b>No opponent benchmark.</b> Stockfish and Leela Chess Zero are cited only for research context. Their source is not included and JOSHUA has not played them. No statistical Elo, tournament result, or superiority claim is made.')
p('<b>Weak handcrafted evaluation.</b> V3 is richer than V2, but it is not a trained evaluator and its pawn, piece-square and king-shelter features intentionally simplify chess. It cannot capture many concrete threats and combinations.')
p('<b>Limited tactical search.</b> The bounded extension is an exploratory mechanism and the transposition table does not yet incorporate all path-dependent repetition data. Neither pointwise heuristic scores nor a depth-10 constrained endgame constitute a proof of optimal play.')
p('<b>Depth cost.</b> Running a depth-10 search on a two-move endgame is much easier than running depth 10 from the initial 20-move opening. The complete opening full-width tree is computationally immense; practical progress requires incremental move-generation optimization and carefully validated selective search.')
h('Suggested next validation gates')
p('First, add position-history-aware transpositions, robust tactical verification, and dedicated checking of horizon effects. Second, compare V3 against exact seven-piece endgame tablebases when applicable. Third, introduce a separately trained NNUE-compatible scoring experiment without sacrificing the paceval mathematical graph audit. Only after these steps should fair Elo matches against pinned Stockfish and Lc0 versions be considered.')

# 14
pg('13. Rebuild commands and release structure')
code('''cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \\
  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j
ctest --test-dir build --output-on-failure

./build/joshua --mode alphabeta --model 3 --depth 5 \\
  --quiescence 2 --plies 10 --no-board --output results/new_run

./build/joshua --mode research --model 3 --depth 3 \\
  --batch-rows 65536 --plies 3 --no-board \\
  --output results/new_fullwidth''')
p('The archive includes the exact C++ source and SDK interface, self-play and audit commands, result CSV/JSON evidence files, original logs, and source-derived figures. The externally supplied paceval Linux .so is not redistributed. The run outputs are reproducible in logic, but wall times and order of events may vary by machine and compiler.')
p('The console game always remains JOSHUA (White) versus JOSHUA (Black). Future UCI matches against external engines would be a separate release with independent testing and appropriate software licensing.')

# 15
pg('14. References and scope notes')
for title,url in [
 ('Stockfish official documentation (current 2026 release family)','https://stockfishchess.org/documentation'),
 ('Stockfish public Alpha-Beta/search source','https://github.com/official-stockfish/Stockfish/blob/master/src/search.cpp'),
 ('Leela Chess Zero search architecture and algorithm overview','https://lczero.org/dev/overview/'),
 ('paceval Mathematical Engine developer documentation','https://paceval.com/developers/')]:
 h(title);small(url)
p('These external sources support the choice of baseline search architectures and define comparison targets. They do <b>not</b> independently certify a particular paceval graph, measured timing or JOSHUA chess decision. The experimental claims in this report are grounded instead in the included compiled C++ program, local paceval execution evidence, and independent regression/audit scripts.')
p('“WarGames” is cited as the inspiration for the name JOSHUA. The project has no affiliation with the film, its cast, producers or rights holders.')
p('This document is the <b>one and only scientific whitepaper</b> included in the release. Intermediate research papers, historical addenda and duplicated versions are deliberately excluded.')

doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('SINGLE_WHITEPAPER_CREATED',P)
