#!/usr/bin/env python3
"""Convert legitimately obtained real KITTI/SemanticKITTI Velodyne *.bin scans to CSV.

Usage: python convert_kitti_to_csv.py path/to/velodyne/ output.csv
Each scan is float32 [x,y,z,reflectance]; output is frame,x,y,z.
No dataset is downloaded or redistributed by this script.
"""
import argparse
import csv
import struct
from pathlib import Path

def convert(input_dir: Path, output: Path, limit: int):
    files = sorted(input_dir.glob('*.bin'))[:limit]
    if not files:
        raise SystemExit(f'No *.bin scans found in {input_dir}')
    output.parent.mkdir(parents=True, exist_ok=True)
    points = 0
    with output.open('w', newline='', encoding='utf-8') as out:
        writer = csv.writer(out)
        writer.writerow(('frame', 'x', 'y', 'z'))
        for frame, path in enumerate(files):
            if path.stat().st_size % 16:
                raise ValueError(f'Not a Velodyne Nx4 float32 binary file: {path}')
            with path.open('rb') as f:
                while data := f.read(16 * 8192):
                    if len(data) % 16:
                        raise ValueError(f'Incomplete record: {path}')
                    for x, y, z, intensity in struct.iter_unpack('<ffff', data):
                        writer.writerow((frame, format(x, '.9g'), format(y, '.9g'), format(z, '.9g')))
                        points += 1
            print(f'Converted scan {frame}: {path.name}')
    print(f'Wrote {points:,} real sensor points from {len(files)} scans to {output}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_dir', type=Path)
    parser.add_argument('output_csv', type=Path)
    parser.add_argument('--frames', type=int, default=4)
    args = parser.parse_args()
    convert(args.input_dir, args.output_csv, args.frames)
