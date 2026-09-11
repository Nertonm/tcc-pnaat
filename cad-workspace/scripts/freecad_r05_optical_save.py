"""Save document, inspectable evidence and screenshots through live FreeCAD GUI."""
shots=OUT+'/optical-block-screenshots'
os.makedirs(shots,exist_ok=True)
for group_name,roles in [('Printed_Parts',{'printed'}),('Electronics',{'electronics'}),('Fasteners',{'hardware'}),('Cable_Routes',{'cable','datum'}),('Context_Placeholders',{'context'}),('Keepouts_Unverified',{'keepout'})]:
    g=d.getObject(group_name) or d.addObject('App::DocumentObjectGroup',group_name)
    g.addObjects([o for o in d.Objects if hasattr(o,'Role') and o.Role in roles])
meta=d.getObject('Validation_Status') or d.addObject('App::FeaturePython','Validation_Status')
for prop,val in [('Overall',evidence['overall']),('GateSummary',json.dumps(evidence['gates'])),('Scope','Geometric concept only. No FOV, load, thermal or safety validation. G2 unresolved.'),('CableStock','2 x Standard-Mini 200 mm; local PDF is Standard-Standard, not a connector compatibility drawing.')]:
    if prop not in meta.PropertiesList:meta.addProperty('App::PropertyString',prop)
    setattr(meta,prop,val)
view=Gui.activeDocument().activeView()
for o in context:o.Visibility=False
view.viewAxonometric(); view.fitAll()
view.saveImage(shots+'/bloco.png',1600,1200,'White')
view.viewTop(); view.fitAll(); view.saveImage(shots+'/top.png',1600,1200,'White')
view.viewRight(); view.fitAll(); view.saveImage(shots+'/side.png',1600,1200,'White')
for o in printed:o.ViewObject.Transparency=82
for o in hardware:o.Visibility=False
view.viewAxonometric(); view.fitAll(); view.saveImage(shots+'/cabos.png',1600,1200,'White')
for o in printed:o.ViewObject.Transparency=0
for o in hardware:o.Visibility=True
for o in context:o.Visibility=True
view.viewAxonometric(); view.fitAll(); view.saveImage(shots+'/contexto.png',1600,1200,'White')
# Opening the document emphasizes the optical block, not the placeholder pedestal.
for o in context:o.Visibility=False
view.viewAxonometric(); view.fitAll()
d.recompute()
path=OUT+'/optical-rig-r05-optical-block.FCStd'
d.saveAs(path)
evidence['objects']=len(d.Objects)
evidence['files']={'FCStd':path,'screenshots':[shots+'/'+n+'.png' for n in ['bloco','top','side','cabos','contexto']]}
with open(OUT+'/validation.json','w') as f:json.dump(evidence,f,indent=2)
print('SAVED',path,'objects',len(d.Objects),'printed',len(printed))
print('GATES',json.dumps(evidence['gates']))
