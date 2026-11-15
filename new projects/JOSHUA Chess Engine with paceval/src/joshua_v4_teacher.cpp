// Deterministic internal teacher set. Labels are depth-2 classical V3 minimax,
// not Stockfish, not external data, and not a claim of chess strength.
#include "paceval_main.h"
#include "chess_rules.h"
#include "paceval_math.h"
#include "joshua_v4_features.h"
#include <random>
#include <cstdlib>
using namespace std;
static double teacher(const Board&b,int depth){
   auto moves=legal(b);
   if(moves.empty())return check(b,b.turn)?(b.turn==1?-30000.0:30000.0):0.0;
   if(b.half>=100)return 0.0;
   if(!depth)return scoreNativeV3(featuresV3(b));
   double best=b.turn==1?-32001.0:32001.0;
   for(const auto&m:moves){double x=teacher(::apply(b,m),depth-1);
     best=b.turn==1?max(best,x):min(best,x);}
   return best;
}
int main(int argc,char**argv){
 try{
   insist(argc==3,"usage: joshua_v4_teacher OUTPUT.csv GAMES");
   int games=stoi(argv[2]);insist(games>0&&games<=400,"Invalid game count");
   ofstream file(argv[1]);insist(bool(file),"Cannot open output");
   file<<"game_id,sample_no,fen,teacher_cp,v3_cp,residual_cp";
   for(const auto&f:featureNamesV4)file<<','<<f;
   file<<'\n'<<setprecision(17);
   mt19937 rng(20261115);size_t count=0;
   const string start="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
   for(int game=0;game<games;game++){
     Board b=fen(start);int emitted=0;
     // Whole games are reserved together for train/validation/test.
     for(int ply=0;ply<56;ply++){
       auto options=legal(b);if(options.empty()||b.half>=100)break;
       if(ply>=6&&ply%4==(game%4)&&emitted<12){
         auto x=featuresV4(b);
         double baseline=scoreNativeV3(vector<double>(x.begin(),x.begin()+32));
         double strong=teacher(b,2);
         double residual=max(-220.0,min(220.0,strong-baseline));
         file<<game<<','<<emitted<<','<<toFen(b)<<','<<strong<<','<<baseline<<','<<residual;
         for(double z:x)file<<','<<z;
         file<<'\n';count++;emitted++;
       }
       // Unbiased but deterministic pseudo-random move selection; this produces
       // exploratory synthetic chess positions, not human opening distributions.
       int r=uniform_int_distribution<int>(0,int(options.size())-1)(rng);
       b=::apply(b,options[r]);
     }
   }
   insist(count>200,"Insufficient positions");
   cout<<"JOSHUA V4 teacher: "<<count<<" deterministic legal positions, "<<games<<" games, classical V3 depth-2 labels\n";
   return 0;
 }catch(const exception&e){cerr<<e.what()<<'\n';return 1;}
}
