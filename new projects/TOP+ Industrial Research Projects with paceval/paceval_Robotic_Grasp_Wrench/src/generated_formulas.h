// Generated model declarations. Exact expressions registered and evaluated with paceval MCP 4.26.
#pragma once
#include <cstddef>
struct ModelGraph { const char* id; const char* expression; const char* units; };
static const char* contact_variable_list = R"paceval(Fn Ft Fz nx ny R z mu Ncap)paceval";
static const char* aggregate_variable_list = R"paceval(fx1 fy1 fz1 tx1 ty1 tz1 mf1 mn1 mc1 fx2 fy2 fz2 tx2 ty2 tz2 mf2 mn2 mc2 fx3 fy3 fz3 tx3 ty3 tz3 mf3 mn3 mc3 mass g ex ey ez etx ety etz Ftol Ttol Lref wF wT wM)paceval";
static constexpr size_t contact_variable_count = 9;
static constexpr size_t aggregate_variable_count = 41;
static const ModelGraph contact_graphs[] = {
    {R"paceval(fx)paceval", R"paceval((-Fn*nx-Ft*ny))paceval", R"paceval(N)paceval"},
    {R"paceval(fy)paceval", R"paceval((-Fn*ny+Ft*nx))paceval", R"paceval(N)paceval"},
    {R"paceval(fz)paceval", R"paceval(Fz)paceval", R"paceval(N)paceval"},
    {R"paceval(tx)paceval", R"paceval((R*ny*Fz-z*(-Fn*ny+Ft*nx)))paceval", R"paceval(N*m)paceval"},
    {R"paceval(ty)paceval", R"paceval((z*(-Fn*nx-Ft*ny)-R*nx*Fz))paceval", R"paceval(N*m)paceval"},
    {R"paceval(tz)paceval", R"paceval((R*Ft))paceval", R"paceval(N*m)paceval"},
    {R"paceval(friction_margin)paceval", R"paceval((mu*Fn-sqrt(Ft*Ft+Fz*Fz)))paceval", R"paceval(N)paceval"},
    {R"paceval(compression_margin)paceval", R"paceval(Fn)paceval", R"paceval(N)paceval"},
    {R"paceval(capacity_margin)paceval", R"paceval((Ncap-Fn))paceval", R"paceval(N)paceval"},
    {R"paceval(contact_normal_unit_residual)paceval", R"paceval((nx*nx+ny*ny-1))paceval", R"paceval(1)paceval"},
};
static const ModelGraph aggregate_graphs[] = {
    {R"paceval(force_residual_v1)paceval", R"paceval(sqrt(((fx1+fx2+fx3))^2+((fy1+fy2+fy3))^2+((fz1+fz2+fz3-mass*g))^2))paceval", R"paceval(N)paceval"},
    {R"paceval(torque_residual_v1)paceval", R"paceval(sqrt(((tx1+tx2+tx3))^2+((ty1+ty2+ty3))^2+((tz1+tz2+tz3))^2))paceval", R"paceval(N*m)paceval"},
    {R"paceval(force_residual_v2)paceval", R"paceval(sqrt((((fx1+fx2+fx3)+ex))^2+(((fy1+fy2+fy3)+ey))^2+(((fz1+fz2+fz3-mass*g)+ez))^2))paceval", R"paceval(N)paceval"},
    {R"paceval(torque_residual_v2)paceval", R"paceval(sqrt((((tx1+tx2+tx3)+etx))^2+(((ty1+ty2+ty3)+ety))^2+(((tz1+tz2+tz3)+etz))^2))paceval", R"paceval(N*m)paceval"},
    {R"paceval(friction_margin_min)paceval", R"paceval((mf1 min mf2 min mf3))paceval", R"paceval(N)paceval"},
    {R"paceval(normal_margin_min)paceval", R"paceval((mn1 min mn2 min mn3))paceval", R"paceval(N)paceval"},
    {R"paceval(capacity_margin_min)paceval", R"paceval((mc1 min mc2 min mc3))paceval", R"paceval(N)paceval"},
    {R"paceval(force_margin_v1)paceval", R"paceval((Ftol-sqrt(((fx1+fx2+fx3))^2+((fy1+fy2+fy3))^2+((fz1+fz2+fz3-mass*g))^2)))paceval", R"paceval(N)paceval"},
    {R"paceval(force_margin_v2)paceval", R"paceval((Ftol-sqrt((((fx1+fx2+fx3)+ex))^2+(((fy1+fy2+fy3)+ey))^2+(((fz1+fz2+fz3-mass*g)+ez))^2)))paceval", R"paceval(N)paceval"},
    {R"paceval(torque_margin_v1)paceval", R"paceval((Ttol-sqrt(((tx1+tx2+tx3))^2+((ty1+ty2+ty3))^2+((tz1+tz2+tz3))^2)))paceval", R"paceval(N*m)paceval"},
    {R"paceval(torque_margin_v2)paceval", R"paceval((Ttol-sqrt((((tx1+tx2+tx3)+etx))^2+(((ty1+ty2+ty3)+ety))^2+(((tz1+tz2+tz3)+etz))^2)))paceval", R"paceval(N*m)paceval"},
    {R"paceval(friction_violation_squared)paceval", R"paceval(((0 max (-mf1))^2+(0 max (-mf2))^2+(0 max (-mf3))^2))paceval", R"paceval(N^2)paceval"},
    {R"paceval(cost_v1)paceval", R"paceval((wF*(sqrt(((fx1+fx2+fx3))^2+((fy1+fy2+fy3))^2+((fz1+fz2+fz3-mass*g))^2))^2+wT*((sqrt(((tx1+tx2+tx3))^2+((ty1+ty2+ty3))^2+((tz1+tz2+tz3))^2))/Lref)^2+wM*((0 max (-mf1))^2+(0 max (-mf2))^2+(0 max (-mf3))^2)))paceval", R"paceval(N^2)paceval"},
    {R"paceval(cost_v2)paceval", R"paceval((wF*(sqrt((((fx1+fx2+fx3)+ex))^2+(((fy1+fy2+fy3)+ey))^2+(((fz1+fz2+fz3-mass*g)+ez))^2))^2+wT*((sqrt((((tx1+tx2+tx3)+etx))^2+(((ty1+ty2+ty3)+ety))^2+(((tz1+tz2+tz3)+etz))^2))/Lref)^2+wM*((0 max (-mf1))^2+(0 max (-mf2))^2+(0 max (-mf3))^2)))paceval", R"paceval(N^2)paceval"},
    {R"paceval(candidate_guard_v1)paceval", R"paceval((((((sqrt(((fx1+fx2+fx3))^2+((fy1+fy2+fy3))^2+((fz1+fz2+fz3-mass*g))^2))<=Ftol) AND ((sqrt(((tx1+tx2+tx3))^2+((ty1+ty2+ty3))^2+((tz1+tz2+tz3))^2))<=Ttol)) AND ((mf1 min mf2 min mf3)>=0)) AND (((mn1 min mn2 min mn3)>=0) AND ((mc1 min mc2 min mc3)>=0))))paceval", R"paceval(0/1)paceval"},
    {R"paceval(candidate_guard_v2)paceval", R"paceval((((((sqrt((((fx1+fx2+fx3)+ex))^2+(((fy1+fy2+fy3)+ey))^2+(((fz1+fz2+fz3-mass*g)+ez))^2))<=Ftol) AND ((sqrt((((tx1+tx2+tx3)+etx))^2+(((ty1+ty2+ty3)+ety))^2+(((tz1+tz2+tz3)+etz))^2))<=Ttol)) AND ((mf1 min mf2 min mf3)>=0)) AND (((mn1 min mn2 min mn3)>=0) AND ((mc1 min mc2 min mc3)>=0))))paceval", R"paceval(0/1)paceval"},
    {R"paceval(joint_margin_v2)paceval", R"paceval(((((Ftol-sqrt((((fx1+fx2+fx3)+ex))^2+(((fy1+fy2+fy3)+ey))^2+(((fz1+fz2+fz3-mass*g)+ez))^2)) min ((Ttol-sqrt((((tx1+tx2+tx3)+etx))^2+(((ty1+ty2+ty3)+ety))^2+(((tz1+tz2+tz3)+etz))^2))/Lref)) min (mf1 min mf2 min mf3)) min ((mn1 min mn2 min mn3) min (mc1 min mc2 min mc3))))paceval", R"paceval(N)paceval"},
    {R"paceval(external_disturbance_cost_delta)paceval", R"paceval(((wF*(sqrt((((fx1+fx2+fx3)+ex))^2+(((fy1+fy2+fy3)+ey))^2+(((fz1+fz2+fz3-mass*g)+ez))^2))^2+wT*((sqrt((((tx1+tx2+tx3)+etx))^2+(((ty1+ty2+ty3)+ety))^2+(((tz1+tz2+tz3)+etz))^2))/Lref)^2+wM*((0 max (-mf1))^2+(0 max (-mf2))^2+(0 max (-mf3))^2))-(wF*(sqrt(((fx1+fx2+fx3))^2+((fy1+fy2+fy3))^2+((fz1+fz2+fz3-mass*g))^2))^2+wT*((sqrt(((tx1+tx2+tx3))^2+((ty1+ty2+ty3))^2+((tz1+tz2+tz3))^2))/Lref)^2+wM*((0 max (-mf1))^2+(0 max (-mf2))^2+(0 max (-mf3))^2))))paceval", R"paceval(N^2)paceval"},
};
static constexpr size_t contact_graph_count = 10;
static constexpr size_t aggregate_graph_count = 18;
