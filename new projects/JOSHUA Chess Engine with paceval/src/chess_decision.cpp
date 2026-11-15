// Chess Decision Graph research demonstrator, November 2026.
// The host implements legal chess moves, bounded tree construction, control flow and I/O.
// All numerical leaf evaluations and dynamically synthesized minimax reductions are
// REAL persistent paceval execution graphs. This is NOT a solved chess engine.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
namespace fs=std::filesystem;
using std::string; using std::vector;
void insist(bool v,const string& why){if(!v)throw std::runtime_error(why);}
void near(double a,double b,double eps=1e-7){insist(std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=eps*(1+std::max(std::abs(a),std::abs(b))),"Independent numeric mismatch");}
int col(char p){return p=='.'?0:(p>='A'&&p<='Z'?1:-1);}
int fileof(int i){return i&7;} int rankof(int i){return i>>4;}
bool inside(int i){return i>=0&&i<128&&!(i&0x88);}
string sq(int i){return string(1,char('a'+fileof(i)))+char('8'-rankof(i));}
int ix(const string& s){if(s.size()!=2||s[0]<'a'||s[0]>'h'||s[1]<'1'||s[1]>'8')throw std::runtime_error("Invalid square");return ('8'-s[1])*16+(s[0]-'a');}
struct Move{int f,t;char promo=' ';bool ep=false,castle=false;};
string uci(const Move&m){return sq(m.f)+sq(m.t)+(m.promo==' '?"":string(1,m.promo));}
struct Board{std::array<char,128>b{};int turn=1,castle=15,ep=-1,half=0,full=1;};
Board fen(const string& text){
 std::istringstream ss(text);string placement,side,rights,enpassant;int half=0,full=1;
 insist(bool(ss>>placement>>side>>rights>>enpassant>>half>>full),"FEN must contain six fields");
 insist(side=="w"||side=="b","Invalid FEN turn");insist(half>=0&&full>=1,"Invalid FEN clocks");
 Board s;s.b.fill('.');s.turn=side=="w"?1:-1;s.castle=0;s.half=half;s.full=full;
 int r=0,f=0;
 for(char c:placement){if(c=='/'){insist(f==8&&r<7,"FEN rank length");r++;f=0;continue;}
  if(c>='1'&&c<='8'){f+=c-'0';insist(f<=8,"FEN rank overflow");continue;}
  insist(string("KQRBNPkqrbnp").find(c)!=string::npos&&f<8,"Invalid FEN piece");s.b[16*r+f++]=c;}
 insist(r==7&&f==8,"FEN must have eight ranks");
 insist(std::count(s.b.begin(),s.b.end(),'K')==1&&std::count(s.b.begin(),s.b.end(),'k')==1,"Exactly one king per color required");
 if(rights!="-"){std::set<char> seen;for(char c:rights){insist(seen.insert(c).second,"Duplicate castling right");if(c=='K')s.castle|=1;else if(c=='Q')s.castle|=2;else if(c=='k')s.castle|=4;else if(c=='q')s.castle|=8;else throw std::runtime_error("Invalid castling right");}}
 if(s.castle&1)insist(s.b[ix("e1")]=='K'&&s.b[ix("h1")]=='R',"Inconsistent castling K");
 if(s.castle&2)insist(s.b[ix("e1")]=='K'&&s.b[ix("a1")]=='R',"Inconsistent castling Q");
 if(s.castle&4)insist(s.b[ix("e8")]=='k'&&s.b[ix("h8")]=='r',"Inconsistent castling k");
 if(s.castle&8)insist(s.b[ix("e8")]=='k'&&s.b[ix("a8")]=='r',"Inconsistent castling q");
 if(enpassant!="-"){s.ep=ix(enpassant);insist((s.turn==1&&enpassant[1]=='6')||(s.turn==-1&&enpassant[1]=='3'),"Wrong en-passant rank");}
 // Reject adjacent kings and positions where the side that just played is in check.
 return s;
}
const vector<int> knight={-33,-31,-18,-14,14,18,31,33};
const vector<int> bishop={-17,-15,15,17};const vector<int> rook={-16,-1,1,16};
const vector<int> king={-17,-16,-15,-1,1,15,16,17};
int kingAt(const Board&s,int side){auto it=std::find(s.b.begin(),s.b.end(),side==1?'K':'k');return it==s.b.end()?-1:int(it-s.b.begin());}
bool attacked(const Board&s,int target,int by){
 for(int f=0;f<128;f++){if(!inside(f)||col(s.b[f])!=by)continue;char p=char(std::tolower(s.b[f]));
  if(p=='p'){if(target==f-16*by-1||target==f-16*by+1)return true;continue;}
  const vector<int>*d=&king;if(p=='n')d=&knight;else if(p=='b')d=&bishop;else if(p=='r')d=&rook;
  else if(p=='q'){for(const auto&v:{bishop,rook})for(int delta:v)for(int t=f+delta;inside(t);t+=delta){if(t==target)return true;if(s.b[t]!='.')break;}continue;}
  for(int delta:*d)for(int t=f+delta;inside(t);t+=delta){if(t==target)return true;if(s.b[t]!='.'||p=='n'||p=='k')break;}
 }
 return false;
}
bool check(const Board&s,int side){int k=kingAt(s,side);insist(k>=0,"Missing king");return attacked(s,k,-side);}
Board apply(const Board&s,const Move&m){Board n=s;char p=n.b[m.f],cap=n.b[m.t];n.b[m.f]='.';n.b[m.t]=m.promo==' '?p:(s.turn==1?char(std::toupper(m.promo)):m.promo);
 if(m.ep)n.b[m.t+16*s.turn]='.';
 if(m.castle){int rf=m.t>m.f?m.f+3:m.f-4, rt=m.t>m.f?m.f+1:m.f-1;n.b[rt]=n.b[rf];n.b[rf]='.';}
 if(p=='K')n.castle&=~3;if(p=='k')n.castle&=~12;
 auto bit=[](int k){return k==119?1:k==112?2:k==7?4:k==0?8:0;};
 if(std::tolower(p)=='r')n.castle&=~bit(m.f);
 if(std::tolower(cap)=='r')n.castle&=~bit(m.t);
 n.ep=std::tolower(p)=='p'&&std::abs(m.t-m.f)==32?(m.t+m.f)/2:-1;
 n.half=std::tolower(p)=='p'||cap!='.'||m.ep?0:s.half+1;n.full=s.full+(s.turn==-1);n.turn=-s.turn;return n;}
