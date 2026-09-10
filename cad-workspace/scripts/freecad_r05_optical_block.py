"""Run only with execute_code in the live FreeCAD MCP GUI. No CadQuery.

Derivative: John Cole PiPiece.jscad / case.stl (ISC); James Pilgrim
pi-camera-mounts (GPL-2.0). New adapter geometry distributed under GPL-2.0.
"""
import FreeCAD as App, FreeCADGui as Gui, Part, Mesh, math, os, json
from FreeCAD import Vector as V
ROOT = '/home/nerton/tcc-pnaat/github/cad-workspace'
OUT = ROOT + '/exports/concepts/optical-rig-r05'
d = App.getDocument('R05OpticalBlock')
App.setActiveDocument(d.Name)
assert d.getObject('RigidFrame') is None, 'Refusing to overwrite an existing build'
sources = {k: d.getObject(k).Shape.copy() for k in ['Pi5_Official','CM3_Wide_Official','CM3_Std_Official']}
case = d.Pipiece_Source.Shape.copy()
for o in d.Objects: o.Visibility = False
printed=[]; hardware=[]; context=[]
def box(x,y,z,a,b,c): return Part.makeBox(a,b,c,V(x,y,z))
def cyl(r,h,p,axis=V(0,0,1)): return Part.makeCylinder(r,h,p,axis)
def add(name,s,color=(0.25,0.51,0.69),role='printed',source='R05 optical block; GPL-2.0 adapter'):
    o=d.addObject('PartDesign::Feature',name); o.Shape=s
    o.addProperty('App::PropertyString','Role'); o.Role=role
    o.addProperty('App::PropertyString','Source'); o.Source=source
    o.ViewObject.ShapeColor=color; o.ViewObject.LineColor=(0.15,0.17,0.2)
    if role=='printed': printed.append(o)
    elif role=='hardware': hardware.append(o)
    elif role=='context': context.append(o)
    return o
def move(s,p,r=App.Rotation()):
    t=s.copy(); t.Placement=App.Placement(p,r).multiply(t.Placement); return t
def bolt(name,r,length,p,axis=V(0,0,1)):
    # Shank starts at p; head rests on starting mating face.
    return add(name,cyl(r,length,p,axis).fuse(cyl(r*1.8,2*r,p-axis*(2*r),axis)),(0.66,0.68,0.71),'hardware')
def nut(name,r,p,axis=V(0,0,1)):
    a=App.Rotation(V(0,0,1),axis)
    pts=[V(1.9*r*math.cos(i*math.pi/3),1.9*r*math.sin(i*math.pi/3),0) for i in range(7)]
    s=Part.Face(Part.makePolygon(pts)).extrude(V(0,0,1.5*r)).cut(cyl(r+0.1,1.5*r,V()))
    return add(name,move(s,p,a),(0.56,0.58,0.61),'hardware')
params=d.addObject('Spreadsheet::Sheet','Parameters')
for i,(n,v) in enumerate([('CableNominal',200),('CableWorst',199),('RequiredReserve',20),('DesignBendRadius',12),('BottleHeight',370),('BottleDiameter',120),('PiBoardZ',350),('TopLensZ',397),('SideLensZ',300)],1):
    params.set('A'+str(i),n); params.set('B'+str(i),str(v)); params.setAlias('B'+str(i),n)
params.set('A12','DesignBendRadius is a design assumption, not a vendor rating')
# PiPiece source shell: preserve exterior, vent slots and original port topology.
# Recut internal clearance, rebuild bosses from the official STEP hole pattern.
case=case.cut(box(-46,-29,-3,89,58,38))
case=case.fuse(box(-46,-28.8,-4.5,89,57.6,1.5))
for x in [3.5,61.5]:
    for y in [3.5,52.5]:
        q=V(x-45,y-28,-4.5)
        case=case.fuse(cyl(2.75,4.53,q)).cut(cyl(1.35,8,q-V(0,0,1)))
# Access tunnels are aligned to actual port solids, expanded for plug bodies.
port_specs=[('USB_LAN',box(20,-28,-1,32,58,23)),
            ('HDMI_USBC',box(-41,-36,-1,39,10,10)),
            ('MICROSD',box(-61,-10,-5,21,22,7))]
for _,s in port_specs: case=case.cut(s)
# The roof is open: cooler + fan inlet remain accessible. Conservative envelope.
cooler_local=box(-39,-9,1.31,57,34,27)
case=case.cut(cooler_local)
pi_rot=App.Rotation(V(0,0,1),-90); case_pos=V(0,-65,350)
case=move(case,case_pos,pi_rot)
pi=move(sources['Pi5_Official'],V(-28,-20,350),pi_rot)
pi_obj=add('Pi5_Central',pi,(0.18,0.47,0.27),'electronics','Official rpi-5b_no_graphics.step')
cooler=add('ActiveCooler_Keepout',move(cooler_local,case_pos,pi_rot),(0.87,0.34,0.3),'keepout','Conservative design envelope; not an official cooler STEP')
cooler.Visibility=False
for y in [-100,-30]:
    case=case.fuse(box(30,y-6,342.5,18,12,6)).cut(cyl(2.2,15,V(41,y,338)))
