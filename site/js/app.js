// js/app.js

class App {
    constructor() {
        this.contentArea = document.getElementById('content-area');
        this.pageTitle = document.getElementById('page-title');
        this.pageSubtitle = document.getElementById('page-subtitle');
        this.currentView = 'operacao';
        this.initTheme();
        
        // Initial render
        this.navigate('operacao');
    }

    initTheme() {
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
            el.classList.remove('bg-light-bg', 'dark:bg-dark-bg', 'text-brand-red', 'font-bold');
            el.classList.add('text-gray-500', 'dark:text-gray-400');
        });
        
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
            navItems[indexMap[view]].classList.add('bg-light-bg', 'dark:bg-dark-bg', 'text-brand-red', 'font-bold');
            navItems[indexMap[view]].classList.remove('text-gray-500', 'dark:text-gray-400');
        }
    }

    navigate(view, param = null) {
        this.currentView = view;
        this.updateNav(view);
        
        // Limpa a área
        this.contentArea.innerHTML = '';

        // Títulos
        const titles = {
            'operacao': { title: 'Operação', sub: 'Visão geral da bancada em tempo real' },
            'capturas': { title: 'Galeria', sub: 'Histórico auditável de capturas' },
            'investigacao': { title: 'Investigação', sub: 'Análise de evidências e correção' },
            'qualidade': { title: 'Qualidade', sub: 'Métricas e tendências' },
            'saude': { title: 'Saúde Borda', sub: 'Métricas do hardware e serviços' },
            'lote': { title: 'Relatórios', sub: 'Exportação e consolidação' }
        };

        const currentTitles = titles[view] || titles['operacao'];
        if(this.pageTitle) this.pageTitle.innerText = currentTitles.title;
        if(this.pageSubtitle) this.pageSubtitle.innerText = currentTitles.sub;

        // Renderiza componente
        let html = '';
        switch(view) {
            case 'operacao': html = renderOperacao(); break;
            case 'capturas': html = renderCapturas(); break;
            case 'investigacao': html = renderInvestigacao(param); break;
            case 'qualidade': html = renderQualidade(); break;
            case 'saude': html = renderSaude(); break;
            case 'lote': html = renderLote(); break;
            default: html = renderOperacao();
        }

        this.contentArea.innerHTML = html;
        
        if(window.lucide) {
            lucide.createIcons();
        }
    }
}

const app = new App();
