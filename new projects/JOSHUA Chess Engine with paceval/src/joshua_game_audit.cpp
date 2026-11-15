// Validate the historical ChatGPT-white/JOSHUA-black game independently from
// recorded moves, using the same independently tested chess-rule routines.
#include "paceval_main.h"
#include "chess_rules.h"
#include <fstream>
#include <filesystem>
#include <sstream>
using std::string;
static std::vector<string> csvrow(const string&line){
 std::vector<string> out;string v;bool quoted=false;
 for(size_t i=0;i<line.size();i++){char c=line[i];if(c=='"'){if(quoted&&i+1<line.size()&&line[i+1]=='"'){v+='"';i++;}else quoted=!quoted;}
 else if(c==','&&!quoted){out.push_back(v);v.clear();}else v+=c;}
 out.push_back(v);return out;
}
int main(int argc,char**argv){try{
 insist(argc==3,"Usage: joshua_game_audit INPUT.csv OUTPUT.json");
 std::ifstream f(argv[1]);insist(bool(f),"Missing recorded chess game");
 string line;insist(bool(std::getline(f,line)),"Empty CSV");
 auto names=csvrow(line);std::map<string,size_t>fields;for(size_t i=0;i<names.size();i++)fields[names[i]]=i;
 for(const auto&n:{"ply","side","uci","fen_before","fen_after","san"})insist(fields.count(n)>0,"Missing CSV column "+string(n));
 auto field=[&](const std::vector<string>&r,const string&n)->string{auto i=fields.at(n);insist(i<r.size(),"Truncated CSV");return r[i];};
 Board board=fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
 int plies=0,white=0,black=0,blackKnightMoves=0,whiteCaptures=0,blackCaptures=0,blackKnightLosses=0;
 string lastBlackMove,openingBlack;
 while(std::getline(f,line)){
  if(line.empty())continue;const auto r=csvrow(line);
  insist(std::stoi(field(r,"ply"))==plies+1,"Ply index mismatch");
  insist(toFen(board)==field(r,"fen_before"),"Recorded FEN before does not match replayed board at ply "+std::to_string(plies+1));
  insist(field(r,"side")==string(board.turn==1?"white":"black"),"Side-to-move mismatch");
  const string move=field(r,"uci");auto moves=legal(board);
  auto it=std::find_if(moves.begin(),moves.end(),[&](const Move&m){return uci(m)==move;});
  insist(it!=moves.end(),"Illegal recorded move at ply "+std::to_string(plies+1)+": "+move);
  const char piece=board.b[it->f];const bool capture=board.b[it->t]!='.'||it->ep;
  if(board.turn==1){white++;if(capture)whiteCaptures++;}else{
   black++;lastBlackMove=move;if(black==1)openingBlack=move;
   if(std::tolower(static_cast<unsigned char>(piece))=='n')blackKnightMoves++;
   if(capture)blackCaptures++;
  }
  if(board.turn==1&&capture&&std::tolower(static_cast<unsigned char>(board.b[it->t]))=='n')blackKnightLosses++;
  board=apply(board,*it);
  insist(toFen(board)==field(r,"fen_after"),"Recorded FEN after does not match replayed board at ply "+std::to_string(plies+1));
  plies++;
 }
 insist(plies>=90,"Expected the recorded 94-ply historical game");
 const bool ongoing=!legal(board).empty();
 std::filesystem::create_directories(std::filesystem::path(argv[2]).parent_path());
 std::ofstream out(argv[2]);insist(bool(out),"Could not write audit report");
 out<<"{\n  \"verified_halfmoves\": "<<plies<<",\n  \"chatgpt_white_moves\": "<<white
    <<",\n  \"joshua_black_moves\": "<<black<<",\n  \"joshua_knight_moves\": "<<blackKnightMoves
    <<",\n  \"white_captures\": "<<whiteCaptures<<",\n  \"black_captures\": "<<blackCaptures
    <<",\n  \"black_knights_captured\": "<<blackKnightLosses
    <<",\n  \"game_finished\": "<<(ongoing?"false":"true")
    <<",\n  \"final_fen\": \""<<toFen(board)<<"\"\n}\n";
 std::cout<<"JOSHUA GAME AUDIT PASS: "<<plies<<" legal moves, FEN transitions independently reconstructed, unfinished="<<(ongoing?"yes":"no")<<"\n";
 }catch(const std::exception&e){std::cerr<<"JOSHUA GAME AUDIT FAILED: "<<e.what()<<"\n";return 1;}return 0;
}
