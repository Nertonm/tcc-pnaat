"""Independent v3 audit. Execute through FreeCAD MCP on GUI thread."""
import FreeCAD as App, FreeCADGui as Gui, Part, json, hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'exports/concepts/optical-rig-r05'
p=out/'optical-rig-r05-column-modules-v3.step'
doc=App.getDocument('R05Refs')
shape=Part.Shape(); shape.read(str(p)); solids=shape.Solids
names=['PLINTH','MODULE_1_BODY','MODULE_1_SHOULDER','MODULE_2_BODY','MODULE_2_SHOULDER','MODULE_3_BODY','MODULE_3_SHOULDER','MODULE_4_BODY','MODULE_4_SHOULDER','CROSSBAR_BAR','CROSSBAR_PLATFORM']
assert len(solids)==len(names)
def bb(s):
 b=s.BoundBox
 return [round(v,6) for v in (b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax)]
pieces=[{'index':i,'name':names[i],'bounds_mm':bb(s),'volume_mm3':s.Volume,'valid':s.isValid(),'cylindrical_faces':[{'radius_mm':f.Surface.Radius,'axis':list(f.Surface.Axis),'center':list(f.Surface.Center),'angular_span_rad':f.ParameterRange[1]-f.ParameterRange[0],'bounds_mm':bb(f)} for f in s.Faces if isinstance(f.Surface,Part.Cylinder)]} for i,s in enumerate(solids)]
pairs=[]
for i,a in enumerate(solids):
 for j in range(i+1,len(solids)):
  b=solids[j]; d=a.distToShape(b)[0]
  pairs.append({'a':names[i],'b':names[j],'distance_mm':d,'common_mm3':a.common(b).Volume if d<1e-6 else 0.0})
bottle=Part.makeCylinder(60,370)
product=[{'name':names[i],'common_mm3':s.common(bottle).Volume,'distance_mm':s.distToShape(bottle)[0]} for i,s in enumerate(solids)]
fpc=[]
for z in [-5,1,7,20,61.95,100,110,120,161.95,210,261.95,310,350,410,425]:
 probe=Part.makeBox(20,10,.1,App.Vector(-10,-205,z))
 occupied=[s.common(probe) for s in solids]
 occupied=[s for s in occupied if s.Volume>1e-8]
 vol=0
 if occupied:
  union=occupied[0]
  for s in occupied[1:]: union=union.fuse(s)
  vol=union.Volume
 fpc.append({'z_mm':z,'occupied_area_mm2':vol/.1})
