"""Reproduction entry point, to execute on the live FreeCAD GUI via MCP only.

Refuses to replace an open R05OpticalBlock. Geometry derives from local licensed
vendor sources; the existing tower documents are never used as architecture.
"""
import FreeCAD as App, Part, Mesh
ROOT='/home/nerton/tcc-pnaat/github/cad-workspace'
assert 'R05OpticalBlock' not in App.listDocuments(), 'Close the existing document before rebuilding'
doc=App.newDocument('R05OpticalBlock')
for name,rel in [('Pi5_Official','pi5/step/rpi-5b_no_graphics.step'),
                 ('CM3_Wide_Official','camera-module-3/step/Camera_module_3_wide_model_simple.stp'),
                 ('CM3_Std_Official','camera-module-3/step/Camera_module_3_std_model_simple.stp')]:
    o=doc.addObject('PartDesign::Feature',name)
    o.Shape=Part.read(ROOT+'/references/vendor/raspberry-pi/'+rel); o.Visibility=False
if 'Master_Document' not in App.listDocuments():
    App.openDocument(ROOT+'/references/vendor/pi5-case-refs/pi-camera-mounts/Master Document.FCStd')
if 'Camera_Mount___Bottom' not in App.listDocuments():
    App.openDocument(ROOT+'/references/vendor/pi5-case-refs/pi-camera-mounts/Camera Mount - Bottom.FCStd')
m=Mesh.Mesh(ROOT+'/references/vendor/pi5-case-refs/pipiece/stl/case.stl')
m.removeDuplicatedPoints(); m.removeDuplicatedFacets(); m.fixIndices(); m.fixDegenerations(); m.harmonizeNormals()
cs=Part.Shape(); cs.makeShapeFromMesh(m.Topology,0.00001)
assert len(cs.Shells)==1 and cs.Shells[0].isClosed()
raw=Part.makeSolid(cs.Shells[0])
if raw.Volume<0:raw.reverse()
assert raw.isValid()
o=doc.addObject('PartDesign::Feature','Pipiece_Source'); o.Shape=raw.removeSplitter(); o.Visibility=False
App.setActiveDocument(doc.Name)
for stage in ['block','cables','finish','validate','save']:
    path=ROOT+'/scripts/freecad_r05_optical_'+stage+'.py'
    exec(compile(open(path).read(),path,'exec'))
