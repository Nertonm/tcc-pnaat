"""Run ONLY with qwen-mm-plugins-freecad.execute_code in the live R03 document.
Native FreeCAD primitives/booleans and spreadsheet expressions; no external CAD kernel.
"""
import FreeCAD as A, Part, json, os, math, shutil
D = A.getDocument('OpticalRigR03OpenPortal')
ROOT = '/home/nerton/tcc-pnaat/github/cad-workspace'
OUT = ROOT + '/exports/concepts/optical-rig-r04'
os.makedirs(OUT + '/parts', exist_ok=True)
S = D.Parameters
assert not D.getObject('R04_BUILD_HISTORY'), 'R04 already constructed; do not duplicate'
shutil.copy2(D.FileName, OUT + '/r03-before-continuation.fcstd')
baseline = {}
for name in ['C_TOP','C_LEFT','C_RIGHT','Product_80x80x240_OPEN']:
    o = D.getObject(name)
    baseline[name] = {'position':list(o.getGlobalPlacement().Base), 'rotation':list(o.getGlobalPlacement().Rotation.Q)}
baseline['cables'] = {o.Name:[list(v.Point) for v in o.Shape.Vertexes] for o in D.CABLES.Group}
json.dump(baseline, open(OUT+'/baseline.json','w'), indent=2)
H = D.addObject('App::DocumentObjectGroup','R04_BUILD_HISTORY')
H.Label = 'R04 native boolean operands (not individual manufactured parts)'
P = D.addObject('App::DocumentObjectGroup','R04_PRINT_PARTS')
Ad = D.addObject('App::DocumentObjectGroup','R04_ADAPTER_ALTERNATIVES')
row = 26
aliases = {}
def par(name, value, unit='mm'):
    global row
    if name in aliases: return 'Parameters.'+name
    S.set('A'+str(row),name)
    S.set('B'+str(row), ('='+value if isinstance(value,str) else '='+str(value)+' '+unit))
    S.setAlias('B'+str(row), name)
    aliases[name] = 'B'+str(row)
    row += 1
    return 'Parameters.'+name
def expr(value):
    if isinstance(value,str): return value
    key = ('v_m' if value < 0 else 'v_p') + str(abs(float(value))).replace('.','_')
    return par(key,value)
def bind(o, prop, val): o.setExpression(prop,expr(val))
def place(o, xyz):
    for axis,val in zip('xyz',xyz): bind(o,'Placement.Base.'+axis,val)
def box(name, size, pos=(0,0,0)):
    o=D.addObject('Part::Box',name); H.addObject(o)
    for p,v in zip(['Length','Width','Height'],size): bind(o,p,v)
    place(o,pos); return o
def cyl(name,r,h,pos=(0,0,0),axis=(0,0,1)):
    o=D.addObject('Part::Cylinder',name); H.addObject(o)
    bind(o,'Radius',r); bind(o,'Height',h); place(o,pos)
    o.Placement.Rotation=A.Rotation(A.Vector(0,0,1),A.Vector(*axis))
    return o
def cut(a,b,name):
    o=D.addObject('Part::Cut',name); o.Base=a; o.Tool=b; o.Refine=True; H.addObject(o); return o
def fuse(parts,name):
    if len(parts)==1: return parts[0]
    o=D.addObject('Part::MultiFuse',name); o.Shapes=parts; o.Refine=True; H.addObject(o); return o
def holes(shape, centers, depth, name, axis=(0,0,1)):
    tools=[cyl(name+'_tool_'+str(i),'Parameters.m5_clearance / 2',depth,c,axis) for i,c in enumerate(centers)]
    return cut(shape,fuse(tools,name+'_tools'),name)
def slot(name,x,y,z,travel,depth,axis='x'):
    r='Parameters.m5_clearance / 2'
    if axis=='x':
        ends=[(x,y,z),('('+expr(x)+') + ('+expr(travel)+')',y,z)]
        web=box(name+'_web',(travel,'Parameters.m5_clearance',depth),(x,'('+expr(y)+') - '+r,z))
    else:
        ends=[(x,y,z),(x,'('+expr(y)+') + ('+expr(travel)+')',z)]
        web=box(name+'_web',('Parameters.m5_clearance',travel,depth),('('+expr(x)+') - '+r,y,z))
    return fuse([web]+[cyl(name+'_end'+str(i),r,depth,p) for i,p in enumerate(ends)],name)
