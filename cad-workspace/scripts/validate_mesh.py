#!/usr/bin/env python3
from pathlib import Path
import sys
import numpy as np
import trimesh

def main():
    path=Path(sys.argv[1] if len(sys.argv)>1 else "exports/canary/canary.stl")
    if not path.is_file():
        print(f"FAIL: missing mesh {path}")
        raise SystemExit(1)
    mesh=trimesh.load_mesh(path, process=True, validate=True)
    if not isinstance(mesh, trimesh.Trimesh):
        print("FAIL: not a single triangular mesh")
        raise SystemExit(1)
    checks={
        "watertight": bool(mesh.is_watertight),
        "volume": bool(mesh.is_volume),
        "finite": bool(np.isfinite(mesh.vertices).all() and np.isfinite(mesh.faces).all()),
        "faces": len(mesh.faces)>0,
    }
    print({"processing":"trimesh.process(validate=True)", **checks})
    if not all(checks.values()):
        print("FAIL: mesh validation")
        raise SystemExit(1)
    print(f"PASS: mesh {path} bounds={mesh.bounds.tolist()} volume={mesh.volume}")

if __name__ == "__main__":
    main()
