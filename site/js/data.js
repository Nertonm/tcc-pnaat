const mockCapturas = [
    {
        id: 'CAP-1042',
        item: 'ITM-902',
        vista: 'Topo',
        lote: 'L2024-89',
        timestamp: '14:32:01',
        status: 'OK',
        confianca: '98%',
        latencia: '132ms',
        qualidade: 'Completo',
        img: 'https://placehold.co/800x600/171A1D/F9FBFD?text=Vista+Topo+OK'
    },

    {
        id: 'CAP-1043',
        item: 'ITM-902',
        vista: 'Lateral',
        lote: 'L2024-89',
        timestamp: '14:32:02',
        status: 'OK',
        confianca: '95%',
        latencia: '141ms',
        qualidade: 'Completo',
        img: 'https://placehold.co/800x600/252A30/F9FBFD?text=Vista+Lateral+OK'
    },

    {
        id: 'CAP-1044',
        item: 'ITM-903',
        vista: 'Topo',
        lote: 'L2024-89',
        timestamp: '14:32:15',
        status: 'Defeito',
        confianca: '89%',
        latencia: '138ms',
        qualidade: 'Completo',
        img: 'https://placehold.co/800x600/D61A22/F9FBFD?text=Defeito+Risco'
    },

    {
        id: 'CAP-1045',
        item: 'ITM-903',
        vista: 'Lateral',
        lote: 'L2024-89',
        timestamp: '14:32:16',
        status: 'OK',
        confianca: '91%',
        latencia: '145ms',
        qualidade: 'Completo',
        img: 'https://placehold.co/800x600/171A1D/F9FBFD?text=Vista+Lateral+OK'
    },

    {
        id: 'CAP-1046',
        item: 'ITM-904',
        vista: 'Topo',
        lote: 'L2024-89',
        timestamp: '14:32:28',
        status: 'Pendente',
        confianca: '--',
        latencia: '--',
        qualidade: 'Processando',
        img: 'https://placehold.co/800x600/3A4048/F9FBFD?text=Aguardando+Processamento'
    }
];

const mockStats = {
    totalLote: 450,
    aprovados: 412,
    reprovados: 38,
    taxaDefeito: '8.4%',
    latenciaMedia: '142ms',

    producaoAnterior: 401,

    tendencia: [
        48,
        54,
        51,
        63,
        69,
        74,
        79,
        88
    ]
};

const mockHealth = {
    status: 'Online',
    cpu: '45%',
    memoria: '1.2 GB',
    temperatura: '58°C',
    armazenamento: '14.2 MB',
    armazenamentoTotal: '32 GB',
    filaImagens: 2,
    latencia: '12ms',
    ultimoHeartbeat: 'Agora mesmo'
};

const mockServices = [
    {
        name: 'Câmera GigE Vision',
        detail: '192.168.1.100',
        icon: 'camera',
        status: 'Conectado',
        state: 'ok'
    },

    {
        name: 'TensorFlow Lite',
        detail: 'resnet_v2.tflite',
        icon: 'cpu',
        status: 'Ativo',
        state: 'ok'
    },

    {
        name: 'SQLite',
        detail: '/var/opt/pnaat/db.sqlite3',
        icon: 'database',
        status: 'Disponível',
        state: 'neutral'
    },

    {
        name: 'Fila de imagens',
        detail: '2 imagens aguardando processamento',
        icon: 'images',
        status: 'Normal',
        state: 'warning'
    }
];