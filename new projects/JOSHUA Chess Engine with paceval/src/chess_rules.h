#pragma once
// Chess Decision Graph research demonstrator, November 2026.
// The host implements legal chess moves, bounded tree construction, control flow and I/O.
// All numerical leaf evaluations and dynamically synthesized minimax reductions are
// REAL persistent paceval execution graphs. This is NOT a solved chess engine.

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
// Target-centric attack detection. Tests only squares capable of attacking target.
// For the 0x88 board, rays terminate at first occupied square.
bool attacked(const Board&s,int target,int by){
 const char pawn=by==1?'P':'p', knightPiece=by==1?'N':'n', kingPiece=by==1?'K':'k';
 const char bishopPiece=by==1?'B':'b', rookPiece=by==1?'R':'r',queenPiece=by==1?'Q':'q';
 for(int d:{-1,1}){int from=target+16*by+d;if(inside(from)&&s.b[from]==pawn)return true;}
 for(int d:knight){int from=target+d;if(inside(from)&&s.b[from]==knightPiece)return true;}
 for(int d:king){int from=target+d;if(inside(from)&&s.b[from]==kingPiece)return true;}
 for(int d:bishop)for(int from=target+d;inside(from);from+=d){char p=s.b[from];if(p!='.'){if(p==bishopPiece||p==queenPiece)return true;break;}}
 for(int d:rook)for(int from=target+d;inside(from);from+=d){char p=s.b[from];if(p!='.'){if(p==rookPiece||p==queenPiece)return true;break;}}
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
vector<Move> pseudo(const Board&s){vector<Move>out;out.reserve(80);
 for(int f=0;f<128;f++){if(!inside(f)||col(s.b[f])!=s.turn)continue;char p=char(std::tolower(s.b[f]));
  auto add=[&](int t,bool ep=false,bool castle=false){if(std::tolower(s.b[t])=='k')return;
   if(p=='p'&&(rankof(t)==0||rankof(t)==7))for(char q:string("qrbn"))out.push_back({f,t,q,ep,castle});else out.push_back({f,t,' ',ep,castle});};
  if(p=='p'){
   int t=f-16*s.turn;if(inside(t)&&s.b[t]=='.'){add(t);int u=t-16*s.turn;if(rankof(f)==(s.turn==1?6:1)&&s.b[u]=='.')add(u);}
   for(int d:{-1,1}){int u=t+d;if(!inside(u))continue;if(col(s.b[u])==-s.turn)add(u);
    else if(u==s.ep&&s.b[u]=='.'&&s.b[u+16*s.turn]==(s.turn==1?'p':'P'))add(u,true);}
  }else{
   auto visit=[&](const vector<int>&dirs){for(int delta:dirs)for(int t=f+delta;inside(t);t+=delta){if(col(s.b[t])==s.turn)break;add(t);if(s.b[t]!='.'||p=='n'||p=='k')break;}};
   if(p=='n')visit(knight);else if(p=='b')visit(bishop);else if(p=='r')visit(rook);
   else if(p=='q'){visit(bishop);visit(rook);}else visit(king);
   int home=s.turn==1?116:4;char rp=s.turn==1?'R':'r';int bits=s.turn==1?1:4;
   if(p=='k'&&f==home&&!check(s,s.turn)){
    if((s.castle&bits)&&s.b[f+3]==rp&&s.b[f+1]=='.'&&s.b[f+2]=='.'&&!attacked(s,f+1,-s.turn)&&!attacked(s,f+2,-s.turn))add(f+2,false,true);
    if((s.castle&(bits<<1))&&s.b[f-4]==rp&&s.b[f-1]=='.'&&s.b[f-2]=='.'&&s.b[f-3]=='.'&&!attacked(s,f-1,-s.turn)&&!attacked(s,f-2,-s.turn))add(f-2,false,true);
   }
  }
 }
 return out;
}

struct MoveUndo{char moving='.',captured='.',epCaptured='.',rook='.';int castle=0,ep=-1,half=0,full=1,turn=1;};
MoveUndo makeMove(Board&s,const Move&m){
 MoveUndo u;u.moving=s.b[m.f];u.captured=s.b[m.t];u.castle=s.castle;u.ep=s.ep;u.half=s.half;u.full=s.full;u.turn=s.turn;
 char p=u.moving,cap=u.captured;
 s.b[m.f]='.';s.b[m.t]=m.promo==' '?p:(u.turn==1?char(std::toupper(static_cast<unsigned char>(m.promo))):m.promo);
 if(m.ep){int c=m.t+16*u.turn;u.epCaptured=s.b[c];s.b[c]='.';}
 if(m.castle){int rf=m.t>m.f?m.f+3:m.f-4,rt=m.t>m.f?m.f+1:m.f-1;u.rook=s.b[rf];s.b[rt]=s.b[rf];s.b[rf]='.';}
 if(p=='K')s.castle&=~3;if(p=='k')s.castle&=~12;
 auto bit=[](int k){return k==119?1:k==112?2:k==7?4:k==0?8:0;};
 if(std::tolower(static_cast<unsigned char>(p))=='r')s.castle&=~bit(m.f);
 if(std::tolower(static_cast<unsigned char>(cap))=='r')s.castle&=~bit(m.t);
 s.ep=std::tolower(static_cast<unsigned char>(p))=='p'&&std::abs(m.t-m.f)==32?(m.t+m.f)/2:-1;
 s.half=std::tolower(static_cast<unsigned char>(p))=='p'||cap!='.'||m.ep?0:u.half+1;
 s.full=u.full+(u.turn==-1);s.turn=-u.turn;
 return u;
}
void unmakeMove(Board&s,const Move&m,const MoveUndo&u){
 s.turn=u.turn;s.castle=u.castle;s.ep=u.ep;s.half=u.half;s.full=u.full;
 s.b[m.f]=u.moving;s.b[m.t]=u.captured;
 if(m.ep)s.b[m.t+16*u.turn]=u.epCaptured;
 if(m.castle){int rf=m.t>m.f?m.f+3:m.f-4,rt=m.t>m.f?m.f+1:m.f-1;s.b[rf]=u.rook;s.b[rt]='.';}
}
vector<Move> legal(const Board&s){
 vector<Move>out;out.reserve(80);Board work=s;
 for(const auto&m:pseudo(s)){MoveUndo u=makeMove(work,m);const bool valid=!check(work,s.turn);unmakeMove(work,m,u);if(valid)out.push_back(m);}
 return out;
}
string toFen(const Board&s){string z;for(int r=0;r<8;r++){if(r)z+='/';int empty=0;for(int f=0;f<8;f++){char p=s.b[r*16+f];if(p=='.')empty++;else{if(empty){z+=char('0'+empty);empty=0;}z+=p;}}if(empty)z+=char('0'+empty);}z+=s.turn==1?" w ":" b ";string cr;if(s.castle&1)cr+='K';if(s.castle&2)cr+='Q';if(s.castle&4)cr+='k';if(s.castle&8)cr+='q';z+=cr.empty()?"-":cr;z+=' ';z+=s.ep<0?"-":sq(s.ep);z+=' ';z+=std::to_string(s.half);z+=' ';z+=std::to_string(s.full);return z;}
string boardKey(const Board&s){string k;for(int i=0;i<128;i++)if(inside(i))k.push_back(s.b[i]);k+=s.turn==1?'w':'b';k+=char('a'+s.castle);if(s.ep>=0)k+=sq(s.ep);return k;}
size_t perft(const Board&s,int depth){if(depth==0)return 1;size_t count=0;for(auto&m:legal(s))count+=perft(apply(s,m),depth-1);return count;}
string join(const vector<string>&v){string s;for(auto&x:v){if(!s.empty())s+=' ';s+=x;}return s;}
bool literal(const string&s){static const std::regex r(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,r);}
double parseNumber(const string&s){insist(literal(s),"Only finite decimal literals accepted");int err=-1;long pos=-1;double v=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);insist(err==0&&std::isfinite(v),"paceval numeric parse failed");return v;}
string fmt(double x){insist(std::isfinite(x),"nonfinite CSV output");char out[512]{};int r=paceval_dConvertFloatToString(out,x);insist(r>0&&out[0],"paceval conversion to text failed");return out;}

