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

            default:
                html = renderOperacao();
        }


        this.contentArea.innerHTML =
            html;


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

            window.PNAAT_API.item(alvo ? alvo.id : param, () => {
                if (this.currentView !== 'investigacao') {
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


    exportarCSV() {
        /*
         * Exporta as linhas de vista que a tela mostra — as MESMAS linhas do filtro atual, com os
         * mesmos campos do adaptador. Antes o botao "Exportar CSV" nao tinha handler: era afirmacao
         * funcional sem funcao.
         */
        if (!mockCapturas.length) {
            return;
        }

        const colunas = ['id', 'item', 'vista', 'dominio', 'papel', 'lote', 'timestamp',
                         'status_vista', 'status_item', 'codigo', 'confianca', 'latencia',
                         'qualidade', 'tem_evidencia'];

        const celula = valor => `"${String(valor === null || valor === undefined ? '' : valor)
            .replace(/"/g, '""')}"`;

        const linhas = mockCapturas.map(cap =>
            colunas.map(coluna => celula(cap[coluna])).join(','));

        const csv = [colunas.join(','), ...linhas].join('\n');
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


        const temperature =
            parseFloat(
                mockHealth.temperatura
            ) || 0;


        const latency =
            parseFloat(
                mockHealth.latencia
            ) || 0;


        const queue =
            Number(
                mockHealth.filaImagens
            ) || 0;


        let severity =
            'success';


        let label =
            'Raspberry Pi online';


        /*
         * Offline sempre é erro.
         */
        if (
            status !== 'online'
        ) {
            severity = 'danger';

            label =
                'Raspberry Pi offline';
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
        else if (
            temperature >= 65 ||
            latency >= 100 ||
            queue >= 5
        ) {
            severity = 'warning';

            label =
                'Raspberry Pi requer atenção';
        }


        dot.classList.remove(
            'status-success',
            'status-warning',
            'status-danger'
        );


        dot.classList.add(
            `status-${severity}`
        );


        statusText.textContent =
            label;


        latencyText.textContent =
            `Latência ${mockHealth.latencia || '--'}`;
    }
}


const app = new App();