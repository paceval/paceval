#!/usr/bin/env python3
"""Additional high-precision and convergence checks for braneworld v1.2.

Runs the highlighted case (rho0,w,D)=(10,-0.5,1) using mpmath quadrature
and independent ODE integration in scale factor a. It does NOT validate
observable gravitational-wave propagation, a physical 5th dimension,
or paceval's implementation.
"""
import json
import math
import sys
from pathlib import Path

import mpmath as mp
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference_python"))
from models import hubble


def high_precision_case():
    mp.mp.dps = 65
    rho0, w, D = mp.mpf("10"), mp.mpf("-0.5"), mp.mpf("1")

    def rho(a):
        return rho0 * a ** (-3 * (1 + w))

    def H(a):
        q = rho(a) / 6
        return mp.sqrt(q * (q + 2))

    def T(a):
        return mp.quad(lambda u: (1 + rho(u) / 6) / (u*u*H(u)), [1, a])

    def X(a):
        return mp.quad(lambda u: 1 / (u*u*H(u)), [1, a])

    def tau(a):
        return mp.quad(lambda u: 1 / (u*H(u)), [1, a])

    a_brane = mp.findroot(lambda a: X(a)-D, (15,17), tol=mp.mpf("1e-60"))
    a_bulk = mp.findroot(
        lambda a: T(a)**2-(1-1/a)**2-D*D, (12,13), tol=mp.mpf("1e-60"))
    tau_brane, tau_bulk = tau(a_brane), tau(a_bulk)
    delta = tau_brane-tau_bulk
    result = {k: mp.nstr(v,65) for k,v in {
        "rho0": rho0, "w": w, "D": D, "a_brane": a_brane,
        "a_bulk": a_bulk, "tau_brane": tau_brane, "tau_bulk": tau_bulk,
        "advance": delta, "relative_pct": 100*delta/tau_brane,
        "bulk_T": T(a_bulk), "bulk_z": 1/a_bulk,
    }.items()}
    return result, float(delta)


def independent_ode(rtol, atol, step_cap, reference):
    rho0,w,D=10.,-0.5,1.
    def rhs(a, y):
        rho = rho0*a**(-3*(1+w))
        H = float(hubble(a,rho0,w))
        q = 1+rho/6
        return [q/(a*a*H), 1/(a*a*H), 1/(a*H)]

    sol=solve_ivp(rhs, (1.,20.), [0.,0.,0.], rtol=rtol, atol=atol,
                  dense_output=True, max_step=step_cap)
    if not sol.success:
        raise RuntimeError(sol.message)
    a_brane=brentq(lambda a:sol.sol(a)[1]-D,1+1e-9,20.,xtol=1e-13)
    a_bulk=brentq(lambda a:sol.sol(a)[0]**2-(1-1/a)**2-D*D,
                  1+1e-9,a_brane,xtol=1e-13)
    advance=float(sol.sol(a_brane)[2]-sol.sol(a_bulk)[2])
    return {
      "rtol":rtol,"atol":atol,"max_step_a":step_cap,"nfev":sol.nfev,
      "advance":advance,"abs_error_vs_65digit":abs(advance-reference),
      "a_brane":a_brane,"a_bulk":a_bulk,
    }


def israel_checks():
    checks=[]
    for rho0,w,a in [(0.1,0,1),(1,1/3,1.5),(10,-0.5,10),(10,1,1.3)]:
        rho = rho0*a**(-3*(1+w))
        H = float(hubble(a,rho0,w))
        hdot = -0.5*(1+w)*rho*(1+rho/6)
        kspace=-math.sqrt(1+H*H)
        ktime=kspace-hdot/math.sqrt(1+H*H)
        checks.append({
            "rho0":rho0,"w":w,"a":a,
            "spatial_residual":kspace+(1+rho/6),
            "temporal_residual":ktime-(-1+(2+3*w)*rho/6),
        })
    return checks

if __name__=="__main__":
    high, reference=high_precision_case()
    convergence=[independent_ode(*args,reference) for args in [
        (1e-7,1e-9,.4), (1e-9,1e-11,.15),
        (1e-11,1e-13,.05), (1e-12,1e-14,.025),
    ]]
    israel=israel_checks()
    results={"high_precision":high,"convergence":convergence,
             "israel_eigenvalue_residual_checks":israel}
    print(json.dumps(results,indent=2))
    print("PASS highlighted case: ", high["relative_pct"],"%")
    assert abs(reference-1.0377148766929376)<1e-12
    assert convergence[-1]["abs_error_vs_65digit"]<1e-10
    assert all(abs(v["spatial_residual"])<1e-12 and
               abs(v["temporal_residual"])<1e-12 for v in israel)
    print("PASS high precision, convergence and Israel algebraic controls")