parts=[]
def finish(o,name,group,xyz=(0,0,0),orientation='XY flat; +Z up',joint='',color=(0.67,0.72,0.80)):
    o.Label=name
    o.addProperty('App::PropertyString','PrintPartID','Manufacturing'); o.PrintPartID=name
    o.addProperty('App::PropertyString','PrintOrientation','Manufacturing'); o.PrintOrientation=orientation
    o.addProperty('App::PropertyString','JointDescription','Manufacturing'); o.JointDescription=joint
    o.addProperty('App::PropertyString','Material','Manufacturing'); o.Material='PETG'
    o.addProperty('App::PropertyBool','ManufacturedPart','Manufacturing'); o.ManufacturedPart=True
    place(o,xyz)
    group.addObject(o); P.addObject(o); parts.append(o)
    o.ViewObject.ShapeColor=color
    return o
def q(s): return 'Parameters.'+s
for n,v in [('zero',0),('wall',4),('m5_clearance',5.6),('insert_bore',6.4),('insert_depth',8),('joint_clearance',0.3),('base_z',-60),('post_width',30),('sleeve_wall',8),('joint_engagement',24),('strap_length',50),('strap_width',40),('strap_thickness',8),('hole_edge',12),('dock_x',55),('dock_y',-300),('dock_z',-42),('receiver_length',130),('receiver_width',70),('receiver_floor',6),('receiver_rail',8),('tongue_length',90),('tongue_width',52),('tongue_thickness',8),('dock_pitch',32),('cam_radius',13),('cam_eccentricity',2),('cam_thickness',8),('mount_slot_travel',18),('mount_thickness',16),('mount_width',24),('mount_camera_offset',20),('top_mount_offset',25),('side_mount_offset',16),('adapter_plate_length',140),('adapter_plate_width',90),('adapter_plate_thickness',10),('clamp_wall',8),('clamp_height',55),('jaw_length',50),('jaw_depth',24)]: par(n,v)
for n,v in [('product_x','ProductX'),('product_y','ProductY'),('product_z','ProductZ'),('working_distance',180),('top_height','product_z + working_distance'),('camera_spacing',460),('side_y','camera_spacing / 2'),('side_z',150),('post_y',180),('post_x',90),('post_top','top_height + 40 mm'),('tile_x','BaseX / 4'),('tile_y','BaseY / 4'),('post_segment_length','(post_top - base_z - BaseT) / 3'),('crossbar_segment_length','(2 * post_y + post_width) / 3')]: par(n,v)
for cell,formula in [('B7','top_height'),('B8','side_y'),('B9','side_z'),('B10','post_y'),('B11','post_x'),('B12','post_top')]: S.set(cell,'='+formula)
for key,opening,distance in [('A',65,85),('B',25,55),('C',40,70)]:
    par('adapter_'+key+'_opening',opening); par('adapter_'+key+'_grip_distance',distance)
    par('adapter_'+key+'_slot_travel',30)
D.recompute()
# Remove obsolete manufactured envelopes only. Preserve all optical/reference objects.
for name in ['BaseBelowBelt','Post_Left','Post_Right','CrossbarAboveProduct','Foot_Left','Foot_Right','CameraArm_Left','CameraArm_Right','ArmTie_Left','ArmTie_Right','TopCameraCantilever']:
    D.removeObject(name)
for o in list(D.DOCK.Group):
    if o.TypeId not in ['App::Origin','App::Point']: D.removeObject(o.Name)
