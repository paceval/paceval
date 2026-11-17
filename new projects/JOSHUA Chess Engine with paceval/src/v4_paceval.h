#pragma once
#include "joshua_v4_features.h"
#include "v4_trained_model.h"
#include "v4_graph_formulas.h"
#include "adaptive_score_graph.h"
struct NeuralV4 {
 Engine& e;
 vector<PACEVAL_HANDLE> hidden;
 PACEVAL_HANDLE fused{};
 PACEVAL_HANDLE fusedAdaptive{};
 std::string fusedAdaptiveFormula;
 size_t checked=0, fusedChecks=0;
 explicit NeuralV4(Engine&eng,const joshua_adapt::Spec* adaptiveSpec=nullptr,bool allowFusion=true):e(eng){
   insist(V4_INPUTS==48 && featureNamesV4.size()==48,"V4 network input mismatch");
   for(int i=0;i<V4_HIDDEN;i++)hidden.push_back(e.create(V4_GRAPH_EXPRESSIONS[i],featureNamesV4));
   vector<string>names;for(int i=0;i<V4_HIDDEN;i++)names.push_back("h"+std::to_string(i));names.push_back("base");
   fused=e.create(V4_GRAPH_EXPRESSIONS[V4_HIDDEN],names);
   // V13: one persistent paceval graph evaluates the original fused V4 output
   // plus the bounded adaptive correction. All twelve sigmoid graphs remain
   // separately reusable; no arithmetic evaluation is moved to C++.
   // Model inputs are the 12 sigmoid values, the V3 base, then the 48 board features.
   if(adaptiveSpec && allowFusion && !adaptiveSpec->expression.empty()){
     fusedAdaptiveFormula=adaptiveSpec->expression;
     const std::size_t marker=fusedAdaptiveFormula.find("base+");
     insist(marker!=std::string::npos,"Adaptive template missing base term");
     fusedAdaptiveFormula.replace(marker,5,"("+std::string(V4_GRAPH_EXPRESSIONS[V4_HIDDEN])+")+");
     names.insert(names.end(),featureNamesV4.begin(),featureNamesV4.end());
     fusedAdaptive=e.create(fusedAdaptiveFormula,names);
   }
 }
 // One paceval batch for all hidden units and one for the composed output.
 // Reference comparisons use the independently executed unfused graph path.
 vector<double> scoreAdaptiveBatch(const vector<vector<double>>&rows,const vector<double>&base,
                                    joshua_adapt::Graph&adaptive){
   insist(fusedAdaptive!=nullptr && adaptive.active(),"Fused adaptive graph not ready");
   insist(!rows.empty()&&rows.size()==base.size(),"Fused score input mismatch");
   auto intermediate=e.multi(hidden,rows);
   vector<vector<double>>inputs; inputs.reserve(rows.size());
   for(size_t i=0;i<rows.size();i++){
     auto x=std::move(intermediate[i]); x.push_back(base[i]);
     x.insert(x.end(),rows[i].begin(),rows[i].end());
     inputs.push_back(std::move(x));
   }
   auto scores=e.single(fusedAdaptive,inputs);
   adaptive.evaluations+=rows.size();
   for(size_t i=0;i<rows.size() && fusedChecks<12;i++){
     const double first=independent(rows[i],base[i]);
     vector<double>referenceInputs=rows[i]; referenceInputs.push_back(first);
     const double reference=e.eval(adaptive.h,referenceInputs);
     const double tol=2e-7*(1+std::max(std::abs(scores[i]),std::abs(reference)));
     insist(std::abs(scores[i]-reference)<=tol,"Fused adaptive paceval mismatch");
     ++fusedChecks;
   }
   checked+=rows.size();
   return scores;
 }
 double scoreAdaptiveOne(const vector<double>&row,double base,joshua_adapt::Graph&adaptive){
   return scoreAdaptiveBatch({row},{base},adaptive)[0];
 }
 void exportFusedGraph(const std::string&directory)const {
   if(!fusedAdaptive)return;
   std::ofstream out(std::filesystem::path(directory)/"paceval_v13_fused_score.txt");
   insist(bool(out),"Cannot write fused paceval formula");
   out<<"# V13 genuine persistent paceval graph: 12 hidden outputs, V3 base, 48 features\n";
   out<<"# The 12 hidden output graphs are evaluated separately and reused.\n";
   out<<"variables=";
   for(int i=0;i<V4_HIDDEN;i++)out<<"h"<<i<<",";
   out<<"base";
   for(const auto&name:featureNamesV4)out<<","<<name;
   out<<"\nexpression="<<fusedAdaptiveFormula<<"\n";
 }

 double independent(const vector<double>&x,double base) const {
   insist(int(x.size())==V4_INPUTS,"V4 independent evaluator: input width mismatch");
   double z=V4_BIAS;
   for(int h=0;h<V4_HIDDEN;h++){
     double t=V4_B[h];
     for(int k=0;k<V4_INPUTS;k++)t+=V4_W[h][k]*(x[k]-V4_MEAN[k])/V4_SCALE[k];
     const double sigmoid=t>=0?1.0/(1.0+std::exp(-t)):std::exp(t)/(1.0+std::exp(t));
     z+=V4_OUT[h]*sigmoid;
   }
   return base+std::max(-V4_CLIP,std::min(V4_CLIP,100.0*z));
 }
 vector<double> scoreBatch(const vector<vector<double>>&rows,const vector<double>&base){
   insist(!rows.empty()&&rows.size()==base.size(),"V4 batch mismatch");
   auto intermediate=e.multi(hidden,rows);
   vector<vector<double>>inputs;inputs.reserve(rows.size());
   for(size_t i=0;i<rows.size();i++){
     auto x=std::move(intermediate[i]);x.push_back(base[i]);inputs.push_back(std::move(x));
   }
   auto scores=e.single(fused,inputs);
   for(size_t i=0;i<rows.size();i++){
     const double ref=independent(rows[i],base[i]);
     if(std::abs(scores[i]-ref)>2e-8*(1+std::max(std::abs(scores[i]),std::abs(ref)))) {
       std::ostringstream error; error<<std::setprecision(17)<<"V4 mismatch paceval="<<scores[i]<<" native="<<ref<<" base="<<base[i]<<" diff="<<scores[i]-ref;
       throw std::runtime_error(error.str());
     } checked++;
   }
   return scores;
 }
 double scoreOne(const vector<double>&row,double base){
   return scoreBatch({row},{base})[0];
 }
};
