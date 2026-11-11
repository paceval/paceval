#!/usr/bin/env python3
"""Independent 110-decimal-digit numerical and experiment-integrity audit.

Uses mpmath (not paceval) to evaluate every published audit sample, the
selected model's held-out predictions and all TINC sample bounds. It also
checks that the training shortlist and validation selection match the CSVs.

Usage: python3 src/high_precision_reference.py examples/
Exit code is nonzero on any failed *required* numerical or integrity check.
TINC coverage is reported faithfully and can be inspected independently;
finite sample containment must never be interpreted as a universal guarantee.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import mpmath as mp

mp.mp.dps = 110


def rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def expr(family, x, a, b, c, d):
    f = int(family)
    if f == 0:
        return a * mp.sin(b * x) + c * x * x + d
    if f == 1:
        return a * mp.cos(b * x) + c * x * x + d
    if f == 2:
        return a * mp.tanh(b * x) + c * x * x + d
    if f == 3:
        return a * mp.exp(-b * x * x) + c * x * x + d
    if f == 4:
        return a * mp.sin(b * x) + c * x + d
    if f == 5:
        return a * mp.cos(b * x) + c * x + d
    if f == 6:
        return a * mp.sin(b * x) + c * x * x + d * mp.cos(x)
    if f == 7:
        return a * mp.log(1 + b * x * x) + c * x * x + d
    raise ValueError(f"unknown family {f}")


def bfloat(value):
    """Exact binary double that the original C++ engine used."""
    return mp.mpf(float(value))


def close(actual, ref):
    return abs(actual - ref) <= mp.mpf("2e-9") * (1 + abs(ref))


def main(folder):
    summary = json.loads((folder / "validation.json").read_text())
    aud = rows(folder / "audit_samples.csv")
    hypotheses = rows(folder / "hypotheses.csv")
    shortlist = rows(folder / "shortlist.csv")
    data = rows(folder / "dataset.csv")
    selected = rows(folder / "selected_predictions.csv")
    intervals = rows(folder / "tinc_samples.csv")

    assert summary["status"] == "PASS"
    assert len(hypotheses) == summary["candidate_count"]
    assert len(shortlist) == min(100, len(hypotheses))
    assert len(data) == 288 and len(selected) == 288
    assert len(intervals) == 24
    assert not summary["selection_used_test_data"]
    # Audit shortlist construction and training-only rank.
    ranked = sorted(hypotheses, key=lambda r: (float(r["training_mse"]), int(r["candidate_id"])))
    assert [int(r["candidate_id"]) for r in shortlist] == [int(r["candidate_id"]) for r in ranked[:len(shortlist)]]
    winner = min(shortlist, key=lambda r: (float(r["validation_mse"]), int(r["complexity"]), int(r["candidate_id"])))
    assert int(winner["candidate_id"]) == summary["selected_candidate_id"]

    max_err = mp.mpf("0")
    failed = 0
    for r in aud:
        v = expr(r["family"], *[bfloat(r[q]) for q in ("x", "a", "b", "c", "d")])
        observed = bfloat(r["paceval_value"])
        delta = abs(observed - v)
        max_err = max(max_err, delta)
        failed += not close(observed, v)
    assert failed == 0, f"{failed} high-precision hypothesis samples failed"

    # Independently recompute the winner on all four partitions, including
    # held-out and extrapolation, using coefficients read from hypothesis CSV.
    winner_coeffs = hypotheses[summary["selected_candidate_id"]]
    param = [bfloat(winner_coeffs[q]) for q in ("a", "b", "c", "d")]
    fold_errors = {k: [] for k in ("training", "validation", "test", "extrapolation")}
    for r in selected:
        predicted = expr(winner_coeffs["family"], bfloat(r["x"]), *param)
        value = bfloat(r["paceval_prediction"])
        observed = bfloat(r["observed_y"])
        fold_errors[r["partition"]].append((predicted - observed) ** 2)
        delta = abs(predicted - value)
        max_err = max(max_err, delta)
        failed += not close(value, predicted)
    assert failed == 0, f"{failed} high-precision predictions failed"
    for fold, published in (
        ("training", summary["selected_train_mse"]),
        ("validation", summary["selected_validation_mse"]),
        ("test", summary["selected_test_mse"]),
        ("extrapolation", summary["selected_extrapolation_mse"]),
    ):
        estimate = sum(fold_errors[fold]) / len(fold_errors[fold])
        assert abs(estimate - bfloat(published)) <= mp.mpf("2e-9"), f"MSE mismatch {fold}"

    # TINC: report the actual finite-sample inclusion count, including failures.
    contained = 0
    interval_failures = []
    for i, row in enumerate(intervals):
        high_precision = expr(0, *[bfloat(row[q]) for q in ("x", "a", "b", "c", "d")])
        lo = bfloat(row["lower_bound"])
        hi = bfloat(row["upper_bound"])
        nominal = bfloat(row["paceval_value"])
        assert lo <= hi
        assert close(nominal, high_precision)
        if lo <= high_precision <= hi:
            contained += 1
        else:
            interval_failures.append(i)

    report = {
        "status": "PASS",
        "precision_decimal_digits": 110,
        "candidate_count": len(hypotheses),
        "selected_candidate_id": summary["selected_candidate_id"],
        "independent_high_precision_candidate_samples": len(aud),
        "independent_high_precision_selected_predictions": len(selected),
        "max_abs_high_precision_difference": mp.nstr(max_err, 14),
        "high_precision_numeric_tolerance_violations": failed,
        "interval_samples": len(intervals),
        "interval_reference_containment_count": contained,
        "interval_failure_indices": interval_failures,
        "note": "TINC sample observations are not proof of a universal rigorous enclosure."
    }
    (folder / "high_precision_audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("folder", type=Path)
    args = p.parse_args()
    raise SystemExit(main(args.folder))