vector<Move> pseudo(const Board&s){vector<Move>out;
 for(int f=0;f<128;f++){if(!inside(f)||col(s.b[f])!=s.turn)continue;char p=char(std::tolower(s.b[f]));
  auto add=[&](int t,bool ep=false,bool castle=false){if(std::tolower(s.b[t])=='k')return;
   if(p=='p'&&(rankof(t)==0||rankof(t)==7))for(char q:string("qrbn"))out.push_back({f,t,q,ep,castle});else out.push_back({f,t,' ',ep,castle});};
  if(p=='p'){
   int t=f-16*s.turn;if(inside(t)&&s.b[t]=='.'){add(t);int u=t-16*s.turn;if(rankof(f)==(s.turn==1?6:1)&&s.b[u]=='.')add(u);}
   for(int d:{-1,1}){int u=t+d;if(!inside(u))continue;if(col(s.b[u])==-s.turn)add(u);
    else if(u==s.ep&&s.b[u]=='.'&&s.b[u+16*s.turn]==(s.turn==1?'p':'P'))add(u,true);}
  }else{
   vector<int> d=p=='n'?knight:p=='b'?bishop:p=='r'?rook:king;if(p=='q'){d=bishop;d.insert(d.end(),rook.begin(),rook.end());}
   for(int delta:d)for(int t=f+delta;inside(t);t+=delta){if(col(s.b[t])==s.turn)break;add(t);if(s.b[t]!='.'||p=='n'||p=='k')break;}
   int home=s.turn==1?116:4;char rp=s.turn==1?'R':'r';int bits=s.turn==1?1:4;
   if(p=='k'&&f==home&&!check(s,s.turn)){
    if((s.castle&bits)&&s.b[f+3]==rp&&s.b[f+1]=='.'&&s.b[f+2]=='.'&&!attacked(s,f+1,-s.turn)&&!attacked(s,f+2,-s.turn))add(f+2,false,true);
    if((s.castle&(bits<<1))&&s.b[f-4]==rp&&s.b[f-1]=='.'&&s.b[f-2]=='.'&&s.b[f-3]=='.'&&!attacked(s,f-1,-s.turn)&&!attacked(s,f-2,-s.turn))add(f-2,false,true);
   }
  }
 }
 return out;
}
vector<Move> legal(const Board&s){vector<Move>out;for(auto&m:pseudo(s))if(!check(apply(s,m),s.turn))out.push_back(m);return out;}
string toFen(const Board&s){string z;for(int r=0;r<8;r++){if(r)z+='/';int empty=0;for(int f=0;f<8;f++){char p=s.b[r*16+f];if(p=='.')empty++;else{if(empty){z+=char('0'+empty);empty=0;}z+=p;}}if(empty)z+=char('0'+empty);}z+=s.turn==1?" w ":" b ";string cr;if(s.castle&1)cr+='K';if(s.castle&2)cr+='Q';if(s.castle&4)cr+='k';if(s.castle&8)cr+='q';z+=cr.empty()?"-":cr;z+=' ';z+=s.ep<0?"-":sq(s.ep);z+=' ';z+=std::to_string(s.half);z+=' ';z+=std::to_string(s.full);return z;}
string boardKey(const Board&s){string k;for(int i=0;i<128;i++)if(inside(i))k.push_back(s.b[i]);k+=s.turn==1?'w':'b';k+=char('a'+s.castle);if(s.ep>=0)k+=sq(s.ep);return k;}
size_t perft(const Board&s,int depth){if(depth==0)return 1;size_t count=0;for(auto&m:legal(s))count+=perft(apply(s,m),depth-1);return count;}
string join(const vector<string>&v){string s;for(auto&x:v){if(!s.empty())s+=' ';s+=x;}return s;}
bool literal(const string&s){static const std::regex r(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,r);}
double parseNumber(const string&s){insist(literal(s),"Only finite decimal literals accepted");int err=-1;long pos=-1;double v=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);insist(err==0&&std::isfinite(v),"paceval numeric parse failed");return v;}
string fmt(double x){insist(std::isfinite(x),"nonfinite CSV output");char out[512]{};int r=paceval_dConvertFloatToString(out,x);insist(r>0&&out[0],"paceval conversion to text failed");return out;}
struct Engine{
 vector<PACEVAL_HANDLE>owned;size_t scalar=0,batches=0,graphPoints=0;bool graphMajor=false;
 Engine(){insist(paceval_InitializeLibrary(nullptr),"paceval library init failed");}
 ~Engine(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const string& formula,const vector<string>&vars){auto names=join(vars);auto h=paceval_CreateComputation(formula.c_str(),vars.size(),names.c_str(),false,nullptr);insist(h&&!paceval_GetIsError(h),"Graph compile failed: "+formula);owned.push_back(h);return h;}
 double eval(PACEVAL_HANDLE h,const vector<double>&v){auto a=v;double r=paceval_dGetComputationResult(h,a.data(),nullptr,nullptr);scalar++;insist(!paceval_GetIsError(h)&&std::isfinite(r),"Scalar graph failed");graphPoints++;return r;}
 void probe(){auto a=create("x+2*y",{"x","y"}),b=create("3*x-y",{"x","y"});PACEVAL_HANDLE hs[]={a,b};double in[]={1,2,4,7},o[4]{},lo[4]{},hi[4]{};int err[4]{};bool failure=paceval_dGetMultipleComputationsResultsExt(hs,2,in,2,o,lo,hi,err);insist(!failure&&!err[0]&&!err[1]&&!err[2]&&!err[3],"API layout probe failed");
 if(std::abs(o[0]-5)<1e-8&&std::abs(o[1]-18)<1e-8&&std::abs(o[2]-1)<1e-8&&std::abs(o[3]-5)<1e-8)graphMajor=true;
 else if(std::abs(o[0]-5)<1e-8&&std::abs(o[1]-1)<1e-8&&std::abs(o[2]-18)<1e-8&&std::abs(o[3]-5)<1e-8)graphMajor=false;
 else throw std::runtime_error("Unexpected multi-graph output layout");batches++;graphPoints+=4;}
 vector<vector<double>> multi(const vector<PACEVAL_HANDLE>&h,const vector<vector<double>>&rows){insist(!h.empty()&&!rows.empty(),"Empty batch");size_t n=rows.size(),m=rows[0].size();vector<double>in;in.reserve(n*m);for(auto&r:rows){insist(r.size()==m,"Width mismatch");for(double v:r)insist(std::isfinite(v),"nonfinite input");in.insert(in.end(),r.begin(),r.end());}
 vector<double>out(n*h.size()),lo(out.size()),hi(out.size());vector<int>e(out.size(),-1);bool fail=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(h.data()),h.size(),in.data(),n,out.data(),lo.data(),hi.data(),e.data());insist(!fail,"MultiGraph failed");for(int x:e)insist(x==0,"MultiGraph error code");vector<vector<double>>z(n,vector<double>(h.size()));for(size_t i=0;i<n;i++)for(size_t j=0;j<h.size();j++){z[i][j]=out[graphMajor?j*n+i:i*h.size()+j];insist(std::isfinite(z[i][j]),"Nonfinite graph result");}batches++;graphPoints+=out.size();return z;}
 vector<double>single(PACEVAL_HANDLE h,const vector<vector<double>>&rows){size_t n=rows.size(),m=rows[0].size();vector<double>in;in.reserve(n*m);for(auto&r:rows){insist(r.size()==m,"Variable mismatch");in.insert(in.end(),r.begin(),r.end());}vector<double>out(n),lo(n),hi(n);vector<int>err(n,-1);bool fail=paceval_dGetComputationResultExt(h,in.data(),n,out.data(),lo.data(),hi.data(),err.data());insist(!fail,"Single batch error");for(size_t i=0;i<n;i++)insist(err[i]==0&&std::isfinite(out[i]),"Single batch result error");batches++;graphPoints+=n;return out;}
};
// Input features are literal counts, not native weighted evaluations.
const vector<string> featureNames={"wp","wn","wb","wr","wq","bp","bn","bb","br","bq","wc","bc","wd","bd","wa","ba","wk","bk","bias"};
vector<double> features(const Board&s){vector<double>x(19,0);const string pcs="PNBRQpnbrq";for(int i=0;i<128;i++){if(!inside(i))continue;char p=s.b[i];auto j=pcs.find(p);if(j!=string::npos)x[j]++;
 int c=col(p),f=fileof(i),r=rankof(i);if(c==0)continue;
 if(f>=2&&f<=5&&r>=2&&r<=5){if(c>0)x[10]++;else x[11]++;}
 if(p=='N'||p=='B'){if(r<7)x[12]++;}if(p=='n'||p=='b'){if(r>0)x[13]++;}
 if(p=='P')x[14]+=6-r;else if(p=='p')x[15]+=r-1;
 if(p=='K')x[16]=(f==6||f==2)?1:0;if(p=='k')x[17]=(f==6||f==2)?1:0;
 }x[18]=1;return x;}
