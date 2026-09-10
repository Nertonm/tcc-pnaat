"""Run after polish, in the same MCP FreeCAD Python context."""
for side,sgn in [('left',-1),('right',1)]:
    for j in [0,1]:
        stem='post_'+side+'_foot_slot'+str(j)
        bind(D.getObject(stem+'_web'),'Length',70)
        bind(D.getObject(stem+'_web'),'Placement.Base.x',10)
        bind(D.getObject(stem+'_end0'),'Placement.Base.x',10)
        bind(D.getObject(stem+'_end1'),'Placement.Base.x',80)
for i in range(8):
    bind(D.getObject('base_install_drill_'+str(i)),'Placement.Base.x','Parameters.post_x'+('-35 mm' if i%4<2 else '+35 mm'))
# Align sensor post/arm holes with >=4 mm surrounding material.
bind(D.E18_TriggerArmPost,'Height','Parameters.E18_SeparateTriggerArm_pos_z-Parameters.base_z-Parameters.BaseT')
bind(D.E18_SeparateTriggerArm,'Placement.Base.y','-Parameters.side_y-10 mm')
bind(D.E18_SeparateTriggerArm,'Length',24)
bind(D.E18_SeparateTriggerArm,'Width',125)
for name in ['E18_TriggerArmPost','VL53_DiagnosticPost']:
    tools=D.getObject(name+'_M5_tools'); tools.Shapes=tools.Shapes[:1]
    t=D.getObject(name+'_M5_tool_0')
    bind(t,'Placement.Base.x',name+'.Placement.Base.x + '+name+'.Length/2')
for name,ys in [('E18_SeparateTriggerArm',[10,75]),('VL53_DiagnosticArm',[10,77.5])]:
    for i,y in enumerate(ys):
        t=D.getObject(name+'_M5_tool_'+str(i))
        bind(t,'Placement.Base.x',name+'.Placement.Base.x + '+name+'.Length/2')
        bind(t,'Placement.Base.y',name+'.Placement.Base.y + '+expr(y))
# Keep one base hole per sensor post, matching the center bore.
for idx,name in [(14,'E18_TriggerArmPost'),(16,'VL53_DiagnosticPost')]:
    t=D.getObject('base_install_drill_'+str(idx))
    bind(t,'Placement.Base.x',name+'.Placement.Base.x + '+name+'.Length/2')
D.base_install_drills.Shapes=[t for t in D.base_install_drills.Shapes if t.Name not in ['base_install_drill_15','base_install_drill_17']]
# Retained sensor structures have matching top M5 bores; printable feet for stability.
for name,group in [('E18_TriggerArmPost',D.SENSORS),('VL53_DiagnosticPost',D.SENSORS)]:
    n=name+'_base_flange'
    b=holes(box(n+'_blank',(50,50,8)),[(25,25,-1),(10,10,-1),(40,40,-1)],10,n)
    finish(b,n,group,(name+'.Placement.Base.x + '+name+'.Length/2 - 25 mm',name+'.Placement.Base.y + '+name+'.Width/2 - 25 mm','Parameters.base_z+Parameters.BaseT'),joint='M5 center through bolt to post; two M5 flange screws to base')
    # Flanges would intersect the first 8 mm of post; recessed sockets preserve the R03 height.
    socket=box(n+'_socket',(name+'.Length+0.6 mm',name+'.Width+0.6 mm',5),(name+'.Placement.Base.x-0.3 mm',name+'.Placement.Base.y-0.3 mm','Parameters.base_z+Parameters.BaseT+4 mm'))
    # Keep simple four mm bearing floor; post moves up 4 mm and is shortened to retain its top.
    old=parts[-1]; replace(old,cut(old,socket,n+'_socketed'),group)
    bind(D.getObject(name),'Placement.Base.z','Parameters.base_z+Parameters.BaseT+Parameters.wall')
    if name=='E18_TriggerArmPost': bind(D.getObject(name),'Height','Parameters.E18_SeparateTriggerArm_pos_z-Parameters.base_z-Parameters.BaseT-Parameters.wall')
    else: bind(D.getObject(name),'Height','Parameters.VL53_DiagnosticArm_pos_z-Parameters.base_z-Parameters.BaseT-Parameters.wall')
