// js/app.js

class App {
    constructor() {
        this.contentArea = document.getElementById('content-area');
        this.pageTitle = document.getElementById('page-title');
        this.currentView = 'operacao';
        this.initTheme();
        
        // Initial render
        this.navigate('operacao');
    }

    initTheme() {
        // Verifica preferência do sistema ou salva
        if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }

    toggleTheme() {
        if (document.documentElement.classList.contains('dark')) {
            document.documentElement.classList.remove('dark');
            localStorage.theme = 'light';
        } else {
            document.documentElement.classList.add('dark');
            localStorage.theme = 'dark';
        }
    }

    updateNav(view) {
        document.querySelectorAll('.nav-item').forEach(el => {
            el.classList.remove('bg-gray-100', 'dark:bg-dark-border', 'text-brand-red');
        });
        
        // Simples highlight baseado no texto ou ID
        const indexMap = {
            'operacao': 0,
            'capturas': 1,
            'investigacao': 2,
            'qualidade': 3,
            'saude': 4,
            'lote': 5
        };
        
        const navItems = document.querySelectorAll('.nav-item');
        if(navItems[indexMap[view]]) {
            navItems[indexMap[view]].classList.add('bg-gray-100', 'dark:bg-dark-border', 'font-semibold');
        }
    }

    navigate(view, param = null) {
        this.currentView = view;
        this.updateNav(view);
        
        // Limpa a área
        this.contentArea.innerHTML = '';

        // Títulos
        const titles = {
            'operacao': 'Painel de Operação',
            'capturas': 'Histórico de Capturas',
            'investigacao': 'Investigação de Detalhe',
            'qualidade': 'Controle de Qualidade',
            'saude': 'Saúde do Sistema Borda',
            'lote': 'Relatórios de Lote'
        };

        this.pageTitle.innerText = titles[view] || 'PNAAT Vision';

        // Renderiza componente
        let html = '';
        switch(view) {
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
        
        // Re-inicializa ícones dinâmicos injetados
        if(window.lucide) {
            lucide.createIcons();
        }
    }
}

// Inicia aplicação
const app = new App();
