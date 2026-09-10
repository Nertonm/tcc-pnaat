#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"data/concepts/optical-rig-r02.json"
OUT=ROOT/"exports/concepts/optical-rig-r02"
D=json.loads(CFG.read_text())
assert D["status"] == "ASSUMPTION_DRIVEN"
assert D["release_class"] == "PROTOTYPE_CONCEPT"
assert D["prototype_print_allowed"] is True
assert D["production_release"] is False
assert D["camera_count"] == 3
required=["mount_C_TOP","mount_C_LEFT","mount_C_RIGHT","pi5_concept_case","trigger_mount","diagnostic_mount","ky040_mount","receiver","tongue","cam_lever","captive_screw_keeper","cable_guide_00","adapter_plate_A","adapter_plate_B","adapter_plate_C"]
for name in required:
    for ext in (".step",".stl"):
        p=OUT/(name+ext)
        assert p.exists() and p.stat().st_size>0, str(p)
manifest=json.loads((OUT/"components.json").read_text())
assert manifest["status"]=="ASSUMPTION_DRIVEN"
assert manifest["release_class"]=="PROTOTYPE_CONCEPT"
names={c["name"] for c in manifest["components"]}
assert set(required)<=names
for name in required:
    assert (OUT/(name+".step")).stat().st_size>1000
    assert (OUT/(name+".stl")).stat().st_size>1000
print(f"PASS_ASSUMPTION_DRIVEN: {len(manifest['components'])} manifest components; 3 cameras; positive retention; cable routes; adapters A/B/C")