case_obj=add('Pipiece_Pi5_Case',case.removeSplitter(),(0.77,0.79,0.82),source='John Cole pipiece/stl/case.stl + PiPiece.jscad PiCase; ISC; cavity, bosses, port cuts, mounting ears')
for x in [3.5,61.5]:
    for y in [3.5,52.5]:
        q=V(-28,-20,350)+pi_rot.multVec(V(x,y,0))
        bolt('Pi_M25_%s_%s'%(x,y),1.25,7,q+V(0,0,1.4),V(0,0,-1))
# A single rigid, printable frame underneath the case and both gimbals.
frame=box(-36,-116,336.5,88,99,6)
frame=frame.fuse(box(40,-84,280,12,14,165))
frame=frame.fuse(box(40,-84,437,12,149,8))
frame=frame.fuse(box(-55,45,437,107,20,8))
frame=frame.fuse(box(-55,-78,280,107,8,40))
for y in [-100,-30]:
    frame=frame.cut(cyl(2.2,15,V(41,y,334)))
    bolt('Case_Frame_M4_'+str(abs(y)),2,14,V(41,y,348.5),V(0,0,-1))
    nut('Case_Frame_Nut_'+str(abs(y)),2,V(41,y,333.5))
frame=frame.cut(cyl(2.75,15,V(0,-95,331)))
bolt('Elevation_M5',2.5,18,V(0,-95,343),V(0,0,-1))
# Vendor source gimbal, preserving both M4 tilt ears and M5 pan bore.
cradle=App.getDocument('Camera_Mount___Bottom').Fillet.Shape.copy()
cradle=cradle.transformGeometry(App.Placement(V(0,0,35),App.Rotation(V(1,0,0),90)).toMatrix())
cradle=move(cradle,V(),App.Rotation(V(0,0,1),90))
# New carrier interfaces to unchanged 58 mm-wide vendor gimbal.
plate=box(-16,-28.8,7,32,57.6,3)
for y in [-28.8,25]: plate=plate.fuse(box(-6,y,-5,12,3.8,15))
plate=plate.cut(cyl(2.25,70,V(0,-35,0),V(0,1,0)))
# The detachable CM3 cassette uses M2.5 away from the actual 2.2 mm PCB holes.
for x in [-21,21]: plate=plate.cut(cyl(1.35,8,V(0,x,5)))
# Ribbon passes out +local X; open mouth avoids original HQ backplate interference.
plate=plate.cut(box(7,-10,6.9,18,20,4))
for x,y in [(-12.4,-10.5),(0.1,-10.5),(-12.4,10.5),(0.1,10.5)]: plate=plate.cut(cyl(1.1,6,V(x,y,6)))
# Cassette is derived from PiPiece CameraCase: back wall, discrete pads, ribbon cut.
cassette=box(-15,-24,5.5,30,48,1.5)
cassette=cassette.cut(box(4,-12,5.4,22,24,2))
holes=[(-12.4,-10.5),(0.1,-10.5),(-12.4,10.5),(0.1,10.5)]
for x,y in holes:
    cassette=cassette.fuse(cyl(2,1.72548,V(x,y,3.77452)))
    cassette=cassette.cut(cyl(1.1,5,V(x,y,3)))
