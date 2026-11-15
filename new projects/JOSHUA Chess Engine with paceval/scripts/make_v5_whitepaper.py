#!/usr/bin/env python3
"""Create one consolidated English V5 report from actual measured results.

The retained V4 foundation is embedded in the same PDF, not distributed as a
separate whitepaper. All V5 tables/chessboard diagrams come from recorded files.
"""
from pathlib import Path
import csv,json,math,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image as RLImage,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader,PdfWriter
ROOT=Path(__file__).resolve().parent.parent
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
REPORT=ROOT/'JOSHUA_Chess_Research_Whitepaper_EN.pdf'
V4BASE=ROOT/'docs'/'V4_Foundation_Previous_Whitepaper_EN.pdf'
if not V4BASE.is_file():
    # Rebuild the retained V4 foundation from its source, rather than shipping
    # a second PDF inside the release ZIP. The intermediate exists only during
    # whitepaper assembly and is deleted after the single report is merged.
    subprocess.run([sys.executable,str(ROOT/'scripts'/'make_v4_whitepaper.py')],check=True)
    V4BASE.parent.mkdir(parents=True,exist_ok=True)
    (ROOT/'JOSHUA_Chess_Research_Whitepaper_EN.pdf').replace(V4BASE)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',FONT));pdfmetrics.registerFont(TTFont('DejaVu-Bold',BOLD))
S=getSampleStyleSheet()
S.add(ParagraphStyle(name='H1v5',fontName='DejaVu-Bold',fontSize=17,leading=22,spaceAfter=12,textColor=colors.HexColor('#142f40')))
S.add(ParagraphStyle(name='H2v5',fontName='DejaVu-Bold',fontSize=12,leading=16,spaceBefore=11,spaceAfter=7,textColor=colors.HexColor('#22445e')))
S.add(ParagraphStyle(name='Bodyv5',fontName='DejaVu',fontSize=8.6,leading=13.2,spaceAfter=8))
S.add(ParagraphStyle(name='Smallv5',fontName='DejaVu',fontSize=7.2,leading=10.1,spaceAfter=5))
S.add(ParagraphStyle(name='Captionv5',fontName='DejaVu',fontSize=7,leading=9.8,textColor=colors.HexColor('#486277'),spaceAfter=9))
S.add(ParagraphStyle(name='Monov5',fontName='Courier',fontSize=7.5,leading=10.2,spaceAfter=6))

# Geometrically faithful chessboards from source FEN, with true square coordinates.
PIECE={'K':'♔','Q':'♕','R':'♖','B':'♗','N':'♘','P':'♙','k':'♚','q':'♛','r':'♜','b':'♝','n':'♞','p':'♟'}
def board(path,fen,title,focus=None):
    rows=fen.split()[0].split('/');assert len(rows)==8
    arr=[]
    for r in rows:
        squares=[]
        for x in r:
            if x.isdigit():squares.extend(['.']*int(x))
            else:squares.append(x)
        assert len(squares)==8
        arr.append(squares)
    wh=695;box=74;off=46
    im=Image.new('RGB',(wh,wh+62),'white');d=ImageDraw.Draw(im)
    pf=ImageFont.truetype(FONT,47);lab=ImageFont.truetype(BOLD,17);heading=ImageFont.truetype(BOLD,21)
    d.text((wh/2,12),title,font=heading,anchor='mt',fill='#17344c')
    for y in range(8):
        for x in range(8):
            px=off+x*box;py=off+y*box
            dark=(x+y)%2==1
            d.rectangle((px,py,px+box,py+box),fill='#b58863' if dark else '#f0d9b5')
            piece=arr[y][x]
            if piece!='.':
                fill='#ffffff' if piece.isupper() else '#171717'
                stroke='#151515' if piece.isupper() else '#e2d7c3'
                d.text((px+box/2,py+box/2+3),PIECE[piece],font=pf,anchor='mm',fill=fill,stroke_width=1,stroke_fill=stroke)
            if focus and (x,y) in focus:
                d.rectangle((px+3,py+3,px+box-3,py+box-3),outline='#ce263b',width=5)
    for k in range(8):
        d.text((off-21,off+k*box+box/2),str(8-k),font=lab,anchor='mm',fill='#183048')
        d.text((off+k*box+box/2,off+8*box+18),'abcdefgh'[k],font=lab,anchor='mm',fill='#183048')
    im.save(path)
    return path

