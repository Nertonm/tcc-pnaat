"""Run through FreeCAD MCP execute_code on the GUI thread. No geometry repair.

Snapshot R05Refs and audit the supplied column STEP in its original coordinates.
The explicit user gate prevents refinement when these checks fail.
"""
import FreeCAD as App
import FreeCADGui as Gui
import Part
import json
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'exports/concepts/optical-rig-r05'
source = App.getDocument('R05Refs')
if 'R05Refined' in App.listDocuments():
    raise RuntimeError('R05Refined already exists; do not overwrite a live document')
step_path = out / 'optical-rig-r05-column-modules.step'
shape = Part.Shape()
shape.read(str(step_path))
solids = shape.Solids

def bbox(b):
    return [round(v, 6) for v in (b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax)]

def size(b):
    return [round(v, 6) for v in (b.XLength, b.YLength, b.ZLength)]

names = ['PLINTH', 'MODULE_1_BODY', 'MODULE_2_BODY', 'MODULE_2_SHOULDER',
         'MODULE_3_BODY', 'MODULE_3_SHOULDER', 'CROSSBAR_BAR', 'CROSSBAR_PAD']
pieces = [{'index': i, 'name': names[i], 'bounds_mm': bbox(s.BoundBox),
           'size_mm': size(s.BoundBox), 'valid': s.isValid(), 'volume_mm3': s.Volume}
          for i, s in enumerate(solids)]
product = Part.makeCylinder(60, 370)
pair_checks = []
for i, a in enumerate(solids):
    for j in range(i + 1, len(solids)):
        b = solids[j]
        distance = a.distToShape(b)[0]
        volume = a.common(b).Volume if distance < 1e-6 else 0.0
        pair_checks.append({'a': names[i], 'b': names[j],
                            'distance_mm': distance, 'common_mm3': volume})
product_checks = [{'name': names[i], 'common_mm3': s.common(product).Volume}
                  for i, s in enumerate(solids)]
meshes = []
for obj in source.Objects:
    if not hasattr(obj, 'Mesh'):
        continue
    m = obj.Mesh
    meshes.append({'name': obj.Name, 'label': obj.Label, 'visible': obj.Visibility,
                   'bounds_mm': bbox(m.BoundBox), 'size_mm': size(m.BoundBox),
                   'solid_mesh': m.isSolid(), 'facets': m.CountFacets,
                   'vertices_inside_product': sum(
                       1 for p in m.Points if p.Vector.x**2+p.Vector.y**2 < 3600-1e-5
                       and 0 < p.Vector.z < 370)})
fpc_checks = []
for z in [0, 16, 61.95, 161.95, 205, 210, 218, 261.9, 305, 310, 318, 325]:
    probe = Part.makeBox(20, 10, 0.1, App.Vector(-10, -5, z))
    # Sum is deliberately not used: overlapping source solids must not double count.
    occupied = [s.common(probe) for s in solids]
    nonempty = [s for s in occupied if s.Volume > 1e-8]
    volume = 0.0
    if nonempty:
        union = nonempty[0]
        for s in nonempty[1:]:
            union = union.fuse(s)
        volume = union.Volume
    fpc_checks.append({'z_mm': z, 'probe_mm': [20, 10, 0.1],
                       'occupied_area_mm2': volume / 0.1})

target = App.newDocument('R05Refined')
target.Label = 'R05Refined — BLOCKED / diagnóstico dos gates'
for obj in source.Objects:
    copied = target.copyObject(obj, False)
    copied.Visibility = obj.Visibility
    copied.addProperty('App::PropertyString', 'AuditSource', 'R05 Audit')
    copied.AuditSource = 'R05Refs/' + obj.Name + '; original geometry and placement'
column_group = target.addObject('App::DocumentObjectGroup', 'COLUMN_STEP_AUDIT')
for i, s in enumerate(solids):
    obj = target.addObject('Part::Feature', 'STEP_' + names[i])
    obj.Shape = s
    obj.addProperty('App::PropertyString', 'SourcePath', 'R05 Audit')
    obj.SourcePath = str(step_path.relative_to(root)) + '; solid index ' + str(i)
    obj.addProperty('App::PropertyString', 'GateStatus', 'R05 Audit')
    obj.GateStatus = 'FAIL — unchanged source geometry'
    obj.ViewObject.ShapeColor = (0.9, 0.58, 0.16) if i in (0, 3, 5, 6, 7) else (0.3, 0.55, 0.85)
    obj.ViewObject.Transparency = 45
    column_group.addObject(obj)
envelope = target.addObject('Part::Cylinder', 'PRODUCT_H370_D120_REFERENCE')
envelope.Radius = 60
envelope.Height = 370
envelope.Placement = App.Placement()
envelope.addProperty('App::PropertyString', 'Purpose', 'R05 Audit')
envelope.Purpose = 'Non-printable inspection envelope; assumed center X=Y=0; NOT a conveyor'
envelope.ViewObject.ShapeColor = (0.95, 0.2, 0.2)
envelope.ViewObject.Transparency = 85
params = target.addObject('Spreadsheet::Sheet', 'Params')
for row, (alias, value) in enumerate([
    ('BottleHeight', '370 mm'), ('BottleDiameter', '120 mm'),
    ('ContractTopMin', '520 mm'), ('ContractTopMax', '560 mm'),
    ('SourceColumnTop', '326 mm'), ('NominalModulePitch', '100 mm'),
    ('DesiredJointClearance', '0.2 mm'), ('BuildX', '220 mm'),
    ('BuildY', '220 mm'), ('BuildZ', '250 mm')], 1):
    params.set('A' + str(row), alias)
    params.set('B' + str(row), value)
    params.setAlias('B' + str(row), alias)
