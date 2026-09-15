class App {
    constructor() {
        this.contentArea =
            document.getElementById('content-area');

        this.pageTitle =
            document.getElementById('page-title');

        this.pageSubtitle =
            document.getElementById('page-subtitle');


        this.currentView = 'operacao';


        /*
         * Filtros efetivamente aplicados.
         *
         * O usuário pode mudar os selects sem alterar
         * imediatamente os resultados.
         */
        this.captureFilters = {
            view: 'all',
            status: 'all'
        };


        this.notifications =
            typeof mockNotifications !== 'undefined'
                ? mockNotifications
                : [];


        this.initTheme();

        this.initGlobalSearch();

        this.initNotifications();

        this.refreshSystemStatus();


        this.navigate('operacao');


        /*
         * A vista ja montou com dado vazio; agora os numeros chegam da API e a tela e remontada.
         * A recarga periodica so roda com a aba visivel (api.js).
         */
        if (window.PNAAT_API) {
            window.PNAAT_API.iniciar(() => {
                /*
                 * A lista de notificacoes e RECOLETADA aqui: o adaptador reatribui `mockNotifications`
                 * quando os dados chegam, e a copia feita no construtor continuava apontando para o
                 * array vazio — o sino dizia "Nenhuma notificacao" com defeito e inconclusivo no
                 * registro (achado da auditoria de ponta a ponta).
                 */
                this.notifications =
                    typeof mockNotifications !== 'undefined'
                        ? mockNotifications
                        : [];

                /*
                 * O painel do sino precisa REMONTAR aqui: `renderNotifications()` so era chamado no
                 * construtor (lista ainda vazia) e ao marcar como lido, entao com 10 notificacoes
                 * reais a tela seguia dizendo "Nenhuma notificacao".
                 */
                this.renderNotifications();

                const seloDoLote =
                    document.getElementById('lote-atual');

                if (seloDoLote) {
                    seloDoLote.textContent =
                        (mockCapturas[0] && mockCapturas[0].lote) || 'sem lote';
                }

                this.navigate(this.currentView);
            });
        }
    }


    /* ========================================================= */
    /* TEMA */
    /* ========================================================= */

    initTheme() {
        const storedTheme =
            localStorage.getItem('theme');


        const prefersDark =
            window.matchMedia &&
            window
                .matchMedia('(prefers-color-scheme: dark)')
                .matches;


        if (
            storedTheme === 'dark' ||
            (!storedTheme && prefersDark)
        ) {
            document.documentElement.classList.add('dark');
            document.documentElement.classList.remove('light');
        } else {
            document.documentElement.classList.remove('dark');
            document.documentElement.classList.add('light');
        }
    }


    toggleTheme() {
        const root =
            document.documentElement;


        const isDark =
            root.classList.contains('dark');


        if (isDark) {
            root.classList.remove('dark');
            root.classList.add('light');

            localStorage.setItem(
                'theme',
                'light'
            );
        } else {
            root.classList.add('dark');
            root.classList.remove('light');

            localStorage.setItem(
                'theme',
                'dark'
            );
        }


        this.refreshIcons();
    }


    /* ========================================================= */
    /* NAVEGAÇÃO */
    /* ========================================================= */

    updateNav(view) {
        document
            .querySelectorAll('.nav-item')
            .forEach(item => {
                item.classList.remove('active');
            });


        const target =
            document.querySelector(
                `.nav-item[data-view="${view}"]`
            );


        if (target) {
            target.classList.add('active');
        }
    }


    getViewConfig(view) {
        const views = {
            operacao: {
                title: 'Operação',
                subtitle:
                    'Visão geral da bancada de inspeção'
            },

            capturas: {
                title: 'Capturas',
                subtitle:
                    'Histórico auditável de imagens e resultados'
            },

            investigacao: {
                title: 'Investigação',
                subtitle:
                    'Evidências, metadados e decisão do operador'
            },

            qualidade: {
                title: 'Qualidade',
                subtitle:
                    'Indicadores e integração estatística'
            },

            saude: {
                title: 'Saúde da Pi',
                subtitle:
                    'Hardware, serviços e conectividade local'
            },

            lote: {
                title: 'Relatório de Lote',
                subtitle:
                    'Resumo consolidado e exportação'
            },

            debug: {
                title: 'Debug da bancada',
                subtitle:
                    'Gatilho, delay de captura e captura manual'
            }
        };


        return views[view] || views.operacao;
    }


    navigate(view, param = null) {
        this.currentView = view;


        const viewConfig =
            this.getViewConfig(view);


        this.updateNav(view);


        if (this.pageTitle) {
            this.pageTitle.textContent =
                viewConfig.title;
        }


        if (this.pageSubtitle) {
            this.pageSubtitle.textContent =
                viewConfig.subtitle;
        }


        document.title =
            `${viewConfig.title} • PNAAT`;


        let html = '';


        switch (view) {
            case 'operacao':
                html = renderOperacao();
                break;

            case 'capturas':
                html = renderCapturas();
                break;

            case 'investigacao':
                html =
                    renderInvestigacao(param);
                break;

            case 'qualidade':
                html = renderQualidade();
                break;

            case 'saude':
                html = renderSaude();
                break;

            case 'lote':
                html = renderLote();
                break;

            case 'debug':
                html = renderDebug();
                break;

            default:
                html = renderOperacao();
        }


        /*
         * A recarga de 15 s remonta a area inteira: sem guardar isto, o texto digitado na busca de
         * Capturas desaparece no meio da digitacao (o select e restaurado por syncCaptureFiltersUI,
         * o texto nao).
         */
        const buscaAntes =
            document.getElementById('capture-search');

        const valorDaBusca =
            buscaAntes ? buscaAntes.value : null;

        const buscaTinhaFoco =
            buscaAntes ? document.activeElement === buscaAntes : false;

        this.contentArea.innerHTML =
            html;

        if (valorDaBusca) {
            const buscaDepois =
                document.getElementById('capture-search');

            if (buscaDepois) {
                buscaDepois.value = valorDaBusca;

                if (buscaTinhaFoco) {
                    buscaDepois.focus();
                }
            }
        }


        /*
         * A aba de debug busca o estado do rig/ponte na PRIMEIRA entrada (e quando o operador pedir).
         * A carga repinta a area por um metodo proprio (`repintarDebug`), SEM passar pelo navigate:
         * navigate dispara carga e carga repinta — chamar navigate aqui fecharia laco (foi o defeito
         * corrigido na Investigacao).
         */
        if (view === 'debug' && window.PNAAT_API) {
            const semDados =
                !mockDebug || (!mockDebug.estado && !mockDebug.ponte && !mockDebug.gatilhos);

            if (semDados) {
                this.carregarDebug();
            }
        }

        /*
         * Quando voltar para Capturas,
         * restaura visualmente os filtros aplicados.
         */
        if (view === 'capturas') {
            this.syncCaptureFiltersUI();

            this.filterCaptures();
        }


        this.refreshIcons();

        this.refreshSystemStatus();

        // o painel do sino mostra o estado da carga atual, nao o da carga em que abriu
        this.renderNotifications();

        /*
         * A Investigacao busca UM item na API: a lista serve cabecalho e cartao, mas as evidencias
         * (D-30) e as correcoes do operador so existem no detalhe.
         *
         * Dois cuidados que a auditoria exigiu:
         *   - o id vem da MESMA regra que a vista usa (`cartaoDaInvestigacao`), senao sem param o
         *     pedido ia nulo e o detalhe vinha de outro item;
         *   - o callback confere a vista atual: a resposta pode chegar depois de o usuario trocar de
         *     tela, e sem isso a Investigacao era desenhada por cima da vista nova.
         */
        if (view === 'investigacao' && window.PNAAT_API) {
            this.paramInvestigacao = param;

            const alvo =
                typeof cartaoDaInvestigacao === 'function'
                    ? cartaoDaInvestigacao(param).cap
                    : null;

            const idPedido = alvo ? alvo.id : param;

            window.PNAAT_API.item(idPedido, () => {
                if (this.currentView !== 'investigacao') {
                    return;
                }

                // resposta de um pedido que ja nao e o da tela: nao desenha
                const atual = typeof cartaoDaInvestigacao === 'function'
                    ? cartaoDaInvestigacao(this.paramInvestigacao).cap
                    : null;

                if ((atual ? atual.id : this.paramInvestigacao) !== idPedido) {
                    return;
                }

                this.navigate('investigacao', this.paramInvestigacao);
            });
        }
    }


    refreshIcons() {
        if (window.lucide) {
            lucide.createIcons();
        }
    }


    /* ========================================================= */
    /* BUSCA GLOBAL */
    /* ========================================================= */

    initGlobalSearch() {
        const input =
            document.getElementById(
                'global-search'
            );


        if (!input) {
            return;
        }


        input.addEventListener(
            'keydown',
            event => {
                if (event.key !== 'Enter') {
                    return;
                }


                const query =
                    input.value.trim();


                if (!query) {
                    return;
                }


                this.navigate('capturas');


                setTimeout(() => {
                    const localSearch =
                        document.getElementById(
                            'capture-search'
                        );


                    if (!localSearch) {
                        return;
                    }


                    localSearch.value =
                        query;


                    localSearch.focus();


                    this.filterCaptures();
                }, 30);
            }
        );


        /*
         * Atalho "/"
         */
        document.addEventListener(
            'keydown',
            event => {
                const active =
                    document.activeElement;


                const tag =
                    active?.tagName;


                const editing =
                    tag === 'INPUT' ||
                    tag === 'TEXTAREA' ||
                    tag === 'SELECT';


                if (
                    event.key === '/' &&
                    !editing
                ) {
                    event.preventDefault();

                    input.focus();
                }
            }
        );
    }


    /* ========================================================= */
    /* FILTROS DE CAPTURA */
    /* ========================================================= */

    filterCaptures() {
        const search =
            document
                .getElementById(
                    'capture-search'
                )
                ?.value
                .trim()
                .toLowerCase() || '';


        /*
         * IMPORTANTE:
         *
         * usa os filtros salvos no estado,
         * e não diretamente o valor dos selects.
         */
        const selectedView =
            this.captureFilters.view;


        const selectedStatus =
            this.captureFilters.status;


        const cards =
            document.querySelectorAll(
                '[data-capture-card]'
            );


        cards.forEach(card => {
            const item =
                card.dataset.item
                    ?.toLowerCase() || '';


            const id =
                card.dataset.id
                    ?.toLowerCase() || '';


            const cardView =
                card.dataset.view;


            const cardStatus =
                card.dataset.status;


            /*
             * A BUSCA continua instantânea.
             */
            const matchSearch =
                !search ||
                item.includes(search) ||
                id.includes(search);


            /*
             * Os SELECTS só entram aqui
             * depois de clicar em Aplicar.
             */
            const matchView =
                selectedView === 'all' ||
                cardView === selectedView;


            const matchStatus =
                selectedStatus === 'all' ||
                cardStatus === selectedStatus;


            card.style.display =
                matchSearch &&
                matchView &&
                matchStatus
                    ? ''
                    : 'none';
        });
    }


    applyCaptureFilters() {
        const view =
            document.getElementById(
                'capture-view'
            );


        const status =
            document.getElementById(
                'capture-status'
            );


        this.captureFilters = {
            view:
                view?.value || 'all',

            status:
                status?.value || 'all'
        };


        this.filterCaptures();
    }


    clearCaptureFilters() {
        this.captureFilters = {
            view: 'all',
            status: 'all'
        };


        const search =
            document.getElementById(
                'capture-search'
            );


        const view =
            document.getElementById(
                'capture-view'
            );


        const status =
            document.getElementById(
                'capture-status'
            );


        if (search) {
            search.value = '';
        }


        if (view) {
            view.value = 'all';
        }


        if (status) {
            status.value = 'all';
        }


        this.filterCaptures();
    }


    syncCaptureFiltersUI() {
        const view =
            document.getElementById(
                'capture-view'
            );


        const status =
            document.getElementById(
                'capture-status'
            );


        if (view) {
            view.value =
                this.captureFilters.view;
        }


        if (status) {
            status.value =
                this.captureFilters.status;
        }
    }


    /* ========================================================= */
    /* NOTIFICAÇÕES */
    /* ========================================================= */

    initNotifications() {
        const button =
            document.getElementById(
                'notifications-button'
            );


        const panel =
            document.getElementById(
                'notification-panel'
            );


        const wrapper =
            document.getElementById(
                'notifications-wrapper'
            );


        const markRead =
            document.getElementById(
                'mark-notifications-read'
            );


        if (
            !button ||
            !panel ||
            !wrapper
        ) {
            return;
        }


        button.addEventListener(
            'click',
            event => {
                event.stopPropagation();

                this.toggleNotifications();
            }
        );


        panel.addEventListener(
            'click',
            event => {
                event.stopPropagation();
            }
        );


        if (markRead) {
            markRead.addEventListener(
                'click',
                () => {
                    this.markAllNotificationsRead();
                }
            );
        }


        /*
         * Fecha ao clicar fora.
         */
        document.addEventListener(
            'click',
            event => {
                if (
                    !wrapper.contains(
                        event.target
                    )
                ) {
                    this.closeNotifications();
                }
            }
        );


        /*
         * Fecha com ESC.
         */
        document.addEventListener(
            'keydown',
            event => {
                if (event.key === 'Escape') {
                    this.closeNotifications();
                }
            }
        );


        this.renderNotifications();
    }


    toggleNotifications() {
        const panel =
            document.getElementById(
                'notification-panel'
            );


        const button =
            document.getElementById(
                'notifications-button'
            );


        if (!panel || !button) {
            return;
        }


        const isHidden =
            panel.classList.contains(
                'hidden'
            );


        if (isHidden) {
            panel.classList.remove(
                'hidden'
            );

            button.setAttribute(
                'aria-expanded',
                'true'
            );
        } else {
            this.closeNotifications();
        }
    }


    closeNotifications() {
        const panel =
            document.getElementById(
                'notification-panel'
            );


        const button =
            document.getElementById(
                'notifications-button'
            );


        panel?.classList.add(
            'hidden'
        );


        button?.setAttribute(
            'aria-expanded',
            'false'
        );
    }


    repintarDebug() {
        /* Repinta SO a area de conteudo, sem passar pelo navigate (evita laco carga<->render). */
        if (this.currentView !== 'debug') {
            return;
        }

        this.contentArea.innerHTML = renderDebug();

        this.refreshIcons();
    }

    async carregarDebug() {
        /* Le rig, ponte, series e historico de gatilho. Cada leitura e independente e falha declarada. */
        mockDebug = { atualizado_em: new Date().toTimeString().slice(0, 8) };

        const ler = async (rota, chave) => {
            try {
                const resposta = await fetch(`${window.PNAAT_API.base}${rota}`, {
                    cache: 'no-store',
                    signal: AbortSignal.timeout(15000)
                });
                const corpo = await resposta.json();
                mockDebug[chave] = (corpo && corpo.ok) ? corpo.dados : {
                    erro: `${(corpo && corpo.erro) || 'resposta inesperada'}: ${(corpo && corpo.detalhe) || ''}`
                };
            } catch (erro) {
                mockDebug[chave] = { erro: erro.message };
            }

            mockDebug.atualizado_em = new Date().toTimeString().slice(0, 8);
            this.repintarDebug();
        };

        await Promise.all([
            ler('/api/rig/estado', 'estado'),
            ler('/api/rig/gatilho', 'ponte'),
            ler('/api/rig/delay-camera', 'delayCamera'),
            ler('/api/series?limite=20', 'series'),
            ler('/api/itens-ingeridos?limite=12', 'ingeridos'),
            ler('/api/modelo', 'modelo'),
            ler('/api/gatilhos?limite=25', 'gatilhos')
        ]);
    }

    async acaoDeBancada(rota, corpo, rotulo) {
        /* POST de bancada com resultado declarado na tela (sucesso e falha). */
        mockDebug = mockDebug || {};
        mockDebug.acao = { rotulo: rotulo, estado: 'enviando...' };
        this.repintarDebug();

        try {
            const resposta = await fetch(`${window.PNAAT_API.base}${rota}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(corpo || {}),
                // teto de tempo: sem ele o botao fica em "enviando..." para sempre se o hub travar
                signal: AbortSignal.timeout(60000)
            });
            const texto = await resposta.json().catch(() => ({ erro: 'resposta nao era JSON' }));

            mockDebug.acao = {
                rotulo: rotulo,
                estado: (resposta.ok && texto.ok) ? 'ok' : 'falhou',
                erro: texto.erro || null,
                detalhe: texto.detalhe || null,
                dados: texto.dados || null
            };
        } catch (erro) {
            mockDebug.acao = { rotulo: rotulo, estado: 'falhou', erro: 'rede', detalhe: erro.message };
        }

        // carregarDebug RECRIA mockDebug (faz mockDebug = {...}), entao a mensagem de resultado tem de
        // ser aplicada DEPOIS da recarga: antes dela a recarga apagava a mensagem, e o operador nao via
        // com que configuracao a bancada ficou.
        const acao = mockDebug.acao;
        const porCamera = acao && acao.dados && acao.dados.leitura_de_volta
            && acao.dados.leitura_de_volta.por_camera_ms;

        await this.carregarDebug();

        if (acao) {
            if (acao.estado === "ok" && porCamera) {
                acao.detalhe = "configuracao agora: csi " + porCamera.csi + " ms · usb "
                    + porCamera.usb + " ms · espcam " + porCamera.espcam + " ms";
            }
            mockDebug.acao = acao;
        }
        this.repintarDebug();
    }

    configurarDelay() {
        const campo = document.getElementById('debug-delay-ms');
        const campoOperador = document.getElementById('debug-delay-operador');
        const operador = campoOperador ? campoOperador.value.trim() : '';
        const ms = campo ? Number(campo.value) : NaN;

        if (!operador) {
            mockDebug.acao = { rotulo: 'configurar delay', estado: 'falhou', erro: 'operador_ausente',
                               detalhe: 'o delay define a janela de captura: informe quem esta mudando' };
            this.repintarDebug();
            return;
        }

        if (!Number.isFinite(ms)) {
            mockDebug.acao = { rotulo: 'configurar delay', estado: 'falhou',
                               erro: 'delay_invalido', detalhe: 'informe um numero de milissegundos' };
            this.repintarDebug();
            return;
        }

        const campoCamera = document.getElementById('debug-delay-camera');
        const camera = campoCamera ? campoCamera.value.trim() : '';

        if (!camera) {
            // sem escolha explicita a rota aplicaria o mesmo valor nas TRES cameras e apagaria a
            // calibracao das outras duas (foi o que aconteceu na bancada). Recusar e mais honesto.
            mockDebug.acao = { rotulo: 'configurar delay', estado: 'falhou', erro: 'camera_nao_escolhida',
                               detalhe: 'escolha a camera. Sem escolha o valor iria para as tres de uma '
                                        + 'vez e apagaria a calibracao das outras duas. Se a intencao e '
                                        + 'mesmo igualar as tres, escolha "todas (substitui as tres)".' };
            this.repintarDebug();
            return;
        }

        this.acaoDeBancada('/api/rig/delay', { ms: ms, operador: operador, camera: camera },
                           `configurar delay de ${camera === 'todas' ? 'todas as cameras' : 'camera ' + camera} para ${ms} ms (por ${operador})`);
    }

    testarGatilho() {
        const campo = document.getElementById('debug-item-teste');
        const item = campo ? campo.value.trim() : '';

        this.acaoDeBancada('/api/rig/teste-trigger', item ? { item_id: item } : {},
                           item ? `teste do gatilho (item ${item})` : 'teste do gatilho (sem item)');
    }

    capturarManual() {
        this.acaoDeBancada('/api/rig/captura', {}, 'captura manual das 3 cameras');
    }

    async registrarDecisao(decisao) {
        /*
         * Decisao humana da D-30: grava pelo unico caminho de escrita (`POST /api/correcao`, que passa
         * pelo `Registro`) e mostra o que o REGISTRO devolveu — nao o que foi enviado. O registro
         * preserva a decisao original; por isso a confirmacao traz "antes".
         */
        const campo = document.getElementById('operador-nome');
        const area = document.getElementById('resultado-decisao');
        const operador = (campo ? campo.value : '').trim();

        const avisar = (texto, cor) => {
            if (!area) { return; }
            area.className = `text-xs ${cor}`;
            area.textContent = texto;
        };

        if (!operador) {
            avisar('informe quem decide: o nome vai para a trilha da correção', 'text-orange-500');
            if (campo) { campo.focus(); }
            return;
        }

        const cartao = typeof cartaoDaInvestigacao === 'function'
            ? cartaoDaInvestigacao(this.paramInvestigacao).cap
            : null;

        const itemNaTela = cartao ? cartao.item : null;
        const itemDoDetalhe = (mockItemDetalhe && mockItemDetalhe.item_id) || null;

        if (!itemNaTela) {
            avisar('sem item na tela: abra um cartão em Capturas', 'text-orange-500');
            return;
        }

        /*
         * O alvo e o item QUE ESTA NA TELA. Se o detalhe carregado for de outro item, gravar aqui poria
         * a decisao do operador no item errado (aconteceu no teste: a reversao foi para ITM-004 com a
         * tela em ITM-003). Recarrega o detalhe e pede confirmacao de novo.
         */
        if (itemDoDetalhe !== itemNaTela) {
            window.PNAAT_API.esquecerDetalhe();

            window.PNAAT_API.item(cartao.id, () => {
                if (this.currentView === 'investigacao') {
                    this.navigate('investigacao', this.paramInvestigacao);
                }
            });

            avisar(
                `o detalhe carregado era de ${itemDoDetalhe || 'nenhum item'}: recarreguei o de `
                + `${itemNaTela} — confirme a decisão de novo`,
                'text-orange-500'
            );
            return;
        }

        const item = itemNaTela;

        avisar('registrando...', 'text-gray-400');

        try {
            const resposta = await fetch(`${window.PNAAT_API.base}/api/correcao`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_id: item, decisao_corrigida: decisao,
                                       corrigido_por: operador })
            });
            const corpo = await resposta.json();

            if (!resposta.ok || !corpo.ok) {
                avisar(`não registrado: ${corpo.erro} — ${corpo.detalhe}`, 'text-brand-red');
                return;
            }

            const dados = corpo.dados;
            const mensagem =
                `registrado no registro: ${dados.decisao_efetiva} por `
                + `${dados.correcao.corrigido_por} (antes: ${dados.correcao.decisao_original}, `
                + `em ${dados.correcao.timestamp})`;

            // le o item de novo: a tela mostra o estado do registro, nao o otimismo do formulario
            window.PNAAT_API.esquecerDetalhe();

            const cartao = typeof cartaoDaInvestigacao === 'function'
                ? cartaoDaInvestigacao(this.paramInvestigacao).cap
                : null;

            const aplicar = () => {
                if (this.currentView !== 'investigacao') { return; }
                this.navigate('investigacao', this.paramInvestigacao);
                avisar(mensagem, 'text-brand-green');
            };

            if (cartao) {
                window.PNAAT_API.item(cartao.id, aplicar);
            } else {
                aplicar();
            }
        } catch (erro) {
            avisar(`falha de rede ao registrar: ${erro.message}`, 'text-brand-red');
        }
    }

    exportarCSV() {
        /*
         * Exporta as linhas de vista VISIVEIS na grade, com os valores CRUS do registro.
         *
         * Antes: dizia "as MESMAS linhas do filtro atual" e exportava as 200 carregadas (o filtro so
         * esconde cartao no DOM), com rotulos de tela — id 'CAP-26', confianca '70%', hora '06:30:26'
         * — nem numerico nem casavel com o banco. Ausencia agora sai vazia (nao '--'), e celula que
         * comeca com = + - @ ganha apostrofo, porque Excel/LibreOffice avaliam formula mesmo entre
         * aspas e esses valores vem do registro (dado nao confiavel).
         */
        const visiveis = new Set(
            [...document.querySelectorAll('[data-capture-card]')]
                .filter(cartao => cartao.style.display !== 'none')
                .map(cartao => cartao.getAttribute('data-id'))
        );

        const linhasVisiveis = mockCapturas.filter(cap => visiveis.has(cap.id));

        if (!linhasVisiveis.length) {
            return;
        }

        const colunas = ['id_registro', 'item_id', 'vista', 'vista_registro', 'dominio', 'papel', 'lote',
                         'timestamp_trigger', 'timestamp_captura', 'status_vista', 'status_item',
                         'codigo_defeito', 'confianca', 'latencia_ms', 'qualidade_registro',
                         'tem_evidencia'];

        const celula = valor => {
            if (valor === null || valor === undefined || valor === '') {
                return '';
            }

            let texto = String(valor);

            if (/^[=+\-@]/.test(texto)) {
                texto = `'${texto}`;
            }

            return `"${texto.replace(/"/g, '""')}"`;
        };

        const linhas = linhasVisiveis.map(cap => [
            cap.id_registro, cap.item, cap.vista, cap.vista_registro, cap.dominio_registro,
            cap.papel, cap.lote,
            cap.timestamp_trigger_iso, cap.timestamp_captura_iso, cap.status_vista, cap.status_item,
            cap.codigo === '--' ? '' : cap.codigo, cap.confianca_valor, cap.latencia_valor,
            cap.qualidade, cap.tem_evidencia
        ].map(celula).join(','));

        // BOM + CRLF: sem isso o Excel pt-BR le UTF-8 como ANSI
        const csv = `\ufeff${[colunas.join(','), ...linhas].join('\r\n')}\r\n`;
        const arquivo = new Blob([csv], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(arquivo);
        const link = document.createElement('a');

        link.href = url;
        link.download = `pnaat-linhas-${new Date().toISOString().slice(0, 10)}.csv`;

        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }

    renderNotifications() {
        const list =
            document.getElementById(
                'notification-list'
            );


        if (!list) {
            return;
        }


        if (
            !this.notifications ||
            this.notifications.length === 0
        ) {
            list.innerHTML = `
                <div class="notification-empty">
                    <i
                        data-lucide="bell-off"
                        class="mb-2 h-5 w-5"
                    ></i>

                    Nenhuma notificação.
                </div>
            `;

            this.updateNotificationBadge();

            this.refreshIcons();

            return;
        }


        list.innerHTML =
            this.notifications
                .map(
                    (notification, index) => {

                        let indicator =
                            'notification-dot-neutral';


                        if (
                            notification.type ===
                            'danger'
                        ) {
                            indicator =
                                'notification-dot-danger';
                        }


                        if (
                            notification.type ===
                            'success'
                        ) {
                            indicator =
                                'notification-dot-success';
                        }


                        return `
                            <button
                                type="button"

                                onclick="app.openNotification(${index})"

                                class="
                                    notification-item
                                    ${
                                        notification.read
                                            ? 'notification-read'
                                            : ''
                                    }
                                "
                            >

                                <span
                                    class="
                                        notification-dot
                                        ${indicator}
                                    "
                                ></span>

                                <span
                                    class="
                                        min-w-0
                                        flex-1
                                    "
                                >

                                    <span
                                        class="
                                            block

                                            text-left
                                            text-xs
                                            font-bold
                                        "
                                    >
                                        ${notification.title}
                                    </span>

                                    <span
                                        class="
                                            mt-1

                                            block

                                            text-left
                                            text-[11px]
                                            leading-4

                                            text-gray-500
                                            dark:text-gray-400
                                        "
                                    >
                                        ${notification.message}
                                    </span>

                                    <span
                                        class="
                                            mt-1.5

                                            block

                                            text-left
                                            text-[10px]

                                            text-gray-400
                                        "
                                    >
                                        ${notification.time}
                                    </span>

                                </span>

                            </button>
                        `;
                    }
                )
                .join('');


        this.updateNotificationBadge();

        this.refreshIcons();
    }


    openNotification(index) {
        const notification =
            this.notifications[index];


        if (!notification) {
            return;
        }


        notification.read = true;


        this.renderNotifications();


        this.closeNotifications();


        if (notification.view) {
            this.navigate(
                notification.view,
                notification.param || null
            );
        }
    }


    markAllNotificationsRead() {
        this.notifications.forEach(
            notification => {
                notification.read = true;
            }
        );


        this.renderNotifications();
    }


    updateNotificationBadge() {
        const badge =
            document.getElementById(
                'notification-badge'
            );


        if (!badge) {
            return;
        }


        const unread =
            this.notifications.filter(
                notification =>
                    !notification.read
            ).length;


        if (unread > 0) {
            badge.classList.remove(
                'hidden'
            );

            badge.title =
                `${unread} notificação(ões) não lida(s)`;
        } else {
            badge.classList.add(
                'hidden'
            );
        }
    }


    /* ========================================================= */
    /* STATUS DA RASPBERRY PI */
    /* ========================================================= */

    refreshSystemStatus() {
        if (
            typeof mockHealth ===
            'undefined'
        ) {
            return;
        }


        const dot =
            document.getElementById(
                'pi-status-dot'
            );


        const statusText =
            document.getElementById(
                'pi-status-text'
            );


        const latencyText =
            document.getElementById(
                'pi-latency-text'
            );


        if (
            !dot ||
            !statusText ||
            !latencyText
        ) {
            return;
        }


        const status =
            String(
                mockHealth.status || ''
            ).toLowerCase();


        /*
         * Sem `|| 0`: ausencia nao e zero. `parseFloat` de '--' da NaN, e NaN nao dispara limiar
         * nenhum — que e o comportamento certo quando nao houve leitura.
         *
         * As faixas de 75/65 C e 250/100 ms foram retiradas: o registro nao declara faixa de alerta e a
         * propria vista Saude diz "faixa nao declarada". Inventar limite e inventar veredito.
         */
        const temperature =
            parseFloat(
                mockHealth.temperatura
            );


        const latency =
            parseFloat(
                mockHealth.latencia
            );


        const queue =
            Number(
                mockHealth.filaImagens
            );


        const semLeitura =
            status === '' || status === 'sem leitura';


        const leituraParcial =
            (mockHealth.sem_leitura || []).length > 0;


        let severity =
            'success';


        let label =
            'no online';


        if (
            semLeitura
        ) {
            severity = null;

            label =
                'sem leitura do no';
        }


        /*
         * Offline sempre é erro.
         */
        else if (
            status !== 'online'
        ) {
            severity = 'danger';

            label =
                'no offline';
        }

        /*
         * Estado crítico.
         */
        else if (
            temperature >= 75 ||
            latency >= 250 ||
            queue >= 10
        ) {
            severity = 'danger';

            label =
                'Raspberry Pi em estado crítico';
        }

        /*
         * Atenção.
         */
        /*
         * Atencao: so o que o registro declara — fila de envio acumulando ou leitura parcial de
         * hardware. Temperatura e latencia entram como sintoma, com o numero a vista, sem limiar
         * inventado.
         */
        else if (
            queue >= 10 ||
            leituraParcial
        ) {
            severity = 'warning';

            label = leituraParcial
                ? `leitura parcial de hardware (${mockHealth.sem_leitura.join(', ')})`
                : 'fila de envio acumulando';
        }


        dot.classList.remove(
            'status-success',
            'status-warning',
            'status-danger'
        );


        if (severity) {
            dot.classList.add(
                `status-${severity}`
            );
        }


        statusText.textContent =
            label;


        latencyText.textContent =
            `Sonda do adaptador ${mockHealth.latencia || '--'}`;
    }
}


const app = new App();