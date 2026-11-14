// Generated from formula_manifest.json. Source equations are executed by original paceval SDK.
#pragma once
#include <array>
#include <cstddef>
struct GraphFormula { const char* id; const char* expression; };
static constexpr const char* variable_list="Th Tc Ch Cc Uc A Rf Fc D1 D2 Qtarget Rremain H Price Cclean Approach DeltaP DeltaPmax";
static constexpr size_t variable_count=18;
static constexpr std::array<GraphFormula,24> model_graphs {{
 GraphFormula{"Ueff","(1/(1/Uc+Rf))"},
 GraphFormula{"LMTD_direct","((D1-D2)/ln(D1/D2))"},
 GraphFormula{"LMTD_series","((D1+D2)/2*(1-((D1-D2)/(D1+D2))^2/3-4*((D1-D2)/(D1+D2))^4/45-44*((D1-D2)/(D1+D2))^6/945))"},
 GraphFormula{"Q_LMTD_v1","((1/(1/Uc+Rf))*A*Fc*((D1-D2)/ln(D1/D2)))"},
 GraphFormula{"Q_LMTD_series_v1","((1/(1/Uc+Rf))*A*Fc*((D1+D2)/2*(1-((D1-D2)/(D1+D2))^2/3-4*((D1-D2)/(D1+D2))^4/45-44*((D1-D2)/(D1+D2))^6/945)))"},
 GraphFormula{"capacity_ratio","((Ch min Cc)/(Ch max Cc))"},
 GraphFormula{"NTU_v2","((1/(1/Uc+Rf))*A/(Ch min Cc))"},
 GraphFormula{"effectiveness_v2","((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc))))))"},
 GraphFormula{"Q_NTU_v2","((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))"},
 GraphFormula{"Q_clean_option","((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rremain))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rremain))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))"},
 GraphFormula{"hot_out_v2","(Th-((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))/Ch)"},
 GraphFormula{"cold_out_v2","(Tc+((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))/Cc)"},
 GraphFormula{"pinch_min_v2","((Th-(Tc+((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))/Cc)) min ((Th-((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))/Ch)-Tc))"},
 GraphFormula{"duty_margin_v2","(((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))-Qtarget)"},
 GraphFormula{"pinch_margin_v2","(((Th-(Tc+((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))/Cc)) min ((Th-((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))/Ch)-Tc))-Approach)"},
 GraphFormula{"energy_balance_residual_v2","(Ch*(Th-(Th-((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))/Ch))-Cc*((Tc+((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))/Cc)-Tc))"},
 GraphFormula{"wait_cost_score","(Price*H*((Qtarget-((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))) max 0)/1000)"},
 GraphFormula{"clean_cost_score","(Cclean+Price*H*((Qtarget-((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rremain))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rremain))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))) max 0)/1000)"},
 GraphFormula{"cleaning_advantage_score","((Price*H*((Qtarget-((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))) max 0)/1000)-(Cclean+Price*H*((Qtarget-((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rremain))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rremain))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))) max 0)/1000))"},
 GraphFormula{"cleaning_guard","((((Price*H*((Qtarget-((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))) max 0)/1000)-(Cclean+Price*H*((Qtarget-((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rremain))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rremain))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))) max 0)/1000))>0) AND (Rf>Rremain))"},
 GraphFormula{"operation_guard","(((((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))>=Qtarget) AND (((Th-(Tc+((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))/Cc)) min ((Th-((Ch min Cc)*(Th-Tc)*((1-exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))))/Ch)-Tc))>=Approach)) AND (DeltaP<=DeltaPmax))"},
 GraphFormula{"sensitivity_U_Rf","(-1/((1/Uc+Rf)*(1/Uc+Rf)))"},
 GraphFormula{"sensitivity_Q_Rf","(-((Th-Tc)*A*(1-((Ch min Cc)/(Ch max Cc)))*(1-((Ch min Cc)/(Ch max Cc)))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))/((1/Uc+Rf)^2*(1-((Ch min Cc)/(Ch max Cc))*exp(-((1/(1/Uc+Rf))*A/(Ch min Cc))*(1-((Ch min Cc)/(Ch max Cc)))))^2))"},
 GraphFormula{"balanced_effectiveness","(((1/(1/Uc+Rf))*A/(Ch min Cc))/(1+((1/(1/Uc+Rf))*A/(Ch min Cc))))"},
}};
