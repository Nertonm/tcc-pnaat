// js/components.js

const renderOperacao = () => `
    <div class="fade-in space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div class="card p-6 rounded-xl shadow-sm">
                <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Produzido</h3>
                <div class="text-3xl font-bold">${mockStats.totalLote}</div>
            </div>
            <div class="card p-6 rounded-xl shadow-sm border-l-4 border-brand-green">
                <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Aprovados</h3>
                <div class="text-3xl font-bold text-brand-green">${mockStats.aprovados}</div>
            </div>
            <div class="card p-6 rounded-xl shadow-sm border-l-4 border-brand-red">
                <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Reprovados</h3>
                <div class="text-3xl font-bold text-brand-red">${mockStats.reprovados}</div>
            </div>
            <div class="card p-6 rounded-xl shadow-sm">
                <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Taxa de Defeito</h3>
                <div class="text-3xl font-bold">${mockStats.taxaDefeito}</div>
            </div>
        </div>

        <div class="card rounded-xl shadow-sm overflow-hidden mt-8 delay-100 fade-in">
            <div class="px-6 py-4 border-b border-gray-200 dark:border-dark-border flex justify-between items-center bg-gray-50 dark:bg-dark-card">
                <h2 class="font-semibold text-lg">Últimos Eventos (Tempo Real)</h2>
                <span class="text-xs px-2 py-1 bg-brand-green/10 text-brand-green rounded-md font-medium border border-brand-green/20">Live</span>
            </div>
            <div class="divide-y divide-gray-200 dark:divide-dark-border">
                ${mockCapturas.map(cap => `
                    <div class="p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-dark-border/50 transition-colors">
                        <div class="flex items-center space-x-4">
                            <div class="w-16 h-12 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden">
                                <img src="${cap.img}" alt="thumbnail" class="w-full h-full object-cover">
                            </div>
                            <div>
                                <div class="font-medium">${cap.item}</div>
                                <div class="text-xs text-gray-500 dark:text-gray-400">${cap.vista} • ${cap.timestamp}</div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-4">
                            <span class="text-sm font-medium ${cap.status === 'OK' ? 'text-brand-green' : (cap.status === 'Defeito' ? 'text-brand-red' : 'text-gray-500')}">
                                ${cap.status}
                            </span>
                            <button onclick="app.navigate('investigacao', '${cap.id}')" class="p-2 text-gray-400 hover:text-brand-black dark:hover:text-brand-white transition-colors" title="Investigar">
                                <i data-lucide="chevron-right" class="w-5 h-5"></i>
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    </div>
`;

const renderCapturas = () => `
    <div class="fade-in h-full flex flex-col">
        <div class="flex justify-between items-center mb-6">
            <div class="flex space-x-2">
                <input type="text" placeholder="Filtrar por item..." class="px-3 py-2 border border-gray-300 dark:border-dark-border rounded-md bg-white dark:bg-dark-card focus:outline-none focus:ring-2 focus:ring-brand-black dark:focus:ring-brand-white text-sm">
                <select class="px-3 py-2 border border-gray-300 dark:border-dark-border rounded-md bg-white dark:bg-dark-card text-sm">
                    <option>Todas as vistas</option>
                    <option>Topo</option>
                    <option>Lateral</option>
                </select>
                <select class="px-3 py-2 border border-gray-300 dark:border-dark-border rounded-md bg-white dark:bg-dark-card text-sm">
                    <option>Todos os Status</option>
                    <option>OK</option>
                    <option>Defeito</option>
                </select>
            </div>
            <button class="px-4 py-2 bg-brand-black dark:bg-brand-white text-brand-white dark:text-brand-black rounded-md text-sm font-medium hover:opacity-90 transition-opacity">
                Aplicar Filtros
            </button>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 overflow-y-auto pb-8">
            ${mockCapturas.map((cap, i) => `
                <div class="card rounded-xl overflow-hidden shadow-sm flex flex-col delay-${(i%3)*100} fade-in cursor-pointer hover:border-gray-400 dark:hover:border-gray-500" onclick="app.navigate('investigacao', '${cap.id}')">
                    <div class="h-48 bg-gray-200 dark:bg-gray-800 relative">
                        <img src="${cap.img}" alt="${cap.id}" class="w-full h-full object-cover">
                        <div class="absolute top-2 right-2 px-2 py-1 rounded text-xs font-bold text-white ${cap.status === 'OK' ? 'bg-brand-green' : (cap.status === 'Defeito' ? 'bg-brand-red' : 'bg-gray-600')}">
                            ${cap.status}
                        </div>
                    </div>
                    <div class="p-4 flex-1 flex flex-col">
                        <div class="flex justify-between items-start mb-2">
                            <h4 class="font-bold text-lg">${cap.item}</h4>
                            <span class="text-xs text-gray-500">${cap.timestamp}</span>
                        </div>
                        <div class="text-sm text-gray-600 dark:text-gray-400 flex-1">
                            Vista: ${cap.vista}
                        </div>
                        <div class="mt-4 pt-3 border-t border-gray-100 dark:border-dark-border flex justify-between items-center">
                            <span class="text-xs text-gray-500">Confiança: ${cap.confianca}</span>
                            <span class="text-xs font-mono bg-gray-100 dark:bg-dark-bg px-2 py-1 rounded">${cap.id}</span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    </div>
`;

const renderInvestigacao = (id) => {
    const cap = mockCapturas.find(c => c.id === id) || mockCapturas[2]; // Default to a defect if none selected
    
    return `
    <div class="fade-in max-w-5xl mx-auto">
        <button onclick="app.navigate('capturas')" class="flex items-center text-sm text-gray-500 hover:text-brand-black dark:hover:text-brand-white mb-6 transition-colors">
            <i data-lucide="arrow-left" class="w-4 h-4 mr-1"></i> Voltar para Capturas
        </button>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- Imagem Principal -->
            <div class="lg:col-span-2 space-y-4">
                <div class="card rounded-xl overflow-hidden p-2">
                    <div class="relative rounded-lg overflow-hidden border border-gray-200 dark:border-dark-border group">
                        <img src="${cap.img}" alt="Evidência" class="w-full h-auto">
                        <div class="absolute inset-0 bg-brand-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                            <button class="bg-brand-white text-brand-black px-4 py-2 rounded-md font-medium shadow-lg flex items-center">
                                <i data-lucide="zoom-in" class="w-4 h-4 mr-2"></i> Ampliar Detalhe
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="card rounded-xl p-4">
                    <h3 class="font-medium mb-3 text-sm">Histórico da Peça (${cap.item})</h3>
                    <div class="flex space-x-4 overflow-x-auto pb-2">
                        <div class="w-32 flex-shrink-0 border-2 border-brand-red rounded overflow-hidden">
                            <img src="${cap.img}" class="w-full h-24 object-cover">
                            <div class="text-center text-xs py-1 font-medium bg-gray-50 dark:bg-dark-bg">Topo</div>
                        </div>
                        <div class="w-32 flex-shrink-0 border border-gray-200 dark:border-dark-border rounded overflow-hidden opacity-60">
                            <img src="https://placehold.co/400x300/1E2022/F9FBFD?text=Lateral" class="w-full h-24 object-cover">
                            <div class="text-center text-xs py-1 bg-gray-50 dark:bg-dark-bg">Lateral</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Metadados e Ações -->
            <div class="space-y-6">
                <div class="card rounded-xl p-6">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-xl font-bold">${cap.id}</h2>
                        <span class="px-3 py-1 text-sm font-bold rounded-md ${cap.status === 'OK' ? 'bg-brand-green/20 text-brand-green' : 'bg-brand-red/20 text-brand-red'}">
                            ${cap.status}
                        </span>
                    </div>

                    <div class="space-y-4 mb-8">
                        <div>
                            <div class="text-xs text-gray-500 mb-1">Timestamp Original</div>
                            <div class="font-mono text-sm">${cap.timestamp} (UTC-3)</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500 mb-1">Lote</div>
                            <div class="text-sm">${cap.lote}</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500 mb-1">Confiança do Modelo</div>
                            <div class="text-sm font-medium">${cap.confianca}</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500 mb-1">Latência de Processamento</div>
                            <div class="text-sm">138ms</div>
                        </div>
                    </div>

                    <hr class="border-gray-200 dark:border-dark-border mb-6">

                    <div class="space-y-4">
                        <h3 class="font-medium text-sm">Auditoria e Correção (SITE-08)</h3>
                        <div class="space-y-2">
                            <button class="w-full py-2 px-4 border border-brand-green text-brand-green rounded-md hover:bg-brand-green hover:text-white transition-colors text-sm font-medium text-center">
                                Forçar Aprovação (Falso Positivo)
                            </button>
                            <button class="w-full py-2 px-4 border border-brand-red text-brand-red rounded-md hover:bg-brand-red hover:text-white transition-colors text-sm font-medium text-center">
                                Confirmar Defeito (Verdadeiro Positivo)
                            </button>
                        </div>
                        <p class="text-xs text-gray-500 text-center mt-2">Ação requer autenticação de supervisor</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `;
};

const renderQualidade = () => `
    <div class="fade-in space-y-6">
        <div class="card p-8 rounded-xl flex items-center justify-center border-dashed border-2">
            <div class="text-center opacity-60">
                <i data-lucide="bar-chart-2" class="w-12 h-12 mx-auto mb-4"></i>
                <h3 class="text-lg font-medium">Dashboard de Qualidade</h3>
                <p class="text-sm mt-2 max-w-md">Gráficos de defeitos por código/severidade, registros parciais e tendências serão renderizados aqui utilizando bibliotecas como Chart.js ou via integração com Grafana (SITE-10).</p>
            </div>
        </div>
    </div>
`;

const renderSaude = () => `
    <div class="fade-in max-w-4xl mx-auto space-y-6">
        <h2 class="text-lg font-semibold mb-4">Métricas de Saúde da Borda (Raspberry Pi)</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div class="card p-5 rounded-xl border-t-4 border-brand-green">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-sm text-gray-500">Status Geral</span>
                    <i data-lucide="wifi" class="w-4 h-4 text-brand-green"></i>
                </div>
                <div class="text-2xl font-bold">${mockHealth.status}</div>
                <div class="text-xs text-gray-500 mt-2">Último ping: ${mockHealth.ultimoHeartbeat}</div>
            </div>
            
            <div class="card p-5 rounded-xl">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-sm text-gray-500">Temperatura SOC</span>
                    <i data-lucide="thermometer" class="w-4 h-4 text-orange-500"></i>
                </div>
                <div class="text-2xl font-bold">${mockHealth.temperatura}</div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 h-1.5 rounded-full mt-3 overflow-hidden">
                    <div class="bg-orange-500 h-full rounded-full" style="width: 58%"></div>
                </div>
            </div>

            <div class="card p-5 rounded-xl">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-sm text-gray-500">Fila de Sincronização</span>
                    <i data-lucide="upload-cloud" class="w-4 h-4 text-blue-500"></i>
                </div>
                <div class="text-2xl font-bold">${mockHealth.filaImagens} img</div>
                <div class="text-xs text-gray-500 mt-2">Sincronizando com backend local</div>
            </div>
        </div>

        <div class="card p-6 rounded-xl">
            <h3 class="font-medium mb-4 border-b border-gray-100 dark:border-dark-border pb-2">Topologia e Serviços</h3>
            <div class="space-y-4">
                <div class="flex justify-between items-center p-3 bg-gray-50 dark:bg-dark-bg rounded border border-gray-200 dark:border-dark-border">
                    <div class="flex items-center">
                        <div class="w-2 h-2 rounded-full bg-brand-green mr-3"></div>
                        <span class="font-medium text-sm">Câmera GigE</span>
                    </div>
                    <span class="text-xs text-gray-500 font-mono">192.168.1.100</span>
                </div>
                <div class="flex justify-between items-center p-3 bg-gray-50 dark:bg-dark-bg rounded border border-gray-200 dark:border-dark-border">
                    <div class="flex items-center">
                        <div class="w-2 h-2 rounded-full bg-brand-green mr-3"></div>
                        <span class="font-medium text-sm">Serviço de Inferência (TensorFlow Lite)</span>
                    </div>
                    <span class="text-xs text-brand-green">Rodando (PID 8432)</span>
                </div>
                <div class="flex justify-between items-center p-3 bg-gray-50 dark:bg-dark-bg rounded border border-gray-200 dark:border-dark-border">
                    <div class="flex items-center">
                        <div class="w-2 h-2 rounded-full bg-brand-green mr-3"></div>
                        <span class="font-medium text-sm">Banco de Dados Local (SQLite)</span>
                    </div>
                    <span class="text-xs text-gray-500">14.2 MB / 32 GB</span>
                </div>
            </div>
        </div>
    </div>
`;

const renderLote = () => `
    <div class="fade-in max-w-4xl mx-auto">
        <div class="card p-8 rounded-xl shadow-sm mb-6">
            <div class="flex justify-between items-start mb-8">
                <div>
                    <h2 class="text-2xl font-bold mb-1">Relatório de Lote: #L2024-89</h2>
                    <p class="text-gray-500 text-sm">Período: 14 Out 2024, 08:00 - Em andamento</p>
                </div>
                <button class="px-4 py-2 bg-brand-black dark:bg-brand-white text-brand-white dark:text-brand-black rounded-md text-sm font-medium flex items-center hover:opacity-90">
                    <i data-lucide="download" class="w-4 h-4 mr-2"></i> Exportar CSV
                </button>
            </div>

            <div class="border border-gray-200 dark:border-dark-border rounded-lg overflow-hidden">
                <table class="w-full text-left text-sm">
                    <thead class="bg-gray-50 dark:bg-dark-bg border-b border-gray-200 dark:border-dark-border">
                        <tr>
                            <th class="px-4 py-3 font-medium">Requisito SITE-09</th>
                            <th class="px-4 py-3 font-medium">Status</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-dark-border">
                        <tr>
                            <td class="px-4 py-3">Resumo Estatístico</td>
                            <td class="px-4 py-3 text-brand-green">Disponível</td>
                        </tr>
                        <tr>
                            <td class="px-4 py-3">Listagem de Exceções (Defeitos)</td>
                            <td class="px-4 py-3 text-brand-green">Disponível</td>
                        </tr>
                        <tr>
                            <td class="px-4 py-3">Assinatura Digital de Auditoria</td>
                            <td class="px-4 py-3 text-gray-400">Pendente Definição</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <p class="text-xs text-gray-500 mt-6 italic">* Apenas dados consolidados locais. Para séries temporais agregadas corporativas, consulte o Grafana corporativo.</p>
        </div>
    </div>
`;
