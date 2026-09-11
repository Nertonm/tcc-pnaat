"""Build a self-contained visual preview of the R05 v7 three-camera rig.

Run from FreeCAD's Python console, replacing the path with the local clone:

    import runpy; runpy.run_path(r"/absolute/path/to/tcc-pnaat/cad-workspace/scripts/freecad_r05_v7_preview.py", run_name="__main__")

This is intentionally a presentation model. It uses only native Part
primitives, so it has no dependency on vendor meshes, external workbenches or
the unavailable USB camera model. It is not a fabrication or safety model.
"""

from pathlib import Path
import os

import FreeCAD as App
import Part
from FreeCAD import Vector as V

# __file__ e definido em freecadcmd <script> e runpy.run_path (modos
# documentados). Fallback: env R05_WORKSPACE ou CWD; argv[0] nao e
# confiavel quando o script e invocado via wrapper.
_script = globals().get("__file__")
if _script:
    ROOT = Path(_script).resolve().parents[1]
elif os.environ.get("R05_WORKSPACE"):
    ROOT = Path(os.environ["R05_WORKSPACE"]).resolve()
else:
    ROOT = Path.cwd()
OUT = ROOT / "exports" / "concepts" / "optical-rig-r05"
OUT.mkdir(parents=True, exist_ok=True)
DOCUMENT = "R05V7ThreeCameraPreview"

if DOCUMENT in App.listDocuments():
    App.closeDocument(DOCUMENT)

doc = App.newDocument(DOCUMENT)
if doc is None:  # freecadcmd pode retornar None em contexto headless
    doc = App.listDocuments().get(DOCUMENT)
if doc is None:
    raise RuntimeError("could not create document")


def add(name, shape, color, role, transparency=0):
    """Add one named primitive with enough metadata for visual inspection."""
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "Role")
    obj.Role = role
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Transparency = transparency
    return obj


def box(x, y, z, dx, dy, dz):
    return Part.makeBox(dx, dy, dz, V(x, y, z))


def cylinder(radius, height, x, y, z, axis=V(0, 0, 1)):
    return Part.makeCylinder(radius, height, V(x, y, z), axis)


def datum(name, center, direction, description):
    obj = doc.addObject("App::FeaturePython", name)
    obj.addProperty("App::PropertyVector", "OpticalCenter")
    obj.OpticalCenter = center
    obj.addProperty("App::PropertyVector", "LookDirection")
    obj.LookDirection = direction
    obj.addProperty("App::PropertyString", "Description")
    obj.Description = description
    return obj


# Reference conveyor: IN 150 compact nominal only. The belt is intentionally
# translucent; all structural contact dimensions remain pending G0.
add("BELT_IN150_190x1500_REFERENCE", box(-750, -95, -12, 1500, 190, 12), (0.15, 0.15, 0.15), "reference", 65)
add("LEFT_GUIDE_REFERENCE", box(-750, -175, 0, 1500, 12, 60), (0.55, 0.55, 0.58), "reference", 50)
add("RIGHT_GUIDE_REFERENCE", box(-750, 163, 0, 1500, 12, 60), (0.55, 0.55, 0.58), "reference", 50)

# Reference product and nominal 80 mm clearance from belt edge to side optics.
add("BOTTLE_H370_D120_REFERENCE", cylinder(60, 370, 0, 0, 0), (0.25, 0.85, 0.45), "reference", 78)
add("LEFT_CLEARANCE_80_REFERENCE", box(-80, -175, 0, 160, 80, 370), (0.95, 0.78, 0.15), "reference", 90)
add("RIGHT_CLEARANCE_80_REFERENCE", box(-80, 95, 0, 160, 80, 370), (0.95, 0.78, 0.15), "reference", 90)

# Project-designed adapter placeholders. These deliberately are not copies of
# the third-party G-clamp model; each accepts a 1/4-20 tripod interface.
clamp_left = box(-50, -225, 0, 100, 50, 26).fuse(box(-26, -210, 26, 52, 20, 24))
clamp_right = box(-50, 175, 0, 100, 50, 26).fuse(box(-26, 190, 26, 52, 20, 24))
add("LEFT_TRIPOD_CLAMP_ADAPTER_REFERENCE", clamp_left, (0.88, 0.55, 0.19), "reference")
add("RIGHT_TRIPOD_CLAMP_ADAPTER_REFERENCE", clamp_right, (0.88, 0.55, 0.19), "reference")

