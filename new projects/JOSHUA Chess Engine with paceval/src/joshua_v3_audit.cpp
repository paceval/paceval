// Independently auditable V3 feature and formula evaluations from the local SDK.
#include "paceval_main.h"
#include "chess_rules.h"
#include "paceval_math.h"
#include <fstream>
int main(int argc,char**argv){try{
 insist(argc==2,"Usage: joshua_v3_audit OUTPUT_CSV");
 const vector<string> test={
  "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
  "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
  "r1bqkbnr/pppppppp/2n5/8/8/2N5/PPPPPPPP/R1BQKBNR w KQkq - 2 2",
  "8/8/8/8/8/7P/2k5/K7 w - - 0 1",
  "8/8/8/8/7P/8/2k5/K7 b - - 0 1",
  "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
  "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
  "4k3/6P1/8/8/8/8/8/4K3 w - - 0 1"
 };
 Engine e;e.probe();EvaluatorV3 g(e);vector<vector<double>> rows;for(const string&pos:test){auto b=fen(pos);rows.push_back(featuresV3(b));}
 const auto results=e.multi(g.handles(),rows);std::ofstream f(argv[1]);insist(bool(f),"Unable to write audit CSV");
 f<<"case,fen";for(auto x:featureNamesV3)f<<","<<x;for(auto x:g.expr)f<<","<<x.name;f<<"\n";
 for(size_t i=0;i<test.size();i++){near(results[i][g.by.at("SCORE")],scoreNativeV3(rows[i]),1e-12);f<<i<<","<<test[i];for(double x:rows[i])f<<","<<std::setprecision(17)<<x;for(double x:results[i])f<<","<<std::setprecision(17)<<x;f<<"\n";}
 insist(bool(f),"Failed writing audit CSV");std::cout<<"V3_AUDIT_PASS cases="<<test.size()<<" graph_count="<<g.expr.size()<<" graph_point_evaluations="<<e.graphPoints<<"\n";
 return 0;
 }catch(const std::exception&ex){std::cerr<<ex.what()<<"\n";return 1;}}
