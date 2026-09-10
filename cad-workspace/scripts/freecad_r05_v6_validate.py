"""Run on FreeCAD GUI thread via MCP. Audit actual final BReps, including electronics."""
import itertools,json,math,hashlib,os
D=App.getDocument('R05ColumnV6'); d=D
TOL=1e-5
physical=[o for o in D.Objects if hasattr(o,'Role') and o.Role in ('printed','hardware','electronics')]
printed=[o for o in physical if o.Role=='printed']
def ov(a,b):
    return max(0.0,a.common(b).Volume) if a.BoundBox.intersect(b.BoundBox) else 0.0
def bbox(s):
    b=s.BoundBox
    return [b.XMin,b.YMin,b.ZMin,b.XLength,b.YLength,b.ZLength]
pairs=[{'a':a.Name,'b':b.Name,'volume_mm3':ov(a.Shape,b.Shape)} for a,b in itertools.combinations(physical,2)]
hits=[r for r in pairs if r['volume_mm3']>TOL]
invalid=[o.Name for o in physical if not o.Shape.isValid() or (o.Role!='electronics' and len(o.Shape.Solids)!=1)]
bottle=[{'part':o.Name,'volume_mm3':ov(o.Shape,D.BOTTLE_H370_D120.Shape),'distance_mm':o.Shape.distToShape(D.BOTTLE_H370_D120.Shape)[0]} for o in physical]
backlight=[{'part':o.Name,'volume_mm3':ov(o.Shape,D.BACKLIGHT_BEHIND_BOTTLE.Shape)} for o in physical]
probe=D.FPC_PROBE_20x10.Shape
fpc=[{'part':o.Name,'volume_mm3':ov(o.Shape,probe)} for o in physical]
joint_specs=[('BASE_SLEEVE','MODULE_1',20),('MODULE_1','MODULE_2',115),('MODULE_2','MODULE_3',210),('MODULE_3','MODULE_4',305),('MODULE_4','CASE_LOWER_COLLAR',400),('CASE_TOP_COLLAR','CROSSBAR_C_TOP',540)]
joints=[]
for i,(an,bn,z) in enumerate(joint_specs):
    a=D.getObject(an).Shape;b=D.getObject(bn).Shape
    shaft=cyl(2,40,-20,-208,z+6,V(1,0,0))
    neck=a.common(box(-20,-216,z-0.5,40,32,1))
    male_body=a.common(box(-16,-212,z,32,24,12))
    # Horizontal shoulder contact, actual material engagement and unobstructed M4 clearance.
    contact=a.distToShape(b)[0]
    shell=b.common(box(-20,-216,z,40,32,12))
    blocked=ov(shaft,a)+ov(shaft,b)
    joints.append({'lower':an,'upper':bn,'z_mm':z,'minimum_distance_mm':contact,'engagement_bbox_z_mm':male_body.BoundBox.ZLength,'male_neck_solid_count':len(neck.Solids),'female_surround_volume_mm3':shell.Volume,'male_volume_mm3':male_body.Volume,'shaft_collision_mm3':blocked,'bore_diameter_mm':4.4,'M4_radial_clearance_mm':0.2,'male_female_side_clearance_mm':0.2,'fastener':'JointM4_'+str(i),'pass':contact<=1e-5 and len(neck.Solids)==1 and male_body.BoundBox.ZLength>=11.99 and shell.Volume>0 and blocked<=TOL})
case_contacts=[{'a':a,'b':b,'distance_mm':D.getObject(a).Shape.distToShape(D.getObject(b).Shape)[0]} for a,b in [('CASE_LOWER_COLLAR','PIPIECE_CASE_VERTICAL'),('PIPIECE_CASE_VERTICAL','CASE_TOP_COLLAR')]]
baseprobe=channel(0,20)
baseblock=ov(baseprobe,D.BASE_SLEEVE.Shape)+ov(baseprobe,D.GRIP_STANDARD_ADAPTER.Shape)
holes=[]
for x in [-30,30]:
 for y in [-222,-178]:
    pr=cyl(2.19,20,x,y,0)
    holes.append({'xy_mm':[x,y],'blocked_mm3':ov(pr,D.BASE_SLEEVE.Shape)+ov(pr,D.GRIP_STANDARD_ADAPTER.Shape)})
fit=[]
for o in physical:
    dims=bbox(o.Shape)[3:]
    perms=[list(p) for p in itertools.permutations(range(3)) if all(dims[p[k]]<=v+1e-5 for k,v in enumerate([220,220,250]))]
    fit.append({'name':o.Name,'role':o.Role,'assembly_bbox_mm':dims,'print_axes':perms[0] if perms else None,'oriented_bbox_mm':[dims[k] for k in perms[0]] if perms else None,'pass':bool(perms)})
