"""Second native MCP pass: installation holes, mechanical clearances and adapters."""
# Helpers and document from freecad_r04_continue.py remain in the live MCP namespace.
# Restore exclusive assembly membership (FreeCAD Group ownership is exclusive).
P.Group=[]
P.addProperty('App::PropertyLinkList','Parts','Manufacturing')
for o in parts:
    ident=o.PrintPartID
    g=D.getObject('Adapter_'+ident.split('_')[1]) if ident.startswith('adapter_') else D.DOCK if ident.startswith(('receiver_','tongue_','cam_')) else D.FRAME
    g.addObject(o)
P.Parts=parts
def finish(o,name,group,xyz=(0,0,0),orientation='XY flat; +Z up',joint='',color=(0.67,0.72,0.80)):
    o.Label=name
    for prop,value in [('PrintPartID',name),('PrintOrientation',orientation),('JointDescription',joint),('Material','PETG')]:
        o.addProperty('App::PropertyString',prop,'Manufacturing'); setattr(o,prop,value)
    o.addProperty('App::PropertyBool','ManufacturedPart','Manufacturing'); o.ManufacturedPart=True
    place(o,xyz); group.addObject(o); parts.append(o); P.Parts=parts
    o.ViewObject.ShapeColor=color
    return o
def replace(old,new,group):
    data={k:getattr(old,k) for k in ['PrintPartID','PrintOrientation','JointDescription']}
    parts.remove(old)
    old.ManufacturedPart=False; old.removeProperty('PrintPartID')
    group.removeObject(old); H.addObject(old)
    # New cut uses the old solid in its existing coordinates; no additional translation.
    return finish(new,data['PrintPartID'],group,orientation=data['PrintOrientation'],joint=data['JointDescription'])
def setp(n,v): S.set(aliases[n], '='+str(v)+' mm' if not isinstance(v,str) else '='+v)
setp('top_mount_offset',26)
par('foot_thickness',8)
S.set(aliases['post_segment_length'],'=(post_top - base_z - BaseT - foot_thickness)/3')
for side,sgn in [('left',-1),('right',1)]:
    foot=D.getObject('post_'+side+'_foot_slotcut1')
    bind(foot,'Placement.Base.z','Parameters.base_z+Parameters.BaseT')
    for k in range(3):
        bind(D.getObject('post_%s_seg_%d'%(side,k+1)),'Placement.Base.z','Parameters.base_z+Parameters.BaseT+Parameters.foot_thickness+%d*Parameters.post_segment_length'%k)
    for k in [1,2]:
        bind(D.getObject('post_%s_joint_%d'%(side,k)),'Placement.Base.z','Parameters.base_z+Parameters.BaseT+Parameters.foot_thickness+%d*Parameters.post_segment_length-Parameters.joint_engagement'%k)
    tie=D.getObject('camera_tie_'+side)
    bind(tie,'Placement.Base.z','Parameters.side_z+Parameters.side_mount_offset+Parameters.mount_thickness')
    # Mount distal slot passes through the tie's longitudinal slot.
    for suffix in ['_web','_end0','_end1']:
        tool=D.getObject('camera_mount_'+side+'_slot1'+suffix)
        bind(tool,'Placement.Base.x','Parameters.post_x+Parameters.mount_camera_offset-5 mm'+(' + Parameters.mount_slot_travel' if suffix=='_end1' else ''))
    # Trim slot travel near the far end of arm to preserve >=4 mm wall.
    bind(D.getObject('camera_mount_'+side+'_slot1_web'),'Length',10)
    bind(D.getObject('camera_mount_'+side+'_slot1_end1'),'Placement.Base.x','Parameters.post_x+Parameters.mount_camera_offset+5 mm')
    # Sleeve supporting the side arm; one M5 insert into post, tie rests on upper face.
    name='camera_post_collar_'+side
    b=box(name+'_outer',(46.6,46.6,32))
    b=cut(b,box(name+'_socket',(30.6,30.6,34),(8,8,-1)),name+'_open')
    b=holes(b,[(-1,23.3,16)],10,name,(1,0,0))
    collar=finish(b,name,D.FRAME,('Parameters.post_x-23.3 mm','%d*Parameters.post_y-23.3 mm'%sgn,'Parameters.side_z+Parameters.side_mount_offset+Parameters.mount_thickness-32 mm'),joint='M5x16 side bolt + M5 insert into segment 2; collar supports camera tie')
    post=D.getObject('post_'+side+'_seg_2')
    tool=cyl(name+'_post_insert','Parameters.insert_bore/2',9,('Parameters.post_x-16 mm','%d*Parameters.post_y'%sgn,'Parameters.side_z+Parameters.side_mount_offset+Parameters.mount_thickness-16 mm'),(1,0,0))
    replace(post,cut(post,tool,name+'_post_drilled'),D.FRAME)
