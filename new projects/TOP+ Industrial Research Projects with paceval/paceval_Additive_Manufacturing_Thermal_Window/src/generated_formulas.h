// Generated from the versioned formula manifest. DO NOT alter by hand.
// Core mathematical expressions are evaluated by original paceval graphs.
#pragma once
#include <array>
struct GraphSpec { const char* id; const char* formula; };
static constexpr std::array<GraphSpec,12> kGraphs{{
  {"temp_surface_v1","(T0+(eta*P/(2*pi*k*sqrt(xs*xs+ys*ys+zs*zs+r0*r0)))*exp((-v*(xs+sqrt(xs*xs+ys*ys+zs*zs+r0*r0))*rho*cp)/(2*k)))"},
  {"temp_depth_v1","(T0+(eta*P/(2*pi*k*sqrt(xd*xd+yd*yd+zd*zd+r0*r0)))*exp((-v*(xd+sqrt(xd*xd+yd*yd+zd*zd+r0*r0))*rho*cp)/(2*k)))"},
  {"temp_surface_v2","(T0+(eta*P/(2*pi*k*sqrt(xs*xs+(ys/beta)*(ys/beta)+(zs/gamma)*(zs/gamma)+r0*r0)))*exp((-v*(xs+sqrt(xs*xs+(ys/beta)*(ys/beta)+(zs/gamma)*(zs/gamma)+r0*r0))*rho*cp)/(2*k)))"},
  {"temp_depth_v2","(T0+(eta*P/(2*pi*k*sqrt(xd*xd+(yd/beta)*(yd/beta)+(zd/gamma)*(zd/gamma)+r0*r0)))*exp((-v*(xd+sqrt(xd*xd+(yd/beta)*(yd/beta)+(zd/gamma)*(zd/gamma)+r0*r0))*rho*cp)/(2*k)))"},
  {"window_margin_v1","(((T0+(eta*P/(2*pi*k*sqrt(xd*xd+yd*yd+zd*zd+r0*r0)))*exp((-v*(xd+sqrt(xd*xd+yd*yd+zd*zd+r0*r0))*rho*cp)/(2*k)))-Tliq) min (Tvap-(T0+(eta*P/(2*pi*k*sqrt(xs*xs+ys*ys+zs*zs+r0*r0)))*exp((-v*(xs+sqrt(xs*xs+ys*ys+zs*zs+r0*r0))*rho*cp)/(2*k)))))"},
  {"window_margin_v2","(((T0+(eta*P/(2*pi*k*sqrt(xd*xd+(yd/beta)*(yd/beta)+(zd/gamma)*(zd/gamma)+r0*r0)))*exp((-v*(xd+sqrt(xd*xd+(yd/beta)*(yd/beta)+(zd/gamma)*(zd/gamma)+r0*r0))*rho*cp)/(2*k)))-Tliq) min (Tvap-(T0+(eta*P/(2*pi*k*sqrt(xs*xs+(ys/beta)*(ys/beta)+(zs/gamma)*(zs/gamma)+r0*r0)))*exp((-v*(xs+sqrt(xs*xs+(ys/beta)*(ys/beta)+(zs/gamma)*(zs/gamma)+r0*r0))*rho*cp)/(2*k)))))"},
  {"window_flag_v1","((((T0+(eta*P/(2*pi*k*sqrt(xd*xd+yd*yd+zd*zd+r0*r0)))*exp((-v*(xd+sqrt(xd*xd+yd*yd+zd*zd+r0*r0))*rho*cp)/(2*k)))-Tliq)>=0) AND ((Tvap-(T0+(eta*P/(2*pi*k*sqrt(xs*xs+ys*ys+zs*zs+r0*r0)))*exp((-v*(xs+sqrt(xs*xs+ys*ys+zs*zs+r0*r0))*rho*cp)/(2*k))))>=0))"},
  {"window_flag_v2","((((T0+(eta*P/(2*pi*k*sqrt(xd*xd+(yd/beta)*(yd/beta)+(zd/gamma)*(zd/gamma)+r0*r0)))*exp((-v*(xd+sqrt(xd*xd+(yd/beta)*(yd/beta)+(zd/gamma)*(zd/gamma)+r0*r0))*rho*cp)/(2*k)))-Tliq)>=0) AND ((Tvap-(T0+(eta*P/(2*pi*k*sqrt(xs*xs+(ys/beta)*(ys/beta)+(zs/gamma)*(zs/gamma)+r0*r0)))*exp((-v*(xs+sqrt(xs*xs+(ys/beta)*(ys/beta)+(zs/gamma)*(zs/gamma)+r0*r0))*rho*cp)/(2*k))))>=0))"},
  {"gradient_power_depth_v1","((eta/(2*pi*k*sqrt(xd*xd+yd*yd+zd*zd+r0*r0)))*exp((-v*(xd+sqrt(xd*xd+yd*yd+zd*zd+r0*r0))*rho*cp)/(2*k)))"},
  {"gradient_speed_surface_v1","(-((eta*P/(2*pi*k*sqrt(xs*xs+ys*ys+zs*zs+r0*r0)))*exp((-v*(xs+sqrt(xs*xs+ys*ys+zs*zs+r0*r0))*rho*cp)/(2*k)))*((xs+sqrt(xs*xs+ys*ys+zs*zs+r0*r0))*rho*cp/(2*k)))"},
  {"delta_depth_v2_v1","((T0+(eta*P/(2*pi*k*sqrt(xd*xd+(yd/beta)*(yd/beta)+(zd/gamma)*(zd/gamma)+r0*r0)))*exp((-v*(xd+sqrt(xd*xd+(yd/beta)*(yd/beta)+(zd/gamma)*(zd/gamma)+r0*r0))*rho*cp)/(2*k)))-(T0+(eta*P/(2*pi*k*sqrt(xd*xd+yd*yd+zd*zd+r0*r0)))*exp((-v*(xd+sqrt(xd*xd+yd*yd+zd*zd+r0*r0))*rho*cp)/(2*k))))"},
  {"thermal_diffusivity","k/(rho*cp)"},
}};
