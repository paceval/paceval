#!/usr/bin/env python3
"""Regenerate strict JSONL calls from the included, deterministic research CSV."""
import csv
import json
from pathlib import Path


def make(folder):
    with (folder / "requests.csv").open(newline="") as f:
        all_rows = list(csv.DictReader(f))
    calls = []
    for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11):
        q = all_rows[i]
        model = q["model"]
        if model == "npv6":
            parameters = {"rate": float(q["rate"]),
                          "cashflows": [float(q[f"c{k}"]) for k in range(6)]}
        elif model == "future_value":
            parameters = {"rate": float(q["rate"]), "years": int(float(q["years"])),
                          "principal": float(q["principal"])}
        elif model == "annuity_pv":
            parameters = {"rate": float(q["rate"]), "years": int(float(q["years"])),
                          "payment": float(q["payment"])}
        else:
            parameters = {"years": int(float(q["years"])), "principal": float(q["principal"]),
                          "final": float(q["final"])}
        calls.append({**{k: q[k] for k in ("request_id", "model", "version", "currency", "rate_unit", "period")},
                      "parameters": parameters})
    altered = [dict(calls[i]) for i in range(4)]
    altered[0]["request_id"] = "JSON_BAD_UNIT"
    altered[0]["rate_unit"] = "percent"
    altered[1]["request_id"] = "JSON_UNAPPROVED_MODEL"
    altered[1]["model"] = "arbitrary_formula"
    altered[2]["request_id"] = "JSON_UNSUPPORTED_VERSION"
    altered[2]["version"] = "2"
    altered[3]["request_id"] = "JSON_AMBIGUOUS"
    del altered[3]["period"]
    calls.extend(altered)
    (folder / "agent_calls.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in calls))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("directory", type=Path)
    make(p.parse_args().directory)
