// Generated formula registry; audited remote MCP expressions (paceval 4.26).
// Local SDK registration is a separate, not-yet-executed reproduction path.
#pragma once
#include <array>
#include <cstddef>
struct GraphFormula { const char* id; const char* expression; };
static constexpr const char* variable_list="NH4 DO Xn muN YN KN KO tau aN bX alphaO2 Vol Temp Tref theta KI KL DOsat Nlimit DOmin Pmax Q Price Hours";
static constexpr size_t variable_count=24;
static constexpr std::array<GraphFormula,23> model_graphs {{
 GraphFormula{"rate_v1","((muN/YN)*Xn*(NH4/(KN+NH4))*(DO/(KO+DO)))"},
 GraphFormula{"rate_v2","((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref))"},
 GraphFormula{"effective_rate_v1","(((muN/YN)*Xn*(NH4/(KN+NH4))*(DO/(KO+DO))) min (NH4/tau))"},
 GraphFormula{"effective_rate_v2","(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))"},
 GraphFormula{"nh4_out_v1","(NH4-(((muN/YN)*Xn*(NH4/(KN+NH4))*(DO/(KO+DO))) min (NH4/tau))*tau)"},
 GraphFormula{"nh4_out_v2","(NH4-(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))*tau)"},
 GraphFormula{"oxygen_demand_v1","(aN*(((muN/YN)*Xn*(NH4/(KN+NH4))*(DO/(KO+DO))) min (NH4/tau))+bX*Xn)"},
 GraphFormula{"oxygen_demand_v2","(aN*(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))+bX*Xn)"},
 GraphFormula{"oxygen_transfer","(KL*(DOsat-DO))"},
 GraphFormula{"oxygen_margin_v1","((KL*(DOsat-DO))-(aN*(((muN/YN)*Xn*(NH4/(KN+NH4))*(DO/(KO+DO))) min (NH4/tau))+bX*Xn))"},
 GraphFormula{"oxygen_margin_v2","((KL*(DOsat-DO))-(aN*(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))+bX*Xn))"},
 GraphFormula{"aeration_power_v1","((aN*(((muN/YN)*Xn*(NH4/(KN+NH4))*(DO/(KO+DO))) min (NH4/tau))+bX*Xn)*Vol/(1000*alphaO2))"},
 GraphFormula{"aeration_power_v2","((aN*(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))+bX*Xn)*Vol/(1000*alphaO2))"},
 GraphFormula{"effluent_margin_v1","(Nlimit-(NH4-(((muN/YN)*Xn*(NH4/(KN+NH4))*(DO/(KO+DO))) min (NH4/tau))*tau))"},
 GraphFormula{"effluent_margin_v2","(Nlimit-(NH4-(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))*tau))"},
 GraphFormula{"mass_balance_residual_v2","(NH4-(NH4-(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))*tau)-(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))*tau)"},
 GraphFormula{"guard_v1","(((((NH4-(((muN/YN)*Xn*(NH4/(KN+NH4))*(DO/(KO+DO))) min (NH4/tau))*tau)<=Nlimit) AND ((KL*(DOsat-DO))>=(aN*(((muN/YN)*Xn*(NH4/(KN+NH4))*(DO/(KO+DO))) min (NH4/tau))+bX*Xn))) AND (DO>=DOmin)) AND (((aN*(((muN/YN)*Xn*(NH4/(KN+NH4))*(DO/(KO+DO))) min (NH4/tau))+bX*Xn)*Vol/(1000*alphaO2))<=Pmax))"},
 GraphFormula{"guard_v2","(((((NH4-(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))*tau)<=Nlimit) AND ((KL*(DOsat-DO))>=(aN*(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))+bX*Xn))) AND (DO>=DOmin)) AND (((aN*(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))+bX*Xn)*Vol/(1000*alphaO2))<=Pmax))"},
 GraphFormula{"power_margin_v2","(Pmax-((aN*(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))+bX*Xn)*Vol/(1000*alphaO2)))"},
 GraphFormula{"relative_oxygen_utilization_v2","((aN*(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))+bX*Xn)/(KL*(DOsat-DO)))"},
 GraphFormula{"rate_sensitivity_do_v2","((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*theta^(Temp-Tref)*KO/((KO+DO)*(KO+DO)))"},
 GraphFormula{"power_delta_v2_v1","(((aN*(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))+bX*Xn)*Vol/(1000*alphaO2))-((aN*(((muN/YN)*Xn*(NH4/(KN+NH4))*(DO/(KO+DO))) min (NH4/tau))+bX*Xn)*Vol/(1000*alphaO2)))"},
 GraphFormula{"energy_cost_v2","(((aN*(((muN/YN)*Xn*(NH4/(KN+NH4+NH4*NH4/KI))*(DO/(KO+DO))*theta^(Temp-Tref)) min (NH4/tau))+bX*Xn)*Vol/(1000*alphaO2))*Hours*Price)"},
}};
