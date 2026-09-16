/*
 * Fonte de dados do site: a API local do hub (`src-production/api.py`, mesma origem).
 *
 * Por que este arquivo substitui o `data.js` (mocks retirados):
 *   o draft do site trazia numero inventado (`mockCapturas`, `mockStats`, `mockHealth`). Numero
 *   inventado nao e so feio: quando a API cai, a tela continua bonita mostrando aprovacao que nunca
 *   foi medida. Aqui as globais existem com o MESMO nome e forma que os templates ja consomem, mas
 *   sao preenchidas pela API — e quando a API nao responde elas ficam VAZIAS com o aviso na tela.
 *
 * Regras que este adaptador faz valer:
 *   * nada de placeholder externo (o mock apontava para placehold.co): imagem ausente vira um
 *     SVG local que diz "sem evidencia registrada";
 *   * ausencia nunca vira zero: metrica sem dado aparece como `--`;
 *   * o selo diz de ONDE vem o dado, com o caminho do banco — demo e linha real nao se confundem.
 */

/*
 * Token de operacao (rotas de POST). Vem do fragmento da URL (`#token=...`) uma vez e fica em
 * sessionStorage: fragmento nao vai para o servidor nem para log de acesso, e o header substitui
 * a query string (token em URL e registrado por qualquer proxy).
 */
