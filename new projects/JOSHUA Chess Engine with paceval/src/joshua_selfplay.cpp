// JOSHUA V6 continuous self-play supervisor and reproducible diagnostic logger.
// This program does not evaluate chess mathematics. It starts the ORIGINAL JOSHUA
// executable, which must use the local original paceval Mathematical Engine.
// Each game runs in its own subprocess to release ALL paceval handles at exit.
// Diagnostic triggers are hypotheses for later independent testing, not training.
#include <algorithm>
#include <atomic>
#include <cerrno>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <chrono>
#include <cmath>
#include <vector>
#include <ctime>
#include "paceval_main.h"
#include "chess_rules.h"
#include <sys/types.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <unistd.h>
namespace fs=std::filesystem;
using std::string; using std::vector;
static volatile sig_atomic_t stopRequested=0;
static volatile sig_atomic_t childPid=0;
static void stopHandler(int){stopRequested=1;if(childPid>0)kill(childPid,SIGTERM);}
static void require(bool ok,const string&msg){if(!ok)throw std::runtime_error(msg);}
static string trim(const string&s){const auto a=s.find_first_not_of(" \t\r\n"),b=s.find_last_not_of(" \t\r\n");return a==string::npos?"":s.substr(a,b-a+1);}
static string escapeJson(const string&s){string r;for(unsigned char c:s){if(c=='"'||c=='\\'){r+='\\';r+=c;}else if(c=='\n')r+="\\n";else if(c=='\r')r+="\\r";else if(c=='\t')r+="\\t";else if(c<32){const char *hex="0123456789abcdef";r+="\\u00";r+=hex[c>>4];r+=hex[c&15];}else r+=c;}return r;}
static string readText(const fs::path&p){std::ifstream f(p,std::ios::binary);require(bool(f),"Cannot read "+p.string());return string(std::istreambuf_iterator<char>(f),{});}
static void writeText(const fs::path&p,const string&s){std::ofstream f(p,std::ios::binary|std::ios::trunc);require(bool(f),"Cannot write "+p.string());f<<s;f.flush();require(bool(f),"Failed to flush "+p.string());}
static void appendText(const fs::path&p,const string&s){std::ofstream f(p,std::ios::binary|std::ios::app);require(bool(f),"Cannot append "+p.string());f<<s;f.flush();require(bool(f),"Failed to flush "+p.string());}
static string isoNow(){std::time_t t=std::time(nullptr);std::tm u{};gmtime_r(&t,&u);char buff[32];std::strftime(buff,sizeof(buff),"%Y-%m-%dT%H:%M:%SZ",&u);return buff;}
static string csvSafe(const string&s){string r="\"";for(char c:s){if(c=='"')r+='"';if(c=='\n'||c=='\r')r+=' ';else r+=c;}return r+'"';}
static vector<string> csvFields(const string&line){vector<string>out;string part;bool quoted=false;for(size_t i=0;i<line.size();i++){char c=line[i];if(c=='"'){if(quoted&&i+1<line.size()&&line[i+1]=='"'){part+='"';i++;}else quoted=!quoted;}else if(c==','&&!quoted){out.push_back(part);part.clear();}else part+=c;}require(!quoted,"Unterminated CSV quote");out.push_back(part);return out;}
using Record=std::map<string,string>;
static vector<Record> csvRead(const fs::path&p){std::ifstream f(p);require(bool(f),"Missing CSV "+p.string());string line;require(bool(std::getline(f,line)),"Empty CSV "+p.string());auto header=csvFields(line);vector<Record>rows;size_t lineNo=1;while(std::getline(f,line)){++lineNo;if(line.empty())continue;auto fields=csvFields(line);require(fields.size()==header.size(),"CSV width mismatch "+p.string()+" line="+std::to_string(lineNo));Record r;for(size_t j=0;j<header.size();j++)r[header[j]]=fields[j];rows.push_back(std::move(r));}return rows;}
static string get(const Record&r,const string&key){auto it=r.find(key);require(it!=r.end(),"Missing CSV column "+key);return it->second;}
static int asInt(const string&s){size_t pos=0;int n=std::stoi(s,&pos);require(pos==s.size(),"Invalid integer: "+s);return n;}
static double asDouble(const string&s){size_t pos=0;double n=std::stod(s,&pos);require(pos==s.size()&&std::isfinite(n),"Invalid finite number: "+s);return n;}
static string jsonString(const string&doc,const string&key,const string&fallback=""){
  const string tag="\""+key+"\"";size_t p=doc.find(tag);if(p==string::npos)return fallback;p=doc.find(':',p+tag.size());if(p==string::npos)return fallback;p=doc.find('"',p+1);if(p==string::npos)return fallback;
  string out;bool esc=false;for(++p;p<doc.size();p++){char c=doc[p];if(esc){out+=c;esc=false;}else if(c=='\\')esc=true;else if(c=='"')return out;else out+=c;}return fallback;
}
static string jsonNumber(const string&doc,const string&key,const string&fallback=""){
 const string tag="\""+key+"\"";size_t p=doc.find(tag);if(p==string::npos)return fallback;p=doc.find(':',p+tag.size());if(p==string::npos)return fallback;p=doc.find_first_not_of(" \t\n\r",p+1);if(p==string::npos)return fallback;size_t e=doc.find_first_of(",}\n\r",p);return trim(doc.substr(p,e==string::npos?string::npos:e-p));
}
static string positionKey(const string&fen){std::istringstream f(fen);string a,b,c,d;if(!(f>>a>>b>>c>>d))return fen;return a+" "+b+" "+c+" "+d;}
struct Observation{string code,location,detail,proposal;};
struct Analysis{string result="*",reason="unknown",finalFen="", gamePath="";size_t plies=0,largeSwings=0,closeChoices=0,repeatedPositions=0,captureMoves=0,uniquePositions=0;long long nodes=0,pacevalPoints=0;vector<Observation>findings;string firstMove="";};
static Analysis analyze(const fs::path&dir){
 Analysis a; a.gamePath=dir.string();const auto rows=csvRead(dir/"selfplay_timeline.csv"), rankings=csvRead(dir/"root_move_rankings.csv");
 require(fs::exists(dir/"run_evidence.json"),"Missing evidence file in "+dir.string());
 const string evidence=readText(dir/"run_evidence.json");
 require(evidence.find("\"mcp_used\": false")!=string::npos,"Expected local paceval run evidence, not MCP");
 if(fs::exists(dir/"end_state.json")){const auto state=readText(dir/"end_state.json");a.result=jsonString(state,"result","*");a.reason=jsonString(state,"termination","unknown");a.finalFen=jsonString(state,"final_fen","");a.plies=static_cast<size_t>(std::stoul(jsonNumber(state,"played_halfmoves","0")));}
 else {a.reason="legacy_unclassified";a.finalFen=jsonString(evidence,"final_fen","");a.plies=static_cast<size_t>(std::stoul(jsonNumber(evidence,"played_halfmoves","0")));}
 const int expected=asInt(jsonNumber(evidence,"played_halfmoves","0"));require(expected>=int(rows.size()),"Evidence moves smaller than timeline");if(!a.plies)a.plies=static_cast<size_t>(expected);
 std::map<int,vector<double>> ranked;std::map<int,string> chosen;
 for(auto&r:rankings){int ply=asInt(get(r,"halfmove"));ranked[ply].push_back(asDouble(get(r,"white_score_cp")));if(get(r,"rank")=="1")chosen[ply]=get(r,"uci");}
 std::map<string,int>positions;double previous=0;bool havePrevious=false;string previousFen;
 for(const auto&r:rows){
  const int ply=asInt(get(r,"halfmove"));const string side=get(r,"side"),fenBefore=get(r,"fen_before"),fenAfter=get(r,"fen_after"),uci=get(r,"chosen_uci");
  require(side=="white"||side=="black","Invalid side");require(uci.size()==4||uci.size()==5,"Invalid UCI");
  require(chosen[ply]==uci,"Selected root move inconsistent with ranking at ply "+std::to_string(ply));
  if(!previousFen.empty())require(previousFen==fenBefore,"Broken FEN chain at ply "+std::to_string(ply));previousFen=fenAfter;
  if(positions.empty())positions[positionKey(fenBefore)]++;
  if(++positions[positionKey(fenAfter)]==2){a.repeatedPositions++;if(a.repeatedPositions<=4)a.findings.push_back({"REPEATED_POSITION","ply "+std::to_string(ply),"A prior board state recurred.","Review draw-aware evaluation, repetition penalties and transposition-history handling."});}
  a.nodes+=std::stoll(get(r,"tree_nodes"));a.pacevalPoints=static_cast<long long>(asDouble(get(r,"paceval_graph_points_total")));
  if(get(r,"is_capture")=="1")a.captureMoves++;
  const double score=asDouble(get(r,"white_score_cp"));
  if(havePrevious&&std::abs(score-previous)>=250.0){a.largeSwings++;if(a.largeSwings<=6){std::ostringstream msg;msg<<"White-perspective root score changed from "<<previous<<" cp to "<<score<<" cp across adjacent turns; this is NOT independent proof of a blunder.";a.findings.push_back({"EVALUATION_REVERSAL","ply "+std::to_string(ply)+" "+uci,msg.str(),"Replay this FEN at depth d, d+2, with/without quiescence. Confirm a tactical error using an independent reference before changing weights."});}}
  previous=score;havePrevious=true;
  const auto it=ranked.find(ply);if(it!=ranked.end()&&it->second.size()>=2){double gap=side=="white"?it->second[0]-it->second[1]:it->second[1]-it->second[0];if(gap>=-1e-7&&gap<=12.0){a.closeChoices++;if(a.closeChoices<=4)a.findings.push_back({"CLOSE_ROOT_CHOICES","ply "+std::to_string(ply)+" "+uci,"The top two candidate scores differ by at most 12 cp.","Test depth stability and evaluate alternative lines. Add controlled opening diversity rather than changing score coefficients from this signal alone."});}}
 }
 a.uniquePositions=positions.size();
 if(a.reason=="max_halfmoves"){a.findings.push_back({"MOVE_LIMIT","game end","Search stopped at the configured halfmove limit. This is NOT a completed or drawn chess game.","Raise --plies if acceptable, and compare decisive-game rates under identical search settings."});}
 if(a.reason=="threefold_repetition"||a.reason=="fifty_move_rule"||a.reason=="insufficient_material")a.findings.push_back({"DRAW_MECHANISM","game end","Draw recorded by a defined termination rule: "+a.reason,"Investigate repetition-awareness, progress incentives and endgame-specific evaluation with an independent holdout test."});
 if(a.reason=="checkmate")a.findings.push_back({"DECISIVE_GAME","game end","Legal checkmate outcome reported by the chess host.","Retain the complete move trajectory for tactical replay and compare alternative model versions against fixed positions."});
 if(a.largeSwings==0&&a.closeChoices==0&&a.repeatedPositions==0)a.findings.push_back({"NO_TRIGGER","game end","No configured diagnostic threshold was crossed.","Keep this game as a baseline. No algorithmic improvement can be inferred from this trace alone."});
 return a;
}
static void logAnalysis(const Analysis&a,const fs::path&root,int gameNumber,const string&opening,const string&stamp){
 std::ostringstream out;
 out<<"\n## Game "<<gameNumber<<" | "<<stamp<<"\n\n";
 out<<"Game folder: `"<<a.gamePath<<"`  \nOpening control: `"<<(opening.empty()?"engine-selected":opening)<<"`  \n";
 out<<"Result: `"<<a.result<<"`; termination: `"<<a.reason<<"`; played plies: "<<a.plies<<"  \n";
 out<<"Observed search nodes (sum of recorded root searches): "<<a.nodes<<". paceval graph-point counter: "<<(a.pacevalPoints>0?std::to_string(a.pacevalPoints):"not available for the V5 full-graph path")<<". These counts do not measure chess strength.  \n";
 out<<"Diagnostic summary: score reversals="<<a.largeSwings<<", near-tied root choices="<<a.closeChoices<<", recurring board states="<<a.repeatedPositions<<", captures="<<a.captureMoves<<".\n\n";
 out<<"### Review candidates (not automatically trained)\n\n";
 for(auto&f:a.findings)out<<"- **"<<f.code<<"**, "<<f.location<<": "<<f.detail<<"  Suggested experiment: "<<f.proposal<<"\n";
 out<<"\n**Limits:** Score jumps are heuristic alarms, not independently proven mistakes. The code does not update neural weights, evolve graphs, or prove that any proposed improvement works. All actual game evaluations must come from the original paceval runtime.\n";
 writeText(fs::path(a.gamePath)/"learning_report.md",out.str());appendText(root/"learning_log.md",out.str());
 std::ostringstream js;js<<"{\"game\":"<<gameNumber<<",\"timestamp\":\""<<escapeJson(stamp)<<"\",\"directory\":\""<<escapeJson(a.gamePath)<<"\",\"opening\":\""<<escapeJson(opening)<<"\",\"result\":\""<<escapeJson(a.result)<<"\",\"termination\":\""<<escapeJson(a.reason)<<"\",\"plies\":"<<a.plies<<",\"score_reversals\":"<<a.largeSwings<<",\"close_choices\":"<<a.closeChoices<<",\"repeated_positions\":"<<a.repeatedPositions<<",\"paceval_graph_points\":"<<a.pacevalPoints<<",\"flags\":[";
 for(size_t i=0;i<a.findings.size();i++){if(i)js<<',';auto&f=a.findings[i];js<<"{\"code\":\""<<escapeJson(f.code)<<"\",\"location\":\""<<escapeJson(f.location)<<"\",\"detail\":\""<<escapeJson(f.detail)<<"\",\"proposal\":\""<<escapeJson(f.proposal)<<"\"}";}
 js<<"]}\n";appendText(root/"learning_events.jsonl",js.str());
 if(!fs::exists(root/"games_index.csv"))appendText(root/"games_index.csv","game,timestamp,directory,opening,result,termination,plies,score_reversals,close_choices,repeated_positions,paceval_graph_points\n");
 appendText(root/"games_index.csv",std::to_string(gameNumber)+","+csvSafe(stamp)+","+csvSafe(a.gamePath)+","+csvSafe(opening)+","+csvSafe(a.result)+","+csvSafe(a.reason)+","+std::to_string(a.plies)+","+std::to_string(a.largeSwings)+","+std::to_string(a.closeChoices)+","+std::to_string(a.repeatedPositions)+","+std::to_string(a.pacevalPoints)+"\n");
 // Exact FEN and UCI rows turn the suggestions into a reproducible experiment
 // queue for the next source-code iteration, not automatic neural training.
 const fs::path queue=root/"analysis_queue.csv";
 if(!fs::exists(queue))appendText(queue,"game,ply,flag,uci,fen_before,white_score_cp,proposed_followup\n");
 const fs::path local=fs::path(a.gamePath)/"analysis_queue.csv";
 writeText(local,"game,ply,flag,uci,fen_before,white_score_cp,proposed_followup\n");
 const auto rows=csvRead(fs::path(a.gamePath)/"selfplay_timeline.csv");
 std::map<int,Record>byPly;for(const auto&r:rows)byPly[asInt(get(r,"halfmove"))]=r;
 for(const auto&f:a.findings){
   if(f.location.rfind("ply ",0)!=0)continue;
   int ply=0;try{ply=asInt(f.location.substr(4,f.location.find(' ',4)-4));}catch(const std::exception&){continue;}
   auto it=byPly.find(ply);if(it==byPly.end())continue;
   const auto&r=it->second;
   const string row=std::to_string(gameNumber)+","+std::to_string(ply)+","+csvSafe(f.code)+","+csvSafe(get(r,"chosen_uci"))+","+csvSafe(get(r,"fen_before"))+","+get(r,"white_score_cp")+","+csvSafe(f.proposal)+"\n";
   appendText(queue,row);appendText(local,row);
 }
}
struct Settings{fs::path engine="",output="selfplay_sessions",analyzeOnly="";int depth=2,model=4,quiescence=2,plies=160,maxGames=0,pauseMs=0,seed=20261115;string mode="alphabeta",opening="cycle",firstMove="";int maxNodes=25000,maxChars=2500000;};
static vector<string> openings(){return {"e2e4","d2d4","c2c4","g1f3","b1c3","e2e3","d2d3","g2g3","b2b3","f2f4","a2a3","h2h3","a2a4","h2h4"};}
static void usage(){std::cout<<"JOSHUA V6 continuous self-play supervisor (Linux x86-64, uses genuine local paceval via ./joshua)\n"
 "  --engine PATH           Existing genuine JOSHUA executable (default: ./joshua next to supervisor)\n"
 "  --output DIR            Durable session directory (default: selfplay_sessions)\n"
 "  --max-games N           N=0 means indefinitely, Ctrl+C stops after SIGTERM\n"
 "  --depth N --model 1..4 --quiescence N --plies N --mode alphabeta|research|longgraph\n"
 "  --opening cycle|fixed  Cycle deterministic, legal first moves to avoid identical games\n"
 "  --first-move UCI        Used with --opening fixed; empty allows normal selection\n"
 "  --seed N                Deterministic opening rotation (default: 20261115)\n"
 "  --max-nodes N --max-chars N  Full V5 mathematical decision-tree budgets\n"
 "  --pause-ms N            Pause between games; no background service\n"
 "  --analyze-only DIR      Offline analyse existing game without paceval execution\n"
 "  --selftest              Test parser and signals without executing paceval\n";}