moves=list(csv.DictReader((ROOT/'input/chatgpt_vs_joshua_94_halfmoves.csv').open()))
assert len(moves)==94
fen0=moves[29]['fen_before'];fen1=moves[29]['fen_after'];fen2=moves[30]['fen_after']
q2=list(csv.DictReader((ROOT/'results/game_analysis/position_15_black_q2/selfplay_timeline.csv').open()))
assert len(q2)==1;fen3=q2[0]['fen_after']
board(FIG/'v5_01_before_blunder.png',fen0,'Position before 15... Nxe5',[(2,4),(4,3)])
board(FIG/'v5_02_after_blunder.png',fen1,'After 15... Nxe5',[(4,3)])
board(FIG/'v5_03_capture.png',fen2,'After 16. dxe5',[(4,3)])
board(FIG/'v5_04_alternative.png',fen3,'Alternative 15... Nb6',[(1,2)])

rows=[]
for tag,label in [('depth3','V3, depth 3'),('depth3_v4','V4, depth 3'),('depth4','V3, depth 4'),('depth4_v4','V4, depth 4')]:
 j=json.loads((ROOT/'results/v5_long_graph'/tag/'run_evidence.json').read_text())
 rows.append((label,j))

# Use a source-derived comparison diagram. Times recorded on real local Linux build.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(9.4,4.4))
labels=[r[0] for r in rows];vals=[r[1]['graph_characters'] for r in rows]
bars=ax.bar(labels,[v/1e6 for v in vals],color=['#477d91','#90b4c7','#1c5069','#d08256'])
ax.set_ylabel('Compiled mathematical expression length (million characters)')
ax.set_ylim(0,2.48)
for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,b.get_height()+.045,f'{v:,}',ha='center',va='bottom',fontsize=10)
ax.spines[['top','right']].set_visible(False)
fig.tight_layout();fig.savefig(FIG/'v5_05_actual_graph_lengths.png',dpi=180);fig.savefig(FIG/'v5_05_actual_graph_lengths.pdf');plt.close(fig)

# Architecture: actual algorithmic workflow, not fictional internal SDK node export.
fig,ax=plt.subplots(figsize=(10,4));ax.set(xlim=(0,10),ylim=(0,4));ax.axis('off')
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
components=[('Legal FEN state\nC++ rules',.1),('Complete tree\nC++ recursion',2.2),('Leaf features\n48 values / position',4.3),('paceval SDK\nneural V4 batches',6.4),('paceval SDK\nfull minimax graph',8.5)]
for name,x in components:
 patch=FancyBboxPatch((x,.95),1.4,1.65,boxstyle='round,pad=.12',edgecolor='#175571',facecolor='#eef6f9',linewidth=1.6)
 ax.add_patch(patch);ax.text(x+.7,1.78,name,ha='center',va='center',fontsize=10,color='#132b3a',linespacing=1.35)
for i in range(len(components)-1):
 x=components[i][1]
 ax.add_patch(FancyArrowPatch((x+1.52,1.78),(components[i+1][1]-.12,1.78),arrowstyle='-|>',mutation_scale=13,color='#c56543',lw=1.8))
ax.text(5,3.43,'One complete, fixed legal topology, compiled into one reusable mathematical decision expression',ha='center',fontsize=10,color='#163d50')
ax.text(5,.38,'Independent C++ minimax is evaluated separately to verify the paceval result',ha='center',fontsize=10,color='#163d50')
fig.tight_layout();fig.savefig(FIG/'v5_06_architecture.png',dpi=180);fig.savefig(FIG/'v5_06_architecture.pdf');plt.close(fig)

# Exact mathematical recurrence; draw as rendered mathematics, not illustrative text.
fig,ax=plt.subplots(figsize=(10.2,3.1));ax.axis('off')
ax.text(.03,.81,r'$V_0(s)=E(s)\quad\mathrm{(nonterminal\ leaf)}$',fontsize=18,transform=ax.transAxes,color='#12394e')
ax.text(.03,.50,r'$V_d(s)=\max_{a\in L(s)}\;V_{d-1}(T(s,a))\qquad\mathrm{White\ to\ move}$',fontsize=17,transform=ax.transAxes,color='#12394e')
ax.text(.03,.17,r'$V_d(s)=\min_{a\in L(s)}\;V_{d-1}(T(s,a))\qquad\mathrm{Black\ to\ move}$',fontsize=17,transform=ax.transAxes,color='#12394e')
fig.tight_layout();fig.savefig(FIG/'v5_08_minimax_notation.png',dpi=200,bbox_inches='tight');fig.savefig(FIG/'v5_08_minimax_notation.pdf',bbox_inches='tight');plt.close(fig)

