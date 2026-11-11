#!/usr/bin/env python3
"""End-to-end HTTP test against the real paceval C++ executable."""
import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

script = Path(__file__).with_name("http_bridge.py")
engine = sys.argv[1] if len(sys.argv)>1 else "./build/lowcode_math"
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
proc = subprocess.Popen([sys.executable,str(script),"--engine",engine,"--port",str(port)],
                        stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
url = f"http://127.0.0.1:{port}"

def request(route, obj=None):
    payload = None if obj is None else json.dumps(obj).encode()
    r = Request(url+route,data=payload,
                headers={"Content-Type":"application/json"} if payload else {})
    try:
        with urlopen(r,timeout=3) as resp:
            return resp.status,json.load(resp)
    except HTTPError as e:
        return e.code,json.load(e)
try:
    for i in range(100):
        try:
            assert request("/health")[1]["status"] == "ok";break
        except (URLError,ConnectionError):
            time.sleep(.05)
    else:
        raise AssertionError("bridge never started")
    status,models = request("/api/v1/models")
    assert status==200 and len(models["models"])==4
    v={"model":"condition_score","version":"1.0",
       "rows":[[0,0,0,0,1,1,1],[0.5,0.1,-0.2,0.0,1,1,1]]}
    status,r=request("/api/v1/evaluate",v)
    assert status==200 and abs(r["results"][0]-.5)<1e-14 and r["graph_prepared"] and not r["graph_reused"]
    status,r2=request("/api/v1/evaluate",v)
    assert status==200 and r2["results"]==r["results"] and r2["graph_reused"], "persistent graph reuse failed"
    status,wrong=request("/api/v1/evaluate",{**v,"version":"9.9"})
    assert status==400 and wrong["error"]=="UNKNOWN_MODEL_OR_VERSION"
    status,wrong=request("/api/v1/evaluate",{**v,"rows":[[2,0,0,0,1,1,1]]})
    assert status==400 and wrong["error"]=="CONDITION_INPUT_RANGE"
    status,wrong=request("/api/v1/evaluate",{**v,"rows":[[float("nan"),0,0,0,1,1,1]]})
    assert status==400 and wrong["error"]=="NONFINITE_OR_INVALID_VALUE"
    status,wrong=request("/api/v1/evaluate",{**v,"rows":[[0,0,0,0,1,1]]})
    assert status==400 and wrong["error"]=="WRONG_VARIABLE_COUNT"
    status,q=request("/api/v1/evaluate",{"model":"quotation","version":"1.0",
                  "rows":[[100,0.1,.05,2,5]]})
    assert status==200 and abs(q["results"][0]-126.275)<1e-10
    status,c=request("/api/v1/evaluate",{"model":"calibration","version":"1.0",
                  "rows":[[20,1,0.01,.0001,.5,10]]})
    assert status==200 and 22<c["results"][0]<23
    status,v2=request("/api/v1/evaluate",{**v,"version":"1.1"})
    assert status==200 and v2["results"][1]!=r["results"][1]
    print("PASS HTTP integration: 4 registered graphs, reuse, 3 domains, versioning, invalid inputs")
finally:
    proc.terminate()
    try:proc.wait(timeout=5)
    except subprocess.TimeoutExpired:proc.kill();proc.wait()
