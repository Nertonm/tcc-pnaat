// js/components.js

const renderOperacao = () => `
    <div class="fade-in-up space-y-8">
        <!-- Metric Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="modern-card p-6 rounded-3xl bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border relative overflow-hidden group">
                <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <i data-lucide="layers" class="w-16 h-16 text-brand-black dark:text-brand-white"></i>
                </div>
                <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Total Produzido</h3>
                <div class="text-4xl font-bold tracking-tight">${mockStats.totalLote}</div>
                <div class="mt-4 flex items-center text-xs text-brand-green">
                    <i data-lucide="trending-up" class="w-4 h-4 mr-1"></i> +12% desde ontem
                </div>
            </div>
            
            <div class="modern-card p-6 rounded-3xl bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border relative overflow-hidden group">
                <div class="absolute inset-y-0 left-0 w-1 bg-brand-green"></div>
                <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <i data-lucide="check-circle" class="w-16 h-16 text-brand-green"></i>
                </div>
                <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Aprovados</h3>
                <div class="text-4xl font-bold tracking-tight text-brand-green">${mockStats.aprovados}</div>
                <div class="mt-4 flex items-center text-xs text-gray-500">
                    <span class="font-medium mr-1">91.5%</span> yield
                </div>
            </div>
            
            <div class="modern-card p-6 rounded-3xl bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border relative overflow-hidden group shadow-[0_0_15px_rgba(214,26,34,0.1)] dark:shadow-none">
                <div class="absolute inset-y-0 left-0 w-1 bg-brand-red"></div>
                <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <i data-lucide="alert-triangle" class="w-16 h-16 text-brand-red"></i>
                </div>
                <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Reprovados</h3>
                <div class="text-4xl font-bold tracking-tight text-brand-red">${mockStats.reprovados}</div>
                <div class="mt-4 flex items-center text-xs text-brand-red font-medium">
                    <i data-lucide="alert-circle" class="w-4 h-4 mr-1"></i> 3 ações requeridas
                </div>
            </div>
            
            <div class="modern-card p-6 rounded-3xl bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border relative overflow-hidden group">
                <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <i data-lucide="activity" class="w-16 h-16 text-brand-black dark:text-brand-white"></i>
                </div>
                <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Taxa de Defeito</h3>
                <div class="text-4xl font-bold tracking-tight">${mockStats.taxaDefeito}</div>
                <div class="mt-4 flex items-center text-xs text-brand-red">
                    <i data-lucide="trending-up" class="w-4 h-4 mr-1"></i> +0.4% variação
                </div>
            </div>
        </div>

        <!-- Live Feed Section -->
        <div class="rounded-3xl border border-light-border dark:border-dark-border overflow-hidden delay-150 fade-in-up bg-white dark:bg-[#1C1E22]">
            <div class="px-8 py-5 border-b border-light-border dark:border-dark-border flex justify-between items-center bg-gray-50/50 dark:bg-dark-bg/50 backdrop-blur-md">
                <div class="flex items-center">
                    <i data-lucide="radio" class="w-5 h-5 mr-3 text-brand-red animate-pulse"></i>
                    <h2 class="font-semibold text-lg tracking-tight">Feed ao Vivo</h2>
                </div>
                <button class="text-sm font-medium text-brand-red hover:opacity-80 transition-opacity flex items-center">
                    Ver todos <i data-lucide="arrow-right" class="w-4 h-4 ml-1"></i>
                </button>
            </div>
            
            <div class="divide-y divide-light-border dark:divide-dark-border">
                ${mockCapturas.map((cap, index) => `
                    <div class="p-5 flex flex-col sm:flex-row sm:items-center justify-between hover:bg-light-bg/50 dark:hover:bg-dark-bg/50 transition-colors group delay-${index * 75} fade-in-up">
                        <div class="flex items-center space-x-5 mb-4 sm:mb-0">
                            <div class="relative w-20 h-14 rounded-xl overflow-hidden shadow-sm">
                                <img src="${cap.img}" alt="thumbnail" class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500">
                                <div class="absolute inset-0 border border-black/10 dark:border-white/10 rounded-xl"></div>
                            </div>
                            <div>
                                <div class="font-semibold text-lg mb-0.5 flex items-center">
                                    ${cap.item}
                                    ${cap.status === 'Defeito' ? '<span class="ml-2 w-2 h-2 rounded-full bg-brand-red animate-pulse"></span>' : ''}
                                </div>
                                <div class="text-sm text-gray-500 dark:text-gray-400 flex items-center">
                                    <i data-lucide="camera" class="w-3.5 h-3.5 mr-1.5 opacity-70"></i> ${cap.vista} 
                                    <span class="mx-2 opacity-30">•</span> 
                                    <i data-lucide="clock" class="w-3.5 h-3.5 mr-1.5 opacity-70"></i> ${cap.timestamp}
                                </div>
                            </div>
                        </div>
                        
                        <div class="flex items-center justify-between sm:justify-end space-x-6 w-full sm:w-auto">
                            <div class="flex flex-col items-start sm:items-end">
                                <span class="text-sm font-bold px-3 py-1 rounded-lg ${cap.status === 'OK' ? 'bg-brand-green/10 text-brand-green' : (cap.status === 'Defeito' ? 'bg-brand-red/10 text-brand-red' : 'bg-gray-100 dark:bg-gray-800 text-gray-500')}">
                                    ${cap.status}
                                </span>
                                <span class="text-xs text-gray-400 mt-1">Confiança: ${cap.confianca}</span>
                            </div>
                            <button onclick="app.navigate('investigacao', '${cap.id}')" class="h-10 w-10 rounded-full bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border flex items-center justify-center text-gray-500 hover:text-white hover:bg-brand-black dark:hover:bg-brand-red hover:border-transparent transition-all group-hover:shadow-md" title="Investigar">
                                <i data-lucide="arrow-right" class="w-4 h-4 transform group-hover:translate-x-0.5 transition-transform"></i>
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    </div>
`;

const renderCapturas = () => `
    <div class="fade-in-up h-full flex flex-col space-y-6">
        <!-- Modern Filters Area -->
        <div class="p-4 sm:p-6 bg-light-bg dark:bg-dark-bg rounded-3xl border border-light-border dark:border-dark-border flex flex-col md:flex-row justify-between items-center gap-4">
            <div class="flex flex-wrap items-center gap-3 w-full md:w-auto">
                <div class="relative w-full sm:w-auto">
                    <i data-lucide="search" class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"></i>
                    <input type="text" placeholder="Buscar ID ou Item..." class="modern-input w-full sm:w-64 pl-10 pr-4 py-2.5 bg-white dark:bg-dark-card border border-light-border dark:border-dark-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-red/50 dark:focus:ring-brand-red/50 transition-shadow">
                </div>
                
                <select class="modern-input px-4 py-2.5 bg-white dark:bg-dark-card border border-light-border dark:border-dark-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-red/50 transition-shadow cursor-pointer">
                    <option>Todas as vistas</option>
                    <option>Topo</option>
                    <option>Lateral</option>
                </select>
                
                <select class="modern-input px-4 py-2.5 bg-white dark:bg-dark-card border border-light-border dark:border-dark-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-red/50 transition-shadow cursor-pointer">
                    <option>Status: Todos</option>
                    <option>OK</option>
                    <option>Defeito</option>
                </select>
            </div>
            
            <button class="w-full md:w-auto px-6 py-2.5 bg-brand-red hover:bg-red-700 text-white rounded-xl text-sm font-semibold transition-colors shadow-glow-red flex items-center justify-center">
                <i data-lucide="filter" class="w-4 h-4 mr-2"></i> Filtrar
            </button>
        </div>
        
        <!-- Grid of Images -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 overflow-y-auto pb-10">
            ${mockCapturas.map((cap, i) => `
                <div class="modern-card rounded-3xl overflow-hidden bg-white dark:bg-dark-bg border border-light-border dark:border-dark-border flex flex-col delay-${(i%4)*75} fade-in-up cursor-pointer group" onclick="app.navigate('investigacao', '${cap.id}')">
                    <div class="h-48 relative overflow-hidden">
                        <img src="${cap.img}" alt="${cap.id}" class="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-700">
                        <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        
                        <div class="absolute top-3 right-3 px-3 py-1.5 rounded-lg text-xs font-bold text-white shadow-md backdrop-blur-md ${cap.status === 'OK' ? 'bg-brand-green/90' : (cap.status === 'Defeito' ? 'bg-brand-red/90' : 'bg-gray-800/90')}">
                            ${cap.status}
                        </div>
                        
                        <div class="absolute bottom-3 left-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300 transform translate-y-2 group-hover:translate-y-0">
                            <span class="px-3 py-1.5 bg-white/20 backdrop-blur-md rounded-lg text-white text-xs font-medium border border-white/20">
                                Ver Detalhes
                            </span>
                        </div>
                    </div>
                    <div class="p-5 flex-1 flex flex-col relative z-10 bg-white dark:bg-[#1C1E22]">
                        <div class="flex justify-between items-start mb-1">
                            <h4 class="font-bold text-lg tracking-tight">${cap.item}</h4>
                            <span class="text-xs text-gray-500 font-medium bg-light-bg dark:bg-dark-bg px-2 py-1 rounded-md">${cap.timestamp}</span>
                        </div>
                        <div class="text-sm text-gray-500 flex-1 mb-4 flex items-center">
                            <i data-lucide="eye" class="w-3.5 h-3.5 mr-1.5"></i> Vista: ${cap.vista}
                        </div>
                        
                        <div class="flex justify-between items-center pt-4 border-t border-light-border dark:border-dark-border">
                            <div class="flex flex-col">
                                <span class="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Confiança</span>
                                <span class="text-sm font-semibold ${parseInt(cap.confianca) > 90 ? 'text-brand-green' : 'text-brand-red'}">${cap.confianca}</span>
                            </div>
                            <span class="text-xs font-mono bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border px-2.5 py-1.5 rounded-lg text-gray-600 dark:text-gray-300">
                                ${cap.id}
                            </span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    </div>
`;

const renderInvestigacao = (id) => {
    const cap = mockCapturas.find(c => c.id === id) || mockCapturas[2];
    
    return `
    <div class="fade-in-up max-w-6xl mx-auto pb-10">
        <!-- Breadcrumb / Back -->
        <div class="flex items-center justify-between mb-8">
            <button onclick="app.navigate('capturas')" class="flex items-center text-sm font-medium text-gray-500 hover:text-brand-red transition-colors group">
                <div class="w-8 h-8 rounded-full bg-light-bg dark:bg-dark-bg flex items-center justify-center mr-3 group-hover:bg-brand-red/10 transition-colors">
                    <i data-lucide="arrow-left" class="w-4 h-4"></i> 
                </div>
                Voltar para Galeria
            </button>
            <div class="px-4 py-1.5 bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border rounded-full text-xs font-mono font-medium tracking-wide">
                ${cap.id}
            </div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
            
            <!-- Imagem Principal (2/3 width) -->
            <div class="xl:col-span-2 space-y-6">
                <!-- Main Viewer -->
                <div class="modern-card p-2 rounded-3xl bg-white dark:bg-dark-bg border border-light-border dark:border-dark-border shadow-sm relative group">
                    <div class="absolute top-6 left-6 z-10 flex space-x-2">
                        <span class="px-3 py-1.5 bg-black/60 backdrop-blur-md rounded-lg text-white text-xs font-bold border border-white/10 shadow-lg">
                            ${cap.vista}
                        </span>
                    </div>
                    <div class="absolute top-6 right-6 z-10">
                        <button class="w-10 h-10 bg-black/60 backdrop-blur-md rounded-xl text-white flex items-center justify-center hover:bg-brand-red transition-colors border border-white/10 shadow-lg">
                            <i data-lucide="maximize" class="w-4 h-4"></i>
                        </button>
                    </div>
                    
                    <div class="relative rounded-2xl overflow-hidden bg-gray-100 dark:bg-black/50 aspect-video flex items-center justify-center">
                        <img src="${cap.img}" alt="Evidência" class="w-full h-full object-cover">
                        
                        <!-- Mock bounding box if defect -->
                        ${cap.status === 'Defeito' ? `
                            <div class="absolute border-2 border-brand-red bg-brand-red/10 rounded" style="top: 30%; left: 40%; width: 20%; height: 25%;">
                                <span class="absolute -top-6 left-0 bg-brand-red text-white text-[10px] font-bold px-2 py-0.5 rounded shadow">RISCO 89%</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <!-- Histórico da Peça Miniaturas -->
                <div class="p-6 rounded-3xl bg-white dark:bg-[#1C1E22] border border-light-border dark:border-dark-border shadow-sm">
                    <h3 class="font-semibold text-sm mb-4 text-gray-500 uppercase tracking-wider">Histórico de Vistas do Item (${cap.item})</h3>
                    <div class="flex space-x-4 overflow-x-auto pb-2 custom-scrollbar">
                        <div class="w-40 flex-shrink-0 rounded-2xl overflow-hidden cursor-pointer relative group border-2 border-brand-red shadow-glow-red">
                            <img src="${cap.img}" class="w-full h-28 object-cover opacity-90 group-hover:opacity-100 transition-opacity">
                            <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3 pt-8">
                                <div class="text-white text-xs font-bold">Topo</div>
                                <div class="text-brand-red text-[10px] font-bold">DEFEITO</div>
                            </div>
                        </div>
                        <div class="w-40 flex-shrink-0 rounded-2xl overflow-hidden cursor-pointer relative group border border-light-border dark:border-dark-border hover:border-brand-red/50 transition-colors opacity-60 hover:opacity-100">
                            <img src="https://placehold.co/400x300/1E2022/F9FBFD?text=Lateral" class="w-full h-28 object-cover">
                            <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3 pt-8">
                                <div class="text-white text-xs font-bold">Lateral</div>
                                <div class="text-brand-green text-[10px] font-bold">OK</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Metadados e Ações (1/3 width) -->
            <div class="space-y-6">
                <!-- Status Card -->
                <div class="p-8 rounded-3xl bg-white dark:bg-[#1C1E22] border border-light-border dark:border-dark-border shadow-sm flex flex-col items-center text-center">
                    <div class="w-20 h-20 rounded-full flex items-center justify-center mb-4 shadow-inner ${cap.status === 'OK' ? 'bg-brand-green/10 text-brand-green' : 'bg-brand-red/10 text-brand-red'}">
                        <i data-lucide="${cap.status === 'OK' ? 'check' : 'alert-triangle'}" class="w-10 h-10"></i>
                    </div>
                    <h2 class="text-2xl font-bold mb-1">${cap.status}</h2>
                    <p class="text-sm text-gray-500 mb-6">Classificação Automática</p>
                    
                    <div class="w-full bg-light-bg dark:bg-dark-bg rounded-2xl p-4 flex justify-between items-center border border-light-border dark:border-dark-border">
                        <span class="text-xs text-gray-500 font-semibold uppercase tracking-wider">Confiança</span>
                        <span class="text-lg font-bold">${cap.confianca}</span>
                    </div>
                </div>

                <!-- Data Card -->
                <div class="p-6 rounded-3xl bg-white dark:bg-[#1C1E22] border border-light-border dark:border-dark-border shadow-sm">
                    <h3 class="font-semibold text-sm mb-5 text-gray-500 uppercase tracking-wider border-b border-light-border dark:border-dark-border pb-3">Detalhes da Captura</h3>
                    
                    <div class="space-y-4">
                        <div class="flex justify-between items-center">
                            <div class="flex items-center text-gray-500 text-sm">
                                <i data-lucide="clock" class="w-4 h-4 mr-2"></i> Timestamp
                            </div>
                            <div class="font-mono text-sm">${cap.timestamp}</div>
                        </div>
                        <div class="flex justify-between items-center">
                            <div class="flex items-center text-gray-500 text-sm">
                                <i data-lucide="package" class="w-4 h-4 mr-2"></i> Lote
                            </div>
                            <div class="text-sm font-semibold">${cap.lote}</div>
                        </div>
                        <div class="flex justify-between items-center">
                            <div class="flex items-center text-gray-500 text-sm">
                                <i data-lucide="zap" class="w-4 h-4 mr-2"></i> Latência IA
                            </div>
                            <div class="text-sm">138ms</div>
                        </div>
                    </div>
                </div>

                <!-- Action Card (SITE-08) -->
                <div class="p-6 rounded-3xl bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border shadow-sm relative overflow-hidden">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-brand-red/5 rounded-full blur-3xl -mr-10 -mt-10"></div>
                    
                    <h3 class="font-semibold text-sm mb-5 text-gray-500 uppercase tracking-wider">Ação do Operador</h3>
                    
                    <div class="space-y-3 relative z-10">
                        <button class="w-full py-3.5 px-4 bg-white dark:bg-dark-card border-2 border-brand-green/30 text-brand-green rounded-2xl hover:bg-brand-green hover:text-white hover:border-brand-green transition-all shadow-sm text-sm font-bold flex justify-center items-center group">
                            <i data-lucide="check-circle" class="w-4 h-4 mr-2 group-hover:scale-110 transition-transform"></i> Forçar Aprovação
                        </button>
                        <button class="w-full py-3.5 px-4 bg-brand-red text-white rounded-2xl hover:bg-red-700 transition-all shadow-glow-red text-sm font-bold flex justify-center items-center group">
                            <i data-lucide="alert-triangle" class="w-4 h-4 mr-2 group-hover:scale-110 transition-transform"></i> Confirmar Defeito
                        </button>
                    </div>
                    
                    <div class="flex items-center justify-center text-xs text-gray-500 mt-5 relative z-10">
                        <i data-lucide="lock" class="w-3 h-3 mr-1.5 opacity-70"></i> Requer privilégio Admin
                    </div>
                </div>
            </div>
        </div>
    </div>
    `;
};

const renderQualidade = () => `
    <div class="fade-in-up space-y-6 h-full flex flex-col justify-center pb-20">
        <div class="max-w-md mx-auto text-center space-y-6">
            <div class="w-24 h-24 bg-light-bg dark:bg-dark-bg rounded-full flex items-center justify-center mx-auto border border-light-border dark:border-dark-border shadow-soft">
                <i data-lucide="pie-chart" class="w-10 h-10 text-brand-red"></i>
            </div>
            <h2 class="text-2xl font-bold tracking-tight">Módulo de Qualidade</h2>
            <p class="text-gray-500 dark:text-gray-400">
                Gráficos avançados, mapa de calor de defeitos e tendências estatísticas (SITE-10).
            </p>
            <div class="p-6 bg-light-bg dark:bg-dark-bg rounded-3xl border border-dashed border-gray-300 dark:border-gray-700">
                <p class="text-sm font-mono text-gray-500">Integração pendente com ECharts/Grafana</p>
            </div>
        </div>
    </div>
`;

const renderSaude = () => `
    <div class="fade-in-up max-w-5xl mx-auto space-y-8 pb-10">
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="modern-card p-6 rounded-3xl bg-white dark:bg-[#1C1E22] border border-light-border dark:border-dark-border shadow-sm relative overflow-hidden">
                <div class="absolute right-0 top-0 w-24 h-24 bg-brand-green/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
                <div class="flex items-center mb-4">
                    <div class="w-10 h-10 rounded-xl bg-brand-green/10 flex items-center justify-center mr-4">
                        <i data-lucide="activity" class="w-5 h-5 text-brand-green"></i>
                    </div>
                    <span class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Status Geral</span>
                </div>
                <div class="text-3xl font-bold mb-1">${mockHealth.status}</div>
                <div class="text-xs text-gray-500">Último ping: ${mockHealth.ultimoHeartbeat}</div>
            </div>
            
            <div class="modern-card p-6 rounded-3xl bg-white dark:bg-[#1C1E22] border border-light-border dark:border-dark-border shadow-sm relative overflow-hidden">
                <div class="flex items-center mb-4">
                    <div class="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center mr-4">
                        <i data-lucide="thermometer" class="w-5 h-5 text-orange-500"></i>
                    </div>
                    <span class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Temp SOC</span>
                </div>
                <div class="text-3xl font-bold mb-4">${mockHealth.temperatura}</div>
                <div class="w-full bg-light-bg dark:bg-dark-bg h-2 rounded-full overflow-hidden">
                    <div class="bg-gradient-to-r from-orange-400 to-red-500 h-full rounded-full w-[58%] relative">
                        <div class="absolute right-0 top-0 bottom-0 w-4 bg-white/20 animate-pulse"></div>
                    </div>
                </div>
            </div>

            <div class="modern-card p-6 rounded-3xl bg-white dark:bg-[#1C1E22] border border-light-border dark:border-dark-border shadow-sm relative overflow-hidden">
                <div class="flex items-center mb-4">
                    <div class="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center mr-4">
                        <i data-lucide="upload-cloud" class="w-5 h-5 text-blue-500"></i>
                    </div>
                    <span class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Sincronização</span>
                </div>
                <div class="text-3xl font-bold mb-1">${mockHealth.filaImagens} <span class="text-lg text-gray-500 font-normal">img</span></div>
                <div class="text-xs text-blue-500 font-medium">Na fila local aguardando push</div>
            </div>
        </div>

        <div class="p-8 rounded-3xl bg-white dark:bg-[#1C1E22] border border-light-border dark:border-dark-border shadow-sm">
            <h3 class="font-bold text-lg mb-6 flex items-center">
                <i data-lucide="server" class="w-5 h-5 mr-3 text-brand-red"></i> Topologia e Serviços
            </h3>
            <div class="space-y-4">
                <div class="group flex flex-col md:flex-row justify-between items-start md:items-center p-4 bg-light-bg dark:bg-dark-bg rounded-2xl border border-light-border dark:border-dark-border hover:border-gray-400 transition-colors">
                    <div class="flex items-center mb-3 md:mb-0">
                        <div class="w-12 h-12 rounded-xl bg-white dark:bg-dark-card border border-light-border dark:border-dark-border flex items-center justify-center mr-4 shadow-sm">
                            <i data-lucide="camera" class="w-5 h-5 text-gray-600 dark:text-gray-300"></i>
                        </div>
                        <div>
                            <div class="font-bold text-sm">Câmera GigE Vision</div>
                            <div class="text-xs text-gray-500 font-mono mt-0.5">IP: 192.168.1.100</div>
                        </div>
                    </div>
                    <div class="flex items-center px-3 py-1.5 bg-brand-green/10 text-brand-green rounded-lg text-xs font-bold">
                        <span class="w-2 h-2 rounded-full bg-brand-green mr-2 animate-pulse"></span> Conectado
                    </div>
                </div>
                
                <div class="group flex flex-col md:flex-row justify-between items-start md:items-center p-4 bg-light-bg dark:bg-dark-bg rounded-2xl border border-light-border dark:border-dark-border hover:border-gray-400 transition-colors">
                    <div class="flex items-center mb-3 md:mb-0">
                        <div class="w-12 h-12 rounded-xl bg-white dark:bg-dark-card border border-light-border dark:border-dark-border flex items-center justify-center mr-4 shadow-sm">
                            <i data-lucide="cpu" class="w-5 h-5 text-brand-red"></i>
                        </div>
                        <div>
                            <div class="font-bold text-sm">TensorFlow Lite (Inferência)</div>
                            <div class="text-xs text-gray-500 font-mono mt-0.5">PID: 8432 | Mod: resnet_v2.tflite</div>
                        </div>
                    </div>
                    <div class="flex items-center px-3 py-1.5 bg-brand-green/10 text-brand-green rounded-lg text-xs font-bold">
                        <span class="w-2 h-2 rounded-full bg-brand-green mr-2 animate-pulse"></span> Ativo
                    </div>
                </div>
                
                <div class="group flex flex-col md:flex-row justify-between items-start md:items-center p-4 bg-light-bg dark:bg-dark-bg rounded-2xl border border-light-border dark:border-dark-border hover:border-gray-400 transition-colors">
                    <div class="flex items-center mb-3 md:mb-0">
                        <div class="w-12 h-12 rounded-xl bg-white dark:bg-dark-card border border-light-border dark:border-dark-border flex items-center justify-center mr-4 shadow-sm">
                            <i data-lucide="database" class="w-5 h-5 text-blue-500"></i>
                        </div>
                        <div>
                            <div class="font-bold text-sm">SQLite (Storage Local)</div>
                            <div class="text-xs text-gray-500 font-mono mt-0.5">/var/opt/pnaat/db.sqlite3</div>
                        </div>
                    </div>
                    <div class="flex items-center px-3 py-1.5 bg-gray-200 dark:bg-gray-800 text-gray-600 dark:text-gray-300 rounded-lg text-xs font-bold">
                        <i data-lucide="hard-drive" class="w-3 h-3 mr-1.5"></i> 14.2 MB / 32 GB
                    </div>
                </div>
            </div>
        </div>
    </div>
`;

const renderLote = () => `
    <div class="fade-in-up max-w-5xl mx-auto pb-10">
        <div class="p-8 sm:p-10 rounded-3xl bg-white dark:bg-[#1C1E22] border border-light-border dark:border-dark-border shadow-sm mb-6 relative overflow-hidden">
            <!-- Dekor -->
            <div class="absolute -right-20 -top-20 w-64 h-64 bg-brand-red/5 rounded-full blur-3xl"></div>
            
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-10 relative z-10">
                <div class="mb-6 sm:mb-0">
                    <div class="flex items-center space-x-3 mb-2">
                        <h2 class="text-3xl font-bold tracking-tight">Relatório de Lote</h2>
                        <span class="px-3 py-1 bg-brand-red/10 text-brand-red text-sm font-bold rounded-xl border border-brand-red/20">#L2024-89</span>
                    </div>
                    <p class="text-gray-500 flex items-center text-sm">
                        <i data-lucide="calendar" class="w-4 h-4 mr-2"></i> Período: 14 Out 2024, 08:00 - Em andamento
                    </p>
                </div>
                <button class="w-full sm:w-auto px-6 py-3 bg-brand-black dark:bg-white text-white dark:text-black rounded-2xl text-sm font-bold shadow-md hover:scale-105 transition-transform flex items-center justify-center group">
                    <i data-lucide="download" class="w-4 h-4 mr-2 group-hover:animate-bounce"></i> Baixar CSV
                </button>
            </div>

            <div class="border border-light-border dark:border-dark-border rounded-2xl overflow-hidden shadow-sm relative z-10">
                <table class="w-full text-left text-sm">
                    <thead class="bg-light-bg dark:bg-dark-bg border-b border-light-border dark:border-dark-border">
                        <tr>
                            <th class="px-6 py-4 font-semibold text-gray-500 uppercase tracking-wider text-xs">Requisito (SITE-09)</th>
                            <th class="px-6 py-4 font-semibold text-gray-500 uppercase tracking-wider text-xs text-right">Status do Módulo</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-light-border dark:divide-dark-border bg-white dark:bg-[#1C1E22]">
                        <tr class="hover:bg-gray-50/50 dark:hover:bg-dark-bg/50 transition-colors">
                            <td class="px-6 py-5 font-medium flex items-center">
                                <i data-lucide="bar-chart-2" class="w-4 h-4 mr-3 text-gray-400"></i> Resumo Estatístico
                            </td>
                            <td class="px-6 py-5 text-right">
                                <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-brand-green/10 text-brand-green">
                                    <span class="w-1.5 h-1.5 rounded-full bg-brand-green mr-1.5"></span> Disponível
                                </span>
                            </td>
                        </tr>
                        <tr class="hover:bg-gray-50/50 dark:hover:bg-dark-bg/50 transition-colors">
                            <td class="px-6 py-5 font-medium flex items-center">
                                <i data-lucide="list-x" class="w-4 h-4 mr-3 text-gray-400"></i> Listagem de Exceções
                            </td>
                            <td class="px-6 py-5 text-right">
                                <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-brand-green/10 text-brand-green">
                                    <span class="w-1.5 h-1.5 rounded-full bg-brand-green mr-1.5"></span> Disponível
                                </span>
                            </td>
                        </tr>
                        <tr class="hover:bg-gray-50/50 dark:hover:bg-dark-bg/50 transition-colors">
                            <td class="px-6 py-5 font-medium flex items-center text-gray-400">
                                <i data-lucide="shield-check" class="w-4 h-4 mr-3"></i> Assinatura Digital
                            </td>
                            <td class="px-6 py-5 text-right">
                                <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-gray-100 dark:bg-gray-800 text-gray-500 border border-gray-200 dark:border-gray-700">
                                    Pendente Definição
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="mt-8 p-4 bg-blue-50 dark:bg-blue-900/10 rounded-2xl border border-blue-100 dark:border-blue-900/30 flex items-start">
                <i data-lucide="info" class="w-5 h-5 text-blue-500 mr-3 mt-0.5 flex-shrink-0"></i>
                <p class="text-sm text-blue-700 dark:text-blue-400 leading-relaxed">
                    Apenas dados consolidados localmente estão listados aqui. Para ver séries temporais agregadas ao nível corporativo (múltiplas linhas de produção), acesse o dashboard corporativo no Grafana.
                </p>
            </div>
        </div>
    </div>
`;