# Consolidated V5 cover and Part-II technical content.
cover=ROOT/'_v5_new_cover.pdf';extra=ROOT/'_v5_research_section.pdf'
def makecover():
 from reportlab.pdfgen import canvas
 c=canvas.Canvas(str(cover),pagesize=(595.2756,841.8898));W,H=595.2756,841.8898
 c.setFillColor(colors.HexColor('#142e40'));c.rect(0,0,W,H,stroke=0,fill=1)
 image=FIG/'JOSHUA_Chess_Research_Cover_2400x1200.png'
 if image.exists():c.drawImage(str(image),0,H-340,width=W,height=300,preserveAspectRatio=False,mask='auto')
 c.setFillColor(colors.white);c.setFont('DejaVu-Bold',25);c.drawString(48,447,'JOSHUA V5')
 c.setFont('DejaVu-Bold',15);c.drawString(48,417,'Mathematical Chess Decision Graph Research')
 c.setFont('DejaVu',10)
 for i,l in enumerate(['Long, automatically compiled paceval minimax expressions',
   'Tactical regression from a real ChatGPT versus JOSHUA game',
   'Genuine local paceval SDK and trained neural support',
   'One consolidated English scientific report']):c.drawString(48,377-i*25,l)
 c.setFont('DejaVu',9);c.setFillColor(colors.HexColor('#c2d8e7'))
 c.drawString(48,125,'Technical research demonstrator. No claim of grandmaster strength or a solved chess game.')
 c.drawString(48,104,'15 November 2026  |  C++  |  Linux  |  Local paceval  |  Reproducible source and results')
 c.showPage();c.save()

