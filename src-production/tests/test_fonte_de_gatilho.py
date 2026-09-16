"""Testes da fonte de gatilho (RF-01.1): o CSV e a ENTRADA e o registro e conferido por SQL direto.

Cada CSV e escrito a mao em `tmp_path`; nada e gerado pelo modulo de producao, que so transcreve o
que o arquivo diz. Cada numero esperado foi contado a mao a partir do arquivo escrito aqui, e o
banco e conferido linha a linha (nao pela API de leitura) para que a gravacao seja observada como
esta: id, timestamp, estado, fonte, vinculo, motivo, debounce e ponto.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from dominio import Classe, Dominio, Evento, Medida, Vista
from fonte_gatilho import (
    ESTADOS,
    PERDA_DE_DETECCAO,
    ArquivoDeGatilhoIlegivel,
    CabecalhoInvalido,
    ContagemPorEstado,
    ErroDeFonteDeGatilho,
    EstadoDeGatilho,
    EstadoForaDoVocabulario,
    EventoDeGatilho,
    FonteDeCsvDeGatilho,
    FonteDeGatilho,
    MotivoDeRecusa,
    Recusa,
    ResumoDaFonte,
)
from painel import Painel
from registro import Registro

CABECALHO = "timestamp,estado,fonte,motivo,item_id,debounce_ms"
T0 = datetime(2026, 9, 13, 3, 0, tzinfo=timezone.utc)


def _linha(
    timestamp: str = "",
    estado: str = "",
    fonte: str = "",
    motivo: str = "",
    item_id: str = "",
    debounce_ms: str = "",
) -> str:
    """Uma linha de dados com as SEIS colunas do cabecalho, na ordem do cabecalho."""
    return f"{timestamp},{estado},{fonte},{motivo},{item_id},{debounce_ms}"


def _csv(tmp_path, texto: str):
    """Grava o CSV e devolve a fonte apontando para ele."""
    caminho = tmp_path / "gatilhos.csv"
    caminho.write_text(texto, encoding="utf-8")
    return FonteDeCsvDeGatilho(caminho)


def _evento_do_item(item_id: str = "i-001") -> Evento:
    """Item gravado ANTES da ingestao: uma linha do arquivo vai apontar para ele."""
    medidas = (
        Medida(
            vista=Vista.LATERAL1,
            dominio=Dominio.TAMPA,
            classe=Classe.NORMAL,
            confianca=0.9,
        ),
        Medida(
            vista=Vista.LATERAL2,
            dominio=Dominio.TAMPA,
            classe=Classe.NORMAL,
            confianca=0.9,
        ),
    )
    return Evento(
        item_id=item_id,
        capturado_em=T0,
        equipamento="pi5-rig",
        localizacao="bancada-b",
        vistas=(Vista.LATERAL1, Vista.LATERAL2),
        medidas=medidas,
        status=Classe.NORMAL,
    )


def _gatilhos(reg) -> list:
    """O estado do banco como esta: o que a fonte gravou, na ordem em que gravou."""
    return [
        tuple(r)
        for r in reg._cx.execute(
            "SELECT id, timestamp, estado, fonte, item_id, motivo, debounce_ms, ponto_id"
            " FROM evento_gatilho ORDER BY id"
        )
    ]


def _contagem(resumo: ResumoDaFonte) -> list:
    return [(c.estado, c.eventos) for c in resumo.por_estado]


@pytest.fixture()
def reg(tmp_path):
    r = Registro.abrir(tmp_path / "hub.db")
    yield r
    r.fechar()


# ---------------------------------------------------------------- arquivo de ensaio completo


def test_arquivo_de_ensaio_entra_no_registro_e_o_resumo_fecha(tmp_path, reg):
    """5 linhas boas: 2 aceitos, 1 duplicado, 1 falso, 1 invalido, 2 em branco ao final."""
    assert (
        reg.registrar(_evento_do_item()) == "inserido"
    )  # i-001 existe: a linha 2 aponta para ele
    texto = (
        "\n".join(
            [
                CABECALHO,
                _linha(
                    "2026-09-13T03:00:00Z", "aceito", "e18_d80nk", item_id="i-001"
                ),  # linha 2
                _linha(
                    "2026-09-13T00:00:00.050-03:00",
                    "duplicado",
                    "e18_d80nk",  # linha 3
                    motivo="debounce",
                    debounce_ms="50",
                ),
                _linha(
                    "2026-09-13T03:00:05+00:00",
                    "falso",
                    "e18_d80nk",  # linha 4
                    motivo="sem captura na janela",
                ),
                _linha(
                    "2026-09-13T03:00:06+00:00",
                    "invalido",
                    "vl53l0x",  # linha 5
                    motivo="sinal fora do nivel logico",
                ),
                _linha("2026-09-13T03:00:10+00:00", "aceito", "vl53l0x"),  # linha 6
                "",
                "",
            ]
        )
        + "\n"
    )

    resumo = _csv(tmp_path, texto).processar(reg)

    assert (
        resumo.lidas,
        resumo.ids_criados,
        resumo.linhas_recusadas,
        resumo.linhas_em_branco,
    ) == (5, 5, 0, 2)
    assert resumo.recusas == ()
    assert _contagem(resumo) == [
        (EstadoDeGatilho.ACEITO, 2),
        (EstadoDeGatilho.DUPLICADO, 1),
        (EstadoDeGatilho.FALSO, 1),
        (EstadoDeGatilho.INVALIDO, 1),
    ]
    # `Z` e grafado como `+00:00` e `.050` como `.050000`: o instante e o fuso sao os do arquivo, a
    # grafia e a canonica (e o indice do banco ordena por texto).
    assert _gatilhos(reg) == [
        (
            1,
            "2026-09-13T03:00:00+00:00",
            "aceito",
            "e18_d80nk",
            "i-001",
            None,
            None,
            None,
        ),
        (
            2,
            "2026-09-13T00:00:00.050000-03:00",
            "duplicado",
            "e18_d80nk",
            None,
            "debounce",
            50,
            None,
        ),
        (
            3,
            "2026-09-13T03:00:05+00:00",
            "falso",
            "e18_d80nk",
            None,
            "sem captura na janela",
            None,
            None,
        ),
        (
            4,
            "2026-09-13T03:00:06+00:00",
            "invalido",
            "vl53l0x",
            None,
            "sinal fora do nivel logico",
            None,
            None,
        ),
        (5, "2026-09-13T03:00:10+00:00", "aceito", "vl53l0x", None, None, None, None),
    ]
    # nenhum item foi criado pela ingestao e o item pre-existente continua como estava
    assert reg._cx.execute("SELECT COUNT(*) FROM item").fetchone()[0] == 1
    assert reg.ler("i-001") is not None


def test_a_leitura_e_por_nome_e_nao_por_posicao(tmp_path, reg):
    """A ordem das colunas nao importa: quem manda e o nome de cada uma."""
    texto = (
        "fonte,item_id,debounce_ms,timestamp,motivo,estado\n"
        "vl53l0x,,25,2026-09-13T03:00:00+00:00,,falso\n"
    )
    resumo = _csv(tmp_path, texto).processar(reg)
    assert (resumo.lidas, resumo.ids_criados) == (1, 1)
    assert _gatilhos(reg) == [
        (1, "2026-09-13T03:00:00+00:00", "falso", "vl53l0x", None, None, 25, None)
    ]


def test_arquivo_sem_eventos_devolve_resumo_zerado(tmp_path, reg):
    """Ensaio sem passagem e resposta legitima: zero aqui e medido, nao inventado."""
    resumo = _csv(tmp_path, CABECALHO + "\n").processar(reg)
    assert (
        resumo.lidas,
        resumo.ids_criados,
        resumo.linhas_recusadas,
        resumo.linhas_em_branco,
    ) == (0, 0, 0, 0)
    assert [c.eventos for c in resumo.por_estado] == [0, 0, 0, 0]
    assert _gatilhos(reg) == []


# ---------------------------------------------------------------- estado fora do vocabulario


@pytest.mark.parametrize("estado", ["talvez", "", "aceito ", "ACEITO", "falso_disparo"])
def test_estado_fora_do_vocabulario_falha_o_arquivo_inteiro(tmp_path, reg, estado):
    """A linha ruim vem DEPOIS de uma linha boa e ANTES de outra: se algo tivesse sido gravado
    antes da leitura do arquivo inteiro, apareceria no banco."""
    texto = (
        "\n".join(
            [
                CABECALHO,
                _linha("2026-09-13T03:00:00+00:00", "aceito", "e18_d80nk"),  # linha 2
                _linha("2026-09-13T03:00:01+00:00", estado, "e18_d80nk"),  # linha 3
                _linha("2026-09-13T03:00:02+00:00", "aceito", "e18_d80nk"),  # linha 4
            ]
        )
        + "\n"
    )
    fonte = _csv(tmp_path, texto)

    with pytest.raises(
        EstadoForaDoVocabulario
    ) as erro:  # a leitura a seco ja recusa o arquivo
        fonte.ler()
    assert "linha 3" in str(erro.value)
    assert f"{estado!r}" in str(erro.value)
    assert "|".join(ESTADOS) in str(erro.value)

    with pytest.raises(EstadoForaDoVocabulario):
        fonte.processar(reg)
    assert reg._cx.execute("SELECT COUNT(*) FROM evento_gatilho").fetchone()[0] == 0


# ---------------------------------------------------------------- timestamp


@pytest.mark.parametrize(
    "bruto, motivo, detalhe",
    [
        ("ontem", MotivoDeRecusa.TIMESTAMP_ILEGIVEL, "ontem"),
        ("", MotivoDeRecusa.TIMESTAMP_AUSENTE, None),
        (
            "2026-09-13T03:00:00",
            MotivoDeRecusa.TIMESTAMP_SEM_FUSO,
            "2026-09-13T03:00:00",
        ),
    ],
)
def test_timestamp_ruim_e_recusado_sem_derrubar_o_resto(
    tmp_path, reg, bruto, motivo, detalhe
):
    """Timestamp sem fuso nao e rastreavel: a linha nao entra, e a recusa fica declarada."""
    texto = (
        "\n".join(
            [
                CABECALHO,
                _linha(bruto, "aceito", "e18_d80nk"),  # linha 2: recusada
                _linha(
                    "2026-09-13T03:00:01+00:00", "aceito", "e18_d80nk"
                ),  # linha 3: entra
            ]
        )
        + "\n"
    )
    fonte = _csv(tmp_path, texto)

    leitura = fonte.ler()  # a seco: nao grava e ja classifica
    assert len(leitura.eventos) == 1 and leitura.linhas_de_dados == 2
    assert leitura.recusas == (Recusa(linha=2, motivo=motivo, detalhe=detalhe),)
    assert reg._cx.execute("SELECT COUNT(*) FROM evento_gatilho").fetchone()[0] == 0

    resumo = fonte.processar(reg)
    assert (resumo.lidas, resumo.ids_criados, resumo.linhas_recusadas) == (2, 1, 1)
    assert resumo.recusas == (Recusa(linha=2, motivo=motivo, detalhe=detalhe),)
    assert _contagem(resumo) == [
        (EstadoDeGatilho.ACEITO, 1),
        (EstadoDeGatilho.DUPLICADO, 0),
        (EstadoDeGatilho.FALSO, 0),
        (EstadoDeGatilho.INVALIDO, 0),
    ]
    assert _gatilhos(reg) == [
        (1, "2026-09-13T03:00:01+00:00", "aceito", "e18_d80nk", None, None, None, None)
    ]


def test_evento_de_gatilho_sem_fuso_nao_existe():
    """O fuso e invariante do proprio contrato, nao so da leitura do arquivo."""
    with pytest.raises(ErroDeFonteDeGatilho) as erro:
        EventoDeGatilho(
            linha=2,
            timestamp=datetime(2026, 9, 13, 3, 0),  # noqa: DTZ001
            estado=EstadoDeGatilho.ACEITO,
            fonte=FonteDeGatilho.E18_D80NK,
        )
    assert "fuso" in str(erro.value)
    evento = EventoDeGatilho(
        linha=2,
        timestamp=T0,
        estado=EstadoDeGatilho.ACEITO,
        fonte=FonteDeGatilho.E18_D80NK,
    )
    assert (evento.estado.value, evento.item_id, evento.debounce_ms) == (
        "aceito",
        None,
        None,
    )


# ---------------------------------------------------------------- vinculo com o item


def test_item_inexistente_e_recusado_pela_api_do_registro(tmp_path, reg):
    """Nao invente o item: quem diz que o item nao existe e a API do registro, e a linha inteira cai
    (sem gatilho gravado pela metade e sem item criado aqui)."""
    texto = (
        "\n".join(
            [
                CABECALHO,
                _linha(
                    "2026-09-13T03:00:00+00:00", "aceito", "e18_d80nk", item_id="i-999"
                ),
            ]
        )
        + "\n"
    )
    resumo = _csv(tmp_path, texto).processar(reg)

    assert (resumo.lidas, resumo.ids_criados, resumo.linhas_recusadas) == (1, 0, 1)
    assert [c.eventos for c in resumo.por_estado] == [0, 0, 0, 0]
    recusa = resumo.recusas[0]
    assert (recusa.linha, recusa.motivo) == (
        2,
        MotivoDeRecusa.ITEM_RECUSADO_PELO_REGISTRO,
    )
    assert (
        "item inexistente: 'i-999'" in recusa.detalhe
    )  # o texto e o da API, nao um diagnostico novo
    assert _gatilhos(reg) == []
    assert reg._cx.execute("SELECT COUNT(*) FROM item").fetchone()[0] == 0


def test_gatilho_aceito_sem_item_entra_sem_vinculo(tmp_path, reg):
    """O gatilho precede o item (RF-01.1): aceito sem item_id nao e recusa e nao cria item."""
    texto = (
        "\n".join(
            [
                CABECALHO,
                _linha("2026-09-13T03:00:00+00:00", "aceito", "e18_d80nk"),
            ]
        )
        + "\n"
    )
    resumo = _csv(tmp_path, texto).processar(reg)
    assert (resumo.lidas, resumo.ids_criados, resumo.recusas) == (1, 1, ())
    assert _gatilhos(reg) == [
        (1, "2026-09-13T03:00:00+00:00", "aceito", "e18_d80nk", None, None, None, None)
    ]
    assert reg._cx.execute("SELECT COUNT(*) FROM item").fetchone()[0] == 0


# ---------------------------------------------------------------- fonte (origem)


def test_fonte_ausente_e_estado_e_fonte_estranha_e_recusa(tmp_path, reg):
    """Vazio = o arquivo declarou que nao identificou a origem. Valor preenchido fora do vocabulario
    = origem que este leitor nao conhece: gravar `nao_declarada` apagaria o que o arquivo disse."""
    texto = (
        "\n".join(
            [
                CABECALHO,
                _linha("2026-09-13T03:00:00+00:00", "aceito"),  # linha 2: sem origem
                _linha(
                    "2026-09-13T03:00:01+00:00", "falso", "e18_d80nk_v2"
                ),  # linha 3: estranha
            ]
        )
        + "\n"
    )
    resumo = _csv(tmp_path, texto).processar(reg)

    assert (resumo.lidas, resumo.ids_criados, resumo.linhas_recusadas) == (2, 1, 1)
    assert resumo.recusas == (
        Recusa(
            linha=3, motivo=MotivoDeRecusa.FONTE_DESCONHECIDA, detalhe="e18_d80nk_v2"
        ),
    )
    assert _gatilhos(reg) == [
        (
            1,
            "2026-09-13T03:00:00+00:00",
            "aceito",
            "nao_declarada",
            None,
            None,
            None,
            None,
        )
    ]


# ---------------------------------------------------------------- debounce


@pytest.mark.parametrize("bruto", ["cinquenta", "50ms", "-5", "50.0", " 50"])
def test_debounce_que_nao_e_inteiro_nao_negativo_e_recusado(tmp_path, reg, bruto):
    """'-5' e ' 50' sao recusados: interpretar seria gravar um numero que o arquivo nao escreveu."""
    texto = (
        "\n".join(
            [
                CABECALHO,
                _linha(
                    "2026-09-13T03:00:00+00:00",
                    "aceito",
                    "e18_d80nk",
                    debounce_ms=bruto,
                ),
            ]
        )
        + "\n"
    )
    resumo = _csv(tmp_path, texto).processar(reg)
    assert (resumo.lidas, resumo.ids_criados) == (1, 0)
    assert resumo.recusas == (
        Recusa(linha=2, motivo=MotivoDeRecusa.DEBOUNCE_INVALIDO, detalhe=bruto),
    )
    assert _gatilhos(reg) == []


def test_debounce_zero_e_valor_declarado_e_vazio_e_nulo(tmp_path, reg):
    """Zero e um debounce configurado; vazio e ausencia de declaracao. Sao coisas distintas."""
    texto = (
        "\n".join(
            [
                CABECALHO,
                _linha(
                    "2026-09-13T03:00:00+00:00", "aceito", "e18_d80nk", debounce_ms="0"
                ),  # linha 2
                _linha(
                    "2026-09-13T03:00:01+00:00", "duplicado", "e18_d80nk"
                ),  # linha 3
            ]
        )
        + "\n"
    )
    resumo = _csv(tmp_path, texto).processar(reg)
    assert (resumo.ids_criados, resumo.recusas) == (2, ())
    assert (
        reg._cx.execute(
            "SELECT debounce_ms FROM evento_gatilho ORDER BY id"
        ).fetchall()[0][0]
        == 0
    )
    assert (
        reg._cx.execute(
            "SELECT debounce_ms FROM evento_gatilho ORDER BY id"
        ).fetchall()[1][0]
        is None
    )


# ---------------------------------------------------------------- linha do arquivo


def test_colunas_divergentes_do_cabecalho_e_linha_fisica_do_arquivo(tmp_path, reg):
    """Virgula nao escapada desloca as colunas: a linha e recusada em vez de reinterpretada. E o
    motivo com quebra de linha mostra que `linha` e a linha FISICA (um contador por linha de dados
    diria 4; no arquivo, a linha do defeito e a 5)."""
    texto = (
        "timestamp,estado,fonte,motivo,item_id,debounce_ms\n"
        '2026-09-13T03:00:00+00:00,falso,e18_d80nk,"sem captura\n'
        'na janela",,\n'
        "2026-09-13T03:01:00+00:00,aceito,e18_d80nk,,,\n"
        "2026-09-13T03:02:00+00:00,aceito,e18_d80nk,,,cinquenta,y\n"
    )
    resumo = _csv(tmp_path, texto).processar(reg)

    assert (resumo.lidas, resumo.ids_criados, resumo.linhas_recusadas) == (3, 2, 1)
    assert resumo.recusas == (
        Recusa(
            linha=5,
            motivo=MotivoDeRecusa.COLUNAS_DIVERGENTES,
            detalhe="esperado 6 campos, lidos 7",
        ),
    )
    assert _contagem(resumo) == [
        (EstadoDeGatilho.ACEITO, 1),
        (EstadoDeGatilho.DUPLICADO, 0),
        (EstadoDeGatilho.FALSO, 1),
        (EstadoDeGatilho.INVALIDO, 0),
    ]
    assert _gatilhos(reg) == [
        (
            1,
            "2026-09-13T03:00:00+00:00",
            "falso",
            "e18_d80nk",
            None,
            "sem captura\nna janela",
            None,
            None,
        ),
        (2, "2026-09-13T03:01:00+00:00", "aceito", "e18_d80nk", None, None, None, None),
    ]


# ---------------------------------------------------------------- cabecalho e arquivo


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("", "vazio"),  # arquivo sem linha nenhuma
        ("timestamp,estado\n", "fonte"),  # falta coluna obrigatoria
        (
            "timestamp,estado,fonte,item\n",
            "desconhecida",
        ),  # coluna que este leitor nao conhece
        ("timestamp,timestamp,estado,fonte\n", "repetida"),  # coluna duplicada
        # BOM: `\ufefftimestamp` nao e `timestamp`. O erro mostra as colunas LIDAS, e o repr do BOM
        # escapa a sequencia; ela fica visivel para quem vai consertar o arquivo.
        ("\ufefftimestamp,estado,fonte\n", "\\ufefftimestamp"),
    ],
)
def test_cabecalho_fora_do_contrato_falha_sem_gravar(tmp_path, reg, texto, esperado):
    fonte = _csv(tmp_path, texto)
    with pytest.raises(CabecalhoInvalido) as erro:
        fonte.processar(reg)
    assert esperado in str(erro.value)
    assert reg._cx.execute("SELECT COUNT(*) FROM evento_gatilho").fetchone()[0] == 0


def test_arquivo_inexistente_falha_explicitamente(tmp_path, reg):
    with pytest.raises(ArquivoDeGatilhoIlegivel) as erro:
        FonteDeCsvDeGatilho(tmp_path / "ensaio-de-hoje.csv").processar(reg)
    assert "ensaio-de-hoje.csv" in str(erro.value)


# ---------------------------------------------------------------- limites declarados


def test_perda_de_deteccao_e_declarada_e_nunca_zero(tmp_path, reg):
    """RF-01.1: o gatilho observa falso disparo, duplicata e sinal invalido. O item que passou sem
    disparar NAO deixou evento: medir isso exige o encoder (D-21), e o resumo declara em vez de
    devolver zero. A declaracao tem de ser a mesma da leitura analitica."""
    resumo = _csv(tmp_path, CABECALHO + "\n").processar(reg)
    assert resumo.perda_de_deteccao == PERDA_DE_DETECCAO
    assert "nao e observavel" in resumo.perda_de_deteccao
    assert "KY-040" in resumo.perda_de_deteccao and "D-21" in resumo.perda_de_deteccao

    painel = Painel(reg._cx).perda_de_deteccao()
    assert painel.instrumentada is False and "encoder" in painel.motivo


# ---------------------------------------------------------------- invariantes do resumo


def _resumo(
    lidas: int = 1, ids_criados: int = 1, por_estado=None, recusas=()
) -> ResumoDaFonte:
    if por_estado is None:
        por_estado = tuple(
            ContagemPorEstado(
                estado, ids_criados if estado is EstadoDeGatilho.ACEITO else 0
            )
            for estado in EstadoDeGatilho
        )
    return ResumoDaFonte(
        lidas=lidas,
        ids_criados=ids_criados,
        por_estado=por_estado,
        recusas=recusas,
        linhas_em_branco=0,
    )


def test_resumo_que_nao_fecha_e_recusado():
    """Cada linha do arquivo ou virou evento, ou foi recusada com motivo: nada some no caminho."""
    assert _resumo().ids_criados == 1  # o resumo coerente e construivel
    with pytest.raises(ErroDeFonteDeGatilho) as erro:
        _resumo(lidas=2, ids_criados=1, recusas=())
    assert "nao fecha" in str(erro.value)


def test_resumo_sem_um_dos_quatro_estados_e_recusado():
    """Estado ausente do resumo seria indistinguivel de zero eventos."""
    with pytest.raises(ErroDeFonteDeGatilho) as erro:
        _resumo(
            por_estado=(
                ContagemPorEstado(EstadoDeGatilho.ACEITO, 1),
                ContagemPorEstado(EstadoDeGatilho.FALSO, 0),
                ContagemPorEstado(EstadoDeGatilho.INVALIDO, 0),
            )
        )
    assert "quatro estados" in str(erro.value)


def test_resumo_com_contagem_que_nao_bate_com_os_ids_e_recusado():
    with pytest.raises(ErroDeFonteDeGatilho) as erro:
        _resumo(
            lidas=1,
            ids_criados=1,
            por_estado=tuple(
                ContagemPorEstado(estado, 0) for estado in EstadoDeGatilho
            ),
        )
    assert "por_estado soma 0" in str(erro.value)
