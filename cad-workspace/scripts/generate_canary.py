#!/usr/bin/env python3
from pathlib import Path
import argparse
import hashlib
import json
import re
import yaml
import cadquery as cq

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonicalize_step(path):
    data=path.read_bytes()
    pattern=rb"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    fixed=b"2000-01-01T00:00:00"
    out,n=re.subn(pattern,fixed,data,count=1)
    if n != 1:
        raise RuntimeError("STEP timestamp header not found")
    path.write_bytes(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--g0", default="data/g0/canary.yaml")
    ap.add_argument("--out", default="exports/canary")
    args=ap.parse_args()
    g0=yaml.safe_load(Path(args.g0).read_text(encoding="utf-8"))
    p=g0["parameters"]
    out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    model=(cq.Workplane("XY").box(p["block_length_mm"], p["block_width_mm"], p["block_height_mm"])
           .faces(">Z").workplane()
           .pushPoints([(-10,-5),(10,-5)]).hole(p["hole_diameter_mm"]))
    step=out/"canary.step"; stl=out/"canary.stl"
    cq.exporters.export(model, str(step), exportType="STEP")
    canonicalize_step(step)
    cq.exporters.export(model, str(stl), exportType="STL")
    manifest={"g0_id":g0["g0_id"],"units":"mm","parameters":p,"artifacts":{"step":{"path":str(step),"sha256":sha(step)},"stl":{"path":str(stl),"sha256":sha(stl)}}}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(f"PASS: generated {step} and {stl}")
    print(json.dumps(manifest,indent=2))

if __name__ == "__main__": main()