const PNAAT_TOKEN = (() => {
    try {
        const m = String(window.location.hash || '').match(/(?:^#|&)token=([^&]+)/);
        if (m) {
            window.sessionStorage.setItem('pnaat_token', decodeURIComponent(m[1]));
            history.replaceState(null, '', window.location.pathname + window.location.search);
        }
        return window.sessionStorage.getItem('pnaat_token') || '';
    } catch (erro) {
        return '';
    }
})();

const PNAAT_HEADERS = extra => {
    const cabecalhos = Object.assign({}, extra || {});
    if (PNAAT_TOKEN) {
        cabecalhos.Authorization = 'Bearer ' + PNAAT_TOKEN;
    }
    return cabecalhos;
};

if (typeof window !== 'undefined') {
    window.PNAAT_HEADERS = PNAAT_HEADERS;
}

const PNAAT_ESCAPE = valor => String(valor === null || valor === undefined ? '' : valor)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

if (typeof window !== 'undefined') {
    window.PNAAT_ESCAPE = PNAAT_ESCAPE;
}

const PNAAT_SAFE_URL = valor => {
    const raw = String(valor === null || valor === undefined ? '' : valor).trim();
    if (raw.startsWith('data:image/')) {
        return raw;
    }
    try {
        const parsed = new URL(raw, window.location.origin);
        return parsed.origin === window.location.origin && parsed.pathname.startsWith('/') ? raw : '';
    } catch {
        return '';
    }
};

if (typeof window !== 'undefined') {
    window.PNAAT_SAFE_URL = PNAAT_SAFE_URL;
}

const PNAAT_OPERATION_OK = corpo => {
    if (!corpo || corpo.ok !== true) {
        return false;
    }
    const dados = corpo.dados || {};
    return dados.parcial !== true
        && !(dados.rig && dados.rig.ok === false)
        && dados.confirmado !== false;
};

if (typeof window !== 'undefined') {
    window.PNAAT_OPERATION_OK = PNAAT_OPERATION_OK;
}

let mockCapturas = [];
let mockStats = {};
let mockHealth = {};
let mockServices = [];
let mockNotifications = [];
let mockLotes = [];
let mockQualidade = {};
let mockDebug = {};
let mockItemDetalhe = null;

const PNAAT_API = {
    base: '',                     // mesma origem: o api.py serve o site e a API juntos
    intervalo_ms: 15000,
    estado: {
        carregada: false,
        erro: null,
        banco: null,
        itens: 0,
        adaptador: null,
        adaptador_ok: false,
        atualizada_em: null
    },

    // ---------------------------------------------------------------- apoio

    async _pega(rota) {
        /*
         * Teto de tempo: sem ele uma API que aceita a conexao e nao responde deixa o selo preso em
         * "carregando" para sempre e o ciclo periodico empilha requisicoes pendentes.
         */
        const resposta = await fetch(this.base + rota, {
            cache: 'no-store',
            signal: AbortSignal.timeout(8000)
        });

        if (!resposta.ok) {
            throw new Error(`${rota} respondeu ${resposta.status}`);
        }

        const corpo = await resposta.json();

        if (!corpo.ok) {
            throw new Error(corpo.erro || `${rota} recusou`);
        }

        return corpo.dados;
    },

    _hora(iso) {
        if (!iso) return '--';

        const d = new Date(iso);

        return isNaN(d) ? String(iso) : d.toTimeString().slice(0, 8);
    },

    _rotuloVista(vista) {
        return { topo: 'Topo', lateral1: 'Lateral 1', lateral2: 'Lateral 2' }[vista] || vista;
    },

    // O template so conhece tres selos: OK | Defeito | Pendente.
    _rotuloStatus(status) {
        return { ok: 'OK', defeito: 'Defeito', inconclusivo: 'Pendente',
                 erro_processamento: 'Pendente' }[status] || 'Pendente';
    },

    _semImagem(idItem, vista, motivo) {
        const texto = motivo ? `sem evidencia: ${motivo}` : `sem evidencia registrada (${idItem})`;
        const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
            <rect width="800" height="600" fill="#171a1d"/>
            <text x="400" y="290" fill="#f9fbfd" font-family="monospace" font-size="20"
                  text-anchor="middle">${idItem} - ${vista}</text>
            <text x="400" y="330" fill="#8a929b" font-family="monospace" font-size="16"
                  text-anchor="middle">${texto}</text>
        </svg>`;

        return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
    },

    _pct(valor) {
        return valor === null || valor === undefined ? '--' : `${Math.round(valor * 100)}%`;
    },

    _ms(valor) {
        return valor === null || valor === undefined ? '--' : `${Math.round(valor)} ms`;
    },

    // ---------------------------------------------------------------- mapeamento

    _capturas(dados) {
        return dados.capturas.map(c => ({
            id: `CAP-${c.id}`,
            item: c.item_id,
            vista: this._rotuloVista(c.vista),
            dominio: c.dominio || '--',
            papel: c.papel,
            lote: c.lote || '(sem lote)',
            timestamp: this._hora(c.timestamp_trigger),
            codigo: c.codigo_defeito || '--',
            status: this._rotuloStatus(c.status_item),
            status_item: c.status_item,
            status_vista: c.status_vista,
            motivo: c.motivo_inconclusivo || null,
            confianca: this._pct(c.confianca),
            latencia: this._ms(c.latencia_ms),
            qualidade: c.qualidade_registro || '--',
            img: c.evidencia_url || this._semImagem(c.item_id, this._rotuloVista(c.vista),
                                                     c.motivo_inconclusivo),
            tem_evidencia: c.tem_evidencia,
            evidencia_url: c.evidencia_url,

            // valores CRUS do registro: a tela usa os rotulos, o CSV usa estes
            id_registro: c.id,
            confianca_valor: c.confianca,
            latencia_valor: c.latencia_ms,
            timestamp_trigger_iso: c.timestamp_trigger,
            timestamp_captura_iso: c.timestamp_captura,
            dominio_registro: c.dominio || '',
            vista_registro: c.vista
        }));
    },

    _resumo(dados) {
        const estados = dados.contagem_por_estado || {};

        const latencias = mockCapturas
            .map(c => parseInt(c.latencia, 10))
            .filter(v => !isNaN(v));

        const media = latencias.length
            ? Math.round(latencias.reduce((a, b) => a + b, 0) / latencias.length)
            : null;

        return {
            totalLote: dados.total ?? '--',
            aprovados: dados.aprovados ?? '--',
            reprovados: estados.defeito ?? '--',
            inconclusivos: estados.inconclusivo ?? '--',
            taxaDefeito: dados.total ? this._pct((estados.defeito || 0) / dados.total) : '--',
            latenciaMedia: this._ms(media),
            producaoAnterior: '--',          // nao ha serie historica no registro: nao se inventa
            tendencia: (dados.tendencia || []).map(t => t.itens),
            nota: 'inconclusivo nao entra em aprovados (so `ok` aprova)'
        };
    },

    _saude(saude) {
        const hw = saude.hardware || {};
        const camera = saude.camera || {};
        const memoria = hw.memoria || {};

        /*
         * Estado geral = o que a resposta prova (a API respondeu) + o heartbeat do no. Antes era o
         * adaptador do modelo: com o modelo fora do ar a tela mostrava tudo "ok" e o estado geral
         * "Offline" — o site se declarando fora do ar enquanto servia o proprio painel.
         */
        const heartbeat = saude.heartbeat || null;
        const statusNo = heartbeat ? String(heartbeat.status || '').toLowerCase() : null;
        const estadoNo = ['online', 'degradado', 'offline'].includes(statusNo) ? statusNo : null;
        const rotulosNo = { online: 'Online', degradado: 'Degradado', offline: 'Offline' };

        return {
            status: estadoNo ? rotulosNo[estadoNo] : 'sem leitura',
            statusNo: estadoNo,
            statusFonte: 'heartbeat do no + resposta da API',
            adaptador: camera.adaptador || '--',
            adaptadorEstado: camera.porta_aberta ? 'respondendo' : 'sem resposta',
            adaptadorMotivo: camera.motivo || null,
            cpu: hw.cpu_carga_1min === null || hw.cpu_carga_1min === undefined
                ? '--' : hw.cpu_carga_1min.toFixed(2),
            memoria: memoria.usada_mb ? `${(memoria.usada_mb / 1024).toFixed(1)} GB` : '--',
            temperatura: hw.temperatura_c === null || hw.temperatura_c === undefined
                ? '--' : `${hw.temperatura_c} °C`,
            armazenamento: hw.armazenamento
                ? `${(hw.armazenamento.livre_mb / 1024).toFixed(1)} GB livres` : '--',
            armazenamentoTotal: hw.armazenamento
                ? `${(hw.armazenamento.total_mb / 1024).toFixed(1)} GB` : '--',
            filaImagens: saude.heartbeat ? saude.heartbeat.fila_pendente : '--',
            latencia: camera.latencia_ms === null || camera.latencia_ms === undefined
                ? '--' : `${camera.latencia_ms} ms`,
            ultimoHeartbeat: saude.heartbeat ? this._hora(saude.heartbeat.timestamp) : '--',
            sem_leitura: hw.sem_leitura || [],
            banco: saude.banco ? saude.banco.caminho : '--',
            itens: saude.banco ? saude.banco.itens : 0
        };
    },

    _qualidade(dados) {
        /*
         * `/api/qualidade` ja respondia e o payload era descartado: a vista Qualidade dizia
         * "integracao pendente". Aqui o payload vira dado de tela, sem inventar campo ausente.
         */
        const pct = valor => (valor === null || valor === undefined)
            ? '--' : `${Math.round(valor * 1000) / 10}%`;

        return {
            latencia: (dados.latencia_por_vista || []).map(l => ({
                vista: this._rotuloVista(l.vista), medidas: l.medidas,
                media: this._ms(l.media_ms), maxima: this._ms(l.maxima_ms)
            })),
            saturacao: (dados.saturacao_por_vista || []).map(s => ({
                vista: this._rotuloVista(s.vista), medidas: s.medidas,
                media: s.media_pct === null || s.media_pct === undefined ? '--' : `${s.media_pct}%`,
                maxima: s.maxima_pct === null || s.maxima_pct === undefined ? '--' : `${s.maxima_pct}%`
            })),
            gatilho: (dados.gatilho_por_fonte || []).map(g => ({
                fonte: g.fonte, eventos: g.eventos, aceitos: g.aceitos, falsos: g.falsos,
                duplicados: g.duplicados, invalidos: g.invalidos, taxa_falso: pct(g.taxa_falso)
            })),
            perda: dados.perda_de_deteccao || { instrumentada: false, motivo: null },
            discordancia: dados.discordancia_lateral || null,
            inconclusivos: dados.inconclusivos_por_lote || [],
            correcoes: dados.correcoes_para_auditoria || [],
            separacoes: dados.separacoes_nao_confirmadas || [],
            nos: (dados.saude_dos_nos || []).map(n => ({
                ponto_id: n.ponto_id, status: n.status, fila_pendente: n.fila_pendente,
                timestamp: this._hora(n.timestamp)
            })),
            correlacao: dados.correlacao_ambiental || null
        };
    },

    _notificacoes() {
        const avisos = [];

        mockCapturas
            .filter(c => c.status_item === 'defeito')
            .slice(0, 5)
            .forEach((c, i) => avisos.push({
                id: `NOT-DEF-${i}`,
                title: 'Defeito no registro',
                message: `${c.item} - vista ${c.vista}, codigo ${c.codigo} (lote ${c.lote})`,
                time: c.timestamp,
                type: 'danger',
                read: false,
                view: 'investigacao',
                param: c.id
            }));

        mockCapturas
            .filter(c => c.status_item === 'inconclusivo')
            .slice(0, 3)
            .forEach((c, i) => avisos.push({
                id: `NOT-INC-${i}`,
                title: 'Item inconclusivo',
                message: `${c.item}: ${c.motivo || 'evidencia insuficiente'} — precisa de decisao humana`,
                time: c.timestamp,
                type: 'neutral',
                read: false,
                view: 'investigacao',
                param: c.id
            }));

        mockServices
            .filter(s => s.state !== 'ok')
            .forEach((s, i) => avisos.push({
                id: `NOT-SRV-${i}`,
                title: 'Servico fora do esperado',
                message: `${s.name}: ${s.status}`,
                time: PNAAT_API.estado.atualizada_em || '--',
                type: 'warning',
                read: false,
                view: 'saude',
                param: null
            }));

        return avisos;
    },

    // ---------------------------------------------------------------- um item

    esquecerDetalhe() {
        /*
         * Invalida o detalhe em cache: depois de uma escrita, a tela le o registro de novo.
         */
        mockItemDetalhe = null;
    },

    async item(id, aoPronto) {
        /*
         * A Investigacao navega com o id do CARTAO (`CAP-<n>`), e `/api/item/<id>` responde por id de
         * ITEM. Sem esta traducao o detalhe nunca carregava: o endpoint respondia 404 e a tabela de
         * evidencias aparecia sempre vazia (achado da revisao em navegador).
         */
        const cap = mockCapturas.find(c => c.id === id);
        const itemId = cap ? cap.item : id;

        /*
         * Cache com veredito, e SEM chamar o callback quando nada foi a rede.
         *
         * O callback aqui era um laco: `aoPronto` re-renderiza a Investigacao, o render pede o item
         * outra vez, o item em cache chama `aoPronto` de novo — tudo SINCRONO, sem await no meio.
         * Medido no site servido: 1968 navegacoes e 1967 pedidos por UMA abertura da vista.
         *
         * 404 tambem e resposta legitima (o item nao existe no registro) e nao se repete; falha de
         * REDE se repete, para uma oscilacao nao virar "nao existe" permanente.
         */
        if (mockItemDetalhe && mockItemDetalhe.item_id === itemId) {
            if (!mockItemDetalhe.falha_de_rede) {
                return mockItemDetalhe;
            }

            mockItemDetalhe = null;
        }

        if (!itemId) {
            return null;
        }

        try {
            mockItemDetalhe = await this._pega(`/api/item/${encodeURIComponent(itemId)}`);
            mockItemDetalhe.inexistente = false;
        } catch (erro) {
            const semRegistro = /\b404\b/.test(erro.message);

            mockItemDetalhe = {
                item_id: itemId,
                inexistente: semRegistro,
                falha_de_rede: !semRegistro,
                motivo: erro.message
            };
        }

        if (typeof aoPronto === 'function') { aoPronto(); }

        return mockItemDetalhe;
    },

    // ---------------------------------------------------------------- selo de origem

    _selo() {
        const alvos = document.querySelectorAll('[data-fonte-dados]');
        const e = this.estado;

        let texto;
        let cor = 'text-white/70';

        if (e.erro) {
            cor = 'text-amber-300';
            texto = `API indisponivel (${e.erro}) — sem dados do registro`;
        } else if (!e.carregada) {
            texto = 'carregando dados do registro...';
        } else {
            texto = `${e.itens} itens | banco ${e.banco} | adaptador ${e.adaptador} `
                + (e.adaptador_ok ? 'respondendo (porta aberta)' : 'sem resposta');
        }

        alvos.forEach(a => {
            a.textContent = texto;
            a.className = cor;
        });
    },

    // ---------------------------------------------------------------- carga

    async carregar(aoPronto) {
        try {
            const [saude, resumo, capturas, qualidade, lotes] = await Promise.all([
                this._pega('/api/health'),
                this._pega('/api/resumo'),
                this._pega('/api/capturas?limite=200'),
                this._pega('/api/qualidade'),
                this._pega('/api/lotes')
            ]);

            // sem `?.` um campo ausente derrubava a carga inteira e a tela ficava com undefined
            this.estado.banco = saude.banco?.caminho || '--';
            this.estado.itens = saude.banco?.itens ?? 0;
            this.estado.totalCapturas = capturas.base ?? capturas.total ?? null;
            this.estado.capturasCarregadas = capturas.total ?? 0;
            this.estado.adaptador = saude.camera?.adaptador || '--';
            this.estado.adaptador_ok = Boolean(saude.camera?.porta_aberta);
            this.estado.carregada = true;
            this.estado.erro = null;
            this.estado.atualizada_em = saude.agora;

            mockCapturas = this._capturas(capturas);
            mockStats = this._resumo(resumo);
            mockHealth = this._saude(saude);
            mockLotes = lotes.lotes;
            mockQualidade = this._qualidade(qualidade);
            /*
             * A API declara 7 literais de estado (ok, conectado, servindo, servido nesta origem, sem
             * banco, sem resposta, ausente). Conhecer so 2 fazia o proprio Site e a raiz de evidencias
             * entrarem como alerta, gerando notificacao falsa a cada carga.
             */
            const SAUDAVEIS = new Set(['ok', 'conectado', 'servindo', 'servido nesta origem']);

            mockServices = (saude.servicos || []).map(s => {
                const estado = String(s.estado || '').toLowerCase();
                const saudavel = SAUDAVEIS.has(estado);

                return {
                    name: s.nome,
                    detail: s.detalhe,
                    icon: estado === 'conectado' ? 'camera'
                        : saudavel ? 'check-circle-2' : 'triangle-alert',
                    status: s.estado,
                    state: saudavel ? 'ok' : 'warning'
                };
            });
            this.estado.qualidade = qualidade;
            mockNotifications = this._notificacoes();
        } catch (erro) {
            this.estado.carregada = false;
            this.estado.erro = erro.message;

            // API fora: a tela fica VAZIA e diz isso. Nao se mantem numero antigo como se fosse atual.
            /*
             * API fora: forma DECLARADA, nao objeto vazio. Com `{}` a tela imprimia 'undefined' e
             * chegava a afirmar leitura ("sensor lido nesta coleta") sem ter lido nada.
             */
            mockCapturas = [];
            mockStats = {
                totalLote: '--', aprovados: '--', reprovados: '--', inconclusivos: '--',
                taxaDefeito: '--', latenciaMedia: '--', producaoAnterior: '--',
                tendencia: [], nota: ''
            };
            mockHealth = {
                status: 'sem leitura', cpu: '--', memoria: '--', temperatura: '--',
                armazenamento: '--', armazenamentoTotal: '--', filaImagens: '--', latencia: '--',
                ultimoHeartbeat: '--', sem_leitura: [], banco: '--', itens: 0
            };
            mockLotes = [];
            mockQualidade = {};
            mockServices = [];
            mockNotifications = [];
            mockItemDetalhe = null;
        }

        this._selo();

        if (typeof aoPronto === 'function') {
            aoPronto();
        }
    },

    iniciar(recarrega) {
        const ciclo = () => this.carregar(recarrega);

        ciclo();

        setInterval(() => {
            if (document.visibilityState === 'visible') {
                ciclo();
            }
        }, this.intervalo_ms);
    }
};

window.PNAAT_API = PNAAT_API;
