#!/usr/bin/env python3
"""Independent Decimal-based reference for the released CSV results.

Uses decimal arithmetic (100 digits), not paceval or C++ native formulas.
The accuracy check pertains to numeric values, not to whether assumptions
are financially appropriate or whether an LLM correctly interpreted intent.
"""
import argparse
import csv
import json
from decimal import Decimal, localcontext
from pathlib import Path


def D(s):
    return Decimal(str(s))


def financial_ref(model, r, years, c, principal, final, payment):
    one = D(1)
    if model == "npv6":
        return sum((c[t] / (one + r) ** t for t in range(6)), D(0))
    if model == "future_value":
        return principal * (years * (one + r).ln()).exp()
    if model == "annuity_pv":
        return payment * (one - (-years * (one + r).ln()).exp()) / r
    if model == "cagr":
        return ((final / principal).ln() / years).exp() - one
    raise ValueError("bad model")


def audit(directory):
    with localcontext() as ctx:
        ctx.prec = 100
        tasks = {}
        with (directory / "requests.csv").open(newline="") as f:
            for row in csv.DictReader(f):
                tasks[row["request_id"]] = row
        errors, count, max_diff = [], 0, 0.0
        with (directory / "sensitivity_results.csv").open(newline="") as f:
            for row in csv.DictReader(f):
                task = tasks[row["request_id"]]
                c = [D(task[f"c{i}"]) for i in range(6)]
                reference = financial_ref(row["model"], D(row["rate"]), D(row["years"]), c,
                                          D(row["principal"]), D(row["final"]), D(row["payment"]))
                discrepancy = abs(D(row["paceval"]) - reference)
                threshold = D("1e-9") * (D(1) + abs(reference))
                count += 1
                max_diff = max(max_diff, float(discrepancy))
                if discrepancy > threshold:
                    errors.append({"case": row["request_id"], "sample": row["sample"],
                                   "absolute_difference": str(discrepancy)})
        update_rows, update_errors = 0, 0
        with (directory / "model_update.csv").open(newline="") as f:
            for row in csv.DictReader(f):
                i = int(row["sample"])
                task = tasks["TASK_1000"]
                c = [D(task[f"c{j}"]) for j in range(6)]
                c[5] *= D("0.98")
                rate = D(task["rate"]) + (D(i) - D("7.5")) / D(1000)
                reference = financial_ref("npv6", rate, D(task["years"]), c,
                                          D(task["principal"]), D(task["final"]), D(task["payment"]))
                update_rows += 1
                if abs(D(row["new_value"]) - reference) > D("1e-9") * (1 + abs(reference)):
                    update_errors += 1
        # TINC reference: use the EXACT binary float value encoded by each
        # 17-digit round-tripping CSV field (not its rounded decimal display).
        # Decimal.from_float returns the precisely represented binary64 value.
        # This matters near degenerate intervals: a text-level audit can hide
        # a one-ULP failure at an input such as rate=0.024.
        def audit_tinc_file(filename):
            totals = {"count": 0, "reformulated_enclosed": 0,
                      "direct_division_enclosed": 0, "failures": [],
                      "direct_fail_indices": []}
            with (directory / filename).open(newline="") as inp:
                for row in csv.DictReader(inp):
                    def exact_binary(field):
                        return Decimal.from_float(float(row[field]))
                    reference = exact_binary("principal") / (Decimal(1) + exact_binary("rate"))
                    lo, hi = exact_binary("raw_lower"), exact_binary("raw_upper")
                    old_lo, old_hi = exact_binary("baseline_lower"), exact_binary("baseline_upper")
                    totals["count"] += 1
                    if lo <= reference <= hi:
                        totals["reformulated_enclosed"] += 1
                    else:
                        totals["failures"].append({"sample": int(row["sample"]),
                                                   "reference": str(reference),
                                                   "lower": str(lo), "upper": str(hi)})
                    if old_lo <= reference <= old_hi:
                        totals["direct_division_enclosed"] += 1
                    else:
                        totals["direct_fail_indices"].append(int(row["sample"]))
            return totals

        fixed_tinc = audit_tinc_file("tinc_samples.csv")
        broad_tinc = audit_tinc_file("tinc_stress_samples.csv")
        summary = {"decimal_precision": 100, "audited_values": count, "failures": len(errors),
                   "max_absolute_difference": max_diff, "formula_update_cases": update_rows,
                   "formula_update_failures": update_errors,
                   "tinc_formula": "principal*exp(-ln(1+rate))",
                   "tinc_exact_reference": "exact IEEE-754 binary64 input values, evaluated in Decimal(100)",
                   "fixed_tinc": fixed_tinc, "stress_tinc": broad_tinc,
                   "tinc_sample_count": fixed_tinc["count"],
                   "raw_tinc_inclusions": fixed_tinc["reformulated_enclosed"],
                   "tinc_scope": "observed inclusion for the specified samples only; not a general proof",
                   "fail_examples": errors[:8]}
        (directory / "high_precision_audit.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
        if (errors or update_errors or fixed_tinc["count"] != 24 or broad_tinc["count"] != 1500
                or fixed_tinc["failures"] or broad_tinc["failures"]):
            raise SystemExit(1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("directory", type=Path)
    audit(p.parse_args().directory)


if __name__ == "__main__":
    main()
