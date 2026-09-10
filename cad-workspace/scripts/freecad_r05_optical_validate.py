"""Geometry evidence, conservative gates; execute in live FreeCAD MCP."""
import itertools, hashlib
evidence={'document':d.Name,'units':'mm','objects':len(d.Objects),'cables':{},'printed_parts':[],
          'printed_intersections':[],'printed_contacts':[],'electronics_intersections':[],
          'cooler_intersections':[],'cable_intersections':[],'camera_axes':{},'gates':{}}
for tag,v in routes.items():
    tang=[]
    ee=v['wire'].Edges
    for e1,e2 in zip(ee,ee[1:]):
        t1=e1.tangentAt(e1.LastParameter); t2=e2.tangentAt(e2.FirstParameter)
        tang.append(math.degrees(t1.getAngle(t2)))
    evidence['cables'][tag]={'path_mm':v['wire'].Length,'insertion_allowance_mm':10,
        'required_total_mm':v['wire'].Length+10,'nominal_mm':200,'minimum_stock_mm':199,
        'reserve_at_199_mm':199-v['wire'].Length-10,'centre_radius_mm':v['radius'],
        'ribbon_inner_radius_mm':v['radius']-0.175,'tangent_junction_angles_deg':tang,
        'start_CSI':list(v['start']),'end_CM3':list(v['end']),
        'full_200mm_slack_ribbon_modelled':False,'supplier_minimum_bend_radius_mm':None}
for o in printed:
    b=o.Shape.BoundBox
    dims=[b.XLength,b.YLength,b.ZLength]
    evidence['printed_parts'].append({'name':o.Name,'size_xyz_mm':dims,'valid':o.Shape.isValid(),
                                    'solids':len(o.Shape.Solids),'K1C':all(a<=b+0.001 for a,b in zip(dims,[220,220,250]))})
for a,b in itertools.combinations(printed,2):
    if not a.Shape.BoundBox.intersect(b.Shape.BoundBox): continue
    vol=a.Shape.common(b.Shape).Volume
    if vol>0.02: evidence['printed_intersections'].append({'a':a.Name,'b':b.Name,'volume_mm3':vol})
    elif a.Shape.distToShape(b.Shape)[0]<0.03: evidence['printed_contacts'].append([a.Name,b.Name])
for o in printed:
    if o.Shape.BoundBox.intersect(cooler.Shape.BoundBox):
        vol=o.Shape.common(cooler.Shape).Volume
        if vol>0.02:evidence['cooler_intersections'].append({'part':o.Name,'volume_mm3':vol})
    for tag,v in routes.items():
        if not o.Shape.BoundBox.intersect(v['span'].BoundBox):continue
        vol=o.Shape.common(v['span']).Volume
        if vol>0.02:evidence['cable_intersections'].append({'part':o.Name,'cable':tag,'volume_mm3':vol})
for ename in ['Pi5_Central','C_TOP_OfficialCM3','C_SIDE_OfficialCM3']:
    el=d.getObject(ename)
    # Solid-level pruning avoids running booleans against thousands of irrelevant contacts.
    for o in printed:
        if not o.Shape.BoundBox.intersect(el.Shape.BoundBox):continue
        nearby=[s for s in el.Shape.Solids if s.BoundBox.intersect(o.Shape.BoundBox)]
        vol=o.Shape.common(Part.makeCompound(nearby)).Volume if nearby else 0
        if vol>0.02:evidence['electronics_intersections'].append({'electronics':ename,'part':o.Name,'volume_mm3':vol})
for tag,v in camera_info.items():
    ray=Part.makeLine(v['lens'],v['lens']+v['direction']*200)
    evidence['camera_axes'][tag]={'lens':list(v['lens']),'direction':list(v['direction']),
        'intersects_bottle':not ray.common(bottle.Shape).isNull()}
evidence['cable_to_cable_volume_mm3']=routes['TOP']['span'].common(routes['SIDE']['span']).Volume
evidence['gates']['G1']={'status':'PASS' if all(x['reserve_at_199_mm']>=20 for x in evidence['cables'].values()) else 'FAIL',
    'scope':'Required mouth-to-mouth route plus 10 mm insertion allowance; 199 mm worst-case stock'}
evidence['gates']['G2']={'status':'FAIL','reason':'Supplier bend radius unavailable; full residual slack ribbon and terminal transition not solved. Smooth planar required spans are modelled, but cannot certify the complete cables.'}
evidence['gates']['G3']={'status':'PASS' if not evidence['electronics_intersections'] and not evidence['cooler_intersections'] else 'FAIL',
    'scope':'Official electronics against printed solids; conservative cooler envelope. Port openings preserved/expanded; no thermal validation.'}
evidence['gates']['G4']={'status':'PASS' if all(x['intersects_bottle'] for x in evidence['camera_axes'].values()) else 'FAIL','scope':'Centre axes only; no FOV or image coverage validation'}
evidence['gates']['G5']={'status':'FAIL','reason':'Pending connected-part and joint review'}
evidence['gates']['G6']={'status':'PASS' if all(p['valid'] and p['solids']==1 and p['K1C'] for p in evidence['printed_parts']) else 'FAIL','scope':'Individual printed parts only, assembled-axis bounding boxes; pedestal and bottle are non-printed placeholders'}
evidence['overall']='FAIL' if any(v['status']=='FAIL' for v in evidence['gates'].values()) else 'PASS'
with open(OUT+'/validation.json','w') as f:json.dump(evidence,f,indent=2)
print(json.dumps(evidence,indent=2))
