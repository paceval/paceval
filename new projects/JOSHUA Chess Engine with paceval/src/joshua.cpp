// JOSHUA Chess Engine. Linux C++17; only JOSHUA vs JOSHUA; local paceval runtime only.
// Every half move generates a complete bounded, unpruned legal move tree.
// All distinct nonterminal leaf feature vectors are evaluated by the real paceval
// multi-graph batch API; all internal min/max reductions are evaluated by real
// persistent paceval graphs, grouped in batch by fanout and player to move.
// This is a technical demonstration, NOT a modern chess-strength engine.
#include "paceval_main.h"
#include "chess_rules.h"
#include "paceval_math.h"
#include <chrono>
#include <functional>
#include <ctime>
#include <memory>
#include <tuple>
#include <utility>
using Clock=std::chrono::steady_clock;
static const string START_FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
struct Config {int depth=3,maxPlies=80,model=2;size_t batchSize=8192,maxNodes=600000;string startFen=START_FEN,firstMove="",output="results";bool selftest=false, printBoard=true;};
struct Node {Board b;int ply=0;int featureId=-1;int terminal=0;vector<int> children;double val=0;string action;};
struct Times {double generated=0,features=0,reduced=0;};
struct Metrics {size_t nodes=0,leaves=0,terminal=0,uniqueVectors=0,scoreBatches=0,reductionBatches=0,newGraphs=0,graphPoints=0,scoreChecks=0,reductionChecks=0;};
string cleanClock(double s){std::ostringstream o;o<<std::fixed<<std::setprecision(6)<<s;return o.str();}
string jsonEscape(const string&s){string r;for(char c:s){if(c=='\\'||c=='"')r+='\\';if(c=='\n')r+="\\n";else r+=c;}return r;}
void boardAscii(const Board&b){std::cout<<"    a b c d e f g h\n";for(int r=0;r<8;r++){std::cout<<" "<<(8-r)<<"  ";for(int f=0;f<8;f++)std::cout<<b.b[r*16+f]<<' ';std::cout<<" "<<(8-r)<<"\n";}std::cout<<"    a b c d e f g h\n";}
int scoreNative(const vector<double>&v,int model){insist(v.size()==19,"score input width mismatch");double x=100*(v[0]-v[5])+320*(v[1]-v[6])+330*(v[2]-v[7])+500*(v[3]-v[8])+900*(v[4]-v[9]);if(model==2)x+=13*(v[10]-v[11])+17*(v[12]-v[13])+3*(v[14]-v[15])+18*(v[16]-v[17]);return int(std::lround(x));}
// Selfplay follows explicit draw claims at 50 moves and 3-fold repetition;
// no such rules are inferred from a heuristic leaf value.
string repetitionKey(const Board&s){string k;for(int i=0;i<128;i++)if(inside(i))k.push_back(s.b[i]);k+=(s.turn==1?'w':'b');k+=char('A'+s.castle);bool hasLegalEp=false;if(s.ep>=0)for(const Move&m:legal(s))if(m.ep){hasLegalEp=true;break;}if(hasLegalEp)k+=sq(s.ep);return k;}
bool minorDraw(const Board&s){int minors=0;bool other=false;int bColor=-1;bool allSameBishops=true;for(int i=0;i<128;i++){if(!inside(i))continue;char p=char(std::tolower(s.b[i]));if(p=='.'||p=='k')continue;if(p=='p'||p=='r'||p=='q')other=true;else if(p=='b'){minors++;int c=(rankof(i)+fileof(i))%2;if(bColor<0)bColor=c;else if(bColor!=c)allSameBishops=false;}else if(p=='n'){minors++;allSameBishops=false;}}return !other&&(minors==0||minors==1||(allSameBishops&&minors>0));}
struct TreeWorker {
 Engine&e;Evaluator&formula;const Config&cfg;double startS=0;
 std::map<std::pair<int,int>,PACEVAL_HANDLE> reductions;
 TreeWorker(Engine&x,Evaluator&f,const Config&c):e(x),formula(f),cfg(c){}
 PACEVAL_HANDLE reduction(int fanout,int turn,Metrics&met){insist(fanout>=2&&fanout<=218,"Invalid reduction arity");auto key=std::make_pair(fanout,turn);auto it=reductions.find(key);if(it!=reductions.end())return it->second;vector<string>vars;string expression="(";for(int i=0;i<fanout;i++){vars.push_back("v"+std::to_string(i));if(i)expression+=(turn==1?" max ":" min ");expression+=vars.back();}expression+=")";PACEVAL_HANDLE h=e.create(expression,vars);met.newGraphs++;reductions[key]=h;return h;}
 string outputTree(const Board&root,int requestedDepth,int turnNo,Metrics&met,Times&tm,vector<string>&ranked,vector<double>&values){
    auto beg=Clock::now();vector<Node>nodes;nodes.reserve(16000);vector<vector<int>>byDepth(requestedDepth+1);
    // 0=not terminal, +1=white wins, -1=black wins, 2=draw.
    std::function<int(const Board&,int,string)> grow = [&](const Board&b,int depth,string label)->int{
      insist(nodes.size()<cfg.maxNodes,"Maximum tree node budget reached; lower --depth or increase --max-nodes");int id=int(nodes.size());nodes.emplace_back();nodes[id].b=b;nodes[id].ply=depth;nodes[id].action=label;byDepth[depth].push_back(id);
      const auto moves=legal(b);if(moves.empty()){nodes[id].terminal=check(b,b.turn)?(b.turn==1?-1:1):2;return id;}
      if(b.half>=100||minorDraw(b)){nodes[id].terminal=2;return id;}
      if(depth==requestedDepth)return id;
      for(const auto&m:moves){Board n=apply(b,m);int child=grow(n,depth+1,uci(m));nodes[id].children.push_back(child);}return id;
    };
    grow(root,0,"");tm.generated=std::chrono::duration<double>(Clock::now()-beg).count();met.nodes=nodes.size();
    // Build a unique set of feature vectors. Explicit white-score/black-score orientation.
    beg=Clock::now();std::map<vector<double>,int>intern;vector<vector<double>>uni;vector<int>indices;
    for(size_t i=0;i<nodes.size();i++)if(nodes[i].children.empty()){
      met.leaves++;
      if(nodes[i].terminal){met.terminal++;nodes[i].val=nodes[i].terminal==2?0:(nodes[i].terminal==1?30000-nodes[i].ply:-30000+nodes[i].ply);continue;}
      auto v=features(nodes[i].b);auto p=intern.find(v);int idx;if(p!=intern.end())idx=p->second;else{idx=int(uni.size());uni.push_back(v);intern.emplace(std::move(v),idx);}nodes[i].featureId=idx;
    }
    met.uniqueVectors=uni.size();
    const size_t scoreIx=formula.by.at(cfg.model==1?"V1_SCORE":"V2_SCORE");
    vector<double>scores(uni.size());
    for(size_t i=0;i<uni.size();i+=cfg.batchSize){
      size_t end=std::min(uni.size(),i+cfg.batchSize);vector<vector<double>>rows(uni.begin()+i,uni.begin()+end);auto computed=e.multi(formula.handles(),rows);met.scoreBatches++;
      for(size_t j=0;j<rows.size();j++){
        double x=computed[j][scoreIx];int reference=scoreNative(rows[j],cfg.model);near(x,reference,1e-12);scores[i+j]=x;met.scoreChecks++;
      }
    }
    for(Node&n:nodes)if(n.featureId>=0)n.val=scores[n.featureId];
    tm.features=std::chrono::duration<double>(Clock::now()-beg).count();
    // Group all equally wide reductions at each depth, preserving node/player semantics.
    beg=Clock::now();for(int depth=requestedDepth-1;depth>=0;depth--){
      std::map<std::pair<int,int>,vector<int>> groups;
      for(int id:byDepth[depth]){Node&n=nodes[id];if(n.children.empty())continue;if(n.children.size()==1){n.val=nodes[n.children[0]].val;continue;}
        groups[{int(n.children.size()),n.b.turn}].push_back(id);
      }
      for(const auto&kv:groups){int f=kv.first.first,t=kv.first.second;auto h=reduction(f,t,met);auto&ids=kv.second;
        for(size_t at=0;at<ids.size();at+=cfg.batchSize){size_t end=std::min(ids.size(),at+cfg.batchSize);vector<vector<double>>rows;rows.reserve(end-at);
          for(size_t p=at;p<end;p++){const Node&n=nodes[ids[p]];vector<double>values;values.reserve(f);for(int c:n.children)values.push_back(nodes[c].val);rows.push_back(std::move(values));}
          auto result=e.single(h,rows);met.reductionBatches++;
          for(size_t p=0;p<rows.size();p++){int id=ids[at+p];auto mm=std::minmax_element(rows[p].begin(),rows[p].end());double expected=t==1?*mm.second:*mm.first;near(result[p],expected,1e-12);nodes[id].val=result[p];met.reductionChecks++;}
        }
      }
    }
    tm.reduced=std::chrono::duration<double>(Clock::now()-beg).count();
    insist(!nodes[0].children.empty(),"No legal moves available at root");
    struct R {string move;double score;};vector<R>rr;for(int id:nodes[0].children)rr.push_back({nodes[id].action,nodes[id].val});
    std::sort(rr.begin(),rr.end(),[&](const R&a,const R&b){if(a.score!=b.score)return root.turn==1?a.score>b.score:a.score<b.score;return a.move<b.move;});
    for(const auto&r:rr){ranked.push_back(r.move);values.push_back(r.score);}
    met.graphPoints=e.graphPoints;
    return rr[0].move;
 }
};
// The move description is derived solely from the position BEFORE the chosen move.
// English SAN is conventional chess notation (N=knight, B=bishop); the separately
// printed German piece name is intended to be clear to non-chess specialists.
string pieceNameGerman(char p){
 switch(char(std::tolower(static_cast<unsigned char>(p)))){
 case 'p':return "Bauer"; case 'n':return "Springer (Pferd)";
 case 'b':return "Läufer"; case 'r':return "Turm";
 case 'q':return "Dame"; case 'k':return "König";
 default:throw std::runtime_error("Invalid moving chess piece");
 }
}
string pieceSanLetter(char p){
 switch(char(std::tolower(static_cast<unsigned char>(p)))){
 case 'n':return "N";case 'b':return "B";case 'r':return "R";
 case 'q':return "Q";case 'k':return "K";case 'p':return "";
 default:throw std::runtime_error("Invalid SAN piece");
 }
}
string notationSan(const Board&before,const Move&m,const vector<Move>&allLegal){
 const char piece=before.b[m.f];insist(col(piece)==before.turn,"SAN mover side mismatch");
 const bool capture=before.b[m.t]!='.'||m.ep;
 string notation;
 if(m.castle){notation=m.t>m.f?"O-O":"O-O-O";}
 else {
  notation=pieceSanLetter(piece);
  if(std::tolower(static_cast<unsigned char>(piece))=='p'){
   if(capture)notation+=char('a'+fileof(m.f));
  }else{
   vector<Move>other;
   for(const Move&candidate:allLegal)
    if(candidate.t==m.t && candidate.f!=m.f && before.b[candidate.f]==piece)
     other.push_back(candidate);
   if(!other.empty()){
    bool fileUnique=true,rankUnique=true;
    for(const Move&candidate:other){
     if(fileof(candidate.f)==fileof(m.f))fileUnique=false;
     if(rankof(candidate.f)==rankof(m.f))rankUnique=false;
    }
    if(fileUnique)notation+=char('a'+fileof(m.f));
    else if(rankUnique)notation+=char('8'-rankof(m.f));
    else notation+=sq(m.f);
   }
  }
  if(capture)notation+='x';
  notation+=sq(m.t);
  if(m.promo!=' ')notation+='='+pieceSanLetter(m.promo);
 }
 Board after=apply(before,m);
 if(check(after,after.turn))notation+=legal(after).empty()?"#":"+";
 return notation;
}
string description(const Board&before,const Move&m){
 const char p=before.b[m.f];
 string z=pieceNameGerman(p)+" "+sq(m.f)+" -> "+sq(m.t);
 if(m.castle)z+=" ("+string(m.t>m.f?"kurze Rochade":"lange Rochade")+")";
 if(before.b[m.t]!='.'||m.ep)z+=" (schlägt "+pieceNameGerman(m.ep?'p':before.b[m.t])+")";
 if(m.promo!=' ')z+=" (Umwandlung in "+pieceNameGerman(m.promo)+")";
 return z;
}
void appendLine(std::ofstream&f,const string&s){f<<s<<'\n';insist(bool(f),"CSV/trace write failed");}
int runGame(const Config&cfg){
 auto timerStart=Clock::now();const auto elapsed=[&](){return std::chrono::duration<double>(Clock::now()-timerStart).count();};
 fs::create_directories(cfg.output);std::ofstream timeline(fs::path(cfg.output)/"selfplay_timeline.csv"),moves(fs::path(cfg.output)/"root_move_rankings.csv"),pgn(fs::path(cfg.output)/"game_uci.txt"),evidence(fs::path(cfg.output)/"run_evidence.json");
 insist(timeline&&moves&&pgn&&evidence,"Failed to create output files");
 appendLine(timeline,"halfmove,side,start_s,tree_ready_s,leaf_values_ready_s,decision_s,tree_generation_s,score_batch_s,reduction_s,legal_root_moves,tree_nodes,leaf_nodes,terminal_leaves,unique_feature_vectors,new_paceval_reduction_graphs,score_batches,reduction_batches,paceval_graph_points_total,chosen_uci,chosen_piece,chosen_san,from_square,to_square,is_capture,promotion,white_score_cp,fen_before,fen_after");
 appendLine(moves,"halfmove,depth,side,rank,uci,white_score_cp");
 Board b=fen(cfg.startFen);insist(!check(b,-b.turn),"Invalid initial FEN: previous player still checked");
 std::cout<<"JOSHUA | JOSHUA (WHITE) vs JOSHUA (BLACK) | local paceval SDK | full-width minimax | depth="<<cfg.depth<<" | model="<<cfg.model<<"\n";
 std::cout<<"[+"<<cleanClock(elapsed())<<"s] start FEN: "<<toFen(b)<<"\n";
 Engine engine;engine.probe();Evaluator form(engine);TreeWorker worker(engine,form,cfg);
 std::cout<<"[+"<<cleanClock(elapsed())<<"s] paceval persistent feature graphs="<<form.expr.size()<<"; multi-graph layout="<<(engine.graphMajor?"graph-major":"case-major")<<"; max batch rows="<<cfg.batchSize<<"\n";
 std::map<string,int>history;history[repetitionKey(b)]++;
 if(cfg.printBoard)boardAscii(b);
 vector<string>played;int actual=0;
 if(!cfg.firstMove.empty()){
   auto legalMoves=legal(b);auto it=std::find_if(legalMoves.begin(),legalMoves.end(),[&](const Move&m){return uci(m)==cfg.firstMove;});insist(it!=legalMoves.end(),"--first-move is not legal for starting FEN");
   std::cout<<"[+"<<cleanClock(elapsed())<<"s] JOSHUA scenario: user-forced opening move "<<cfg.firstMove<<" | Figur="<<description(b,*it)<<" | SAN="<<notationSan(b,*it,legalMoves)<<" (not engine-selected)\n";b=apply(b,*it);played.push_back(cfg.firstMove);history[repetitionKey(b)]++;actual++;
 }
 for(int h=actual;h<cfg.maxPlies;h++){
   auto legalMoves=legal(b);if(legalMoves.empty()){std::cout<<"[+"<<cleanClock(elapsed())<<"s] "<<(check(b,b.turn)?"CHECKMATE":"STALEMATE")<<"\n";break;}
   if(b.half>=100||minorDraw(b)||history[repetitionKey(b)]>=3){std::cout<<"[+"<<cleanClock(elapsed())<<"s] DRAW under chosen auto-claim policy\n";break;}
   const double begin=elapsed();std::cout<<"[+"<<cleanClock(begin)<<"s] ply="<<(h+1)<<" "<<(b.turn==1?"WHITE":"BLACK")<<" legal="<<legalMoves.size()<<"; BUILD search tree\n";
   Metrics m;Times t;vector<string>ranking;vector<double>values;string best=worker.outputTree(b,cfg.depth,h,m,t,ranking,values);
   const double now=elapsed();Board old=b;auto it=std::find_if(legalMoves.begin(),legalMoves.end(),[&](const Move&mv){return uci(mv)==best;});insist(it!=legalMoves.end(),"Generated move not legal at root");
   const string piece=pieceNameGerman(old.b[it->f]);
   const string san=notationSan(old,*it,legalMoves);
   const bool capture=(old.b[it->t]!='.'||it->ep);
   const string promotion=it->promo==' '?"":pieceNameGerman(it->promo);
   const string moveDescription=description(old,*it);
   b=apply(b,*it);played.push_back(best);history[repetitionKey(b)]++;
   const double val=values[0];
   std::cout<<"[+"<<cleanClock(begin+t.generated)<<"s] tree nodes="<<m.nodes<<" leaves="<<m.leaves<<" | gen_s="<<cleanClock(t.generated)<<"\n";
   std::cout<<"[+"<<cleanClock(begin+t.generated+t.features)<<"s] paceval features unique="<<m.uniqueVectors<<" point_checks="<<m.scoreChecks<<" batch_calls="<<m.scoreBatches<<" | stage_s="<<cleanClock(t.features)<<"\n";
   std::cout<<"[+"<<cleanClock(now)<<"s] paceval minmax checks="<<m.reductionChecks<<" batch_calls="<<m.reductionBatches<<" new_graphs="<<m.newGraphs<<" | stage_s="<<cleanClock(t.reduced)<<"\n";
   std::cout<<"[+"<<cleanClock(now)<<"s] JOSHUA BEST "<<(old.turn==1?"WHITE":"BLACK")<<" "<<best<<" | Figur="<<moveDescription<<" | SAN="<<san<<" | score_white="<<val<<"cp | FEN "<<toFen(b)<<"\n";
   if(cfg.printBoard)boardAscii(b);
   timeline<<h+1<<','<<(old.turn==1?"white":"black")<<','<<cleanClock(begin)<<','<<cleanClock(begin+t.generated)<<','<<cleanClock(begin+t.generated+t.features)<<','<<cleanClock(now)<<','<<cleanClock(t.generated)<<','<<cleanClock(t.features)<<','<<cleanClock(t.reduced)<<','<<legalMoves.size()<<','<<m.nodes<<','<<m.leaves<<','<<m.terminal<<','<<m.uniqueVectors<<','<<m.newGraphs<<','<<m.scoreBatches<<','<<m.reductionBatches<<','<<m.graphPoints<<','<<best<<",\""<<piece<<"\",\""<<san<<"\","<<sq(it->f)<<','<<sq(it->t)<<','<<(capture?1:0)<<",\""<<promotion<<"\","<<val<<",\""<<toFen(old)<<"\",\""<<toFen(b)<<"\"\n";
   for(size_t i=0;i<ranking.size();i++)moves<<h+1<<','<<cfg.depth<<','<<(old.turn==1?"white":"black")<<','<<i+1<<','<<ranking[i]<<','<<values[i]<<'\n';
   insist(bool(timeline)&&bool(moves),"CSV write failed");
 }
 pgn<<"# JOSHUA chess self-play, UCI moves, not PGN SAN\n";for(auto&s:played)pgn<<s<<' ';pgn<<"\nfinal_fen "<<toFen(b)<<"\n";
 evidence<<"{\n"<<"  \"engine_name\": \"JOSHUA\",\n"<<"  \"opponents\": \"JOSHUA vs JOSHUA only\",\n"<<"  \"sdk\": \"local paceval 4.25-compatible original shared library\",\n"<<"  \"mcp_used\": false,\n"<<"  \"search_mode\": \"unpruned_full_width_minimax\",\n"<<"  \"depth_each_move\": "<<cfg.depth<<",\n"<<"  \"model\": "<<cfg.model<<",\n"<<"  \"played_halfmoves\": "<<played.size()<<",\n"<<"  \"max_halfmoves\": "<<cfg.maxPlies<<",\n"<<"  \"maximum_batch_rows\": "<<cfg.batchSize<<",\n"<<"  \"all_formulas_reused\": true,\n"<<"  \"leaf_multi_graph_count\": "<<form.expr.size()<<",\n"<<"  \"all_minmax_reductions_via_paceval\": true,\n"<<"  \"paceval_graphs_created\": "<<engine.owned.size()<<",\n"<<"  \"paceval_batch_calls\": "<<engine.batches<<",\n"<<"  \"paceval_graph_point_evaluations\": "<<engine.graphPoints<<",\n"<<"  \"elapsed_seconds\": "<<cleanClock(elapsed())<<",\n"<<"  \"finished_game\": "<<(legal(b).empty()?"true":"false")<<",\n"<<"  \"final_fen\": \""<<jsonEscape(toFen(b))<<"\",\n"<<"  \"note\": \"Heuristic depth-limited selfplay; not proof of best chess play or engine-strength benchmark\"\n}\n";
 std::cout<<"[+"<<cleanClock(elapsed())<<"s] JOSHUA SELF-PLAY END plies="<<played.size()<<" paceval_graphs="<<engine.owned.size()<<" paceval_batch_calls="<<engine.batches<<" graph_points="<<engine.graphPoints<<"\n";
 return 0;
}
int main(int argc,char**argv){try{
 Config c;for(int i=1;i<argc;i++){
  string a=argv[i];auto value=[&]()->string{insist(i+1<argc,"Missing parameter for "+a);return argv[++i];};
  if(a=="--help"){std::cout<<"Usage: joshua [--depth 1..4] [--plies 1..200] [--model 1|2] [--fen SIX_PART_FEN] [--first-move e2e4] [--batch-rows 1..65536] [--max-nodes N] [--no-board] [--output DIR]\nDefault: JOSHUA plays both White and Black at depth 3; local paceval SDK only.\n";return 0;}else if(a=="--depth")c.depth=std::stoi(value());else if(a=="--plies")c.maxPlies=std::stoi(value());else if(a=="--model")c.model=std::stoi(value());else if(a=="--batch-rows")c.batchSize=std::stoul(value());else if(a=="--max-nodes")c.maxNodes=std::stoul(value());else if(a=="--output")c.output=value();else if(a=="--fen")c.startFen=value();else if(a=="--first-move")c.firstMove=value();else if(a=="--no-board")c.printBoard=false;else if(a=="--selftest")c.selftest=true;else throw std::runtime_error("Unknown flag: "+a);
 }
 insist(c.depth>=1&&c.depth<=4,"--depth must be 1..4; tree budget protects memory");insist(c.maxPlies>=1&&c.maxPlies<=200,"--plies must be 1..200");insist(c.model==1||c.model==2,"--model must be 1 or 2");insist(c.batchSize>=1&&c.batchSize<=65536,"--batch-rows must be 1..65536");
 if(c.selftest){
  // Verify the displayed piece and SAN against concrete legal positions.
  const auto checkNotation=[&](const string&position,const string&uciMove,const string&expectedPiece,const string&expectedSan){
   const Board b=fen(position);const auto lm=legal(b);
   const auto it=std::find_if(lm.begin(),lm.end(),[&](const Move&m){return uci(m)==uciMove;});
   insist(it!=lm.end(),"Test move is not legal: "+uciMove);
   insist(pieceNameGerman(b.b[it->f])==expectedPiece,"Displayed piece name mismatch: "+uciMove);
   insist(notationSan(b,*it,lm)==expectedSan,"SAN mismatch: "+uciMove+" expected "+expectedSan+" got "+notationSan(b,*it,lm));
  };
  checkNotation(START_FEN,"b1c3","Springer (Pferd)","Nc3");
  checkNotation(START_FEN,"e2e4","Bauer","e4");
  checkNotation("rnbqkbnr/pppppppp/8/8/4P3/2N5/PPPP1PPP/R1BQKBNR b KQkq e3 0 1","b8c6","Springer (Pferd)","Nc6");
  checkNotation("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1","e1g1","König","O-O");
  checkNotation("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1","e1c1","König","O-O-O");
  checkNotation("4k3/6P1/8/8/8/8/8/4K3 w - - 0 1","g7g8q","Bauer","g8=Q+");
  checkNotation("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1","e5d6","Bauer","exd6");
  const Board s=fen(START_FEN);const size_t targets[]={0,20,400,8902,197281};for(int dep=1;dep<=4;dep++)insist(perft(s,dep)==targets[dep],"Perft mismatch at depth "+std::to_string(dep));Engine e;e.probe();Evaluator ev(e);auto z=ev.evaluate(s);near(z[ev.by.at("V1_SCORE")],0,1e-12);near(z[ev.by.at("V2_SCORE")],0,1e-12);std::cout<<"JOSHUA_SELFTEST_PASS piece_names_SAN_castling_promotion_enpassant=PASS perft4=197281 sdk_graphs="<<e.owned.size()<<"\n";return 0;}
 return runGame(c);
 }catch(const std::exception&ex){std::cerr<<"ERROR: "<<ex.what()<<"\n";return 1;}}
