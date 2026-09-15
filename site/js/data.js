// js/data.js
// Mock data para a demonstração (Fixtures)

const mockCapturas = [
    { id: 'CAP-1042', item: 'ITM-902', vista: 'Topo', lote: 'L2024-89', timestamp: '14:32:01', status: 'OK', confianca: '98%', img: 'https://placehold.co/400x300/1E2022/F9FBFD?text=Vista+Topo+OK' },
    { id: 'CAP-1043', item: 'ITM-902', vista: 'Lateral', lote: 'L2024-89', timestamp: '14:32:02', status: 'OK', confianca: '95%', img: 'https://placehold.co/400x300/1E2022/F9FBFD?text=Vista+Lateral+OK' },
    { id: 'CAP-1044', item: 'ITM-903', vista: 'Topo', lote: 'L2024-89', timestamp: '14:32:15', status: 'Defeito', confianca: '89%', img: 'https://placehold.co/400x300/D61A22/F9FBFD?text=Defeito+Risco' },
    { id: 'CAP-1045', item: 'ITM-903', vista: 'Lateral', lote: 'L2024-89', timestamp: '14:32:16', status: 'OK', confianca: '91%', img: 'https://placehold.co/400x300/1E2022/F9FBFD?text=Vista+Lateral+OK' },
    { id: 'CAP-1046', item: 'ITM-904', vista: 'Topo', lote: 'L2024-89', timestamp: '14:32:28', status: 'Pendente', confianca: '--', img: 'https://placehold.co/400x300/2A2C30/F9FBFD?text=Aguardando+Processamento' }
];

const mockStats = {
    totalLote: 450,
    aprovados: 412,
    reprovados: 38,
    taxaDefeito: '8.4%',
    latenciaMedia: '142ms'
};

const mockHealth = {
    status: 'Online',
    cpu: '45%',
    memoria: '1.2 GB',
    temperatura: '58°C',
    filaImagens: 2,
    ultimoHeartbeat: 'Agora mesmo'
};
