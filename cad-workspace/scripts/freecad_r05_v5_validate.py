"""Final geometric audit. Run through MCP execute_code in the real FreeCAD GUI."""
import itertools, json, math, datetime
parts=[o for o in d.Objects if hasattr(o,'Role') and o.Role in ('printed','hardware')]
tol=1e-5
def vol(a,b):
    return max(0.0,a.common(b).Volume) if a.BoundBox.intersect(b.BoundBox) else 0.0
records=[]
for a,b in itertools.combinations(parts,2):
    records.append({'a':a.Name,'b':b.Name,'volume_mm3':vol(a.Shape,b.Shape)})
collisions=[r for r in records if r['volume_mm3']>tol]
invalid=[o.Name for o in parts if not o.Shape.isValid() or len(o.Shape.Solids)!=1]
bottle=[{'part':o.Name,'volume_mm3':vol(o.Shape,d.BOTTLE_H370_D120.Shape),'distance_mm':o.Shape.distToShape(d.BOTTLE_H370_D120.Shape)[0]} for o in parts]
fpc=[{'part':o.Name,'volume_mm3':vol(o.Shape,d.FPC_PROBE_20x10.Shape)} for o in parts]
ordered=[d.CASE_TOP_COLLAR,d.MODULE_1,d.MODULE_2,d.MODULE_3,d.MODULE_4,d.CROSSBAR_C_TOP]
joints=[]
for i,(a,b) in enumerate(zip(ordered,ordered[1:])):
    z=140+95*i
    shaft=cyl(2,40,-20,-208,z+6,V(1,0,0))
    low=box(-20,-216,z-1,40,32,1)
    high=box(-20,-216,z,40,32,1)
    joined=a.Shape.common(low.fuse(high))
    joints.append({'lower':a.Name,'upper':b.Name,'body_interface_z_mm':z,'axial_gap_mm':a.Shape.distToShape(b.Shape)[0],
      'engagement_mm':12,'lateral_clearance_mm':0.2,'pocket_depth_mm':12.2,'m4_bore_mm':4.4,'m4_radial_clearance_mm':0.2,
      'lower_is_one_solid':len(a.Shape.Solids)==1,'shoulder_neck_connected':len(joined.Solids)==1,
      'shaft_interference_mm3':vol(shaft,a.Shape)+vol(shaft,b.Shape),'fastener':'JointM4_'+str(i)})
baseholes=[]
for x in [-30,30]:
    for y in [-222,-178]:
        bore=cyl(2.19,20,x,y,0)
        baseholes.append({'xy_mm':[x,y],'blocked_mm3':vol(bore,d.BASE_SLEEVE.Shape)+vol(bore,d.GRIP_STANDARD_ADAPTER.Shape)})
baseprobe=channel(0,46)
baseblocked=vol(baseprobe,d.BASE_SLEEVE.Shape)+vol(baseprobe,d.GRIP_STANDARD_ADAPTER.Shape)
k1c=[]
for o in parts:
    b=o.Shape.BoundBox; dims=[b.XLength,b.YLength,b.ZLength]
    orientations=[list(v) for v in itertools.permutations(range(3)) if all(dims[v[k]]<=limit+1e-5 for k,limit in enumerate([220,220,250]))]
    axes=orientations[0] if orientations else None
    k1c.append({'part':o.Name,'role':o.Role,'assembly_bbox_mm':dims,'print_axis_order':axes,'print_bbox_mm':[dims[k] for k in axes] if axes else None,'pass':bool(axes)})
height=d.REF_TOP_CM3_Wide.LensFrontCenter.z
gates={
 '1_interference':{'pass':not collisions and not invalid,'pair_count':len(records),'max_volume_mm3':max(r['volume_mm3'] for r in records),'collisions':collisions,'invalid_or_multisolid_parts':invalid},
 '2_bottle':{'pass':all(r['volume_mm3']<=tol for r in bottle),'minimum_distance_mm':min(r['distance_mm'] for r in bottle),'measurements':bottle},
 '3_top_height':{'pass':520<=height<=560,'lens_front_z_mm':height,'look_direction':[0,0,-1],'note':'Mechanical lens-front datum from official STEP, not entrance pupil/FOV'},
 '4_joints_M4':{'pass':all(j['axial_gap_mm']<=1 and j['lower_is_one_solid'] and j['shoulder_neck_connected'] and j['shaft_interference_mm3']<=tol for j in joints),'joints':joints},
 '5_FPC':{'pass':all(r['volume_mm3']<=tol for r in fpc) and len(d.FPC_PROBE_20x10.Shape.Solids)==1,'probe_section_mm':[20,10],'probe_solid_count':len(d.FPC_PROBE_20x10.Shape.Solids),'probe_volume_mm3':d.FPC_PROBE_20x10.Shape.Volume,'measurements':fpc,'route':'Z8..596 at X[-10,10],Y[-205,-195], then Z582..592 to Y-19 and descending exit Y[-29,-19] to Z548; geometric probe only'},
 '6_replaceable_grip':{'pass':baseblocked<=tol and all(h['blocked_mm3']<=tol for h in baseholes),'central_opening_mm':[20,10],'blocked_mm3':baseblocked,'standard_pattern_mm':[60,44],'bores':baseholes,'adapter':'GRIP_STANDARD_ADAPTER'},
 '7_K1C':{'pass':all(r['pass'] for r in k1c),'envelope_mm':[220,220,250],'parts':k1c,'note':'Orthogonal orientation bbox fit; does not include supports/brim or slicing'}
}
result={'document':d.Name,'object_count':len(d.Objects),'physical_part_count':len(parts),'units':'mm','tolerance_mm3':tol,'gates':gates,'all_gates_pass':all(g['pass'] for g in gates.values()),'all_pairs':records,
 'scope':'All final printed parts and fastener envelopes, including source-derived case, grip and camera mounts. Bottle checked separately. Official electronics are reference bodies and excluded from manufactured-part pair audit; their placement is not an electronics-fit certification.',
 'not_evaluated':['FOV','load','safety','electronics fit','printing process'],
 'sources':{'case':'pipiece ISC','grip':'light-clamp ISC','kinematics':'pi-camera-mounts GPL-2.0','electronics':'official local Raspberry Pi STEP references'}}
with open(OUT+'/validation.json','w') as f: json.dump(result,f,indent=2)
for name,g in gates.items(): print(name,'PASS' if g['pass'] else 'FAIL')
print('COLLISIONS',collisions,'INVALID',invalid)
print('FPC BLOCKERS',[v for v in fpc if v['volume_mm3']>tol])
print('JOINTS',joints)
print('OBJECTS',len(d.Objects),'PHYSICAL',len(parts))