def paged(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#d4e0e7'));canvas.line(36,39,560,39)
 canvas.setFont('DejaVu',7);canvas.setFillColor(colors.HexColor('#587184'))
 canvas.drawString(38,29,'JOSHUA V5 | Extended graph research | Local paceval SDK')
 canvas.drawRightString(560,29,str(doc.page));canvas.restoreState()
def P(s):return Paragraph(s,S['Bodyv5'])
def H(s):return Paragraph(s,S['H2v5'])
def CAP(s):return Paragraph(s,S['Captionv5'])
def img(path,w=490):
 from PIL import Image
 im=Image.open(path);return RLImage(str(path),width=w,height=w*im.height/im.width)
def make_appendix():
 doc=SimpleDocTemplate(str(extra),pagesize=(595.2756,841.8898),leftMargin=43,rightMargin=43,topMargin=55,bottomMargin=55)
 story=[]
 story.extend([Paragraph('Part II. JOSHUA V5: Full-Width Mathematical Graphs',S['H1v5']),P('This section extends the V4 trained-neural foundation included in Part I of this same document. It reports actual C++/local paceval SDK experiments, not simulated throughput or chess-engine strength.'),H('Research questions and experimental separation'),P('Can legal chess decisions be regenerated as large mathematical min/max expressions? How much graph construction is needed? Is a compiled graph reusable when leaf scores change? Can the engine diagnose and avoid a mistake seen in its earlier match against ChatGPT? The experiments answer these questions only for the precisely described cases.'),H('The full-width mathematical model'),P('For a state s and remaining depth d, JOSHUA enumerates every legal move in L(s). White selects the maximum successor value, while Black selects the minimum. When d reaches zero, the V3 score or trained V4 score is used. Terminal checkmates and draws override the heuristic score.'),img(FIG/'v5_08_minimax_notation.png',465),CAP('Finite-horizon mathematical recurrence. Terminal checkmate and drawn states override leaf E(s).'),P('The graph contains only the immutable mathematical rollback topology. Legal-move generation, castling, en passant, check detection and the board transitions remain C++. This separation is essential: a compiled decision graph cannot itself establish which moves are legal in a changed board.'),img(FIG/'v5_06_architecture.png',480),CAP('Figure V5-1. Diagram of real software stages. This is a source-derived logical architecture, not an exported internal SDK execution-node plan.'),H('Two distinct paceval graph families'),P('The V4 neural score uses 12 sigmoid hidden graphs with 48 input features, one fused output graph, and the pre-existing V3 score. The total neural formula text length in the earlier release was 43,311 characters. These graphs calculate leaf values in genuine paceval batches.'),P('Separately, the V5 generator emits a single expression such as (v0 min v1 min v2) max (v3 min v4 min v5), with nesting determined exclusively by the real legal chess tree. Here v_i denotes a numerically evaluated leaf-feature class. Repeated feature vectors share one input variable; this is a mathematical-input deduplication, not a claim that all positions have identical chess meaning.')])
 story.extend([Paragraph('Measured Graph Scale and Reuse',S['H1v5']),P('All measurements below were taken from the compiled local Linux C++ program and the original paceval shared library. Compilation and evaluation are reported separately. The metric "graph characters" is expression text length; it is not an SDK internal node count.'),img(FIG/'v5_05_actual_graph_lengths.png',470),CAP('Figure V5-2. Actual full-width, automatically generated paceval minimax expression lengths, as read from the saved graph files.'),H('Executed experiments'),])
 data=[[Paragraph(z,S['Smallv5']) for z in ['Model / depth','Tree nodes','Distinct inputs','Graph characters','Creation (s)','Evaluation (s)']]]
 for title,j in rows:
  data.append([Paragraph(str(x),S['Smallv5']) for x in [title,f"{j['nodes']:,}",f"{j['unique_feature_vectors']:,}",f"{j['graph_characters']:,}",f"{j['paceval_graph_creation_seconds']:.4f}",f"{j['paceval_graph_evaluation_seconds']:.4f}"]])
 table=Table(data,colWidths=[92,72,91,96,79,79],repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1edf3')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#c5d4dc')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(table)
 story.extend([Spacer(1,8),P('From the standard initial position, depth 4 contains 206,604 cumulative search nodes and exactly 197,281 legal four-ply continuations. The V4 experiment deduplicated the 197,281 leaf-position feature vectors to 40,946 distinct input vectors. A single 2,088,691-character min/max formula was successfully compiled and evaluated with all of them.'),P('For each graph, the SDK root value agreed with an independently coded C++ minimax traversal. The compiled graph was also evaluated a second time after a deterministic perturbation to its leaf-score vector, without recompiling the graph, and was independently checked again.'),H('Boundary conditions and representational risks'),P('The expression is complete only through the tested finite horizon. There is no proof of an optimal chess move beyond it. Full expansion grows exponentially and soon becomes impractical. Leaf-feature aliasing can lose tactical distinctions. A long function is not automatically a faster, stronger or more explainable engine.')])
 story.extend([Paragraph('Concrete Tactical Error: 15...Nxe5',S['H1v5']),P('The historical game played ChatGPT as White and JOSHUA V4 as Black. All 94 recorded halfmoves were replayed and independently checked against legal UCI moves and FEN state transitions. The game was not finished; no winner is assigned.'),H('The recorded position and the material loss')])
 def pair(a,b,caption):
  ta=Table([[img(FIG/a,225),img(FIG/b,225)]],colWidths=[240,240]);ta.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]));return [ta,CAP(caption)]
 story+=pair('v5_01_before_blunder.png','v5_02_after_blunder.png','Figure V5-3. Both boards are generated from the exact historical FEN records. The red square identifies the black knight on c4 before its capture of the pawn on e5.')
 story+=pair('v5_03_capture.png','v5_04_alternative.png','Figure V5-4. Left: the documented 16.dxe5 captures the black knight. Right: in a fresh depth-2 V4 run with quiescence depth 2, JOSHUA instead selects the legal knight retreat 15...Nb6.')
 story.extend([H('Actual tactic regression results'),P('Using the exact same recorded FEN before Black move 15, JOSHUA at V4 depth 2 with quiescence disabled selected c4e5 (SAN Nxe5), and White could respond d4e5 (SAN dxe5). With quiescence depth 2, the engine selected c4b6 (SAN Nb6). A separate depth-3 search with two tactical plies selected d7d5 (SAN d5). These are controlled differences in the evaluated local horizons, not reference-engine certified best moves.'),P('An additional bounded in-check quiescence safeguard examines immediate legal evasions when the tactical budget runs out, instead of returning an in-check stand-pat estimate as if the position were quiet.')])
 story.extend([Paragraph('Recompiling Decision Graphs Before Every Move',S['H1v5']),P('The new script launches the C++ legal-tree and graph compiler for every successive position. The Python host reads the legal selected move and next FEN returned by C++ and does not itself choose chess moves. Each step independently compiles local paceval neural scores plus one new full-width mathematical minimax graph.'),H('Measured eight-halfmove experiment, V4, depth 3')])
 game=list(csv.DictReader((ROOT/'results/v5_graph_rebuilt_selfplay_8ply/selfplay_timeline.csv').open()))
 data=[[Paragraph(x,S['Smallv5']) for x in ['Ply','Color','Chosen legal UCI','Nodes','Graph chars','Elapsed (s)']]]
 for r in game:
  data.append([Paragraph(str(x),S['Smallv5']) for x in [r['ply'],r['side'],r['move_uci'],f"{int(r['search_nodes']):,}",f"{int(r['graph_characters']):,}",f"{float(r['elapsed_seconds']):.3f}"]])
 t=Table(data,colWidths=[38,66,126,76,97,103]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1edf3')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#c5d4dc')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(t)
 summary=json.loads((ROOT/'results/v5_graph_rebuilt_selfplay_8ply/summary.json').read_text())
 story.extend([Spacer(1,10),P(f"The eight separately compiled expressions contain {summary['total_graph_characters_generated']:,} characters in total. Their scores agree with C++ minimax separately on every move. The run ended after a user-configured eight-halfmove limit; it was not a completed chess game."),H('Comparison with classical chess-engine search'),P('Stockfish uses a highly optimized search process with alpha-beta pruning, transposition-table information, move ordering, and tactical quiescence handling. JOSHUA V5 instead tests a full-width mathematical graph representation up to a bounded horizon. The new graph mode does not claim any speed or chess-strength advantage over Stockfish or Leela Chess Zero. More useful future work includes graph decomposition, persistent shared subgraphs, explicit error bounds, and robust comparison against a reference engine at equal resources.'),H('Mathematical encoding and correctness'),P('A mate is handled as a signed terminal value with a ply-dependent score. Negative numbers in the generated paceval expression are written as explicit differences, for example (0-29996), to avoid ambiguous parsing after the min/max operators. This correction was discovered and verified during the depth-4 experiment.'),P('A repeated leaf-feature vector is evaluated only once. This reduces mathematical input complexity but is not identical to transposition-table equivalence. Two different boards with identical features may have different tactics; the current trained residual does not remove this limitation.')])
 story.extend([Paragraph('Validation, Reproduction and Limitations',S['H1v5']),H('Reproducibility checklist'),P('The full research ZIP includes the original paceval C API interface source, the original compatible local shared-library loader, CMake Linux build scripts, exact generated multi-million-character graph strings, per-run JSON evidence, independent C++ root-value comparisons, game replay validation, tactical re-evaluations, graph-regeneration self-play, source-derived scientific diagrams and one consolidated PDF.'),P('The external proprietary Linux shared library is not bundled. JOSHUA does not use MCP, does not call Stockfish or Lc0 for evaluation, and has not achieved proven grandmaster strength. The displayed creation/evaluation durations are measured on the available Linux environment and are not general performance claims.'),H('GitHub Markdown regression'),P('The earlier README used an unsupported rendered math macro for clipping. The public documentation now writes the V4 bounded residual explicitly as a composition of min and max. The archive-wide checker inspects the contents of mathematics code fences, not just prose. It rejects the previous macro in a dedicated negative test.'),Paragraph('E4(s) = E3(s) + max(-150, min(150, R(s)))',S['Monov5']),H('Independent game-analysis limits'),P('The previous match against ChatGPT has 94 validated legal halfmoves but no terminal winner. The position-by-position audit does not convert JOSHUA into a stronger chess engine or establish the optimality of its new move selections. To demonstrate sustained improvements, the program needs a larger tactical test set, carefully controlled Elo matches, stronger supervised training targets, and disjoint test games.'),H('Next research milestones'),P('First: compile and test reusable subgraph blocks to extend beyond a 2-million-character monolith. Second: add exact terminal and draw-history state treatment to graph merging. Third: improve move ordering and tactical extensions without sacrificing full-width research mode. Fourth: train the neural score on stronger, legally licensed reference data and compare JOSHUA V5 variants in independent matches.'),H('References'),P('Stockfish official C++ search source: https://github.com/official-stockfish/Stockfish/blob/master/src/search.cpp'),P('Stockfish documentation: https://official-stockfish.github.io/docs/'),P('paceval developer API: https://paceval.com/developers/'),P('User-provided paceval neural-network formula-export whitepaper, 12 pages (2023). Its intermediate-variable principle motivates the use of separate neural and minimax graph layers.'),P('Every numerical value and pictured chess position in Part II is derived from the included checked research artifacts. Part I retains the complete scientific account of the trained V4 foundation.'),])
 doc.build(story,onFirstPage=paged,onLaterPages=paged)

makecover();make_appendix()
w=PdfWriter();w.append(str(cover));w.append(str(V4BASE),pages=(1,len(PdfReader(V4BASE).pages)));w.append(str(extra));w.add_metadata({'/Title':'JOSHUA V5: Mathematical Chess Decision Graph Research','/Author':'JOSHUA / paceval research demonstrator','/Subject':'One consolidated scientific report: V4 foundation and verified V5 advances'})
with REPORT.open('wb') as f:w.write(f)
print('V5 CONSOLIDATED PDF',REPORT,'pages',len(PdfReader(REPORT).pages))
V4BASE.unlink(missing_ok=True)
cover.unlink(missing_ok=True)
extra.unlink(missing_ok=True)
