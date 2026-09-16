import FreeCAD as A,Part,Mesh,json
from pathlib import Path
V=A.Vector
D = Path(__file__).resolve().parent
d=A.openDocument(str(D/'composicao.FCStd'));p={o.Name:o.Shape for o in d.Objects if hasattr(o,'Shape')}
assert len(p)==51
assert not any(n.startswith('Pi_DIN') or n=='Pi_Tray_CONCEPT' for n in p)
assert all(n in p for n in ['RPiCam_Top_Housing','RPiCam_Top_Cover','RPiCam_PCB_ILLUSTRATIVE','RPiCam_Lens_ILLUSTRATIVE'])
assert all(s.isValid() and s.Volume>0 and s.Solids for s in p.values())
s=Part.Shape();s.read(str(D/'composicao.step'));m=Mesh.Mesh(str(D/'composicao.stl'));comp=Part.makeCompound(list(p.values()))
def bb(s):
 b=s.BoundBox;return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
assert s.isValid() and len(s.Solids)==len(comp.Solids)
assert max(abs(a-b) for a,b in zip(bb(s),bb(comp)))<.01
assert max(abs(a-b) for a,b in zip(bb(m),bb(comp)))<.01
assert abs(s.Volume-comp.Volume)/comp.Volume<1e-6
r=p['MontanteA'].removeSplitter().common(Part.makeBox(80,40,30,V(-240,-30,1145)))
nominal={};clips=[]
for name in ['Pi5_DIN_Bottom','Pi5_DIN_Top']:
 shape=max(p[name].Solids,key=lambda a:a.Volume).removeSplitter();clip=shape.common(Part.makeBox(40,12,30,V(-220,-20,1145))).removeSplitter();clips.append(clip)
 nominal[name]=sum(abs(q.Volume) for q in clip.common(r).Solids);assert nominal[name]<.05
c=Part.makeCompound(clips);mut=c.copy();mut.translate(V(0,1,0));out=c.copy();out.translate(V(0,-1,0));far=c.copy();far.translate(V(0,5000,0))
vv=lambda x:sum(abs(q.Volume) for q in x.common(r).Solids)
assert vv(mut)>1 and vv(out)>1 and vv(far)==0
lens=p['RPiCam_Lens_ILLUSTRATIVE'];b=lens.BoundBox
assert abs((b.XMin+b.XMax)/2)<1e-6 and abs((b.YMin+b.YMax)/2+77)<1e-6
assert b.ZMin>p['PET_REFERENCE'].BoundBox.ZMax
cyl=[f.Surface for f in lens.Faces if isinstance(f.Surface,Part.Cylinder)];assert len(cyl)==1 and abs(cyl[0].Axis.z)>.999999
bottom_faces=[f for f in lens.Faces if isinstance(f.Surface,Part.Plane) and abs(f.BoundBox.ZMin-b.ZMin)<1e-6]
assert any(f.normalAt(0,0).z<-.99999 for f in bottom_faces)
report={'status':'PASS_READBACK_SCOPED_GEOMETRY','objects':len(p),'solids_step':len(s.Solids),'triangles_stl':m.CountFacets,'bounds_mm':bb(s),'no_pi_tray_or_external_collar':True,'native_pi_residual_interference_mm3':nominal,'control_inward_mm3':vv(mut),'control_outward_hook_mm3':vv(out),'control_far_mm3':vv(far),'top_camera_optical_axis':[0,0,-1],'top_camera_to_bottle_top_clearance_mm':b.ZMin-p['PET_REFERENCE'].BoundBox.ZMax,'step_volume_relative_error':abs(s.Volume-comp.Volume)/comp.Volume,'visual_inspection':'not performed: vision tool provider error','manufacturing_release':False}
(D/'verification-readback.json').write_text(json.dumps(report,indent=2));print('VERIFIED',json.dumps(report),flush=True)