# Two vertical posts and an overhead bridge. The bridge is above the tallest
# 370 mm bottle; side cameras descend only outside the belt width.
left_post = box(-20, -216, 26, 40, 32, 370)
right_post = box(-20, 184, 26, 40, 32, 370)
bridge = box(-20, -216, 396, 40, 432, 18)
top_riser = box(-20, -16, 414, 40, 32, 110)
add("LEFT_POST", left_post, (0.18, 0.46, 0.72), "printed")
add("RIGHT_POST", right_post, (0.18, 0.46, 0.72), "printed")
add("OVERHEAD_BRIDGE", bridge, (0.18, 0.46, 0.72), "printed")
add("TOP_CAMERA_RISER", top_riser, (0.18, 0.46, 0.72), "printed")

# Pi 5 case is an envelope on the left post, high enough to keep CSI routes
# short. Camera dimensions are reference envelopes, not purchased hardware.
add("PI5_CASE_ENVELOPE", box(-52, -250, 416, 104, 65, 33), (0.76, 0.78, 0.82), "reference", 25)

top_mount = box(-35, -35, 524, 70, 70, 16)
left_mount = box(-35, -192, 229, 70, 20, 32)
right_mount = box(-35, 172, 229, 70, 20, 32)
add("MOUNT_C_TOP", top_mount, (0.88, 0.55, 0.19), "printed")
add("MOUNT_C_LEFT", left_mount, (0.88, 0.55, 0.19), "printed")
add("MOUNT_C_RIGHT_USB_C", right_mount, (0.88, 0.55, 0.19), "printed")

add("C_TOP_CM3_REFERENCE", box(-25, -25, 540, 50, 50, 24), (0.2, 0.5, 0.25), "reference")
add("C_LEFT_CM3_REFERENCE", box(-25, -175, 233, 50, 24, 24), (0.2, 0.5, 0.25), "reference")
add("C_RIGHT_USB_C_UVC_ENVELOPE", box(-30, 151, 230, 60, 30, 30), (0.55, 0.25, 0.75), "reference")

# Visible optical axes make the three viewpoints obvious in the preview.
add("C_TOP_AXIS", cylinder(2, 170, 0, 0, 540, V(0, 0, -1)), (1.0, 0.15, 0.15), "reference")
add("C_LEFT_AXIS", cylinder(2, 175, 0, -165, 245, V(0, 1, 0)), (1.0, 0.15, 0.15), "reference")
add("C_RIGHT_AXIS", cylinder(2, 175, 0, 165, 245, V(0, -1, 0)), (1.0, 0.15, 0.15), "reference")

datum("C_TOP", V(0, 0, 540), V(0, 0, -1), "Raspberry Pi CSI camera; cap view")
datum("C_LEFT", V(0, -165, 245), V(0, 1, 0), "Raspberry Pi CSI camera; left body view")
datum("C_RIGHT", V(0, 165, 245), V(0, -1, 0), "USB-C/UVC envelope; right body view")

info = doc.addObject("App::FeaturePython", "PREVIEW_STATUS")
info.addProperty("App::PropertyString", "Status")
info.Status = "REFERENCE_ONLY; no vendor mesh, G0 fit, FOV, load, slicing or safety validation"
info.addProperty("App::PropertyString", "Contract")
info.Contract = "OPTICAL_RIG_R05_v7_3CAM; IN 150 compact nominal 190 x 1500 mm"

doc.recompute()
if App.GuiUp:
    import FreeCADGui as Gui
    Gui.activeDocument().activeView().viewAxonometric()
    Gui.activeDocument().activeView().fitAll()

output = OUT / "optical-rig-r05-v7-3cam-preview.fcstd"
doc.saveAs(str(output))
print(f"PREVIEW_BUILT {output}")
