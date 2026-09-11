"""Execute through FreeCAD MCP in OpticalRigR03OpenPortal. Raises on any failed gate.
Outputs oriented per-part STEP/STL and measured validation.json before asserting.
Reference hardware/datums/FOV and boolean tools are not manufactured parts.
"""
import FreeCAD as A, Part, Mesh, MeshPart, json, os, math, re
D=A.getDocument('OpticalRigR03OpenPortal')
ROOT='<CAD_WORKSPACE>'
OUT=ROOT+'/exports/concepts/optical-rig-r04'
S=D.Parameters
page_states=[]
for pg in D.Objects:
    if pg.TypeId=='TechDraw::DrawPage' and 'KeepUpdated' in pg.PropertiesList:
        page_states.append((pg,pg.KeepUpdated));pg.KeepUpdated=False
parts=list(D.R04_PRINT_PARTS.Parts)
baseline=json.load(open(OUT+'/baseline.json'))
result={'document':D.Name,'file':D.FileName,'object_count':len(D.Objects),'print_part_count':len(parts),'validation_scope':'Native geometry, expression dependency, oriented build volume. No physical/FOV/load/safety validation.'}
def dims(s): return [getattr(s.BoundBox,k+'Length') for k in 'XYZ']
def global_shape(o):
    s=o.Shape.copy()
    s.Placement=o.getGlobalPlacement().multiply(o.Placement.inverse()).multiply(s.Placement)
    return s
def bindings():
    errors=[]; checked=[]
    for o in D.Objects:
        props=[]
        if o.TypeId in ['Part::Box','Part::Cylinder','Part::Cone','Part::Prism']:
            props=['Placement.Base.'+k for k in 'xyz']+[k for k in ['Length','Width','Height','Radius','Radius1','Radius2','Circumradius'] if k in o.PropertiesList]
        elif o.Name in ['C_TOP','C_LEFT','C_RIGHT','Adapter_A','Adapter_B','Adapter_C','DOCK'] or getattr(o,'ManufacturedPart',False): props=['Placement.Base.'+k for k in 'xyz']
        ex={p.lstrip('.'):e for p,e in o.ExpressionEngine}
        for prop in props:
            val=ex.get(prop,'')
            checked.append([o.Name,prop,val])
            # Expressions may reference another native object's sheet-driven dimensions.
            if not val or not ('Parameters.' in val or any(n+'.' in val for n in ['Height','Pi5TrayOutsideSweep','E18_','VL53_']) or re.search(r'(Pi5TrayOutsideSweep|E18_\w+|VL53_\w+)\.',val)):
                errors.append([o.Name,prop,val])
    return checked,errors
checked,errors=bindings()
result['expression_audit']={'checked_property_count':len(checked),'missing_bindings':errors}
json.dump(checked,open(OUT+'/expression-bindings.json','w'),indent=2)
# A real negative test: delete a required position expression, require detection, restore.
target=D.C_LEFT; prop='Placement.Base.y'
saved=dict((p.lstrip('.'),e) for p,e in target.ExpressionEngine)[prop]
target.setExpression(prop,None)
negative=bindings()[1]
target.setExpression(prop,saved); D.recompute()
result['unlinked_position_negative_test']={'removed':'C_LEFT.Placement.Base.y','detected':any(n=='C_LEFT' and p==prop for n,p,e in negative),'restored':not any(n=='C_LEFT' and p==prop for n,p,e in bindings()[1])}
# Sensitivity checks exercise positions and dimensions, not only presence of aliases.
probes=[
 ('camera_spacing',4,'C_LEFT','placement'),('camera_spacing',4,'camera_mount_left_cut1','bounds'),
 ('working_distance',2,'C_TOP','placement'),('working_distance',2,'camera_mount_top_cut1','bounds'),
 ('top_height',2,'camera_mount_top_cut1','bounds'),('side_y',2,'camera_mount_right_cut1','bounds'),
 ('side_z',2,'camera_mount_left_cut1','bounds'),('post_x',2,'post_left_seg_1','bounds'),
 ('post_y',2,'crossbar_seg_1','bounds'),('ProductX',2,'Product_80x80x240_OPEN','bounds'),
 ('ProductY',2,'Product_80x80x240_OPEN','bounds'),('ProductZ',2,'Product_80x80x240_OPEN','bounds'),
 ('BaseX',4,'base_plate_1_1_installed','bounds'),('BaseY',4,'base_plate_1_1_installed','bounds'),
 ('dock_x',2,'receiver_common','bounds'),('dock_y',2,'receiver_common','bounds'),('dock_z',2,'receiver_common','bounds'),
 ('dock_pitch',1,'tongue_common','volume'),('PiX',2,'Pi5TrayOutsideSweep_M5','bounds')]