place(D.DOCK,(0,0,0))
# Base: 4 x 4 plates; common M5 edge pattern and separate bolted splines underneath.
for i in range(4):
 for j in range(4):
    name='base_plate_%d_%d'%(i+1,j+1)
    body=box(name+'_blank',(q('tile_x'),q('tile_y'),'Parameters.BaseT'))
    pts=[]
    for x in [q('hole_edge'),q('tile_x')+' - '+q('hole_edge')]:
        for y in [q('tile_y')+'/2 - 10 mm',q('tile_y')+'/2 + 10 mm']: pts.append((x,y,-1))
    for y in [q('hole_edge'),q('tile_y')+' - '+q('hole_edge')]:
        for x in [q('tile_x')+'/2 - 10 mm',q('tile_x')+'/2 + 10 mm']: pts.append((x,y,-1))
    # 20 mm service grid, including foot/dock mounting; avoid duplicate edge holes.
    for x in [30,60,90,120]:
        for y in [30,60,100,130]: pts.append((x,y,-1))
    body=holes(body,pts,'Parameters.BaseT + 2 mm',name)
    finish(body,name,D.FRAME,('-Parameters.BaseX/2 + %d*Parameters.tile_x'%i,'-Parameters.BaseY/2 + %d*Parameters.tile_y'%j,q('base_z')),joint='M5 through holes + 50x40x8 bolted joint splines; service grid')
for direction in ['x','y']:
 for i in range(3):
  for j in range(4):
    name='base_joint_%s_%d_%d'%(direction,i+1,j+1)
    if direction=='x':
        size=(q('strap_length'),q('strap_width'),q('strap_thickness'))
        pts=[(x,y,-1) for x in [13,37] for y in [10,30]]
        pos=('-Parameters.BaseX/2 + %d*Parameters.tile_x - Parameters.strap_length/2'%(i+1),'-Parameters.BaseY/2 + (%d+0.5)*Parameters.tile_y - Parameters.strap_width/2'%j,'Parameters.base_z - Parameters.strap_thickness')
    else:
        size=(q('strap_width'),q('strap_length'),q('strap_thickness'))
        pts=[(x,y,-1) for x in [10,30] for y in [13,37]]
        pos=('-Parameters.BaseX/2 + (%d+0.5)*Parameters.tile_x - Parameters.strap_width/2'%j,'-Parameters.BaseY/2 + %d*Parameters.tile_y - Parameters.strap_length/2'%(i+1),'Parameters.base_z - Parameters.strap_thickness')
    body=holes(box(name+'_blank',size),pts,'Parameters.strap_thickness + 2 mm',name)
    finish(body,name,D.FRAME,pos,joint='4 M5x35 + washers + locking nuts; bolts locate both plates')
# Three solid printed post modules per side. Side screws engage inserts in each module.
for side,sign in [('left',-1),('right',1)]:
 for k in range(3):
    name='post_%s_seg_%d'%(side,k+1)
    b=box(name+'_blank',(q('post_width'),q('post_width'),q('post_segment_length')))
    centers=[(-1,'Parameters.post_width/2',z) for z in [12,'Parameters.post_segment_length - 12 mm']]
    # Blind insert sockets enter from -X; printed bore defines adjustable insert specification.
    ts=[cyl(name+'_insert'+str(t),'Parameters.insert_bore/2','Parameters.insert_depth + 1 mm',p,(1,0,0)) for t,p in enumerate(centers)]
    b=cut(b,fuse(ts,name+'_insert_tools'),name)
    finish(b,name,D.FRAME,('Parameters.post_x - Parameters.post_width/2','%d*Parameters.post_y - Parameters.post_width/2'%sign,'Parameters.base_z + Parameters.BaseT + %d*Parameters.post_segment_length'%k),orientation='post axis +Z; print upright, insert bores horizontal',joint='Sleeve socket + M5 screw into blind M5 insert at each end')
 for k in [1,2]:
    name='post_%s_joint_%d'%(side,k)
    b=box(name+'_outer',('Parameters.post_width + 2*Parameters.joint_clearance + 2*Parameters.sleeve_wall','Parameters.post_width + 2*Parameters.joint_clearance + 2*Parameters.sleeve_wall','2*Parameters.joint_engagement'))
    b=cut(b,box(name+'_socket',('Parameters.post_width + 2*Parameters.joint_clearance','Parameters.post_width + 2*Parameters.joint_clearance','2*Parameters.joint_engagement + 2 mm'),(q('sleeve_wall'),q('sleeve_wall'),-1)),name+'_hollow')
    b=holes(b,[(-1,'Parameters.sleeve_wall + Parameters.joint_clearance + Parameters.post_width/2',z) for z in [12,36]],'Parameters.sleeve_wall + 2 mm',name,(1,0,0))
    finish(b,name,D.FRAME,('Parameters.post_x - Parameters.post_width/2 - Parameters.sleeve_wall - Parameters.joint_clearance','%d*Parameters.post_y - Parameters.post_width/2 - Parameters.sleeve_wall - Parameters.joint_clearance'%sign,'Parameters.base_z + Parameters.BaseT + %d*Parameters.post_segment_length - Parameters.joint_engagement'%k),orientation='socket axis +Z; open through bore',joint='2 M5x16 and 2 M5 inserts in adjacent segments; 24 mm engagement per segment')
 # Foot has a 24 mm deep socket and external slots; fix to service grid using a backing plate.
 name='post_'+side+'_foot'
 b=box(name+'_sole',(90,90,8))
 socket=box(name+'_boss',(46.6,46.6,24),(21.7,21.7,8))
 b=fuse([b,socket],name+'_union')
 b=cut(b,box(name+'_socket',(30.6,30.6,25),(29.7,29.7,8)),name+'_hollow')
 b=holes(b,[(-1,45,20)],100,name+'_pin',(1,0,0))
 for h,y in enumerate([10,80]): b=cut(b,slot(name+'_slot'+str(h),15,y,-1,60,10),name+'_slotcut'+str(h))
 finish(b,name,D.FRAME,('Parameters.post_x - 45 mm','%d*Parameters.post_y - 45 mm'%sign,'Parameters.base_z + Parameters.BaseT - 8 mm'),joint='Socket + M5x16 into bottom insert; 4 M5 through slot/plate with backing washers')
