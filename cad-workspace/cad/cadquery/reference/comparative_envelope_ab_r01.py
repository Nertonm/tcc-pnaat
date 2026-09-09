#!/usr/bin/env python3
"""Comparative reference envelopes only. No mounting geometry or fabrication authority."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import traceback
import cadquery as cq
import numpy as np
import trimesh
import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'exports/reference-envelope/ab-r01'
REPORT = ROOT / 'reports/REFERENCE-ENVELOPE-AB.md'
FLAGS = dict(reference_only=True, measured=False, fabrication_allowed=False)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, obj):
    with p.open('x') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')

def bounds(s):
    b = s.BoundingBox()
    return [[b.xmin, b.ymin, b.zmin], [b.xmax, b.ymax, b.zmax]]

def validate():
    """Separate process: only serialized STEP, STL and component expectations."""
    m = json.loads((OUT/'components.json').read_text())
    step = OUT/'comparative_REFERENCE_ONLY.step'
    solids = cq.importers.importStep(str(step)).val().Solids()
    remaining = list(solids)
    rows = []
    serialized = {}
    for r in m['components']:
        matches = [s for s in remaining if np.allclose(bounds(s), r['bounds_mm'], atol=1e-5, rtol=0)
                   and abs(s.Volume()-r['volume_mm3']) <= 1e-5]
        s = matches[0] if len(matches) == 1 else None
        if s is not None:
            remaining.remove(s)
            serialized[r['name']] = s
        raw = trimesh.load_mesh(OUT/r['stl'], process=False)
        mesh = raw.copy()
        mesh.merge_vertices()  # STL duplicates vertices; no repair or face removal.
        delta = float(np.max(np.abs(raw.bounds-np.array(r['bounds_mm']))))
        checks = dict(step_unique_match=s is not None,
                      step_valid_positive_finite=s is not None and s.isValid() and s.Volume()>0 and math.isfinite(s.Volume()) and bool(np.isfinite(bounds(s)).all()),
                      mesh_finite=bool(np.isfinite(raw.vertices).all()) and bool(np.isfinite(raw.faces).all()),
                      mesh_watertight=bool(mesh.is_watertight), mesh_winding=bool(mesh.is_winding_consistent),
                      mesh_positive_volume=bool(mesh.is_volume) and math.isfinite(mesh.volume) and mesh.volume>0,
                      bounds_serialization=delta <= 0.1,
                      step_stl_bounds=s is not None and bool(np.allclose(bounds(s), raw.bounds, atol=0.1, rtol=0)))
        rows.append(dict(name=r['name'], checks=checks, step_bounds_mm=bounds(s) if s is not None else None,
                         stl_bounds_mm=raw.bounds.tolist(), max_bounds_delta_mm=delta, mesh_volume_mm3=float(mesh.volume)))
    required = {'belt_nominal','generic_side_left','generic_side_right','roller_keepout_start','roller_keepout_end',
                'motor_keepout','bottle','camera_top','camera_left','camera_right','trigger','lighting_top',
                'lighting_left','lighting_right','cable_top','cable_left','cable_right','common_optical_interface_ABSTRACT',
                'forbidden_belt_support'}
    optical = {n for n in required if n.startswith(('camera','lighting','cable','trigger','common_'))}
    checks = dict(all_components=not remaining and len(rows)==len(solids) and all(all(r['checks'].values()) for r in rows))
    contacts = {}
    for scene in ('CONVEYOR_A_REFERENCE','CONVEYOR_B_REFERENCE'):
        names={r['local_name'] for r in m['components'] if r['scene']==scene}
        checks[scene+'_coverage'] = names == required
        checks[scene+'_step_name'] = scene in step.read_text()
        belt=serialized.get(scene+'__belt_nominal')
        for n in optical:
            s=serialized.get(scene+'__'+n)
            distance = s.distance(belt) if s is not None and belt is not None else None
            contacts[scene+'__'+n] = distance
        checks[scene+'_no_optical_belt_contact'] = all(contacts[scene+'__'+n] is not None and contacts[scene+'__'+n]>1e-5 for n in optical)
    # Compare local coordinates after removing the presentation offset only.
    rec={(r['scene'],r['local_name']):r for r in m['components']}
    checks['common_optical_layout_identical'] = all(
        rec[('CONVEYOR_A_REFERENCE',n)]['local_center_mm']==rec[('CONVEYOR_B_REFERENCE',n)]['local_center_mm'] and
        rec[('CONVEYOR_A_REFERENCE',n)]['dimensions_mm']==rec[('CONVEYOR_B_REFERENCE',n)]['dimensions_mm'] for n in optical)
    result=dict(**FLAGS, provenance={'components_sha256':sha(OUT/'components.json'),'step_sha256':sha(step)},
                gate='PASS' if all(checks.values()) else 'FAIL', checks=checks, components=rows,
                optical_to_belt_distances_mm=contacts, step_solid_count=len(solids),
                serialization_tolerances={'step_bounds_mm':1e-5,'step_volume_mm3':1e-5,'stl_bounds_mm':0.1,
                    'stl_deflection_mm':0.1,'stl_angle_rad':0.1,'note':'Serialização somente; não é precisão ou tolerância mecânica.'},
                mesh_processing='process=False then merge_vertices only; no repair',
                limits='No support path modeled. Positive distances are synthetic occupancy checks, not structural or physical safety evidence.')
    write(OUT/'readback_validation.json',result)
    print(result['gate'],len(solids),'STEP solids;',len(rows),'separate STL envelopes')
    return 0 if all(checks.values()) else 1

def main():
    # Optional environment metadata; no host/container gate.
    if REPORT.exists():
        raise FileExistsError(REPORT)
    OUT.mkdir(parents=True,exist_ok=False)
    manifest=dict(**FLAGS,evidence='SPECULATIVE',decision='OPEN',validation_gate='INCOMPLETE',
                  provenance={},commands=[],tools={'cadquery':cq.__version__,'trimesh':trimesh.__version__},
                  environment={'container':os.environ.get('CAD_ENVIRONMENT', 'unspecified'),'cwd':str(ROOT)},
                  scope='Digital reference only; no adapters, holes, datums, clamps, materials or structural parts.')
    code=1
    try:
        data={}
        for family in ('a','b'):
            p=ROOT/f'data/g0/esteira-{family}-reference-r01.yaml'
            d=yaml.safe_load(p.read_text())
            assert d['status']=='reference_only' and d['units']=='mm'
            assert d['provenance']['measured'] is False and d['provenance']['fabrication_allowed'] is False
            assert d['reference_scenario']['fabrication_allowed'] is False
            for group in (d['reference_scenario']['selected_nominal'],):
                for k,v in group.items():
                    assert type(v) in (int,float) and math.isfinite(v) and (v>0 or k=='belt_top_z_mm')
            for env in d['reference_scenario']['envelopes_mm'].values():
                assert all(type(env[k]) in (int,float) and math.isfinite(env[k]) and env[k]>0 for k in ('width','depth','height'))
            data[family]=d
            manifest['provenance'][family]={'path':str(p.relative_to(ROOT)),'sha256':sha(p),'reference_id':d['reference_id']}
        manifest['provenance']['script']={'path':str(Path(__file__).relative_to(ROOT)),'sha256':sha(Path(__file__))}
        assembly=cq.Assembly(name='AB_REFERENCE_ONLY_NON_FABRICABLE')
        rows=[]
        bn=data['b']['reference_scenario']['selected_nominal']
        optical=data['b']['optical_envelope']
        centers={k:optical['cameras'][v]['center_xyz_mm'] for k,v in [('top','top'),('left','side_left'),('right','side_right')]}
        # Common optics is a reference comparison assumption; fail if input sizes differ.
        keys=('bottle','camera_top','camera_side','trigger','lighting_top','lighting_side','cable_bundle')
        assert all(data['a']['reference_scenario']['envelopes_mm'][k]==data['b']['reference_scenario']['envelopes_mm'][k] for k in keys)
        offset_y=2*(data['a']['reference_scenario']['selected_nominal']['belt_width_mm']+data['a']['reference_scenario']['envelopes_mm']['motor_keepout']['depth']+bn['belt_width_mm'])
        for family in ('a','b'):
            scene='CONVEYOR_'+family.upper()+'_REFERENCE'
            sub=cq.Assembly(name=scene)
            n=data[family]['reference_scenario']['selected_nominal']; e=data[family]['reference_scenario']['envelopes_mm']
            L,W,z=n['conveyor_length_mm'],n['belt_width_mm'],n['belt_top_z_mm']
            offset=[0,0 if family=='a' else offset_y,0]
            def box(name,dims,c,rule,role='visual envelope'):
                assert all(math.isfinite(v) and v>0 for v in dims) and all(math.isfinite(v) for v in c)
                s=cq.Workplane('XY').box(*dims).translate(c).val()
                assert s.isValid() and s.Volume()>0
                color=cq.Color(1,0.2,0.1,0.3) if ('keepout' in name or 'forbidden' in name) else cq.Color(0.2,0.6,0.9,0.55)
                if name.startswith('common_'): color=cq.Color(0.6,0.2,0.8,0.3)
                sub.add(s,name=name,color=color)
                global_s=s.translate(offset)
                path=f'{scene}__{name}.stl'
                cq.exporters.export(global_s,str(OUT/path),tolerance=0.1,angularTolerance=0.1)
                rows.append(dict(**FLAGS,evidence='SPECULATIVE',name=scene+'__'+name,scene=scene,local_name=name,
                    dimensions_mm=dims,local_center_mm=c,presentation_offset_mm=offset,bounds_mm=bounds(global_s),
                    volume_mm3=global_s.Volume(),stl=path,role=role,provenance_rule=rule))
            def env(name,key,c,rule):
                box(name,[e[key][k] for k in ('width','depth','height')],c,rule+'; size: own YAML reference_scenario.envelopes_mm.'+key)
            t=bn['side_plate_thickness_mm'] if family=='b' else e['cable_bundle']['height']
            depth=bn['roller_diameter_mm'] if family=='b' else e['motor_keepout']['height']
            lateral=bn['side_plate_thickness_mm'] if family=='b' else n['side_clearance_mm']
            rule=('B nominal plate thickness and roller diameter; rectangular roller exclusion, not roller solid' if family=='b' else
                  'A unknown thickness/roller size NOT filled: cable height for belt display, side_clearance for lateral band, motor height for end/depth exclusion glyph; no real surface or roller diameter')
            box('belt_nominal',[L,W,t],[0,0,z-t/2],rule+'; nominal L/W; display depth only','belt reference')
            # Separate coincident designation, intentionally not fused with the belt envelope.
            box('forbidden_belt_support',[L,W,t],[0,0,z-t/2],rule+'; coincident semantic prohibition; no structural belt support','forbidden region')
            for sign,label in ((-1,'left'),(1,'right')):
                box('generic_side_'+label,[L,lateral,depth],[0,sign*(W+lateral)/2,z-depth/2],rule,'generic lateral region; no mounting surface')
            for sign,label in ((-1,'start'),(1,'end')):
                box('roller_keepout_'+label,[depth,W,depth],[sign*L/2,0,z-depth/2],rule,'nominal exclusion; actual extent unknown')
            motor=e['motor_keepout']
            env('motor_keepout','motor_keepout',[-L/2,W/2+lateral+motor['depth']/2,z-motor['height']/2],
                'nominal region at upstream lateral end; placement speculative, no real clearance')
            env('bottle','bottle',[0,0,z+e['bottle']['height']/2],'centered nominal bottle bounding box')
            for label,c in centers.items():
                key='camera_top' if label=='top' else 'camera_side'
                env('camera_'+label,key,c,'same B optical_envelope camera center in both scenarios; A transfer hypothesis')
                env('cable_'+label,'cable_bundle',[c[0],c[1],c[2]+e[key]['height']/2+e['cable_bundle']['height']],
                    'local occupancy above camera by camera half-height + cable height; no cable routing')
            env('trigger','trigger',optical['trigger']['center_xyz_mm'],'same B trigger center in both scenarios')
            env('lighting_top','lighting_top',[0,e['camera_top']['depth']/2+e['lighting_top']['depth'],centers['top'][2]],
                'top camera y + half camera depth + lighting depth')
            for sign,label in ((-1,'left'),(1,'right')):
                env('lighting_'+label,'lighting_side',[0,sign*(abs(centers[label][1])+e['camera_side']['depth']/2+e['lighting_side']['depth']/2+e['cable_bundle']['depth']),centers[label][2]],
                    'outside side camera by half camera depth + half light depth + cable depth; common layout')
            # An occupancy marker above optics, not a bridge, datum or attachable plate.
            h=e['cable_bundle']['height']
            box('common_optical_interface_ABSTRACT',[e['lighting_top']['width'],2*abs(centers['right'][1])+e['camera_side']['depth'],h],
                [0,0,centers['top'][2]+e['camera_top']['height']/2+3*h],
                'abstract common region: lighting width x lateral camera outer span x cable height; z above top camera by half-height + 3 cable heights',
                'abstract occupancy marker; no fixing surface, datum or support geometry')
            assembly.add(sub,loc=cq.Location(cq.Vector(*offset)))
        assembly.export(str(OUT/'comparative_REFERENCE_ONLY.step'))
        write(OUT/'components.json',dict(**FLAGS,provenance=manifest['provenance'],components=rows,
              presentation='Two scenes separated in y for viewing; local origin is synthetic, not a datum. Coincident belt/forbidden volumes intentional; per-component STL only, no fabrication union.'))
        command=[sys.executable,str(Path(__file__)),'--validate']
        p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        (OUT/'validation.log').write_text(p.stdout+p.stderr)
        manifest['commands'].append({'argv':command,'exit_code':p.returncode})
        if p.returncode: raise RuntimeError('Independent readback failed; see validation.log')
        validation=json.loads((OUT/'readback_validation.json').read_text())
        manifest['validation_gate']='PASS'
        report='''# Envelope comparativo A/B - referência visual\n\nreference_only=true; measured=false; fabrication_allowed=false. Evidência: SPECULATIVE. Gate digital: PASS. Decisão: OPEN.\n\nO envelope permite manter a Arq.1 como opção tecnicamente plausível **somente nos dois cenários nominais de referência**, pois a disposição óptica comum permanece idêntica e afastada da correia nas duas cenas. Nenhum resultado prova compatibilidade com as máquinas reais ou libera fabricação. Não demonstra superioridade, menor custo, rigidez, repetibilidade ou fabricabilidade.\n\nA: nominal 1500 × 190 mm; B: nominal 450 × 200 mm. A Large (1470 × 300 mm) e os extremos intervalares de B não foram validados. As posições ópticas de B foram transferidas como hipótese para A. Não foram modelados adaptadores, furos, datums, clamps nem caminhos de carga. A interface comum é apenas uma região abstrata acima das câmeras.\n\nAs dimensões ausentes de A continuam BLOCKED. Laterais e roletes de A são símbolos volumétricos derivados de side_clearance e motor_keepout; a espessura de exibição da correia reutiliza cable_bundle.height. Não representam espessuras, diâmetros ou superfícies reais. Em B, roletes são caixas de exclusão com o diâmetro nominal como extensão. Cada fórmula e fonte consta em components.json. A origem é sintética; o deslocamento entre cenas serve apenas à apresentação.\n\nHá três câmeras, trigger, três regiões de iluminação, três ocupações locais de cabos, garrafa, laterais e exclusões em cada cena. Cabos não representam rotas verificadas. Garrafa toca nominalmente a correia como produto transportado. A região proibida da correia coincide intencionalmente com seu envelope. Nenhum elemento óptico toca a correia; isso não verifica um suporte, pois suporte estrutural não foi modelado. Não houve avaliação de campo de visão, foco, oclusão, curso do produto ou colisões de rotas completas.\n\nValidação em processo separado: readback STEP e STL por componente, correspondência unívoca por bounds/volume, sólidos válidos, valores finitos, malhas fechadas com volume positivo e orientação consistente, nomes das cenas, cobertura de todos os componentes e afastamento óptico da correia. Apenas união de vértices coincidentes no STL; sem reparo. Serialização: STEP 1e-5 mm e 1e-5 mm³; STL 0,1 mm e tesselação angular 0,1 rad. Esses valores não são precisão mecânica.\n\nBloqueios físicos: identificar A e B, medir interfaces de chassi, laterais, roletes/motor e regiões proibidas, levantar envelope e massa/CG do módulo, óptica e cabos reais; G0/M0/P1 e revisão humana seguem necessários. Próxima medição: caracterizar primeiro B, largura/comprimento efetivos, espessuras laterais, posição/extensão de motor/roletes e interfaces estruturais independentes da correia, com instrumento, método e repetição; depois A.\n\nSTEP: `exports/reference-envelope/ab-r01/comparative_REFERENCE_ONLY.step`. STL separados destinam-se exclusivamente à inspeção digital. Manifest, readback, auditoria e SHA256SUMS acompanham a revisão. Hashes formam grafo sem ciclo: manifest referencia payloads; auditoria referencia manifest; SHA256SUMS cobre ambos e não inclui a si mesmo.\n\n## Bounds globais por componente (mm)\n\n| Cena / componente | Mínimo [x,y,z] | Máximo [x,y,z] |\n|---|---|---|\n'''
        for r in rows:
            report+=f"| {r['name']} | {r['bounds_mm'][0]} | {r['bounds_mm'][1]} |\n"
        with REPORT.open('x') as f: f.write(report)
        code=0
    except Exception:
        manifest['validation_gate']='FAIL'
        (OUT/'failure.log').write_text(traceback.format_exc())
        traceback.print_exc()
    finally:
        manifest['commands'].append({'argv':[sys.executable,str(Path(__file__))],'exit_code':code})
        manifest['artifacts']={str(p.relative_to(ROOT)):{'sha256':sha(p),'provenance':'generated by script and reference inputs above'} for p in sorted(OUT.iterdir()) if p.is_file()}
        if REPORT.exists(): manifest['artifacts'][str(REPORT.relative_to(ROOT))]={'sha256':sha(REPORT),'provenance':'reference comparison and serialized readback'}
        write(OUT/'manifest.json',manifest)
    print('PASS_REFERENCE_ONLY' if code==0 else 'FAIL_REFERENCE_ONLY','exit_code='+str(code))
    return code

if __name__=='__main__':
    sys.exit(validate() if sys.argv[1:]==['--validate'] else main())