refs=[{'name':o.Name,'label':o.Label,'visibility':o.Visibility,'bounds_mm':bb(o.Mesh),'solid_mesh':o.Mesh.isSolid()} for o in doc.Objects if hasattr(o,'Mesh')]
gates={
'interference':{'status':'FAIL','bottle_subgate':'PASS','bottle_min_distance_mm':min(x['distance_mm'] for x in product),'column_y_mm':[-240,-160],'pair_checks':pairs,'product_checks':product,'reason':'Plinth/body1 and shoulder4/crossbar have positive common volumes; adjacent bodies touch without volumetric overlap.'},
'height':{'status':'FAIL','platform_z_mm':[423,433],'contract_z_mm':[520,560],'missing_mm':[87,127],'net_module_pitch_mm':100,'additional_modules_estimate':1,'estimated_platform_z_with_one_module_mm':533,'reason':'Platform height only. Contract refers to C_TOP optical point; final CM3 mounting offset remains unmeasured.'},
'engagement':{'status':'FAIL','body_z_mm':[[-38,62],[62,162],[162,262],[262,362]],'shoulder_z_mm':[[104,120],[204,220],[304,320],[404,420]],'body_to_own_shoulder_axial_gap_mm':42,'body_joint_engagement_mm':0,'body4_to_crossbar_gap_mm':43,'bar_to_platform_gap_mm':4,'shoulder4_to_platform_gap_mm':3,'m4_nominal_cut_diameter_mm':4.4,'m4_nominal_radial_clearance_mm':0.2,'reason':'Shoulders are detached; body interfaces are butt contacts. Cylindrical cuts exist in v3 bodies and shoulders, but are partial arcs/open notches, not a demonstrated assembled screw joint. Nominal diameter clearance does not establish shoulder fit.'},
'fpc_channel':{'status':'FAIL','probe_xy_mm':[-10,-205,10,-195],'probe_section_mm':[20,10],'samples':fpc,'reason':'Central passage is fully occupied by shoulders at Z110/210/310/410 and platform at Z425. Body interfaces at Z62/162/262 are locally clear. Probe is diagnostic, not a specified cable/connector envelope; no alternative route demonstrated.'},
'interchangeable_grip':{'status':'FAIL','reason':'No matching adapter/receiver for exchangeable foot in supplied v3 STEP. Live LIGHTCLAMP references lie at Y[-25,0], separated at least 135 mm in Y from plinth Y[-240,-160]. Plinth bottom section Z-5 is a closed 120x80 rectangle with no through openings; existing upper cylindrical cuts are diameter 7.2, not proof of a mating interchangeable interface. No new grip geometry was inferred from v1.'}}
result={'status':'BLOCKED','revision':'v3','source_document':'R05Refs','method':'FreeCAD MCP execute_code; native Part/OCCT read, common, distToShape and slices; no CadQuery','input':str(p.relative_to(root)),'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'contract_sha256':hashlib.sha256((root/'data/concepts/optical-rig-r05-contract.json').read_bytes()).hexdigest(),'volume_tolerance_mm3':1e-5,'coordinate_assumption':'Original STEP coordinates; bottle center X=Y=0, base Z=0; physical envelope only, no FOV test. Solid names assigned from bounds and STEP order.','gates':gates,'pieces':pieces,'reference_meshes':refs,'refinement_performed':False,'excluded':['FOV','loads','safety'],'v1_results_reused':False}
(out/'validation-v3.json').write_text(json.dumps(result,indent=2)+'\n')
assert not doc.getObject('V3_GATE_BLOCKED'), 'Audit already exists; do not duplicate'
group=doc.addObject('App::DocumentObjectGroup','V3_GATE_BLOCKED')
group.Label='V3 — BLOCKED — gate geométrico'
for prop,value in [('GateStatus','BLOCKED'),('SourceSTEP',str(p)),('SourceSHA256',result['input_sha256']),('EvidenceJSON',str(out/'validation-v3.json'))]:
 group.addProperty('App::PropertyString',prop,'V3 Audit'); setattr(group,prop,value)
for i,s in enumerate(solids):
 o=doc.addObject('Part::Feature','V3_'+names[i]); o.Shape=s
 o.addProperty('App::PropertyInteger','SourceSolidIndex','V3 Audit'); o.SourceSolidIndex=i
 o.ViewObject.ShapeColor=(0.9,0.6,0.15) if i%2==0 else (0.25,0.55,0.85)
 o.ViewObject.Transparency=25; group.addObject(o)
for check in pairs:
 if check['common_mm3']>1e-5:
  i=names.index(check['a']);j=names.index(check['b'])
  o=doc.addObject('Part::Feature','V3_COLLISION_'+check['a']+'_'+check['b']);o.Shape=solids[i].common(solids[j]);o.ViewObject.ShapeColor=(1.,0.,0.);group.addObject(o)
env=doc.addObject('Part::Feature','V3_BOTTLE_H370_D120');env.Shape=bottle;env.ViewObject.ShapeColor=(0.2,0.8,0.35);env.ViewObject.Transparency=80;group.addObject(env)
for z in [520,560]:
 o=doc.addObject('Part::Feature','V3_CONTRACT_Z'+str(z));o.Shape=Part.makePlane(120,80,App.Vector(-60,-240,z));o.ViewObject.ShapeColor=(0.5,0.25,0.7);o.ViewObject.Transparency=70;group.addObject(o)
doc.recompute();App.setActiveDocument(doc.Name)
original_visibility={x['name']:x['visibility'] for x in refs}
for name in original_visibility: doc.getObject(name).Visibility=False
view=Gui.activeDocument().activeView()
for name,orient in [('isometric',view.viewAxonometric),('front',view.viewFront),('top',view.viewTop)]:
 orient();view.fitAll();Gui.updateGui();view.saveImage(str(out/('v3-gate-'+name+'.png')),1600,1200,'White')
for name,visible in original_visibility.items():doc.getObject(name).Visibility=visible
view.viewAxonometric();view.fitAll();doc.recompute()
doc.saveAs(str(out/'R05Refs-v3-BLOCKED.FCStd'))
print(json.dumps({'status':result['status'],'gates':{k:v['status'] for k,v in gates.items()},'file':doc.FileName,'input_sha256':result['input_sha256'],'collisions':[x for x in pairs if x['common_mm3']>1e-5]}))