# Crossbar: three 130 mm lengths, sleeve joints; seated above the existing post tops.
for k in range(3):
 name='crossbar_seg_'+str(k+1)
 b=box(name+'_blank',(q('post_width'),q('crossbar_segment_length'),q('post_width')))
 ts=[cyl(name+'_insert'+str(t),'Parameters.insert_bore/2','Parameters.insert_depth+1 mm',p,(1,0,0)) for t,p in enumerate([(-1,12,15),(-1,'Parameters.crossbar_segment_length - 12 mm',15)])]
 b=cut(b,fuse(ts,name+'_tools'),name)
 finish(b,name,D.FRAME,('Parameters.post_x-Parameters.post_width/2','-Parameters.post_y-Parameters.post_width/2 + %d*Parameters.crossbar_segment_length'%k,q('post_top')),joint='2 M5 blind insert sockets; external sleeves lock adjacent modules')
for k in [1,2]:
 name='crossbar_joint_'+str(k)
 b=box(name+'_outer',(46.6,48,46.6))
 b=cut(b,box(name+'_socket',(30.6,50,30.6),(8,-1,8)),name+'_hollow')
 b=holes(b,[(-1,y,23.3) for y in [12,36]],10,name,(1,0,0))
 finish(b,name,D.FRAME,('Parameters.post_x - 23.3 mm','-Parameters.post_y-Parameters.post_width/2+%d*Parameters.crossbar_segment_length-24 mm'%k,'Parameters.post_top-8.3 mm'),orientation='rotate +90 deg about X; open sleeve axis vertical',joint='2 M5x16 + 2 M5 inserts in crossbar ends')
# Separate corner cheek brackets use the same upper-post and outer-crossbar insert sockets.
for side,sign in [('left',-1),('right',1)]:
 name='crossbar_'+side+'_corner'
 b=box(name+'_blank',(8,60,60))
 yy=33 if sign==-1 else 27
 b=holes(b,[(-1,30,12),(-1,yy,39)],10,name,(1,0,0))
 finish(b,name,D.FRAME,('Parameters.post_x-Parameters.post_width/2-8 mm','%d*Parameters.post_y-30 mm'%sign,'Parameters.post_top-24 mm'),orientation='rotate +90 deg about Y; 60x60 face on bed',joint='2 M5x16 into post and crossbar blind inserts; two-sided bearing at corner')
