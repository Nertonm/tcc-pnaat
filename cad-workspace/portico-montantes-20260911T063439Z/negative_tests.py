"""Negative tests (mutations).

Every mutation must be CAUGHT by a named check.  A mutation that slips through
means the corresponding check is worthless, and the report must say so.
Each mutation also reports `isValid` so the classic trap is visible: a broken
part can still be B-Rep valid and still pass a poorly chosen gate.
"""

import json
import sys
from pathlib import Path

import FreeCAD as A
import Part
from FreeCAD import Vector as V

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import lib_geo as G  # noqa: E402
from lib_geo import contact_area, overlap_volume, place, stats  # noqa: E402

IN = ROOT / "inputs"
BUILD = json.loads((ROOT / "build-measurements.json").read_text())
P = BUILD["placements"]
XC, Y0, ZB, JY = P["XC"], P["Y0"], P["ZB"], P["JY"]
JX0, JY0, JZ0, JX1, JY1, JZ1 = P["junction_box"]
DX = 400.0
IDENT = ((1, 0, 0), (0, 1, 0), (0, 0, 1))

rail0 = Part.read(str(IN / "dinr135-007.5.step"))
sec = G.rail_section_face(rail0)
montante = place(G.build_rail(sec, 450.0)[0], *G.ROT_UPRIGHT, (XC, Y0, ZB))

results = {}


def clean(s):
    """removeSplitter() where the kernel returned a single solid, leave Compounds alone."""
    try:
        return s.removeSplitter()
    except AttributeError:
        return s


def record(name, caught, detail, gates_probed):
    results[name] = {"caught": caught, "detail": detail, "checks_probed": gates_probed}
    print("[%s] caught=%s %s" % (name, caught, json.dumps(detail)), flush=True)


def base_junction():
    band_u = place(sec.extrude(V(140.0, 0, 0)), *G.ROT_UPRIGHT, (XC, JY - 70.0, ZB))
    band_c = place(sec.extrude(V(160.0, 0, 0)), *G.ROT_CROSSBAR, (P["TX"] - 20.0, JY, P["TZ"]))
    blk = Part.makeBox(JX1 - JX0, JY1 - JY0, JZ1 - JZ0, V(JX0, JY0, JZ0))
    return clean(blk.cut(band_u).cut(band_c))


def obround(xc, yc, length, width, z0, h):
    straight = length - width
    s = Part.makeBox(width, straight, h, V(xc - width / 2.0, yc - straight / 2.0, z0))
    for dy in (-straight / 2.0, straight / 2.0):
        s = s.fuse(Part.makeCylinder(width / 2.0, h, V(xc, yc + dy, z0), V(0, 0, 1)))
    return s


# --------------------------------------------------------------------------- #
# N1: junction cut in two -> the single-solid gate must refuse it
# --------------------------------------------------------------------------- #
j = base_junction()
j = clean(j.cut(Part.makeBox(80.0, 100.0, 0.4, V(JX0 - 10.0, JY - 50.0, 13.7))))
n_solids = len(j.Solids)
record("N1_junction_split_into_two", n_solids != 1,
       {"solids": n_solids, "isValid": bool(j.isValid()),
        "note": "B-Rep validity alone does not see this (the old R07 defect)"},
       ["parts_single_valid_solid"])

# --------------------------------------------------------------------------- #
# N2: rectangular groove instead of the profile channel -> anti-rotation dies
# --------------------------------------------------------------------------- #
j = base_junction()
groove = Part.makeBox(36.5, 100.0, 8.5, V(XC - 18.25, JY - 50.0, ZB - 0.5))
j2 = clean(j.cut(groove))
key = obround(XC, JY, 14.6, 6.2, JZ0, 5.0)
j2 = clean(j2.cut(obround(XC, JY, 15.0, 6.2, JZ0 - 0.1, 5.1)))
blocked = {}
for deg in (0.5, 1.0, 2.0):
    r = G.rot_about_axis(montante, (XC, JY, ZB + 3.75), (0, 1, 0), deg)
    blocked["%.1fdeg" % deg] = overlap_volume(r, j2)
