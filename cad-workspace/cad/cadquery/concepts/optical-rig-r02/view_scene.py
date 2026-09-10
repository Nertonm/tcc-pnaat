"""Open in CQ-editor: official sources appear only as reference bodies."""
import importlib.util
import json
from pathlib import Path
spec=importlib.util.spec_from_file_location('rig_r02',Path(__file__).with_name('rig.py'))
rig=importlib.util.module_from_spec(spec); spec.loader.exec_module(rig)
items,_=rig.build(json.loads(rig.CONFIG.read_text()))
if 'show_object' in globals():
    for name,component in items.items():
        show_object(component['shape'],name=name)