for k in ['A','B','C']:
    probes += [('adapter_'+k+'_opening',2,'adapter_'+k+'_jaw_1_nut_captured','bounds'),('adapter_'+k+'_grip_distance',2,'adapter_'+k+'_jaw_1_nut_captured','bounds'),('adapter_'+k+'_slot_travel',2,'adapter_'+k+'_carrier_cut1','volume')]
def signature(o,kind):
    if kind=='placement': return list(o.getGlobalPlacement().Base)
    if kind=='volume': return [o.Shape.Volume]
    b=global_shape(o).BoundBox; return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
probe_results=[]
for alias,delta,name,kind in probes:
    o=D.getObject(name); cell=S.getCellFromAlias(alias); original=S.getContents(cell)
    before=signature(o,kind); value=getattr(S,alias).Value
    try:
        S.set(cell,'='+str(value+delta)+' mm'); D.recompute()
        after=signature(o,kind)
        changed=any(abs(a-b)>1e-6 for a,b in zip(before,after))
        # A pitch relocation does not change volume: examine center coordinates of hole tools.
        if alias=='dock_pitch': changed=abs(D.tongue_common_tool_2.Placement.Base.x-(S.tongue_pattern_x.Value+value+delta))<1e-6
        probe_results.append({'alias':alias,'object':name,'delta_mm':delta,'changed':changed})
        json.dump(probe_results,open(OUT+'/probe-progress.json','w'),indent=2)
    finally:
        S.set(cell,original); D.recompute()
result['parameter_probes']=probe_results
result['document_errors']=[{'name':o.Name,'state':list(o.State)} for o in D.Objects if 'Invalid' in o.State or 'Error' in o.State]
contract={}
for name in ['C_TOP','C_LEFT','C_RIGHT','Product_80x80x240_OPEN']:
    o=D.getObject(name); p=o.getGlobalPlacement()
    expected=baseline[name]
    contract[name]={'position':list(p.Base),'rotation':list(p.Rotation.Q),'unchanged':max(abs(a-b) for a,b in zip(list(p.Base)+list(p.Rotation.Q),expected['position']+expected['rotation']))<1e-7}
contract['FOV']={'illustrative_degrees':S.IllustrativeFOV.Value,'unchanged':abs(S.IllustrativeFOV.Value-55)<1e-7}
contract['cables_unchanged']=all([[list(v.Point) for v in D.getObject(n).Shape.Vertexes]==vs for n,vs in baseline['cables'].items()])
result['r03_contract']=contract
sweep=global_shape(D.ProductSweep_EXCLUSION)
overlaps=[]
for o in parts:
    if o.PrintPartID.startswith('adapter_'):continue
    s=global_shape(o)
    if s.BoundBox.intersect(sweep.BoundBox):
        vol=s.common(sweep).Volume
        if vol>1e-6: overlaps.append({'part':o.PrintPartID,'volume_mm3':vol})
