#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p results validation
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release > validation/cmake_setup.log
cmake --build build -j2 > validation/cmake_build.log
: > validation/wave_iterations.log
for dt in 0.006 0.003 0.0015; do
  ./build/braneworld_v14 --mode static --k 3 --ny 81 --dt "$dt" --tmax 1 \
     --out "results/wave_static_dt${dt}.csv" | tee -a validation/wave_iterations.log
done
for ny in 81 161 321; do
  dt=$(awk -v n="$ny" 'BEGIN {printf "%.12f", 0.20*3/(n-1)}')
  ./build/braneworld_v14 --mode pulse --k 0 --ny "$ny" --dt "$dt" --tmax 1 \
     --out "results/wave_pulse_ny${ny}.csv" | tee -a validation/wave_iterations.log
  ./build/braneworld_v14 --mode moving-constant --k 0 --ny "$ny" --dt "$dt" --tmax 1 \
     --out "results/wave_constant_ny${ny}.csv" | tee -a validation/wave_iterations.log
done
./build/braneworld_v14 --mode pulse --k 2 --ny 161 --dt 0.003 --tmax 1.5 \
    --out results/wave_pulse_k2.csv | tee -a validation/wave_iterations.log
: > validation/cosmo_iterations.log
for n in 100 250 500 1000 2000; do
  ./build/braneworld_v15 --n "$n" --ellmin 0.1 --ellmax 0.535 --count 2 \
     --out "results/cosmo_n${n}.csv" | tee -a validation/cosmo_iterations.log
done
./build/braneworld_v15 --n 400 --ellmin 0.005 --ellmax 0.535 --count 13 \
    --out results/cosmo_scan_13.csv | tee -a validation/cosmo_iterations.log
./build/braneworld_v14 --mode pulse --ny 161 --dt .003 --tmax 1.5 \
    --out results/test_pulse161.csv | tee -a validation/wave_iterations.log
./build/braneworld_v14 --mode pulse --rho0 10 --w -.5 --ny 161 --dt .002 --tmax 1.5 \
    --out results/wave_pulse_high_density.csv | tee -a validation/wave_iterations.log
for n in 31 61; do
  ./build/braneworld_v14_planar --nx "$n" --ny "$n" --dt .004 --tmax 1.7 \
     --out "results/planar_n${n}.csv" | tee -a validation/wave_iterations.log
done
python validation/independent_characteristics.py > validation/planar_characteristic_comparison.json
python validation/independent_v14_scipy.py --ny 161 --tmax 1.5 --rho0 10 --w -0.5 \
  --csv results/wave_pulse_high_density.csv > validation/v14_scipy_highdensity.json
python validation/independent_v15_mpmath.py > validation/v15_highprecision.json
python validation/independent_v14_scipy.py --ny 81 --tmax 1 \
  --csv results/wave_pulse_ny81.csv > validation/v14_scipy81.json
python validation/independent_v14_scipy.py --ny 161 --tmax 1 \
  --csv results/wave_pulse_ny161.csv > validation/v14_scipy161.json
python validation/compare_iterations.py > validation/iteration_summary.json
cat validation/iteration_summary.json
