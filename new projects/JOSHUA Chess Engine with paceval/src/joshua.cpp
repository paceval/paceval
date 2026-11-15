// JOSHUA Chess Engine. Linux C++17; only JOSHUA vs JOSHUA; local paceval runtime only.
// Research mode builds a complete bounded search tree; Alpha-Beta supports depth 10.
// All distinct nonterminal leaf feature vectors are evaluated by the real paceval
// multi-graph batch API; all internal min/max reductions are evaluated by real
// persistent paceval graphs, grouped in batch by fanout and player to move.
// This is a technical demonstration, NOT a modern chess-strength engine.
#include "paceval_main.h"
#include "selfplay_exploration.h"
#include "chess_rules.h"
#include "paceval_math.h"
#include "v4_paceval.h"
#include <chrono>
#include <functional>
#include <ctime>
#include <memory>
#include <unordered_map>
#include <climits>
#include <tuple>
#include <utility>
using Clock=std::chrono::steady_clock;
static const string START_FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
struct Config {int depth=3,maxPlies=80,model=3,qdepth=0;size_t batchSize=8192,maxNodes=600000;string startFen=START_FEN,firstMove="",output="results",mode="alphabeta";bool selftest=false, printBoard=true;int explorePlies=0;double exploreCp=0.0;std::uint64_t gameSeed=0;};
// Compact nodes store only graph topology and metadata, not a full chessboard.
// All child indices belong to one contiguous slice of a global edge array.
struct Node {int firstEdge=0,count=0,ply=0,featureId=-1,terminal=0,turn=1;double val=0;Move action{};};
struct Times {double generated=0,features=0,reduced=0;};
struct Metrics {size_t nodes=0,leaves=0,terminal=0,uniqueVectors=0,scoreBatches=0,reductionBatches=0,newGraphs=0,graphPoints=0,scoreChecks=0,reductionChecks=0,ttHits=0,prunes=0;};
string cleanClock(double s){std::ostringstream o;o<<std::fixed<<std::setprecision(6)<<s;return o.str();}
string jsonEscape(const string&s){string r;for(char c:s){if(c=='\\'||c=='"')r+='\\';if(c=='\n')r+="\\n";else r+=c;}return r;}
void boardAscii(const Board&b){std::cout<<"    a b c d e f g h\n";for(int r=0;r<8;r++){std::cout<<" "<<(8-r)<<"  ";for(int f=0;f<8;f++)std::cout<<b.b[r*16+f]<<' ';std::cout<<" "<<(8-r)<<"\n";}std::cout<<"    a b c d e f g h\n";}
int scoreNative(const vector<double>&v,int model){insist(v.size()==19,"score input width mismatch");double x=100*(v[0]-v[5])+320*(v[1]-v[6])+330*(v[2]-v[7])+500*(v[3]-v[8])+900*(v[4]-v[9]);if(model==2)x+=13*(v[10]-v[11])+17*(v[12]-v[13])+3*(v[14]-v[15])+18*(v[16]-v[17]);return int(std::lround(x));}
// Selfplay follows explicit draw claims at 50 moves and 3-fold repetition;
// no such rules are inferred from a heuristic leaf value.
string repetitionKey(const Board&s){string k;for(int i=0;i<128;i++)if(inside(i))k.push_back(s.b[i]);k+=(s.turn==1?'w':'b');k+=char('A'+s.castle);bool hasLegalEp=false;if(s.ep>=0)for(const Move&m:legal(s))if(m.ep){hasLegalEp=true;break;}if(hasLegalEp)k+=sq(s.ep);return k;}
bool minorDraw(const Board&s){int minors=0;bool other=false;int bColor=-1;bool allSameBishops=true;for(int i=0;i<128;i++){if(!inside(i))continue;char p=char(std::tolower(s.b[i]));if(p=='.'||p=='k')continue;if(p=='p'||p=='r'||p=='q')other=true;else if(p=='b'){minors++;int c=(rankof(i)+fileof(i))%2;if(bColor<0)bColor=c;else if(bColor!=c)allSameBishops=false;}else if(p=='n'){minors++;allSameBishops=false;}}return !other&&(minors==0||minors==1||(allSameBishops&&minors>0));}
struct TreeWorker {
 Engine&e;Evaluator&formula;EvaluatorV3&v3;NeuralV4* nn;const Config&cfg;double startS=0;
 std::map<std::pair<int,int>,PACEVAL_HANDLE> reductions;
 TreeWorker(Engine&x,Evaluator&f,EvaluatorV3&enhanced,NeuralV4* neural,const Config&c):e(x),formula(f),v3(enhanced),nn(neural),cfg(c){}
 PACEVAL_HANDLE reduction(int fanout,int turn,Metrics&met){insist(fanout>=2&&fanout<=218,"Invalid reduction arity");auto key=std::make_pair(fanout,turn);auto it=reductions.find(key);if(it!=reductions.end())return it->second;vector<string>vars;string expression="(";for(int i=0;i<fanout;i++){vars.push_back("v"+std::to_string(i));if(i)expression+=(turn==1?" max ":" min ");expression+=vars.back();}expression+=")";PACEVAL_HANDLE h=e.create(expression,vars);met.newGraphs++;reductions[key]=h;return h;}
 string outputTree(const Board&root,int requestedDepth,int turnNo,Metrics&met,Times&tm,vector<string>&ranked,vector<double>&values){
    auto beg=Clock::now();vector<Node>nodes;nodes.reserve(18000);
    vector<int>edges;edges.reserve(18000);
    vector<vector<int>>byDepth(requestedDepth+1);
    std::map<vector<double>,int>intern;vector<vector<double>>uni;
    // All nodes are generated from one mutable board with lossless make/unmake.
    Board work=root;
    std::function<int(int,Move)> grow = [&](int depth,Move action)->int{
      insist(nodes.size()<cfg.maxNodes,"Maximum tree node budget reached; lower --depth or increase --max-nodes");
      const int id=int(nodes.size());nodes.emplace_back();nodes[id].ply=depth;nodes[id].turn=work.turn;nodes[id].action=action;
      byDepth[depth].push_back(id);
      auto moves=legal(work);
      if(moves.empty()){nodes[id].terminal=check(work,work.turn)?(work.turn==1?-1:1):2;return id;}
      if(work.half>=100||minorDraw(work)){nodes[id].terminal=2;return id;}
      if(depth==requestedDepth){
        auto fv=cfg.model==4?featuresV4(work):(cfg.model==3?featuresV3(work):features(work));auto it=intern.find(fv);
        if(it!=intern.end())nodes[id].featureId=it->second;
        else {const int ix=int(uni.size());intern.emplace(fv,ix);uni.push_back(std::move(fv));nodes[id].featureId=ix;}
        return id;
      }
      const int first=int(edges.size());edges.resize(edges.size()+moves.size(),-1);
      nodes[id].firstEdge=first;nodes[id].count=int(moves.size());
      for(size_t i=0;i<moves.size();i++){
         const MoveUndo saved=makeMove(work,moves[i]);
         const int child=grow(depth+1,moves[i]);
         unmakeMove(work,moves[i],saved);
         edges[first+i]=child;
      }
      return id;
    };
    grow(0,Move{});tm.generated=std::chrono::duration<double>(Clock::now()-beg).count();met.nodes=nodes.size();
    met.uniqueVectors=uni.size();
    // Evaluate ALL nonterminal leaf feature vectors with genuine local paceval multi-graph batches.
    beg=Clock::now();
    for(auto&n:nodes)if(n.count==0){
      met.leaves++;
      if(n.terminal){met.terminal++;n.val=n.terminal==2?0:(n.terminal==1?30000-n.ply:-30000+n.ply);}
    }
    const size_t scoreIx=cfg.model==3?v3.by.at("SCORE"):formula.by.at(cfg.model==1?"V1_SCORE":"V2_SCORE");
    vector<double>scores(uni.size());
    for(size_t i=0;i<uni.size();i+=cfg.batchSize){
      const size_t end=std::min(uni.size(),i+cfg.batchSize);
      vector<vector<double>>rows(uni.begin()+i,uni.begin()+end);
      if(cfg.model==4){
        insist(nn!=nullptr,"V4 neural evaluator is not initialized");
        vector<vector<double>>first32;first32.reserve(rows.size());
        for(const auto&r:rows)first32.emplace_back(r.begin(),r.begin()+32);
        auto components=e.multi(v3.handles(),first32);
        vector<double>base;for(size_t j=0;j<rows.size();j++){
          const double classical=components[j][v3.by.at("SCORE")];
          near(classical,scoreNativeV3(first32[j]),1e-12);base.push_back(classical);
        }
        auto nnOutputs=nn->scoreBatch(rows,base);
        met.scoreBatches+=3;
        for(size_t j=0;j<rows.size();j++){
           scores[i+j]=nnOutputs[j];met.scoreChecks++;
        }
      }else{
        auto computed=e.multi(cfg.model==3?v3.handles():formula.handles(),rows);met.scoreBatches++;
        for(size_t j=0;j<rows.size();j++){
          double x=computed[j][scoreIx];int reference=cfg.model==3?scoreNativeV3(rows[j]):scoreNative(rows[j],cfg.model);
          near(x,reference,1e-12);scores[i+j]=x;met.scoreChecks++;
        }
      }
    }
    for(Node&n:nodes)if(n.featureId>=0)n.val=scores[n.featureId];
    tm.features=std::chrono::duration<double>(Clock::now()-beg).count();
    // Exact fixed-depth minimax using local paceval max/min graphs, grouped by fanout.
    beg=Clock::now();for(int depth=requestedDepth-1;depth>=0;depth--){
      std::map<std::pair<int,int>,vector<int>> groups;
      for(int id:byDepth[depth]){Node&n=nodes[id];if(n.count==0)continue;
        if(n.count==1){n.val=nodes[edges[n.firstEdge]].val;continue;}
        groups[{n.count,n.turn}].push_back(id);
      }
      for(const auto&kv:groups){const int f=kv.first.first,t=kv.first.second;
        auto h=reduction(f,t,met);const auto&ids=kv.second;
        for(size_t at=0;at<ids.size();at+=cfg.batchSize){size_t end=std::min(ids.size(),at+cfg.batchSize);
          vector<vector<double>>rows;rows.reserve(end-at);
          for(size_t p=at;p<end;p++){const Node&n=nodes[ids[p]];vector<double>values;values.reserve(f);
            for(int k=0;k<n.count;k++)values.push_back(nodes[edges[n.firstEdge+k]].val);
            rows.push_back(std::move(values));}
          auto result=e.single(h,rows);met.reductionBatches++;
          for(size_t p=0;p<rows.size();p++){const int id=ids[at+p];
            auto mm=std::minmax_element(rows[p].begin(),rows[p].end());
            double expected=t==1?*mm.second:*mm.first;
            near(result[p],expected,1e-12);nodes[id].val=result[p];met.reductionChecks++;}
        }
      }
    }
    tm.reduced=std::chrono::duration<double>(Clock::now()-beg).count();
    insist(nodes[0].count>0,"No legal moves available at root");
    struct R{string move;double score;};vector<R>rr;
    for(int k=0;k<nodes[0].count;k++){
      const Node&child=nodes[edges[nodes[0].firstEdge+k]];
      rr.push_back({uci(child.action),child.val});
    }
    std::sort(rr.begin(),rr.end(),[&](const R&a,const R&b){if(a.score!=b.score)return root.turn==1?a.score>b.score:a.score<b.score;return a.move<b.move;});
    for(const auto&r:rr){ranked.push_back(r.move);values.push_back(r.score);}
    met.graphPoints=e.graphPoints;
    return rr[0].move;
 }
};
// Optional, exact fixed-horizon alpha-beta mode. C++ maintains alpha/beta bounds,
// and a conservative transposition table. Only the *local* paceval SDK evaluates
// leaf formulas and the final root min/max graph. No external opponents or MCP.
// This mode is not a full-width enumeration; its node count is visited nodes.
struct AlphaBetaWorker {
 Engine&e; Evaluator&formula; EvaluatorV3&v3; NeuralV4* nn; const Config&cfg;
 struct TTEntry {int depth=0,ply=0;double value=0;int bound=0;Move best{};};
 // bounds: 0 EXACT, 1 LOWER, 2 UPPER.
 std::unordered_map<string,TTEntry> tt;
 std::map<vector<double>,double> scoreCache;
 std::set<vector<double>> visitedFeatures;
 std::map<std::pair<int,int>,PACEVAL_HANDLE> rootGraphs;
 size_t visited=0,evalLeaves=0,terminalLeaves=0,ttHits=0,prunes=0,scoreMisses=0;
 explicit AlphaBetaWorker(Engine&x,Evaluator&f,EvaluatorV3&enhanced,NeuralV4* neural,const Config&c):e(x),formula(f),v3(enhanced),nn(neural),cfg(c){}
 double leafScore(const Board&b){
   auto f=cfg.model==4?featuresV4(b):(cfg.model==3?featuresV3(b):features(b));
   visitedFeatures.insert(f);auto it=scoreCache.find(f);
   if(it!=scoreCache.end())return it->second*b.turn;
   double white=0.0;
   if(cfg.model==4){
      insist(nn!=nullptr,"V4 neural evaluator is not initialized");
      vector<double>v3inputs(f.begin(),f.begin()+32);
      const double base=e.eval(v3.expr[v3.by.at("SCORE")].h,v3inputs);
      near(base,scoreNativeV3(v3inputs),1e-12);
      white=nn->scoreOne(f,base);
   }else{
      const size_t ix=cfg.model==3?v3.by.at("SCORE"):formula.by.at(cfg.model==1?"V1_SCORE":"V2_SCORE");
      // All scalar scores are calculated using the real persistent paceval handle.
      white=e.eval(cfg.model==3?v3.expr[ix].h:formula.expr[ix].h,f);
      near(white,cfg.model==3?scoreNativeV3(f):scoreNative(f,cfg.model),1e-12);
   }
   scoreCache.emplace(std::move(f),white);scoreMisses++;
   return white*b.turn;
 }
 static int moveOrder(const Board&b,const Move&m){
   auto worth=[](char p)->int{switch(std::tolower(static_cast<unsigned char>(p))){case 'p':return 100;case 'n':return 320;case 'b':return 330;case 'r':return 500;case 'q':return 900;default:return 0;}};
   const int capture=(m.ep?100:worth(b.b[m.t]));
   return (m.promo!=' '?1800+worth(m.promo):0)+(capture?200+capture-worth(b.b[m.f])/20:0);
 }
 static void orderMoves(vector<Move>&moves,const Board&b,const Move&best){
   std::stable_sort(moves.begin(),moves.end(),[&](const Move&a,const Move&c){
    const bool aa=(uci(a)==uci(best)), cc=(uci(c)==uci(best));if(aa!=cc)return aa;
    return moveOrder(b,a)>moveOrder(b,c);
   });
 }
 // Bounded capture/evasion quiescence. This is a selective extension, not an
 // exact fixed-horizon minimax evaluation and not a proven tactical oracle.
 double quiescence(Board&b,double alpha,double beta,int ply,int budget){
   visited++;
   const auto moves=legal(b);
   const bool inCheck=check(b,b.turn);
   if(moves.empty()){terminalLeaves++;return inCheck?-30000.0+ply:0.0;}
   if(b.half>=100||minorDraw(b)){terminalLeaves++;return 0.0;}
   const double stand=leafScore(b);evalLeaves++;
   if(!inCheck){if(stand>=beta)return stand;if(stand>alpha)alpha=stand;}
   if(budget<=0){
     if(!inCheck)return stand;
     // Never declare an in-check position quiet at the tactical horizon.
     // Extend forced evasions by one legal reply only, then evaluate the
     // resulting nonterminal position. This is bounded, not a mate oracle.
     double bestEvasion=-32001.0;
     for(const Move&m:moves){
       const auto undo=makeMove(b,m);
       const auto replies=legal(b);
       double v=0.0;
       if(replies.empty()){
          const bool mate=check(b,b.turn);
          v=mate?(30000.0-(ply+1)):0.0;
          terminalLeaves++;
       }else if(b.half>=100||minorDraw(b)){v=0.0;terminalLeaves++;}
       else{v=-leafScore(b);evalLeaves++;}
       unmakeMove(b,m,undo);
       bestEvasion=std::max(bestEvasion,v);
     }
     return bestEvasion;
   }
   vector<Move>tactical;
   for(const Move&m:moves)if(inCheck||b.b[m.t]!='.'||m.ep||m.promo!=' ')tactical.push_back(m);
   orderMoves(tactical,b,Move{});
   double best=inCheck?-32001.0:stand;
   for(const Move&m:tactical){auto undo=makeMove(b,m);
      const double z=-quiescence(b,-beta,-alpha,ply+1,budget-1);
      unmakeMove(b,m,undo);
      if(z>best)best=z;
      if(z>alpha)alpha=z;
      if(alpha>=beta){prunes++;break;}
   }
   return best;
 }
 double search(Board&b,int remaining,double alpha,double beta,int ply){
   visited++;
   const auto movesOrig=legal(b); // detect checkmate/stalemate even at leaves
   if(movesOrig.empty()){terminalLeaves++;return check(b,b.turn)?(-30000.0+ply):0.0;}
   if(b.half>=100||minorDraw(b)){terminalLeaves++;return 0.0;}
   if(remaining==0){if(cfg.qdepth>0)return quiescence(b,alpha,beta,ply,cfg.qdepth);evalLeaves++;return leafScore(b);}
   const double originalAlpha=alpha,originalBeta=beta;
   const string key=boardKey(b)+"|"+std::to_string(b.half)+"|"+std::to_string(remaining)+"|"+std::to_string(ply);
   auto found=tt.find(key);Move preferred{};
   if(found!=tt.end()){
      ttHits++;const auto&v=found->second;preferred=v.best;
      if(v.bound==0)return v.value;
      if(v.bound==1)alpha=std::max(alpha,v.value);
      else beta=std::min(beta,v.value);
      if(alpha>=beta)return v.value;
   }
   auto moves=movesOrig;orderMoves(moves,b,preferred);
   double best=-32001.0;Move bestMove{};
   for(const auto&m:moves){
      const MoveUndo u=makeMove(b,m);
      const double val=-search(b,remaining-1,-beta,-alpha,ply+1);
      unmakeMove(b,m,u);
      if(val>best){best=val;bestMove=m;}
      if(val>alpha)alpha=val;
      if(alpha>=beta){prunes++;break;}
   }
   // Only reuse bounds with correct proof direction.
   const int bound=best<=originalAlpha?2:(best>=originalBeta?1:0);
   tt[key]={remaining,ply,best,bound,bestMove};
   return best;
 }
 PACEVAL_HANDLE rootGraph(int fanout,int turn,Metrics&met){
   auto key=std::make_pair(fanout,turn);auto it=rootGraphs.find(key);if(it!=rootGraphs.end())return it->second;
   vector<string>vars;string expression="(";
   for(int i=0;i<fanout;i++){auto name="v"+std::to_string(i);vars.push_back(name);if(i)expression+=(turn==1?" max ":" min ");expression+=name;}
   expression+=")";auto h=e.create(expression,vars);rootGraphs[key]=h;met.newGraphs++;return h;
 }
 string outputTree(const Board&root,int depth,int turnNo,Metrics&met,Times&tm,vector<string>&ranked,vector<double>&values){
   visited=evalLeaves=terminalLeaves=ttHits=prunes=scoreMisses=0;visitedFeatures.clear();
   const auto begin=Clock::now();std::map<string,double> finalResults;
   auto base=legal(root);insist(!base.empty(),"No root moves");
   // Iterative deepening. Each root alternative is searched with a full window,
   // ensuring its reported score is exact at that depth, not just a bound.
   for(int d=1;d<=depth;d++){
     tt.clear();finalResults.clear();
     for(const auto&m:base){
       Board child=root;const auto u=makeMove(child,m);
       const double v=-search(child,d-1,-32001.0,32001.0,1);
       finalResults.emplace(uci(m),v*root.turn);
     }
   }
   tm.generated=std::chrono::duration<double>(Clock::now()-begin).count();
   met.nodes=visited;met.leaves=evalLeaves;met.terminal=terminalLeaves;
   met.uniqueVectors=visitedFeatures.size();met.scoreChecks=scoreMisses;met.ttHits=ttHits;met.prunes=prunes;
   met.scoreBatches=0; // This alpha-beta mode uses genuine scalar paceval calls.
   tm.features=0.0;
   // Final root-value reduction still runs in a persistent paceval graph.
   const auto reduceStart=Clock::now();
   vector<string>keyMoves;vector<double>rootValues;
   for(const auto&m:base){keyMoves.push_back(uci(m));rootValues.push_back(finalResults.at(uci(m)));}
   if(rootValues.size()>1){auto h=rootGraph(int(rootValues.size()),root.turn,met);
      const auto red=e.single(h,{rootValues});met.reductionBatches++;
      auto mm=std::minmax_element(rootValues.begin(),rootValues.end());
      near(red[0],root.turn==1?*mm.second:*mm.first,1e-12);met.reductionChecks++;
   }
   tm.reduced=std::chrono::duration<double>(Clock::now()-reduceStart).count();
   struct R{string move;double value;};vector<R>rr;
   for(auto&p:finalResults)rr.push_back({p.first,p.second});
   std::sort(rr.begin(),rr.end(),[&](const R&a,const R&b){if(a.value!=b.value)return root.turn==1?a.value>b.value:a.value<b.value;return a.move<b.move;});
   for(const auto&r:rr){ranked.push_back(r.move);values.push_back(r.value);}
   met.graphPoints=e.graphPoints;
   return rr[0].move;
 }
};

