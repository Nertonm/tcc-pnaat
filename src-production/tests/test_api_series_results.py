import ast
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class SeriesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.s = self.base / "20260915-191847-490"
        self.s.mkdir()
        self.model = self.base / "models"
        self.model.mkdir()
        (self.model / "v9b-lateral.pt").write_bytes(b"test model fixture")
        self.man = {
            "serie": self.s.name,
            "trigger_n": 2,
            "origem_trigger": "fisico",
            "fontes": [
                {"nome": n, "camera": n[:-4]}
                for n in ("cam-csi.jpg", "cam-usb.jpg", "espcam.jpg")
            ],
        }
        for f in self.man["fontes"]:
            (self.s / f["nome"]).write_bytes(b"unit fixture")
        (self.s / "manifest.json").write_text(json.dumps(self.man))
        def sha(p):
            return hashlib.sha256(p.read_bytes()).hexdigest()
        self.d = {
            "serie": self.s.name,
            "trigger_n": 2,
            "origem_trigger": "fisico",
            "manifest_sha256": sha(self.s / "manifest.json"),
            "fontes_sha256": {
                f["nome"]: sha(self.s / f["nome"]) for f in self.man["fontes"]
            },
            "jpeg": "cam-csi.jpg",
            "jpeg_sha256": sha(self.s / "cam-csi.jpg"),
            "modelo": "v9b-lateral.pt",
            "modelo_sha256": sha(self.model / "v9b-lateral.pt"),
            "veredito": {"veredito": "inconclusivo"},
        }
        api_path = (
            ROOT / "live/api.py"
            if (ROOT / "live/api.py").is_file()
            else ROOT.parent / "api.py"
        )
        text = api_path.read_text()
        tree = ast.parse(text)
        funcs = [
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef)
            and n.name in ("_deteccao_da_serie", "_series_locais")
        ]
        from datetime import UTC, datetime

        class MappedPath:
            def __new__(cls, p):
                return self.model if str(p) == str(self.model) else Path(p)

        for _c in ("MODELOS_DIR", "SERIES_DIR"):
            assert _c in text, (
                f"api.py deixou de definir {_c}: o harness precisa acompanhar"
            )
        self.ns = {
            "Path": MappedPath,
            "json": json,
            "re": re,
            "SERIES_DIR": self.base,
            "ARQUIVO_DE_SERIE": re.compile(
                r"(?:manifest\.json|[A-Za-z0-9][A-Za-z0-9._-]{0,63}\.jpg)"
            ),
            "CAMERAS_DE_CAPTURA": ["csi", "usb", "espcam"],
            "datetime": datetime,
            "UTC": UTC,
            "MODELOS_DIR": self.model,
        }
        exec(  # noqa: S102 - harness executes only AST-selected API helpers
            compile(ast.Module(body=funcs, type_ignores=[]), "api.py", "exec"),
            self.ns,
        )

    def run_result(self):
        (self.s / "deteccao.json").write_text(json.dumps(self.d))
        return self.ns["_deteccao_da_serie"](self.s, self.man)

    def test_real_contract_shape(self):
        self.assertEqual(self.run_result()["estado"], "verificado")

    def test_missing(self):
        self.assertEqual(
            self.ns["_deteccao_da_serie"](self.s, self.man)["estado"], "aguardando"
        )

    def test_mismatch(self):
        self.d["jpeg_sha256"] = "0" * 64
        r = self.run_result()
        self.assertEqual(r["estado"], "erro")
        self.assertNotIn("veredito", r)

    def test_identity(self):
        self.d["trigger_n"] = 3
        self.assertEqual(self.run_result()["estado"], "erro")

    def test_changed_source(self):
        (self.s / "cam-usb.jpg").write_bytes(b"changed")
        self.assertEqual(self.run_result()["estado"], "erro")

    def test_wrong_model(self):
        self.d["modelo_sha256"] = "0" * 64
        self.assertEqual(self.run_result()["estado"], "erro")

    def test_no_usb_inference(self):
        self.d["jpeg"] = "cam-usb.jpg"
        self.assertEqual(self.run_result()["estado"], "erro")

    def test_malformed(self):
        (self.s / "deteccao.json").write_text("{")
        self.assertEqual(
            self.ns["_deteccao_da_serie"](self.s, self.man)["estado"], "erro"
        )

    def test_partial(self):
        (self.s / "espcam.jpg").unlink()
        rows = self.ns["_series_locais"]()
        row = next(r for r in rows if r["serie"] == self.s.name)
        self.assertFalse(row["completa"])
        self.assertEqual(len(row["fotos"]), 2)
        self.assertEqual(row["deteccao"]["estado"], "aguardando")


if __name__ == "__main__":
    unittest.main(verbosity=2)
