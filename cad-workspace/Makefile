PY=.venv/bin/python

.PHONY: canary validate-g0 generate validate-mesh

canary: validate-g0 generate validate-mesh
	@echo PASS: CAD pipeline canary

validate-g0:
	$(PY) scripts/validate_g0.py data/g0/canary.yaml

generate:
	$(PY) scripts/generate_canary.py --g0 data/g0/canary.yaml --out exports/canary

validate-mesh:
	$(PY) scripts/validate_mesh.py exports/canary/canary.stl
