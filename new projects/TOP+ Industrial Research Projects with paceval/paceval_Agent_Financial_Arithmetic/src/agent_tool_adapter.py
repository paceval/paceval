#!/usr/bin/env python3
"""Local JSONL-to-persistent-C++ tool adapter (NOT an MCP server or a live LLM).

No subprocess shell, arbitrary formula, filesystem tool, or trading operation is
exposed to untrusted JSON. The 2026 MCP schema references in the README are
architectural context only; this is a separate, locally tested JSONL protocol.
"""
import argparse
import json
import math
import re
import subprocess
from pathlib import Path

MODELS = {"npv6", "future_value", "annuity_pv", "cagr"}
VARIABLES = ("rate", "years", "c0", "c1", "c2", "c3", "c4", "c5", "principal", "final", "payment")
REQUIRED = {"request_id", "model", "version", "currency", "rate_unit", "period", "parameters"}
PARAMS = {
    "npv6": {"rate", "cashflows"},
    "future_value": {"rate", "years", "principal"},
    "annuity_pv": {"rate", "years", "payment"},
    "cagr": {"years", "principal", "final"},
}


def encode(payload):
    if not isinstance(payload, dict) or set(payload) != REQUIRED:
        raise ValueError("missing_or_extra_fields")
    rid = payload["request_id"]
    if not isinstance(rid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", rid):
        raise ValueError("invalid_request_id")
    model = payload["model"]
    if not isinstance(model, str) or model not in MODELS:
        raise ValueError("unknown_model")
    if payload["version"] != "1":
        raise ValueError("unknown_version")
    if payload["currency"] not in ("EUR", "USD"):
        raise ValueError("unsupported_currency")
    if payload["rate_unit"] != "decimal_per_year":
        raise ValueError("ambiguous_rate_unit")
    if payload["period"] != "annual":
        raise ValueError("unsupported_cashflow_frequency")
    parameters = payload["parameters"]
    if not isinstance(parameters, dict) or set(parameters) != PARAMS[model]:
        raise ValueError("missing_or_extra_model_parameters")
    # These defaults belong ONLY to unused slots in the fixed C++ graph ABI;
    # all model-relevant values must be explicitly supplied by the caller.
    values = {"rate": 0.05, "years": 5, "c0": 0, "c1": 0, "c2": 0,
              "c3": 0, "c4": 0, "c5": 0, "principal": 1000, "final": 1100, "payment": 0}
    if model == "npv6":
        cf = parameters["cashflows"]
        if not isinstance(cf, list) or len(cf) != 6:
            raise ValueError("cashflows_require_exactly_six_periods")
        for i, value in enumerate(cf):
            values[f"c{i}"] = value
        values["rate"] = parameters["rate"]
    else:
        values.update(parameters)
    nums = []
    for key in VARIABLES:
        val = values[key]
        if isinstance(val, bool) or not isinstance(val, (float, int)) or not math.isfinite(val):
            raise ValueError("invalid_number_" + key)
        nums.append(format(float(val), ".17g"))
    return "|".join([rid, model, payload["version"], payload["currency"],
                     payload["rate_unit"], payload["period"], *nums])


def run(binary, in_path, out_path):
    # The engine is initialized once in the subprocess and its four graphs stay
    # alive for the entire stream. Each line is a separate structured request.
    with subprocess.Popen([str(binary), "--serve"], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, bufsize=1) as proc:
        with open(in_path, encoding="utf-8") as inp, open(out_path, "w", encoding="utf-8") as out:
            for n, line in enumerate(inp, 1):
                if len(line) > 8192:
                    obj = {"request_id": f"LINE_{n}", "status": "REJECTED", "reason": "line_too_long"}
                else:
                    request_id = f"LINE_{n}"
                    try:
                        data = json.loads(line)
                        if isinstance(data, dict) and isinstance(data.get("request_id"), str):
                            request_id = data["request_id"][:48]
                        encoded = encode(data)
                        proc.stdin.write(encoded + "\n")
                        proc.stdin.flush()
                        response = proc.stdout.readline().rstrip("\n")
                        parts = response.split("|")
                        if len(parts) == 5 and parts[1] == "OK" and parts[0] == request_id:
                            obj = {"request_id": parts[0], "status": "OK", "value": float(parts[2]),
                                   "graph_reused": parts[3] == "true", "formula_version": parts[4],
                                   "unit": ("decimal_annual_return" if data["model"] == "cagr" else data["currency"]), "engine": "paceval"}
                        elif len(parts) == 3 and parts[1] == "REJECTED":
                            obj = {"request_id": request_id, "status": "REJECTED", "reason": parts[2]}
                        else:
                            raise ValueError("invalid_core_response")
                    except (ValueError, TypeError, json.JSONDecodeError) as exc:
                        obj = {"request_id": request_id, "status": "REJECTED", "reason": str(exc)}
                out.write(json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
        proc.stdin.close()
        if proc.wait(timeout=10) != 0:
            raise RuntimeError("persistent core failed: " + proc.stderr.read()[:1000])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binary", required=True, type=Path)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    run(a.binary.resolve(), a.input, a.output)


if __name__ == "__main__":
    main()
