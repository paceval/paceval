// Chess rules only. No paceval runtime required for referee validation.
#include "paceval_main.h"
#include "chess_rules.h"
#include <iostream>
#include <sstream>
#include <cctype>
#include <stdexcept>
#include <algorithm>
#include <functional>
#include <set>
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

static std::string status(const Board&b){
 auto a=legal(b);
 if(a.empty())return check(b,b.turn)?"checkmate":"stalemate";
 if(b.half>=100)return "fifty_move_claim";
 int minors=0;bool major=false;bool same=true;int bishopColor=-1;
 for(int i=0;i<128;i++)if(inside(i)){
  const char x=char(std::tolower(static_cast<unsigned char>(b.b[i])));
  if(x=='.'||x=='k')continue;
  if(x=='p'||x=='q'||x=='r')major=true;
  else if(x=='n'){++minors;same=false;}
  else if(x=='b'){
   ++minors;
   int c=(rankof(i)+fileof(i))&1;
   if(bishopColor<0)bishopColor=c;
   else if(bishopColor!=c)same=false;
  }
 }
 if(!major&&(minors<=1||same))return "insufficient_material";
 return "ongoing";
}
static std::string key(const Board&b){
 auto name=toFen(b);std::istringstream in(name);
 std::string pieces,side,castle,ep;in>>pieces>>side>>castle>>ep;
 if(ep!="-"){
  bool possible=false;
  for(const auto&m:legal(b))if(m.ep){possible=true;break;}
  if(!possible)ep="-";
 }
 return pieces+" "+side+" "+castle+" "+ep;
}
int main(int argc,char**argv){
 try{
  std::string fenText,move;
  for(int i=1;i<argc;++i){std::string a=argv[i];if(a=="--fen"&&i+1<argc)fenText=argv[++i];
   else if(a=="--move"&&i+1<argc)move=argv[++i];else throw std::runtime_error("Usage: joshua_referee --fen SIX_FIELD_FEN [--move UCI]");}
  if(fenText.empty())throw std::runtime_error("Missing FEN");
  Board b=fen(fenText);if(check(b,-b.turn))throw std::runtime_error("Invalid FEN: previous side is in check");
  auto lm=legal(b);std::string san="-";
  if(!move.empty()){
   auto it=std::find_if(lm.begin(),lm.end(),[&](const Move&m){return uci(m)==move;});
   if(it==lm.end())throw std::runtime_error("Illegal UCI move: "+move);
   san=notationSan(b,*it,lm);b=apply(b,*it);
  }
  std::cout<<toFen(b)<<"\n"<<status(b)<<"\n"<<san<<"\n"<<key(b)<<"\n"<<legal(b).size()<<"\n";
  return 0;
 }catch(const std::exception&e){std::cerr<<"REFEREE_ERROR "<<e.what()<<"\n";return 2;}
}
