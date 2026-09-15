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

let mockCapturas = [];
let mockStats = {};
let mockHealth = {};
let mockServices = [];
let mockNotifications = [];
let mockLotes = [];
let mockQualidade = {};
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
        const resposta = await fetch(this.base + rota, { cache: 'no-store' });

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
            evidencia_url: c.evidencia_url
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
        const noOnline = heartbeat ? String(heartbeat.status).toLowerCase() === 'online' : null;

        return {
            status: noOnline === null ? 'sem leitura' : (noOnline ? 'Online' : 'Offline'),
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

    async item(id, aoPronto) {
        /*
         * A Investigacao navega com o id do CARTAO (`CAP-<n>`), e `/api/item/<id>` responde por id de
         * ITEM. Sem esta traducao o detalhe nunca carregava: o endpoint respondia 404 e a tabela de
         * evidencias aparecia sempre vazia (achado da revisao em navegador).
         */
        const cap = mockCapturas.find(c => c.id === id);
        const itemId = cap ? cap.item : id;

        // Sem esta guarda vira laco: carregar -> re-renderizar -> carregar de novo.
        if (mockItemDetalhe && mockItemDetalhe.item_id === itemId && !mockItemDetalhe.inexistente) {
            if (typeof aoPronto === 'function') { aoPronto(); }
            return mockItemDetalhe;
        }

        try {
            mockItemDetalhe = await this._pega(`/api/item/${encodeURIComponent(itemId)}`);
        } catch (erro) {
            // 404 aqui e RESPOSTA, nao falha de rede: o item nao existe no registro.
            mockItemDetalhe = { item_id: itemId, inexistente: true, motivo: erro.message };
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

            this.estado.banco = saude.banco.caminho;
            this.estado.itens = saude.banco.itens;
            this.estado.adaptador = saude.camera.adaptador;
            this.estado.adaptador_ok = saude.camera.porta_aberta;
            this.estado.carregada = true;
            this.estado.erro = null;
            this.estado.atualizada_em = saude.agora;

            mockCapturas = this._capturas(capturas);
            mockStats = this._resumo(resumo);
            mockHealth = this._saude(saude);
            mockLotes = lotes.lotes;
            mockQualidade = this._qualidade(qualidade);
            mockServices = (saude.servicos || []).map(s => ({
                name: s.nome,
                detail: s.detalhe,
                icon: s.estado === 'ok' ? 'check-circle-2'
                    : s.estado === 'conectado' ? 'camera' : 'triangle-alert',
                status: s.estado,
                state: s.estado === 'ok' || s.estado === 'conectado' ? 'ok' : 'warning'
            }));
            this.estado.qualidade = qualidade;
            mockNotifications = this._notificacoes();
        } catch (erro) {
            this.estado.carregada = false;
            this.estado.erro = erro.message;

            // API fora: a tela fica VAZIA e diz isso. Nao se mantem numero antigo como se fosse atual.
            mockCapturas = [];
            mockStats = {};
            mockHealth = {};
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
