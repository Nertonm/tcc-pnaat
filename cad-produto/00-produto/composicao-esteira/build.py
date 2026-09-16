import os
import FreeCAD as A,Part,Mesh,MeshPart,Import,json,hashlib,math
from pathlib import Path
V=A.Vector
ROOT = Path(__file__).resolve().parents[1]   # 00-produto, resolvido a partir deste arquivo
OLD=ROOT/'composicao-esteira-usb-esp-ilustrativa-r02'
OUT=ROOT/'composicao-esteira-3cams-din-nativo-r03'
OUT.mkdir(exist_ok=True);assert not (OUT/'composicao.FCStd').exists()
d=A.openDocument(str(OLD/'composicao.FCStd'))
for n in [o.Name for o in d.Objects if o.Name.startswith('Pi_DIN') or o.Name=='Pi_Tray_CONCEPT']:
 d.removeObject(n)
P=ROOT.parent/'02-impressao/case-pi-din'
R = Path(os.environ.get('PNAAT_CAM_REF', ''))  # referencia da camera, fora do repo
sources=[]
def load(p,all_shells=True):
 m=Mesh.Mesh(str(p));sh=Part.Shape();sh.makeShapeFromMesh(m.Topology,.01);ss=[]
 for shell in sh.Shells:
  assert shell.isClosed();s=Part.makeSolid(shell)
  if s.Volume<0:s.reverse()
  assert s.isValid() and s.Volume>0;ss.append(s)
 sources.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'shell_volumes_mm3':[s.Volume for s in ss]})
 if not all_shells:return max(ss,key=lambda s:s.Volume).removeSplitter()
 return Part.makeCompound(ss) if len(ss)>1 else ss[0]
def add(n,s):
 assert s.isValid() and s.Solids and s.Volume>0,n
 f=d.addObject('PartDesign::Feature',n);f.Shape=s;return s
def box(x,y,z,dx,dy,dz):return Part.makeBox(dx,dy,dz,V(x,y,z))
def vol(a,b):
 assert a.isValid() and b.isValid() and a.Solids and b.Solids
 return sum(abs(s.Volume) for s in a.common(b).Solids)
def bb(s):
 b=s.BoundBox;return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
# NATIVE CLIP: local +X side wall, localY groove width35.5, localZ rail extrusion.
# Source bottom has tiny tessellation angular offsets; nominal residual is reported, not hidden.
trans=V(-248.899,-89.5256,1145)
for name,fn in [('Pi5_DIN_Bottom','pi5-din-bottom-side.stl'),('Pi5_DIN_Top','pi5-din-topside.stl')]:
 s=load(P/fn);s.rotate(V(0,0,0),V(0,0,1),90);s.translate(trans);d.getObject(name).Shape=s
# True source RPi camera enclosure, opening located by inner wire in source cover.
# Aperture centre local (0, -17.7164, 111.962); rotate about X => downward normal.
camT=V(0,34.962,1295)
def camera_place(s):
 s=s.copy();s.rotate(V(0,0,0),V(1,0,0),90);s.translate(camT);return s
housing=load(R/'cam_housing.stl');cover=load(R/'cam_cover.stl')
add('RPiCam_Top_Housing',camera_place(housing));add('RPiCam_Top_Cover',camera_place(cover))
# Reference-only board and lens occupy the vendor enclosure; not an exact CM3 board.
board=box(-12.5,-10.3164,102.5,25,1.6,24)
for x in [-10.5,10.5]:
 for z in [112,124.5]:board=board.cut(Part.makeCylinder(2.05,3,V(x,-11,z),V(0,1,0)))
add('RPiCam_PCB_ILLUSTRATIVE',camera_place(board))
lens=Part.makeCylinder(3.8,9.4,V(0,-10.3164,111.962),V(0,-1,0));add('RPiCam_Lens_ILLUSTRATIVE',camera_place(lens))
# Horizontal DIN split collar and bracket to camera rear face; no belt support.
ring=box(-18,-34.5,1190.9020080566,36,21.5,49).cut(box(-19,-27.5,1197.90200805664,38,7.5,35))
for x in [-12,12]:
 for z in [1194,1241]:ring=ring.cut(Part.makeCylinder(1.7,24,V(x,-36,z),V(0,1,0)))
