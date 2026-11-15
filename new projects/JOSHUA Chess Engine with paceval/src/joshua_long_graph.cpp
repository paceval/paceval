// JOSHUA V5 experimental *full-width* mathematical decision-tree compiler.
// Every legal move is expanded to requested depth (within explicit resource limits).
// Leaf scores and the final minimax value are evaluated with the local paceval SDK.
// A separate C++ bottom-up minimax implementation validates the paceval decision graph.
// This graph contains fixed legal topology; the same expression can be evaluated with
// different leaf-value vectors but cannot make an illegal move become legal.
#include "paceval_main.h"
#include "chess_rules.h"
#include "paceval_math.h"
#include "v4_paceval.h"
#include <chrono>
#include <memory>
#include <functional>
#include <fstream>
#include <filesystem>
#include <iomanip>
#include <sstream>
#include <algorithm>
using ClockGraph=std::chrono::steady_clock;
struct GraphNode {int firstChild=0,childCount=0,turn=1,leafIdx=-1,terminal=0,ply=0;Move move{};};
struct GraphExperiment {
 Engine engine;
 Evaluator classic;
 EvaluatorV3 v3;
 std::unique_ptr<NeuralV4> v4;
 int model, depth;
 size_t maxNodes;
 std::vector<GraphNode> nodes;
 std::vector<int> edges;
 std::vector<std::vector<double>> uniqueInputs;
 std::map<std::vector<double>,int> featureIds;
 std::vector<double> leafScores;
 size_t terminalCount=0;
 explicit GraphExperiment(int m,int d,size_t maxn):classic(engine),v3(engine),model(m),depth(d),maxNodes(maxn){
  if(model==4)v4.reset(new NeuralV4(engine));
 }
 int grow(Board&b,int ply,Move move){
  insist(nodes.size()<maxNodes,"Graph node budget reached. Lower --depth or increase --max-nodes.");
  const int id=int(nodes.size());nodes.emplace_back();nodes[id].turn=b.turn;nodes[id].ply=ply;nodes[id].move=move;
  const auto moves=legal(b);
  if(moves.empty()){nodes[id].terminal=check(b,b.turn)?(b.turn==1?-1:1):2;terminalCount++;return id;}
  if(b.half>=100){nodes[id].terminal=2;terminalCount++;return id;}
  if(ply==depth){
   auto x=model==4?featuresV4(b):featuresV3(b);
   auto it=featureIds.find(x);
   if(it==featureIds.end()){int idx=int(uniqueInputs.size());featureIds.emplace(x,idx);uniqueInputs.push_back(std::move(x));nodes[id].leafIdx=idx;}
   else nodes[id].leafIdx=it->second;
   return id;
  }
  nodes[id].firstChild=int(edges.size());nodes[id].childCount=int(moves.size());
  edges.resize(edges.size()+moves.size(),-1);
  for(size_t j=0;j<moves.size();j++){
   auto undo=makeMove(b,moves[j]);int child=grow(b,ply+1,moves[j]);unmakeMove(b,moves[j],undo);
   edges[nodes[id].firstChild+int(j)]=child;
  }
  return id;
 }
 void score(size_t rowsPerBatch){
  leafScores.assign(uniqueInputs.size(),0.0);
  for(size_t i=0;i<uniqueInputs.size();i+=rowsPerBatch){
   size_t end=std::min(uniqueInputs.size(),i+rowsPerBatch);
   std::vector<std::vector<double>> rows(uniqueInputs.begin()+i,uniqueInputs.begin()+end);
   if(model==3){
    auto all=engine.multi(v3.handles(),rows);
    for(size_t j=0;j<all.size();j++){
     double val=all[j][v3.by.at("SCORE")];
     near(val,scoreNativeV3(rows[j]),1e-12);leafScores[i+j]=val;
    }
   }else{
    std::vector<std::vector<double>> first32;
    first32.reserve(rows.size());
    for(const auto&x:rows)first32.emplace_back(x.begin(),x.begin()+32);
    auto baseMatrix=engine.multi(v3.handles(),first32);
    std::vector<double> bases;
    for(size_t j=0;j<rows.size();j++){
     const double val=baseMatrix[j][v3.by.at("SCORE")];near(val,scoreNativeV3(first32[j]),1e-12);bases.push_back(val);
    }
    auto neural=v4->scoreBatch(rows,bases);
    for(size_t j=0;j<rows.size();j++)leafScores[i+j]=neural[j];
   }
  }
 }
 double native(int i){
  const auto&n=nodes[i];
  if(n.terminal)return n.terminal==2?0.0:(n.terminal==1?30000.0-n.ply:-30000.0+n.ply);
  if(n.leafIdx>=0)return leafScores[n.leafIdx];
  double v=n.turn==1?-32001:32001;
  for(int j=0;j<n.childCount;j++){
   double x=native(edges[n.firstChild+j]);
   if(n.turn==1)v=std::max(v,x);else v=std::min(v,x);
  }
  return v;
 }
 std::string formula(int i){
  const auto&n=nodes[i];
  if(n.terminal){double val=n.terminal==2?0.0:(n.terminal==1?30000.0-n.ply:-30000.0+n.ply);return val<0?"(0-"+std::to_string(int(-val))+")":std::to_string(int(val));}
  if(n.leafIdx>=0)return "v"+std::to_string(n.leafIdx);
  if(n.childCount==1)return formula(edges[n.firstChild]);
  std::string result="(";const std::string op=n.turn==1?" max ":" min ";
  for(int j=0;j<n.childCount;j++){if(j)result+=op;result+=formula(edges[n.firstChild+j]);}
  return result+")";
 }
};
static std::string quote(const std::string&s){std::string r;for(char c:s){if(c=='"'||c=='\\')r+='\\';r+=c;}return r;}
int main(int argc,char**argv){try{
 std::string input="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
 std::string output="results/v5_long_graph";int depth=2,model=3;size_t maxNodes=35000,rows=8192,maxChars=500000;
 for(int i=1;i<argc;i++){std::string a=argv[i];auto next=[&](){insist(i+1<argc,"Missing argument for "+a);return std::string(argv[++i]);};
  if(a=="--depth")depth=std::stoi(next());else if(a=="--model")model=std::stoi(next());
  else if(a=="--fen")input=next();else if(a=="--output")output=next();
  else if(a=="--max-nodes")maxNodes=std::stoull(next());else if(a=="--max-chars")maxChars=std::stoull(next());
  else if(a=="--batch-rows")rows=std::stoull(next());else if(a=="--help"){
   std::cout<<"Usage: joshua_long_graph [--depth 1..4] [--model 3|4] [--fen FEN] [--max-nodes N] [--max-chars N] [--batch-rows N] [--output DIR]\\n";return 0;
  }else throw std::runtime_error("Unknown argument: "+a);
 }
 insist(depth>=1&&depth<=4&& (model==3||model==4),"Unsupported depth or model");
 insist(rows>=1&&rows<=65536&&maxNodes>=100&&maxChars>=100,"Invalid resource limits");
 std::filesystem::create_directories(output);
 auto allStart=ClockGraph::now();auto seconds=[&](){return std::chrono::duration<double>(ClockGraph::now()-allStart).count();};
 GraphExperiment gx(model,depth,maxNodes);
 gx.engine.probe();Board b=fen(input);insist(!check(b,-b.turn),"Illegal starting FEN");
 std::cout<<std::setprecision(9)<<std::fixed;
 std::cout<<"[+"<<seconds()<<"s] JOSHUA LONG GRAPH build full legal search depth="<<depth<<" model="<<model<<" FEN="<<input<<"\n";
 auto t=ClockGraph::now();gx.grow(b,0,Move{});const double generateS=std::chrono::duration<double>(ClockGraph::now()-t).count();
 const auto rootMoveCount=gx.nodes[0].childCount;insist(rootMoveCount>0,"Root has no moves");
 t=ClockGraph::now();gx.score(rows);const double scoreS=std::chrono::duration<double>(ClockGraph::now()-t).count();
 t=ClockGraph::now();const std::string expr=gx.formula(0);const double stringS=std::chrono::duration<double>(ClockGraph::now()-t).count();
 insist(expr.size()<=maxChars,"Generated graph exceeds expression budget. Limit depth or increase --max-chars.");
 std::vector<std::string> vars;for(size_t i=0;i<gx.uniqueInputs.size();i++)vars.push_back("v"+std::to_string(i));
 if(vars.empty())vars.push_back("v0");
 t=ClockGraph::now();
 std::ofstream expressionFile(std::filesystem::path(output)/"paceval_minimax_expression.txt");expressionFile<<expr<<"\n";expressionFile.close();
 std::string declared=join(vars);
 auto h=paceval_CreateComputation(expr.c_str(),static_cast<unsigned long>(vars.size()),declared.c_str(),false,nullptr);
 if(!h||paceval_GetIsError(h)){
   int error=-1;long position=-1;char op[256]{};
   if(h)error=paceval_GetErrorInformation(h,op,&position);
   if(h)paceval_DeleteComputation(h);
   std::ostringstream problem;problem<<"paceval rejected the full graph: characters="<<expr.size()<<" variables="<<vars.size()<<" error_code="<<error<<" error_position="<<position<<" operator="<<op;
   throw std::runtime_error(problem.str());
 }
 gx.engine.owned.push_back(h);
 const double compileS=std::chrono::duration<double>(ClockGraph::now()-t).count();
 t=ClockGraph::now();auto actual=gx.engine.single(h,{gx.leafScores.empty()?std::vector<double>{0.0}:gx.leafScores})[0];
 const double evalS=std::chrono::duration<double>(ClockGraph::now()-t).count();
 const double expected=gx.native(0);near(actual,expected,1e-10);
 // Compile once, then re-evaluate an intentionally perturbed vector WITHOUT
 // rebuilding the graph. This proves the reusable-graph claim independently.
 std::vector<double> perturbed=gx.leafScores;
 for(size_t j=0;j<perturbed.size();j++)perturbed[j]+=0.25*double(int(j%7)-3);
 t=ClockGraph::now();auto reused=gx.engine.single(h,{perturbed.empty()?std::vector<double>{0.0}:perturbed})[0];
 const double reuseS=std::chrono::duration<double>(ClockGraph::now()-t).count();
 gx.leafScores.swap(perturbed);const double reuseExpected=gx.native(0);
 near(reused,reuseExpected,1e-10);gx.leafScores.swap(perturbed);
 double best=b.turn==1?-32001:32001;std::string bestMove;
 std::ofstream ranking(std::filesystem::path(output)/"root_moves.csv");ranking<<"move,score_white_cp\n";
 for(int j=0;j<rootMoveCount;j++){
  int cid=gx.edges[gx.nodes[0].firstChild+j];double v=gx.native(cid);
  std::string move=uci(gx.nodes[cid].move);ranking<<move<<","<<v<<"\n";
  if(bestMove.empty()||(b.turn==1?v>best:v<best)||(v==best&&move<bestMove)){best=v;bestMove=move;}
 }
 near(best,actual,1e-10);
 std::string nextFen="";
 for(const Move&m:legal(b))if(uci(m)==bestMove){nextFen=toFen(apply(b,m));break;}
 insist(!nextFen.empty(),"Selected root move was not legal");
 std::ofstream f(std::filesystem::path(output)/"paceval_minimax_expression.txt");f<<expr<<"\n";
 std::ofstream values(std::filesystem::path(output)/"leaf_values.csv");values<<"input_index,score_white_cp\n";
 for(size_t j=0;j<gx.leafScores.size();j++)values<<j<<","<<std::setprecision(17)<<gx.leafScores[j]<<"\n";
 std::ofstream js(std::filesystem::path(output)/"run_evidence.json");js<<std::setprecision(12);
 js<<"{\n  \"sdk\": \"original local paceval\",\n  \"mcp_used\": false,\n  \"depth\": "<<depth<<",\n  \"model\": "<<model<<",\n  \"nodes\": "<<gx.nodes.size()<<",\n  \"terminal_nodes\": "<<gx.terminalCount<<",\n  \"unique_feature_vectors\": "<<gx.uniqueInputs.size()<<",\n  \"graph_characters\": "<<expr.size()<<",\n  \"root_legal_moves\": "<<rootMoveCount<<",\n  \"selected_move\": \""<<quote(bestMove)<<"\",\n  \"fen_before\": \""<<quote(input)<<"\",\n  \"fen_after\": \""<<quote(nextFen)<<"\",\n  \"paceval_value_cp\": "<<actual<<",\n  \"independent_cpp_minimax_cp\": "<<expected<<",\n  \"graph_generation_seconds\": "<<generateS<<",\n  \"paceval_leaf_batch_seconds\": "<<scoreS<<",\n  \"expression_serialization_seconds\": "<<stringS<<",\n  \"paceval_graph_creation_seconds\": "<<compileS<<",\n  \"paceval_graph_evaluation_seconds\": "<<evalS<<",\n  \"graph_result_verified\": true,\n  \"reused_graph_evaluation_seconds\": "<<reuseS<<",\n  \"reused_graph_value_cp\": "<<reused<<",\n  \"reused_graph_independent_cpp_cp\": "<<reuseExpected<<",\n  \"reused_graph_result_verified\": true,\n  \"elapsed_seconds\": "<<seconds()<<"\n}\n";
 std::cout<<"[+"<<seconds()<<"s] complete_tree_nodes="<<gx.nodes.size()<<" distinct_leaf_inputs="<<gx.uniqueInputs.size()<<" graph_characters="<<expr.size()<<"\n";
 std::cout<<"[+"<<seconds()<<"s] paceval_graph_compiled="<<compileS<<"s evaluation="<<evalS<<"s reuse_evaluation="<<reuseS<<"s root_value="<<actual<<" independent_value="<<expected<<"\n";
 std::cout<<"[+"<<seconds()<<"s] BEST "<<(b.turn==1?"WHITE ":"BLACK ")<<bestMove<<" score_white="<<best<<"cp VERIFIED\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<"JOSHUA LONG GRAPH ERROR: "<<e.what()<<"\n";return 1;}
}
