// Generated from the formulas actually registered with paceval MCP 4.26.
#pragma once
#include <cstddef>
struct ModelGraph { const char* id; const char* expression; const char* units; };
static const char* furnace_variable_list = R"pv(mf LHV eta mp cp Tin Tout beta U A Tw Tamb eps sigma mex cpe Tex rec efco2 cNOx qflue capco2 capnox fuelcap Tmax)pv";
static constexpr std::size_t furnace_variable_count = 25;
static const ModelGraph furnace_graphs[] = {
    {R"pv(fuel_heat)pv", R"pv(mf*LHV*eta)pv", R"pv(W)pv"},
    {R"pv(product_heat_v1)pv", R"pv(mp*cp*(Tout-Tin))pv", R"pv(W)pv"},
    {R"pv(product_heat_v2)pv", R"pv(mp*cp*((Tout-Tin)+beta*(Tout-Tin)^2/2))pv", R"pv(W)pv"},
    {R"pv(wall_convection)pv", R"pv(U*A*(Tw-Tamb))pv", R"pv(W)pv"},
    {R"pv(wall_radiation)pv", R"pv(eps*sigma*A*(Tw^4-Tamb^4))pv", R"pv(W)pv"},
    {R"pv(exhaust_heat_gross)pv", R"pv(mex*cpe*(Tex-Tamb))pv", R"pv(W)pv"},
    {R"pv(recovered_heat)pv", R"pv(rec*mex*cpe*(Tex-Tamb))pv", R"pv(W)pv"},
    {R"pv(exhaust_heat_net)pv", R"pv((1-rec)*mex*cpe*(Tex-Tamb))pv", R"pv(W)pv"},
    {R"pv(heat_demand_v1)pv", R"pv(((mp*cp*(Tout-Tin))+(U*A*(Tw-Tamb))+(eps*sigma*A*(Tw^4-Tamb^4))+(mex*cpe*(Tex-Tamb))))pv", R"pv(W)pv"},
    {R"pv(heat_demand_v2)pv", R"pv(((mp*cp*((Tout-Tin)+beta*(Tout-Tin)^2/2))+(U*A*(Tw-Tamb))+(eps*sigma*A*(Tw^4-Tamb^4))+((1-rec)*(mex*cpe*(Tex-Tamb)))))pv", R"pv(W)pv"},
    {R"pv(balance_margin_v1)pv", R"pv(((mf*LHV*eta)-((mp*cp*(Tout-Tin))+(U*A*(Tw-Tamb))+(eps*sigma*A*(Tw^4-Tamb^4))+(mex*cpe*(Tex-Tamb)))))pv", R"pv(W)pv"},
    {R"pv(balance_margin_v2)pv", R"pv(((mf*LHV*eta)-((mp*cp*((Tout-Tin)+beta*(Tout-Tin)^2/2))+(U*A*(Tw-Tamb))+(eps*sigma*A*(Tw^4-Tamb^4))+((1-rec)*(mex*cpe*(Tex-Tamb))))))pv", R"pv(W)pv"},
    {R"pv(fuel_required_v2)pv", R"pv((((mp*cp*((Tout-Tin)+beta*(Tout-Tin)^2/2))+(U*A*(Tw-Tamb))+(eps*sigma*A*(Tw^4-Tamb^4))+((1-rec)*(mex*cpe*(Tex-Tamb))))/(LHV*eta)))pv", R"pv(kg/s)pv"},
    {R"pv(thermal_efficiency_v2)pv", R"pv(((mp*cp*((Tout-Tin)+beta*(Tout-Tin)^2/2))/(mf*LHV)))pv", R"pv(fraction)pv"},
    {R"pv(balance_delta_v2_v1)pv", R"pv((((mf*LHV*eta)-((mp*cp*((Tout-Tin)+beta*(Tout-Tin)^2/2))+(U*A*(Tw-Tamb))+(eps*sigma*A*(Tw^4-Tamb^4))+((1-rec)*(mex*cpe*(Tex-Tamb)))))-((mf*LHV*eta)-((mp*cp*(Tout-Tin))+(U*A*(Tw-Tamb))+(eps*sigma*A*(Tw^4-Tamb^4))+(mex*cpe*(Tex-Tamb))))))pv", R"pv(W)pv"},
    {R"pv(emission_CO2_rate)pv", R"pv(mf*efco2)pv", R"pv(kg/s)pv"},
    {R"pv(emission_NOx_measured_rate)pv", R"pv((cNOx*qflue*0.000001))pv", R"pv(kg/s)pv"},
    {R"pv(CO2_margin)pv", R"pv((capco2-(mf*efco2)))pv", R"pv(kg/s)pv"},
    {R"pv(NOx_margin)pv", R"pv((capnox-(cNOx*qflue*0.000001)))pv", R"pv(kg/s)pv"},
    {R"pv(fuel_margin)pv", R"pv((fuelcap-mf))pv", R"pv(kg/s)pv"},
    {R"pv(temperature_margin)pv", R"pv((Tmax-Tout))pv", R"pv(K)pv"},
    {R"pv(constraint_guard_v1)pv", R"pv((((((((mf*LHV*eta)-((mp*cp*(Tout-Tin))+(U*A*(Tw-Tamb))+(eps*sigma*A*(Tw^4-Tamb^4))+(mex*cpe*(Tex-Tamb))))>=0) AND ((capco2-(mf*efco2))>=0)) AND ((capnox-(cNOx*qflue*0.000001))>=0)) AND ((fuelcap-mf)>=0)) AND ((Tmax-Tout)>=0)))pv", R"pv(0/1)pv"},
    {R"pv(constraint_guard_v2)pv", R"pv((((((((mf*LHV*eta)-((mp*cp*((Tout-Tin)+beta*(Tout-Tin)^2/2))+(U*A*(Tw-Tamb))+(eps*sigma*A*(Tw^4-Tamb^4))+((1-rec)*(mex*cpe*(Tex-Tamb)))))>=0) AND ((capco2-(mf*efco2))>=0)) AND ((capnox-(cNOx*qflue*0.000001))>=0)) AND ((fuelcap-mf)>=0)) AND ((Tmax-Tout)>=0)))pv", R"pv(0/1)pv"},
    {R"pv(score_v2)pv", R"pv((((((((mf*LHV*eta)-((mp*cp*((Tout-Tin)+beta*(Tout-Tin)^2/2))+(U*A*(Tw-Tamb))+(eps*sigma*A*(Tw^4-Tamb^4))+((1-rec)*(mex*cpe*(Tex-Tamb)))))/(mf*LHV*eta)) min ((capco2-(mf*efco2))/capco2)) min ((capnox-(cNOx*qflue*0.000001))/capnox)) min ((fuelcap-mf)/fuelcap)) min ((Tmax-Tout)/Tmax)))pv", R"pv(dimensionless)pv"},
    {R"pv(sensitivity_balance_to_fuel)pv", R"pv((LHV*eta))pv", R"pv(J/kg)pv"},
    {R"pv(sensitivity_balance_to_recovery)pv", R"pv((mex*cpe*(Tex-Tamb)))pv", R"pv(W)pv"},
    {R"pv(sensitivity_radiation_to_wall_temp)pv", R"pv((4*eps*sigma*A*Tw^3))pv", R"pv(W/K)pv"},
    {R"pv(sensitivity_product_heat_to_outlet)pv", R"pv((mp*cp*(1+beta*(Tout-Tin))))pv", R"pv(W/K)pv"},
    {R"pv(sensitivity_fuel_required_to_recovery)pv", R"pv((-(mex*cpe*(Tex-Tamb))/(LHV*eta)))pv", R"pv(kg/s)pv"},
    {R"pv(CO2_intensity_per_GJ_useful)pv", R"pv((mf*efco2*1000000000/(mp*cp*((Tout-Tin)+beta*(Tout-Tin)^2/2))))pv", R"pv(kg/GJ)pv"},
    {R"pv(recovery_fraction_of_gross_exhaust)pv", R"pv((((1-rec)*(mex*cpe*(Tex-Tamb)))/(mex*cpe*(Tex-Tamb))))pv", R"pv(fraction)pv"},
    {R"pv(emission_and_energy_joint_margin)pv", R"pv(((((mf*LHV*eta)-((mp*cp*((Tout-Tin)+beta*(Tout-Tin)^2/2))+(U*A*(Tw-Tamb))+(eps*sigma*A*(Tw^4-Tamb^4))+((1-rec)*(mex*cpe*(Tex-Tamb)))))/(mf*LHV*eta)) min ((capco2-mf*efco2)/capco2) min ((capnox-cNOx*qflue*0.000001)/capnox)))pv", R"pv(dimensionless)pv"},
};
static constexpr std::size_t furnace_graph_count = sizeof(furnace_graphs)/sizeof(furnace_graphs[0]);
