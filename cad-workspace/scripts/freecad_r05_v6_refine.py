# Execute only after validation-v6-core.json passes. Source geometry is adapted directly.
import json
assert json.load(open(OUT+'/validation-v6-core.json'))['pass']
mountdoc=App.getDocument('Camera_Mount___Bottom')
official={}
for key,path in [('Pi5','pi5/step/rpi-5b_no_graphics.step'),('CM3_Std','camera-module-3/step/Camera_module_3_std_model_simple.stp'),('CM3_Wide','camera-module-3/step/Camera_module_3_wide_model_simple.stp')]:
    official[key]=Part.read(ROOT+'/references/vendor/raspberry-pi/'+path)
App.setActiveDocument('R05ColumnV6')
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
camera_sets=[
    ('TOP',V(0,0,545),App.Rotation(), 'CM3_Wide'),
    ('LEFT',V(0,-165,245),App.Rotation(V(1,0,0),90),'CM3_Std'),
]
for name,origin,rot,key in camera_sets:
    mat=App.Placement(origin,rot).toMatrix()
    add('C_'+name+'_PAN_TILT_CRADLE',cradle.transformGeometry(mat),(0.36,0.39,0.45),source=source)
    add('C_'+name+'_CM3_BACKPLATE',plate.transformGeometry(mat),(0.78,0.45,0.17),source='v6 replacement using official STEP PCB holes; mating GPL-2.0 cradle')
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
# The USB-C/UVC camera is deliberately an envelope rather than an invented
# vendor STEP.  Procurement must select the exact module and connector before
# this reference is promoted to a manufactured mount.
usb=box(-30,150,230,60,30,30)
o=add('REF_RIGHT_USB_C_UVC',usb,(0.55,0.25,0.75),'reference',source='USB-C/UVC camera envelope; exact model BLOCKED')
o.addProperty('App::PropertyVector','LensFrontCenter'); o.LensFrontCenter=V(0,165,245)
# Official Pi body as a reference, aligned with the standing vendor case axes.
pi=official['Pi5'].copy()
pi.translate(V(-45,-28,0))
pi=pi.transformGeometry(App.Placement(V(-0.750000953674316,-209.06999969482422,477.0999984741211),App.Rotation(V(1,1,1),-120)).toMatrix())
o=add('REF_PI5_OFFICIAL',pi,(0.2,0.5,0.25),'reference',source='official rpi-5b_no_graphics.step; reference placement, electronics fit not certified')
o.ViewObject.Visibility=True
d.C_TOP.Status='Official CM3 Wide lens-front datum at Z540; direction -Z'
d.recompute(); Gui.activeDocument().activeView().fitAll()
print('REFINED',len(d.Objects))
