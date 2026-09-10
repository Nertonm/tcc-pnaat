import itertools, json
D=App.getDocument('R05ColumnV6')
P=[o for o in D.Objects if hasattr(o,'Role') and o.Role in ('printed','hardware')]
def overlap(a,b):
    return max(0.0,a.common(b).Volume) if a.BoundBox.intersect(b.BoundBox) else 0.0
hits=[]
for a,b in itertools.combinations(P,2):
    v=overlap(a.Shape,b.Shape)
    if v>1e-5: hits.append([a.Name,b.Name,v])
blocked=[[o.Name,overlap(o.Shape,D.FPC_PROBE_20x10.Shape)] for o in P if overlap(o.Shape,D.FPC_PROBE_20x10.Shape)>1e-5]
invalid=[o.Name for o in P if not o.Shape.isValid() or len(o.Shape.Solids)!=1]
result={'stage':'core before official STEP refinement','collisions':hits,'fpc_blockers':blocked,'invalid':invalid,'pass':not (hits or blocked or invalid)}
open(OUT+'/validation-v6-core.json','w').write(json.dumps(result,indent=2))
print(json.dumps(result))
