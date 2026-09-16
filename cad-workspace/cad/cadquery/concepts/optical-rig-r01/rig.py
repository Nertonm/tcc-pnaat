"""REFERENCE_ONLY. Run with workspace .venv; vendor shapes are NEVER exported.
Coordinates x=transport downstream, y=transverse, z=up; generic belt top z=0.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import cadquery as cq
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT/'data/concepts/optical-rig-r01.json'
OUT = ROOT/'exports/concepts/optical-rig-r01'
VENDOR = ROOT/'references/vendor/raspberry-pi'
SOURCES = {'standard': VENDOR/'camera-module-3/step/Camera_module_3_std_model_simple.stp',
           'wide': VENDOR/'camera-module-3/step/Camera_module_3_wide_model_simple.stp',
           'pi5': VENDOR/'pi5/step/rpi-5b_no_graphics.step'}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def bounds(s):
    b=Bnd_Box()
    # Ignore cached STL triangulation: use analytic BRep bounds for stable readback.
    BRepBndLib.AddOptimal_s(s.wrapped,b,False,False)
    return list(b.Get())
def box(size, center): return cq.Workplane('XY').box(*size).translate(center).val()
def jsonwrite(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def check_params(p):
    assert p['status']=='REFERENCE_ONLY' and p['fabrication_allowed'] is False and p['measured'] is False
    assert p['camera_count']==3
    for k in ('camera_spacing','working_distance','cable_length','top_height','dock_width','cable_bend_radius','cable_service_allowance'):
        assert type(p[k]) in (int,float) and math.isfinite(p[k]) and p[k]>0, k
    assert len(p['product_envelope'])==3 and all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in p['product_envelope'])
    assert math.isfinite(p['side_angle']) and abs(p['side_angle'])<=20
    assert p['camera_spacing']>=p['product_envelope'][1]+120
    assert abs(p['top_height']-p['product_envelope'][2]-p['working_distance'])<1e-6, 'top_height = product height + working_distance'
    assert 100<=p['dock_width']<=200 and 15<=p['cable_bend_radius']<=35

def build(p):
    check_params(p)
    items={}; refs={}
    def add(name,s,role,printable=False,**meta):
        assert name not in items
        items[name]={'shape':s,'role':role,'printable':printable,**meta}
    for key,path in SOURCES.items():
        print('Import reference:',key,flush=True)
        s=cq.importers.importStep(str(path)).val()
        refs[key]={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'bounds_mm':bounds(s),'solid_count':len(s.Solids())}
        refs[key]['shape']=s
    h=p['product_envelope'][2]; top=p['top_height']; spacing=p['camera_spacing']; angle=p['side_angle']
    frame_y=spacing/2+80; frame_z=top+60
    add('base_MDF',box((450,2*frame_y+120,18),(25,0,-109)),'structure')
    for side,sign in [('LEFT',-1),('RIGHT',1)]:
        add('post_'+side,box((30,30,frame_z+100),(65,sign*frame_y,(frame_z-100)/2)),'structure')
    add('crossbar_profile',box((30,2*frame_y+30,30),(65,0,frame_z+15)),'structure')
    add('belt_GENERIC',box((600,160,20),(0,0,-10)),'exclusion')
    add('product_sweep',box((600,p['product_envelope'][1],h),(0,0,h/2)),'exclusion')
    add('product_mockup',box(p['product_envelope'],(0,0,h/2)),'mockup')
    # Camera model local optical face points towards -Z. Bounding-box centering is
    # explicit; exact principal-point registration remains an optical calibration task.
    for name,variant,sign in [('C_TOP','standard',0),('C_LEFT','wide',-1),('C_RIGHT','standard',1)]:
        source=refs[variant]['shape']; b=source.BoundingBox()
        source=source.translate((-b.center.x,-b.center.y,-b.zmin))
        cy=sign*spacing/2
        center=(0,cy,top if sign==0 else h/2)
        def place(s):
            if sign: s=s.rotate((0,0,0),(1,0,0),-sign*90).translate(center).rotate((0,0,0),(0,0,1),angle)
            else: s=s.translate(center)
            return s
        actual=place(source); bb=actual.BoundingBox()
        add(name,actual,'camera',reference=variant,connection={'C_TOP':'CSI0','C_LEFT':'CSI1','C_RIGHT':'CSI-to-USB conceptual'}[name])
        # Conservative official STEP envelope used by collision gate, never exported.
        items[name]['collision_shape']=box((bb.xlen,bb.ylen,bb.zlen),bb.center.toTuple())
        depth=b.zlen
        plate=cq.Workplane('XY').box(36,36,4).faces('>Z').workplane().pushPoints([(-14,-10),(14,-10),(-14,10),(14,10)]).hole(3.4).val().translate((0,0,depth+5))
        add('support_camera_module_3_'+name,place(plate),'mount',True,attachment='M3 hardware outside PCB envelope, PCB retention/insulating spacers pending bench fit')
        if sign==0:
            mount=box((80,24,8),(25,0,top+depth+11)).fuse(box((8,24,frame_z-(top+depth+15)),(61,0,(frame_z+top+depth+15)/2)))
        else:
            # short saddle backed by metal/profile arm: FDM is not the cantilever.
            mount=place(box((36,26,8),(0,0,depth+11)))
            arm=box((65,20,20),(32.5,sign*(spacing/2+depth+21),h/2))
            arm=arm.fuse(box((20,frame_y-(spacing/2+depth+21),20),(65,sign*(frame_y+spacing/2+depth+21)/2,h/2)))
            arm=arm.rotate((0,0,0),(0,0,1),angle)
            mount=mount.cut(arm)
            add('metal_arm_'+name,arm,'structure')
        add('mount_'+name,mount,'mount',True,requires='metal insert/captive hardware, unverified attachment')
        lc=(45,0,top-30) if not sign else (45,sign*(spacing/2-30),h/2)
        add('light_'+name,box((20,65,15),lc),'lighting',component='unselected envelope')
    # Pi on a tray attached to MDF, four isolated stand-offs under official mounting pattern.
    pi=refs['pi5']['shape'].translate((-80,frame_y-40,-88.55))
    add('PI5',pi,'pi',reference='pi5')
    b=pi.BoundingBox(); items['PI5']['collision_shape']=box((b.xlen,b.ylen,b.zlen),b.center.toTuple())
    tray=box((108,78,4),(-36,frame_y-12,-98))
    for x in (3.5,61.5):
        for y in (3.5,52.5):
            boss=cq.Workplane('XY').circle(3).circle(1.4).extrude(6).translate((x-80,frame_y-40+y,-96)).val()
            tray=tray.fuse(boss)
    add('pi5_concept_case',tray,'case',True,retention='four M2.5 conceptual fasteners; confirm physical board stack')
    # Open-sided corner bumper leaves connectors and cooling top accessible.
    for x in (-88,16):
        traycorner=box((6,6,27),(x,frame_y+23,-82.5))
        add('pi5_bumper_'+str(x),traycorner,'protector',True)
    add('PI_connector_access',box((150,105,24),(-36,frame_y-12,-75)),'access')
    add('USB_bridge_unselected',box((45,30,16),(120,frame_y-20,-85)),'electronics_envelope')
    add('TRIGGER_E18',box((55,22,22),(-150,-115,95)),'trigger',identification='E18 family; dimensions assumption')
    add('trigger_mount',cq.Workplane('XY').box(65,34,5).val().translate((-150,-115,80)),'mount',True)
    add('trigger_metal_arm',box((20,frame_y-115,20),(-150,-(frame_y+115)/2,70)),'structure')
    add('trigger_post',box((20,20,170),(-150,-frame_y,-15)),'structure')
    add('VL53L0X_diagnostic',box((25,15,8),(-70,-120,100)),'diagnostic')
    add('diagnostic_mount',box((35,25,4),(-70,-120,94)),'mount',True)
    add('diagnostic_metal_arm',box((100,15,8),(-110,-120,70)).fuse(box((15,15,18),(-70,-120,83))),'structure')
    add('roller_GENERIC',box((40,200,40),(-260,0,-40)),'exclusion')
    add('KY040_on_roller',box((25,25,25),(-260,-125,-40)),'encoder',attachment='roller-axis coupling, not optical crossbar; shaft/ratio/slip BLOCKED')
    add('roller_coupler_concept',box((8,12.5,8),(-260,-106.25,-40)),'hardware_envelope')
    # Dock receiver two open datum rails, transverse antirotation stop and captive screw boss.
    w=p['dock_width']; dock=box((80,w,6),(125,0,-97))
    for y in (-w/2+4,w/2-4): dock=dock.fuse(box((80,8,8),(125,y,-90)))
    dock=dock.fuse(box((8,w-16,8),(161,0,-90)))
    dock=dock.cut(cq.Workplane('XY').circle(2.7).extrude(20).translate((100,0,-103)).val())
    add('dock_interface',dock,'dock',True,datums=['D1 left rail','D2 floor'],antirotation='end stop',lock='captive M5 screw concept; metal washer/nut required')
    add('dock_tongue',box((62,w-18,5),(122,0,-91.5)),'mount',True)
    for label,width in [('A',w+20),('B',w+40)]:
        add('adapter_plate_'+label,box((100,width,6),(300,0 if label=='A' else width+20,-97)),'adapter',True,active=False,holes=[],target='A mini / B industrial presentation labels only; identities unconfirmed')
    # Swept round occupancy corridors: no assertion of FPC cross-section or twist compliance.
    for name,sign in [('C_TOP',0),('C_LEFT',-1),('C_RIGHT',1)]:
        start=(0,-50,top+32) if not sign else (0,sign*(spacing/2+55),h/2+35)
        points=[start,(150,start[1],start[2]),(150,start[1],frame_z+100),(150,frame_y+90,frame_z+100),(150,frame_y+90,-40),(-36,frame_y+90,-40),(-36,frame_y-12,-40)]
        wire=cq.Wire.makePolygon([cq.Vector(*v) for v in points])
        wire=wire.fillet(p['cable_bend_radius'],list(wire.Vertices())[1:-1])
        path=cq.Workplane(obj=wire)
        route=cq.Workplane('YZ',origin=start).circle(3).sweep(path,transition='round').val()
        length=wire.Length()
        add('channel_'+name,route,'cable',route_mm=length,bend_radius_mm=p['cable_bend_radius'],allowance_mm=p['cable_service_allowance'],available_mm=p['cable_length'],endpoint_note='ends at connector service zones; final FPC tails/pin mapping/twist remain BLOCKED')
        # Open U guide and independent strap slots, away from the camera connector.
        guide=cq.Workplane('XY').box(26,22,12).cut(cq.Workplane('XY').box(28,16,10).translate((0,0,4)))
        guide=guide.faces('<Z').workplane().pushPoints([(-8,0),(8,0)]).rect(3,10).cutThruAll().val()
        add('cable_guide_'+name,guide.translate((110,start[1],start[2]-5)),'guide',True,restraint='soft strap on cable jacket/support beyond connector; FPC connector never clamped')
    return items,refs

def metadata(items,refs,p):
    sources=list(SOURCES.values())+sorted((VENDOR/'docs').glob('*.pdf'))+[ROOT/'reports/COMMON-OPTICAL-INTERFACE-M0.md',ROOT/'reports/REFERENCE-ENVELOPE-AB.md',ROOT/'data/g0/esteira-b-g0-photo-r03.yaml']
    return {'status':'REFERENCE_ONLY','fabrication_allowed':False,'measured':False,'parameters':p,'sources':[{'path':str(f.relative_to(ROOT)),'sha256':sha(f)} for f in sources],
        'references':{k:{a:v for a,v in r.items() if a!='shape'} for k,r in refs.items()},
        'components':[{'name':n,**{k:v for k,v in c.items() if k not in ('shape','collision_shape')},'bounds_mm':bounds(c['shape']),'volume_mm3':c['shape'].Volume()} for n,c in items.items()]}

def preview(items,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig,axes=plt.subplots(1,2,figsize=(16,8))
    for ax,dims,title in zip(axes,[(1,2),(0,1)],['Front: y / z [mm]','Plan: x / y [mm]']):
        for n,c in items.items():
            if c.get('active') is False or c['role']=='access': continue
            b=bounds(c['shape']); i,j=dims
            color={'camera':'green','pi':'green','structure':'saddlebrown','cable':'purple','exclusion':'red','lighting':'orange'}.get(c['role'],'steelblue')
            ax.add_patch(Rectangle((b[i],b[j]),b[i+3]-b[i],b[j+3]-b[j],fill=False,edgecolor=color,lw=.8))
            if c['role'] in ('camera','pi','trigger','encoder','dock'): ax.text((b[i]+b[i+3])/2,(b[j]+b[j+3])/2,n,fontsize=7)
        ax.autoscale(); ax.set_aspect('equal'); ax.grid(alpha=.15); ax.set_title(title)
    fig.suptitle('PNAAT 3 views; REFERENCE_ONLY; not for fabrication\nConservative bounding envelopes; all bench dimensions ASSUMPTIONS')
    fig.tight_layout(); fig.savefig(out/'overview.pdf'); fig.savefig(out/'overview.png',dpi=130); plt.close(fig)

def generate(config=CONFIG,out=OUT):
    p=json.loads(config.read_text()); check_params(p)
    if out.exists() and any(out.iterdir()): raise ValueError('Refusing to overwrite existing artifacts')
    items,refs=build(p); out.mkdir(parents=True,exist_ok=True)
    for n,c in items.items():
        if c['printable']:
            cq.exporters.export(c['shape'],str(out/(n+'.step')))
            f=out/(n+'.step'); f.write_text(f.read_text().replace('HEADER;','HEADER;\n/* REFERENCE_ONLY FABRICATION_ALLOWED=false */',1))
            cq.exporters.export(c['shape'],str(out/(n+'.stl')),tolerance=.05,angularTolerance=.1)
            f=out/(n+'.stl'); raw=f.read_bytes(); f.write_bytes(b'REFERENCE_ONLY FABRICATION_ALLOWED=false'.ljust(80,b' ')+raw[80:])
    jsonwrite(out/'components.json',metadata(items,refs,p)); preview(items,out)
    print('GENERATED',out,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--config',type=Path,default=CONFIG); ap.add_argument('--out',type=Path,default=OUT)
    a=ap.parse_args(); generate(a.config,a.out)
