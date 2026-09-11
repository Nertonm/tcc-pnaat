from pathlib import Path
import json
p=Path(__file__).resolve().parent
data=json.loads((p/'redux-sections.json').read_text());out={}
for h,edges in data.items():
    adj={}
    for a,b in edges:
        ka=tuple(round(x,4) for x in a);kb=tuple(round(x,4) for x in b)
        adj.setdefault(ka,set()).add(kb);adj.setdefault(kb,set()).add(ka)
    seen=set();comps=[]
    for v in adj:
        if v in seen: continue
        stack=[v];pts=[];seen.add(v)
        while stack:
            a=stack.pop();pts.append(a)
            for b in adj[a]-seen: seen.add(b);stack.append(b)
        comps.append({'vertices':len(pts),'bbox':[[min(q[i] for q in pts),max(q[i] for q in pts)] for i in range(3)],'closed_graph':all(len(adj[q])==2 for q in pts)})
    out[h]=comps
(p/'redux-section-components.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
