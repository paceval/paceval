#!/usr/bin/env python3
"""Build the V13 standalone scientific PDF only from checked source and SDK data."""
from pathlib import Path
from xml.sax.saxutils import escape
import csv, json
from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Image,Spacer,Table,TableStyle,PageBreak,Preformatted,KeepTogether
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'JOSHUA_Chess_Research_Whitepaper_EN.pdf'
F='/usr/share/fonts/truetype/dejavu'
pdfmetrics.registerFont(TTFont('DejaVu',F+'/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuBold',F+'/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuMono',F+'/DejaVuSansMono.ttf'))
NAVY=colors.HexColor('#152F43'); ACC=colors.HexColor('#137987'); LIGHT=colors.HexColor('#EEF5F4');GRAY=colors.HexColor('#51616B')
sty={
 'Title':ParagraphStyle('Title',fontName='DejaVuBold',fontSize=23,leading=28,textColor=NAVY,spaceAfter=14),
 'H1':ParagraphStyle('H1',fontName='DejaVuBold',fontSize=16,leading=21,textColor=NAVY,spaceBefore=9,spaceAfter=10),
 'H2':ParagraphStyle('H2',fontName='DejaVuBold',fontSize=11,leading=15,textColor=ACC,spaceBefore=11,spaceAfter=6),
 'Body':ParagraphStyle('Body',fontName='DejaVu',fontSize=8.8,leading=13.3,textColor=NAVY,spaceAfter=9),
 'Small':ParagraphStyle('Small',fontName='DejaVu',fontSize=7.6,leading=11.0,textColor=GRAY,spaceAfter=6),
 'Caption':ParagraphStyle('Caption',fontName='DejaVu',fontSize=7.9,leading=11.5,textColor=GRAY,spaceBefore=5,spaceAfter=12),
 'Code':ParagraphStyle('Code',fontName='DejaVuMono',fontSize=7.3,leading=10.6,textColor=NAVY,spaceAfter=9),
}
W=A4[0]-86
story=[]
def head(t):story.append(Paragraph(t,sty['H1']))
def sub(t):story.append(Paragraph(t,sty['H2']))
def body(t):story.append(Paragraph(t,sty['Body']))
def small(t):story.append(Paragraph(t,sty['Small']))
def new(t):story.append(PageBreak());head(t)
def pic(name,width=W,caption=''):
 f=ROOT/'figures'/name
 with PILImage.open(f) as im:ratio=im.height/im.width
 if width*ratio>350:width=350/ratio
 story.append(Image(str(f),width=width,height=width*ratio))
 if caption:story.append(Paragraph(caption,sty['Caption']))