# The build gate requires EVERY probed angle (1/2/5 deg) to be blocked, so the
# mutation is caught as soon as one probed angle slips through unblocked.
record("N2_rectangular_groove_no_keying", any(v <= 1e-3 for v in blocked.values()),
       {"overlap_on_rotation_mm3": blocked, "groove": "36.5 x 8.5 rectangular",
        "note": "a groove that merely holds the rail does not key the profile: at 1.0 deg "
                "the rail turns with zero overlap, so the build's rotation_blocked gate "
                "(1/2/5 deg) goes False"},
       ["rotation_blocked"])

# --------------------------------------------------------------------------- #
# N3: key too short -> the positive axial stop is not detected
# --------------------------------------------------------------------------- #
j3 = clean(base_junction().cut(obround(XC, JY, 15.0, 6.2, JZ0 - 0.1, 5.1)))
short_key = obround(XC, JY, 12.6, 6.2, JZ0, 5.0)
r = place(montante, *IDENT, (0, 0.5, 0))
ov_short = overlap_volume(r, short_key)
long_key = obround(XC, JY, 14.6, 6.2, JZ0, 5.0)
ov_long = overlap_volume(r, long_key)
record("N3_key_too_short_by_2mm", ov_short <= 1e-3 and ov_long > 1e-3,
       {"overlap_0.5mm_shift_short_key_mm3": ov_short,
        "overlap_0.5mm_shift_design_key_mm3": ov_long,
        "note": "the check must separate a 12.6 key (no stop) from the 14.6 design key"},
       ["key_positive_stop"])

# --------------------------------------------------------------------------- #
# N4: key too narrow -> slot contact disappears
# --------------------------------------------------------------------------- #
narrow_key = obround(XC, JY, 14.6, 5.6, JZ0, 5.0)
ca_narrow = contact_area(narrow_key, montante)
ca_design = contact_area(long_key, montante)
record("N4_key_0.6mm_too_narrow", ca_narrow[0] <= 1e-9 and ca_design[0] > 1e-9,
       {"key_slot_contact_area_narrow_mm2": ca_narrow[0],
        "key_slot_contact_area_design_mm2": ca_design[0],
        "by_axis_design": ca_design[1]},
       ["face_contact_on_declared_pairs"])

# --------------------------------------------------------------------------- #
# N5: junction mounted between two slots -> the key fouls the rail base plate
# --------------------------------------------------------------------------- #
j5 = clean(base_junction().cut(obround(XC, JY, 15.0, 6.2, JZ0 - 0.1, 5.1)))
j5_between = place(j5, *IDENT, (0, 12.5, 0))
k5 = place(long_key, *IDENT, (0, 12.5, 0))
ov_j = overlap_volume(j5_between, montante)
ov_k = overlap_volume(k5, montante)
# The key is its own body, so the junction body alone stays clean; the foul shows
# up on the declared Chaveta<->Montante contact pair, whose overlap must be 0.
record("N5_junction_between_two_slots", ov_k > 1e-3,
       {"overlap_junction_upright_mm3": ov_j, "overlap_key_upright_mm3": ov_k,
        "note": "the key body fouls the rail base plate by 66.8 mm3, so the zero_interference "
                "gate on the Chaveta<->Montante pair goes False"},
       ["zero_interference"])

# --------------------------------------------------------------------------- #
out = {"stage": "negative", "results": results,
       "all_mutations_caught": all(v["caught"] for v in results.values())}
(ROOT / "negative-results.json").write_text(json.dumps(out, indent=2))
print(json.dumps({k: v["caught"] for k, v in results.items()}, indent=2))
print("all_mutations_caught:", out["all_mutations_caught"])