params.set('A12', 'BLOCKED: audit values only; source STEP is not parametrically repaired')
target.recompute()

print_checks = []
for p in pieces + [m for m in meshes if m['visible']]:
    dims = p['size_mm']
    print_checks.append({'name': p['name'], 'size_mm': dims,
                         'fits_source_axes': all(a <= b for a, b in zip(dims, [220, 220, 250])),
                         'scope': 'bounding-box only; no slicing/manifold/support validation'})
gates = {
    'interference': {'status': 'FAIL', 'passed': False,
        'reason': 'Exact BRep intersections within column and with product at assumed origin; open case/grip meshes prevent solid-volume certification.',
        'column_pair_checks': pair_checks, 'product_checks': product_checks,
        'case_volume_test': 'BLOCKED_NON_SOLID_MESH'},
    'height': {'status': 'FAIL', 'passed': False, 'column_top_z_mm': 326,
        'crossbar_bar_z_mm': [307, 317], 'crossbar_pad_z_mm': [318, 326],
        'existing_mount_origin_z_mm': 430, 'existing_mount_bounds_z_mm': [415, 469],
        'optical_center_z_mm': None, 'contract_z_mm': [520, 560],
        'user_gate_z_mm': [430, 520], 'gap_to_430_mm': 104, 'gap_to_520_mm': 194,
        'correction_estimate': '2 additional net 100 mm pitches give support top Z526; alternatively add total 194–234 mm net height across the SAME 3 modules. Camera offset and engagement must be included before approval.'},
    'engagement': {'status': 'FAIL', 'passed': False,
        'reason': 'Body joints at Z62 and Z162 have zero axial engagement; module shoulders are detached: 43 mm axial gap. Last body to crossbar bar: 45 mm axial gap; bar to pad: 1 mm gap.',
        'body_z_mm': [[-38, 62], [62, 162], [162, 262]],
        'shoulder_z_mm': [[205, 219], [305, 319]],
        'm4_bore_diameter_mm': 4.4, 'm4_radial_clearance_mm': 0.2,
        'm4_note': 'Diameter only passes locally on plinth/shoulders; no cylindrical bores in module bodies and no assembled M4 continuity.'},
    'fpc_channel': {'status': 'FAIL', 'passed': False,
        'reason': 'Central 20x10 mm diagnostic passage fully blocked at shoulder and crossbar heights; probe is an assumption, not a specified FPC cable envelope.',
        'samples': fpc_checks},
    'interchangeable_grip': {'status': 'FAIL', 'passed': False,
        'reason': 'No receiver/adapter or matching grip interface present. Plinth ends Z17 and case starts Z102.5 (85.5 mm separation). Independent objects do not establish interchangeability.'},
    'k1c_per_piece': {'status': 'PASS', 'passed': True,
        'scope': 'DIMENSIONAL_ENVELOPE_ONLY', 'build_volume_mm': [220, 220, 250],
        'pieces': print_checks,
        'limitation': '8 constituent solids are not 8 approved printable parts; two module compounds and crossbar contain detached solids.'}
}
inputs = [step_path, out / 'r05-full-real-assembly.stl',
          root / 'data/concepts/optical-rig-r05-contract.json']
result = {'status': 'BLOCKED_READ_GATE', 'refinement_performed': False,
          'document': target.Name, 'object_count': len(target.Objects),
          'source_document': source.Name, 'source_object_count': len(source.Objects),
          'coordinate_assumption': 'Column STEP and R05Refs placements retained exactly; bottle at X=Y=0, base Z0. No registration transform supplied. Internal STEP collisions are independent of this assumption.',
          'method': 'FreeCAD MCP execute_code, GUI thread; OCCT BRep common/distToShape; mesh solidity and vertices; bounding boxes',
          'tolerance_mm3': 0.00001, 'gates': gates, 'column_pieces': pieces,
          'source_meshes': meshes, 'official_steps_imported': [],
          'official_import_status': 'BLOCKED_BY_USER_PRE_REFINEMENT_GATE',
          'pending': ['Official Pi5 + CM3 Standard/Wide import and mechanical registration',
                      'Pi5 bosses/port alignment and case fit',
                      'Three CM3 backplates and variant windows',
                      'Mating shoulders and FPC channel continuity',
                      'Connected camera mounts, C_TOP -Z and lateral axes +/-Y',
                      'Lateral column registration and backlight corridor'],
          'excluded': ['FOV', 'calibration', 'loads', 'real safety', 'production approval'],
          'inputs_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
(out / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
target.recompute()
target.saveAs(str(out / 'optical-rig-r05-refined.fcstd'))
view = Gui.activeDocument().activeView()
for name, orient in [('isometric', view.viewAxonometric), ('front', view.viewFront), ('top', view.viewTop)]:
    orient()
    view.fitAll()
    Gui.updateGui()
    view.saveImage(str(out / ('optical-rig-r05-refined-' + name + '.png')), 1600, 1200, 'White')
view.viewAxonometric()
view.fitAll()
print(json.dumps({'document': target.Name, 'objects': len(target.Objects),
                  'gates': {k: v['status'] for k, v in gates.items()},
                  'file': target.FileName}))