for x in [-21,21]: cassette=cassette.cut(cyl(1.35,5,V(0,x,4)))
# Top native X->-Y; side native X->+Z. Both ribbons bend in planes YZ.
top_rot=App.Rotation(V(0,0,1),-90)
side_rot=App.Rotation(V(0,0,1),90).multiply(App.Rotation(V(1,0,0),90))
# Explicit basis side: X->Z, Y->-X, Z->-Y.
side_rot=App.Rotation(V(0,0,1),V(-1,0,0),V(0,-1,0),'ZXY')
camera_info={}
for tag,origin,rot,key in [('TOP',V(-19.5,55,402),top_rot,'CM3_Wide_Official'),('SIDE',V(-19.5,-35,300),side_rot,'CM3_Std_Official')]:
    cr=add('C_'+tag+'_VendorGimbal',move(cradle,origin,rot),(0.32,0.35,0.4),source='James Pilgrim pi-camera-mounts / Camera Mount - Bottom.FCStd / Fillet; GPL-2.0; original pan/tilt geometry')
    add('C_'+tag+'_TiltCarrier',move(plate,origin,rot),(0.84,0.54,0.22))
    add('C_'+tag+'_CM3_Backplate',move(cassette,origin,rot),(0.86,0.65,0.28),source='PiPiece CameraCase topology (ISC), CM3 STEP hole pattern, GPL-2.0 mating carrier')
    ref=move(move(sources[key],V(-14.4,-12.5,3.805)),origin,rot)
    co=add('C_'+tag+'_OfficialCM3',ref,(0.19,0.49,0.25),'electronics','Official '+key+' STEP')
    lens=origin+rot.multVec(V(0,0,-5 if tag=='TOP' else -3.845))
    direction=rot.multVec(V(0,0,-1))
    for prop,val in [('LensFrontCenter',lens),('LookDirection',direction)]:
        co.addProperty('App::PropertyVector',prop); setattr(co,prop,val)
    # Optical guard ring: variant-specific depth and opening, outside STEP lens envelope.
    zfront=-5.8 if tag=='TOP' else -4.6
    guard=box(-16,-15,zfront,31,30,1.5).cut(box(-6,-6,zfront-1,12,12,4))
    for x,y in holes:
        guard=guard.fuse(cyl(2,3.10396-zfront,V(x,y,zfront)))
        guard=guard.cut(cyl(1.1,12,V(x,y,zfront-1)))
    # Remove full sensor keepout behind the front ring, preserve corner standoffs.
    guard=guard.cut(box(-5.8,-5.8,zfront+1.5,11.6,11.6,15))
    add('C_'+tag+'_OpticalWindow',move(guard.removeSplitter(),origin,rot),(0.22,0.25,0.29),source='PiPiece housing topology; CM3 '+('Wide' if tag=='TOP' else 'Standard')+' STEP envelope + 12 mm window')
    for x,y in holes:
        q=origin+rot.multVec(V(x,y,zfront))
        bolt('C_'+tag+'_PCB_M2_'+str(x)+'_'+str(y),1,18,q,rot.multVec(V(0,0,1)))
        nut('C_'+tag+'_PCB_Nut_'+str(x)+'_'+str(y),1,origin+rot.multVec(V(x,y,10)),rot.multVec(V(0,0,1)))
    for x in [-21,21]:
        q=origin+rot.multVec(V(0,x,5.5))
        bolt('C_'+tag+'_Cassette_M25_'+str(x),1.25,7,q,rot.multVec(V(0,0,1)))
        nut('C_'+tag+'_Cassette_Nut_'+str(x),1.25,origin+rot.multVec(V(0,x,10)),rot.multVec(V(0,0,1)))
    for side in [-1,1]:
        axis=rot.multVec(V(0,-side,0))
        bolt('C_'+tag+'_Tilt_M4_'+str(side),2,10,origin+rot.multVec(V(0,side*33,0)),axis)
        nut('C_'+tag+'_Tilt_Nut_'+str(side),2,origin+rot.multVec(V(0,side*25,0)),axis)
    pan=origin+rot.multVec(V(0,0,35))
    axis=rot.multVec(V(0,0,1))
    frame=frame.cut(cyl(2.75,22,pan-axis*5,axis))
    bolt('C_'+tag+'_Pan_M5',2.5,19,pan+axis*8,-axis)
    # Two locking M3 dowel screws stop pan after positioning; no friction-only claim.
    for xx in [-7,7]:
        q=origin+rot.multVec(V(xx,0,35))
        drill=cyl(1.7,18,q-axis*5,axis)
        frame=frame.cut(drill); cr.Shape=cr.Shape.cut(drill)
        bolt('C_'+tag+'_PanLock_M3_'+str(xx),1.5,14,q+axis*8,-axis)
    camera_info[tag]={'origin':origin,'rotation':rot,'lens':lens,'direction':direction,
                      'connector':origin+rot.multVec(V(23.492-14.4,0,3.805+1.315))}
frame_obj=add('RigidFrame',frame.removeSplitter(),(0.23,0.47,0.63))
# Context only: removable elevated block on a simple bench pedestal.
post=add('Elevation_PLACEHOLDER',box(-12,-107,12,24,24,324.5).cut(cyl(2.75,18,V(0,-95,321))),(0.45,0.46,0.48),'context','Primitive support only; not designed or included in printed-parts gate')
foot=add('BenchFoot_PLACEHOLDER',box(-65,-145,0,130,100,12),(0.48,0.49,0.5),'context','Primitive bench foot, D-01 sliding rail context; dimensions provisional')
bottle=add('Bottle_Envelope_H370_D120',cyl(60,340,V(-19.5,55,0)).fuse(Part.makeCone(60,15,20,V(-19.5,55,340))).fuse(cyl(15,10,V(-19.5,55,360))),(0.35,0.78,0.62),'context','PET maximum envelope H370 D120; shape illustrative')
bottle.ViewObject.Transparency=82
# Directed centre rays (not FOV) distinguish camera orientation from coverage.
for tag,data in camera_info.items():
    end=data['lens']+data['direction']*(32 if tag=='TOP' else 30)
    add('C_'+tag+'_Axis',Part.makeLine(data['lens'],end),(0.95,0.23,0.23),'datum').ViewObject.LineWidth=3
d.recompute()
Gui.activeDocument().activeView().viewAxonometric(); Gui.activeDocument().activeView().fitAll()
print('BUILT',d.Name,len(d.Objects),'printed',len(printed))
print('CAMERA',[(k,tuple(v['connector']),tuple(v['lens']),tuple(v['direction'])) for k,v in camera_info.items()])
print('INVALID',[(o.Name,o.Shape.isValid(),len(o.Shape.Solids)) for o in printed if not o.Shape.isValid() or len(o.Shape.Solids)!=1])