front=ring.common(box(-20,-40,1185,40,16.25,70));rear=ring.common(box(-20,-23.75,1185,40,20,70))
# Original housing rear flat plane transforms into z1287.7835998535.
backZ=1287.7835998535156
boom=box(-9,-40.5,1220,18,6,backZ+5-1220).fuse(box(-9,-86,backZ,18,51.5,5)).removeSplitter()
add('TopCam_DIN_FrontAndBoom',front.fuse(boom).removeSplitter());add('TopCam_DIN_Rear',rear)
for i,x in enumerate([-12,12]):
 bolt=Part.makeCylinder(1.5,24,V(x,-36,1194),V(0,1,0)).fuse(Part.makeCylinder(3,2,V(x,-38,1194),V(0,1,0)))
 add('TopCam_M3_'+str(i),bolt)
# Verification predicates. Clip window bounds enclose every possible native case/rail intersection.
p={o.Name:o.Shape for o in d.Objects if hasattr(o,'Shape')}
r=p['MontanteA'].removeSplitter().common(box(-240,-30,1145,80,40,30))
fit={};pi_full=[]
for n in ['Pi5_DIN_Bottom','Pi5_DIN_Top']:
 s=p[n];primary=max(s.Solids,key=lambda q:q.Volume).removeSplitter()
 clip=primary.common(box(-220,-20,1145,40,12,30)).removeSplitter();pi_full.append(clip)
 v=vol(clip,r);extras=sum(x.Volume for x in s.Solids)-primary.Volume
 assert v+max(0,extras)<.05,(n,v,extras)
 fit[n]={'primary_interference_mm3':v,'excluded_micro_shell_volume_bound_mm3':max(0,extras),'distance_mm':clip.distToShape(r)[0]}
# CTL+: inward push by1mm must collide; outward removal hits the native hooks, not an external collar.
clip=Part.makeCompound(pi_full)
inward=clip.copy();inward.translate(V(0,1,0));outward=clip.copy();outward.translate(V(0,-1,0));far=clip.copy();far.translate(V(0,5000,0))
controls={'inward_1mm_mm3':vol(inward,r),'outward_1mm_hook_interference_mm3':vol(outward,r),'far_mm3':vol(far,r)}
assert controls['inward_1mm_mm3']>1 and controls['outward_1mm_hook_interference_mm3']>1 and controls['far_mm3']==0
# Direction from the actual transformed cylinder (and explicit origin/end).
lens_start=camera_place(Part.Vertex(V(0,-10.3164,111.962))).Vertexes[0].Point
lens_end=camera_place(Part.Vertex(V(0,-19.7164,111.962))).Vertexes[0].Point
axis=lens_end-lens_start;axis.normalize();target=V(0,-77,1165)-lens_end;target.normalize();dot=axis.dot(target);assert dot>.999999
# Full pair candidate checks, excluding Pi/rail pair already bounded above.
collisions=[];names=list(p)
for i,a in enumerate(names):
 for b in names[i+1:]:
  if {a,b} in [{'Pi5_DIN_Bottom','MontanteA'},{'Pi5_DIN_Top','MontanteA'}]:continue
  aa,bbx=p[a].BoundBox,p[b].BoundBox
  if min(aa.XMax,bbx.XMax)-max(aa.XMin,bbx.XMin)<=.005 or min(aa.YMax,bbx.YMax)-max(aa.YMin,bbx.YMin)<=.005 or min(aa.ZMax,bbx.ZMax)-max(aa.ZMin,bbx.ZMin)<=.005:continue
  vv=vol(p[a],p[b])
  if vv>.1:collisions.append({'a':a,'b':b,'mm3':vv})
