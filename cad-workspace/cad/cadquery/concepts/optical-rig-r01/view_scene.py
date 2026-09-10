"""Open in CQ-editor/run with show_object injected. No vendor export is performed."""
from pathlib import Path
import importlib.util
import json
spec=importlib.util.spec_from_file_location('optical_rig',Path(__file__).with_name('rig.py'))
rig=importlib.util.module_from_spec(spec); spec.loader.exec_module(rig)
items,_=rig.build(json.loads(rig.CONFIG.read_text()))
if 'show_object' in globals():
    for name,item in items.items():
        show_object(item['shape'],name=name,options={'alpha':.25 if item['role'] in ('access','exclusion','lighting','cable') else 1})
else:
    print('Scene built in memory. Use CQ-editor show_object to inspect vendor references; no assembly export.')
