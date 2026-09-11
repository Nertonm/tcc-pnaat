"""Final GUI pass: render the views, raise the real window, grab the desktop,
then quit.  Only run after every geometric gate has passed.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.path.expanduser("~") + "/tcc-pnaat/github/cad-workspace/portico-montantes-20260911T063439Z")
SHOTS = ROOT / "shots"
FCSTD = ROOT / "exports" / "portico-montantes.FCStd"
LOG = open(str(ROOT / "gui-shots-trace.txt"), "a")


def trace(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    LOG.flush()


time.sleep(25)
import FreeCAD as A            # noqa: E402
import FreeCADGui as Gui       # noqa: E402

for name in list(A.listDocuments()):
    A.closeDocument(name)
A.openDocument(str(FCSTD))
doc = Gui.activeDocument()
for o in doc.Document.Objects:
    vo = getattr(o, "ViewObject", None)
    if vo is not None:
        vo.Visibility = True
Gui.updateGui()
view = doc.activeView()

mw = Gui.getMainWindow()
out = {"gui_up": bool(A.GuiUp), "document": doc.Document.Name,
       "objects": len(doc.Document.Objects),
       "main_window_title": mw.windowTitle(), "shots": []}

for name, fn in (("iso", "viewAxonometric"), ("topo", "viewTop"),
                 ("lado", "viewRight"), ("frente", "viewFront")):
    getattr(view, fn)()
    view.fitAll()
    Gui.updateGui()
    p = SHOTS / ("%s.png" % name)
    view.saveImage(str(p), 1600, 1200, "White")
    out["shots"].append({"view": name, "path": str(p), "bytes": p.stat().st_size})
    trace("saved", name, p.stat().st_size)

# put the real window in front, then grab the actual desktop
try:
    mw.resize(1500, 950)
    mw.showNormal()
    mw.raise_()
    mw.activateWindow()
    Gui.updateGui()
    time.sleep(6)
    out["window_geometry_px"] = [mw.width(), mw.height()]
    out["window_visible"] = bool(mw.isVisible())
    env = dict(os.environ)
    env["WAYLAND_DISPLAY"] = "wayland-1"
    env["XDG_RUNTIME_DIR"] = "/run/user/1000"
    grab = SHOTS / "janela-real.png"
    r = subprocess.run(["grim", str(grab)], env=env, capture_output=True, timeout=90)
    out["desktop_grab"] = {"path": str(grab), "returncode": r.returncode,
                           "bytes": grab.stat().st_size if grab.exists() else 0,
                           "stderr": r.stderr.decode()[:300]}
    trace("grab", out["desktop_grab"])
except Exception as e:                                          # noqa: BLE001
    out["desktop_grab"] = {"error": repr(e)}
    trace("grab failed", repr(e))

(ROOT / "gui-shots.json").write_text(json.dumps(out, indent=2))
trace("done", json.dumps(out))
time.sleep(3)
Gui.getMainWindow().close()
sys.exit(0)
