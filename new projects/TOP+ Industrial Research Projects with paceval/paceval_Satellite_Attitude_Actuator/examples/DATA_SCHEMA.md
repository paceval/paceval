# Input schema, units and declared physical domains

The `axis_snapshots.csv` file stores one row per axis, **147 rows** in consecutive x/y/z triplets for **49** synthetic candidates. All values are explicit decimal literals (not formulas). Source order: `case_id,axis,I,Ij,Ik,w,wj,wk,h,hj,hk,tau,ext,dt,taumax,hmax,wlimit,Jw,wF,wH,wA,targetAcc`.

| Column | Units | Interpretation |
|---|---|---|
| I, Ij, Ik | kg m² | Diagonal body inertia about current and cyclic transverse axes; all strictly positive |
| w, wj, wk | rad/s | Current body angular rates (cyclic coordinates) |
| h, hj, hk | N m s | Signed current reaction-wheel axial momenta |
| tau | N m | Commanded torque acting on the **body**; wheel torque has opposite sign |
| ext | N m | External torque acting on spacecraft body |
| dt | s | Positive one-step prediction duration |
| taumax | N m | Positive magnitude limit on commanded body torque |
| hmax | N m s | Positive maximum wheel momentum magnitude |
| wlimit | rad/s | Positive limit on the predicted body angular-rate magnitude |
| Jw | kg m² | Positive reaction-wheel axial moment of inertia |
| wF, wH, wA | dimensionless | Nonnegative user-selected illustrative cost weights |
| targetAcc | rad/s² | Target acceleration in the illustrative cost graph |

The x-axis inputs use `(I,Ij,Ik)=(Ix,Iy,Iz)`, y-axis `(Iy,Iz,Ix)` and z-axis `(Iz,Ix,Iy)`. For a general non-orthogonal wheel array this mapping is invalid and a separate allocation matrix is necessary.

The `quaternion_snapshots.csv` file supplies `case_id,q0,q1,q2,q3,wx,wy,wz,dt`, where q is a scalar-first unit quaternion, angular velocity is in rad/s, and dt is in seconds. The orientation model uses a Hamilton body-to-inertial convention and a normalized first-order update. No physical flight timestamps, accelerometer measurements or ground-truth attitude observations are included.

The aggregate stage uses 18 scalar values transferred from the **paceval-computed axis graph outputs** in this order: x/y/z torque margins, x/y/z wheel momentum margins, x/y/z rate margins v1, x/y/z rate margins v2, x/y/z normalized scores v1, x/y/z normalized scores v2. The project records the exact aggregate mathematical graphs in its manifest.

The initial x-wheel momentum values of the grid are 0.015, 0.019, 0.023, 0.027, 0.031, 0.035 and 0.039 N m s. The x-body torque values are −0.0009, −0.0006, −0.0003, 0, +0.0003, +0.0006 and +0.0009 N m. The grid is deterministic, with no hidden random seed. Other axis values are recorded directly in the CSV. Every scenario is synthetic, not an operational spacecraft state.