# All referenced support dimensions include the actual sheet expression chain.
# Clamp nuts are captured in hexagonal pockets, separate pad discs prevent point loading.
par('m5_nut_af',8.2)
par('m5_nut_depth',4.2)
for key in ['A','B','C']:
    for j in [1,2]:
        name='adapter_'+key+'_jaw_'+str(j)
        old=D.getObject(name)
        # Native Part::Prism is parametric; orientation points its extrusion into the jaw wall.
        h=D.addObject('Part::Prism',name+'_nut_pocket'); H.addObject(h)
        h.Polygon=6
        bind(h,'Circumradius','Parameters.m5_nut_af / sqrt(3)')
        bind(h,'Height','Parameters.m5_nut_depth')
        # Cutter positioned in the same local jaw frame, then transformed by its assembly placement.
        place(h,('Parameters.adapter_'+key+'_grip_distance+25 mm','Parameters.adapter_plate_width/2 '+('-' if j==1 else '+')+' (Parameters.adapter_'+key+'_opening/2 + Parameters.clamp_wall)',48))
        h.Placement.Rotation=A.Rotation(A.Vector(0,0,1),A.Vector(0,1 if j==1 else -1,0))
        replace(old,cut(old,h,name+'_nut_captured'),D.getObject('Adapter_'+key))
        pad=holes(cyl(name+'_pad_blank',12,8),[(0,0,-1)],10,name+'_pad')
        finish(pad,name+'_pad',D.getObject('Adapter_'+key),(-30,j*30,0),joint='M5 screw and washer into a replaceable contact pad; pad shown in exploded position',color=(0.35,0.65,0.85))
# Explicit constants on native primitives; rotations are sheet-driven where adjustable.
for o in D.Objects:
    if o.TypeId=='Part::Prism':
        for axis in 'xyz':
            if not any(p.lstrip('.')=='Placement.Base.'+axis for p,e in o.ExpressionEngine): bind(o,'Placement.Base.'+axis,0)
# Sources for dimensions not driven by the selected primary aliases remain separately editable
# in Parameters; no static shape generators are involved.
for o in parts:
    if 'MinimumWall' not in o.PropertiesList:
        o.addProperty('App::PropertyLength','MinimumWall','Manufacturing'); bind(o,'MinimumWall','Parameters.wall')
for c in S.getNonEmptyCells():
    if c.startswith('B'):
        v=S.getContents(c).lstrip("'")
        if re.match(r'^-?[0-9.]+ (mm|deg)$',v): S.set(c,'='+v)
D.recompute()
for o in parts:
    if o.PrintPartID.startswith('base_plate_'): o.JointDescription='4-hole M5 bolted spline at each internal edge; dedicated installation bores'
for o in D.Objects:
    if hasattr(o,'Shape') and o.TypeId not in ['App::Part'] and o.Name not in original_names and not getattr(o,'ManufacturedPart',False): o.ViewObject.Visibility=False
for o in parts: o.ViewObject.Visibility=not o.PrintPartID.startswith('adapter_')
for key in ['A','B','C']: D.getObject('Adapter_'+key).ViewObject.Visibility=False
P.Parts=parts
json.dump({'parts':[o.Name for o in parts],'aliases':aliases,'baseline':baseline},open(OUT+'/build-manifest.json','w'),indent=2)
D.recompute(); D.save()
print(json.dumps({'objects':len(D.Objects),'print_parts':len(parts),'bad':[(o.Name,o.State) for o in D.Objects if 'Invalid' in o.State or 'Error' in o.State]}))