// The move description is derived solely from the position BEFORE the chosen move.
// English SAN is conventional chess notation (N=knight, B=bishop); the separately
// printed English piece name makes moves clear to non-chess specialists.
string pieceNameEnglish(char p){
 switch(char(std::tolower(static_cast<unsigned char>(p)))){
 case 'p':return "Pawn"; case 'n':return "Knight";
 case 'b':return "Bishop"; case 'r':return "Rook";
 case 'q':return "Queen"; case 'k':return "King";
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
 string z=pieceNameEnglish(p)+" "+sq(m.f)+" -> "+sq(m.t);
 if(m.castle)z+=" ("+string(m.t>m.f?"kingside castling":"queenside castling")+")";
 if(before.b[m.t]!='.'||m.ep)z+=" (captures "+pieceNameEnglish(m.ep?'p':before.b[m.t])+")";
 if(m.promo!=' ')z+=" (promotes to "+pieceNameEnglish(m.promo)+")";
 return z;
}
void appendLine(std::ofstream&f,const string&s){f<<s<<'\n';insist(bool(f),"CSV/trace write failed");}
int runGame(const Config&cfg){
 auto timerStart=Clock::now();const auto elapsed=[&](){return std::chrono::duration<double>(Clock::now()-timerStart).count();};
 fs::create_directories(cfg.output);std::ofstream timeline(fs::path(cfg.output)/"selfplay_timeline.csv"),moves(fs::path(cfg.output)/"root_move_rankings.csv"),pgn(fs::path(cfg.output)/"game_uci.txt"),evidence(fs::path(cfg.output)/"run_evidence.json"),gamePgn(fs::path(cfg.output)/"game.pgn"),endState(fs::path(cfg.output)/"end_state.json");
 insist(timeline&&moves&&pgn&&evidence&&gamePgn&&endState,"Failed to create output files");
 appendLine(timeline,"halfmove,side,start_s,tree_ready_s,leaf_values_ready_s,decision_s,tree_generation_s,score_batch_s,reduction_s,legal_root_moves,tree_nodes,leaf_nodes,terminal_leaves,unique_feature_vectors,new_paceval_reduction_graphs,score_batches,reduction_batches,paceval_graph_points_total,chosen_uci,chosen_piece,chosen_san,from_square,to_square,is_capture,promotion,white_score_cp,fen_before,fen_after");
 appendLine(moves,"halfmove,depth,side,rank,uci,white_score_cp,selected");
 Board b=fen(cfg.startFen);insist(!check(b,-b.turn),"Invalid initial FEN: previous player still checked");
 std::cout<<"JOSHUA | JOSHUA (WHITE) vs JOSHUA (BLACK) | local paceval SDK | mode="<<cfg.mode<<" | depth="<<cfg.depth<<" | model="<<cfg.model<<" | qdepth="<<cfg.qdepth<<"\n";
 std::cout<<"[+"<<cleanClock(elapsed())<<"s] start FEN: "<<toFen(b)<<"\n";
 Engine engine;engine.probe();Evaluator form(engine);EvaluatorV3 advanced(engine);std::unique_ptr<NeuralV4> neural; if(cfg.model==4)neural.reset(new NeuralV4(engine));TreeWorker worker(engine,form,advanced,neural.get(),cfg);AlphaBetaWorker abworker(engine,form,advanced,neural.get(),cfg);
 std::cout<<"[+"<<cleanClock(elapsed())<<"s] paceval persistent feature graphs="<<(form.expr.size()+advanced.expr.size()+(neural?size_t(V4_HIDDEN+1):0))<<"; multi-graph layout="<<(engine.graphMajor?"graph-major":"case-major")<<"; max batch rows="<<cfg.batchSize<<"\n";
 std::map<string,int>history;history[repetitionKey(b)]++;
 if(cfg.printBoard)boardAscii(b);
 vector<string>played, playedSan;int actual=0;
 if(!cfg.firstMove.empty()){
   auto legalMoves=legal(b);auto it=std::find_if(legalMoves.begin(),legalMoves.end(),[&](const Move&m){return uci(m)==cfg.firstMove;});insist(it!=legalMoves.end(),"--first-move is not legal for starting FEN");
   std::cout<<"[+"<<cleanClock(elapsed())<<"s] JOSHUA scenario: user-forced opening move "<<cfg.firstMove<<" | Piece="<<description(b,*it)<<" | SAN="<<notationSan(b,*it,legalMoves)<<" (not engine-selected)\n";playedSan.push_back(notationSan(b,*it,legalMoves));b=apply(b,*it);played.push_back(cfg.firstMove);history[repetitionKey(b)]++;actual++;
 }
 for(int h=actual;h<cfg.maxPlies;h++){
   auto legalMoves=legal(b);if(legalMoves.empty()){std::cout<<"[+"<<cleanClock(elapsed())<<"s] "<<(check(b,b.turn)?"CHECKMATE":"STALEMATE")<<"\n";break;}
   if(b.half>=100||minorDraw(b)||history[repetitionKey(b)]>=3){std::cout<<"[+"<<cleanClock(elapsed())<<"s] DRAW under chosen auto-claim policy\n";break;}
   const double begin=elapsed();std::cout<<"[+"<<cleanClock(begin)<<"s] ply="<<(h+1)<<" "<<(b.turn==1?"WHITE":"BLACK")<<" legal="<<legalMoves.size()<<"; SEARCH legal moves\n";
   Metrics m;Times t;vector<string>ranking;vector<double>values;string best=cfg.mode=="research"?worker.outputTree(b,cfg.depth,h,m,t,ranking,values):abworker.outputTree(b,cfg.depth,h,m,t,ranking,values);
   // Optional V8 exploration selects a nearby evaluated alternative. All
   // candidate scores remain from the ORIGINAL paceval-backed root search.
   // The ranked best move and the deliberately played move are distinct data.
   const auto choice=joshua_explore::choose(values,b.turn,toFen(b),h+1,cfg.exploreCp,cfg.explorePlies,cfg.gameSeed);
   const string policyBest=best;
   if(choice.index>0){best=ranking.at(choice.index);}
   const double now=elapsed();Board old=b;auto it=std::find_if(legalMoves.begin(),legalMoves.end(),[&](const Move&mv){return uci(mv)==best;});insist(it!=legalMoves.end(),"Generated move not legal at root");
   const string piece=pieceNameEnglish(old.b[it->f]);
   const string san=notationSan(old,*it,legalMoves);
   const bool capture=(old.b[it->t]!='.'||it->ep);
   const string promotion=it->promo==' '?"":pieceNameEnglish(it->promo);
   const string moveDescription=description(old,*it);
   b=apply(b,*it);played.push_back(best);playedSan.push_back(san);history[repetitionKey(b)]++;
   const double val=values.at(choice.index);
   std::cout<<"[+"<<cleanClock(begin+t.generated)<<"s] tree nodes="<<m.nodes<<" leaves="<<m.leaves<<" | search_s="<<cleanClock(t.generated)<<"\n";
   std::cout<<"[+"<<cleanClock(begin+t.generated+t.features)<<"s] paceval features unique="<<m.uniqueVectors<<" point_checks="<<m.scoreChecks<<" batch_calls="<<m.scoreBatches<<" | stage_s="<<cleanClock(t.features)<<"\n";
   std::cout<<"[+"<<cleanClock(now)<<"s] paceval minmax checks="<<m.reductionChecks<<" batch_calls="<<m.reductionBatches<<" new_graphs="<<m.newGraphs<<" | stage_s="<<cleanClock(t.reduced)<<"\n";
   if(cfg.model==4)std::cout<<"[+"<<cleanClock(now)<<"s] V4 neural support active: "<<V4_HIDDEN<<" hidden paceval graphs + 1 fused graph; independent checks="<<(neural?neural->checked:0)<<"\n";
   if(cfg.mode=="alphabeta")std::cout<<"[+"<<cleanClock(now)<<"s] alpha-beta TT_hits="<<m.ttHits<<" cutoffs="<<m.prunes<<" leaf_scalar_paceval_evaluations="<<m.scoreChecks<<"\n";
   if(cfg.exploreCp>0.0 && h+1<=cfg.explorePlies)
     std::cout<<"[+"<<cleanClock(now)<<"s] EXPLORE ply="<<(h+1)<<" candidates="<<choice.eligible
              <<" policy_best="<<policyBest<<" played="<<best<<" loss_cp="<<choice.regretCp
              <<" seed="<<cfg.gameSeed<<"\n";
   std::cout<<"[+"<<cleanClock(now)<<"s] "<<(choice.index>0?"JOSHUA PLAYED ":"JOSHUA BEST ")<<(old.turn==1?"WHITE":"BLACK")<<" "<<best<<" | Piece="<<moveDescription<<" | SAN="<<san<<" | score_white="<<val<<"cp | FEN "<<toFen(b)<<"\n";
   if(cfg.printBoard)boardAscii(b);
   timeline<<h+1<<','<<(old.turn==1?"white":"black")<<','<<cleanClock(begin)<<','<<cleanClock(begin+t.generated)<<','<<cleanClock(begin+t.generated+t.features)<<','<<cleanClock(now)<<','<<cleanClock(t.generated)<<','<<cleanClock(t.features)<<','<<cleanClock(t.reduced)<<','<<legalMoves.size()<<','<<m.nodes<<','<<m.leaves<<','<<m.terminal<<','<<m.uniqueVectors<<','<<m.newGraphs<<','<<m.scoreBatches<<','<<m.reductionBatches<<','<<m.graphPoints<<','<<best<<",\""<<piece<<"\",\""<<san<<"\","<<sq(it->f)<<','<<sq(it->t)<<','<<(capture?1:0)<<",\""<<promotion<<"\","<<val<<",\""<<toFen(old)<<"\",\""<<toFen(b)<<"\"\n";
   for(size_t i=0;i<ranking.size();i++)moves<<h+1<<','<<cfg.depth<<','<<(old.turn==1?"white":"black")<<','<<i+1<<','<<ranking[i]<<','<<values[i]<<','<<(ranking[i]==best?1:0)<<'\n';
   insist(bool(timeline)&&bool(moves),"CSV write failed");
 }
 // State the actual chess termination, distinguishing a capped trace from a draw.
 string termination="max_halfmoves",result="*";
 const auto remainingMoves=legal(b);
 if(remainingMoves.empty()){
   if(check(b,b.turn)){termination="checkmate";result=b.turn==1?"0-1":"1-0";}
   else{termination="stalemate";result="1/2-1/2";}
 }else if(history[repetitionKey(b)]>=3){termination="threefold_repetition";result="1/2-1/2";}
 else if(b.half>=100){termination="fifty_move_rule";result="1/2-1/2";}
 else if(minorDraw(b)){termination="insufficient_material";result="1/2-1/2";}
 // This game PGN is generated from legal SAN notation recorded during play.
 gamePgn<<"[Event \"JOSHUA continuous self-play\"]\n[Site \"Local paceval SDK\"]\n[White \"JOSHUA\"]\n[Black \"JOSHUA\"]\n[Result \""<<result<<"\"]\n";
 if(cfg.startFen!=START_FEN)gamePgn<<"[SetUp \"1\"]\n[FEN \""<<cfg.startFen<<"\"]\n";
 gamePgn<<"\n";
 const Board initialPgnPosition=fen(cfg.startFen);
 int printedMoveNumber=initialPgnPosition.full;
 int printedTurn=initialPgnPosition.turn;
 for(size_t i=0;i<playedSan.size();i++){
   if(printedTurn==1)gamePgn<<printedMoveNumber<<". ";
   else if(i==0)gamePgn<<printedMoveNumber<<"... ";
   gamePgn<<playedSan[i]<<' ';
   if(printedTurn==-1)++printedMoveNumber;
   printedTurn=-printedTurn;
 }
 gamePgn<<result<<"\n";
 endState<<"{\n  \"result\": \""<<result<<"\",\n  \"termination\": \""<<termination<<"\",\n  \"played_halfmoves\": "<<played.size()<<",\n  \"final_fen\": \""<<jsonEscape(toFen(b))<<"\",\n  \"analysis_status\": \"heuristic self-play, not automatically trained\"\n}\n";
 insist(bool(gamePgn)&&bool(endState),"Failed to write final game state");
 pgn<<"# JOSHUA chess self-play, UCI moves, not PGN SAN\n";for(auto&s:played)pgn<<s<<' ';pgn<<"\nfinal_fen "<<toFen(b)<<"\n";
 evidence<<"{\n"<<"  \"engine_name\": \"JOSHUA\",\n"<<"  \"opponents\": \"JOSHUA vs JOSHUA only\",\n"<<"  \"sdk\": \"local paceval 4.25-compatible original shared library\",\n"<<"  \"mcp_used\": false,\n"<<"  \"search_mode\": \""<<cfg.mode<<"\",\n"<<"  \"depth_each_move\": "<<cfg.depth<<",\n"<<"  \"model\": "<<cfg.model<<",\n"<<"  \"trained_neural_support\": "<<(cfg.model==4?"true":"false")<<",\n"<<"  \"neural_training_teacher\": \"V3 depth-two search on synthetic chess positions; NOT Stockfish or Lc0\",\n"<<"  \"neural_graphs\": "<<(cfg.model==4?V4_HIDDEN+1:0)<<",\n"<<"  \"neural_independent_checks\": "<<(neural?neural->checked:0)<<",\n"<<"  \"exploration_window_cp\": "<<cfg.exploreCp<<",\n"<<"  \"exploration_plies\": "<<cfg.explorePlies<<",\n"<<"  \"exploration_game_seed\": "<<cfg.gameSeed<<",\n"<<"  \"quiescence_plies\": "<<cfg.qdepth<<",\n"<<"  \"played_halfmoves\": "<<played.size()<<",\n"<<"  \"max_halfmoves\": "<<cfg.maxPlies<<",\n"<<"  \"maximum_batch_rows\": "<<cfg.batchSize<<",\n"<<"  \"all_formulas_reused\": true,\n"<<"  \"leaf_multi_graph_count\": "<<(cfg.model==4?advanced.expr.size()+size_t(V4_HIDDEN+1):(cfg.model==3?advanced.expr.size():form.expr.size()))<<",\n"<<"  \"all_minmax_reductions_via_paceval\": "<<(cfg.mode=="research"?"true":"false")<<",\n"<<"  \"paceval_graphs_created\": "<<engine.owned.size()<<",\n"<<"  \"paceval_batch_calls\": "<<engine.batches<<",\n"<<"  \"paceval_graph_point_evaluations\": "<<engine.graphPoints<<",\n"<<"  \"elapsed_seconds\": "<<cleanClock(elapsed())<<",\n"<<"  \"finished_game\": "<<(legal(b).empty()?"true":"false")<<",\n"<<"  \"final_fen\": \""<<jsonEscape(toFen(b))<<"\",\n"<<"  \"note\": \"Heuristic depth-limited selfplay; not proof of best chess play or engine-strength benchmark\"\n}\n";
 std::cout<<"[+"<<cleanClock(elapsed())<<"s] JOSHUA SELF-PLAY END plies="<<played.size()<<" paceval_graphs="<<engine.owned.size()<<" paceval_batch_calls="<<engine.batches<<" graph_points="<<engine.graphPoints<<"\n";
 return 0;
}
int main(int argc,char**argv){try{
 // Flush status lines in real time although the supervisor redirects stdout
 // to a per-game log file. Numeric work remains inside the paceval engine.
 std::cout.setf(std::ios::unitbuf);
 Config c;for(int i=1;i<argc;i++){
  string a=argv[i];auto value=[&]()->string{insist(i+1<argc,"Missing parameter for "+a);return argv[++i];};
  if(a=="--help"){std::cout<<"Usage: joshua [--mode research|alphabeta] [--depth 1..10] [--plies 1..200] [--model 1|2|3|4] [--quiescence 0..4] [--fen SIX_PART_FEN] [--first-move e2e4] [--batch-rows 1..65536] [--max-nodes N] [--no-board] [--output DIR] [--explore-cp N] [--explore-plies N] [--game-seed N]\nDefault: JOSHUA plays both White and Black in Alpha-Beta mode, depth 3, V3 evaluation, local paceval SDK only.\n";return 0;}else if(a=="--mode")c.mode=value();else if(a=="--quiescence")c.qdepth=std::stoi(value());else if(a=="--depth")c.depth=std::stoi(value());else if(a=="--plies")c.maxPlies=std::stoi(value());else if(a=="--model")c.model=std::stoi(value());else if(a=="--batch-rows")c.batchSize=std::stoul(value());else if(a=="--max-nodes")c.maxNodes=std::stoul(value());else if(a=="--output")c.output=value();else if(a=="--explore-cp")c.exploreCp=std::stod(value());else if(a=="--explore-plies")c.explorePlies=std::stoi(value());else if(a=="--game-seed")c.gameSeed=std::stoull(value());else if(a=="--fen")c.startFen=value();else if(a=="--first-move")c.firstMove=value();else if(a=="--no-board")c.printBoard=false;else if(a=="--selftest")c.selftest=true;else throw std::runtime_error("Unknown flag: "+a);
 }
 insist(c.mode=="research"||c.mode=="alphabeta","--mode must be research or alphabeta");insist(c.depth>=1&&c.depth<=(c.mode=="research"?4:10),"--depth must be 1..4 (research) or 1..10 (alphabeta)");insist(c.maxPlies>=1&&c.maxPlies<=200,"--plies must be 1..200");insist(c.model>=1&&c.model<=4,"--model must be 1, 2, 3, or 4");insist(c.qdepth>=0&&c.qdepth<=4,"--quiescence must be 0..4");insist(c.qdepth==0||c.mode=="alphabeta","Quiescence is available only in alphabeta mode");insist(c.batchSize>=1&&c.batchSize<=65536,"--batch-rows must be 1..65536");
 insist(std::isfinite(c.exploreCp)&&c.exploreCp>=0.0&&c.exploreCp<=500.0&&c.explorePlies>=0&&c.explorePlies<=200,"Invalid exploration configuration");
 if(c.selftest){
  // Verify the displayed piece and SAN against concrete legal positions.
  const auto checkNotation=[&](const string&position,const string&uciMove,const string&expectedPiece,const string&expectedSan){
   const Board b=fen(position);const auto lm=legal(b);
   const auto it=std::find_if(lm.begin(),lm.end(),[&](const Move&m){return uci(m)==uciMove;});
   insist(it!=lm.end(),"Test move is not legal: "+uciMove);
   insist(pieceNameEnglish(b.b[it->f])==expectedPiece,"Displayed piece name mismatch: "+uciMove);
   insist(notationSan(b,*it,lm)==expectedSan,"SAN mismatch: "+uciMove+" expected "+expectedSan+" got "+notationSan(b,*it,lm));
  };
  checkNotation(START_FEN,"b1c3","Knight","Nc3");
  checkNotation(START_FEN,"e2e4","Pawn","e4");
  checkNotation("rnbqkbnr/pppppppp/8/8/4P3/2N5/PPPP1PPP/R1BQKBNR b KQkq e3 0 1","b8c6","Knight","Nc6");
  checkNotation("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1","e1g1","King","O-O");
  checkNotation("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1","e1c1","King","O-O-O");
  checkNotation("4k3/6P1/8/8/8/8/8/4K3 w - - 0 1","g7g8q","Pawn","g8=Q+");
  checkNotation("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1","e5d6","Pawn","exd6");
  // Compare lossless board transitions with the original independent copying
  // implementation across every legal move in a depth-three opening walk.
  size_t reversibleChecks=0;
  std::function<void(const Board&,int)> reversible=[&](const Board&source,int depth){
    if(depth==0)return;
    const auto moves=legal(source);
    for(const auto&m:moves){
       Board mutableBoard=source;const Board copied=apply(source,m);
       const MoveUndo saved=makeMove(mutableBoard,m);
       insist(toFen(mutableBoard)==toFen(copied),"makeMove differs from reference apply");
       unmakeMove(mutableBoard,m,saved);
       insist(toFen(mutableBoard)==toFen(source),"unmakeMove did not restore full original state");
       reversibleChecks++;
       reversible(copied,depth-1);
    }
  };
  reversible(fen(START_FEN),3);
  for(const auto&position: {"r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1","4k3/6P1/8/8/8/8/8/4K3 w - - 0 1","4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"})reversible(fen(position),1);
  insist(reversibleChecks>9000,"Not enough reversible tests");
  const Board s=fen(START_FEN);const size_t targets[]={0,20,400,8902,197281};for(int dep=1;dep<=4;dep++)insist(perft(s,dep)==targets[dep],"Perft mismatch at depth "+std::to_string(dep));Engine e;e.probe();Evaluator ev(e);auto z=ev.evaluate(s);near(z[ev.by.at("V1_SCORE")],0,1e-12);near(z[ev.by.at("V2_SCORE")],0,1e-12);EvaluatorV3 ev3(e);auto x3=featuresV3(s);auto actual3=e.eval(ev3.expr[ev3.by.at("SCORE")].h,x3);near(actual3,scoreNativeV3(x3),1e-12);std::cout<<"JOSHUA_SELFTEST_PASS english_piece_names_SAN_castling_promotion_enpassant=PASS perft4=197281 reversible_checks="<<reversibleChecks<<" sdk_graphs="<<e.owned.size()<<"\n";return 0;}
 return runGame(c);
 }catch(const std::exception&ex){std::cerr<<"ERROR: "<<ex.what()<<"\n";return 1;}}