result['product_corridor_overlap']=overlaps
# Measured pair collisions of manufactured parts; alternatives checked in their own local assembly.
collisions=[]
for i,o in enumerate(parts):
    if o.PrintPartID.startswith('adapter_'):continue
    a=global_shape(o)
    for p in parts[i+1:]:
        if p.PrintPartID.startswith('adapter_'):continue
        b=global_shape(p)
        if a.BoundBox.intersect(b.BoundBox):
            v=a.common(b).Volume
            if v>1e-4: collisions.append({'a':o.PrintPartID,'b':p.PrintPartID,'volume_mm3':v})
result['manufactured_part_collisions']=collisions
adapter_collisions=[]
for key in ['A','B','C']:
    ps=[o for o in parts if o.PrintPartID.startswith('adapter_'+key+'_')]
    for i,o in enumerate(ps):
        for p in ps[i+1:]:
            a=global_shape(o);b=global_shape(p)
            if a.BoundBox.intersect(b.BoundBox):
                v=a.common(b).Volume
                if v>1e-4:adapter_collisions.append({'a':o.PrintPartID,'b':p.PrintPartID,'volume_mm3':v})
result['adapter_collisions']=adapter_collisions
# Check the common mounting pattern after applying the installation translation.
pattern=[]
for key in ['A','B','C']:
    tp=[D.getObject('tongue_common_tool_'+str(i)).Placement.Base for i in range(4)]
    ap=[D.getObject('adapter_'+key+'_carrier_common_pattern_tool_'+str(i)).Placement.Base for i in range(4)]
    shifts=[t-a for t,a in zip(tp,ap)]
    pattern.append({'adapter':key,'same_pattern':all((x-shifts[0]).Length<1e-6 for x in shifts),'translation_xy_mm':[shifts[0].x,shifts[0].y]})
result['common_interface_patterns']=pattern
cam=D.R04_cam_lock; tongue=global_shape(D.tongue_common)
shifted=tongue.copy();shifted.translate(A.Vector(1,0,0))
closed_block=shifted.common(global_shape(cam)).Volume
cell=S.getCellFromAlias('cam_angle'); saved=S.getContents(cell)
try:
    S.set(cell,'=180 deg');D.recompute()
    open_cam=global_shape(cam)
    open_intersections=[]
    for dx in [1,30,110,200]:
        t=tongue.copy();t.translate(A.Vector(dx,0,0));open_intersections.append(t.common(open_cam).Volume)
finally:
    S.set(cell,saved);D.recompute()
result['cam_geometry']={'closed_blocks_1mm_withdrawal_mm3':closed_block,'open_180deg_intersections_mm3':open_intersections,'scope':'Discrete geometric positions, no real motion/force/safety validation'}
records=[]
for o in parts:
    name=o.PrintPartID; s=o.Shape.copy()
    rotation=A.Rotation()
    if name.startswith('crossbar_joint_'):rotation=A.Rotation(A.Vector(1,0,0),90)
    elif name.endswith('_corner'):rotation=A.Rotation(A.Vector(0,1,0),90)
    s.rotate(A.Vector(),rotation.Axis,rotation.Angle*180/math.pi)
    b=s.BoundBox; s.translate(A.Vector(-b.XMin,-b.YMin,-b.ZMin))
    size=dims(s); fits=all(a<=b+1e-6 for a,b in zip(size,[220,220,250]))
    step=OUT+'/parts/'+name+'.step'; stl=OUT+'/parts/'+name+'.stl'
    s.exportStep(step)
    mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=0.12,AngularDeflection=0.25,Relative=False)
    mesh.write(stl)
    check=Part.read(step); reread=Mesh.Mesh(stl)
    records.append({'id':name,'object':o.Name,'oriented_mm':[round(v,6) for v in size],'print_rotation_xyzw':list(rotation.Q),'bed_min_xyz':[0,0,0],'material':'PETG','orientation':o.PrintOrientation,'joint':o.JointDescription,'k1c_pass':fits,'base_180_pass':not name.startswith('base_plate_') or max(size[:2])<=180+1e-6,'shape_valid':s.isValid(),'solid_count':len(s.Solids),'step_roundtrip_valid':check.isValid() and len(check.Solids)==1 and max(abs(a-b) for a,b in zip(dims(check),size))<1e-4,'stl_closed':reread.isSolid(),'stl_facets':reread.CountFacets,'step':step,'stl':stl})
