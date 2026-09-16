#!/usr/bin/env python3
"""Trava de frescor: aborta se o Label Studio avancou desde o ultimo export canonico.

Uso no pipeline: python src-production/treino/guarda_frescor.py  (rc=0 libera, rc=3 aborta)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fingerprint_ls import main  # noqa: E402

raise SystemExit(main())