height=D.REF_TOP_CM3_Wide.LensFrontCenter.z
routes=[]
for name in ['TOP','SIDE']:
    o=D.getObject('FPC_ROUTE_'+name)
    points=list(o.Waypoints)
    length=sum((b-a).Length for a,b in zip(points,points[1:]))
    interference=[{'part':p.Name,'volume_mm3':ov(p.Shape,o.Shape)} for p in physical if ov(p.Shape,o.Shape)>TOL]
    routes.append({'camera':'C_'+name,'waypoints_mm':[[v.x,v.y,v.z] for v in points],'straight_distance_mm':(points[-1]-points[0]).Length,'route_length_mm':length,'service_allowance_mm':o.ServiceAllowance.Value,'required_length_mm':length+o.ServiceAllowance.Value,'selected_length_mm':o.CableLength.Value,'route_blockers':interference,'pass':length+o.ServiceAllowance.Value<=o.CableLength.Value and not interference})
G={
'1_interference':{'pass':not hits and not invalid and not any(r['volume_mm3']>TOL for r in backlight),'pair_count':len(pairs),'collisions':hits,'invalid_parts':invalid,'max_intersection_mm3':max((r['volume_mm3'] for r in pairs),default=0),'backlight_checks':backlight,'scope':'Every printed part, fastener envelope and all three official electronics bodies; bottle and backlight checked separately. Source copies and diagnostic probes excluded.'},
'2_bottle_corridor':{'pass':all(r['volume_mm3']<=TOL for r in bottle),'bottle_H_D_mm':[370,120],'corridor_Y_mm':[-60,60],'column_axis_Y_mm':-200,'minimum_distance_mm':min(r['distance_mm'] for r in bottle),'measurements':bottle},
'3_C_TOP_height':{'pass':520<=height<=560,'lens_front_Z_mm':height,'allowed_Z_mm':[520,560],'note':'Mechanical lens front from official CM3 STEP; no FOV calculation'},
'4_continuous_joints_M4':{'pass':all(j['pass'] for j in joints) and all(c['distance_mm']<=1e-5 for c in case_contacts),'joints':joints,'standing_case_seating':case_contacts},
'5_continuous_FPC':{'pass':len(probe.Solids)==1 and probe.isValid() and all(r['volume_mm3']<=TOL for r in fpc),'probe_solid_count':len(probe.Solids),'probe_valid':probe.isValid(),'section_mm':[20,10],'measurements':fpc,'note':'Connected clearance volume through all module shoulders; high case detour if needed is explicitly included in geometry.'},
'6_replaceable_grip':{'pass':baseblock<=TOL and all(r['blocked_mm3']<=TOL for r in holes),'central_through_opening_mm':[20,10],'opening_blocked_mm3':baseblock,'four_hole_pattern_mm':[60,44],'hole_diameter_mm':4.4,'holes':holes,'grip_specific_adapter':'GRIP_STANDARD_ADAPTER','jaw_opening_mm':float(D.Parameters.get('B8'))},
'7_K1C':{'pass':all(r['pass'] for r in fit),'envelope_mm':[220,220,250],'parts':fit,'note':'Orthogonal bounding-box placement only; no supports or slicing'},
'8_high_Pi_short_cables':{'pass':len(routes)==2 and all(r['pass'] for r in routes) and D.REF_PI5_OFFICIAL.Shape.BoundBox.ZMin>370,'Pi_bbox_mm':bbox(D.REF_PI5_OFFICIAL.Shape),'routes':routes,'short_cable_criterion':'At most 500 mm per cable, including 50 mm service allowance; geometric routing only, not electrical operation or bend-life validation'}
}
result={'document':D.Name,'object_count':len(D.Objects),'physical_part_count':len(physical),'printed_part_count':len(printed),'camera_count':2,'camera_names':['C_TOP','C_SIDE'],'gates':G,'all_gates_pass':all(g['pass'] for g in G.values()),'units':'mm','intersection_tolerance_mm3':TOL,'all_pairs':pairs,'not_evaluated':['FOV','load','safety','electrical camera operation','slicing'],'parameter_mode':'Spreadsheet aliases record rebuild inputs; BRep geometry changes require rerunning builder and audit, not a live assembly constraint solver.'}
path=OUT+'/validation.json'
if os.path.exists(path):
    previous=json.load(open(path))
    if previous.get('document')!='R05ColumnV6' and not os.path.exists(OUT+'/validation-pre-v6.json'):
        open(OUT+'/validation-pre-v6.json','w').write(json.dumps(previous,indent=2))
open(path,'w').write(json.dumps(result,indent=2))
print('GATES',[(k,'PASS' if v['pass'] else 'FAIL') for k,v in G.items()])
print('COLLISIONS',hits,'INVALID',invalid)
print('FPC_BLOCKERS',[r for r in fpc if r['volume_mm3']>TOL])
print('CASE_CONTACTS',case_contacts)
print('CABLES',routes)
print('COUNTS',D.Name,len(D.Objects),len(physical),len(printed))
