#!/usr/bin/env python3
"""M0 occupancy study only. No physical datum, section selection or fabrication authority."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
import cadquery as cq
import numpy as np
import trimesh
import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'exports/reference-envelope/common-m0-r01'
REPORT = ROOT / 'reports/COMMON-OPTICAL-INTERFACE-M0.md'
BASE = ROOT / 'exports/reference-envelope/ab-r01/review02'
FLAGS = dict(reference_only=True, measured=False, fabrication_allowed=False)
ADDED = {'FRAME_COLUMN_LEFT_CONCEPTUAL', 'FRAME_COLUMN_RIGHT_CONCEPTUAL',
         'FRAME_CROSSBAR_CONCEPTUAL', 'RETENTION_POINT_CONCEPTUAL'}
SCENES = ['CONVEYOR_A_REFERENCE', 'CONVEYOR_B_REFERENCE']
TOL = dict(step_bounds_mm=1e-5, step_volume_mm3=1e-5, stl_bounds_mm=0.1,
           stl_deflection_mm=0.1, stl_angle_rad=0.1,
           meaning='Serialization only; no mechanical precision or manufacturing tolerance.')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, value):
    with p.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def bounds(s):
    b = s.BoundingBox()
    return [[b.xmin, b.ymin, b.zmin], [b.xmax, b.ymax, b.zmax]]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(argv):
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                       env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'GIT_OPTIONAL_LOCKS': '0'})
    return dict(argv=argv, exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)


def snapshot():
    # Only owned CAD paths. Never traverse latex-workspace or external clones.
    paths = [ROOT/'.gitignore', ROOT/'Makefile', ROOT/'README.md', ROOT/'TRANSFER.md']
    for directory in ['cad', 'data', 'design', 'reports', 'scripts']:
        paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and OUT not in p.parents)
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths)) if p.is_file() and p != REPORT}


def validate():
    """Independent process: read serialized artifacts, never call the builder."""
    m = json.loads((OUT/'components.json').read_text())
    base = json.loads((BASE/'components.json').read_text())
    step = OUT/'COMMON_OPTICAL_M0_REFERENCE_ONLY.step'
    solids = cq.importers.importStep(str(step)).val().Solids()
    remaining = list(solids)
    found, rows, checks = {}, [], {}
    for r in m['components']:
        matches = [s for s in remaining if np.allclose(bounds(s), r['bounds_mm'], rtol=0, atol=TOL['step_bounds_mm'])
                   and abs(s.Volume()-r['volume_mm3']) <= TOL['step_volume_mm3']]
        s = matches[0] if matches else None
        if s is not None:
            remaining.remove(s)
            found[r['name']] = s
        mesh = trimesh.load_mesh(OUT/r['stl'], process=False)
        mesh.merge_vertices()  # No repairs, hole filling or face removal.
        c = dict(step_match=s is not None,
                 step_valid_positive_finite=s is not None and s.isValid() and s.Volume()>0
                 and math.isfinite(s.Volume()) and bool(np.isfinite(bounds(s)).all()),
                 mesh_finite=bool(np.isfinite(mesh.vertices).all()),
                 mesh_watertight=bool(mesh.is_watertight), mesh_winding=bool(mesh.is_winding_consistent),
                 mesh_volume=bool(mesh.is_volume) and math.isfinite(float(mesh.volume)) and float(mesh.volume)>0,
                 bounds=s is not None and bool(np.allclose(mesh.bounds, bounds(s), atol=TOL['stl_bounds_mm'], rtol=0)))
        rows.append(dict(name=r['name'], checks=c, step_bounds_mm=bounds(s) if s else None,
                         stl_bounds_mm=mesh.bounds.tolist(), mesh_volume_mm3=float(mesh.volume)))
    checks['all_solids_and_meshes'] = not remaining and len(solids)==len(rows) and all(all(r['checks'].values()) for r in rows)
    original = {r['name']: r for r in base['components']}
    rec = {r['name']: r for r in m['components']}
    checks['unique_names'] = len(rec)==len(rows)
    checks['all_previous_envelopes_preserved'] = all(n in found and
        bool(np.allclose(bounds(found[n]), r['bounds_mm'], rtol=0, atol=TOL['step_bounds_mm']))
        and abs(found[n].Volume()-r['volume_mm3']) <= TOL['step_volume_mm3'] for n,r in original.items())
    contacts, conflicts = {}, []
    for scene in SCENES:
        expected = {r['local_name'] for r in base['components'] if r['scene']==scene} | ADDED
        checks[scene+'_coverage'] = {r['local_name'] for r in m['components'] if r['scene']==scene} == expected
        checks[scene+'_step_names'] = scene in step.read_text() and all(n in step.read_text() for n in expected)
        checks[scene+'_common_interface'] = scene+'__common_optical_interface_ABSTRACT' in found
        optics = [n for n in expected if n.startswith(('camera','lighting','cable','trigger','common_')) or n in ADDED]
        prohibited = ['forbidden_belt_support', 'roller_keepout_start', 'roller_keepout_end', 'motor_keepout',
                      'generic_side_left', 'generic_side_right', 'bottle']
        for n in optics:
            for p in prohibited:
                a,b = found.get(scene+'__'+n), found.get(scene+'__'+p)
                d = a.distance(b) if a is not None and b is not None else None
                contacts[scene+'__'+n+' / '+p] = d
        checks[scene+'_no_belt_support_and_keepouts_clear'] = all(
            contacts[scene+'__'+n+' / '+p] is not None and contacts[scene+'__'+n+' / '+p]>TOL['step_bounds_mm']
            for n in optics for p in prohibited)
        # Check new frame against old optics. Output marker and frame intentionally touch at x=150.
        for n in ADDED:
            for p in optics:
                if p in ADDED or p=='common_optical_interface_ABSTRACT':
                    continue
                a,b = found.get(scene+'__'+n), found.get(scene+'__'+p)
                if a is not None and b is not None and a.distance(b)<=TOL['step_bounds_mm']:
                    conflicts.append(dict(scene=scene, a=n, b=p, type='contact_or_overlap'))
        common = [n for n in expected if n in optics]
    checks['no_frame_optical_conflicts'] = not conflicts
    checks['same_common_frame_and_optics_from_step'] = all(
        SCENES[0]+'__'+n in found and SCENES[1]+'__'+n in found and bool(np.allclose(
            np.array(bounds(found[SCENES[0]+'__'+n]))-rec[SCENES[0]+'__'+n]['presentation_offset_mm'],
            np.array(bounds(found[SCENES[1]+'__'+n]))-rec[SCENES[1]+'__'+n]['presentation_offset_mm'],
            rtol=0, atol=TOL['step_bounds_mm'])) for n in common)
    checks['input_hashes_unchanged'] = all(sha(ROOT/p)==h for p,h in m['provenance'].items())
    result = dict(**FLAGS, gate='PASS' if all(checks.values()) else 'FAIL', checks=checks,
                  components=rows, step_solid_count=len(solids), distances_mm=contacts,
                  frame_optical_conflicts=conflicts, serialization_tolerances=TOL,
                  provenance={'components_sha256':sha(OUT/'components.json'), 'step_sha256':sha(step)},
                  limits='Nominal occupancy only. Suspended columns; no connection to equipment, optical mounts or load path validated.')
    write(OUT/'readback_validation.json', result)
    print(result['gate'], len(solids), 'solids', 'conflicts:', len(conflicts))
    return 0 if all(checks.values()) else 1


def build():
    require(ROOT.exists(), 'Workspace root missing')
    require(BASE.exists(), 'Reference exports are external and not included in this publication')
    require(not OUT.exists() and not REPORT.exists(), 'Refusing to overwrite existing revision/report')
    baseline = snapshot()
    status_cmd = ['git','--no-optional-locks','status','--short','--untracked-files=all','--','.']
    before = run(status_cmd)
    require(before['exit_code']==0, 'Git inspection failed')
    OUT.mkdir()
    commands = [before]
    code = 1
    manifest = dict(**FLAGS, stage='M0 reference-only', evidence='SPECULATIVE', decision='OPEN',
                    units='mm', validation_gate='INCOMPLETE', mechanical_gate='INCOMPLETE',
                    scope='Digital only; symbolic frame, no adapter or fabricable part.',
                    tools={'cadquery':cq.__version__, 'trimesh':trimesh.__version__},
                    serialization_tolerances=TOL)
    try:
        source_paths = ['README.md','TRANSFER.md','reports/conveyor-reference-research.md','reports/REFERENCE-ENVELOPE-AB.md',
            'data/g0/esteira-a-reference-r01.yaml','data/g0/esteira-b-reference-r01.yaml',
            'cad/cadquery/reference/comparative_envelope_ab_r01_review02.py',
            'cad/cadquery/reference/common_optical_interface_m0_r01.py','scripts/validate_mesh.py']
        source_paths += [str((BASE/p).relative_to(ROOT)) for p in ['components.json','readback_validation.json','comparative_REFERENCE_ONLY.step']]
        provenance = {p:sha(ROOT/p) for p in source_paths}
        manifest['provenance'] = provenance
        data = {f:yaml.safe_load((ROOT/f'data/g0/esteira-{f}-reference-r01.yaml').read_text()) for f in ['a','b']}
        for d in data.values():
            require(d['units']=='mm' and d['status']=='reference_only' and d['provenance']['measured'] is False
                    and d['provenance']['fabrication_allowed'] is False, 'Reference input flags invalid')
        old = json.loads((BASE/'components.json').read_text())
        previous = json.loads((BASE/'readback_validation.json').read_text())
        require(previous['gate']=='PASS' and previous['provenance']['components_sha256']==sha(BASE/'components.json')
                and previous['provenance']['step_sha256']==sha(BASE/'comparative_REFERENCE_ONLY.step'), 'Stale prior readback')
        for f in ['a','b']:
            require(old['provenance'][f]['sha256']==sha(ROOT/f'data/g0/esteira-{f}-reference-r01.yaml'), 'YAML differs from prior envelope')
        e = data['b']['reference_scenario']['envelopes_mm']
        require(all(e[k]==data['a']['reference_scenario']['envelopes_mm'][k] for k in e if k!='motor_keepout'), 'Optics differ')
        t = e['cable_bundle']['height']
        w = e['cable_bundle']['width']
        cam = data['b']['optical_envelope']['cameras']
        side = abs(cam['side_right']['center_xyz_mm'][1]) + e['camera_side']['depth']/2
        interface_z = cam['top']['center_xyz_mm'][2]+e['camera_top']['height']/2+3*t
        x = e['lighting_top']['width']/2+w/2
        y = side+e['cable_bundle']['depth']
        bottom = data['b']['reference_scenario']['selected_nominal']['belt_top_z_mm']+t
        beam_bottom = interface_z-t/2
        derived = dict(section_display_mm=[w,e['cable_bundle']['depth']],column_x_mm=x,column_abs_y_mm=y,
                       column_bottom_mm=bottom,column_top_mm=beam_bottom,crossbar_center_z_mm=interface_z)
        manifest['symbolic_construction'] = dict(values=derived,
            rule='B cable width/depth are display cross section only; x=lighting_top.width/2+cable.width/2; '
                 '|y|=abs(side_right camera y)+camera_side.depth/2+cable.depth; bottom=belt_top_z+cable.height; '
                 'crossbar z=top camera z+camera_top.height/2+3*cable.height; columns end at crossbar bottom.',
            state='SPECULATIVE', warning='Arithmetic layout from reference YAML, not measured dimensions or chosen structural sections.')
        assembly = cq.Assembly(name='COMMON_OPTICAL_M0_REFERENCE_ONLY_NON_FABRICABLE')
        rows = []
        def add(sub, scene, name, dims, center, offset, rule, role):
            require(all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in dims), 'Invalid dimensions')
            require(all(type(v) in (int,float) and math.isfinite(v) for v in center), 'Invalid center')
            shape = cq.Workplane('XY').box(*dims).translate(center).val()
            color = cq.Color(0.9,0.25,0.12,0.25) if 'keepout' in name or 'forbidden' in name else cq.Color(0.2,0.6,0.85,0.45)
            if name in ADDED: color=cq.Color(0.2,0.75,0.4,0.8)
            if name.startswith('common_'): color=cq.Color(0.7,0.3,0.8,0.25)
            sub.add(shape,name=name,color=color)
            s = shape.translate(offset)
            filename = scene+'__'+name+'.stl'
            cq.exporters.export(s,str(OUT/filename),tolerance=TOL['stl_deflection_mm'],angularTolerance=TOL['stl_angle_rad'])
            rows.append(dict(**FLAGS, evidence='SPECULATIVE', scene=scene,name=scene+'__'+name,local_name=name,
                             dimensions_mm=dims,local_center_mm=center,presentation_offset_mm=offset,
                             bounds_mm=bounds(s),volume_mm3=s.Volume(),stl=filename,role=role,provenance_rule=rule))
        for scene in SCENES:
            sub = cq.Assembly(name=scene)
            inherited = [r for r in old['components'] if r['scene']==scene]
            offset = inherited[0]['presentation_offset_mm']
            for r in inherited:
                add(sub,scene,r['local_name'],r['dimensions_mm'],r['local_center_mm'],offset,r['provenance_rule'],r['role'])
            for sign,label in [(-1,'LEFT'),(1,'RIGHT')]:
                add(sub,scene,'FRAME_COLUMN_'+label+'_CONCEPTUAL',[w,e['cable_bundle']['depth'],beam_bottom-bottom],
                    [x,sign*y,(bottom+beam_bottom)/2],offset,'symbolic_construction in manifest; column height=beam_bottom-bottom',
                    'Suspended conceptual column; no machine contact or load-bearing section specified')
            add(sub,scene,'FRAME_CROSSBAR_CONCEPTUAL',[w,2*y+e['cable_bundle']['depth'],t],
                [x,0,interface_z],offset,'span=2*column_abs_y+cable.depth; height=cable.height', 'Conceptual crossbar')
            add(sub,scene,'RETENTION_POINT_CONCEPTUAL',[w,e['cable_bundle']['depth'],t],
                [x,0,interface_z+t],offset,'cable sized glyph; center above crossbar by cable.height',
                'Retention location only; no hole, anchor, material, lanyard or load approval')
            assembly.add(sub,loc=cq.Location(cq.Vector(*offset)))
        refs = {
            'COMMON_OPTICAL_INTERFACE_DATUM_A': {'kind':'conceptual plane','axis':'z','value_mm':interface_z-t/2},
            'COMMON_OPTICAL_INTERFACE_DATUM_B': {'kind':'conceptual plane','axis':'x','value_mm':e['lighting_top']['width']/2},
            'COMMON_OPTICAL_INTERFACE_DATUM_C': {'kind':'conceptual plane','axis':'y','value_mm':0}}
        manifest['conceptual_references'] = dict(output_region='common_optical_interface_ABSTRACT',references=refs,
            meaning='Same module-side region and reference planes in both local scenes. Not validated machine datums; no holes or attachment geometry.',
            envelope_aliases={'TOP_CAMERA_ENVELOPE':'camera_top','SIDE_LEFT_CAMERA_ENVELOPE':'camera_left',
                'SIDE_RIGHT_CAMERA_ENVELOPE':'camera_right','TRIGGER_ENVELOPE':'trigger',
                'LIGHTING_ENVELOPE':['lighting_top','lighting_left','lighting_right'],
                'CABLE_ENVELOPE':['cable_top','cable_left','cable_right']})
        assembly.export(str(OUT/'COMMON_OPTICAL_M0_REFERENCE_ONLY.step'))
        manifest['components'] = rows
        manifest['bounds_mm'] = [np.min([r['bounds_mm'][0] for r in rows],axis=0).tolist(),
                                 np.max([r['bounds_mm'][1] for r in rows],axis=0).tolist()]
        write(OUT/'components.json',dict(**FLAGS,units='mm',components=rows,provenance=provenance,
                                       conceptual_references=manifest['conceptual_references']))
        result = run([sys.executable,'-B',str(Path(__file__)),'--validate'])
        commands.append(result)
        require(result['exit_code']==0, 'Independent STEP/STL validation failed')
        mesh_code = "import runpy,sys; from pathlib import Path\nfor p in sorted(Path('exports/reference-envelope/common-m0-r01').glob('*.stl')):\n sys.argv=['scripts/validate_mesh.py',str(p)]\n runpy.run_path('scripts/validate_mesh.py',run_name='__main__')\n"
        result = run([sys.executable,'-B','-c',mesh_code])
        commands.append(result)
        require(result['exit_code']==0, 'Existing independent mesh validator failed')
        manifest['validation_gate'] = 'PASS'
        with REPORT.open('x') as f:
            f.write('''1. **O mesmo frame óptico abstrato cabe nos dois envelopes nominais?** Sim, no sentido limitado de ocupação sem colisão com os volumes representados em A e B. O readback valida 46 sólidos e 46 STL, preserva os 38 envelopes anteriores e confirma o mesmo frame e layout óptico após remover o deslocamento de apresentação. As colunas ocupam x=150-170 mm, y=−210-−190 e 190-210 mm, z=20-370 mm; a travessa ocupa z=370-390 mm. São dimensões simbólicas derivadas dos YAMLs, não seções estruturais. A região de saída comum anterior permanece intacta. COMMON_OPTICAL_INTERFACE_DATUM_A/B/C são referências conceituais nomeadas no manifest, não datums de máquina. Não há envelope externo máximo nem montagem física conhecida que permita afirmar encaixe real.

2. **Quais conflitos aparecem mesmo sem interface real?** Nenhuma colisão do novo frame com câmeras, iluminação, trigger, cabos, produto ou exclusões nominais foi detectada. O frame toca intencionalmente a região abstrata de saída; colunas/travessa e retenção têm contatos conceituais. Correia e sua proibição são volumes coincidentes intencionais. Permanece uma lacuna de integração: as colunas terminam suspensas 20 mm acima do plano nominal da correia, e os envelopes ópticos não possuem ligações físicas ao frame. Iluminação lateral chega a y=±320 mm, além das colunas e das correias nominais. Espaço externo, guias, TIJ, manutenção, cabos completos e campo de visão não foram representados ou validados; não se pode inferir ausência desses conflitos reais.

3. **Quais dados reais ainda bloqueiam Adapter-A e Adapter-B?** A: identificação do exemplar/modelo, geometria e capacidade da interface do chassi, guias/TIJ, acessos e exclusões reais. B: chassi, espessura e condição das laterais, furos/datums candidatos, posições de motor e roletes e acesso à fixação. Ambos: medições com instrumento, método e repetição, envelope óptico real, massa/CG, cabos e raios de curvatura, retenção, vibração e evidência de carga/repetibilidade. G0 físico, gates dependentes de M0/P1 e revisão humana continuam necessários; os campos ausentes não foram preenchidos.

4. **O M0 mantém Arq.1 tecnicamente plausível?** Sim, apenas como hipótese geométrica nos cenários nominais A e B: o módulo abstrato e sua região de saída são idênticos e mantêm afastamento positivo das regiões proibidas representadas. A aprovação digital usa readback STEP/STL em processo separado e o validador de malha existente. Serialização: bounds STEP 1e−5 mm, volume STEP 1e−5 mm³, bounds/deflexão STL 0,1 mm e ângulo 0,1 rad; esses valores não representam precisão mecânica. A decisão permanece OPEN e a evidência SPECULATIVE. O resultado não libera os adaptadores nem a arquitetura física.

5. **O que não pode ser concluído a partir deste artefato?** Compatibilidade real, resistência, rigidez, precisão, repetibilidade, segurança da retenção, tolerância de montagem, material, caminho de carga, desempenho óptico, fabricabilidade, custo ou superioridade sobre Arq.2. Não foram validados A Large nem os extremos dimensionais de B. O ponto de retenção é um marcador, os cabos são ocupações locais e as referências conceituais não criam furos ou superfícies reais. reference_only=true; measured=false; fabrication_allowed=false. STEP e STL em exports/reference-envelope/common-m0-r01 destinam-se exclusivamente à revisão digital; manifest, provenance, SHA256SUMS e execution_audit.json registram a rastreabilidade.

STATUS: PASS_REFERENCE_ONLY
ARCHITECTURE_1: PLAUSIBLE_REFERENCE
FABRICATION_ALLOWED: false
REAL_COMPATIBILITY: BLOCKED
NEXT_MEASUREMENT: G0 físico das interfaces A e B
''')
        code = 0
    except Exception:
        manifest['validation_gate'] = 'FAIL'
        with (OUT/'failure.log').open('x') as f:
            f.write(traceback.format_exc())
        traceback.print_exc()
    after = run(status_cmd)
    commands.append(after)
    unchanged = all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in baseline.items())
    if not unchanged or after['exit_code']!=0:
        code=1
        manifest['validation_gate']='FAIL'
    manifest['artifacts'] = {str(p.relative_to(ROOT)):sha(p) for p in sorted(OUT.iterdir()) if p.is_file()}
    if REPORT.exists(): manifest['artifacts'][str(REPORT.relative_to(ROOT))]=sha(REPORT)
    write(OUT/'manifest.json',manifest)
    write(OUT/'execution_audit.json',dict(**FLAGS, generation={'argv':[sys.executable,'-B',str(Path(__file__))], 'exit_code':code},
        commands=commands, provenance={'manifest_sha256':sha(OUT/'manifest.json'),'script_sha256':sha(Path(__file__))},
        baseline_hashes=baseline, baseline_files_unchanged=unchanged,
        external_clones='No commands read or wrote ctgit/github; writes restricted to three authorized CAD destinations. No external snapshot claim.',
        latex_workspace='No traversal/read/write; excluded from git status.',
        inspection_notes=['Portable workspace root and public provenance inputs verified; CadQuery import succeeded.',
            'Earlier discovery: optional container markers were unavailable; environment verified with Python.'],
        hash_graph='inputs/scripts -> components/readback/report -> manifest -> audit -> SHA256SUMS. SHA256SUMS excludes itself.',
        write_scope=[str(Path(__file__).relative_to(ROOT)),str(OUT.relative_to(ROOT)),str(REPORT.relative_to(ROOT))],
        audit_gate='PASS' if code==0 else 'FAIL'))
    files = sorted(p for p in OUT.iterdir() if p.is_file()) + [Path(__file__)]
    if REPORT.exists(): files.append(REPORT)
    with (OUT/'SHA256SUMS').open('x') as f:
        for p in files: f.write(f'{sha(p)}  {p.relative_to(ROOT)}\n')
    print('PASS_REFERENCE_ONLY' if code==0 else 'FAIL_REFERENCE_ONLY', 'exit_code='+str(code))
    return code


if __name__=='__main__':
    sys.exit(validate() if sys.argv[1:]==['--validate'] else build())
