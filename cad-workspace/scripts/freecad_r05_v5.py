"""Reproduce in live FreeCAD: MCP execute_code(exec(open(this_file).read())).

Refuses to replace an existing document. Native FreeCAD Part/OCCT, no CadQuery.
The spreadsheet stores the validated design snapshot. Rebuild is explicit;
this is not a fully constrained, live-propagating assembly solver.
"""
import FreeCAD as App, FreeCADGui as Gui, Part, Mesh, os
ROOT=str(Path(__file__).resolve().parents[1])
if 'R05ColumnV5' in App.listDocuments():
    raise RuntimeError('R05ColumnV5 already exists; preserve it or close it before rebuilding')
App.newDocument('R05ColumnV5')
v5raw={}
for key,rel in [('case','pipiece/stl/case.stl'),('body','light-clamp/stl/body.stl'),('clamp','light-clamp/stl/clamp.stl')]:
    m=Mesh.Mesh(ROOT+'/references/vendor/pi5-case-refs/'+rel)
    if key=='case':
        m.removeDuplicatedPoints(); m.removeDuplicatedFacets(); m.fixIndices(); m.fixDegenerations(); m.harmonizeNormals()
    s=Part.Shape(); s.makeShapeFromMesh(m.Topology,0.00001 if key=='case' else 0.01)
    assert len(s.Shells)==1 and s.Shells[0].isClosed()
    s=Part.makeSolid(s.Shells[0])
    if s.Volume<0: s.reverse()
    assert s.isValid()
    v5raw[key]=s.removeSplitter() if key=='case' else s
exec(open(ROOT+'/scripts/freecad_r05_v5_build.py').read())
# These reference imports follow the validated core geometry stage.
mountdoc=App.openDocument(ROOT+'/references/vendor/pi5-case-refs/pi-camera-mounts/Camera Mount - Bottom.FCStd')
App.setActiveDocument('R05ColumnV5')
official={}
for key,path in [('Pi5','pi5/step/rpi-5b_no_graphics.step'),('CM3_Std','camera-module-3/step/Camera_module_3_std_model_simple.stp'),('CM3_Wide','camera-module-3/step/Camera_module_3_wide_model_simple.stp')]:
    official[key]=Part.read(ROOT+'/references/vendor/raspberry-pi/'+path)
exec(open(ROOT+'/scripts/freecad_r05_v5_refine.py').read())
exec(open(ROOT+'/scripts/freecad_r05_v5_validate.py').read())
d.recompute()
d.saveAs(OUT+'/optical-rig-r05-column-v5.fcstd')
