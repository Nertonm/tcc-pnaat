"""Last native assembly pass, run through MCP after the first validation."""
# Helper functions remain from the build session; document remains OpticalRigR03OpenPortal.
for side,sgn in [('left',-1),('right',1)]:
    prefix='camera_post_collar_'+side
    bind(D.getObject(prefix+'_outer'),'Length',62.6)
    bind(D.getObject(prefix+'_outer'),'Width',62.6)
    bind(D.getObject(prefix+'_socket'),'Placement.Base.x',16)
    bind(D.getObject(prefix+'_socket'),'Placement.Base.y',16)
    bind(D.getObject(prefix),'Placement.Base.x','Parameters.post_x-31.3 mm')
    bind(D.getObject(prefix),'Placement.Base.y','%d*Parameters.post_y-31.3 mm'%sgn)
    bind(D.getObject(prefix+'_tool_0'),'Placement.Base.y',31.3)
    bind(D.getObject(prefix+'_tool_0'),'Height',18)
    old=D.getObject(prefix)
    drill=cyl(prefix+'_vertical_insert','Parameters.insert_bore/2',9,('Parameters.post_x','%d*(Parameters.post_y+23.3 mm)'%sgn,'Parameters.side_z+Parameters.side_mount_offset+Parameters.mount_thickness+1 mm'),(0,0,-1))
    new=replace(old,cut(old,drill,prefix+'_tie_insert'),D.FRAME)
    new.JointDescription='M5x25 lateral insert screw to post + M5x25 vertical insert screw through tie slot; 16 mm sleeve wall'
# Pi tray stands off the base by the R03 five mm; two annular spacers support its M5 bolts.
for i,frac in enumerate([0.25,0.75]):
    name='pi_tray_spacer_'+str(i+1)
    b=holes(cyl(name+'_blank',8,5),[(0,0,-1)],7,name)
    finish(b,name,D.PI5,('Pi5TrayOutsideSweep.Placement.Base.x + '+str(frac)+'*Pi5TrayOutsideSweep.Length','Pi5TrayOutsideSweep.Placement.Base.y+Pi5TrayOutsideSweep.Width/2','Parameters.base_z+Parameters.BaseT'),joint='M5 through tray, 5 mm annular spacer and base; 5.2 mm radial wall')
# Schematic fastener reference: one physically separate captive pivot, not a printed part.
hw=D.addObject('App::DocumentObjectGroup','R04_HARDWARE_REFERENCES')
pivot=cyl('M5_CAPTIVE_CAM_PIVOT_REFERENCE',2.5,65,('Parameters.dock_x+125 mm','Parameters.dock_y+75 mm','Parameters.dock_z+34 mm-65 mm'))
hw.addObject(pivot); pivot.Label='M5x65 captive pivot — purchased hardware reference'
pivot.ViewObject.ShapeColor=(0.25,0.25,0.25)
for c in S.getNonEmptyCells():
    if c.startswith('B'):
        val=S.getContents(c).lstrip("'")
        if re.match(r'^-?[0-9.]+ (mm|deg)$',val):S.set(c,'='+val)
D.recompute()
for o in D.Objects:
    if hasattr(o,'Shape') and o.TypeId!='App::Part' and o.Name not in original_names and not getattr(o,'ManufacturedPart',False):o.ViewObject.Visibility=False
for o in parts:o.ViewObject.Visibility=not o.PrintPartID.startswith('adapter_')
pivot.ViewObject.Visibility=True
P.Parts=parts
D.recompute();D.save()
print('mount fasteners complete',len(parts),'parts')