# Camera arms retain R03 mounting surfaces. Long slots permit translation and swivel around M5.
for side,sgn in [('left',-1),('right',1),('top',0)]:
 name='camera_mount_'+side
 width='Parameters.mount_width' if sgn else 'Parameters.post_width'
 b=box(name+'_blank',('Parameters.post_x + Parameters.post_width/2 + Parameters.mount_camera_offset',width,'Parameters.mount_thickness' if sgn else 'Parameters.post_top-Parameters.top_height-Parameters.top_mount_offset'))
 for j,x in enumerate([8,85]):
    b=cut(b,slot(name+'_slot'+str(j),x,'('+width+')/2',-1,q('mount_slot_travel'),40),name+'_cut'+str(j))
 z='Parameters.side_z+Parameters.side_mount_offset' if sgn else 'Parameters.top_height+Parameters.top_mount_offset'
 y='%d*Parameters.side_y-Parameters.mount_width/2'%sgn if sgn else '-Parameters.post_width/2'
 finish(b,name,D.FRAME,('-Parameters.mount_camera_offset',y,z),joint='Two 18 mm M5 slots; swivel/translation before tightening; camera requires separate M2 mounting plate')
 if sgn:
    name='camera_tie_'+side
    b=box(name+'_blank',(30,'Parameters.side_y-Parameters.post_y+24 mm',16))
    b=cut(b,slot(name+'_slot',15,12,-1,'Parameters.side_y-Parameters.post_y',18,'y'),name)
    finish(b,name,D.FRAME,('Parameters.post_x-15 mm','-Parameters.side_y-12 mm' if sgn<0 else 'Parameters.post_y-12 mm','Parameters.side_z+Parameters.side_mount_offset'),joint='Longitudinal M5 slot for transverse reach')
# Common receiver: floor, rails and removable capture lips (no roof bridging during print).
rx,ry,rz=q('dock_x'),q('dock_y'),q('dock_z')
b=box('receiver_floor_blank',(q('receiver_length'),q('receiver_width'),q('receiver_floor')))
rails=[box('receiver_rail_'+str(k),(q('receiver_length'),q('receiver_rail'),16),(0,y,q('receiver_floor'))) for k,y in enumerate([0,'Parameters.receiver_width-Parameters.receiver_rail'])]
stop=box('receiver_stop',(8,'Parameters.receiver_width-2*Parameters.receiver_rail',16),(10,q('receiver_rail'),q('receiver_floor')))
b=fuse([b,stop]+rails,'receiver_unbored')
pts=[(x,y,-1) for x in [6,124] for y in [4,66]]+[(117,35,-1)]
b=holes(b,pts,30,'receiver_common')
finish(b,'receiver_common',D.DOCK,(rx,ry,rz),joint='4 M5 through mounting/lip bolts; 1 captive M5 cam pivot; capture lips trap tongue vertically',color=(0.9,0.45,0.08))
for k,y in enumerate([0,58]):
 name='receiver_capture_lip_'+str(k+1)
 b=holes(box(name+'_blank',(q('receiver_length'),12,4)),[(6,4 if k==0 else 8,-1),(124,4 if k==0 else 8,-1)],6,name)
 finish(b,name,D.DOCK,(rx,'Parameters.dock_y + '+str(y)+' mm','Parameters.dock_z+22 mm'),joint='2 shared M5 through receiver and base; 4 mm retaining overhang',color=(0.9,0.45,0.08))
