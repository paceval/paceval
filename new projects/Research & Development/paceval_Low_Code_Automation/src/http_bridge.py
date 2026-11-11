#!/usr/bin/env python3
"""Loopback-only research bridge: HTTP/JSON <-> persistent paceval C++ process.

The bridge intentionally accepts ONLY named, approved model versions. It does
not accept arbitrary mathematical expressions or runtime model registrations.
The underlying .so and paceval_main.cpp perform the actual mathematical work.

This is an offline n8n integration demonstrator, NOT a production API server:
there is no authentication/TLS/tenant isolation, so it binds to 127.0.0.1 only.
If n8n is running in a container, arrange a secure local connection explicitly.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MODELS = {
    ("condition_score", "1.0"): ("uT", "uV", "uI", "b0", "bT", "bV", "bI"),
    ("condition_score", "1.1"): ("uT", "uV", "uI", "b0", "bT", "bV", "bI"),
    ("quotation", "1.0"): ("C", "m", "r", "t", "F"),
    ("calibration", "1.0"): ("T", "a0", "a1", "a2", "b", "h"),
}

class Error(Exception):
    pass

class Engine:
    def __init__(self, exe: str):
        self.process = subprocess.Popen([exe, "--stdio"], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=None,
                                        text=True, bufsize=1)
        self.lock = threading.Lock()
        self.calls = {}  # Per-model successful request count; process lifetime only
        if self.process.poll() is not None:
            raise RuntimeError("C++ engine failed to start")

    def evaluate(self, model: str, version: str, rows: list[list[float]]) -> list[float]:
        key = (model, version)
        if key not in MODELS:
            raise Error("UNKNOWN_MODEL_OR_VERSION")
        if not isinstance(rows, list) or not (1 <= len(rows) <= 512):
            raise Error("BATCH_LIMIT")
        values = []
        for row in rows:
            if not isinstance(row, list) or len(row) != len(MODELS[key]):
                raise Error("WRONG_VARIABLE_COUNT")
            if any(type(x) not in (int, float) or not math.isfinite(x) for x in row):
                raise Error("NONFINITE_OR_INVALID_VALUE")
            values.append(",".join(format(float(x), ".17g") for x in row))
        query = f"EVAL|{model}|{version}|{len(rows)}|{';'.join(values)}\n"
        if len(query) > 100000:
            raise Error("REQUEST_TOO_LARGE")
        with self.lock:
            if self.process.poll() is not None:
                raise Error("ENGINE_NOT_RUNNING")
            assert self.process.stdin and self.process.stdout
            try:
                self.process.stdin.write(query)
                self.process.stdin.flush()
                response = self.process.stdout.readline().strip()
            except (BrokenPipeError, OSError):
                raise Error("ENGINE_COMMUNICATION_FAILURE")
            parts = response.split("|")
            if len(parts) == 2 and parts[0] == "ERR":
                raise Error(parts[1])
            if len(parts) != 4 or parts[0] != "OK" or parts[1:3] != [model, version]:
                raise Error("ENGINE_RESPONSE_ERROR")
            result = [float(v) for v in parts[3].split(",")]
            if len(result) != len(rows) or not all(map(math.isfinite, result)):
                raise Error("ENGINE_RESULT_ERROR")
            reused = self.calls.get(key,0)>0
            self.calls[key] = self.calls.get(key,0)+1
            return result, reused

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


def handler_factory(engine: Engine):
    class Handler(BaseHTTPRequestHandler):
        server_version = "pacevalResearchBridge/1.0"
        def log_message(self, fmt, *args):
            pass  # Inputs are never written into the default HTTP log.
        def send_json(self, status: int, value: dict):
            payload = json.dumps(value, allow_nan=False, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        def do_GET(self):
            if self.path == "/health":
                self.send_json(200, {"status": "ok" if engine.process.poll() is None else "unavailable"})
            elif self.path == "/api/v1/models":
                self.send_json(200, {"models": [
                    {"model": k[0], "version": k[1], "variables": list(v)}
                    for k, v in MODELS.items()]})
            else:
                self.send_json(404, {"error": "NOT_FOUND"})
        def do_POST(self):
            if self.path != "/api/v1/evaluate":
                self.send_json(404, {"error": "NOT_FOUND"}); return
            try:
                ct = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
                if ct != "application/json":
                    raise Error("CONTENT_TYPE")
                n = int(self.headers.get("Content-Length", "-1"))
                if not 1 <= n <= 100000:
                    raise Error("BODY_SIZE_LIMIT")
                obj = json.loads(self.rfile.read(n))
                if not isinstance(obj, dict) or set(obj) != {"model", "version", "rows"}:
                    raise Error("REQUEST_SCHEMA")
                if not isinstance(obj["model"], str) or not isinstance(obj["version"], str):
                    raise Error("REQUEST_SCHEMA")
                results, reused = engine.evaluate(obj["model"], obj["version"], obj["rows"])
                self.send_json(200, {"model": obj["model"], "version": obj["version"],
                                     "results": results, "count": len(results),
                                     "graph_prepared": True, "graph_reused": reused})
            except (Error, ValueError, TypeError, json.JSONDecodeError) as e:
                msg = str(e)
                # Never reflect user-provided content into responses.
                if len(msg) > 100 or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789" for c in msg):
                    msg = "INVALID_REQUEST"
                self.send_json(400, {"error": msg})
            except Exception:
                self.send_json(500, {"error": "INTERNAL_ERROR"})
    return Handler


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--engine", required=True, help="Path to compiled lowcode_math executable")
    p.add_argument("--port", type=int, default=8787)
    args = p.parse_args()
    if not (1 <= args.port <= 65535):
        p.error("invalid port")
    exe = str(Path(args.engine).resolve())
    engine = Engine(exe)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_factory(engine))
    print(f"Research-only HTTP bridge listening on http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever(poll_interval=.1)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        engine.close()

if __name__ == "__main__":
    main()
