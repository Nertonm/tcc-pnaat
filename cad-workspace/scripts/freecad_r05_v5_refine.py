"""MCP GUI refinement, only after the core geometric gates were measured."""
# Uses live native shapes prepared by freecad_r05_v5_build.py and MCP STEP import.
cross=box(-20,-216,520,40,32,74).fuse(box(-20,-200,580,40,220,14))
cross=cross.cut(female(520)).cut(channel(519,77)).cut(crosshole(526))
cross=cross.cut(box(-10,-205,582,20,186,10)).cut(box(-10,-29,579,20,10,16))
cross=cross.cut(cyl(2.75,20,0,0,578))
d.CROSSBAR_C_TOP.Shape=cross.removeSplitter()
probe=channel(8,588).fuse(box(-10,-205,582,20,186,10)).fuse(box(-10,-29,548,20,10,47))
d.FPC_PROBE_20x10.Shape=probe
# Side ears are integral to module 2; central ribbon passage is unaffected.
s=d.MODULE_2.Shape
for x in [-88,20]: s=s.fuse(box(x,-216,228,68,16,34))
for x in [-55,55]: s=s.cut(cyl(2.75,20,x,-218,245,V(0,1,0)))
for x in [-31,20]: s=s.cut(cyl(4.3,11,x,-208,241,V(1,0,0)))
d.MODULE_2.Shape=s.removeSplitter()
source='pi-camera-mounts/Camera Mount - Bottom.FCStd / Fillet; GPL-2.0; cradle pan M5 and tilt M4 retained'
cradle=mountdoc.Fillet.Shape.copy()
# Replace its existing placement with a true transform of its world geometry.
cradle=cradle.transformGeometry(App.Placement(V(0,0,35),App.Rotation(V(1,0,0),90)).toMatrix())
plate=box(-28.8,-16,7,57.6,32,3)
for x in [-28.8,25]: plate=plate.fuse(box(x,-6,-5,3.8,12,15))
plate=plate.cut(cyl(2.2,70,-35,0,0,V(1,0,0)))
hole_xy=[(-12.4,-10.5),(0.1,-10.5),(-12.4,10.5),(0.1,10.5)]
for x,y in hole_xy:
    # Stand-offs contact the official board top; 2.2 mm official mounting pattern.
    plate=plate.fuse(cyl(2,3.22548,x,y,3.77452))
    plate=plate.cut(cyl(1.1,8,x,y,3))
plate=plate.removeSplitter()
camera_sets=[('TOP',V(0,0,545),App.Rotation(), 'CM3_Wide'),('LEFT',V(-55,-165,245),App.Rotation(V(1,0,0),90),'CM3_Std'),('RIGHT',V(55,-165,245),App.Rotation(V(1,0,0),90),'CM3_Std')]
for name,origin,rot,key in camera_sets:
    mat=App.Placement(origin,rot).toMatrix()
    add('C_'+name+'_PAN_TILT_CRADLE',cradle.transformGeometry(mat),(0.36,0.39,0.45),source=source)
    add('C_'+name+'_CM3_BACKPLATE',plate.transformGeometry(mat),(0.78,0.45,0.17),source='v5 replacement using official STEP PCB holes; mating GPL-2.0 cradle')
    # Model only the short side hinge screws so no bolt crosses the camera or FPC.
    for side in [-1,1]:
        axis=V(side,0,0); start=V(side*25,0,0)
        screw=Part.makeCylinder(2,8,start,axis).fuse(Part.makeCylinder(3.5,4,V(side*33,0,0),axis))
        add('C_'+name+'_TILT_M4_'+('L' if side<0 else 'R'),screw.transformGeometry(mat),(0.62,0.64,0.67),'hardware')
    # Pan screw through the preserved source M5 bore and the mating support.
    pan_length=22 if name=='TOP' else 24
    screw=cyl(2.5,pan_length,0,0,27).fuse(cyl(4.25,4,0,0,27+pan_length))
    add('C_'+name+'_PAN_M5',screw.transformGeometry(mat),(0.62,0.64,0.67),'hardware')
    ref=official[key].copy()
    # PCB upper plane aligned with stand-offs, lens points along local -Z.
    ref.translate(V(-14.4,-12.5,3.805))
    ref=ref.transformGeometry(mat)
    o=add('REF_'+name+'_'+key,ref,(0.2,0.5,0.25),'reference',source='official Raspberry Pi '+key+' STEP')
    o.addProperty('App::PropertyVector','LensFrontCenter')
    o.LensFrontCenter=origin+rot.multVec(V(0,0,3.805+(-8.805 if key=='CM3_Wide' else -7.65)))
# Official Pi body as a reference, aligned with the standing vendor case axes.
pi=official['Pi5'].copy()
pi.translate(V(-45,-28,0))
pi=pi.transformGeometry(App.Placement(V(-0.750000953674316,-209.06999969482422,77.0999984741211),App.Rotation(V(1,1,1),-120)).toMatrix())
o=add('REF_PI5_OFFICIAL',pi,(0.2,0.5,0.25),'reference',source='official rpi-5b_no_graphics.step; reference placement, electronics fit not certified')
o.ViewObject.Visibility=False
d.C_TOP.Status='Official CM3 Wide lens-front datum at Z540; direction -Z'
d.recompute(); Gui.activeDocument().activeView().fitAll()
print('REFINED',len(d.Objects))
