test:
	.venv/bin/python -m pytest -q

clean:
	rm -rf .venv .pytest_cache

install:
	python3 -m venv .venv && .venv/bin/pip install -e . pytest
