"""R02 assumed bench prototype. R01 and official reference bodies are read-only."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('r01',ROOT/'cad/cadquery/concepts/optical-rig-r01/rig.py')
r01=importlib.util.module_from_spec(spec); spec.loader.exec_module(r01)
box,bounds,sha,jsonwrite=r01.box,r01.bounds,r01.sha,r01.jsonwrite
CONFIG=ROOT/'data/concepts/optical-rig-r02.json'
OUT=ROOT/'exports/concepts/optical-rig-r02'

def check_params(p):
    assert p['status']=='ASSUMPTION_DRIVEN' and p['release_class']=='PROTOTYPE_CONCEPT'
    assert p['prototype_print_allowed'] is True and p['production_release'] is False and p['measured'] is False
    q=dict(p,status='REFERENCE_ONLY',fabrication_allowed=False); r01.check_params(q)
    assert p['side_angle']==0, 'R02 brackets support zero side angle only'
    assert p['base_size']==[450,680,18] and p['profile']==30
    assert 120<=p['dock_width']<=170
    assert .3<=p['fit_clearance']<=.8
    assert 16<=p['adapter_slot_length']<=30
    assert 20<=p['clamp_opening']<=60 and 4<=p['jaw_step']<=12
    assert 80<=p['saddle_span']<=120 and 90<=p['bench_pitch']<=110
    assert p['hardware']=='M5' and p['material']=='PETG' and p['walls']>=4

def hole(s,x,y,r=2.75):
    return s.cut(cq.Workplane('XY').center(x,y).circle(r).extrude(100).translate((0,0,-40)).val())

def slots(s,points,length):
    for x,y in points:
        tool=cq.Workplane('XY').center(x,y).slot2D(length,5.5,0).extrude(100).translate((0,0,-40)).val()
        s=s.cut(tool)
    return s

def build(p):
    check_params(p)
    items,refs=r01.build(dict(p,status='REFERENCE_ONLY',fabrication_allowed=False))
    # Keep R01 optics, generic frame, source imports and rounded cable corridors.
    for n in list(items):
        if n.startswith(('dock_','adapter_plate_','pi5_bumper_')) or n=='USB_bridge_unselected': del items[n]
    def put(n,s,role='mount',pos=(0,0,0),**meta):
        items[n]={'shape':s.translate(pos),'print_shape':s,'role':role,'printable':True,
                  'assembly_translation_mm':list(pos),'fasteners':'M5 through bolt + metal washer/nut unless specified',**meta}
    w=p['dock_width']; clearance=p['fit_clearance']; slot=p['adapter_slot_length']
    dockpos=(125,0,-84)
    # Undercut rails capture the tongue vertically; end stop and M5 pin capture X.
    receiver=box((80,w,6),(0,0,3))
    for y in (-w/2+4,w/2-4):
        receiver=receiver.fuse(box((80,8,14),(0,y,13)))
        receiver=receiver.fuse(box((80,14,4),(0,y-math.copysign(3,y),18)))
    receiver=receiver.fuse(box((8,w-16,14),(36,0,13)))
    mounting=[(-25,-w/2+20),(-25,w/2-20),(25,-w/2+20),(25,w/2-20)]
    for x,y in mounting+[(-22,0),(35,0)]: receiver=hole(receiver,x,y)
    put('receiver',receiver,'receiver',dockpos,positive_retention=['undercut rails','end stop','M5 cross-lock through tongue'],mounting_xy=mounting)
    tongue=box((62,w-16-2*clearance,5),(-8,0,9))
    tongue=tongue.fuse(box((6,20,15),(20,0,19)))
    # Two M5 holes attach a metal bridge to the optical frame, locking screw is separate.
    for x,y in [(-22,0),(-8,-30),(-8,30)]: tongue=hole(tongue,x,y)
    put('tongue',tongue,'tongue',dockpos,frame_attachment='2 M5 at (-8,+/-30), metal bridge to 30 mm frame/base',lock_hole_xy=[-22,0])
    cam=cq.Workplane('XY').center(-2,0).circle(10).extrude(6).val()
    cam=cam.fuse(box((12,45,6),(0,22.5,3)))
    cam=hole(cam,0,0)
    put('cam_lever',cam,'cam',(dockpos[0]+35,0,dockpos[2]+21),pivot='M5 shoulder bolt/metal sleeve, washers; locknut; eccentricity 2 mm',contact='tongue end lug; snug only; M5 cross-lock required',infill='100% local contact trial or metal contact washer; no load rating')
    # Separate keeper traps screw head with commercial captive washer under a removable bridge.
    keeper=box((20,20,9),(0,0,4.5)).cut(box((13,22,6),(0,0,3)))
    keeper=hole(keeper,0,0)
    for x in (-8,8): keeper=hole(keeper,x,0,1.7)
    put('captive_screw_keeper',keeper,'retention',(103,0,-72.5),fasteners='M5x35 cross-lock + captive retaining washer; 2 M3x16 bolts/nuts through tongue',note='install screw and captive washer before keeper; keeper retains head, metal nut carries load')
    for x in (-30,-14):
        items['tongue']['print_shape']=hole(items['tongue']['print_shape'],x,0,1.7)
    items['tongue']['shape']=items['tongue']['print_shape'].translate(dockpos)
    # Common upper pattern, differing lower attachment, all presented separately.
    for label in ('A','B','C'):
        plate=box((110,w,8),(0,0,4))
        for x,y in mounting+[(-22,0)]: plate=hole(plate,x,y)
        plate=slots(plate,[(-43,-w/2+25),(-43,w/2-25),(43,-w/2+25),(43,w/2-25)],slot)
        put('adapter_plate_'+label,plate,'adapter',(300,{'A':-190,'B':0,'C':190}[label],-100),active=False,variant=label,receiver_pattern=mounting,slots_mm=[slot,5.5])
    # Clamp halves: tie rods plus hooked replaceable jaws wrap an assumed edge.
    for label,z in [('upper',0),('lower',-p['clamp_opening']-20)]:
        half=box((80,w,10),(0,0,5))
        for x,y in [(-30,-w/2+10),(30,-w/2+10),(-30,w/2-10),(30,w/2-10),(-20,-25),(20,25)]: half=hole(half,x,y)
        half=slots(half,[(-25,-w/2+20),(25,w/2-20)],slot)
        put('base_clamp_'+label,half,'clamp',(300,-190,-120+z),active=False,variant='A',retention='four M5 tie rods; jaws hook behind captured edge, no friction-only release')
    for name,sign in [('jaw_left',-1),('jaw_right',1)]:
        jaw=box((65,25,8),(0,0,4))
        jaw=jaw.fuse(box((65,8,p['jaw_step']),(0,sign*8.5,8+p['jaw_step']/2)))
        jaw=slots(jaw,[(-20,0),(20,0)],slot)
        put(name,jaw,'jaw',(300,-190+sign*25,-130),active=False,variant='A',interchangeable=True,print_quantity=2,note='2 per half; orient hooks around opposed edges; lip is positive geometric capture')
    for sign in (-1,1):
        saddle=box((80,30,8),(0,0,4)).fuse(box((80,8,30),(0,11,19)))
        saddle=slots(saddle,[(-25,-3),(25,-3)],slot)
        put('saddle_foot_'+str(sign),saddle,'adapter',(300,sign*p['saddle_span']/2,-138),active=False,variant='B',retention='opposed shoulders plus two M5 tie rods and lower base_clamp_lower; captured support required')
    bench=box((150,w,10),(0,0,5))
    bench=slots(bench,[(x,y) for x in (-p['bench_pitch']/2,p['bench_pitch']/2) for y in (-45,45)],slot)
    for x,y in mounting: bench=hole(bench,x,y)
    put('bench_plate',bench,'adapter',(300,190,-120),active=False,variant='C',retention='4 M5 through bolts into bench with steel backing washers/plate')
    # Retain official Pi position, add ventilation and through base fixing.
    tray=items['pi5_concept_case']['shape']
    for x in (-60,-40,-20,0): tray=tray.cut(box((8,35,8),(x,260,-98)))
    for x,y in [(-82,240),(10,240),(-82,300),(10,300)]:
        tray=tray.cut(cq.Workplane('XY').center(x,y).circle(2.75).extrude(12).translate((0,0,-104)).val())
    local=tray.translate((36,-268,100))
    put('pi5_concept_case',local,'case',(-36,268,-100),fasteners='4 M2.5 board screws/nuts, 4 M5 tray/base screws; insulating spacers',ventilation='four 8x35 bottom slots; open sides and top; connector access volume retained')
    # Camera carriers use the official envelope and strap slots, not assumed PCB hole locations.
    for name in ('C_TOP','C_LEFT','C_RIGHT'):
        items[name]['connection']={'C_TOP':'CSI0 conceptual','C_LEFT':'CSI1 conceptual','C_RIGHT':'USB/UVC equivalent-envelope replacement; no converter selected'}[name]
        old=items['support_camera_module_3_'+name]['shape']; center=old.Center().toTuple()
        carrier=box((42,40,4),(0,0,2))
        carrier=slots(carrier,[(-16,0),(16,0)],12)
        for x,y in [(-14,-14),(-14,14),(14,-14),(14,14)]: carrier=hole(carrier,x,y,1.7)
        # Correct assembly transform of local build plate to the inherited optical plane.
        sign={'C_TOP':0,'C_LEFT':-1,'C_RIGHT':1}[name]
        placed=carrier.translate((0,0,-2))
        if sign: placed=placed.rotate((0,0,0),(1,0,0),-sign*90)
        put('support_camera_module_3_'+name,carrier,'camera_mount',center,fasteners='4 M3 bolts/nuts; nylon standoffs and soft straps outside lens/FPC',retention='strap slots; insulating pads under PCB, physical trial fit required')
        items['support_camera_module_3_'+name]['shape']=placed.translate(center)
        items['support_camera_module_3_'+name]['assembly_rotation_x_deg']=-sign*90
        # Existing short bracket gets cross holes using local bounding box plane.
        m=items['mount_'+name]['shape']; bb=m.BoundingBox()
        # Normalize inherited bracket for slicing; add holes normal to its thinnest axis.
        axis=min(range(3),key=lambda i:[bb.xlen,bb.ylen,bb.zlen][i])
        for offset in (-8,8):
            c=list(bb.center.toTuple()); c[0]+=offset
            direction=[0,0,0]; direction[axis]=1; start=[c[i]-100*direction[i] for i in range(3)]
            m=m.cut(cq.Solid.makeCylinder(2.75,200,cq.Vector(*start),cq.Vector(*direction)))
        items['mount_'+name]['shape']=m
        items['mount_'+name]['print_shape']=m.translate((-bb.xmin,-bb.ymin,-bb.zmin))
        items['mount_'+name]['fasteners']='M5 through bolts + metal bracket/T-nuts; inherited metal arm lengths cut to scene'
    # Sensor plates accept straps and slots, dimensions explicitly assumed.
    for n,size,pos in [('trigger_mount',(65,34,5),(-150,-115,77.5)),('diagnostic_mount',(40,30,5),(-70,-120,92)),('ky040_mount',(50,40,6),(-260,-143,-60))]:
        s=box(size,(0,0,size[2]/2)); s=slots(s,[(-size[0]/2+10,0),(size[0]/2-10,0)],12)
        put(n,s,'sensor_mount',pos,dimensions='ASSUMED envelope, adjustable straps; no real sensor hole pattern')
    coupling=box((50,35,8),(0,0,4)); coupling=slots(coupling,[(-15,0),(15,0)],14); coupling=hole(coupling,0,0,4)
    put('encoder_coupling_plate',coupling,'sensor_mount',(-260,-160,-45),note='8 mm assumed clearance, commercial flexible shaft coupler to roller required, diameter unselected')
    # Channels are fixed on profiles by M5 ears, with soft straps for strain relief.
    guide=box((48,28,4),(0,0,2))
    for y in (-12,12): guide=guide.fuse(box((28,4,12),(0,y,8)))
    for x in (-19,19): guide=hole(guide,x,0)
    guide=slots(guide,[(-8,0),(8,0)],7)
    for n in list(items):
        if n.startswith('cable_guide_'): del items[n]
    # multiple anchor stations and terminal tails, one reusable printable part
    fy=p['camera_spacing']/2+80; fz=p['top_height']+60
    # Guides follow the actual straight sections of the inherited rounded corridors.
    stations=[((150,fy+90,z),'Z') for z in (40,160,300,460)]
    stations += [((150,-p['camera_spacing']/2-55,z),'Z') for z in (240,400)]
    stations += [((150,0,fz+100),'Y'),((80,-50,p['top_height']+32),'X'),((80,p['camera_spacing']/2+55,p['product_envelope'][2]/2+35),'X')]
    for idx,(pos,axis) in enumerate(stations):
        n='cable_guide_%02d'%idx
        put(n,guide,'guide',pos,restraint='2 M5 bolts to stand-off + soft strap; 20 mm channel clearance')
        oriented=guide.translate((0,0,-8))
        if axis=='Z': oriented=oriented.rotate((0,0,0),(0,1,0),-90)
        if axis=='Y': oriented=oriented.rotate((0,0,0),(0,0,1),90)
        items[n]['shape']=oriented.translate(pos)
        items[n]['route_axis']=axis
        # Metal strap stock between profile and offset cable support; cut/drill to these assumed endpoints.
        anchor=(65,math.copysign(fy,pos[1]),min(pos[2],fz)) if axis=='Z' else (65,pos[1],fz+15)
        start=cq.Vector(*anchor); end=cq.Vector(*pos); vec=end-start
        arm=cq.Solid.makeCylinder(4,vec.Length,start,vec.normalized())
        items['guide_metal_standoff_%02d'%idx]={'shape':arm,'role':'hardware_envelope','printable':False,
            'endpoints_mm':[anchor,pos],'note':'M5-ended metal stand-off with angle cleats; rod is route envelope, size not load rated'}
    for n,c in items.items():
        if c['role']=='cable':
            c['frame_anchors']=['cable_guide_%02d'%i for i in range(9)]
            c['anchor_note']='M5 metal stand-offs connect actual corridor guide stations to frame, soft terminal restraint'
    # Lighting strap carriers, no invented light supplier.
    for name in ('C_TOP','C_LEFT','C_RIGHT'):
        center=items['light_'+name]['shape'].Center().toTuple()
        s=box((36,85,5),(0,0,2.5)); s=slots(s,[(0,-33),(0,33)],20)
        put('light_mount_'+name,s,'mount',(center[0],center[1],center[2]+10),fasteners='M5 metal angle to frame + soft straps around assumed luminaire')
    return items,refs

def printable(c):
    s=c.get('print_shape',c['shape']); b=s.BoundingBox()
    return s.translate((-b.xmin,-b.ymin,-b.zmin))

def metadata(items,refs,p):
    sources=list(r01.SOURCES.values())+[r01.VENDOR/'pi5/step/LICENSE.txt',ROOT/'cad/cadquery/concepts/optical-rig-r01/rig.py',ROOT/'data/concepts/optical-rig-r01.json']
    return {'status':p['status'],'release_class':p['release_class'],'prototype_print_allowed':True,'production_release':False,'measured':False,
      'parameters':p,'sources':[{'path':str(f.relative_to(ROOT)),'sha256':sha(f)} for f in sources],
      'limitations':['load','focus','FOV','real cable','real conveyor','safety'],
      'components':[{'name':n,**{k:v for k,v in c.items() if k not in ('shape','print_shape','collision_shape')},'bounds_mm':bounds(c['shape']),'volume_mm3':c['shape'].Volume(),
        **({'print_bounds_mm':bounds(printable(c)),'step':n+'.step','stl':n+'.stl'} if c['printable'] else {})} for n,c in items.items()]}

def preview(items,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig,axes=plt.subplots(1,3,figsize=(22,9))
    colors={'camera':'green','pi':'green','structure':'saddlebrown','cable':'purple','lighting':'orange','trigger':'red'}
    for ax,dims,title in zip(axes[:2],[(1,2),(0,1)],['FRONT Y/Z: three views, Pi and cable corridors','PLAN X/Y: upstream trigger / roller; transport +X']):
        for n,c in items.items():
            if c.get('active') is False or c['role'] in ('access','exclusion'): continue
            b=bounds(c['shape']); i,j=dims
            ax.add_patch(Rectangle((b[i],b[j]),b[i+3]-b[i],b[j+3]-b[j],fill=False,edgecolor=colors.get(c['role'],'steelblue'),lw=.7))
            if c['role'] in ('camera','pi','trigger','encoder','lighting','receiver','diagnostic'):
                ax.annotate(n,((b[i]+b[i+3])/2,(b[j]+b[j+3])/2),xytext=(5,8),textcoords='offset points',fontsize=7)
        ax.autoscale(); ax.set_aspect('equal'); ax.grid(alpha=.15); ax.set_title(title,fontsize=10)
    ax=axes[2]
    for idx,n in enumerate(['adapter_plate_A','receiver','tongue','cam_lever','captive_screw_keeper']):
        s=printable(items[n]); b=bounds(s); y=idx*55
        ax.add_patch(Rectangle((b[0],y),b[3]-b[0],max(6,b[5]-b[2]),fill=False,edgecolor='steelblue'))
        ax.text(0,y+30,n,fontsize=9)
    ax.set_xlim(-10,160); ax.set_ylim(-10,290); ax.set_aspect('equal'); ax.set_title('DOCK exploded schematic X/Z\nM5 pin through tongue / receiver / adapter',fontsize=10)
    fig.suptitle('R02 ASSUMPTION_DRIVEN / PROTOTYPE_CONCEPT; mm assumed; projection of envelopes, not a cutting template\nA: hooked clamp | B: captured saddle | C: bolted bench; same receiver; vendor bodies reference only')
    fig.tight_layout(); fig.savefig(out/'overview.pdf'); fig.savefig(out/'overview.png',dpi=140); plt.close(fig)

def generate(config=CONFIG,out=OUT):
    p=json.loads(config.read_text()); check_params(p)
    if out.exists() and any(out.iterdir()): raise ValueError('Refusing to overwrite existing artifacts')
    items,refs=build(p); out.mkdir(parents=True,exist_ok=True)
    for n,c in items.items():
        if c['printable']:
            s=printable(c)
            assert s.isValid() and len(s.Solids())==1,n
            assert max(bounds(s)[3:])<=220,n
            cq.exporters.export(s,str(out/(n+'.step')))
            cq.exporters.export(s,str(out/(n+'.stl')),tolerance=.05,angularTolerance=.1)
    jsonwrite(out/'components.json',metadata(items,refs,p)); preview(items,out)
    print('GENERATED',out)
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--config',type=Path,default=CONFIG); ap.add_argument('--out',type=Path,default=OUT)
    a=ap.parse_args(); generate(a.config,a.out)
