#!/usr/bin/env python3
"""Readback and independent geometry gate. PASS is never fabrication approval."""
import argparse
import importlib.util
import itertools
import json
import subprocess
import sys
from pathlib import Path
import cadquery as cq
import trimesh
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rig',ROOT/'cad/cadquery/concepts/optical-rig-r01/rig.py')
rig=importlib.util.module_from_spec(spec); spec.loader.exec_module(rig)

def presence(d):
    assert d['status']=='REFERENCE_ONLY' and d['fabrication_allowed'] is False and d['measured'] is False
    rig.check_params(d['parameters'])
    names=[c['name'] for c in d['components']]
    assert len(names)==len(set(names))
    required={'C_TOP','C_LEFT','C_RIGHT','PI5','TRIGGER_E18','dock_interface','channel_C_TOP','channel_C_LEFT','channel_C_RIGHT'}
    assert required<=set(names), 'missing required components'
    assert sum(c['role']=='camera' for c in d['components'])==3
    return required

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,default=rig.OUT); a=ap.parse_args(); out=a.out
    d=json.loads((out/'components.json').read_text()); required=presence(d)
    negatives=[]
    for name in sorted(required):
        m=json.loads(json.dumps(d)); m['components']=[c for c in m['components'] if c['name']!=name]
        try: presence(m)
        except AssertionError: negatives.append('missing '+name)
        else: raise AssertionError('negative test accepted '+name)
    for status in ('PASS','MEASURED','FABRICATION_ALLOWED',None):
        m=dict(d,status=status)
        try: presence(m)
        except AssertionError: negatives.append('status '+str(status))
        else: raise AssertionError('bad status accepted')
    for src in d['sources']: assert rig.sha(ROOT/src['path'])==src['sha256'], src['path']
    items,refs=rig.build(d['parameters'])
    fresh=rig.metadata(items,refs,d['parameters'])
    assert {k:v for k,v in fresh.items() if k!='components'}=={k:v for k,v in d.items() if k!='components'}, 'reference/parameter metadata mismatch'
    assert len(fresh['components'])==len(d['components'])
    for expected,stored in zip(fresh['components'],d['components']):
        keys=('bounds_mm','volume_mm3')
        assert {k:v for k,v in expected.items() if k not in keys}=={k:v for k,v in stored.items() if k not in keys}, expected['name']
        assert max(abs(a-b) for a,b in zip(expected['bounds_mm'],stored['bounds_mm']))<1e-5, ('manifest bounds',expected['name'])
        assert abs(expected['volume_mm3']-stored['volume_mm3'])<1e-3, ('manifest volume',expected['name'])
    checks=[]; exported=[]
    for n,c in items.items():
        s=c['shape']; assert s.Volume()>0 and all(np.isfinite(rig.bounds(s)))
        if c['role'] not in ('camera','pi'): assert s.isValid(), n
        if not c['printable']: continue
        step=cq.importers.importStep(str(out/(n+'.step'))).val()
        mesh=trimesh.load_mesh(out/(n+'.stl'),process=True)
        assert step.isValid() and len(step.Solids())==1, n
        assert max(abs(x-y) for x,y in zip(rig.bounds(step),rig.bounds(s)))<1e-5,n
        assert abs(step.Volume()-s.Volume())<1e-3,n
        assert mesh.is_watertight and mesh.is_volume and np.isfinite(mesh.vertices).all(), n
        assert np.max(np.abs(mesh.bounds.flatten()-np.array(rig.bounds(s))))<.1,n
        assert abs(mesh.volume-s.Volume())<max(1,s.Volume()*.01), n
        proc=subprocess.run([sys.executable,str(ROOT/'scripts/validate_mesh.py'),str(out/(n+'.stl'))],capture_output=True,text=True)
        assert proc.returncode==0, proc.stdout+proc.stderr
        checks.append({'name':n,'step_solids':1,'mesh':'PASS','existing_validator':proc.stdout.strip()})
        exported.extend([n+'.step',n+'.stl'])
    assert {f.name for f in out.iterdir() if f.suffix.lower() in ('.step','.stp','.stl')}==set(exported), 'unexpected export (vendor/assembly forbidden)'
    collisions=[]; clearances=[]
    access_checks=[]
    for n,c in items.items():
        if c['role']=='structure':
            v=c['shape'].intersect(items['PI_connector_access']['shape']).Volume()
            assert v<1e-5, ('PI access',n,v)
            access_checks.append({'structure':n,'intersection_mm3':v})
    physical={n:c.get('collision_shape',c['shape']) for n,c in items.items() if c.get('active',True) and c['role'] not in ('mockup','exclusion','access')}
    for n,s in physical.items():
        for zone in ('belt_GENERIC','product_sweep','roller_GENERIC'):
            v=s.intersect(items[zone]['shape']).Volume()
            clearances.append({'component':n,'zone':zone,'intersection_mm3':v,'distance_mm':s.distance(items[zone]['shape'])})
            assert v<1e-5,(n,zone,v)
    # Complete broad phase then exact BRep common-volume on candidate pairs.
    for (n,s),(m,t) in itertools.combinations(physical.items(),2):
        b=rig.bounds(s); c=rig.bounds(t)
        if not all(min(b[i+3],c[i+3])-max(b[i],c[i])>1e-6 for i in range(3)): continue
        v=s.intersect(t).Volume()
        if v>1e-5:
            assert items[n]['role'] not in ('camera','pi') and items[m]['role'] not in ('camera','pi'), ('electronics interference',n,m,v)
            allowed={frozenset(pair) for pair in [('post_LEFT','metal_arm_C_LEFT'),('post_RIGHT','metal_arm_C_RIGHT'),('trigger_mount','trigger_metal_arm'),('trigger_metal_arm','trigger_post'),('trigger_metal_arm','diagnostic_metal_arm')]}
            shared=items[n]['role']==items[m]['role']=='cable'
            assert shared or frozenset((n,m)) in allowed, ('unexpected overlap',n,m,v)
            collisions.append({'a':n,'b':m,'intersection_mm3':v,'classification':'shared conceptual corridor; physical separation pending' if shared else 'conceptual hardware engagement; joint detailing pending'})
    cables=[]
    for n,c in items.items():
        if c['role']=='cable':
            assert c['route_mm']+c['allowance_mm']<=c['available_mm'], n
            cables.append({k:v for k,v in c.items() if k!='shape'})
    assert items['TRIGGER_E18']['shape'].Center().x<0
    assert items['KY040_on_roller']['shape'].distance(items['roller_GENERIC']['shape'])<20
    assert all(c.get('holes')==[] for c in items.values() if c['role']=='adapter')
    result={'status':'PASS_REFERENCE_ONLY','fabrication_allowed':False,'negative_tests':negatives,'exports':checks,'collision_method':'BRep common volume; vendor conservative STEP bounding boxes; static defaults only','pi_access_checks':access_checks,'pair_overlaps':collisions,'exclusion_checks':clearances,'cables':cables,'limitations':'Overlaps require engineering interpretation; no real machine geometry, FOV, FPC torsion, structural or assembly release.'}
    rig.jsonwrite(out/'validation.json',result)
    print('PASS_REFERENCE_ONLY:',len(checks),'STEP/STL pairs;',len(clearances),'exclusion checks;',len(negatives),'negative tests;',len(collisions),'pair overlaps documented')
if __name__=='__main__':
    try: main()
    except (AssertionError,KeyError,ValueError,OSError) as e:
        print('FAIL:',repr(e)); sys.exit(1)