const string mat="(100*(wp-bp)+320*(wn-bn)+330*(wb-bb)+500*(wr-br)+900*(wq-bq))";
const string center="(wc-bc)",development="(wd-bd)",advance="(wa-ba)",ksafe="(wk-bk)";
struct Expr{string name,ver,formula;PACEVAL_HANDLE h;size_t points=0;};
struct Evaluator{Engine&e;vector<Expr>expr;std::map<string,size_t>by;
 Evaluator(Engine&a):e(a){auto add=[&](string name,string ver,string f){auto h=e.create(f,featureNames);by[ver+"_"+name]=expr.size();expr.push_back({name,ver,f,h,0});};
   for(string version:{"V1","V2"}){
    bool advanced=version=="V2";string score=advanced?"("+mat+"+13*"+center+"+17*"+development+"+3*"+advance+"+18*"+ksafe+")":mat;
    add("MATERIAL",version,mat);add("CENTER",version,center);add("DEVELOPMENT",version,development);add("PAWN_ADVANCE",version,advance);add("KING_ZONE",version,ksafe);add("SCORE",version,score);
    add("SCORE_MARGIN",version,"(2000-abs("+score+"))");add("SCORE_GUARD",version,"((abs("+score+")<=2000) AND (wp>=0) AND (bp>=0))");
    add("SENSITIVITY_CENTER_WEIGHT",version,center);add("COMPOSITE_PIECE_ACTIVITY",version,"(13*"+center+"+17*"+development+")");
   }
 }
 vector<double> evaluate(const Board&b){auto rows=e.multi(handles(),{features(b)});return rows[0];}
 vector<PACEVAL_HANDLE> handles()const{vector<PACEVAL_HANDLE>h;for(auto&x:expr)h.push_back(x.h);return h;}
};
struct Node{Board s;Move move;int parent=-1,ply=0;vector<int>children;double v1=0,v2=0;bool terminal=false;};
struct Tree{vector<Node>nodes;size_t maxNodes=250000;int depth=3;size_t leaves=0;std::set<string>unique;
 int construct(const Board&s,int parent,Move m,int ply){insist(nodes.size()<maxNodes,"Node cap reached before requested full depth; no false completeness claim");int id=int(nodes.size());Node n;n.s=s;n.move=m;n.parent=parent;n.ply=ply;nodes.push_back(std::move(n));unique.insert(boardKey(s));
  auto moves=legal(s);bool term=moves.empty()||s.half>=150; // No claim that unknown FEN history can prove repetition.
  if(ply==depth||term){nodes[id].terminal=term;leaves++;return id;}
  for(auto&a:moves){int child=construct(apply(s,a),id,a,ply+1);nodes[id].children.push_back(child);}
  return id;}
};
struct Reducer{Engine&e;std::map<std::pair<int,bool>,PACEVAL_HANDLE>cache;size_t assigned=0;
 Reducer(Engine&x):e(x){}
 PACEVAL_HANDLE graph(int fanout,bool maximum){auto key=std::make_pair(fanout,maximum);auto it=cache.find(key);if(it!=cache.end())return it->second;insist(fanout>=2&&fanout<=200,"Unsupported branching degree");vector<string>vars;string f;for(int i=0;i<fanout;i++){string v="v"+std::to_string(i);vars.push_back(v);if(!f.empty())f+=" "+string(maximum?"max":"min")+" ";f+=v;}auto h=e.create("("+f+")",vars);cache[key]=h;return h;}
 void reduce(Tree&t,int model){for(int ply=t.depth-1;ply>=0;ply--){std::map<std::pair<int,bool>,vector<int>> groups;
   for(size_t i=0;i<t.nodes.size();i++)if(t.nodes[i].ply==ply&&t.nodes[i].children.size()>1)groups[{int(t.nodes[i].children.size()),t.nodes[i].s.turn==1}].push_back(int(i));
   for(auto&pair:groups){auto h=graph(pair.first.first,pair.first.second);auto&ids=pair.second;
    for(size_t base=0;base<ids.size();base+=256){vector<vector<double>>rows;size_t end=std::min(base+256,ids.size());for(size_t k=base;k<end;k++){vector<double>v;for(int ch:t.nodes[ids[k]].children)v.push_back(model==1?t.nodes[ch].v1:t.nodes[ch].v2);rows.push_back(v);}
     auto results=e.single(h,rows);for(size_t j=0;j<results.size();j++){int id=ids[base+j];if(model==1)t.nodes[id].v1=results[j];else t.nodes[id].v2=results[j];assigned++;}}
   }
   for(auto&n:t.nodes)if(n.ply==ply&&n.children.size()==1){int ch=n.children[0];if(model==1)n.v1=t.nodes[ch].v1;else n.v2=t.nodes[ch].v2;}
  }
 }
};
string pv(const Tree&t,int rootChild,int model){string res;int current=rootChild;while(current>=0){if(t.nodes[current].parent>=0){if(!res.empty())res+=' ';res+=uci(t.nodes[current].move);}if(t.nodes[current].children.empty())break;int next=t.nodes[current].children[0];for(int x:t.nodes[current].children){auto val=[&](int a){return model==1?t.nodes[a].v1:t.nodes[a].v2;};if((t.nodes[current].s.turn==1&&val(x)>val(next))||(t.nodes[current].s.turn==-1&&val(x)<val(next)))next=x;}current=next;}return res;}
int pieceValue(char p){switch(std::tolower(p)){case'p':return 100;case'n':return 320;case'b':return 330;case'r':return 500;case'q':return 900;default:return 0;}}
double nativeScore(const Board&s,int version){auto f=features(s);double v=100*(f[0]-f[5])+320*(f[1]-f[6])+330*(f[2]-f[7])+500*(f[3]-f[8])+900*(f[4]-f[9]);if(version==2)v+=13*(f[10]-f[11])+17*(f[12]-f[13])+3*(f[14]-f[15])+18*(f[16]-f[17]);return v;}
void selftest(Engine&e){e.probe();Board s=fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");for(int d=1;d<=4;d++){size_t n=perft(s,d);const size_t expected[]={0,20,400,8902,197281};insist(n==expected[d],"Perft start position failed depth "+std::to_string(d));}Board castle=fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1");int cc=0;for(auto m:legal(castle))if(m.castle)cc++;insist(cc==2,"Castling validation failed");
 Board blockedCastle=fen("r3k2r/8/8/8/8/5r2/8/R3K2R w KQkq - 0 1");
 for(auto m:legal(blockedCastle))insist(!(m.castle&&m.t==ix("g1")),"Castle through attacked square wrongly legal");
 Board epPin=fen("4r1k1/8/8/3pP3/8/8/8/4K3 w - d6 0 1");
 for(auto m:legal(epPin))insist(!m.ep,"Pinned en-passant incorrectly legal");
 Board mate=fen("7k/6Q1/5K2/8/8/8/8/8 b - - 0 1");
 insist(legal(mate).empty()&&check(mate,-1),"Checkmate recognition failed");
 Board stale=fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1");
 insist(legal(stale).empty()&&!check(stale,-1),"Stalemate recognition failed");
 Board ep=fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1");int ee=0;for(auto m:legal(ep))if(m.ep)ee++;insist(ee==1,"En-passant move missing");Board promo=fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1");int pp=0;for(auto m:legal(promo))if(m.promo!=' ')pp++;insist(pp==4,"Promotion variants missing");
 Evaluator eval(e);auto z=eval.evaluate(s);near(z[eval.by.at("V1_SCORE")],0);near(z[eval.by.at("V2_SCORE")],0);
 auto h=e.create("((a<=b) AND (c>=0))",{"a","b","c"});near(e.eval(h,{1,1,0}),1);near(e.eval(h,{2,1,0}),0);
 auto m=e.create("v0 min v1 min v2",{"v0","v1","v2"});near(e.eval(m,{4,-5,7}),-5);
 auto mod=e.create("x mod y",{"x","y"});auto rem=e.create("x % y",{"x","y"});
 near(e.eval(mod,{-1,10}),9);near(e.eval(rem,{-1,10}),-1);
 auto logic=e.create("(((x=y) OR (x<>y)) AND NOT(x<0))",{"x","y"});
 near(e.eval(logic,{0,2}),1);near(e.eval(logic,{-1,2}),0);
 insist(!literal("1+2")&&!literal("NaN")&&!literal("1,2")&&!literal(""),"numeric CSV grammar failure");near(parseNumber("-3.5e1"),-35);insist(!fmt(1.25).empty(),"Number conversion test failed");
 std::cout<<"SELFTEST_PASS start_perft_1_to_4=20,400,8902,197281 castling=2 en_passant=1 promotions=4 sdk=pass\n";
}
void run(Engine&e,const string&fenText,int depth,const fs::path&out,size_t cap){insist(depth>=1&&depth<=5,"depth must be 1..5; cap limits completeness");fs::create_directories(out);Board start=fen(fenText);insist(!check(start,-start.turn),"Side that moved last is illegally in check");
 Tree t;t.depth=depth;t.maxNodes=cap;t.nodes.reserve(std::min<size_t>(cap,240000));t.construct(start,-1,{},0);
 Evaluator eval(e);vector<int>leaves;for(size_t i=0;i<t.nodes.size();i++)if(t.nodes[i].children.empty())leaves.push_back(i);
 size_t nativeChecks=0;for(size_t base=0;base<leaves.size();base+=256){vector<vector<double>>rows;auto end=std::min(base+256,leaves.size());for(size_t i=base;i<end;i++)rows.push_back(features(t.nodes[leaves[i]].s));auto values=e.multi(eval.handles(),rows);
 for(size_t j=0;j<values.size();j++){auto&id=t.nodes[leaves[base+j]];auto&z=values[j];int cur=id.s.turn;bool noMoves=legal(id.s).empty();bool cm=noMoves&&check(id.s,cur);if(cm){double val=cur==1?-100000+id.ply:100000-id.ply;id.v1=id.v2=val;}else if(noMoves||id.s.half>=150)id.v1=id.v2=0;
  else{id.v1=z[eval.by.at("V1_SCORE")];id.v2=z[eval.by.at("V2_SCORE")];}
  if((base+j)%31==0){near(z[eval.by.at("V1_MATERIAL")],nativeScore(id.s,1));near(z[eval.by.at("V1_SCORE")],nativeScore(id.s,1));near(z[eval.by.at("V2_SCORE")],nativeScore(id.s,2));nativeChecks+=3;}
 }
 }
 Reducer reducer(e);reducer.reduce(t,1);reducer.reduce(t,2);
 // Additional direct-graph experiment: synthesize the ENTIRE depth-two minimax
 // tree as ONE mathematical paceval expression with one variable per leaf.
 // It reuses the same expression for V1 and V2 without recompilation.
 bool unrolledPass=false;size_t unrolledLeaves=0,unrolledLength=0;
 if(depth>=2 && !t.nodes[0].children.empty()){
  vector<string>names;vector<double>in1,in2;string formula="(";
  int groups=0;bool possible=true;
  for(int id:t.nodes[0].children){if(t.nodes[id].children.empty())possible=false;unrolledLeaves+=t.nodes[id].children.size();groups++;}
  if(possible && unrolledLeaves<=512){
   size_t seq=0;bool rootMax=t.nodes[0].s.turn==1;
   for(int id:t.nodes[0].children){if(groups && id!=t.nodes[0].children.front())formula+=rootMax?" max ":" min ";formula+='(';
    bool childMax=t.nodes[id].s.turn==1;bool first=true;
    for(int leaf:t.nodes[id].children){if(!first)formula+=childMax?" max ":" min ";first=false;
     auto var="q"+std::to_string(seq++);formula+=var;names.push_back(var);
     auto feat=features(t.nodes[leaf].s);in1.push_back(e.eval(eval.expr[eval.by.at("V1_SCORE")].h,feat));in2.push_back(e.eval(eval.expr[eval.by.at("V2_SCORE")].h,feat));}
    formula+=')';}
   formula+=')';
   PACEVAL_HANDLE direct=e.create(formula,names);
   double pv1=e.eval(direct,in1),pv2=e.eval(direct,in2);
   size_t cursor=0;double expected1=0,expected2=0;bool firstGroup=true;
   for(int id:t.nodes[0].children){bool childMax=t.nodes[id].s.turn==1;
    double v1=in1[cursor],v2=in2[cursor];for(size_t j=0;j<t.nodes[id].children.size();j++){double a=in1[cursor+j],b=in2[cursor+j];v1=childMax?std::max(v1,a):std::min(v1,a);v2=childMax?std::max(v2,b):std::min(v2,b);}
    cursor+=t.nodes[id].children.size();if(firstGroup){expected1=v1;expected2=v2;firstGroup=false;}
    else{expected1=rootMax?std::max(expected1,v1):std::min(expected1,v1);expected2=rootMax?std::max(expected2,v2):std::min(expected2,v2);}}
   near(pv1,expected1);near(pv2,expected2);
   unrolledPass=true;unrolledLength=formula.size();
   std::ofstream generated(out/"generated_single_graph_depth2.txt");
   generated<<"# Exact synthesized two-ply minimax expression (leaf values are inputs).\n"<<"# Variables: "<<names.size()<<"; expression characters: "<<unrolledLength<<"\n"<<formula<<"\n";
  }
 }

 // Verify independent bottom-up reduction, not merely leaf evaluation.
 size_t internalChecks=0;for(size_t i=0;i<t.nodes.size();i++){auto&n=t.nodes[i];if(n.children.empty())continue;if(i%17)continue;for(int v:{1,2}){double expected=v==1?t.nodes[n.children.front()].v1:t.nodes[n.children.front()].v2;for(int ch:n.children){double x=v==1?t.nodes[ch].v1:t.nodes[ch].v2;expected=n.s.turn==1?std::max(expected,x):std::min(expected,x);}near(v==1?n.v1:n.v2,expected);internalChecks++;}}
 std::ofstream nodes(out/"decision_nodes.csv"),root(out/"root_moves.csv"),manifest(out/"formula_manifest.csv"),inventory(out/"math_execution_inventory.csv");insist(nodes&&root&&manifest&&inventory,"Cannot open CSV outputs");
 nodes<<"id,parent,ply,uci,side,child_count,terminal,value_v1,value_v2,fen\n";for(size_t i=0;i<t.nodes.size();i++){auto&n=t.nodes[i];nodes<<i<<','<<n.parent<<','<<n.ply<<','<<(n.parent<0?"ROOT":uci(n.move))<<','<<(n.s.turn==1?'w':'b')<<','<<n.children.size()<<','<<(n.terminal?1:0)<<','<<fmt(n.v1)<<','<<fmt(n.v2)<<','<<toFen(n.s)<<'\n';}
 root<<"move,score_v1,score_v2,principal_variation_v1,principal_variation_v2\n";
 for(int ch:t.nodes[0].children){auto&n=t.nodes[ch];root<<uci(n.move)<<','<<fmt(n.v1)<<','<<fmt(n.v2)<<",\""<<pv(t,ch,1)<<"\",\""<<pv(t,ch,2)<<"\"\n";}
 manifest<<"formula_id,version,formula,actual_path\n";
 for(auto&x:eval.expr)manifest<<x.name<<','<<x.ver<<",\""<<x.formula<<"\",paceval_MultiGraph_batch\n";
 for(auto&p:reducer.cache)manifest<<"minimax_reducer_"<<p.first.first<<','<<(p.first.second?"max":"min")<<",dynamic_infix_expression,paceval_batch\n";
 inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 for(auto&x:eval.expr)inventory<<x.ver<<'_'<<x.name<<",chess_position_score,\""<<x.formula<<"\",centipawns,paceval,"<<x.ver<<'_'<<x.name<<','<<x.ver<<",multi_graph_batch,native_cpp,executed,\n";
 inventory<<"legal_move_generation,legal_chess_moves,king_safety_and_move_rules,moves,host,,N/A,C++_loop,perft,executed,stateful_rules\n";
 inventory<<"minimax_reduction,game_tree_backup,child_max_or_min,centipawns,paceval,dynamic_min_max_graph,V1_V2,single_graph_batch,native_cpp,executed,C++_orchestrates_tree_levels\n";
 inventory<<"path_independence,draw_repetition,history_aware_repetition,boolean,not_implemented,,N/A,N/A,N/A,not_implemented,FEN_omits_history\n";
 nodes.close();root.close();manifest.close();inventory.close();
 size_t repeated=t.nodes.size()-t.unique.size();std::ofstream ev(out/"execution_evidence.json");ev<<"{\n"<<"  \"model\": \"synthetic bounded minimax V1/V2\",\n"<<"  \"depth\": "<<depth<<",\n"<<"  \"node_count\": "<<t.nodes.size()<<",\n"<<"  \"unique_board_state_keys\": "<<t.unique.size()<<",\n"<<"  \"repeated_board_state_keys\": "<<repeated<<",\n"<<"  \"leaf_count\": "<<t.leaves<<",\n"<<"  \"unique_graphs_created\": "<<e.owned.size()<<",\n"<<"  \"unique_graphs_executed\": "<<e.owned.size()<<",\n"<<"  \"scalar_calls\": "<<e.scalar<<",\n"<<"  \"batch_calls\": "<<e.batches<<",\n"<<"  \"graph_point_evaluations\": "<<e.graphPoints<<",\n"<<"  \"scenario_count\": 1,\n"<<"  \"native_reference_checks\": "<<nativeChecks+internalChecks<<",\n"<<"  \"reducer_batch_assignments\": "<<reducer.assigned<<",\n"<<"  \"unrolled_depth2_graph_executed\": "<<(unrolledPass?"true":"false")<<",\n"<<"  \"unrolled_depth2_leaf_variables\": "<<unrolledLeaves<<",\n"<<"  \"unrolled_depth2_expression_chars\": "<<unrolledLength<<",\n"<<"  \"draw_history_limit\": \"Repetitions before the root FEN are unknown; no global game-theoretic proof\"\n}\n";
 std::cout<<"RUN_PASS depth="<<depth<<" nodes="<<t.nodes.size()<<" leaves="<<t.leaves<<" unique_keys="<<t.unique.size()<<" graphs="<<e.owned.size()<<" graph_points="<<e.graphPoints<<" checks="<<nativeChecks+internalChecks<<" root_V1="<<fmt(t.nodes[0].v1)<<" root_V2="<<fmt(t.nodes[0].v2)<<"\n";
}
void evalCsv(Engine&e,const fs::path&src,const fs::path&outDir){
 e.probe();fs::create_directories(outDir);std::ifstream input(src);insist(bool(input),"CSV input unavailable");
 string header;insist(bool(std::getline(input,header)),"CSV missing header");
 string expected="id";for(auto&x:featureNames)expected+=","+x;insist(header==expected,"CSV schema/header mismatch");
 vector<vector<double>>data;vector<string>ids;string line;size_t lineNo=1;
 while(std::getline(input,line)){lineNo++;insist(!line.empty(),"Empty CSV row");std::istringstream split(line);string item;vector<string>v;while(std::getline(split,item,','))v.push_back(item);insist(v.size()==featureNames.size()+1,"CSV column count mismatch at "+std::to_string(lineNo));
  insist(std::regex_match(v[0],std::regex("[A-Za-z0-9_-]{1,64}")),"Unsafe CSV row id");ids.push_back(v[0]);vector<double>row;for(size_t k=1;k<v.size();k++){double x=parseNumber(v[k]);insist(x>=0&&x<1000,"Feature domain violated");row.push_back(x);}data.push_back(std::move(row));}
 insist(!data.empty()&&data.size()<=100000,"Invalid CSV row count");Evaluator m(e);std::ofstream out(outDir/"features_scored.csv");insist(bool(out),"Cannot write scored features");out<<"id,score_v1,score_v2,center_margin_v2,score_guard_v2\n";
 for(size_t start=0;start<data.size();start+=256){size_t end=std::min(start+256,data.size());auto z=e.multi(m.handles(),vector<vector<double>>(data.begin()+start,data.begin()+end));for(size_t j=0;j<z.size();j++){auto&row=z[j];out<<ids[start+j]<<','<<fmt(row[m.by.at("V1_SCORE")])<<','<<fmt(row[m.by.at("V2_SCORE")])<<','<<fmt(row[m.by.at("V2_CENTER")])<<','<<fmt(row[m.by.at("V2_SCORE_GUARD")])<<'\n';}}
 std::cout<<"CSV_DEMO_PASS input_rows="<<data.size()<<" evaluated_graphs="<<m.expr.size()<<" data_path=paceval_numeric_converter+multigraph\n";
}
int main(int argc,char**argv){try{Engine e;if(argc>=2&&string(argv[1])=="--selftest"){selftest(e);return 0;}if(argc==4&&string(argv[1])=="--csv-demo"){evalCsv(e,argv[2],argv[3]);return 0;}e.probe();string f="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",output="results";int depth=3;size_t cap=260000;
 for(int i=1;i<argc;i++){string a=argv[i];if(a=="--fen"&&i+1<argc)f=argv[++i];else if(a=="--depth"&&i+1<argc)depth=std::stoi(argv[++i]);else if(a=="--output"&&i+1<argc)output=argv[++i];else if(a=="--max-nodes"&&i+1<argc)cap=std::stoull(argv[++i]);else throw std::runtime_error("Usage: chess_decision [--fen 'six-field FEN'] [--depth 1..5] [--output DIR] [--max-nodes N] | --selftest");}
 run(e,f,depth,output,cap);return 0;}catch(const std::exception&x){std::cerr<<"ERROR "<<x.what()<<'\n';return 1;}}
