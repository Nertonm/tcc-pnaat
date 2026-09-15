class App {
    constructor() {
        this.contentArea = document.getElementById('content-area');
        this.pageTitle = document.getElementById('page-title');
        this.pageSubtitle = document.getElementById('page-subtitle');

        this.currentView = 'operacao';

        this.initTheme();
        this.initGlobalSearch();

        this.navigate('operacao');
    }

    initTheme() {
        const storedTheme = localStorage.getItem('theme');

        const prefersDark =
            window.matchMedia &&
            window.matchMedia('(prefers-color-scheme: dark)').matches;

        if (storedTheme === 'dark' || (!storedTheme && prefersDark)) {
            document.documentElement.classList.add('dark');
            document.documentElement.classList.remove('light');
        } else {
            document.documentElement.classList.remove('dark');
            document.documentElement.classList.add('light');
        }
    }

    toggleTheme() {
        const root = document.documentElement;

        const isDark = root.classList.contains('dark');

        if (isDark) {
            root.classList.remove('dark');
            root.classList.add('light');

            localStorage.setItem('theme', 'light');
        } else {
            root.classList.add('dark');
            root.classList.remove('light');

            localStorage.setItem('theme', 'dark');
        }

        this.refreshIcons();
    }

    updateNav(view) {
        document
            .querySelectorAll('.nav-item')
            .forEach(item => item.classList.remove('active'));

        const target = document.querySelector(
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
                subtitle: 'Visão geral da bancada de inspeção'
            },

            capturas: {
                title: 'Capturas',
                subtitle: 'Histórico auditável de imagens e resultados'
            },

            investigacao: {
                title: 'Investigação',
                subtitle: 'Evidências, metadados e decisão do operador'
            },

            qualidade: {
                title: 'Qualidade',
                subtitle: 'Indicadores e integração estatística'
            },

            saude: {
                title: 'Saúde da Pi',
                subtitle: 'Hardware, serviços e conectividade local'
            },

            lote: {
                title: 'Relatório de Lote',
                subtitle: 'Resumo consolidado e exportação'
            }
        };

        return views[view] || views.operacao;
    }

    navigate(view, param = null) {
        this.currentView = view;

        const viewConfig = this.getViewConfig(view);

        this.updateNav(view);

        this.pageTitle.textContent = viewConfig.title;
        this.pageSubtitle.textContent = viewConfig.subtitle;

        document.title = `${viewConfig.title} • PNAAT`;

        let html = '';

        switch (view) {
            case 'operacao':
                html = renderOperacao();
                break;

            case 'capturas':
                html = renderCapturas();
                break;

            case 'investigacao':
                html = renderInvestigacao(param);
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

        this.contentArea.innerHTML = html;

        this.refreshIcons();
    }

    refreshIcons() {
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    initGlobalSearch() {
        const input = document.getElementById('global-search');

        if (!input) {
            return;
        }

        input.addEventListener('keydown', event => {
            if (event.key === 'Enter') {
                const query = input.value.trim();

                if (!query) {
                    return;
                }

                this.navigate('capturas');

                setTimeout(() => {
                    const localSearch =
                        document.getElementById('capture-search');

                    if (localSearch) {
                        localSearch.value = query;
                        localSearch.focus();
                    }
                }, 50);
            }
        });

        document.addEventListener('keydown', event => {
            const tag = document.activeElement?.tagName;

            const editing =
                tag === 'INPUT' ||
                tag === 'TEXTAREA' ||
                tag === 'SELECT';

            if (event.key === '/' && !editing) {
                event.preventDefault();

                input.focus();
            }
        });
    }

    filterCaptures() {
        const search =
            document.getElementById('capture-search')
                ?.value
                .trim()
                .toLowerCase() || '';

        const view =
            document.getElementById('capture-view')?.value || 'all';

        const status =
            document.getElementById('capture-status')?.value || 'all';

        const cards = document.querySelectorAll('[data-capture-card]');

        cards.forEach(card => {
            const item = card.dataset.item.toLowerCase();
            const id = card.dataset.id.toLowerCase();
            const cardView = card.dataset.view;
            const cardStatus = card.dataset.status;

            const matchSearch =
                !search ||
                item.includes(search) ||
                id.includes(search);

            const matchView =
                view === 'all' ||
                cardView === view;

            const matchStatus =
                status === 'all' ||
                cardStatus === status;

            card.style.display =
                matchSearch && matchView && matchStatus
                    ? ''
                    : 'none';
        });
    }
}

const app = new App();