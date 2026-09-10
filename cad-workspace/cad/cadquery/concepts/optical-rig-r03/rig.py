import json, math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[4]
CFG=ROOT/'data/concepts/optical-rig-r03-contract.json'
OUT=ROOT/'exports/concepts/optical-rig-r03'

def box(n,size,pos,role):
 s=cq.Workplane('XY').box(*size).translate((pos[0]+size[0]/2,pos[1]+size[1]/2,pos[2]+size[2]/2)).val()
 return n,s,role

def rod_between(n,a,b,r,role):
 a=cq.Vector(*a); b=cq.Vector(*b); v=b-a
 return n,cq.Solid.makeCylinder(r,v.Length,a,v.normalized()),role

def product_wire():
 e=(80,80,240); x0=-40; y0=-40; z0=0; t=2
 ss=[]
 for y in (y0,y0+e[1]-t): ss.append(cq.Workplane('XY').box(e[0],t,e[2]).translate((x0,y,z0+e[2]/2)).val())
 for x in (x0,x0+e[0]-t): ss.append(cq.Workplane('XY').box(t,e[1],e[2]).translate((x,y0,z0+e[2]/2)).val())
 for z in (z0,z0+e[2]-t): ss.append(cq.Workplane('XY').box(e[0],e[1],t).translate((x0,y0,z+t/2)).val())
 return cq.Compound.makeCompound(ss)

def fov_cone(pos,axis,length=300,half_deg=27):
 p=cq.Vector(*pos); a=cq.Vector(*axis); rad=length*math.tan(math.radians(half_deg))
 return cq.Solid.makeCone(2,rad,length,p,a)

def build():
 c=json.loads(CFG.read_text()); parts=[]
 parts += [box('BASE',(600,520,18),(-300,-260,-18),'structure')]
 parts += [box('BELT',(600,160,20),(-300,-80,0),'belt')]
 parts += [('PRODUCT_ENVELOPE',product_wire(),'product_envelope')]
 parts += [box('POST_LEFT',(30,30,430),(-15,-210,0),'structure'),box('POST_RIGHT',(30,30,430),(-15,180,0),'structure')]
 parts += [box('CROSSBAR',(30,420,30),(-15,-210,430),'structure')]
 # optical camera bodies and mounts, all clearly named
 for name,pos,axis in [('C_TOP',(0,0,420),(0,0,-1)),('C_LEFT',(0,-230,150),(0,1,0)),('C_RIGHT',(0,230,150),(0,-1,0))]:
  parts += [box(name,(42,40,12),(pos[0]-21,pos[1]-20,pos[2]-6),'camera')]
  parts += [rod_between(name+'_AXIS',pos,(pos[0]+axis[0]*150,pos[1]+axis[1]*150,pos[2]+axis[2]*150),1,'optical_axis')]
  parts += [(name+'_FOV',fov_cone(pos,axis),'fov')]
  # mount is a small plate beside the camera, not a wall
  parts += [box(name+'_MOUNT',(60,60,8),(pos[0]-30,pos[1]-30,pos[2]-20),'camera_mount')]
 # lights close to each camera
 parts += [box('LIGHT_TOP',(70,20,8),(-35,-10,380),'lighting')]
 parts += [box('LIGHT_LEFT',(20,70,8),(-10,-205,110),'lighting')]
 parts += [box('LIGHT_RIGHT',(20,70,8),(-10,135,110),'lighting')]
 # Pi base, not portal
 parts += [box('PI5_TRAY',(120,90,10),(-240,250,0),'pi')]
 # open cable routes, following posts to base
 for n,a,b in [('CSI_TOP',(0,0,420),(-200,0,0)),('CSI_LEFT',(0,-230,150),(-200,-180,0)),('USB_RIGHT',(0,230,150),(-200,180,0))]: parts += [rod_between(n+'_CABLE',a,b,3,'cable')]
 # dock at base, with positive lock indicated
 parts += [box('RECEIVER',(120,160,12),(-60,-80,-12),'receiver'),box('TONGUE',(90,40,8),(-45,-20,0),'tongue'),box('CAM_LOCK',(20,20,20),(45,-10,0),'retention')]
 # sensors upstream, away from optical center
 parts += [box('E18_TRIGGER',(55,30,30),(-180,-130,80),'trigger'),box('VL53_DIAGNOSTIC',(35,25,20),(-150,100,100),'diagnostic'),box('KY040_ENCODER',(50,35,30),(-250,-20,30),'encoder')]
 return c,parts

def main():
 c,parts=build(); OUT.mkdir(parents=True,exist_ok=True); shapes=[]; manifest=[]
 for n,s,r in parts:
  assert s.isValid(),n; shapes.append(s); manifest.append({'name':n,'role':r,'bounds_mm':[s.BoundingBox().xmin,s.BoundingBox().ymin,s.BoundingBox().zmin,s.BoundingBox().xmax,s.BoundingBox().ymax,s.BoundingBox().zmax]})
 cq.exporters.export(cq.Compound.makeCompound(shapes),str(OUT/'optical-rig-r03-open-portal.step'))
 (OUT/'components.json').write_text(json.dumps({'status':c['status'],'coordinate_system':c['coordinate_system'],'components':manifest},indent=2))
 print('generated',len(parts),OUT/'optical-rig-r03-open-portal.step')
if __name__=='__main__': main()