# Tongue: shared tooling / interface dimensions for every adapter; shoulder engaged by cam.
b=box('tongue_blank',(q('tongue_length'),q('tongue_width'),q('tongue_thickness')))
b=fuse([b,box('tongue_shoulder',(10,q('tongue_width'),8),('Parameters.tongue_length-10 mm',0,q('tongue_thickness')))],'tongue_union')
b=holes(b,[(x,y,-1) for x in [20,52] for y in [10,42]],20,'tongue_common')
finish(b,'tongue_common',D.DOCK,('Parameters.dock_x+20 mm','Parameters.dock_y+9 mm','Parameters.dock_z+7 mm'),joint='4 M5 on common 32x32 pattern to any A/B/C adapter; 10 mm end shoulder blocked by cam',color=(0.95,0.65,0.15))
b=cyl('cam_disk',q('cam_radius'),q('cam_thickness'))
b=fuse([b,box('cam_handle',(45,9,8),(0,-4.5,0))],'cam_union')
b=holes(b,[(q('cam_eccentricity'),0,-1)],10,'cam_positive_lock')
finish(b,'cam_positive_lock',D.DOCK,('Parameters.dock_x+115 mm','Parameters.dock_y+35 mm','Parameters.dock_z+15 mm'),joint='M5x45 captive pivot with washer, locknut and retaining E-clip; rotate eccentric to block tongue shoulder',color=(0.9,0.25,0.08))
# Interchangeable A/B/C sample assemblies shown separately, hidden in main optical view.
for idx,key in enumerate(['A','B','C']):
 g=D.addObject('App::Part','Adapter_'+key); Ad.addObject(g)
 par('adapter_'+key+'_display_x',-200+idx*170); par('adapter_'+key+'_display_y',-430)
 place(g,(q('adapter_'+key+'_display_x'),q('adapter_'+key+'_display_y'),q('base_z')))
 name='adapter_'+key+'_carrier'
 b=box(name+'_blank',(q('adapter_plate_length'),q('adapter_plate_width'),q('adapter_plate_thickness')))
 b=holes(b,[(x,y,-1) for x in [20,52] for y in [29,61]],12,name+'_common_pattern')
 for j,y in enumerate([12,78]):
    b=cut(b,slot(name+'_adjust'+str(j),q('adapter_'+key+'_grip_distance'),y,-1,q('adapter_'+key+'_slot_travel'),12),name+'_cut'+str(j))
 finish(b,name,g,joint='Same 32x32 M5 tongue pattern; slotted jaw reach controlled by grip_distance and slot_travel',color=(0.35,0.65,0.85))
 for j in range(2):
    name='adapter_'+key+'_jaw_'+str(j+1)
    b=fuse([box(name+'_sole',(50,24,8)),box(name+'_upright',(50,8,q('clamp_height')),(0,0,8))],name+'_union')
    b=holes(b,[(10,16,-1),(40,16,-1)],10,name+'_soleholes')
    b=holes(b,[(25,-1,38)],10,name,(0,1,0))
    finish(b,name,g,(q('adapter_'+key+'_grip_distance'),'Parameters.adapter_plate_width/2 '+('-' if j==0 else '+')+' Parameters.adapter_'+key+'_opening/2 - 4 mm',10),joint='Two M5 foot bolts; M5 clamp screw with captive nut and separate swivel pad',color=(0.35,0.65,0.85))
    if j==1: b.Placement.Rotation=A.Rotation(A.Vector(0,0,1),180); bind(b,'Placement.Base.x','Parameters.adapter_'+key+'_grip_distance+50 mm')
 g.ViewObject.Visibility=False
