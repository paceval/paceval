#!/usr/bin/env python3
"""Independent numerical and geometry audit for the offline robotics demo.

No paceval calls. Reconstructs the two-link arm and its simplified planar
obstacle predicates independently from the CSV. Uses 110-decimal-digit mpmath
values to audit pointwise TINC bounds. This is not a collision-safety proof.
"""
import argparse
import csv
import math
from pathlib import Path
from mpmath import mp
mp.dps = 110
L1, L2 = 1.0, 0.78
OBSTACLES = ((0.48, 1.14, 0.13), (1.19, -0.14, 0.15))
PADDING = 0.035
PREVIOUS = (0.35, 1.0)
JOINT_STEP = 0.24

def assert_close(x, y, tag, scale=3e-11):
    assert math.isfinite(float(x)) and math.isfinite(float(y)), tag
    assert abs(float(x)-float(y)) <= scale*(1+max(abs(float(x)), abs(float(y)))), (tag, x, y)

def endpoint(q):
    q1,q2 = q
    return (math.cos(q1)+L2*math.cos(q1+q2),
            math.sin(q1)+L2*math.sin(q1+q2))

def elbow(q):
    return (math.cos(q[0]), math.sin(q[0]))

def point_to_segment_distance2(p, a, b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    w=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)
    clamped=max(0.0,min(1.0,w))
    xx=a[0]+clamped*dx; yy=a[1]+clamped*dy
    return (p[0]-xx)**2+(p[1]-yy)**2

def margins(q):
    e=end=endpoint(q);el=elbow(q)
    result=[]
    for xo,yo,r in OBSTACLES:
        rad2=(r+PADDING)**2
        result.extend([
            point_to_segment_distance2((xo,yo),(0.,0.),el)-rad2,
            point_to_segment_distance2((xo,yo),el,end)-rad2,
            (end[0]-xo)**2+(end[1]-yo)**2-rad2])
    return result

def safe_transition(q0,q1):
    if max(abs(q1[j]-q0[j]) for j in (0,1))>JOINT_STEP+1e-12:
        return False
    for sub in range(13):
        t=sub/12.
        q=(q0[0]+t*(q1[0]-q0[0]),q0[1]+t*(q1[1]-q0[1]))
        if min(margins(q)) < -1e-12: return False
    return True

def cost(q, target, previous):
    x,y=endpoint(q)
    return (x-target[0])**2+(y-target[1])**2+0.17*((q[0]-previous[0])**2+(q[1]-previous[1])**2)

def native_grid(n):
    for i in range(n):
        for j in range(n):
            yield (-0.1+1.8*i/(n-1), -0.2+2.4*j/(n-1))

def audit_trajectory(path, grid):
    previous=PREVIOUS
    count=0
    for row in csv.DictReader(open(path,encoding='utf-8')):
        q=(float(row['q1']),float(row['q2']))
        target=(float(row['target_x']),float(row['target_y']))
        xy=endpoint(q)
        assert_close(xy[0],float(row['endpoint_x']),'endpoint_x')
        assert_close(xy[1],float(row['endpoint_y']),'endpoint_y')
        assert_close(cost(q,target,previous),float(row['cost']),'cost')
        assert_close(min(margins(q)),float(row['min_circle_margin_sq']),'minimum centerline clearance squared')
        assert_close(L1*L2*math.sin(q[1]),float(row['jacobian_determinant']),'jacobian determinant')
        assert safe_transition(previous,q),f'Invalid sampled planar transition at {row["step_id"]}'
        # Independently exhaustive *one-waypoint* search. This is not a
        # globally optimal multi-waypoint planner, and no such claim is made.
        best=min((cost(c,target,previous) for c in native_grid(grid)
                  if safe_transition(previous,c)),default=float('inf'))
        assert_close(float(row['cost']),best,'greedy best-cost reproducibility',2e-10)
        previous=q
        count+=1
    assert count>0
    print(f'PASS {count} trajectory rows: geometry, cost, derivative, and independent grid oracle')
    return count

def exact_from_binary64(text):
    # Convert the decimal CSV to its exact IEEE 754 binary64 value, then to
    # a 110-digit mpf. This matches the inputs actually seen by the C++ runtime.
    return mp.mpf(float(text))

def audit_tinc(path):
    tested=0;contains=0;largest=mp.mpf('0')
    for row in csv.DictReader(open(path,encoding='utf-8')):
        q1=exact_from_binary64(row['q1']);q2=exact_from_binary64(row['q2'])
        l1=exact_from_binary64(row['l1']);l2=exact_from_binary64(row['l2'])
        if row['expression']=='endpoint_x':
            ref=l1*mp.cos(q1)+l2*mp.cos(q1+q2)
        elif row['expression']=='endpoint_y':
            ref=l1*mp.sin(q1)+l2*mp.sin(q1+q2)
        else:raise AssertionError('Unknown TINC expression')
        lo=exact_from_binary64(row['tinc_lower']);hi=exact_from_binary64(row['tinc_upper'])
        y=exact_from_binary64(row['paceval_result'])
        assert lo<=hi
        tested+=1
        contains+=int(lo<=ref<=hi)
        largest=max(largest,abs(ref-y))
    assert tested==24, (tested,'expected 24 distinct pointwise calls')
    print(f'TINC audit at 110 digits: {contains}/{tested} pointwise references enclosed; max result error {float(largest):.4g}')
    # Report any non-inclusions as scientific findings, not as general proof.
    assert contains==tested, f'{tested-contains} pointwise intervals do not enclose the checked exact values'
    return contains

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--trajectory',required=True,type=Path)
    ap.add_argument('--tinc',required=True,type=Path)
    ap.add_argument('--grid',type=int,default=35)
    a=ap.parse_args()
    audit_trajectory(a.trajectory,a.grid)
    audit_tinc(a.tinc)