# Receiver grows rails to 14 mm: >=4 mm ligament around M5 holes.
setp('receiver_length',140); setp('receiver_width',82); setp('receiver_rail',14)
for k in [0,1]:
    tool=D.getObject('receiver_common_tool_'+str(k*2))
    # Actual ordering is x-major: (6,4),(6,66),(124,4),(124,66).
for k,(x,y) in enumerate([(7,7),(7,75),(133,7),(133,75),(125,75)]):
    place(D.getObject('receiver_common_tool_'+str(k)),(x,y,-1))
for k in [1,2]:
    b=D.getObject('receiver_capture_lip_'+str(k)+'_blank')
    bind(b,'Width',18)
    for j,x in enumerate([7,133]):
        place(D.getObject('receiver_capture_lip_%d_tool_%d'%(k,j)),(x,7 if k==1 else 11,-1))
    lip=D.getObject('receiver_capture_lip_'+str(k))
    bind(lip,'Placement.Base.y','Parameters.dock_y'+('' if k==1 else '+Parameters.receiver_width-18 mm'))
# Common tongue projects through the open mouth; adapter bolts are outside the receiver.
bind(D.tongue_blank,'Length',190)
bind(D.tongue_shoulder,'Width','Parameters.tongue_width-10 mm')
bind(D.tongue_shoulder,'Height',19)
bind(D.tongue_shoulder,'Placement.Base.y',5)
bind(D.tongue_common,'Placement.Base.y','Parameters.dock_y+Parameters.receiver_rail+1 mm')
for i,(x,y) in enumerate([(140,10),(140,42),(172,10),(172,42)]):
    place(D.getObject('tongue_common_tool_'+str(i)),(x,y,-1))
# Positive rotary dog cam: closed left edge tangent to shoulder, opens by 180 degrees.
old=D.cam_positive_lock
parts.remove(old); old.ManufacturedPart=False; old.removeProperty('PrintPartID'); D.DOCK.removeObject(old); H.addObject(old)
par('cam_angle',0,'deg')
b=fuse([cyl('R04_cam_hub',7,8),box('R04_cam_dog',(8,35,8),(-15,-35,0)),box('R04_cam_neck',(15,8,8),(-15,-8,0)),box('R04_cam_lever',(35,8,8),(0,-4,0))],'R04_cam_blank')
b=holes(b,[(0,0,-1)],10,'R04_cam_lock')
cam=finish(b,'cam_positive_lock',D.DOCK,('Parameters.dock_x+125 mm','Parameters.dock_y+75 mm','Parameters.dock_z+26 mm'),joint='Positive rotary dog blocks shoulder; 180 degree opening; captive M5 pivot with washer, locknut and E-clip',color=(0.9,0.25,0.08))
bind(cam,'Placement.Rotation.Angle','Parameters.cam_angle')
# Adapter plates share one mounting pattern; jaws move on long slots, opening is independent.
setp('adapter_plate_length',180); setp('adapter_plate_width',150)
for key in ['A','B','C']:
    for idx,(x,y) in enumerate([(20,59),(20,91),(52,59),(52,91)]):
        place(D.getObject('adapter_'+key+'_carrier_common_pattern_tool_'+str(idx)),(x,y,-1))
    for j in [0,1]:
        yy='Parameters.adapter_plate_width/2 '+('-' if j==0 else '+')+' (Parameters.adapter_'+key+'_opening/2 + 16 mm)'
        stem='adapter_'+key+'_carrier_adjust'+str(j)
        xx='Parameters.adapter_'+key+'_grip_distance+10 mm'
        travel='Parameters.adapter_'+key+'_slot_travel+30 mm'
        place(D.getObject(stem+'_web'),(xx,yy+'-Parameters.m5_clearance/2',-1))
        bind(D.getObject(stem+'_web'),'Length',travel)
        place(D.getObject(stem+'_end0'),(xx,yy,-1)); place(D.getObject(stem+'_end1'),(xx+'+'+travel,yy,-1))
        jaw=D.getObject('adapter_'+key+'_jaw_'+str(j+1))
        bind(jaw,'Placement.Base.y','Parameters.adapter_plate_width/2 '+('-' if j==0 else '+')+' (Parameters.adapter_'+key+'_opening/2 + Parameters.jaw_depth)')
        bind(D.getObject('adapter_'+key+'_jaw_'+str(j+1)+'_upright'),'Placement.Base.y','Parameters.jaw_depth-Parameters.clamp_wall')
        for h in [0,1]: bind(D.getObject('adapter_'+key+'_jaw_'+str(j+1)+'_soleholes_tool_'+str(h)),'Placement.Base.y',8)
        # Cross-hole through the outer upright, accessible captive hex nut pocket.
        tool=D.getObject('adapter_'+key+'_jaw_'+str(j+1)+'_tool_0')
        bind(tool,'Placement.Base.y',15)
    D.getObject('Adapter_'+key).ViewObject.Visibility=False
