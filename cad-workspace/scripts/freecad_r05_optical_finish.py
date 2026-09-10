"""Finish mechanical retention; execute through live MCP."""
# M2.5 bosses receive brass insert envelopes; PCB bores remain official 2.7 mm.
for x in [3.5,61.5]:
    for y in [3.5,52.5]:
        q=V(-28,-20,350)+pi_rot.multVec(V(x,y,0))
        case_obj.Shape=case_obj.Shape.cut(cyl(1.8,3.6,q-V(0,0,3.57)))
        ins=cyl(1.75,3.5,q-V(0,0,3.5)).cut(cyl(1.25,3.5,q-V(0,0,3.5)))
        add('Pi_M25_Insert_'+str(x)+'_'+str(y),ins,(0.76,0.62,0.26),'hardware','M2.5 brass insert envelope OD3.5 L3.5; final insert SKU/tolerance not selected')
for tag,v in camera_info.items():
    origin=v['origin']; rot=v['rotation']; axis=rot.multVec(V(0,0,1))
    # CM3 connector is 22.92 mm across; 24 mm mouth clears both sides.
    bp=d.getObject('C_'+tag+'_CM3_Backplate')
    bp.Shape=bp.Shape.cut(move(box(4,-12,5.4,22,24,2),origin,rot)).removeSplitter()
    nut('C_'+tag+'_Pan_Nut_M5',2.5,origin+rot.multVec(V(0,0,27.25)),axis)
    for xx in [-7,7]: nut('C_'+tag+'_PanLock_Nut_M3_'+str(xx),1.5,origin+rot.multVec(V(xx,0,28.75)),axis)
    for side in [-1,1]:
        ax=rot.multVec(V(0,side,0)); p=origin+rot.multVec(V(0,side*28.8,0))
        s=cyl(3.5,0.2,p,ax).cut(cyl(2.25,0.2,p,ax))
        add('C_'+tag+'_Tilt_ShimmingWasher_'+str(side),s,(0.64,0.65,0.68),'hardware','0.2 mm hinge clearance shim; matching 57.6 mm carrier to vendor 58 mm spacing')
d.recompute()
