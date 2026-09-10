import FreeCAD as App, FreeCADGui as Gui, Part, Mesh
ROOT=str(Path(__file__).resolve().parents[1])
if 'R05ColumnV6' in App.listDocuments():
    raise RuntimeError('R05ColumnV6 already exists; refusing overwrite')
v6raw={}
for key,rel in [('case','pipiece/stl/case.stl'),('body','light-clamp/stl/body.stl'),('clamp','light-clamp/stl/clamp.stl')]:
    m=Mesh.Mesh(ROOT+'/references/vendor/pi5-case-refs/'+rel)
    if key=='case':
        m.removeDuplicatedPoints(); m.removeDuplicatedFacets(); m.fixIndices(); m.fixDegenerations(); m.harmonizeNormals()
    shape=Part.Shape(); shape.makeShapeFromMesh(m.Topology,0.00001 if key=='case' else 0.01)
    assert len(shape.Shells)==1 and shape.Shells[0].isClosed()
    shape=Part.makeSolid(shape.Shells[0])
    if shape.Volume<0: shape.reverse()
    assert shape.isValid()
    v6raw[key]=shape.removeSplitter() if key=='case' else shape
"""Execute inside the live FreeCAD GUI through MCP. Native Part/OCCT only."""
import FreeCAD as App, FreeCADGui as Gui, Part, Mesh, json, os, hashlib
from FreeCAD import Vector as V
ROOT = str(Path(__file__).resolve().parents[1])
OUT = ROOT + '/exports/concepts/optical-rig-r05'
os.makedirs(OUT, exist_ok=True)
d = App.newDocument('R05ColumnV6')
if len(d.Objects):
    raise RuntimeError('Refusing to replace an existing v6 document')
p = d.addObject('Spreadsheet::Sheet', 'Parameters')
for i, (alias, value) in enumerate([('module_h',95),('wall',4),('ch',20),('col_y',-200),('top_z',540),('side_y',-165),('pi_z',477.1),('jaw_opening',28.7)],1):
    p.set('A'+str(i),alias); p.set('B'+str(i),str(value)); p.setAlias('B'+str(i),alias)
p.set('A18','channel depth'); p.set('B18','10')
p.set('A9','male engagement'); p.set('B9','12')
p.set('A10','female lateral clearance'); p.set('B10','0.2')
p.set('A11','M4 through bore'); p.set('B11','4.4')
p.set('A12','jaw opening = source cylindrical seat diameter; conveyor interface unspecified')
d.recompute()
parts=[]; refs=[]
def box(x,y,z,a,b,c): return Part.makeBox(a,b,c,V(x,y,z))
def cyl(r,h,x,y,z,axis=V(0,0,1)): return Part.makeCylinder(r,h,V(x,y,z),axis)
def add(name,s,color=(0.24,0.53,0.8),role='printed',source='new v6 native Part/OCCT'):
    o=d.addObject('Part::Feature',name); o.Shape=s
    o.addProperty('App::PropertyString','Role'); o.Role=role
    o.addProperty('App::PropertyString','Source'); o.Source=source
    o.ViewObject.ShapeColor=color
    (refs if role=='reference' else parts).append(o)
    return o
def channel(z,h): return box(-10,-205,z,20,10,h)
def female(z): return box(-16.2,-212.2,z-0.01,32.4,24.4,12.21)
def male(z): return box(-16,-212,z,32,24,12)
def crosshole(z): return cyl(2.2,60,-30,-208,z,V(1,0,0))
def bolt_x(name,z,y=-208,x=-24,length=48):
    s=cyl(2,length,x,y,z,V(1,0,0)).fuse(cyl(3.5,4,x-4,y,z,V(1,0,0)))
    add(name,s,(0.65,0.67,0.7),'hardware')
    nut=cyl(4,3,x+length,y,z,V(1,0,0)).cut(cyl(2.1,3,x+length,y,z,V(1,0,0)))
    add(name+'_NutEnvelope',nut,(0.55,0.57,0.6),'hardware')
# Source meshes are repaired and converted by the preceding MCP preparation.
case=v6raw['case'].copy()
case.Placement=App.Placement(V(-0.750000953674316,-209.06999969482422,477.0999984741211),App.Rotation(V(1,1,1),-120))
case=case.cut(channel(419,108))
add('PIPIECE_CASE_VERTICAL',case,(0.76,0.78,0.82),source='pipiece/stl/case.stl; ISC; mesh cleanup + through FPC apertures; XYZ -> YZX')
# Light-clamp inverted: its closed foot attaches to the standard adapter above.
for key,name in [('body','LIGHTCLAMP_BODY'),('clamp','LIGHTCLAMP_JAW')]:
    s=v6raw[key].copy(); s.Placement=App.Placement(V(0,-200,0),App.Rotation(V(1,0,0),180))
    if key=='body':
        for x in [-12,12]: s=s.cut(cyl(2.2,40,x,-220,-7,V(0,1,0)))
    else: s.translate(V(0.4,0,0))
    add(name,s,(0.24,0.25,0.29),source='light-clamp/stl/'+('body.stl' if key=='body' else 'clamp.stl')+'; ISC')
