"""Semeia um banco de DEMONSTRACAO do hub para exercitar a API e o site sem bancada.

Dados de demonstracao declarados como tais: o `/api/health` devolve o caminho do banco e o site
mostra esse caminho, justamente para ninguem confundir demo com linha real.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# O modulo roda de dentro de `src-production/`; o caminho vem do proprio arquivo, nunca do host de
# quem escreveu (caminho absoluto de maquina nao vai para o repositorio).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dominio import Classe, Dominio, Evento, Medida, Qualidade, Vista
from registro import Registro

DESTINO = Path(sys.argv[1] if len(sys.argv) > 1 else "hub.db")
EVIDENCIAS = DESTINO.parent / "evidencias"
T0 = datetime(2026, 9, 15, 9, 30, tzinfo=timezone.utc)


def jpeg(nome: str, texto: str, cor: tuple[int, int, int]) -> str:
    from PIL import Image, ImageDraw
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    caminho = EVIDENCIAS / nome
    im = Image.new("RGB", (320, 240), (28, 30, 34))
    d = ImageDraw.Draw(im)
    d.rectangle([120, 60, 200, 200], outline=cor, width=3)
    d.text((12, 12), texto, fill=(235, 238, 242))
    im.save(caminho, "JPEG", quality=88)
    return str(caminho)


def medida(vista, dominio, classe, conf):
    return Medida(vista=vista, dominio=dominio, classe=classe, confianca=conf, qualidade=Qualidade.OK)


def completo(tampa, corpo, conf=0.92):
    return (medida(Vista.LATERAL1, Dominio.TAMPA, tampa, conf),
            medida(Vista.LATERAL2, Dominio.TAMPA, tampa, conf),
            medida(Vista.LATERAL1, Dominio.CORPO, corpo, conf),
            medida(Vista.LATERAL2, Dominio.CORPO, corpo, conf))


def main() -> int:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    if DESTINO.exists():
        DESTINO.unlink()
    reg = Registro.abrir(DESTINO)
    cx = reg._cx
    cx.execute("INSERT INTO lote (lote_id, data_inicio, turno) VALUES ('L2026-09-15-A','2026-09-15','manha')")
    cx.execute("INSERT INTO lote (lote_id, data_inicio, turno) VALUES ('L2026-09-15-B','2026-09-15','tarde')")
    cx.execute("INSERT INTO ponto_linha (ponto_id, nome, tipo) VALUES (1,'bancada-b','rig')")

    itens = [
        ("ITM-001", "L2026-09-15-A", 0, Classe.NORMAL, completo(Classe.NORMAL, Classe.NORMAL), "lateral1"),
        ("ITM-002", "L2026-09-15-A", 4, Classe.NORMAL, completo(Classe.NORMAL, Classe.NORMAL), "lateral2"),
        ("ITM-003", "L2026-09-15-A", 8, Classe.TAMPA_AUSENTE,
         completo(Classe.TAMPA_AUSENTE, Classe.NORMAL), "lateral1"),
        ("ITM-004", "L2026-09-15-A", 12, Classe.DEFEITO_TAMPA,
         completo(Classe.DEFEITO_TAMPA, Classe.NORMAL), "lateral2"),
        ("ITM-005", "L2026-09-15-B", 20, Classe.NORMAL, completo(Classe.NORMAL, Classe.NORMAL), "lateral1"),
        # sem a segunda lateral: o dominio nao decide e o item sai inconclusivo (D-04/D-29)
        ("ITM-006", "L2026-09-15-B", 26, Classe.NORMAL,
         (medida(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL, 0.7),), None),
    ]
    for item_id, lote, segundos, classe, medidas, vista_evidencia in itens:
        reg.registrar(Evento(item_id=item_id, capturado_em=T0 + timedelta(seconds=segundos),
                             equipamento="pi5-rig", localizacao="bancada-b", esteira="est-b",
                             vistas=(Vista.TOPO,), medidas=medidas, status=classe))
        cx.execute("UPDATE item SET lote_id=?, fonte_trigger='e18_d80nk', velocidade_rig_mm_s=100.0"
                   " WHERE item_id=?", (lote, item_id))

    for item_id, vista, texto, cor in (
            ("ITM-003", "lateral1", "ITM-003 tampa ausente", (214, 26, 34)),
            ("ITM-004", "lateral2", "ITM-004 tampa mal rosqueada", (255, 127, 14)),
            ("ITM-001", "lateral1", "ITM-001 normal", (93, 107, 66))):
        caminho = jpeg(f"{item_id}-{vista}.jpg", texto, cor)
        cx.execute("INSERT INTO evidencia (inspecao_vista_id, grandeza, valor, unidade, origem, papel,"
                   " metodo, fonte) SELECT id, 'altura_tampa_mm', 12.4, 'mm', 'geometria', 'auxiliar',"
                   " 'elipse_backlight', ?  FROM inspecao_vista WHERE item_id=? AND vista=?",
                   (caminho, item_id, vista))
        cx.execute("UPDATE inspecao_vista SET caminho_evidencia=?, latencia_ms=?, pixels_saturados_pct=?"
                   " WHERE item_id=? AND vista=?",
                   (caminho, 40 + (hash(item_id) % 20), 1.2, item_id, vista))

    for i, (seg, estado, item, motivo) in enumerate([
            (0, "aceito", "ITM-001", None), (4, "aceito", "ITM-002", None),
            (8, "aceito", "ITM-003", None), (12, "aceito", "ITM-004", None),
            (20, "aceito", "ITM-005", None), (26, "aceito", "ITM-006", None),
            (30, "falso", None, "sem captura na janela"), (34, "duplicado", None, "debounce")]):
        reg.registrar_gatilho((T0 + timedelta(seconds=seg)).isoformat(), estado, fonte="e18_d80nk",
                              item_id=item, ponto_id=1, motivo=motivo, debounce_ms=20)

    for seg, temp in ((0, 21.5), (10, 22.1), (20, 23.4), (30, 22.8)):
        cx.execute("INSERT INTO evento_ambiental (timestamp, ponto_id, temperatura) VALUES (?,?,?)",
                   ((T0 + timedelta(seconds=seg)).isoformat(), 1, temp))
    cx.execute("INSERT INTO heartbeat_no (ponto_id, timestamp, status, fila_pendente,"
               " latencia_envio_ms) VALUES (1, ?, 'online', 0, 12)",
               (datetime.now(timezone.utc).isoformat(),))
    cx.execute("INSERT INTO correcao_operador (item_id, decisao_original, decisao_corrigida,"
               " corrigido_por, timestamp) VALUES ('ITM-004','defeito_tampa','normal','operador-1',?)",
               ((T0 + timedelta(minutes=5)).isoformat(),))
    cx.commit()
    total = cx.execute("SELECT COUNT(*) FROM item").fetchone()[0]
    vistas = cx.execute("SELECT COUNT(*) FROM inspecao_vista").fetchone()[0]
    reg.fechar()
    print(f"banco de demonstracao: {DESTINO} | itens={total} linhas_de_vista={vistas} "
          f"| evidencias={EVIDENCIAS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