# Link all retained primitive dimensions and placement components to spreadsheet aliases.
# Semantic position links first; each remaining local offset is separately editable, not frozen.
semantic={
 'C_TOP':('Parameters.InspectionX','Parameters.CenterY','Parameters.top_height'),
 'C_LEFT':('Parameters.InspectionX','Parameters.CenterY-Parameters.side_y','Parameters.side_z'),
 'C_RIGHT':('Parameters.InspectionX','Parameters.CenterY+Parameters.side_y','Parameters.side_z'),
 'Product_80x80x240_OPEN':('Parameters.InspectionX-Parameters.product_x/2','Parameters.CenterY-Parameters.product_y/2','Parameters.BeltZ'),
 'Pi5TrayOutsideSweep':('Parameters.PiX-20 mm','Parameters.PiY-20 mm','Parameters.base_z+Parameters.BaseT+5 mm'),
 'Pi5_SIMPLIFIED_REFERENCE':('Parameters.PiX-10 mm','Parameters.PiY-8 mm','Parameters.base_z+Parameters.BaseT+17 mm'),
 'Pi5PortsEnvelope':('Parameters.PiX+51 mm','Parameters.PiY-8 mm','Parameters.base_z+Parameters.BaseT+19 mm'),
 'E18_SeparateTriggerArm':('Parameters.TriggerX-12 mm','-Parameters.side_y','45 mm'),
 'E18_TriggerArmPost':('Parameters.TriggerX-10 mm','-Parameters.side_y-10 mm','Parameters.base_z+Parameters.BaseT'),
 'E18_UPSTREAM_TRIGGER':('Parameters.TriggerX','-Parameters.post_y+15 mm','65 mm'),
 'VL53L0X_DIAGNOSTIC':('-100 mm','Parameters.post_y-55 mm','100 mm'),
 'VL53_DiagnosticArm':('-108 mm','Parameters.post_y-55 mm','90 mm'),
 'VL53_DiagnosticPost':('-108 mm','Parameters.post_y+15 mm','Parameters.base_z+Parameters.BaseT'),
 'UPSTREAM_ROLLER_REFERENCE':('Parameters.RollerX','-120 mm','-18 mm'),
 'KY040_UPSTREAM_ROLLER':('Parameters.RollerX-12 mm','-155 mm','-32 mm'),
 'KY040_RollerCoupling':('Parameters.RollerX','-135 mm','-18 mm'),
 'ProductSweep_EXCLUSION':('-Parameters.BaseX/2','Parameters.CenterY-Parameters.product_y/2','Parameters.BeltZ')}
original_names={o['name'] for o in json.load(open(ROOT+'/exports/concepts/optical-rig-r03/r04-before.json'))}
for o in list(D.Objects):
 if o.Name not in original_names: continue
 if o.TypeId in ['Part::Box','Part::Cylinder','Part::Cone']:
    for p in ['Length','Width','Height','Radius','Radius1','Radius2']:
        if p in o.PropertiesList and p not in dict(o.ExpressionEngine): bind(o,p,par(o.Name+'_'+p,getattr(o,p).Value))
 if hasattr(o,'Placement') and (o.TypeId in ['Part::Box','Part::Cylinder','Part::Cone'] or o.Name in semantic):
    for a,val in zip('xyz',o.Placement.Base):
        if o.Name in semantic: v=semantic[o.Name]['xyz'.index(a)]
        elif o.Name.startswith('C_') and ('LightOuter' in o.Name or 'LightOpening' in o.Name):
            cam=o.Name.split('_Light')[0]; v=semantic[cam]['xyz'.index(a)]
        elif o.Name.startswith('PiStandoff'):
            ref={'x':('PiX',170),'y':('PiY',240),'z':('base_z',-60)}[a]
            v='Parameters.'+ref[0]+' + '+par(o.Name+'_offset_'+a,val-ref[1])
        else: v=par(o.Name+'_pos_'+a,val)
        if 'Parameters.' not in v: v=par(o.Name+'_pos_'+a,float(v.replace(' mm','')))
        bind(o,'Placement.Base.'+a,v)
# Record manifest of required bindings; includes operands, assembly placements, not references.
for o in D.Objects:
 if o.TypeId in ['Part::Box','Part::Cylinder'] and o.Name not in original_names:
    pass # all created by helpers with expressions
D.recompute()
for o in H.Group: o.ViewObject.Visibility=False
for o in parts: o.ViewObject.Visibility=True
for key in ['A','B','C']: D.getObject('Adapter_'+key).ViewObject.Visibility=False
for name in ['ProductSweep_EXCLUSION','Camera3_VENDOR_STEP_REFERENCE']: D.getObject(name).ViewObject.Visibility=False
D.Label='Optical rig R04 — printed modular continuation of R03'
S.set('A23','R04 geometric print gates; no physical/FOV/load validation')
S.setColumnWidth('A',320); S.setColumnWidth('B',180)
D.recompute()
json.dump({'parts':[o.Name for o in parts],'aliases':aliases,'baseline':baseline},open(OUT+'/build-manifest.json','w'),indent=2)
D.recompute()
D.save()
A.Gui.activeDocument().activeView().viewAxonometric(); A.Gui.activeDocument().activeView().fitAll()
print(json.dumps({'document':D.Name,'objects':len(D.Objects),'print_parts':len(parts),'aliases_added':len(aliases),'file':D.FileName}))
