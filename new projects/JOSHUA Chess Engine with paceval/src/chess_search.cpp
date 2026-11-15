// paceval Chess Research Engine. Independent iterative alpha-beta demonstrator.
// Legal chess rules: 0x88 C++ host. Mathematical evaluation: real paceval SDK.
// No strength superiority, formal game solution, or complete draw adjudication is claimed.
#include "paceval_main.h"
#include "chess_rules.h"
#include "paceval_math.h"
#include <chrono>
#include <unordered_map>
#include <cctype>
#include <memory>

static const string kStart="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
static const string kE4="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1";

int piece(const char x) {switch(char(std::tolower(x))){case 'p':return 100;case 'n':return 320;case 'b':return 330;case 'r':return 500;case 'q':return 900;default:return 0;}}
bool tactical(const Board&s,const Move&m){return s.b[m.t]!='.'||m.ep||m.promo!=' ';}
int order(const Board&s,const Move&m){return (m.promo!=' '?2000+piece(m.promo):0)+(tactical(s,m)?900+piece(s.b[m.t])-piece(s.b[m.f])/10:0);}
vector<Move> ordered(const Board&s){auto moves=legal(s);std::stable_sort(moves.begin(),moves.end(),[&](const Move&a,const Move&b){return order(s,a)>order(s,b);});return moves;}
string normKey(const Board&s){
 // This key is for search-path repetition ONLY and includes effective en passant.
 string z;for(int i=0;i<128;i++)if(inside(i))z.push_back(s.b[i]);z.push_back(s.turn==1?'w':'b');z.push_back(char('A'+s.castle));
 bool epLegal=false;if(s.ep>=0)for(const auto&m:legal(s))if(m.ep){epLegal=true;break;}
 if(epLegal)z+=sq(s.ep);return z;
}
bool insufficient(const Board&s){
 vector<std::pair<char,int>> v;for(int i=0;i<128;i++)if(inside(i)&&s.b[i]!='.'&&std::tolower(s.b[i])!='k')v.push_back({char(std::tolower(s.b[i])),(fileof(i)+rankof(i))%2});
 if(v.empty())return true;
 if(v.size()==1&&(v[0].first=='b'||v[0].first=='n'))return true;
 if(!v.empty()&&std::all_of(v.begin(),v.end(),[](const auto&p){return p.first=='b';})){int c=v[0].second;if(std::all_of(v.begin(),v.end(),[&](const auto&p){return p.second==c;}))return true;}
 return false;
}
struct Search {
 Engine&e; Evaluator eval; int model=2; int qdepth=6; size_t nodes=0,quietNodes=0,evalCalls=0,batchCalls=0,drawHits=0;
 vector<string>path; std::map<string,double>cache;
 Search(Engine&engine,int v):e(engine),eval(engine),model(v){insist(v==1||v==2,"model must be 1 or 2");}
 bool drawn(const Board&s){if(s.half>=100 || insufficient(s))return true;auto key=normKey(s);int repeated=0;for(const auto&k:path)if(k==key)repeated++;return repeated>=2;}
 int score(const Board&s){ // real paceval graph evaluations; score in centipawns relative to side to move
   auto x=features(s);const string cachekey=boardKey(s)+std::to_string(model);
   auto it=cache.find(cachekey);if(it!=cache.end())return int(std::lround(it->second))*s.turn;
   auto z=eval.evaluate(s);double v=z[eval.by.at(model==1?"V1_SCORE":"V2_SCORE")];cache[cachekey]=v;evalCalls++;return int(std::lround(v))*s.turn;
 }
 int quiet(const Board&s,int alpha,int beta,int ply,int remaining){
   quietNodes++;
   auto moves=ordered(s);const bool incheck=check(s,s.turn);
   if(moves.empty())return incheck?-30000+ply:0;
   if(drawn(s))return 0;
   // If in check, stand-pat is forbidden. Avoid cutting off forced evasions.
   if(remaining<=0 && !incheck)return score(s);
   if(remaining<=-4 && incheck)return score(s); // bounded research fallback, not a formal mate proof
   if(!incheck){int stand=score(s);if(stand>=beta)return stand;if(stand>alpha)alpha=stand;}
   for(const auto&m:moves){if(!incheck&&!tactical(s,m))continue;
     Board next=apply(s,m);path.push_back(normKey(s));int v=-quiet(next,-beta,-alpha,ply+1,remaining-1);path.pop_back();
     if(v>=beta)return v;if(v>alpha)alpha=v;
   }
   return alpha;
 }
 int negamax(const Board&s,int depth,int alpha,int beta,int ply){
   nodes++;
   if(depth<=0)return quiet(s,alpha,beta,ply,qdepth);
   auto moves=ordered(s);
   if(moves.empty())return check(s,s.turn)?-30000+ply:0;
   if(drawn(s))return 0;
   int best=-32000;
   for(const auto&m:moves){Board n=apply(s,m);path.push_back(normKey(s));int v=-negamax(n,depth-1,-beta,-alpha,ply+1);path.pop_back();
      if(v>best)best=v;if(v>alpha)alpha=v;if(alpha>=beta)break;}
   return best;
 }
 struct Result{string move;int value;int ply;};
 vector<Result> root(const Board&s,int depth){
   insist(depth>=1&&depth<=5,"search depth supported: 1..5");nodes=quietNodes=evalCalls=0;path.clear();path.push_back(normKey(s));
   auto moves=ordered(s);vector<Result> out;
   for(const auto&m:moves){Board n=apply(s,m);int value=-negamax(n,depth-1,-32000,32000,1);out.push_back({uci(m),value,depth});}
   std::sort(out.begin(),out.end(),[](const Result&a,const Result&b){return a.value==b.value?a.move<b.move:a.value>b.value;});return out;
 }
 void show(const Board&s,int depth,const fs::path&out){
   fs::create_directories(out);
   std::ofstream csv(out/"iterative_root_scores.csv"),ev(out/"search_evidence.json");
   insist(bool(csv)&&bool(ev),"cannot write result files");
   csv<<"depth,root_move,score_side_to_move_cp,score_white_cp,root_side,model,rank\n";
   string best="";int value=0;size_t count=0;
   for(int d=1;d<=depth;d++){
     auto a=root(s,d);insist(!a.empty(),"No legal root move; use terminal detection first");
     for(size_t i=0;i<a.size();i++)csv<<d<<','<<a[i].move<<','<<a[i].value<<','<<a[i].value*s.turn<<','<<(s.turn==1?"white":"black")<<","<<model<<','<<i+1<<'\n';
     best=a[0].move;value=a[0].value;count=a.size();
     std::cout<<"info depth "<<d<<" nodes "<<nodes<<" score cp "<<value<<" pv "<<best<<"\n";
   }
   ev<<"{\n  \"root_fen\": \""<<toFen(s)<<"\",\n  \"depth\": "<<depth<<",\n  \"root_legal_moves\": "<<count<<",\n  \"best_move_uci\": \""<<best<<"\",\n  \"value_side_to_move_centipawns\": "<<value<<",\n  \"model\": "<<model<<",\n  \"nodes_last_iteration\": "<<nodes<<",\n  \"quiescence_nodes_last_iteration\": "<<quietNodes<<",\n  \"unique_paceval_evaluation_cache_entries\": "<<cache.size()<<",\n  \"graph_point_evaluations\": "<<e.graphPoints<<",\n  \"api_batch_calls\": "<<e.batches<<",\n  \"no_strength_claim\": true,\n  \"no_history_before_fen\": true\n}\n";
   std::cout<<"bestmove "<<best<<"\n";
 }
};
Move parseLegalUci(const Board&s,const string&text){for(const auto&m:legal(s))if(uci(m)==text)return m;throw std::runtime_error("Illegal UCI move: "+text);}
void unittest(){
 Board b=fen(kStart);insist(legal(b).size()==20,"start 20");
 Move m=parseLegalUci(b,"e2e4");b=apply(b,m);insist(toFen(b)==kE4,"e4 FEN mismatch");insist(legal(b).size()==20,"e4 replies 20");
 auto c=apply(b,parseLegalUci(b,"c7c5"));insist(c.b[ix("c5")]=='p'&&c.b[ix("e4")]=='P'&&c.turn==1,"Sicilian diagram invalid");
 auto d=apply(c,parseLegalUci(c,"g1f3"));insist(d.b[ix("f3")]=='N'&&d.b[ix("g1")]=='.',"Sicilian knight diagram invalid");
 auto e=apply(b,parseLegalUci(b,"e7e5"));insist(e.b[ix("e5")]=='p',"e5 diagram invalid");
 Board mat=fen("7k/6Q1/5K2/8/8/8/8/8 b - - 0 1");insist(legal(mat).empty()&&check(mat,-1),"mate test");
 Board sm=fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1");insist(legal(sm).empty()&&!check(sm,-1),"stalemate test");
 for(int dep=1;dep<=4;dep++){const size_t expected[]={0,20,400,8902,197281};insist(perft(fen(kStart),dep)==expected[dep],"Perft failure");}
 Engine eng;eng.probe();Search search(eng,2);auto x=search.root(b,2);insist(x.size()==20,"search must consider all 20 black replies");
 for(const auto&r:x)insist(std::abs(r.value)<30001,"invalid numeric search value");
 std::cout<<"SEARCH_SELFTEST_PASS start_perft4=197281 e4_replies=20 search_depth=2 paceval_graphs="<<eng.owned.size()<<" graph_points="<<eng.graphPoints<<"\n";
}
int main(int argc,char**argv){try{
 string root=kE4,out="results",mode="search";int depth=3,model=2;
 for(int i=1;i<argc;i++){const string a=argv[i];if(a=="--selftest")mode="test";else if(a=="--fen"&&i+1<argc)root=argv[++i];else if(a=="--depth"&&i+1<argc)depth=std::stoi(argv[++i]);else if(a=="--model"&&i+1<argc)model=std::stoi(argv[++i]);else if(a=="--output"&&i+1<argc)out=argv[++i];else if(a=="--perft"&&i+1<argc){mode="perft";depth=std::stoi(argv[++i]);}else throw std::runtime_error("Usage: chess_search [--fen '6-part FEN'] [--depth 1..5] [--model 1|2] [--output DIR] | --perft DEPTH | --selftest");}
 if(mode=="test"){unittest();return 0;}
 Board start=fen(root);insist(!check(start,-start.turn),"Illegal FEN: previous mover is in check");
 if(mode=="perft"){insist(depth>=0&&depth<=6,"perft depth 0..6");std::cout<<"PERFT "<<perft(start,depth)<<"\n";return 0;}
 insist(depth>=1&&depth<=5,"depth must be 1..5");Engine e;e.probe();Search search(e,model);search.show(start,depth,out);return 0;
 }catch(const std::exception&ex){std::cerr<<"ERROR "<<ex.what()<<"\n";return 1;}}