# Replaceable grip-specific adapter; the sleeve above uses only the 60 x 44 M4 interface.
adapter=box(-38,-230,0,76,60,8).fuse(box(-22,-215.5,-12,44,31,12))
adapter=adapter.cut(box(-19.2,-212.7,-12.1,38.4,25.4,12.1)).cut(channel(-13,22))
for x in [-12,12]:
    adapter=adapter.cut(cyl(2.2,40,x,-220,-7,V(0,1,0)))
    sh=cyl(2,31,x,-215.5,-7,V(0,1,0)).fuse(cyl(3.5,4,x,-219.5,-7,V(0,1,0)))
    add('GripCrossBolt_'+str(x).replace('-','N'),sh,(0.6,0.62,0.65),'hardware')
    add('GripCrossNut_'+str(x).replace('-','N'),cyl(4,3,x,-184.5,-7,V(0,1,0)).cut(cyl(2.1,3,x,-184.5,-7,V(0,1,0))),(0.6,0.62,0.65),'hardware')
base=box(-38,-230,8,76,60,12).fuse(male(20)).cut(channel(7,27)).cut(crosshole(26))
for x in [-30,30]:
    for y in [-222,-178]:
        drill=cyl(2.2,24,x,y,-1)
        adapter=adapter.cut(drill); base=base.cut(drill)
        add('BaseM4_%s_%s'%(str(x).replace('-','N'),str(y).replace('-','N')),cyl(2,20,x,y,0).fuse(cyl(3.5,4,x,y,-4)),(0.62,0.64,0.68),'hardware')
        add('BaseNut_%s_%s'%(str(x).replace('-','N'),str(y).replace('-','N')),cyl(4,3,x,y,20).cut(cyl(2.1,3,x,y,20)),(0.62,0.64,0.68),'hardware')
for x in [-30,30]:
    for y in [-222,-178]: base=base.cut(cyl(4.3,4,x,y,20))
add('Grip_QuarterInch_Screw',cyl(3.175,48,-24,-200,-58.175,V(1,0,0)).fuse(cyl(5.5,4,-28,-200,-58.175,V(1,0,0))),(0.6,0.62,0.65),'hardware')
add('GRIP_STANDARD_ADAPTER',adapter.removeSplitter(),(0.88,0.55,0.19))
add('BASE_SLEEVE',base.removeSplitter(),(0.88,0.55,0.19))
# Four new continuous modules below the high standing case; no legacy geometry imported.
for i in range(4):
    z=20+95*i
    s=box(-20,-216,z,40,32,95).fuse(male(z+95))
    s=s.cut(female(z)).cut(channel(z-1,110)).cut(crosshole(z+6)).cut(crosshole(z+101))
    if i==3:
        s=s.fuse(box(20,-216,323,68,16,34)).cut(cyl(2.75,20,55,-218,340,V(0,1,0)))
    o=add('MODULE_%d'%(i+1),s.removeSplitter(),(0.18+0.04*i,0.44+0.04*i,0.68+0.04*i))
    o.addProperty('App::PropertyLength','Pitch'); o.setExpression('Pitch','Parameters.module_h')
    o.addProperty('App::PropertyLength','Engagement'); o.Engagement=12
    bolt_x('JointM4_%d'%i,z+6)
# Socket and seating cup below case; upper collar rests on real vendor case rim.
lower=box(-20,-216,400,40,32,16).fuse(box(-37,-220.5,416,74,41,29)).cut(box(-32.92,-216.77,420,65.84,33.54,26))
lower=lower.cut(female(400)).cut(channel(399,48)).cut(crosshole(406))
add('CASE_LOWER_COLLAR',lower.removeSplitter(),(0.88,0.55,0.19))
bolt_x('JointM4_4',406)
case_top=524.8499984741211
cap=box(-37,-220.5,505,74,41,35).cut(box(-32.92,-216.77,504.9,65.84,33.54,case_top-504.9))
cap=cap.fuse(male(540)).cut(channel(504,50)).cut(crosshole(546))
add('CASE_TOP_COLLAR',cap.removeSplitter(),(0.88,0.55,0.19))
cross=box(-20,-216,540,40,32,54).fuse(box(-20,-200,580,40,220,14))
cross=cross.cut(female(540)).cut(channel(539,57)).cut(crosshole(546))
cross=cross.cut(box(-10,-205,582,20,186,10)).cut(box(-10,-29,579,20,10,16))
cross=cross.cut(cyl(2.75,20,0,0,578))
add('CROSSBAR_C_TOP',cross.removeSplitter(),(0.2,0.5,0.72))
bolt_x('JointM4_5',546)
# Context objects are not manufactured pieces.
add('BOTTLE_H370_D120',cyl(60,370,0,0,0),(0.3,0.85,0.5),'reference').ViewObject.Transparency=80
add('BACKLIGHT_BEHIND_BOTTLE',box(-80,100,20,160,8,360),(0.95,0.92,0.65),'reference').ViewObject.Transparency=65
datum=d.addObject('App::FeaturePython','C_TOP'); datum.addProperty('App::PropertyVector','OpticalCenter'); datum.OpticalCenter=V(0,0,540)
datum.addProperty('App::PropertyVector','LookDirection'); datum.LookDirection=V(0,0,-1)
datum.addProperty('App::PropertyString','Status'); datum.Status='Target datum; official CM3 refinement after gates'
probe=channel(8,588).fuse(box(-10,-205,582,20,186,10)).fuse(box(-10,-29,548,20,10,47))
add('FPC_PROBE_20x10',probe,(1.0,0.25,0.7),'reference').ViewObject.Visibility=False
d.recompute(); Gui.activeDocument().activeView().viewAxonometric(); Gui.activeDocument().activeView().fitAll()
d.saveAs(OUT+'/optical-rig-r05-column-v6.fcstd')
print('BUILT',d.Name,len(d.Objects),'physical',len(parts))
print('INVALID',[(o.Name,len(o.Shape.Solids)) for o in parts if not o.Shape.isValid()])
