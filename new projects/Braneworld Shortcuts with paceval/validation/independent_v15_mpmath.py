"""External-only high-precision check. Never linked or imported by C++ programs.
Direct quadratures + receiver root, not v1.5's stable pair kernel.
"""
import json,sys
import mpmath as mp
mp.mp.dps=68
c=mp.mpf('299792.458'); mpc_km=mp.mpf('3.0856775814913673e19')
H0=mp.mpf('67.4'); Om=mp.mpf('.315'); Or=mp.mpf('0.000092'); OL=1-Om-Or

def solve(ell_string, distance='40'):
    ell=mp.mpf(ell_string);D=mp.mpf(distance)/ell
    h0=ell*H0/c
    r0=6*h0*h0/(1+mp.sqrt(1+h0*h0))
    def hub(a):
        r=r0*(Om/a**3+Or/a**4+OL)
        return mp.sqrt((r/6)*(2+r/6))
    def X(ae,a):return mp.quad(lambda u:1/(u*u*hub(u)),[ae,a])
    ae=mp.findroot(lambda a:X(a,1)-D,(mp.mpf('.98'),mp.mpf('1.0')))
    def T(a):return mp.quad(lambda u:mp.sqrt(1+hub(u)**2)/(u*u*hub(u)),[ae,a])
    def Z(a):return 1/ae-1/a
    def dist(a):return mp.sqrt(T(a)**2-Z(a)**2)
    gap=dist(1)-D
    # First-order Taylor root near the brane arrival, and high-precision Newton.
    dB=(T(1)*mp.sqrt(1+hub(1)**2)-Z(1)*hub(1))/(dist(1))
    a_start=1-gap*hub(1)/dB
    ag=mp.findroot(lambda a:dist(a)-D,(a_start,1),solver='secant',verify=True)
    dt_dim=mp.quad(lambda a:1/(a*hub(a)),[ag,1]); seconds=dt_dim*ell*mpc_km/c
    return dict(ell_Mpc=str(ell),emission_scale=str(ae),receiver_scale=str(ag),
                positive_gap=str(gap),seconds=str(seconds),
                null_residual=str(dist(ag)-D),working_precision=mp.mp.dps)

if __name__=='__main__':
    vals=[solve(x) for x in (sys.argv[1:] or ['0.1','0.535'])]
    print(json.dumps(vals,indent=2))
