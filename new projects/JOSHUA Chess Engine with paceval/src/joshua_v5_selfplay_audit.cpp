// Source-aligned replay of V5 eight-ply graph-rebuilt self-play.
// This independently reconstructs all transitions from recorded UCI moves
// using the chess-rule implementation regression-tested against perft.
#include "paceval_main.h"
#include "chess_rules.h"
#include <fstream>
#include <map>
#include <iostream>
#include <sstream>
int main(int argc,char**argv) {
 try {
  insist(argc==2,"Usage: joshua_v5_selfplay_audit PATH_TO_TIMELINE_CSV");
  std::ifstream f(argv[1]);insist(bool(f),"Missing selfplay timeline");
  string header;insist(bool(std::getline(f,header)),"Missing CSV header");
  std::vector<string> headings;std::istringstream h(header);string item;
  while(std::getline(h,item,',')){if(!item.empty()&&item.back()=='\r')item.pop_back();headings.push_back(item);}
  std::map<string,int> col;
  for(int i=0;i<(int)headings.size();i++)col[headings[i]]=i;
  for(const auto& key:{"ply","side","move_uci","fen_before","fen_after","graph_characters","search_nodes"})
   insist(col.count(key),"Missing column: "+string(key));
  Board board=fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
  int plies=0;unsigned long long totalGraphChars=0;
  string line;
  while(std::getline(f,line)){
   if(line.empty())continue;
   std::vector<string> fields;std::istringstream ss(line);
   while(std::getline(ss,item,',')){if(!item.empty()&&item.back()=='\r')item.pop_back();fields.push_back(item);}
   auto val=[&](const string&k)->string{insist(col.at(k)<(int)fields.size(),"Missing CSV field");return fields[col.at(k)];};
   insist(std::stoi(val("ply"))==plies+1,"Incorrect ply index");
   insist(val("side")==string(board.turn==1?"white":"black"),"Incorrect side");
   insist(toFen(board)==val("fen_before"),"Incorrect FEN before move");
   const string chosen=val("move_uci");
   auto moves=legal(board);
   auto it=std::find_if(moves.begin(),moves.end(),[&](const Move&m){return uci(m)==chosen;});
   insist(it!=moves.end(),"Illegal recorded move "+chosen);
   board=apply(board,*it);
   insist(toFen(board)==val("fen_after"),"Incorrect FEN after move");
   insist(std::stoull(val("search_nodes"))>1,"Invalid node count");
   const auto chars=std::stoull(val("graph_characters"));insist(chars>100,"Invalid graph length");totalGraphChars+=chars;
   plies++;
  }
  insist(plies==8,"Expected exact eight-halfmove experimental record");
  std::cout<<"JOSHUA V5 GRAPH SELFPLAY REPLAY PASS: "<<plies<<" legal moves, "<<totalGraphChars<<" graph characters, final FEN="<<toFen(board)<<"\n";
 } catch(const std::exception&e) {std::cerr<<"JOSHUA V5 REPLAY ERROR: "<<e.what()<<"\n";return 1;}
 return 0;
}