static int nextGameNumber(const fs::path&root){int n=1;if(fs::exists(root))for(const auto&e:fs::directory_iterator(root)){if(!e.is_directory())continue;const string s=e.path().filename().string();if(s.size()==11&&s.rfind("game_",0)==0){try{n=std::max(n,asInt(s.substr(5))+1);}catch(const std::exception&){}}}return n;}
static int runChild(const vector<string>&argv,const fs::path&out){
 require(!argv.empty(),"Missing engine");std::ofstream(out/"launch_arguments.txt")<<"Arguments are recorded in game_console.log header.\n";
 pid_t pid=fork();require(pid>=0,"fork() failed");
 if(pid==0){int fd=open((out/"game_console.log").c_str(),O_WRONLY|O_CREAT|O_TRUNC,0644);if(fd<0)_exit(127);dup2(fd,STDOUT_FILENO);dup2(fd,STDERR_FILENO);close(fd);vector<char*>cargs;for(auto&x:argv)cargs.push_back(const_cast<char*>(x.c_str()));cargs.push_back(nullptr);execv(argv[0].c_str(),cargs.data());std::cerr<<"execv failed: "<<std::strerror(errno)<<'\n';_exit(127);}
 childPid=pid;int status=0;for(;;){pid_t n=waitpid(pid,&status,0);if(n==pid)break;if(n<0&&errno==EINTR)continue;throw std::runtime_error("waitpid() failed");}childPid=0;
 if(WIFEXITED(status))return WEXITSTATUS(status);if(WIFSIGNALED(status))return 128+WTERMSIG(status);return 127;
}
// The second route implements V5's genuine full-tree mathematical graph, rebuilt
// once for EVERY engine-selected halfmove. The supervisor decides only when chess
// ends and writes an interoperable record; paceval still evaluates leaf/decision
// formulas inside the original joshua_long_graph executable.
static void playLongGraph(const Settings&s,const fs::path&dir,const string&opening){
 const string initial="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
 Board board=fen(initial);
 std::map<string,int>history;history[positionKey(toFen(board))]++;
 vector<string>played;
 int forced=0;
 if(!opening.empty()){
  const auto allowed=legal(board);const auto it=std::find_if(allowed.begin(),allowed.end(),[&](const Move&m){return uci(m)==opening;});
  require(it!=allowed.end(),"Illegal forced opening for longgraph: "+opening);
  board=apply(board,*it);played.push_back(opening);forced=1;
  history[positionKey(toFen(board))]++;
 }
 std::ofstream timeline(dir/"selfplay_timeline.csv"),moves(dir/"root_move_rankings.csv"),games(dir/"game_uci.txt");
 require(bool(timeline)&&bool(moves)&&bool(games),"Cannot create V5 longgraph result files");
 timeline<<"halfmove,side,tree_nodes,paceval_graph_points_total,chosen_uci,is_capture,white_score_cp,fen_before,fen_after\n";
 moves<<"halfmove,depth,side,rank,uci,white_score_cp\n";
 string termination="max_halfmoves",result="*";long long graphChars=0,graphCount=0,verified=0;
 for(int ply=forced;ply<s.plies;ply++){
   const auto allowed=legal(board);
   if(allowed.empty()){
     termination=check(board,board.turn)?"checkmate":"stalemate";
     result=check(board,board.turn)?(board.turn==1?"0-1":"1-0"):"1/2-1/2";break;
   }
   if(board.half>=100||history[positionKey(toFen(board))]>=3){termination=board.half>=100?"fifty_move_rule":"threefold_repetition";result="1/2-1/2";break;}
   std::ostringstream tag;tag<<"ply_"<<std::setw(3)<<std::setfill('0')<<(ply+1);
   const auto current=dir/tag.str();fs::create_directories(current);
   const string before=toFen(board),side=board.turn==1?"white":"black";
   const vector<string>args={s.engine.string(),"--depth",std::to_string(s.depth),"--model",std::to_string(s.model),"--fen",before,"--max-nodes",std::to_string(s.maxNodes),"--max-chars",std::to_string(s.maxChars),"--output",current.string()};
   const int exitCode=runChild(args,current);
   if(exitCode!=0)throw std::runtime_error("V5 graph compilation failed on ply "+std::to_string(ply+1)+" (exit "+std::to_string(exitCode)+"). See "+(current/"game_console.log").string());
   const string ev=readText(current/"run_evidence.json");
   require(jsonNumber(ev,"graph_result_verified")=="true"&&jsonNumber(ev,"reused_graph_result_verified")=="true","Independent paceval graph checks not passed");
   require(jsonString(ev,"fen_before")==before,"V5 generated graph for an incorrect FEN");
   const string chosen=jsonString(ev,"selected_move"),after=jsonString(ev,"fen_after");
   auto matched=std::find_if(allowed.begin(),allowed.end(),[&](const Move&m){return uci(m)==chosen;});
   require(matched!=allowed.end(),"V5 selected illegal move "+chosen);
   const Board next=apply(board,*matched);require(toFen(next)==after,"V5 incorrect next-board FEN for "+chosen);
   const bool capture=board.b[matched->t]!='.'||matched->ep;
   auto opts=csvRead(current/"root_moves.csv");require(opts.size()==allowed.size(),"V5 root rank count mismatch");
   vector<std::pair<string,double>>ranked;for(auto&r:opts)ranked.push_back({get(r,"move"),asDouble(get(r,"score_white_cp"))});
   std::sort(ranked.begin(),ranked.end(),[&](const auto&a,const auto&b){if(a.second!=b.second)return board.turn==1?a.second>b.second:a.second<b.second;return a.first<b.first;});
   require(!ranked.empty()&&ranked.front().first==chosen,"V5 best move inconsistent with sorted root values");
   for(size_t j=0;j<ranked.size();j++)moves<<(ply+1)<<','<<s.depth<<','<<side<<','<<(j+1)<<','<<ranked[j].first<<','<<ranked[j].second<<'\n';
   timeline<<(ply+1)<<','<<side<<','<<jsonNumber(ev,"nodes","0")<<",0,"<<chosen<<','<<(capture?1:0)<<','<<ranked.front().second<<",\""<<before<<"\",\""<<after<<"\"\n";
   require(bool(moves)&&bool(timeline),"V5 timeline write failed");
   graphChars+=std::stoll(jsonNumber(ev,"graph_characters","0"));graphCount++;verified++;
   board=next;played.push_back(chosen);history[positionKey(toFen(board))]++;
 }
 if(termination=="max_halfmoves"){
  const auto lm=legal(board);
  if(lm.empty()){termination=check(board,board.turn)?"checkmate":"stalemate";result=check(board,board.turn)?(board.turn==1?"0-1":"1-0"):"1/2-1/2";}
  else if(board.half>=100||history[positionKey(toFen(board))]>=3){termination=board.half>=100?"fifty_move_rule":"threefold_repetition";result="1/2-1/2";}
 }
 for(const auto&m:played)games<<m<<' ';games<<"\nfinal_fen "<<toFen(board)<<'\n';
 std::ostringstream evidence;evidence<<"{\n  \"sdk\": \"original local paceval\",\n  \"mode\": \"longgraph\",\n  \"mcp_used\": false,\n  \"played_halfmoves\": "<<played.size()<<",\n  \"final_fen\": \""<<escapeJson(toFen(board))<<"\",\n  \"full_tree_paceval_graphs_built\": "<<graphCount<<",\n  \"independently_checked_graphs\": "<<verified<<",\n  \"total_formula_characters\": "<<graphChars<<",\n  \"graph_point_counter_available\": false\n}\n";
 writeText(dir/"run_evidence.json",evidence.str());
 std::ostringstream end;end<<"{\"result\":\""<<result<<"\",\"termination\":\""<<termination<<"\",\"played_halfmoves\":"<<played.size()<<",\"final_fen\":\""<<escapeJson(toFen(board))<<"\"}\n";
 writeText(dir/"end_state.json",end.str());
}
static void selftest(){
 require(csvFields("x,\"y, z\",\"a\"\"b\"").size()==3,"CSV quoting failed");
 require(csvFields("x,\"y, z\",\"a\"\"b\"")[2]=="a\"b","CSV escaping failed");
 require(jsonString("{\"result\":\"1-0\"}","result")=="1-0","JSON field failed");
 require(positionKey("8/8/8/8/8/8/8/K6k w - - 0 1")=="8/8/8/8/8/8/8/K6k w - -","FEN key failed");
 require(openings().size()>=12,"Opening coverage insufficient");
 const Board mate=fen("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3");
 require(legal(mate).empty()&&check(mate,mate.turn),"Checkmate classification fixture failed");
 const Board stalemate=fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1");
 require(legal(stalemate).empty()&&!check(stalemate,stalemate.turn),"Stalemate classification fixture failed");
 std::cout<<"JOSHUA_SELFPLAY_MANAGER_SELFTEST_PASS parser json FEN openings mate stalemate\n";
}
int main(int argc,char**argv){try{
 Settings s;for(int i=1;i<argc;i++){string a=argv[i];auto getarg=[&](){require(i+1<argc,"Missing value for "+a);return string(argv[++i]);};
  if(a=="--help"){usage();return 0;}else if(a=="--selftest"){selftest();return 0;}
  else if(a=="--engine")s.engine=getarg();else if(a=="--output")s.output=getarg();else if(a=="--depth")s.depth=asInt(getarg());else if(a=="--model")s.model=asInt(getarg());else if(a=="--quiescence")s.quiescence=asInt(getarg());else if(a=="--plies")s.plies=asInt(getarg());else if(a=="--max-games")s.maxGames=asInt(getarg());else if(a=="--pause-ms")s.pauseMs=asInt(getarg());else if(a=="--seed")s.seed=asInt(getarg());else if(a=="--mode")s.mode=getarg();else if(a=="--max-nodes")s.maxNodes=asInt(getarg());else if(a=="--max-chars")s.maxChars=asInt(getarg());else if(a=="--opening")s.opening=getarg();else if(a=="--first-move")s.firstMove=getarg();else if(a=="--analyze-only")s.analyzeOnly=getarg();else throw std::runtime_error("Unknown option: "+a);
 }
 require(s.depth>=1&&s.depth<=10&&s.model>=1&&s.model<=4&&s.quiescence>=0&&s.quiescence<=4&&s.plies>=1&&s.plies<=200,"Invalid search configuration");
 require(s.mode=="alphabeta"||s.mode=="research"||s.mode=="longgraph","Unknown --mode");require((s.mode=="alphabeta")||(s.depth<=4&&s.quiescence==0),"Research and longgraph require depth<=4 and quiescence=0");require(s.mode!="longgraph"||(s.model>=3&&s.maxNodes>=100&&s.maxChars>=100),"Longgraph requires model 3 or 4 and positive resource budgets");
 require(s.maxGames>=0&&s.pauseMs>=0&&s.pauseMs<=3600000,"Invalid max games or pause");require(s.opening=="cycle"||s.opening=="fixed","Invalid opening policy");
 if(!s.analyzeOnly.empty()){auto a=analyze(s.analyzeOnly);fs::create_directories(s.output);logAnalysis(a,s.output,nextGameNumber(s.output),"offline-analysis",isoNow());std::cout<<"ANALYSIS_OK result="<<a.result<<" plies="<<a.plies<<" flags="<<a.findings.size()<<"\n";return 0;}
 if(s.engine.empty()){fs::path local=fs::absolute(argv[0]).parent_path()/(s.mode=="longgraph"?"joshua_long_graph":"joshua");s.engine=local;}
 s.engine=fs::absolute(s.engine);require(fs::exists(s.engine),"JOSHUA executable unavailable at "+s.engine.string()+"; build it against the original paceval runtime first");require(access(s.engine.c_str(),X_OK)==0,"JOSHUA executable not executable");
 s.output=fs::absolute(s.output);fs::create_directories(s.output);
 struct sigaction sa{};sa.sa_handler=stopHandler;sigemptyset(&sa.sa_mask);sigaction(SIGTERM,&sa,nullptr);sigaction(SIGINT,&sa,nullptr);
 int game=nextGameNumber(s.output),completed=0;const vector<string>openingSet=openings();
 std::cout<<"JOSHUA CONTINUOUS SELFPLAY: engine="<<s.engine<<" output="<<s.output<<" max-games="<<s.maxGames<<" (0=infinite)\n";
 while(!stopRequested&&(s.maxGames==0||completed<s.maxGames)){
   std::ostringstream name;name<<"game_"<<std::setw(6)<<std::setfill('0')<<game;const fs::path dir=s.output/name.str();require(!fs::exists(dir),"Refusing to overwrite existing game directory");fs::create_directories(dir);
   string opening=s.opening=="cycle"?openingSet[(static_cast<unsigned long long>(s.seed)+static_cast<unsigned long long>(game-1))%openingSet.size()]:s.firstMove;
   vector<string>args={s.engine.string(),"--mode",s.mode,"--depth",std::to_string(s.depth),"--model",std::to_string(s.model),"--quiescence",std::to_string(s.quiescence),"--plies",std::to_string(s.plies),"--no-board","--output",dir.string()};if(!opening.empty()){args.push_back("--first-move");args.push_back(opening);}
   const auto ts=isoNow();std::cout<<"GAME_START "<<game<<" opening="<<(opening.empty()?"engine-selected":opening)<<" "<<ts<<std::endl;
   int exitCode=0;
   if(s.mode=="longgraph"){
     // The dedicated V5 executable has a different command line and creates
     // one complete paceval graph for each move, not a traditional AB search.
     try{playLongGraph(s,dir,opening);}catch(const std::exception&ex){
       appendText(s.output/"manager_errors.log",ts+" V5_LONGGRAPH_ERROR game "+std::to_string(game)+": "+ex.what()+"\n");
       if(stopRequested){writeText(dir/"interrupted.txt","User signal interrupted this V5 graph game. Results are incomplete.\n");return 0;}
       std::cerr<<ex.what()<<'\n';return 2;
     }
   }else exitCode=runChild(args,dir);
   writeText(dir/"manager_exit_code.txt",std::to_string(exitCode)+"\n");
   if(stopRequested){
     writeText(dir/"interrupted.txt","Stopped by user signal while the game was active. This is NOT a completed chess game.\n");
     std::cout<<"SUPERVISOR_STOP interrupted_game="<<game<<" completed_games="<<completed<<" reason=user_signal\n";
     return 0;
   }
   if(exitCode!=0){string msg="JOSHUA engine exited with code "+std::to_string(exitCode)+". Read "+(dir/"game_console.log").string()+". The manager stops to prevent an infinite failure loop.\n";appendText(s.output/"manager_errors.log",ts+" "+msg);std::cerr<<msg;return exitCode==0?1:exitCode;}
   try{auto a=analyze(dir);logAnalysis(a,s.output,game,opening,ts);std::cout<<"GAME_END "<<game<<" result="<<a.result<<" termination="<<a.reason<<" plies="<<a.plies<<" diagnostic_flags="<<a.findings.size()<<"\n";}catch(const std::exception&ex){appendText(s.output/"manager_errors.log",ts+" ANALYSIS_ERROR game "+std::to_string(game)+": "+ex.what()+"\n");throw;}
   ++game;++completed;
   if(s.pauseMs>0&&!stopRequested)for(int n=0;n<s.pauseMs&&!stopRequested;n+=100)std::this_thread::sleep_for(std::chrono::milliseconds(std::min(100,s.pauseMs-n)));
 }
 std::cout<<"SUPERVISOR_STOP completed_games="<<completed<<" reason="<<(stopRequested?"signal":"configured_limit")<<std::endl;return 0;
 }catch(const std::exception&ex){std::cerr<<"JOSHUA_SELFPLAY_ERROR "<<ex.what()<<'\n';return 2;}}