def tab(headers,rows,widths=None):
 dat=[[Paragraph(escape(str(x)),sty['Small']) for x in headers]]
 dat += [[Paragraph(escape(str(x)),sty['Small']) for x in row] for row in rows]
 t=Table(dat,colWidths=widths or [W/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('GRID',(0,0),(-1,-1),.25,colors.HexColor('#D4DEDF')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 story.append(t);story.append(Spacer(1,10))
def code(s):story.append(Preformatted(s,sty['Code'],maxLineLength=75))
def footer(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#CFD9DB'));canvas.line(43,43,A4[0]-43,43)
 canvas.setFont('DejaVu',7);canvas.setFillColor(GRAY)
 canvas.drawString(43,31,'JOSHUA V13 | Local paceval Mathematical Engine | 17 Nov 2026')
 canvas.drawRightString(A4[0]-43,31,str(doc.page));canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=43,rightMargin=43,topMargin=48,bottomMargin=53,
 title='JOSHUA V13: Verified Depth-Seven Chess Search and Fused paceval Graph',
 author='paceval scientific research demonstrator')
# Cover
story.append(Spacer(1,11));story.append(Paragraph('JOSHUA V13',sty['Title']))
body('<b>Verified Depth-Seven Chess Search and Composed paceval Evaluation Graphs</b>')
small('Scientific C++17 research demonstrator | Linux x86-64 | Original local paceval SDK | 17 November 2026')
pic('JOSHUA_Chess_Research_Cover_2400x1200.png',W,'Conceptual title illustration. The tested chess positions on later pages come from actual FEN data.')
body('<b>Research question.</b> Can a depth-seven chess decision be completed with persistent paceval mathematical scoring graphs while preserving exact root scores at the completed horizon? Can the V4 neural score and an approved adaptive correction be composed into a single executable paceval graph without changing the mathematical result?')
body('<b>Scope.</b> This document reports a real paceval functional experiment, not a claim of playing-strength advantage. A second, budget-limited test demonstrates honest reporting when a full depth-seven search does not finish. Stockfish is an optional real-world opponent, but no new V13 Stockfish tournament was executed in the available build environment.')

new('1. Practical chess-research use case')
body('A chess position can have many legal actions and each action may lead to more replies. JOSHUA uses C++ for legal move generation, state transitions and Alpha-Beta search. The paceval Mathematical Engine compiles mathematical feature formulas once and evaluates them repeatedly at searched leaf positions. An independently checked root min/max paceval graph combines completed root candidate scores.')
body('The depth target is seven halfmoves from the current position. This is not seven full move pairs, and the optional quiescence search is a selective tactical extension beyond the nominal horizon. The current experiment uses quiescence budget two.')
tab(['Research task','Actual implementation'],[
 ('Generate/check legal moves, checkmate, SAN and FEN','C++ chess host and separate C++ referee'),
 ('Maintain tree, Alpha-Beta, move ordering and search budgets','C++ host, with honest last-completed-depth reporting'),
 ('Score board features and nonlinear neural terms','Original reusable paceval graph handles'),
 ('Combine final V4 neural and adaptive score','One composed persistent paceval graph in V13'),
 ('Perform root min/max comparison','Original paceval reduction graph'),
 ('Judge move quality over real games','External Stockfish diagnostic, not C++ referee')],[W*.48,W*.52])
sub('A useful distinction')
body('V13 does not unroll the entire legal depth-seven tree into one giant formula. The separate full-width research compiler remains limited by its own memory and graph-expansion constraints. The claimed seven-ply completion belongs to the Alpha-Beta path with genuine paceval evaluation at the leaves.')

new('2. Mathematical composition and graph ownership')
body('The trained V4 evaluator has twelve sigmoid subgraphs with 48 board features and one baseline output graph. The adaptive model consists only of known, bounded numeric and nonlinear templates. In V13, the original V4 fused-output expression is substituted into the adaptive correction as one larger persistent paceval expression. The twelve hidden sigmoid graphs stay reusable.')
code('V4(s) = V3(s) + clip(neural_residual(s), -150, +150)\nV13(s) = V4(s) + clip(adaptive_terms(s), -160, +160)')
body('The combined graph receives twelve hidden-neuron results, the V3 baseline value and all 48 V4 features. Its exact source text is exported in <b>paceval_v13_fused_score.txt</b>. The final compiled SDK internal execution structure is proprietary and is not claimed to be serialized as a text file.')
body('For numerical assurance, the independent original path remains available as <b>--no-fused-adaptive</b>. The V13 test executes both paths with the same board state, model coefficients and real paceval library and compares all ranked root candidate values. The graph catalog reports not only registered graphs but actual evaluated points, so an unused graph does not count as proven execution.')
sub('Separate responsibilities')
tab(['Component','Actually performed by'],[
 ('Feature extraction and legal state evolution','C++ host'),
 ('Twelve neural hidden functions','12 genuine paceval handles'),
 ('Combined mathematical final function','1 new genuine paceval handle'),
 ('Search iteration and stopping decision','C++ host'),
 ('Root numerical min/max','Genuine paceval handle')],[W*.47,W*.53])

new('3. Real completed depth-seven chess position')
body('The following nonterminal FEN was evaluated by the actual recompiled Joshua executable with the original supplied Linux paceval library:')
code('8/7k/8/8/8/6K1/7P/8 w - - 0 1')
pic('v13_verified_depth7_board_pair.png',W,'Before/after diagrams constructed from the actual FEN and the returned legal UCI move g3f4 (SAN Kf4). The arrow denotes the played king move.')
body('For this small legal position, the engine completed the full requested depth 7 with quiescence budget 2, using a nonzero approved king-tactics graph coefficient solely to exercise formula composition. This coefficient is not evidence of a learned improvement. The selected move was <b>g3f4</b> (Kf4). The recorded search completed all iterations through depth seven without a search-budget stop.')

new('4. Search iteration and numerical verification')
pic('v13_depth7_completed_iterations.png',W,'Nodes visited, accumulated over successive completed depth iterations in the real V13 depth-seven experiment. These are search-work counts, not a comparison with another engine.')
tab(['Observed quantity','Value'],[
 ('Requested and actually completed depth','7 / 7'),
 ('Quiescence tactical budget','2'),
 ('Cumulative search nodes across completed iterations','31,652'),
 ('Distinct V4 feature vectors evaluated','1,077'),
 ('Selected UCI / SAN move','g3f4 / Kf4'),
 ('Genuine paceval V4/adaptive combined graph','Registered and executed'),
 ('Independent V13 fused/unfused root ranking test','Pass, with recorded numerical agreement'),
 ('Improvement over Stockfish','Not measured')],[W*.58,W*.42])
body('The graph-aggregation step must not be confused with the complete chess search. Numeric scalar paceval calls evaluate leaf feature vectors when Alpha-Beta requests them. The host still owns conditional pruning and exact move legality. A numerical match of the two graph formulations proves only consistency for the tested inputs.')

new('5. Controlled depth shortfall and operational safety')
body('An additional test started at the standard chess opening position with a deliberately small cumulative node budget of 4,500. The engine requested depth seven but safely stopped after the last complete iteration of depth two. This is a necessary distinction for continuous unattended self-play and Stockfish matches.')
code('DEPTH_COMPLETED depth=1 ...\nDEPTH_COMPLETED depth=2 ...\nSEARCH_BUDGET_STOP requested=7 completed=2 reason=nodes\nV13_DEPTH requested=7 actual=2 budget_stop=nodes')
body('The child iteration that exhausts the limit does not produce a decision. The program returns a legal move and a fully ranked root from depth two. The exact requested and reached depths plus the reason are written into CSV and JSON evidence. If even the first full iteration fails, the engine reports an error rather than inventing a move.')
sub('Why the clock limit is independent of a proof of depth')
body('The search deadline and node cap bound experimentation on a specific computer. They do not prove that depth seven is always reachable for chess opening positions with dozens of legal replies. A match controller must also enforce its separate subprocess timeout and preserve these settings as part of the research configuration.')

new('6. Automatic optimization and role of the referee')
body('After each Stockfish match, the controller may identify legal FEN positions with tactical reference-score losses. Candidate mathematical models are created by altering only approved and bounded coefficients and known tactical expression templates. Each variant is executed using genuine paceval, tested on separate held-out positions and then subjected to completed color-paired matches against a frozen Joshua champion before promotion.')
body('The independent <b>joshua_referee</b> does not approve or reject the mathematical quality of a legal move. It verifies FEN transitions, legal move status, SAN and relevant game termination. The controller stores the selected and rejected model versions, their input FENs and the outcome of every gate. The V13 score fusion does not override any champion comparison and is not an automatic neural-network training algorithm.')
sub('Unproven properties')
body('This release does not establish a Stockfish Elo gain, a globally optimal chess move, a guaranteed faster graph, hardware acceleration or a complete depth-seven search in every game. The strongest evidence is that a seven-ply execution succeeded in a controlled position with original paceval, and the fused score preserved the independent unfused numeric result.')

new('7. Build, files and repeatability')
code('cmake -S src -B build -DCMAKE_BUILD_TYPE=Release\ncmake --build build --target joshua joshua_referee \\\n  joshua_selfplay joshua_long_graph -j2\nexport PACEVAL_RUNTIME=/path/to/libpaceval_linux_sharedLIB.so\nctest --test-dir build -R joshua_v13_depth7_original_paceval')
body('To run the same depth target in a Stockfish series, invoke the supplied start script with --depth 7 --quiescence 2 --verify-extra-depth 0 --joshua-search-ms 65000 --joshua-search-nodes 750000. The subprocess controller uses Stockfish installed separately. These settings may cause a move to finish at less than depth seven, which the logs must record explicitly.')
tab(['Reproducible file','Purpose'],[
 ('results/v13_depth7/V13_TEST_EVIDENCE.json','Compact genuine SDK test verdict'),
 ('results/v13_depth7/paceval_v13_fused_score.txt','Exact readable mathematical expression'),
 ('results/v13_depth7/paceval_all_graphs.csv','Registered and actually executed graph catalog'),
 ('results/v13_depth7/selfplay_timeline.csv','Real depth-seven request and completion'),
 ('results/v13_depth7/budget_fallback_timeline.csv','Correctly limited opening-position experiment'),
 ('src/joshua.cpp, src/v4_paceval.h','Actual source modifications')],[W*.54,W*.46])
small('Sources: local exact C++ and original paceval SDK test outputs supplied in the project; paceval API https://paceval.com/api/ ; Stockfish UCI and search source https://github.com/official-stockfish/Stockfish . The external references are context, not certification of the new experiment.')

story.append(Spacer(1,6))
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('CREATED',OUT,OUT.stat().st_size)