checks={'status':'CANDIDATE_GEOMETRY','pi_native_transform':{'rotation_Z_deg':90,'translation_mm':[trans.x,trans.y,trans.z]},'native_clip_width_mm':35.5,'native_clip_local_Y_limits':[-66.848747,-31.34853],'pi_native_fit':fit,'native_clip_controls':controls,'top_camera_direction':[axis.x,axis.y,axis.z],'top_camera_target_dot':dot,'top_camera_lens_endpoint':[lens_end.x,lens_end.y,lens_end.z],'interferences_over_0_1_mm3':collisions,'support_distance_top_mm':p['TopCam_DIN_FrontAndBoom'].distToShape(p['RPiCam_Top_Housing'])[0],'topcollar_interference_mm3':vol(p['TopCam_DIN_FrontAndBoom'],p['Travessa'])+vol(p['TopCam_DIN_Rear'],p['Travessa']),'limitations':['Illustrative composition, not fabrication release','Native Pi clip aligned to actual profile; mesh residuals and retention controls reported','User confirms physical compatibility; no structural/snap-force certification','RPi-camera housing uses Printables301598 reference; board/lens illustrative, not validated CM3 Wide fit','USB and ESP limits remain as documented in r02','No FPC routing/length validation or cable strain relief design']}
(OUT/'verification-build.json').write_text(json.dumps(checks,indent=2));print('CHECKS',json.dumps(checks),flush=True)
assert not collisions,collisions
assert checks['support_distance_top_mm']<.01 and checks['topcollar_interference_mm3']<.1
(OUT/'sources.json').write_text(json.dumps(sources,indent=2))
(OUT/'contract.json').write_text(json.dumps({'vertical':'Z','cameras':['USB lateral generic','ESP lateral source reference','RPi-Cam top pointing down'],'pi_mount':'NATIVE lateral DIN clip, no tray and no external Pi collar','source_assembly':str(OLD/'composicao.FCStd'),'status':'ILLUSTRATIVE_NOT_FOR_FABRICATION'},indent=2))
d.recompute();d.saveAs(str(OUT/'composicao.FCStd'));Import.export([o for o in d.Objects if hasattr(o,'Shape')],str(OUT/'composicao.step'))
mesh=Mesh.Mesh();tris=[];colors=[]
import numpy as np
from PIL import Image,ImageDraw
for n,s in p.items():
 m=MeshPart.meshFromShape(Shape=s,LinearDeflection=.3,AngularDeflection=.4,Relative=False);mesh.addMesh(m)
 c=(.65,.68,.72)
 if any(k in n for k in ['Collar','Saddle','Shelf','Stem','Boom','TopCam_DIN','Foot']):c=(.88,.49,.14)
 if n.startswith('Pi5'):c=(.80,.82,.85)
 if 'PCB' in n or n.startswith('ESP'):c=(.18,.55,.32)
 if 'Lens' in n:c=(.06,.24,.37)
 if 'USB_Generic' in n or 'Belt' in n:c=(.09,.13,.17)
 if n=='PET_REFERENCE':c=(.25,.7,.7)
 for f in m.Facets:tris.append([list(q) for q in f.Points]);colors.append(c)
mesh.write(str(OUT/'composicao.stl'));T=np.array(tris);C=np.array(colors)*255
for label,direction,zmin in [('iso',[1,-1.8,.9],-1),('detalhe',[1,-2,.6],1020),('frente',[0,-1,.1],-1)]:
 mask=T[:,:,2].max(axis=1)>zmin;tt=T[mask];cc=C[mask]
 view=np.array(direction,dtype=float);view/=np.linalg.norm(view);right=np.cross(view,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,view);q=tt@np.stack([right,up,view],axis=1)
 xy=q[:,:,:2];lo=xy.reshape(-1,2).min(0);hi=xy.reshape(-1,2).max(0);wh=hi-lo;W,H=1800,1400;scale=min(1600/wh[0],1140/wh[1]);px=(xy[:,:,0]-lo[0])*scale+(W-wh[0]*scale)/2;py=H-110-(xy[:,:,1]-lo[1])*scale
 normal=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);ln=np.linalg.norm(normal,axis=1);ln[ln==0]=1;normal/=ln[:,None];light=.4+.6*np.abs(normal@np.array([.3,-.4,.866]))
 im=Image.new('RGB',(W,H),(242,245,248));dr=ImageDraw.Draw(im)
 for i in np.argsort(q[:,:,2].mean(1)):dr.polygon([(float(px[i,k]),float(py[i,k])) for k in range(3)],fill=tuple((cc[i]*light[i]).clip(0,255).astype(int)))
 dr.text((35,25),'PNAAT r03 | USB + ESP + RPi-Cam superior | Case Pi no clip DIN nativo',fill=(20,30,40));dr.text((35,55),'Composicao ilustrativa. Sem bandeja Pi. Adaptadores de camera conceituais; nao fabricar.',fill=(20,30,40));im.save(str(OUT/('composicao-'+label+'.png')))
print('EXPORTED',str(OUT),'objects',len(p),'triangles',mesh.CountFacets,flush=True)
