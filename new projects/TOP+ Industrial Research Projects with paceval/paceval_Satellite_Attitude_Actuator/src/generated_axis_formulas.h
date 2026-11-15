// Research graph manifest, actual remote paceval MCP 4.26 successful registration.
#pragma once
#include <cstddef>
static const char* sat_axis_variable_list = R"pv(I Ij Ik w wj wk h hj hk tau ext dt taumax hmax wlimit Jw wF wH wA targetAcc)pv";
static constexpr size_t sat_axis_variable_count = 20;
static const ModelGraph sat_axis_graphs[] = {
    {R"pv(wheel_inertial_coupling)pv", R"pv(((Ik-Ij)*wj*wk))pv", R"pv(N m)pv"},
    {R"pv(wheel_gyro_coupling)pv", R"pv((wj*hk-wk*hj))pv", R"pv(N m)pv"},
    {R"pv(acceleration_v1)pv", R"pv(((tau+ext-((Ik-Ij)*wj*wk))/I))pv", R"pv(rad/s^2)pv"},
    {R"pv(acceleration_v2)pv", R"pv(((tau+ext-((Ik-Ij)*wj*wk)-(wj*hk-wk*hj))/I))pv", R"pv(rad/s^2)pv"},
    {R"pv(rate_next_v1)pv", R"pv((w+dt*((tau+ext-((Ik-Ij)*wj*wk))/I)))pv", R"pv(rad/s)pv"},
    {R"pv(rate_next_v2)pv", R"pv((w+dt*((tau+ext-((Ik-Ij)*wj*wk)-(wj*hk-wk*hj))/I)))pv", R"pv(rad/s)pv"},
    {R"pv(wheel_h_next)pv", R"pv((h-tau*dt))pv", R"pv(N m s)pv"},
    {R"pv(torque_margin)pv", R"pv((taumax-abs(tau)))pv", R"pv(N m)pv"},
    {R"pv(momentum_margin)pv", R"pv((hmax-abs((h-tau*dt))))pv", R"pv(N m s)pv"},
    {R"pv(rate_margin_v1)pv", R"pv((wlimit-abs((w+dt*((tau+ext-((Ik-Ij)*wj*wk))/I)))))pv", R"pv(rad/s)pv"},
    {R"pv(rate_margin_v2)pv", R"pv((wlimit-abs((w+dt*((tau+ext-((Ik-Ij)*wj*wk)-(wj*hk-wk*hj))/I)))))pv", R"pv(rad/s)pv"},
    {R"pv(candidate_guard_v1)pv", R"pv(((((taumax-abs(tau))>=0) AND ((hmax-abs((h-tau*dt)))>=0)) AND ((wlimit-abs((w+dt*((tau+ext-((Ik-Ij)*wj*wk))/I))))>=0)))pv", R"pv(0/1)pv"},
    {R"pv(candidate_guard_v2)pv", R"pv(((((taumax-abs(tau))>=0) AND ((hmax-abs((h-tau*dt)))>=0)) AND ((wlimit-abs((w+dt*((tau+ext-((Ik-Ij)*wj*wk)-(wj*hk-wk*hj))/I))))>=0)))pv", R"pv(0/1)pv"},
    {R"pv(normalized_score_v1)pv", R"pv(((((taumax-abs(tau))/taumax) min ((hmax-abs((h-tau*dt)))/hmax)) min ((wlimit-abs((w+dt*((tau+ext-((Ik-Ij)*wj*wk))/I))))/wlimit)))pv", R"pv(dimensionless)pv"},
    {R"pv(normalized_score_v2)pv", R"pv(((((taumax-abs(tau))/taumax) min ((hmax-abs((h-tau*dt)))/hmax)) min ((wlimit-abs((w+dt*((tau+ext-((Ik-Ij)*wj*wk)-(wj*hk-wk*hj))/I))))/wlimit)))pv", R"pv(dimensionless)pv"},
    {R"pv(cost_v1)pv", R"pv((wF*(tau/taumax)^2+wH*((h-tau*dt)/hmax)^2+wA*((((tau+ext-((Ik-Ij)*wj*wk))/I)-targetAcc)*dt/wlimit)^2))pv", R"pv(dimensionless)pv"},
    {R"pv(cost_v2)pv", R"pv((wF*(tau/taumax)^2+wH*((h-tau*dt)/hmax)^2+wA*((((tau+ext-((Ik-Ij)*wj*wk)-(wj*hk-wk*hj))/I)-targetAcc)*dt/wlimit)^2))pv", R"pv(dimensionless)pv"},
    {R"pv(sensitivity_accel_to_torque)pv", R"pv((1/I))pv", R"pv(1/(kg m^2))pv"},
    {R"pv(sensitivity_momentum_to_torque)pv", R"pv((-dt))pv", R"pv(s)pv"},
    {R"pv(acceleration_version_delta)pv", R"pv((((tau+ext-((Ik-Ij)*wj*wk)-(wj*hk-wk*hj))/I)-((tau+ext-((Ik-Ij)*wj*wk))/I)))pv", R"pv(rad/s^2)pv"},
    {R"pv(angular_momentum_balance_residual_v2)pv", R"pv((I*((tau+ext-((Ik-Ij)*wj*wk)-(wj*hk-wk*hj))/I)-tau-ext+((Ik-Ij)*wj*wk)+(wj*hk-wk*hj)))pv", R"pv(N m)pv"},
    {R"pv(wheel_spin_rate)pv", R"pv((h/Jw))pv", R"pv(rad/s)pv"},
    {R"pv(wheel_mechanical_power_proxy)pv", R"pv(abs(tau*h/Jw))pv", R"pv(W)pv"},
    {R"pv(body_and_wheel_momentum)pv", R"pv((I*w+h))pv", R"pv(N m s)pv"},
    {R"pv(torque_utilization)pv", R"pv((abs(tau)/taumax))pv", R"pv(dimensionless)pv"},
    {R"pv(momentum_utilization)pv", R"pv((abs((h-tau*dt))/hmax))pv", R"pv(dimensionless)pv"},
    {R"pv(gyro_to_torque_ratio)pv", R"pv((abs((wj*hk-wk*hj))/taumax))pv", R"pv(dimensionless)pv"},
    {R"pv(sensitivity_acceleration_to_hj)pv", R"pv((wk/I))pv", R"pv(1/s/(kg m^2))pv"},
    {R"pv(sensitivity_acceleration_to_hk)pv", R"pv((-wj/I))pv", R"pv(1/s/(kg m^2))pv"},
    {R"pv(score_delta_v2_v1)pv", R"pv((((((taumax-abs(tau))/taumax) min ((hmax-abs((h-tau*dt)))/hmax)) min ((wlimit-abs((w+dt*((tau+ext-((Ik-Ij)*wj*wk)-(wj*hk-wk*hj))/I))))/wlimit))-((((taumax-abs(tau))/taumax) min ((hmax-abs((h-tau*dt)))/hmax)) min ((wlimit-abs((w+dt*((tau+ext-((Ik-Ij)*wj*wk))/I))))/wlimit))))pv", R"pv(dimensionless)pv"},
};
static constexpr size_t sat_axis_graph_count = sizeof(sat_axis_graphs)/sizeof(sat_axis_graphs[0]);
