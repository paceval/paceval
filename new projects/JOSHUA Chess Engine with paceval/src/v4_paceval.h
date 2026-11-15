#pragma once
#include "joshua_v4_features.h"
#include "v4_trained_model.h"
#include "v4_graph_formulas.h"
struct NeuralV4 {
 Engine& e;
 vector<PACEVAL_HANDLE> hidden;
 PACEVAL_HANDLE fused{};
 size_t checked=0;
 explicit NeuralV4(Engine&eng):e(eng){
   insist(V4_INPUTS==48 && featureNamesV4.size()==48,"V4 network input mismatch");
   for(int i=0;i<V4_HIDDEN;i++)hidden.push_back(e.create(V4_GRAPH_EXPRESSIONS[i],featureNamesV4));
   vector<string>names;for(int i=0;i<V4_HIDDEN;i++)names.push_back("h"+std::to_string(i));names.push_back("base");
   fused=e.create(V4_GRAPH_EXPRESSIONS[V4_HIDDEN],names);
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