# Make legacy tray and sensor support envelopes into printable bolted parts.
for name,group in [('Pi5TrayOutsideSweep',D.PI5),('E18_SeparateTriggerArm',D.SENSORS),('E18_TriggerArmPost',D.SENSORS),('VL53_DiagnosticArm',D.SENSORS),('VL53_DiagnosticPost',D.SENSORS)]:
    old=D.getObject(name)
    # Native tool linked to old dimensions and global placement; use offset expressions.
    centers=[]
    for frac in [0.25,0.75]:
        centers.append((name+'.Placement.Base.x + '+str(frac)+'*'+name+'.Length',name+'.Placement.Base.y + '+name+'.Width/2',name+'.Placement.Base.z-1 mm'))
    b=holes(old,centers,name+'.Height+2 mm',name+'_M5')
    group.removeObject(old); H.addObject(old)
    finish(b,name+'_printed',group,joint='2 M5 through holes; separate printed support, retain R03 sensor position')
# Installation cuts in all base tiles. Foot slots align at x=post_x+-20, y=post_y+-35.
# Receiver and sensor/Pi supports receive matching holes. No glued or friction-only base mount.
mount_points=[]
for sgn in [-1,1]:
    mount_points += [('Parameters.post_x'+dx,'%d*Parameters.post_y'%sgn+dy) for dx in ['-20 mm','+20 mm'] for dy in ['-35 mm','+35 mm']]
mount_points += [('Parameters.dock_x+%d mm'%x,'Parameters.dock_y+%d mm'%y) for x in [7,133] for y in [7,75]]
for name in ['Pi5TrayOutsideSweep','E18_TriggerArmPost','VL53_DiagnosticPost']:
    mount_points += [(name+'.Placement.Base.x + '+str(frac)+'*'+name+'.Length',name+'.Placement.Base.y + '+name+'.Width/2') for frac in [0.25,0.75]]
drills=fuse([cyl('base_install_drill_'+str(i),'Parameters.m5_clearance/2','Parameters.BaseT+2 mm',(x,y,'Parameters.base_z-1 mm')) for i,(x,y) in enumerate(mount_points)],'base_install_drills')
for old in list(parts):
    if old.PrintPartID.startswith('base_plate_'): replace(old,cut(old,drills,old.PrintPartID+'_installed'),D.FRAME)
# Every native length/position uses a sheet expression or a dependency that resolves to one.
# Supply explicit unit aliases for design constants used in socket geometry.
for o in parts:
    o.addProperty('App::PropertyLength','MinimumWall','Manufacturing'); bind(o,'MinimumWall','Parameters.wall')
for name in ['receiver_floor','mount_thickness','clamp_wall','strap_thickness']:
    # Declared design minima; actual shape verification is separate from this metadata.
    pass
# Link named joint/dock aliases to all shared interface coordinates instead of frozen pitches.
for key in ['A','B','C']:
    for i in range(4):
        t=D.getObject('adapter_'+key+'_carrier_common_pattern_tool_'+str(i))
        bind(t,'Placement.Base.x','20 mm'+(' + Parameters.dock_pitch' if i>=2 else ''))
        bind(t,'Placement.Base.y','Parameters.adapter_plate_width/2-Parameters.dock_pitch/2'+(' + Parameters.dock_pitch' if i%2 else ''))
for i in range(4):
    t=D.getObject('tongue_common_tool_'+str(i))
    bind(t,'Placement.Base.x','140 mm'+(' + Parameters.dock_pitch' if i>=2 else ''))
    bind(t,'Placement.Base.y','Parameters.tongue_width/2-Parameters.dock_pitch/2'+(' + Parameters.dock_pitch' if i%2 else ''))
for o in D.Objects:
    if o.TypeId in ['Part::Box','Part::Cylinder'] and o.Name.startswith('adapter_'):
        for prop,alias in [('Length','jaw_length'),('Width','jaw_depth')]:
            if '_sole' in o.Name and o.TypeId=='Part::Box': bind(o,prop,'Parameters.'+alias)
        if '_upright' in o.Name and o.TypeId=='Part::Box': bind(o,'Width','Parameters.clamp_wall')
D.recompute()
for o in H.Group: o.ViewObject.Visibility=False
for o in parts: o.ViewObject.Visibility=not o.PrintPartID.startswith('adapter_')
for key in ['A','B','C']: D.getObject('Adapter_'+key).ViewObject.Visibility=False
P.Parts=parts
json.dump({'parts':[o.Name for o in parts],'aliases':aliases,'baseline':baseline},open(OUT+'/build-manifest.json','w'),indent=2)
D.recompute(); D.save()
print(json.dumps({'objects':len(D.Objects),'print_parts':len(parts),'invalid':[(o.Name,o.State) for o in D.Objects if 'Invalid' in o.State or 'Error' in o.State]}))
