"""Second live MCP stage: planar FPC routes with analytic tangent arcs."""
assert d.getObject('FPC_TOP_Route') is None
def edge(a,b): return Part.makeLine(a,b)
def arc(a,b,c): return Part.Arc(a,b,c).toShape()
def profile(p,width,depth):
    return Part.Wire(Part.makePolygon([p+V(-width/2,-depth/2,0),p+V(width/2,-depth/2,0),p+V(width/2,depth/2,0),p+V(-width/2,depth/2,0),p+V(-width/2,-depth/2,0)]).Edges)
def sweep(w,p,width,depth): return w.makePipeShell([profile(p,width,depth)],True,False)
routes={}
for tag,native_x in [('TOP',55.205),('SIDE',49.005)]:
    start=V(-19.5,-20-native_x,355.286)
    end=camera_info[tag]['connector']
    if tag=='TOP':
        R=15.0; a=V(start.x,start.y,end.z-R); b=V(start.x,start.y+R,end.z)
        mid=V(start.x,start.y+R-R/math.sqrt(2),end.z-R+R/math.sqrt(2))
    else:
        R=(end.y-start.y)/2; a=start+V(0,0,12); b=V(start.x,end.y,a.z)
        mid=V(start.x,start.y+R,a.z+R)
    w=Part.Wire([edge(start,a),arc(a,mid,b),edge(b,end)])
    obj=add('FPC_'+tag+'_Route',w,(0.96,0.57,0.15) if tag=='TOP' else (0.59,0.29,0.83),'datum','Mouth-to-mouth planar centreline: straight + tangent circular arc + straight')
    obj.ViewObject.LineWidth=4
    for prop,val in [('PathLength',w.Length),('InsertionAllowance',10),('WorstCaseReserve',199-w.Length-10),('MinimumCentreRadius',R)]:
        obj.addProperty('App::PropertyLength',prop); setattr(obj,prop,val)
    # Constant 16 mm wide flexible span is conservative; mini termination narrows to 11.5.
    cable=sweep(w,start,16,0.35)
    add('FPC_'+tag+'_RequiredSpan',cable,(0.95,0.55,0.14) if tag=='TOP' else (0.57,0.26,0.8),'cable','Required span only; residual 200 mm length is not claimed as a solved full ribbon')
    gs=start+V(0,0,8)
    ge=end+(V(0,-8,0) if tag=='TOP' else V(0,0,8))
    gw=Part.Wire([edge(gs,a),arc(a,mid,b),edge(b,ge)])
    # Open U section, 17 mm clear width and 2 mm clear depth about the ribbon.
    coords=[(-10,-2.5),(10,-2.5),(10,2.5),(8.5,2.5),(8.5,-1),(-8.5,-1),(-8.5,2.5),(-10,2.5),(-10,-2.5)]
    sec=Part.Wire(Part.makePolygon([gs+V(x,y,0) for x,y in coords]).Edges)
    guide=gw.makePipeShell([sec],True,False)
    probe=sweep(gw,gs,20.4,5.4)
    # Recut both ribbon exits into the actual case, and routing clearance in adapters.
    for o in list(printed):
        if o.Shape.BoundBox.intersect(probe.BoundBox):
            o.Shape=o.Shape.cut(probe).removeSplitter()
    # Mechanical guide tab on its start, attaches to a case rim shelf with M2.5.
    tab=box(-38,start.y-3,361.5,10,6,3)
    guide=guide.fuse(tab)
    q=V(-34,start.y,361.5)
    guide=guide.cut(cyl(1.35,8,q-V(0,0,1)))
    shelf=box(-38,start.y-3,358.5,8,6,3)
    case_obj.Shape=case_obj.Shape.fuse(shelf).cut(cyl(1.35,10,q-V(0,0,5))).removeSplitter()
    bolt('FPC_'+tag+'_Guide_M25',1.25,8,q+V(0,0,3),V(0,0,-1))
    nut('FPC_'+tag+'_Guide_Nut',1.25,q-V(0,0,5))
    go=add('FPC_'+tag+'_RadiusGuide',guide.removeSplitter(),(0.89,0.74,0.39) if tag=='TOP' else (0.7,0.56,0.8))
    routes[tag]={'wire':w,'start':start,'end':end,'radius':R,'guide':go,'span':cable}
    marker=add('CSI_'+tag+'_Datum',Part.Vertex(start),(1,0,0),'datum','Centre of upper connector housing from official STEP; 10 mm total insertion allowance')
    marker.addProperty('App::PropertyVector','Position'); marker.Position=start
    marker.ViewObject.PointSize=6
# Reserve volumes represent space to develop service loops, not a validated 200 mm ribbon.
for tag,x,y,z in [('TOP',-48,-65,380),('SIDE',-48,-49,325)]:
    o=add('FPC_'+tag+'_SlackEnvelope',box(x,y,z,24,30,25),(0.8,0.5,0.8),'keepout','Provisional service-loop space. Full slack ribbon and material bend radius remain unverified.')
    o.ViewObject.Transparency=85; o.Visibility=False
d.recompute()
print('PATHS',[(k,v['wire'].Length,199-v['wire'].Length-10,v['radius']) for k,v in routes.items()])
print('INVALID',[(o.Name,o.Shape.isValid(),len(o.Shape.Solids)) for o in printed if not o.Shape.isValid() or len(o.Shape.Solids)!=1])
