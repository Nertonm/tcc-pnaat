"""PNAAT portico: two DIN uprights + DIN crossbar + corner junctions.

Everything is generated from script.  Nothing is drawn by hand in the GUI.
Every placement comes from a measured datum (see RELATORIO.md).
"""

import json
import sys
import time
from pathlib import Path

import FreeCAD as A
import Import
import Part
from FreeCAD import Vector as V

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import lib_geo as G  # noqa: E402
from lib_geo import contact_area, min_gap, overlap_volume, place, stats  # noqa: E402

IN = ROOT / "inputs"
OUT = ROOT / "exports"
OUT.mkdir(exist_ok=True)
T0 = time.time()
report = {"stage": "build", "premises": {}, "parts": {}, "pairs": {}, "kinematics": {},
          "gates": {}, "open": []}
_save_path = ROOT / "build-measurements.json"


def save():
    _save_path.write_text(json.dumps(report, indent=2, default=str))


def say(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


# --------------------------------------------------------------------------- #
# 0. premises + input integrity
# --------------------------------------------------------------------------- #
PREM = {
    "frame": {"X": "across conveyor", "Y": "vertical (authored CAD)", "Z": "rail normal"},
    "upright_len_mm": 450.0,
    "crossbar_len_mm": 600.0,
    "upright_spacing_mm": 400.0,
    "junction_height_above_socket_mm": 362.5,
    "junction_height_note": ("contract premise was 350 mm; realised 362.5 mm because the positive "
                             "retention key can only engage a rail slot and the measured slot "
                             "pitch is 25 mm"),
    "second_grip": ("rigid translation of the validated grip+piece by +400 mm in X; its "
                    "orientation relative to the two real sides of the conveyor is NOT validated "
                    "(the conveyor was never measured)"),
    "conveyor_section_measured": False,
    "slot_pattern": ("measured on the vendor 75 mm sample: pitch 25.0 mm, obround 6.2 x 15.0 "
                     "through the 1.0 mm base plate; repeated along the extruded rail"),
    "print_clearance": ("NOT modelled: each mating channel is the exact female of the rail "
                        "section (nominal zero clearance). A real print needs ~0.2-0.3 mm per "
                        "side, which would turn these nominal contacts into clearance fits"),
    "fasteners": ("lock screws are plain cylindrical ENVELOPES; no thread, no torque, no preload "
                  "and no retention of the screw inside its hole is modelled"),
    "load_path": ("the vertical load reaches the upright only through the retention key bearing "
                  "on a rail slot end; that 1.0 mm plate in shear is NOT sized here"),
}
report["premises"] = PREM

INPUTS = ["dinr135-007.5.step", "peca-dupla-plataformas.step",
          "G-clamp_Tripod-component0.stl.brep", "DIN-Rail-Bracket-4mm-component0.stl.brep"]
report["input_sha256"] = {n: G.sha256(IN / n) for n in INPUTS}
save()

# --------------------------------------------------------------------------- #
# 1. calibrate the measurer, extract and validate the section
# --------------------------------------------------------------------------- #
report["measurer_self_test"] = G.self_test_contact_area()
save()

rail0 = Part.read(str(IN / "dinr135-007.5.step"))
sec = G.rail_section_face(rail0)
report["vendor_rail"] = stats(rail0)
report["section"] = {
    "area_mm2": round(sec.Area, 6),
    "perimeter_mm": round(sec.OuterWire.Length, 6),
    "edges": len(sec.OuterWire.Edges),
    "bbox_local": [round(x, 6) for x in (sec.BoundBox.XMin, sec.BoundBox.YMin,
                                         sec.BoundBox.ZMin, sec.BoundBox.XMax,
                                         sec.BoundBox.YMax, sec.BoundBox.ZMax)],
    "note": "open hat band (base plate at local Y=0, open hat mouth at local Y=7.5)",
}

ref75, n75 = G.build_rail(sec, 75.0)
report["section_fidelity_75mm"] = {
    "rebuilt_volume": round(ref75.Volume, 6), "vendor_volume": round(rail0.Volume, 6),
    "delta_volume": round(ref75.Volume - rail0.Volume, 9),
    "rebuilt_bbox": stats(ref75)["bbox"], "vendor_bbox": stats(rail0)["bbox"],
    "slots": n75, "solids": len(ref75.Solids), "valid": bool(ref75.isValid()),
}
report["gates"]["section_fidelity"] = bool(
    abs(ref75.Volume - rail0.Volume) < 1e-6
    and stats(ref75)["bbox"] == stats(rail0)["bbox"]
    and len(ref75.Solids) == 1 and ref75.isValid())
say("section fidelity:", report["gates"]["section_fidelity"], report["section_fidelity_75mm"])
save()

# --------------------------------------------------------------------------- #
# 2. exact socket datum measured on the validated piece
# --------------------------------------------------------------------------- #
peca = Part.read(str(IN / "peca-dupla-plataformas.step"))
clamp = Part.read(str(IN / "G-clamp_Tripod-component0.stl.brep"))


def find_socket_end_face(shape):
    """Planar +Y face of the socket block that caps the hat-shaped through hole."""
    cands = []
    for f in shape.Faces:
        if type(f.Surface).__name__ != "Plane":
            continue
        b = f.BoundBox
        n = f.normalAt(0, 0)
        if n.y < 0.999:
            continue
        if b.YLength > 1e-6 or not (34.0 < b.XLength < 36.5):
            continue
        if not (b.XMin < -47.5 and b.XMax > -13.5 and b.ZMin < 10.2 and b.ZMax > 17.4):
            continue
        cands.append(f)
    if not cands:
        raise RuntimeError("socket end face not found")
    return min(cands, key=lambda f: f.BoundBox.YMin)


sf = find_socket_end_face(peca)
sb = sf.BoundBox
XC = round((sb.XMin + sb.XMax) / 2.0, 6)
Y0 = round(sb.YMin, 6)
ZB = round((sb.ZMin + sb.ZMax) / 2.0 - (sec.BoundBox.YMin + sec.BoundBox.YMax) / 2.0, 6)
report["socket_datum_measured"] = {
    "face_area_mm2": round(sf.Area, 6), "face_edges": len(sf.OuterWire.Edges),
    "face_bbox": [round(v, 6) for v in (sb.XMin, sb.YMin, sb.ZMin, sb.XMax, sb.YMax, sb.ZMax)],
    "XC": XC, "Y0": Y0, "ZB": ZB,
    "method": ("hole end-plane Y; hole bbox centre in X; hole bbox centre in Z minus the rail "
               "section bbox centre in its height axis")}
say("socket datum:", report["socket_datum_measured"])

# --------------------------------------------------------------------------- #
# 3. rails
# --------------------------------------------------------------------------- #
MONT_LEN = PREM["upright_len_mm"]
TRAV_LEN = PREM["crossbar_len_mm"]
SPAN = PREM["upright_spacing_mm"]
JY = 105.402 + 25.0 * 14                       # slot k=14 centre -> 455.402
TZ = 20.0                                       # crossbar base-plate plane
TX = (XC + (XC + SPAN)) / 2.0 - TRAV_LEN / 2.0
WALL = 4.0
JX0, JX1 = XC - 17.5 - WALL, XC + 17.5 + WALL
JY0, JY1 = JY - 17.5 - WALL, JY + 17.5 + WALL
JZ0, JZ1 = ZB - WALL, TZ + 7.5 + WALL
SHEAR_PLANE_UP = 13.5       # rail outer wall plane, local Z (measured: see RELATORIO)
report["placements"] = {"XC": XC, "Y0": Y0, "ZB": ZB, "JY": JY, "TX": TX, "TZ": TZ,
                        "junction_box": [JX0, JY0, JZ0, JX1, JY1, JZ1],
                        "key_slot_centre_Y": JY, "uprights_X": [XC, XC + SPAN],
                        "rail_outer_wall_local_Z": SHEAR_PLANE_UP}

montante, nslots_m = G.build_rail(sec, MONT_LEN)
montante = place(montante, *G.ROT_UPRIGHT, (XC, Y0, ZB))
travessa, nslots_t = G.build_rail(sec, TRAV_LEN)
travessa = place(travessa, *G.ROT_CROSSBAR, (TX, JY, TZ))
report["rail_slot_counts"] = {"upright": nslots_m, "crossbar": nslots_t}

# --------------------------------------------------------------------------- #
# 4. junction
# --------------------------------------------------------------------------- #
band_u = place(sec.extrude(V(140.0, 0, 0)), *G.ROT_UPRIGHT, (XC, JY - 70.0, ZB))
band_c = place(sec.extrude(V(160.0, 0, 0)), *G.ROT_CROSSBAR, (TX - 20.0, JY, TZ))
block = Part.makeBox(JX1 - JX0, JY1 - JY0, JZ1 - JZ0, V(JX0, JY0, JZ0))
junc_nokey = block.cut(band_u).cut(band_c).removeSplitter()
vol_after_channels = junc_nokey.Volume

KEY_W = 6.2          # across the rail width  (world X for the upright)
KEY_CLEAR_END = 0.2  # axial clearance to each slot end (print clearance, modelled)
SLOT_L = 15.0
KEY_L = SLOT_L - 2 * KEY_CLEAR_END          # 14.6 : 0.2 mm play before the key bears
KEY_STRAIGHT = KEY_L - KEY_W                # 8.4 between the two semicircle centres


def key_prism(xc, yc, z0, h):
    """Obround 6.2 x 14.6 (semicircle ends r=3.1) extruded h along +Z."""
    s = Part.makeBox(KEY_W, KEY_STRAIGHT, h, V(xc - KEY_W / 2.0, yc - KEY_STRAIGHT / 2.0, z0))
    for dy in (-KEY_STRAIGHT / 2.0, KEY_STRAIGHT / 2.0):
        s = s.fuse(Part.makeCylinder(KEY_W / 2.0, h, V(xc, yc + dy, z0), V(0, 0, 1)))
    return s


def slot_prism(xc, yc, z0, h):
    """The measured rail slot obround 6.2 x 15.0 (centres 8.8 apart), extruded +Z."""
    s = Part.makeBox(KEY_W, SLOT_L - KEY_W, h, V(xc - KEY_W / 2.0, yc - (SLOT_L - KEY_W) / 2.0, z0))
    for dy in (-(SLOT_L - KEY_W) / 2.0, (SLOT_L - KEY_W) / 2.0):
        s = s.fuse(Part.makeCylinder(KEY_W / 2.0, h, V(xc, yc + dy, z0), V(0, 0, 1)))
    return s


SCREW_R = 1.5        # dia 3.0 envelope
HOLE_R = 1.7         # dia 3.4 hole
V_TIP_X = XC + SHEAR_PLANE_UP          # -17.0 : outer face of the upright's +X wall
H_TIP_Y = JY + SHEAR_PLANE_UP          # 468.902 : outer face of the crossbar's +Y wall
SCREWS = {
    "V": {"hole": ((JX1, JY - 12.0, 13.8), (-1, 0, 0), (JX1 - (V_TIP_X - 0.2))),
          "env": ((V_TIP_X, JY - 12.0, 13.8), (1, 0, 0), 8.0)},
    "H": {"hole": ((XC, JY1, 24.0), (0, -1, 0), (JY1 - (H_TIP_Y - 0.2))),
          "env": ((XC, H_TIP_Y, 24.0), (0, 1, 0), 8.0)},
}
report["lock_screws"] = {"envelope_dia": 2 * SCREW_R, "hole_dia": 2 * HOLE_R,
                         "V_tip_plane_X": V_TIP_X, "H_tip_plane_Y": H_TIP_Y,
                         "hole_overshoot_mm": 0.2}

junc = junc_nokey.cut(slot_prism(XC, JY, JZ0 - 0.1, WALL + 0.2))
for sc in SCREWS.values():
    junc = junc.cut(Part.makeCylinder(HOLE_R, sc["hole"][2], V(*sc["hole"][0]), V(*sc["hole"][1])))
junc = junc.removeSplitter()
report["junction_build"] = {
    "volume_after_channels": round(vol_after_channels, 6),
    "volume_final": round(junc.Volume, 6),
    "solids": len(junc.Solids), "valid": bool(junc.isValid()),
    "no_key_variant_solids": len(junc_nokey.Solids),
    "no_key_variant_valid": bool(junc_nokey.isValid())}
say("junction:", report["junction_build"])
save()

key = key_prism(XC, JY, JZ0, 5.0).removeSplitter()


def env(name):
    h = SCREWS[name]["env"]
    return Part.makeCylinder(SCREW_R, h[2], V(*h[0]), V(*h[1]))


DX = SPAN
IDENT = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
shapes = {
    "ClampFunctionalSource": clamp,
    "PecaDuplaPlataformasOFICIAL": peca,
    "ClampFunctionalSourceB": place(clamp, *IDENT, (DX, 0, 0)),
    "PecaDuplaPlataformasOFICIALB": place(peca, *IDENT, (DX, 0, 0)),
    "MontanteA": montante,
    "MontanteB": place(montante, *IDENT, (DX, 0, 0)),
    "Travessa": travessa,
    "JuncaoA": junc,
    "JuncaoB": place(junc, *IDENT, (DX, 0, 0)),
    "ChavetaA": key,
    "ChavetaB": place(key, *IDENT, (DX, 0, 0)),
    "ParafusoTravaV_A": env("V"),
    "ParafusoTravaH_A": env("H"),
    "ParafusoTravaV_B": place(env("V"), *IDENT, (DX, 0, 0)),
    "ParafusoTravaH_B": place(env("H"), *IDENT, (DX, 0, 0)),
}
report["parts"] = {n: stats(s) for n, s in shapes.items()}
MANUFACTURED = [n for n in shapes if not n.startswith(("Clamp", "Peca"))]
report["gates"]["parts_single_valid_solid"] = all(
    report["parts"][n]["valid"] and report["parts"][n]["solids"] == 1 for n in MANUFACTURED)
say("parts:", json.dumps({k: [v["solids"], round(v["volume"], 2)]
                          for k, v in report["parts"].items()}))
save()

# --------------------------------------------------------------------------- #
# 5. pairs: interference, gap, face contact.  kind: contact / clearance / none
# --------------------------------------------------------------------------- #
PAIRS = [
    ("JuncaoA", "MontanteA", "contact"),
    ("JuncaoA", "Travessa", "contact"),
    ("JuncaoB", "MontanteB", "contact"),
    ("JuncaoB", "Travessa", "contact"),
    ("ChavetaA", "MontanteA", "contact"),
    ("ChavetaB", "MontanteB", "contact"),
    ("ChavetaA", "JuncaoA", "contact"),
    ("ChavetaB", "JuncaoB", "contact"),
    ("ParafusoTravaV_A", "MontanteA", "contact"),
    ("ParafusoTravaH_A", "Travessa", "contact"),
    ("ParafusoTravaV_B", "MontanteB", "contact"),
    ("ParafusoTravaH_B", "Travessa", "contact"),
    ("ClampFunctionalSource", "PecaDuplaPlataformasOFICIAL", "contact"),
    ("ClampFunctionalSourceB", "PecaDuplaPlataformasOFICIALB", "contact"),
    ("MontanteA", "PecaDuplaPlataformasOFICIAL", "contact"),
    ("MontanteB", "PecaDuplaPlataformasOFICIALB", "contact"),
    ("ParafusoTravaV_A", "JuncaoA", "clearance"),
    ("ParafusoTravaH_A", "JuncaoA", "clearance"),
    ("MontanteA", "Travessa", "none"),
    ("JuncaoA", "MontanteB", "none"),
    ("JuncaoA", "ClampFunctionalSource", "none"),
    ("JuncaoA", "PecaDuplaPlataformasOFICIAL", "none"),
]
pairs_out = {}
for a, b, kind in PAIRS:
    ov = overlap_volume(shapes[a], shapes[b])
    gp = min_gap(shapes[a], shapes[b])
    ca, axes, npairs, secs, st = contact_area(shapes[a], shapes[b])
    pairs_out["%s__%s" % (a, b)] = {
        "kind": kind, "overlap_mm3": ov, "min_gap_mm": gp, "contact_area_mm2": ca,
        "contact_by_axis_mm2": axes, "face_pairs_tested": npairs, "seconds": secs,
        "status": st}
    say("pair", a, "<->", b, kind, "overlap", ov, "gap", gp, "contact_area", ca, axes, st)
    report["pairs"] = pairs_out
    save()

# focused diagnostic on the inherited socket interface
rail_end = [f for f in shapes["MontanteA"].Faces
            if type(f.Surface).__name__ == "Plane" and abs(f.normalAt(0, 0).y) > 0.999
            and abs(f.Area - sec.Area) < 1e-3 and abs(f.BoundBox.YMin - Y0) < 1e-6]
report["socket_interface_diagnostic"] = {
    "upright_end_face_area_mm2": round(rail_end[0].Area, 6) if rail_end else None,
    "upright_end_face_Y": round(rail_end[0].BoundBox.YMin, 9) if rail_end else None,
    "socket_end_face_area_mm2": round(sf.Area, 6),
    "socket_end_face_Y": round(sb.YMin, 9),
    "end_face_common_area_mm2": round(rail_end[0].common(sf).Area, 6) if rail_end else None,
    "pair_contact_area_mm2": pairs_out["MontanteA__PecaDuplaPlataformasOFICIAL"]["contact_area_mm2"],
    "pair_contact_by_axis": pairs_out["MontanteA__PecaDuplaPlataformasOFICIAL"]["contact_by_axis_mm2"],
    "min_gap_mm": pairs_out["MontanteA__PecaDuplaPlataformasOFICIAL"]["min_gap_mm"],
    "overlap_mm3": pairs_out["MontanteA__PecaDuplaPlataformasOFICIAL"]["overlap_mm3"],
}
say("socket diagnostic:", report["socket_interface_diagnostic"])

RESIDUE_TOL = 1e-3
contact_pairs = [k for k, v in pairs_out.items() if v["kind"] == "contact"]
report["gates"]["zero_interference"] = all(
    v["overlap_mm3"] <= RESIDUE_TOL for v in pairs_out.values())
report["interference_residues"] = {
    k: v["overlap_mm3"] for k, v in pairs_out.items()
    if 1e-9 < v["overlap_mm3"] <= RESIDUE_TOL}
report["max_overlap_mm3"] = max(v["overlap_mm3"] for v in pairs_out.values())
report["gates"]["face_contact_on_declared_pairs"] = all(
    pairs_out[k]["contact_area_mm2"] > 0.0 for k in contact_pairs)
report["gates"]["declared_clearances_not_touching"] = all(
    pairs_out[k]["contact_area_mm2"] == 0.0 for k, v in pairs_out.items()
    if v["kind"] == "clearance")
report["gates"]["no_contact_pairs_really_clear"] = all(
    pairs_out[k]["contact_area_mm2"] == 0.0 and pairs_out[k]["overlap_mm3"] <= RESIDUE_TOL
    for k, v in pairs_out.items() if v["kind"] == "none")
say("gates pairs:", report["gates"]["zero_interference"],
    report["gates"]["face_contact_on_declared_pairs"],
    report["gates"]["declared_clearances_not_touching"],
    report["gates"]["no_contact_pairs_really_clear"])
save()

# --------------------------------------------------------------------------- #
# 6. kinematics
# --------------------------------------------------------------------------- #
kin = {}
for dy in (-50.0, -25.0, 25.0, 50.0):
    j = place(junc, *IDENT, (0, dy, 0))
    kin["junction_shift_Y_%+.0f" % dy] = {"overlap_vs_upright": overlap_volume(j, montante)}
for dx in (-60.0, -30.0, 30.0, 60.0, 100.0):
    t = place(travessa, *IDENT, (dx, 0, 0))
    kin["crossbar_shift_X_%+.0f" % dx] = {
        "overlap_vs_JuncaoA": overlap_volume(t, junc),
        "overlap_vs_JuncaoB": overlap_volume(t, place(junc, *IDENT, (DX, 0, 0)))}
for dy in (-25.0, 25.0):
    j = place(junc, *IDENT, (0, dy, 0))
    t = place(travessa, *IDENT, (0, dy, 0))
    kin["junction_and_crossbar_shift_Y_%+.0f" % dy] = {
        "overlap_junction_upright": overlap_volume(j, montante),
        "overlap_junction_crossbar": overlap_volume(j, t)}

upoint = (XC, JY, ZB + 3.75)
for deg in (1.0, 2.0, 5.0):
    r = G.rot_about_axis(montante, upoint, (0, 1, 0), deg)
    kin["upright_rot_%.1fdeg" % deg] = {
        "overlap_vs_JuncaoA": overlap_volume(r, junc),
        "overlap_vs_channel_only_no_key_hole": overlap_volume(r, junc_nokey)}
for deg in (1.0, 2.0, 5.0):
    r = G.rot_about_axis(travessa, (XC, JY, TZ + 3.75), (1, 0, 0), deg)
    kin["crossbar_rot_%.1fdeg" % deg] = {"overlap_vs_JuncaoA": overlap_volume(r, junc)}
for deg in (2.0,):
    r = G.rot_about_axis(travessa, (XC, JY, TZ + 3.75), (0, 1, 0), deg)
    kin["crossbar_rot_about_Y_%.1fdeg" % deg] = {"overlap_vs_JuncaoA": overlap_volume(r, junc)}

for dy in (0.0, 0.1, 0.2, 0.5, 2.0):
    r = place(montante, *IDENT, (0, dy, 0))
    kin["upright_axial_%+.1f_with_key" % dy] = {
        "overlap_vs_JuncaoA": overlap_volume(r, junc),
        "overlap_vs_ChavetaA": overlap_volume(r, key)}
for dy in (0.2, 0.5, 2.0):
    r = place(montante, *IDENT, (0, dy, 0))
    kin["upright_axial_%+.1f_key_hole_empty" % dy] = {
        "overlap_vs_JuncaoA_nokey": overlap_volume(r, junc_nokey)}

# transversal restraint of the junction on the upright (cage, not friction)
for axis, dv in (("X", 0.5), ("Z", 0.5)):
    d = {"X": (0.5, 0, 0), "Z": (0, 0, 0.5)}[axis]
    j = place(junc, *IDENT, d)
    kin["junction_shift_%s_%+.1f" % (axis, dv)] = {"overlap_vs_upright": overlap_volume(j, montante)}
# transversal restraint of the crossbar inside the junction
for axis, d in (("Y", (0, 0.5, 0)), ("Z", (0, 0, 0.5))):
    t = place(travessa, *IDENT, d)
    kin["crossbar_shift_%s_%+.1f" % (axis, 0.5)] = {"overlap_vs_JuncaoA": overlap_volume(t, junc)}
report["kinematics"] = kin

report["gates"]["sliding_free"] = (
    all(v["overlap_vs_upright"] <= RESIDUE_TOL for k, v in kin.items()
        if k.startswith("junction_shift_Y"))
    and all(v["overlap_vs_JuncaoA"] <= RESIDUE_TOL and v["overlap_vs_JuncaoB"] <= RESIDUE_TOL
            for k, v in kin.items() if k.startswith("crossbar_shift_X"))
    and all(v["overlap_junction_upright"] <= RESIDUE_TOL
            and v["overlap_junction_crossbar"] <= RESIDUE_TOL
            for k, v in kin.items() if k.startswith("junction_and_crossbar_shift")))
report["gates"]["transversal_restraint"] = (
    all(v["overlap_vs_upright"] > RESIDUE_TOL for k, v in kin.items()
        if k.startswith("junction_shift_X") or k.startswith("junction_shift_Z"))
    and all(v["overlap_vs_JuncaoA"] > RESIDUE_TOL for k, v in kin.items()
            if k.startswith("crossbar_shift_Y") or k.startswith("crossbar_shift_Z")))
report["gates"]["rotation_blocked"] = (
    all(v["overlap_vs_JuncaoA"] > RESIDUE_TOL for k, v in kin.items()
        if k.startswith("upright_rot"))
    and all(v["overlap_vs_channel_only_no_key_hole"] > RESIDUE_TOL
            for k, v in kin.items() if k.startswith("upright_rot"))
    and all(v["overlap_vs_JuncaoA"] > RESIDUE_TOL for k, v in kin.items()
            if k.startswith("crossbar_rot")))
report["gates"]["key_positive_stop"] = (
    kin["upright_axial_+0.0_with_key"]["overlap_vs_ChavetaA"] <= RESIDUE_TOL
    and kin["upright_axial_+0.1_with_key"]["overlap_vs_ChavetaA"] <= RESIDUE_TOL
    and kin["upright_axial_+0.5_with_key"]["overlap_vs_ChavetaA"] > RESIDUE_TOL
    and kin["upright_axial_+0.5_key_hole_empty"]["overlap_vs_JuncaoA_nokey"] <= RESIDUE_TOL)
say("gates kinematics: sliding_free", report["gates"]["sliding_free"],
    "transversal_restraint", report["gates"]["transversal_restraint"],
    "rotation_blocked", report["gates"]["rotation_blocked"],
    "key_positive_stop", report["gates"]["key_positive_stop"])
save()

# --------------------------------------------------------------------------- #
# 7. export
# --------------------------------------------------------------------------- #
DOC = "PNAAT_Portico_Montantes"
if DOC in A.listDocuments():
    A.closeDocument(DOC)
doc = A.newDocument(DOC)
if doc is None:
    doc = A.listDocuments().get(DOC)
feats = []
for name, shape in shapes.items():
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    feats.append(o)
doc.recompute()
fcstd = OUT / "portico-montantes.FCStd"
doc.saveAs(str(fcstd))
step = OUT / "portico-montantes.step"
Import.export(feats, str(step))
report["exports"] = {"step": str(step), "step_bytes": step.stat().st_size,
                     "fcstd": str(fcstd), "fcstd_bytes": fcstd.stat().st_size,
                     "objects": len(feats)}
say("exports:", report["exports"])
save()

report["gates"]["all_geometric_gates_pass"] = all(
    report["gates"][k] for k in ("section_fidelity", "parts_single_valid_solid",
                                 "zero_interference", "face_contact_on_declared_pairs",
                                 "declared_clearances_not_touching",
                                 "no_contact_pairs_really_clear", "sliding_free",
                                 "transversal_restraint", "rotation_blocked",
                                 "key_positive_stop")
) and report["measurer_self_test"]["pass"] and report["measurer_self_test"]["separated_pass"]
report["seconds"] = round(time.time() - T0, 1)
save()
say("ALL GEOMETRIC GATES:", report["gates"]["all_geometric_gates_pass"])
print(json.dumps(report["gates"], indent=2))