result['parts']=records
result['nominal_wall_mm']=S.wall.Value
sections={
 'base_plate_thickness':S.BaseT.Value,'base_joint_thickness':S.strap_thickness.Value,
 'post_socket_wall':S.sleeve_wall.Value,'receiver_floor':S.receiver_floor.Value,
 'receiver_rail':S.receiver_rail.Value,'receiver_capture_lip':D.receiver_capture_lip_1_blank.Height.Value,
 'camera_arm':D.camera_mount_left_blank.Height.Value,'camera_top_arm':D.camera_mount_top_blank.Height.Value,
 'cam_thickness':D.R04_cam_hub.Height.Value,'jaw_sole':D.adapter_A_jaw_1_sole.Height.Value,
 'jaw_wall_behind_nut':S.clamp_wall.Value-S.m5_nut_depth.Value,
 'sensor_flange_floor':S.wall.Value,'pi_tray':D.Pi5TrayOutsideSweep.Height.Value,
 'vl53_post_radial_ligament':D.VL53_DiagnosticPost.Length.Value/2-S.m5_clearance.Value/2,
 'receiver_mount_edge_ligament':D.receiver_common_tool_0.Placement.Base.x-S.m5_clearance.Value/2,
 'cam_pivot_radial_ligament':D.R04_cam_hub.Radius.Value-S.m5_clearance.Value/2,
 'e18_flange_corner_ligament':math.sqrt(2)*((50-D.E18_TriggerArmPost_base_flange_socket.Length.Value)/2-D.E18_TriggerArmPost_base_flange_tool_1.Placement.Base.x)-S.m5_clearance.Value/2}
result['analytical_wall_and_ligament_mm']=sections
result['wall_check_scope']='Analytical nominal plate/rail/sleeve dimensions and local fastener ligaments; not a full medial-axis minimum-wall analysis.'
result['gates']={
 'all_parts_fit_k1c':all(r['k1c_pass'] and r['base_180_pass'] for r in records),
 'all_parts_valid_single_solids':all(r['shape_valid'] and r['solid_count']==1 for r in records),
 'exports_roundtrip':all(r['step_roundtrip_valid'] and r['stl_closed'] for r in records),
 'all_required_bindings':not errors,
 'negative_test_detects_unlinked_position':result['unlinked_position_negative_test']['detected'] and result['unlinked_position_negative_test']['restored'],
 'parameter_response':all(p['changed'] for p in probe_results),
 'document_recompute':not result['document_errors'],
 'r03_contract_preserved':all(v['unchanged'] for v in contract.values() if isinstance(v,dict)) and contract['cables_unchanged'],
 'corridor_clear':not overlaps,
 'manufactured_parts_no_solid_overlap':not collisions,
 'adapter_assemblies_no_solid_overlap':not adapter_collisions,
 'same_receiver_pattern_ABC':all(p['same_pattern'] for p in pattern),
 'cam_positive_geometric_retention':closed_block>1e-4 and max(open_intersections)<1e-4,
 'analytical_structural_sections_min_4mm':min(sections.values())>=4-1e-6}
result['all_gates_pass']=all(result['gates'].values())
json.dump(result,open(OUT+'/validation.json','w'),indent=2)
json.dump({'parts':[o.Name for o in parts],'baseline':baseline},open(OUT+'/build-manifest.json','w'),indent=2)
for pg,val in page_states:pg.KeepUpdated=val
D.recompute(); D.save()
D.saveCopy(OUT+'/optical-rig-r04-print-ready.fcstd')
print(json.dumps({'objects':len(D.Objects),'parts':len(parts),'gates':result['gates'],'errors':errors,'collisions':collisions,'failed_probes':[p for p in probe_results if not p['changed']]}))
assert result['all_gates_pass'], 'R04 gate failure; inspect validation.json; do not report print-ready'
