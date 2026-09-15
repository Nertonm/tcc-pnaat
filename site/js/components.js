const statusBadge = (status, rotulo) => {
    const config = {
        OK: {
            className: 'status-badge-ok',
            icon: 'check-circle-2'
        },

        Defeito: {
            className: 'status-badge-danger',
            icon: 'triangle-alert'
        },

        Pendente: {
            className: 'status-badge-pending',
            icon: 'clock-3'
        }
    };

    const current =
        config[status] || config.Pendente;

    return `
        <span class="status-badge ${current.className}">
            <i
                data-lucide="${current.icon}"
                class="mr-1.5 h-3.5 w-3.5"
            ></i>

            ${rotulo ? `${rotulo} ` : ''}${status}
        </span>
    `;
};


const renderMetricCard = ({
    title,
    value,
    subtitle,
    icon,
    type = 'default',
    className = ''
}) => {
    const iconClass =
        type === 'danger'
            ? 'metric-icon metric-icon-danger'
            : type === 'success'
                ? 'metric-icon metric-icon-success'
                : 'metric-icon';

    return `
        <div class="metric-card ${className}">
            <div class="flex items-start justify-between">

                <div>
                    <p
                        class="
                            text-[11px]
                            font-semibold
                            uppercase
                            tracking-[.12em]

                            text-gray-400
                        "
                    >
                        ${title}
                    </p>

                    <div
                        class="
                            mt-3

                            text-3xl
                            font-bold
                            tracking-tight

                            sm:text-[34px]
                        "
                    >
                        ${value}
                    </div>
                </div>

                <div class="${iconClass}">
                    <i
                        data-lucide="${icon}"
                        class="h-5 w-5"
                    ></i>
                </div>

            </div>

            <div
                class="
                    mt-5

                    text-xs

                    text-gray-500
                    dark:text-gray-400
                "
            >
                ${subtitle}
            </div>
        </div>
    `;
};


const renderOperacao = () => {
    /*
     * A conta so existe com numero: com a API fora as globais tem valor DECLARADO ('--'), e somar
     * placeholder rendia "NaN%" e "--------" na tela.
     */
    const numerico =
        typeof mockStats.aprovados === 'number' && typeof mockStats.reprovados === 'number';

    const total =
        numerico
            ? mockStats.aprovados + mockStats.reprovados
            : null;

    const approvedPercentage =
        total
            ? (mockStats.aprovados / total * 100).toFixed(1)
            : '--';

    return `
        <div class="fade-in-up space-y-6">

            <!-- KPI GRID -->
            <section
                class="
                    grid

                    grid-cols-1
                    gap-4

                    sm:grid-cols-2
                    xl:grid-cols-4
                "
            >

                ${renderMetricCard({
                    title: 'Total produzido',
                    value: mockStats.totalLote,
                    icon: 'layers-3',
                    subtitle:
                        mockStats.producaoAnterior === '--'
                        || mockStats.producaoAnterior === undefined
                            ? `<span class="text-gray-400">
                                   sem serie historica no registro
                               </span>`
                            : `
                        <span
                            class="
                                inline-flex
                                items-center

                                font-semibold
                                text-brand-green
                            "
                        >
                            <i
                                data-lucide="trending-up"
                                class="mr-1 h-3.5 w-3.5"
                            ></i>

                            ${mockStats.producaoAnterior}
                        </span>

                        <span class="ml-1">
                            vs. periodo anterior
                        </span>
                    `
                })}

                ${renderMetricCard({
                    title: 'Aprovados',
                    value: mockStats.aprovados,
                    icon: 'circle-check',
                    type: 'success',
                    subtitle: `
                        <span class="font-semibold">
                            ${approvedPercentage}%
                        </span>

                        dos itens decididos (${mockStats.inconclusivos ?? '--'} inconclusivo(s)
                        fora da conta)
                    `
                })}

                ${renderMetricCard({
                    title: 'Defeitos',
                    value: mockStats.reprovados,
                    icon: 'triangle-alert',
                    type: 'danger',
                    subtitle: `
                        <span
                            class="
                                font-semibold
                                text-brand-red
                            "
                        >
                            ${mockStats.inconclusivos ?? '--'} evento(s)
                        </span>

                        aguardam revisão
                    `
                })}

                ${renderMetricCard({
                    title: 'Taxa de defeito',
                    value: mockStats.taxaDefeito,
                    icon: 'activity',
                    subtitle: `
                        Latência média

                        <span
                            class="
                                ml-1
                                font-semibold
                            "
                        >
                            ${mockStats.latenciaMedia}
                        </span>
                    `
                })}

            </section>


            <!-- MAIN GRID -->
            <section
                class="
                    grid

                    grid-cols-1
                    gap-6

                    xl:grid-cols-[minmax(0,1.75fr)_minmax(300px,.75fr)]
                "
            >

                <!-- LIVE FEED -->
                <div class="surface-card overflow-hidden">

                    <div
                        class="
                            flex

                            items-center
                            justify-between

                            border-b
                            border-light-border
                            dark:border-dark-border

                            px-5
                            py-4

                            sm:px-6
                        "
                    >

                        <div>
                            <div class="flex items-center">
                                <span class="status-dot status-danger mr-2.5"></span>

                                <h2
                                    class="
                                        text-base
                                        font-bold
                                    "
                                >
                                    Feed ao vivo
                                </h2>
                            </div>

                            <p
                                class="
                                    mt-1

                                    text-xs

                                    text-gray-400
                                "
                            >
                                Últimas capturas recebidas pela bancada
                            </p>
                        </div>

                        <button
                            onclick="app.navigate('capturas')"
                            class="
                                secondary-button
                                !min-h-0

                                !px-3
                                !py-2
                            "
                        >
                            Ver histórico

                            <i
                                data-lucide="arrow-up-right"
                                class="ml-2 h-4 w-4"
                            ></i>
                        </button>

                    </div>

                    <div class="p-2 sm:p-3">

                        ${mockCapturas
                            .slice(0, 5)
                            .map(cap => `
                                <div
                                    onclick="app.navigate('investigacao', '${cap.id}')"

                                    class="feed-row group"
                                >

                                    <div
                                        class="
                                            flex
                                            min-w-0
                                            items-center
                                            gap-4
                                        "
                                    >

                                        <div class="feed-thumb">

                                            <img
                                                src="${cap.img}"
                                                alt="${cap.item}"
                                            >

                                        </div>

                                        <div class="min-w-0">

                                            <div
                                                class="
                                                    flex
                                                    items-center
                                                    gap-2
                                                "
                                            >
                                                <h3
                                                    class="
                                                        truncate

                                                        text-sm
                                                        font-bold
                                                    "
                                                >
                                                    ${cap.item}
                                                </h3>

                                                <span
                                                    class="
                                                        hidden

                                                        text-[11px]
                                                        text-gray-400

                                                        sm:inline
                                                    "
                                                >
                                                    ${cap.id}
                                                </span>
                                            </div>

                                            <div
                                                class="
                                                    mt-1

                                                    flex
                                                    flex-wrap
                                                    items-center
                                                    gap-x-2

                                                    text-xs

                                                    text-gray-400
                                                "
                                            >
                                                <span>
                                                    ${cap.vista}
                                                </span>

                                                <span>
                                                    •
                                                </span>

                                                <span>
                                                    ${cap.timestamp}
                                                </span>

                                                <span
                                                    class="
                                                        hidden
                                                        sm:inline
                                                    "
                                                >
                                                    •
                                                </span>

                                                <span
                                                    class="
                                                        hidden
                                                        sm:inline
                                                    "
                                                >
                                                    Confiança ${cap.confianca}
                                                </span>
                                            </div>

                                        </div>

                                    </div>


                                    <div
                                        class="
                                            flex
                                            items-center
                                            gap-3
                                        "
                                    >
                                        ${statusBadge(cap.status)}

                                        <span
                                            class="
                                                flex

                                                h-8
                                                w-8

                                                items-center
                                                justify-center

                                                rounded-full

                                                text-gray-400

                                                opacity-0

                                                transition-all

                                                group-hover:bg-white
                                                group-hover:text-brand-red
                                                group-hover:opacity-100

                                                dark:group-hover:bg-dark-raised
                                            "
                                        >
                                            <i
                                                data-lucide="arrow-right"
                                                class="h-4 w-4"
                                            ></i>
                                        </span>
                                    </div>

                                </div>
                            `)
                            .join('')}

                    </div>

                </div>


                <!-- SIDE COLUMN -->
                <div class="space-y-6">

                    <!-- PI -->
                    <div class="surface-card p-5 sm:p-6">

                        <div
                            class="
                                flex

                                items-start
                                justify-between
                            "
                        >

                            <div>
                                <p
                                    class="
                                        text-[11px]
                                        font-semibold
                                        uppercase
                                        tracking-[.12em]

                                        text-gray-400
                                    "
                                >
                                    Saúde da Pi
                                </p>

                                <div
                                    class="
                                        mt-3

                                        flex
                                        items-center
                                    "
                                >
                                    <span class="status-dot status-success mr-2"></span>

                                    <span
                                        class="
                                            text-xl
                                            font-bold
                                        "
                                    >
                                        ${mockHealth.status}
                                    </span>
                                </div>
                            </div>

                            <div class="metric-icon metric-icon-success">
                                <i
                                    data-lucide="cpu"
                                    class="h-5 w-5"
                                ></i>
                            </div>

                        </div>


                        <div
                            class="
                                mt-6

                                grid
                                grid-cols-2
                                gap-3
                            "
                        >

                            <div
                                class="
                                    rounded-2xl

                                    bg-light-bg
                                    dark:bg-dark-bg

                                    p-4
                                "
                            >
                                <div
                                    class="
                                        text-[10px]
                                        font-semibold
                                        uppercase
                                        tracking-wider

                                        text-gray-400
                                    "
                                >
                                    Temperatura
                                </div>

                                <div
                                    class="
                                        mt-2

                                        text-lg
                                        font-bold
                                    "
                                >
                                    ${mockHealth.temperatura}
                                </div>
                            </div>

                            <div
                                class="
                                    rounded-2xl

                                    bg-light-bg
                                    dark:bg-dark-bg

                                    p-4
                                "
                            >
                                <div
                                    class="
                                        text-[10px]
                                        font-semibold
                                        uppercase
                                        tracking-wider

                                        text-gray-400
                                    "
                                >
                                    Latência
                                </div>

                                <div
                                    class="
                                        mt-2

                                        text-lg
                                        font-bold
                                    "
                                >
                                    ${mockHealth.latencia}
                                </div>
                            </div>

                            <div
                                class="
                                    rounded-2xl

                                    bg-light-bg
                                    dark:bg-dark-bg

                                    p-4
                                "
                            >
                                <div
                                    class="
                                        text-[10px]
                                        font-semibold
                                        uppercase
                                        tracking-wider

                                        text-gray-400
                                    "
                                >
                                    CPU
                                </div>

                                <div
                                    class="
                                        mt-2

                                        text-lg
                                        font-bold
                                    "
                                >
                                    ${mockHealth.cpu}
                                </div>
                            </div>

                            <div
                                class="
                                    rounded-2xl

                                    bg-light-bg
                                    dark:bg-dark-bg

                                    p-4
                                "
                            >
                                <div
                                    class="
                                        text-[10px]
                                        font-semibold
                                        uppercase
                                        tracking-wider

                                        text-gray-400
                                    "
                                >
                                    Fila
                                </div>

                                <div
                                    class="
                                        mt-2

                                        text-lg
                                        font-bold
                                    "
                                >
                                    ${mockHealth.filaImagens}

                                    <span
                                        class="
                                            text-xs
                                            font-normal
                                            text-gray-400
                                        "
                                    >
                                        img
                                    </span>
                                </div>
                            </div>

                        </div>


                        <button
                            onclick="app.navigate('saude')"

                            class="
                                secondary-button

                                mt-5
                                w-full
                            "
                        >
                            Ver detalhes

                            <i
                                data-lucide="arrow-right"
                                class="ml-2 h-4 w-4"
                            ></i>
                        </button>

                    </div>


                    <!-- LOTE -->
                    <div
                        class="
                            surface-card

                            relative
                            overflow-hidden

                            p-5
                            sm:p-6
                        "
                    >

                        <div
                            class="
                                pointer-events-none

                                absolute

                                -right-10
                                -top-10

                                h-32
                                w-32

                                rounded-full

                                bg-brand-red/5

                                blur-2xl
                            "
                        ></div>

                        <div class="relative">

                            <div
                                class="
                                    flex
                                    items-center
                                    justify-between
                                "
                            >
                                <div>
                                    <p
                                        class="
                                            text-[11px]
                                            font-semibold
                                            uppercase
                                            tracking-[.12em]

                                            text-gray-400
                                        "
                                    >
                                        Lote atual
                                    </p>

                                    <div
                                        class="
                                            mt-2

                                            text-xl
                                            font-bold
                                        "
                                    >
                                        ${(mockCapturas[0] && mockCapturas[0].lote) || '(sem lote)'}
                                    </div>
                                </div>

                                <i
                                    data-lucide="package-open"

                                    class="
                                        h-6
                                        w-6

                                        text-brand-red
                                    "
                                ></i>
                            </div>


                            <div class="mt-5">

                                <div
                                    class="
                                        mb-2

                                        flex

                                        items-center
                                        justify-between

                                        text-xs
                                    "
                                >
                                    <span class="text-gray-400">
                                        Lotes no registro
                                    </span>

                                    <span class="font-semibold">
                                        ${(mockLotes || []).length
                                            ? `${(mockLotes || []).reduce((soma, lote) => soma + (lote.itens || 0), 0)} itens em ${(mockLotes || []).length} lote(s)`
                                            : 'nenhum lote no registro'}
                                    </span>
                                </div>

                                <p class="text-xs text-gray-400">
                                    Barra de progresso removida: o registro nao declara meta
                                    nem denominador de lote para medir avanco.
                                </p>

                            </div>


                            <button
                                onclick="app.navigate('lote')"

                                class="
                                    secondary-button

                                    mt-5
                                    w-full
                                "
                            >
                                Abrir relatório

                                <i
                                    data-lucide="file-chart-column"
                                    class="ml-2 h-4 w-4"
                                ></i>
                            </button>

                        </div>

                    </div>

                </div>

            </section>

        </div>
    `;
};


const renderCapturas = () => `
    <div class="fade-in-up space-y-6">

        <!-- FILTER TOOLBAR -->
        <section
            class="
                surface-card

                flex
                flex-col

                gap-4

                p-4

                lg:flex-row
                lg:items-center
                lg:justify-between
            "
        >

            <div
                class="
                    flex
                    flex-1
                    flex-col

                    gap-3

                    sm:flex-row
                "
            >

                <div
                    class="
                        relative

                        flex-1

                        sm:max-w-sm
                    "
                >
                    <i
                        data-lucide="search"

                        class="
                            pointer-events-none

                            absolute

                            left-3.5
                            top-1/2

                            h-4
                            w-4

                            -translate-y-1/2

                            text-gray-400
                        "
                    ></i>

                    <input
                        id="capture-search"

                        oninput="app.filterCaptures()"

                        type="text"

                        placeholder="ID ou item..."

                        class="
                            app-input

                            w-full

                            py-2.5
                            pl-10
                            pr-4
                        "
                    >
                </div>


                <select
                    id="capture-view"

                    class="
                        app-input

                        cursor-pointer

                        px-4
                        py-2.5
                    "
                >
                    <option value="all">
                        Todas as vistas
                    </option>

                    <option value="topo">
                        Topo
                    </option>

                    <option value="lateral1">
                        Lateral 1
                    </option>

                    <option value="lateral2">
                        Lateral 2
                    </option>
                </select>


                <select
                    id="capture-status"

                    class="
                        app-input

                        cursor-pointer

                        px-4
                        py-2.5
                    "
                >
                    <option value="all">
                        Todos os estados
                    </option>

                    <option value="OK">
                        OK
                    </option>

                    <option value="Defeito">
                        Defeito
                    </option>

                    <option value="Pendente">
                        Pendente
                    </option>
                </select>

            </div>


            <div
                class="
                    flex
                    items-center

                    gap-2
                "
            >

                <span
                    class="
                        hidden

                        text-xs

                        text-gray-400

                        sm:inline
                    "
                >
                    ${mockCapturas.length} linhas de vista de ${mockStats.totalLote ?? '--'} itens
                    (${mockStats.aprovados ?? '--'} itens OK, ${mockStats.reprovados ?? '--'} com defeito,
                    ${mockStats.inconclusivos ?? '--'} inconclusivo(s))
                </span>

                <button
                    onclick="app.applyCaptureFilters()"

                    class="
                        primary-button

                        whitespace-nowrap
                    "
                >
                    <i
                        data-lucide="sliders-horizontal"

                        class="
                            mr-2
                            h-4
                            w-4
                        "
                    ></i>

                    Aplicar filtros
                </button>

                <button
                    onclick="app.clearCaptureFilters()"

                    class="
                        secondary-button
                        whitespace-nowrap
                    "
                >

                    <i
                        data-lucide="x-circle"
                        class="mr-2 h-4 w-4"
                    ></i>

                    Limpar filtros
                </button>
            </div>

        </section>


        <!-- SUMMARY -->
        <section
            class="
                flex
                flex-wrap

                gap-2
            "
        >

            <div
                class="
                    rounded-full

                    bg-brand-black

                    px-4
                    py-2

                    text-xs
                    font-semibold
                    text-white

                    dark:bg-white
                    dark:text-black
                "
            >
                Todas as linhas ${mockCapturas.length}
            </div>

            <div
                class="
                    rounded-full

                    bg-brand-green/10

                    px-4
                    py-2

                    text-xs
                    font-semibold
                    text-brand-green
                "
            >
                Linhas OK ${mockCapturas.filter(linha => linha.status_vista === 'ok').length}
            </div>

            <div
                class="
                    rounded-full

                    bg-brand-red/10

                    px-4
                    py-2

                    text-xs
                    font-semibold
                    text-brand-red
                "
            >
                Linhas com defeito ${mockCapturas.filter(linha => linha.status_vista === 'defeito').length}
            </div>

            <div
                class="
                    rounded-full

                    bg-orange-500/10

                    px-4
                    py-2

                    text-xs
                    font-semibold
                    text-orange-500
                "
            >
                Linhas inconclusivas ${mockCapturas.filter(linha => linha.status_vista === 'inconclusivo').length}
            </div>

        </section>


        <!-- GRID -->
        <section
            class="
                grid

                grid-cols-1

                gap-5

                sm:grid-cols-2
                xl:grid-cols-3
                2xl:grid-cols-4
            "
        >

            ${mockCapturas.map((cap, index) => `
                <article
                    data-capture-card
                    data-id="${cap.id}"
                    data-item="${cap.item}"
                    data-view="${cap.vista_registro}"
                    data-status="${cap.status}"

                    onclick="app.navigate('investigacao', '${cap.id}')"

                    class="
                        capture-card

                        fade-in-up

                        delay-${(index % 4) * 75}
                    "
                >

                    <div
                        class="
                            capture-image

                            relative

                            h-48
                        "
                    >

                        <img
                            src="${cap.img}"
                            alt="evidencia da vista ${cap.vista} do item ${cap.item}"
                            loading="lazy"
                            decoding="async"
                        >


                        <div
                            class="
                                absolute

                                left-3
                                top-3
                            "
                        >
                            ${statusBadge(cap.status, 'item')}

                            ${cap.status_vista && cap.status_vista !== 'ok'
                                ? `<span class="status-badge status-badge-pending ml-1">
                                       <i data-lucide="clock-3" class="mr-1.5 h-3.5 w-3.5"></i>
                                       vista ${cap.status_vista}
                                   </span>

                                   ${cap.motivo
                                       ? `<span class="ml-1 rounded bg-black/60 px-2 py-0.5 text-[10px] font-normal text-white">${cap.motivo}</span>`
                                       : ''}`
                                : ''}
                        </div>


                        <div
                            class="
                                absolute

                                inset-x-0
                                bottom-0

                                h-20

                                bg-gradient-to-t

                                from-black/45
                                to-transparent

                                opacity-0

                                transition-opacity

                                group-hover:opacity-100
                            "
                        ></div>

                    </div>


                    <div class="p-5">

                        <div
                            class="
                                flex

                                items-start
                                justify-between

                                gap-3
                            "
                        >

                            <div>

                                <h3
                                    class="
                                        text-base
                                        font-bold
                                    "
                                >
                                    ${cap.item}
                                </h3>

                                <p
                                    class="
                                        mt-1

                                        text-xs
                                        text-gray-400
                                    "
                                >
                                    ${cap.id}
                                </p>

                            </div>


                            <span
                                class="
                                    rounded-lg

                                    bg-light-bg
                                    dark:bg-dark-bg

                                    px-2.5
                                    py-1.5

                                    text-[11px]
                                    font-medium
                                    text-gray-500
                                    dark:text-gray-400
                                "
                            >
                                ${cap.timestamp}
                            </span>

                        </div>


                        <div
                            class="
                                mt-5

                                grid
                                grid-cols-2

                                gap-3
                            "
                        >

                            <div>
                                <div
                                    class="
                                        text-[10px]
                                        font-semibold
                                        uppercase
                                        tracking-wider

                                        text-gray-400
                                    "
                                >
                                    Vista
                                </div>

                                <div
                                    class="
                                        mt-1

                                        text-sm
                                        font-semibold
                                    "
                                >
                                    ${cap.vista}
                                </div>
                            </div>


                            <div>
                                <div
                                    class="
                                        text-[10px]
                                        font-semibold
                                        uppercase
                                        tracking-wider

                                        text-gray-400
                                    "
                                >
                                    Confiança
                                </div>

                                <div
                                    class="
                                        mt-1

                                        text-sm
                                        font-semibold

                                        ${
                                            cap.status === 'Defeito'
                                                ? 'text-brand-red'
                                                : 'text-brand-green'
                                        }
                                    "
                                >
                                    ${cap.confianca}
                                </div>
                            </div>

                        </div>


                        <div
                            class="
                                mt-5

                                flex
                                items-center
                                justify-between

                                border-t
                                border-light-border
                                dark:border-dark-border

                                pt-4
                            "
                        >

                            <span
                                class="
                                    text-xs
                                    text-gray-400
                                "
                            >
                                Lote ${cap.lote}
                            </span>

                            <span
                                class="
                                    flex

                                    h-8
                                    w-8

                                    items-center
                                    justify-center

                                    rounded-full

                                    bg-light-bg
                                    dark:bg-dark-bg

                                    text-gray-400

                                    transition-colors

                                    hover:text-brand-red
                                "
                            >
                                <i
                                    data-lucide="arrow-up-right"
                                    class="h-4 w-4"
                                ></i>
                            </span>

                        </div>

                    </div>

                </article>
            `).join('')}

        </section>

    </div>
`;


const cartaoDaInvestigacao = id => {
    /*
     * Regra UNICA de "qual item a Investigacao abre" — usada pela vista e pelo `app.js`, para que o
     * detalhe buscado em `/api/item/<id>` seja do MESMO item que a tela mostra. Quando o app.js
     * mandava `null`, o detalhe vinha de outro item (ou de nada).
     *
     * Sem item informado, abre o defeito mais recente e DIZ que foi escolha automatica. Com id
     * informado e inexistente, NAO mostra outro item: antes o `||` caia no primeiro defeito (ou no
     * primeiro da lista) e os numeros de outro item apareciam como se fossem deste.
     */
    const pedido =
        id ? mockCapturas.find(item => item.id === id) : null;

    const automatico = !id;

    const cap =
        pedido ||
        (automatico
            ? (mockCapturas.find(item => item.status === 'Defeito') || mockCapturas[0] || null)
            : null);

    return { cap, automatico };
};


const renderInvestigacao = id => {
    const { cap, automatico } = cartaoDaInvestigacao(id);

    if (!cap) {
        return `
            <div class="fade-in-up mx-auto max-w-3xl">
                <section class="surface-card p-8">
                    <div class="flex items-center gap-3 text-brand-red">
                        <i data-lucide="search-x" class="h-6 w-6"></i>

                        <h2 class="text-lg font-bold">
                            Item nao encontrado no registro
                        </h2>
                    </div>

                    <p class="mt-3 text-sm text-gray-500 dark:text-gray-400">
                        Nada foi encontrado para
                        <span class="font-mono">${id || '(sem id)'}</span>.
                        Esta vista nao mostra outro item no lugar do pedido.
                    </p>

                    <button
                        onclick="app.navigate('capturas')"

                        class="mt-5 inline-flex items-center text-sm font-semibold text-brand-red"
                    >
                        <i data-lucide="arrow-left" class="mr-2 h-4 w-4"></i>

                        Voltar para Capturas
                    </button>
                </section>
            </div>`;
    }

    /*
     * O detalhe vem do `/api/item/<id>` (api.js guarda em mockItemDetalhe). A lista da tela de
     * Capturas nao traz evidencia nem correcao: sem esta busca, o rastro da D-30 nao aparecia.
     */
    const detalhe =
        (typeof mockItemDetalhe !== 'undefined' && mockItemDetalhe
         && mockItemDetalhe.item_id === cap.item && !mockItemDetalhe.inexistente)
            ? mockItemDetalhe
            : null;

    const linhasEvidencia =
        detalhe && detalhe.evidencias && detalhe.evidencias.length
            ? detalhe.evidencias.map(e => `
                <tr class="border-b border-black/5 dark:border-white/5">
                    <td class="py-1.5 pr-4 font-mono text-xs">${e.grandeza}</td>
                    <td class="py-1.5 pr-4">${e.valor === null || e.valor === undefined ? '--' : e.valor} ${e.unidade}</td>
                    <td class="py-1.5 pr-4">${e.origem}</td>
                    <td class="py-1.5 pr-4">${e.papel}</td>
                    <td class="py-1.5 font-mono text-xs">${e.metodo}</td>
                </tr>`).join('')
            : `<tr><td colspan="5" class="py-3 text-gray-400">
                   nenhuma grandeza registrada para este item
               </td></tr>`;

    const correcoes =
        detalhe && detalhe.correcoes && detalhe.correcoes.length
            ? detalhe.correcoes.map(c => `
                <li>${c.decisao_original} &rarr; ${c.decisao_corrigida}
                    (por ${c.corrigido_por || '--'})</li>`).join('')
            : '<li class="text-gray-400">nenhuma correcao de operador registrada</li>';

    const blocoDetalhe = `
        <section class="surface-card p-6">
            <div class="flex flex-wrap items-start justify-between gap-3">
                <h3 class="text-xs font-bold uppercase tracking-[.18em] text-gray-500">
                    Evidencias da decisao (D-30)
                </h3>

                ${automatico
                    ? `<p class="text-xs text-gray-400">
                           sem item selecionado — abrindo o defeito mais recente (${cap.id});
                           escolha um cartao em Capturas para abrir um item especifico
                       </p>`
                    : ''}
            </div>

            <table class="mt-3 w-full text-left text-sm">
                <thead class="text-xs uppercase tracking-wider text-gray-400">
                    <tr>
                        <th class="pb-2 pr-4">grandeza</th>
                        <th class="pb-2 pr-4">valor</th>
                        <th class="pb-2 pr-4">origem</th>
                        <th class="pb-2 pr-4">papel</th>
                        <th class="pb-2">metodo</th>
                    </tr>
                </thead>

                <tbody>${linhasEvidencia}</tbody>
            </table>

            <h3 class="mt-6 text-xs font-bold uppercase tracking-[.18em] text-gray-500">
                Correcoes do operador
            </h3>

            <ul class="mt-2 list-disc pl-5 text-sm">${correcoes}</ul>
        </section>`;

    return `
        ${blocoDetalhe}
        <div
            class="
                fade-in-up

                mx-auto

                max-w-[1400px]

                space-y-6
            "
        >

            <!-- BREADCRUMB -->
            <div
                class="
                    flex

                    items-center
                    justify-between
                "
            >

                <button
                    onclick="app.navigate('capturas')"

                    class="
                        inline-flex

                        items-center

                        text-sm
                        font-semibold

                        text-gray-500

                        transition-colors

                        hover:text-brand-red
                    "
                >
                    <span
                        class="
                            mr-2

                            flex

                            h-8
                            w-8

                            items-center
                            justify-center

                            rounded-full

                            bg-light-surface
                            dark:bg-dark-raised

                            shadow-sm
                        "
                    >
                        <i
                            data-lucide="arrow-left"

                            class="
                                h-4
                                w-4
                            "
                        ></i>
                    </span>

                    Capturas
                </button>


                <span
                    class="
                        rounded-full

                        border
                        border-light-border
                        dark:border-dark-border

                        bg-light-surface
                        dark:bg-dark-raised

                        px-3
                        py-1.5

                        font-mono
                        text-xs
                        font-semibold
                        text-gray-500
                        dark:text-gray-300
                    "
                >
                    ${cap.id}
                </span>

            </div>


            <!-- INSPECTOR -->
            <div
                class="
                    grid

                    grid-cols-1

                    gap-6

                    xl:grid-cols-[minmax(0,1fr)_340px]
                "
            >

                <!-- EVIDENCE -->
                <div class="space-y-6">

                    <section
                        class="
                            surface-card

                            overflow-hidden

                            p-2
                        "
                    >

                        <div
                            class="
                                relative

                                aspect-video

                                overflow-hidden

                                rounded-[16px]

                                bg-black
                            "
                        >

                            <img
                                src="${cap.img}"
                                alt="Evidência ${cap.id}"

                                class="
                                    h-full
                                    w-full

                                    object-cover
                                "
                            >


                            <div
                                class="
                                    absolute

                                    left-4
                                    top-4

                                    flex

                                    gap-2
                                "
                            >

                                <span
                                    class="
                                        rounded-lg

                                        border
                                        border-white/10

                                        bg-black/55

                                        px-3
                                        py-1.5

                                        text-xs
                                        font-semibold
                                        text-white

                                        backdrop-blur-lg
                                    "
                                >
                                    ${cap.vista}
                                </span>

                                <span
                                    class="
                                        rounded-lg

                                        border
                                        border-white/10

                                        bg-black/55

                                        px-3
                                        py-1.5

                                        text-xs
                                        font-semibold
                                        text-white

                                        backdrop-blur-lg
                                    "
                                >
                                    ${cap.timestamp}
                                </span>

                            </div>


                            <button
                                class="
                                    absolute

                                    right-4
                                    top-4

                                    flex

                                    h-10
                                    w-10

                                    items-center
                                    justify-center

                                    rounded-xl

                                    border
                                    border-white/10

                                    bg-black/55

                                    text-white

                                    backdrop-blur-lg

                                    transition-colors

                                    hover:bg-brand-red
                                "
                            >
                                <i
                                    data-lucide="maximize-2"
                                    class="h-4 w-4"
                                ></i>
                            </button>


                            

                        </div>

                    </section>


                    <!-- VIEWS -->
                    <section class="surface-card p-5 sm:p-6">

                        <div
                            class="
                                mb-4

                                flex

                                items-center
                                justify-between
                            "
                        >

                            <div>
                                <h3
                                    class="
                                        text-sm
                                        font-bold
                                    "
                                >
                                    Evidências do item
                                </h3>

                                <p
                                    class="
                                        mt-1

                                        text-xs
                                        text-gray-400
                                    "
                                >
                                    Vistas associadas a ${cap.item}
                                </p>
                            </div>

                            <span
                                class="
                                    text-xs
                                    font-medium
                                    text-gray-400
                                "
                            >
                                ${cap.lote}
                            </span>

                        </div>


                        <div
                            class="
                                flex

                                gap-4

                                overflow-x-auto

                                pb-1
                            "
                        >

                            <div
                                class="
                                    relative

                                    w-40
                                    flex-shrink-0

                                    overflow-hidden

                                    rounded-2xl

                                    border-2
                                    border-brand-red

                                    bg-black
                                "
                            >

                                <img
                                    src="${cap.img}"

                                    class="
                                        h-28
                                        w-full

                                        object-cover
                                    "
                                >

                                <div
                                    class="
                                        absolute

                                        inset-x-0
                                        bottom-0

                                        bg-gradient-to-t

                                        from-black/80
                                        to-transparent

                                        p-3
                                        pt-10
                                    "
                                >
                                    <div
                                        class="
                                            text-xs
                                            font-bold
                                            text-white
                                        "
                                    >
                                        ${cap.vista}
                                    </div>

                                    <div
                                        class="
                                            mt-0.5

                                            text-[10px]
                                            font-bold
                                            text-red-300
                                        "
                                    >
                                        ATUAL
                                    </div>
                                </div>

                            </div>


                            <div
                                class="
                                    relative

                                    w-40
                                    flex-shrink-0

                                    overflow-hidden

                                    rounded-2xl

                                    border
                                    border-light-border
                                    dark:border-dark-border

                                    bg-black

                                    opacity-60

                                    transition-all

                                    hover:border-brand-red/40
                                    hover:opacity-100
                                "
                            >

                                <img
                                    src="${PNAAT_API._semImagem(cap.item, 'outra vista', 'sem imagem registrada para esta vista')}"

                                    class="
                                        h-28
                                        w-full

                                        object-cover
                                    "
                                >

                                <div
                                    class="
                                        absolute

                                        inset-x-0
                                        bottom-0

                                        bg-gradient-to-t

                                        from-black/80
                                        to-transparent

                                        p-3
                                        pt-10
                                    "
                                >
                                    <div
                                        class="
                                            text-xs
                                            font-bold
                                            text-white
                                        "
                                    >
                                        ${
                                            cap.vista === 'Topo'
                                                ? 'Lateral'
                                                : 'Topo'
                                        }
                                    </div>

                                    <div
                                        class="
                                            mt-0.5

                                            text-[10px]
                                            font-bold
                                            text-green-300
                                        "
                                    >
                                        REFERÊNCIA
                                    </div>
                                </div>

                            </div>

                        </div>

                    </section>

                </div>


                <!-- INSPECTOR PANEL -->
                <aside class="space-y-5">

                    <!-- STATUS -->
                    <section class="surface-card p-6">

                        <div
                            class="
                                flex

                                items-start
                                justify-between
                            "
                        >

                            <div>

                                <span
                                    class="
                                        text-[10px]
                                        font-semibold
                                        uppercase
                                        tracking-[.13em]

                                        text-gray-400
                                    "
                                >
                                    Resultado automático
                                </span>

                                <div class="mt-3">
                                    ${statusBadge(cap.status)}
                                </div>

                            </div>


                            <div
                                class="
                                    flex

                                    h-12
                                    w-12

                                    items-center
                                    justify-center

                                    rounded-2xl

                                    ${
                                        cap.status === 'Defeito'
                                            ? 'bg-brand-red/10 text-brand-red'
                                            : 'bg-brand-green/10 text-brand-green'
                                    }
                                "
                            >
                                <i
                                    data-lucide="${
                                        cap.status === 'Defeito'
                                            ? 'triangle-alert'
                                            : 'circle-check'
                                    }"

                                    class="
                                        h-6
                                        w-6
                                    "
                                ></i>
                            </div>

                        </div>


                        <div
                            class="
                                mt-6

                                rounded-2xl

                                bg-light-bg
                                dark:bg-dark-bg

                                p-4
                            "
                        >

                            <div
                                class="
                                    flex

                                    items-center
                                    justify-between
                                "
                            >
                                <span
                                    class="
                                        text-xs
                                        font-semibold
                                        text-gray-400
                                    "
                                >
                                    Confiança
                                </span>

                                <span
                                    class="
                                        text-xl
                                        font-bold
                                    "
                                >
                                    ${cap.confianca}
                                </span>
                            </div>

                        </div>

                    </section>


                    <!-- DETAILS -->
                    <section class="surface-card p-6">

                        <h3
                            class="
                                mb-5

                                text-sm
                                font-bold
                            "
                        >
                            Detalhes da captura
                        </h3>


                        <div class="space-y-4">

                            <div
                                class="
                                    flex

                                    items-center
                                    justify-between

                                    gap-3
                                "
                            >
                                <span
                                    class="
                                        flex
                                        items-center

                                        text-xs
                                        text-gray-400
                                    "
                                >
                                    <i
                                        data-lucide="package"
                                        class="mr-2 h-4 w-4"
                                    ></i>

                                    Item
                                </span>

                                <strong class="text-xs">
                                    ${cap.item}
                                </strong>
                            </div>


                            <div
                                class="
                                    flex

                                    items-center
                                    justify-between

                                    gap-3
                                "
                            >
                                <span
                                    class="
                                        flex
                                        items-center

                                        text-xs
                                        text-gray-400
                                    "
                                >
                                    <i
                                        data-lucide="layers"
                                        class="mr-2 h-4 w-4"
                                    ></i>

                                    Lote
                                </span>

                                <strong class="text-xs">
                                    ${cap.lote}
                                </strong>
                            </div>


                            <div
                                class="
                                    flex

                                    items-center
                                    justify-between

                                    gap-3
                                "
                            >
                                <span
                                    class="
                                        flex
                                        items-center

                                        text-xs
                                        text-gray-400
                                    "
                                >
                                    <i
                                        data-lucide="camera"
                                        class="mr-2 h-4 w-4"
                                    ></i>

                                    Vista
                                </span>

                                <strong class="text-xs">
                                    ${cap.vista}
                                </strong>
                            </div>


                            <div
                                class="
                                    flex

                                    items-center
                                    justify-between

                                    gap-3
                                "
                            >
                                <span
                                    class="
                                        flex
                                        items-center

                                        text-xs
                                        text-gray-400
                                    "
                                >
                                    <i
                                        data-lucide="clock-3"
                                        class="mr-2 h-4 w-4"
                                    ></i>

                                    Timestamp
                                </span>

                                <strong
                                    class="
                                        font-mono
                                        text-xs
                                    "
                                >
                                    ${cap.timestamp}
                                </strong>
                            </div>


                            <div
                                class="
                                    flex

                                    items-center
                                    justify-between

                                    gap-3
                                "
                            >
                                <span
                                    class="
                                        flex
                                        items-center

                                        text-xs
                                        text-gray-400
                                    "
                                >
                                    <i
                                        data-lucide="zap"
                                        class="mr-2 h-4 w-4"
                                    ></i>

                                    Inferência
                                </span>

                                <strong class="text-xs">
                                    ${cap.latencia}
                                </strong>
                            </div>

                        </div>

                    </section>


                    <!-- ACTION -->
                    <section
                        class="
                            surface-card

                            relative
                            overflow-hidden

                            p-6
                        "
                    >

                        <div
                            class="
                                pointer-events-none

                                absolute

                                -right-8
                                -top-8

                                h-28
                                w-28

                                rounded-full

                                bg-brand-red/5

                                blur-2xl
                            "
                        ></div>


                        <div class="relative">

                            <h3
                                class="
                                    text-sm
                                    font-bold
                                "
                            >
                                Decisão do operador
                            </h3>

                            <p
                                class="
                                    mt-1

                                    text-xs
                                    leading-relaxed
                                    text-gray-400
                                "
                            >
                                A decisão original permanece registrada.
                            </p>

                            ${(mockItemDetalhe && mockItemDetalhe.correcao_vigente)
                                ? `<p class="mt-2 text-xs text-brand-green">
                                       decisão vigente: ${mockItemDetalhe.decisao_efetiva}
                                       por ${mockItemDetalhe.correcao_vigente.corrigido_por}
                                       em ${mockItemDetalhe.correcao_vigente.timestamp}
                                   </p>`
                                : `<p class="mt-2 text-xs text-gray-400">
                                       sem correção registrada: vale a decisão do registro
                                   </p>`}


                            <div
                                class="
                                    mt-5

                                    space-y-3
                                "
                            >

                                <label
                                    class="block text-[11px] uppercase tracking-[.18em] text-gray-500"
                                    for="operador-nome"
                                >
                                    Quem decide
                                </label>

                                <input
                                    id="operador-nome"
                                    class="app-input w-full px-4 py-2.5"
                                    placeholder="nome do operador (vai para a trilha)"
                                    autocomplete="off"
                                >


                                <button
                                    class="
                                        success-button
                                        w-full
                                    "
                                    onclick="app.registrarDecisao('ok')"
                                >
                                    <i
                                        data-lucide="circle-check"

                                        class="
                                            mr-2
                                            h-4
                                            w-4
                                        "
                                    ></i>

                                    Registrar decisão: aprovado
                                </button>


                                <button
                                    class="
                                        danger-button
                                        w-full
                                    "
                                    onclick="app.registrarDecisao('defeito')"
                                >
                                    <i
                                        data-lucide="triangle-alert"

                                        class="
                                            mr-2
                                            h-4
                                            w-4
                                        "
                                    ></i>

                                    Registrar decisão: defeito
                                </button>


                                <p id="resultado-decisao" class="text-xs"></p>

                            </div>


                            <div
                                class="
                                    mt-5

                                    flex
                                    items-center
                                    justify-center

                                    text-[11px]
                                    text-gray-400
                                "
                            >
                                <i
                                    data-lucide="info"

                                    class="
                                        mr-1.5
                                        h-3.5
                                        w-3.5
                                    "
                                ></i>

                                Esta instalação não tem autenticação: quem alcança a rede registra a
                                decisão, e a trilha guarda o nome informado — sem senha e sem
                                verificação de privilégio.
                            </div>

                        </div>

                    </section>

                </aside>

            </div>

        </div>
    `;
};

/*: escapa texto que vem de fora (motivo livre, detalhe de erro do rig) antes de entrar em innerHTML */
const escDoDebug = valor => String(valor === null || valor === undefined ? '' : valor)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');


// Painel do modelo servido: contrato da entrega (imutavel) + estado vivo do detector.
// Montado por concatenacao de proposito: template aninhado aqui ja custou uma crase desbalanceada.
const renderModelo = (d, painel, linha, falha, escDoDebug) => {
    if (!d || !d.modelo) {
        return painel('Modelo que o detector serve',
            '<p class="text-sm text-gray-400">lendo o modelo...</p>', null);
    }
    const m = d.modelo;
    if (m.erro_contrato) {
        return painel('Modelo que o detector serve',
            falha({ erro: m.erro_contrato }, 'contrato do modelo'),
            'Sem contrato nao ha como saber classes, limiares nem limitacoes do que esta servido.');
    }

    const c = m.contrato || {};
    const s = m.saude || {};
    const mm = c.metricas_medidas || {};
    const linhas = [];

    linhas.push(linha('servindo agora', m.erro_detector
        ? '<span class="text-brand-red">detector fora: ' + escDoDebug(m.erro_detector) + '</span>'
        : escDoDebug(s.model_name || '-') + ' ' + (s.model_loaded ? '(carregado)' : '(NAO carregado)')));
    linhas.push(linha('declarado no contrato', escDoDebug(m.declarado_no_contrato || '-')));
    linhas.push(linha('papel', escDoDebug(c.papel || '-')));
    linhas.push(linha('peso', escDoDebug(c.arquivo || '-') + ' - ' + (c.tamanho_mb || '?') +
        ' MB - sha ' + escDoDebug((c.sha256 || '').slice(0, 12)) + '...'));
    linhas.push(linha('classes do contrato', escDoDebug((c.classes || []).join(' | '))));
    linhas.push(linha('limiares por classe', escDoDebug(JSON.stringify((c.decisao || {}).limiares || {}))));
    linhas.push(linha('regra de decisao', escDoDebug((c.decisao || {}).regra || '-')));
    linhas.push(linha('k-fold (5 dobras)', escDoDebug(mm.kfold_5_dobras_mAP50 || '-')));

    const op = mm.decisao_operacional;
    linhas.push(linha('decisao operacional', op
        ? op.acertos + '/' + op.total + ' - ' + op.revisar + ' em revisao - acuracia ' +
          op.acuracia_sem_revisao + ' - defeito decidido como normal: ' + op.defeito_decidido_como_normal
        : '-'));

    const e = c.entrada || {};
    linhas.push(linha('imgsz', 'treinado ' + e.imgsz_treinado + ' - recomendado na borda ' +
        e.imgsz_recomendado_borda));

    const limites = c.limitacoes_declaradas || [];
    let bloco = '';
    if (limites.length) {
        let itens = '';
        for (const x of limites) {
            itens += '<li>- ' + escDoDebug(x) + '</li>';
        }
        bloco = '<div class="mt-2 rounded-lg border border-orange-500/30 bg-orange-500/5 p-3">' +
            '<p class="text-[10px] font-bold uppercase tracking-wide text-orange-500">' +
            'Limitacoes declaradas pelo produtor</p>' +
            '<ul class="mt-1 space-y-1 text-xs text-gray-300">' + itens + '</ul></div>';
    }

    return painel('Modelo que o detector serve', linhas.join('') + bloco,
        'O contrato vem da entrega do produtor (pasta imutavel, com sha proprio) e o estado acima e '
        + 'lido do detector agora. Candidato medido, nao promovido.');
};


const renderDebug = () => {
    /*
     * Aba de bancada. Todo dado vem do rig (servico da camera) ou da ponte do gatilho, e toda ausencia
     * se declara: se o rig nao responde, a tela diz por que — painel vazio e pior que erro, porque
     * parece que nada aconteceu.
     */
    const d = (typeof mockDebug !== 'undefined' && mockDebug) ? mockDebug : {};
    const ponte = (d.ponte && !d.ponte.erro) ? d.ponte : null;
    // a ponte publica o delay ANINHADO em `trigger`; ler na raiz dava sempre vazio
    const gatilhoDaPonte = (ponte && ponte.trigger) ? ponte.trigger : null;
    const estado = (d.estado && !d.estado.erro) ? d.estado : null;
    const rig = estado ? (estado.rig || {}) : {};

    const falha = (bloco, rotulo) => `
        <p class="text-sm text-brand-red">
            ${rotulo} indisponivel: ${escDoDebug(bloco.erro)}
        </p>`;

    const linha = (rotulo, valor) => `
        <div class="flex items-baseline justify-between gap-4 border-b border-black/5 py-1 dark:border-white/5">
            <span class="text-xs uppercase tracking-wider text-gray-400">${rotulo}</span>
            <span class="font-mono text-xs">${valor === null || valor === undefined || valor === ''
                ? '&mdash;' : valor}</span>
        </div>`;

    const painel = (titulo, corpo, nota) => `
        <section class="surface-card p-6">
            <h3 class="text-xs font-bold uppercase tracking-[.18em] text-gray-500">${titulo}</h3>

            <div class="mt-3">${corpo}</div>

            ${nota ? `<p class="mt-3 text-xs text-gray-400">${nota}</p>` : ''}
        </section>`;

    const acao = d.acao || null;
    const series = (d.series && d.series.series) ? d.series.series : [];
    const gatilhos = (d.gatilhos && d.gatilhos.gatilhos) ? d.gatilhos.gatilhos : [];
    const sensor = (ponte && ponte.sensor) ? ponte.sensor : null;

    return `
        <div class="fade-in-up space-y-6">
            <section class="surface-card p-6">
                <h2 class="text-2xl font-bold tracking-tight">Debug da bancada</h2>

                <p class="mt-2 max-w-3xl text-sm leading-6 text-gray-500 dark:text-gray-400">
                    Estado do gatilho e da camera, delay de captura, captura manual e teste do gatilho.
                    Cada ensaio de bancada entra no registro como evento de gatilho (marcado como teste),
                    para o disparo nao ficar invisivel. Leitura de
                    <span class="font-mono text-xs">${d.atualizado_em || '&mdash;'}</span>.
                </p>

                <div class="mt-4 flex flex-wrap gap-2">
                    <button class="secondary-button" onclick="app.carregarDebug()">
                        <i data-lucide="refresh-cw" class="mr-2 h-4 w-4"></i> Reler estado
                    </button>
                </div>
            </section>


            ${acao ? `
                <section class="surface-card p-6">
                    <h3 class="text-xs font-bold uppercase tracking-[.18em] text-gray-500">
                        Ultima acao: ${acao.rotulo}
                    </h3>

                    <p class="mt-2 text-sm ${acao.estado === 'ok' ? 'text-brand-green'
                        : acao.estado === 'falhou' ? 'text-brand-red' : 'text-gray-400'}">
                        ${escDoDebug(acao.estado)}${acao.erro ? ` — ${escDoDebug(acao.erro)}` : ''}${acao.detalhe ? `: ${escDoDebug(acao.detalhe)}` : ''}
                    </p>

                    ${acao.dados ? `<pre class="custom-scrollbar mt-3 max-h-64 overflow-auto rounded-lg bg-black/5 p-3 text-[11px] leading-4 dark:bg-white/5">${escDoDebug(JSON.stringify(acao.dados, null, 1))}</pre>` : ''}
                </section>` : ''}


            <div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
                ${painel('Gatilho (ponte serial)',
                    !d.ponte ? '<p class="text-sm text-gray-400">lendo o estado do gatilho...</p>'
                    : d.ponte.erro ? falha(d.ponte, 'ponte do gatilho') : `
                        ${linha('serial aberta', ponte.serial_open)}
                        ${linha('erro da serial', ponte.serial_last_error ? ponte.serial_last_error : 'nenhum')}
                        ${linha('bytes / linhas', `${ponte.serial_bytes || 0} / ${ponte.serial_lines || 0}`)}
                        ${linha('frames ok / ruins', `${ponte.frames_ok || 0} / ${ponte.frames_bad || 0}`)}
                        ${linha('frames texto / bin', `${ponte.frames_text || 0} / ${ponte.frames_bin || 0}`)}
                        ${linha('nivel do sensor', sensor ? sensor.nivel : '&mdash;')}
                        ${linha('idade da leitura (s)', sensor ? sensor.idade_s : '&mdash;')}
                        ${linha('transporte', ponte.transport)}
                        ${linha('inicializado (booted)', ponte.booted)}
                        ${linha('delay no dispositivo (ms)', gatilhoDaPonte ? gatilhoDaPonte.delay_ms : '&mdash;')}
                        ${linha('delay salvo em', gatilhoDaPonte ? gatilhoDaPonte.delay_saved_at : '&mdash;')}
                        ${(() => {
                            // latencia MEDIDA do gatilho: e dela que sai o lead da ESP-CAM. Sem isto o
                            // operador so tinha o valor configurado, que nao diz quanto o quadro demora.
                            const est = (ponte && ponte.delay) ? ponte.delay : null;
                            const u = (est && est.ultimo) ? est.ultimo : null;
                            const amostras = est ? (est.n || 0) : 0;
                            if (!u || !amostras) {
                                return linha('latencia medida', 'sem ensaio medido ainda') ;
                            }
                            const ms = v => (v === undefined || v === null) ? '&mdash;' : v + ' ms';
                            return linha('latencia medida (ultima)',
                                    'sensor&rarr;foto ' + ms(u.sensor_foto_ms) +
                                    ' · comando&rarr;foto ' + ms(u.comando_foto_ms) +
                                    ' · camera ' + ms(u.camera_total_ms)) +
                                linha('latencia medida (n=' + amostras + ')',
                                    'media ' + ms(est.media_ms) + ' · min ' + ms(est.min_ms) +
                                    ' · max ' + ms(est.max_ms)) +
                                linha('lead da ESP-CAM',
                                    est.media_ms ? 'o pedido tem de sair ~' + Math.round(est.media_ms) +
                                        ' ms antes do alvo para o quadro cair nele' : '&mdash;');
                        })()}
                        ${linha('estado do gatilho', gatilhoDaPonte ? gatilhoDaPonte.estado : '&mdash;')}
                        ${linha('ultimo evento do gatilho', gatilhoDaPonte ? gatilhoDaPonte.ultimo_n : '&mdash;')}
                    `,
                    'A ponte e quem fala com a ESP pela serial: nivel do sensor, contadores de frame e o delay vigente saem dela.')}

                ${painel('Camera do rig',
                    !d.estado ? '<p class="text-sm text-gray-400">lendo o servico da camera...</p>'
                    : d.estado.erro ? falha(d.estado, 'servico da camera') : `
                        ${linha('camera', rig.camera)}
                        ${linha('erro da camera', rig.erro_camera ? rig.erro_camera : 'nenhum')}
                        ${linha('tem fundo', rig.tem_fundo)}
                        ${linha('tem referencia', rig.tem_referencia)}
                        ${linha('referencia valida', rig.referencia_ok)}
                        ${linha('analises registradas', rig.analises)}
                        ${linha('roi atual', Array.isArray(rig.roi) ? rig.roi.join(', ') : rig.roi)}
                    `,
                    'Este servico e o dono unico da camera: e ele que tira as fotos das 3 fontes.')}
            </div>


            <div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
                ${painel('Delay de captura por camera (gatilho &rarr; foto)', `
                    ${(() => {
                        const config = (d.delayCamera && !d.delayCamera.erro) ? d.delayCamera : null;
                        const ultima = (d.series && d.series.series && d.series.series.length)
                            ? d.series.series.find(s => s.atraso_medido_por_camera
                                && Object.keys(s.atraso_medido_por_camera).length) : null;
                        const medido = (ultima && ultima.atraso_medido_por_camera) || {};
                        const cameras = ['csi', 'usb', 'espcam'];

                        let linhas = '';
                        for (const cam of cameras) {
                            const cfg = config ? config[cam] : undefined;
                            const m = medido[cam] || {};
                            linhas += '<tr class="border-t border-white/5">' +
                                '<td class="py-1 pr-4 font-mono text-xs">' + cam + '</td>' +
                                '<td class="py-1 pr-4 text-xs">' + (cfg === undefined || cfg === null
                                    ? '&mdash;' : cfg + ' ms') + '</td>' +
                                '<td class="py-1 pr-4 text-xs">' + (m.atraso_efetivo_ms === undefined
                                    || m.atraso_efetivo_ms === null ? '&mdash;' : m.atraso_efetivo_ms + ' ms') +
                                '</td>' +
                                '<td class="py-1 text-[11px] text-gray-500">' +
                                (m.atraso_configurado_ms === undefined || m.atraso_configurado_ms === null
                                    ? '' : 'configurado na serie: ' + m.atraso_configurado_ms + ' ms') +
                                '</td></tr>';
                        }

                        return `
                        <p class="text-sm">
                            Delay <span class="font-semibold">deste rig</span> por camera, contra o que a
                            ultima serie <span class="font-semibold">realmente mediu</span>:
                            ${ultima ? '<span class="font-mono text-xs">(' + ultima.serie + ')</span>' : ''}
                        </p>

                        <table class="mt-2 w-full text-left">
                            <thead><tr class="text-[10px] uppercase tracking-wider text-gray-500">
                                <th class="pr-4">camera</th><th class="pr-4">configurado</th>
                                <th class="pr-4">medido</th><th></th>
                            </tr></thead>
                            <tbody>${linhas}</tbody>
                        </table>

                        <p class="mt-2 text-[11px] text-gray-500">
                            Delay da ponte (ramo dela, volatile em RAM): ${(gatilhoDaPonte
                                && gatilhoDaPonte.delay_ms !== undefined && gatilhoDaPonte.delay_ms !== null)
                                ? gatilhoDaPonte.delay_ms + ' ms' : (d.ponte && d.ponte.erro
                                ? 'indisponivel (ponte fora)' : '&mdash;')}.
                            O rig reaplica o valor da ESP-CAM na ponte a cada start.
                            Na ESP-CAM o valor e o instante do PEDIDO: o quadro chega depois, pelo pipeline dela.
                        </p>

                        <div class="mt-3 flex flex-wrap items-end gap-2">
                            <div>
                                <label class="block text-[11px] uppercase tracking-wider text-gray-500"
                                       for="debug-delay-camera">camera</label>

                                <select id="debug-delay-camera" class="app-input mt-1 w-32 px-2 py-2">
                                    <option value="">todas</option>
                                    <option value="csi">csi</option>
                                    <option value="usb">usb</option>
                                    <option value="espcam">espcam</option>
                                </select>
                            </div>

                            <div>
                                <label class="block text-[11px] uppercase tracking-wider text-gray-500"
                                       for="debug-delay-ms">novo delay (ms)</label>

                                <input id="debug-delay-ms" type="number" min="0" max="30000" step="10"
                                       class="app-input mt-1 w-36 px-3 py-2" placeholder="0 a 30000">
                            </div>

                            <div>
                                <label class="block text-[11px] uppercase tracking-wider text-gray-500"
                                       for="debug-delay-operador">quem muda</label>

                                <input id="debug-delay-operador" class="app-input mt-1 w-44 px-3 py-2"
                                       placeholder="operador (vai para a trilha)" autocomplete="off">
                            </div>

                            <button class="secondary-button" onclick="app.configurarDelay()">
                                <i data-lucide="timer-reset" class="mr-2 h-4 w-4"></i> Configurar
                            </button>
                        </div>
                        `;
                    })()}

                    <p class="mt-3 text-xs text-orange-500">
                        Este rig tem UM delay para as tres cameras. Cameras a distancias diferentes do
                        sensor precisam de delays diferentes (<span class="font-mono">tau* = d / v</span>
                        por camera); com um valor so, no maximo uma delas captura no instante certo.
                    </p>
                `, 'Ate o rig aplicar delay por camera, o numero unico e o que existe — e a tela diz isso.')}

                ${painel('Teste do gatilho e captura manual', `
                    <div class="space-y-3">
                        <div>
                            <label class="block text-[11px] uppercase tracking-wider text-gray-500"
                                   for="debug-item-teste">item da bancada (opcional)</label>

                            <input id="debug-item-teste" class="app-input mt-1 w-full px-3 py-2"
                                   placeholder="ex.: ITM-001 (vazio = gatilho precede o item)">
                        </div>

                        <button class="secondary-button w-full" onclick="app.testarGatilho()">
                            <i data-lucide="zap" class="mr-2 h-4 w-4"></i>
                            Testar gatilho nas 3 cameras (bancada)
                        </button>

                        <button class="secondary-button w-full" onclick="app.capturarManual()">
                            <i data-lucide="camera" class="mr-2 h-4 w-4"></i>
                            Captura manual (uma foto de cada fonte)
                        </button>
                    </div>
                `, 'O teste do gatilho usa a mesma rota do sensor na ponte; a captura manual nao e o fluxo do trigger.')}
            </div>


            ${renderModelo(d, painel, linha, falha, escDoDebug)}

            ${painel('Fotos capturadas (series do rig)',
                !d.series ? '<p class="text-sm text-gray-400">lendo as series...</p>'
                : d.series.erro ? falha(d.series, 'lista de series') :
                (series.length ? `
                    <p class="mb-3 text-xs text-gray-400">
                        ${d.series.completas || 0} completa(s) e ${d.series.parciais || 0} incompleta(s) em
                        <span class="font-mono">${d.series.pasta || '&mdash;'}</span>.
                        A captura que falhou no meio CONTINUA aqui: a foto que existe aparece, a que falta
                        e nomeada.
                    </p>

                    <div class="space-y-5">
                        ${series.slice(0, 8).map(s => `
                            <div>
                                <div class="flex flex-wrap items-baseline gap-2">
                                    <span class="font-mono text-xs">${s.serie}</span>

                                    <span class="rounded-full px-2 py-0.5 text-[10px] font-bold ${s.completa
                                        ? 'bg-brand-green/15 text-brand-green'
                                        : 'bg-orange-500/15 text-orange-500'}">
                                        ${s.completa ? 'completa' : 'incompleta'}
                                    </span>

                                    ${(s.faltantes || []).length
                                        ? `<span class="text-[10px] text-orange-500">falta: ${escDoDebug(s.faltantes.join(', '))}</span>`
                                        : ''}

                                    ${s.motivo ? `<span class="text-[10px] text-gray-400">${escDoDebug(s.motivo)}</span>` : ''}
                                </div>

                                ${(s.fotos || []).length ? `
                                    <div class="mt-2 grid grid-cols-3 gap-2">
                                        ${s.fotos.map(f => `
                                            <figure>
                                                <a href="${f.url}" target="_blank" rel="noopener">
                                                    <img src="${f.url}"
                                                         alt="foto ${f.camera || f.arquivo} da serie ${s.serie}"
                                                         loading="lazy" decoding="async"
                                                         class="h-24 w-full rounded-lg object-cover">
                                                </a>
                                                <figcaption class="mt-1 text-[10px] text-gray-400">
                                                    ${f.camera || f.arquivo} • ${Math.round((f.bytes || 0) / 1024)} kB
                                                    <br>${escDoDebug(f.quando || '')}
                                                </figcaption>
                                            </figure>`).join('')}
                                    </div>`
                                    : '<p class="mt-2 text-xs text-brand-red">nenhuma foto nesta pasta (captura interrompida antes de qualquer foto)</p>'}
                            </div>`).join('')}
                    </div>` : `<p class="text-sm text-gray-400">nenhuma pasta de serie nesta instalacao</p>`),
                'As fotos sao servidas pelo hub (mesma origem) e a lista vem da pasta, nao do filtro do rig — por isso a captura incompleta nao desaparece.')}


            ${painel('Fotos dos itens ja ingeridos (evidencia no registro)',
                !d.ingeridos ? '<p class="text-sm text-gray-400">lendo os itens ingeridos...</p>'
                : d.ingeridos.erro ? falha(d.ingeridos, 'itens ingeridos') :
                ((d.ingeridos.itens || []).length ? `
                    <div class="space-y-4">
                        ${d.ingeridos.itens.map(item => `
                            <div>
                                <p class="text-xs">
                                    <span class="font-mono">${escDoDebug(item.item_id)}</span>
                                    • ${escDoDebug(item.status_final)} •
                                    ${escDoDebug(item.qualidade_registro)}
                                    • ${escDoDebug((item.timestamp_trigger || '').slice(0, 19))}
                                </p>

                                <div class="mt-2 grid grid-cols-3 gap-2">
                                    ${(item.fotos || []).map(f => `
                                        <figure>
                                            <a href="${f.url}" target="_blank" rel="noopener">
                                                <img src="${f.url}"
                                                     alt="evidencia da vista ${f.vista} do item ${item.item_id}"
                                                     loading="lazy" decoding="async"
                                                     class="h-24 w-full rounded-lg object-cover">
                                            </a>
                                            <figcaption class="mt-1 text-[10px] text-gray-400">
                                                ${f.vista} (${f.dominio}) — ${escDoDebug(f.arquivo)}
                                            </figcaption>
                                        </figure>`).join('')}
                                </div>
                            </div>`).join('')}
                    </div>`
                    : '<p class="text-sm text-gray-400">nenhum item com foto de serie ingerida ainda</p>'),
                'A evidencia e a copia que ficou na raiz do hub na ingestao: e ela que a Investigacao e o relatorio mostram.')}


            ${painel('Historico de gatilhos no registro',
                !d.gatilhos ? '<p class="text-sm text-gray-400">lendo o historico do registro...</p>'
                : d.gatilhos.erro ? falha(d.gatilhos, 'historico do registro') :
                (gatilhos.length ? `
                    <table class="w-full text-left text-sm">
                        <thead class="text-xs uppercase tracking-wider text-gray-400">
                            <tr>
                                <th class="pb-2 pr-3">id</th>
                                <th class="pb-2 pr-3">quando</th>
                                <th class="pb-2 pr-3">fonte</th>
                                <th class="pb-2 pr-3">estado</th>
                                <th class="pb-2 pr-3">item</th>
                                <th class="pb-2">motivo</th>
                            </tr>
                        </thead>

                        <tbody>
                            ${gatilhos.map(g => `
                                <tr class="border-b border-black/5 dark:border-white/5 ${g.teste ? 'text-orange-500' : ''}">
                                    <td class="py-1.5 pr-3 font-mono text-xs">${g.id}</td>
                                    <td class="py-1.5 pr-3 font-mono text-xs">${g.timestamp}</td>
                                    <td class="py-1.5 pr-3">${g.fonte}</td>
                                    <td class="py-1.5 pr-3">${g.estado}</td>
                                    <td class="py-1.5 pr-3 font-mono text-xs">${g.item_id || '(sem item)'}</td>
                                    <td class="py-1.5 text-xs">${escDoDebug(g.motivo) || '&mdash;'}${g.teste ? ' [teste]' : ''}</td>
                                </tr>`).join('')}
                        </tbody>
                    </table>` : `<p class="text-sm text-gray-400">nenhum evento de gatilho registrado</p>`),
                'O disparo que NAO virou item tambem entra (falso, duplicado, invalido): e o unico jeito de o gatilho ser observavel.')}
        </div>`;
};


const renderQualidade = () => {
    /*
     * Os indicadores vem de `/api/qualidade`. Antes esta vista era um placeholder ("Integracao
     * pendente") e o payload que o adaptador buscava era descartado: dizer "pendente" com o dado
     * chegando seria afirmacao falsa sobre o proprio sistema.
     */
    const q = mockQualidade || {};

    const vazio = texto => `<p class="text-sm text-gray-400">${texto}</p>`;

    const cartao = (titulo, corpo, nota) => `
        <section class="surface-card p-6">
            <h3 class="text-xs font-bold uppercase tracking-[.18em] text-gray-500">${titulo}</h3>

            <div class="mt-3">${corpo}</div>

            ${nota ? `<p class="mt-3 text-xs text-gray-400">${nota}</p>` : ''}
        </section>`;

    const tabela = (cabecalhos, linhas) => `
        <table class="w-full text-left text-sm">
            <thead class="text-xs uppercase tracking-wider text-gray-400">
                <tr>${cabecalhos.map(c => `<th class="pb-2 pr-4">${c}</th>`).join('')}</tr>
            </thead>

            <tbody>${linhas.join('')}</tbody>
        </table>`;

    const linha = celulas => `
        <tr class="border-b border-black/5 dark:border-white/5">
            ${celulas.map((c, indice) => `<td class="py-1.5 ${indice ? '' : 'pr-4 font-mono text-xs'}">${c}</td>`).join('')}
        </tr>`;

    return `
        <div class="fade-in-up space-y-6">
            <section class="surface-card p-6">
                <h2 class="text-2xl font-bold tracking-tight">
                    Indicadores de qualidade
                </h2>

                <p class="mt-2 max-w-2xl text-sm leading-6 text-gray-500 dark:text-gray-400">
                    Lidos de <span class="font-mono">/api/qualidade</span> sobre o registro atual.
                    O que nao esta instrumentado aparece como nao instrumentado, com o motivo declarado —
                    ausencia de dado nao vira zero.
                </p>
            </section>


            <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
                ${cartao('Latencia por vista',
                    (q.latencia || []).length
                        ? tabela(['vista', 'medidas', 'media', 'maxima'],
                                 q.latencia.map(l => linha([l.vista, l.medidas, l.media, l.maxima])))
                        : vazio('nenhuma medida com latencia registrada'))}

                ${cartao('Saturacao do recorte',
                    (q.saturacao || []).length
                        ? tabela(['vista', 'medidas', 'media', 'maxima'],
                                 q.saturacao.map(s => linha([s.vista, s.medidas, s.media, s.maxima])))
                        : vazio('nenhuma medida com saturacao registrada'))}

                ${cartao('Gatilho por fonte',
                    (q.gatilho || []).length
                        ? tabela(['fonte', 'eventos', 'aceitos', 'falsos', 'duplicados', 'invalidos', 'taxa falso'],
                                 q.gatilho.map(g => linha([g.fonte, g.eventos, g.aceitos, g.falsos,
                                                           g.duplicados, g.invalidos, g.taxa_falso])))
                        : vazio('nenhum evento de gatilho registrado'),
                    'Duplicado e falso sao contados separados: duplicado e o mesmo item de novo, falso e a '
                    + 'leitura que nao virou item.')}

                ${cartao('Discordancia entre as duas laterais',
                    q.discordancia
                        ? `<p class="text-sm">
                               ${q.discordancia.itens_com_duas_laterais} itens com as duas laterais;
                               ${q.discordancia.discordantes} discordantes
                               (${q.discordancia.taxa === null || q.discordancia.taxa === undefined
                                    ? '--' : `${Math.round(q.discordancia.taxa * 100)}%`})
                           </p>`
                        : vazio('nenhum item com as duas laterais'))}

                ${cartao('Inconclusivos por lote',
                    (q.inconclusivos || []).length
                        ? tabela(['lote', 'motivo', 'ocorrencias'],
                                 q.inconclusivos.map(x => linha([x.lote_id, x.motivo, x.ocorrencias])))
                        : vazio('nenhum inconclusivo registrado por lote'))}

                ${cartao('Perda de deteccao',
                    q.perda && q.perda.instrumentada
                        ? `<p class="text-sm">instrumentada</p>`
                        : vazio('nao instrumentada'),
                    (q.perda && q.perda.motivo) || null)}

                ${cartao('Correcoes para auditoria',
                    (q.correcoes || []).length
                        ? tabela(['item', 'decisao original', 'decisao corrigida', 'por', 'quando'],
                                 q.correcoes.map(c => linha([c.item_id, c.decisao_original,
                                                             c.decisao_corrigida, c.corrigido_por,
                                                             c.timestamp])))
                        : vazio('nenhuma correcao de operador registrada'),
                    (q.separacoes || []).length
                        ? `${q.separacoes.length} separacao(oes) nao confirmada(s)`
                        : null)}

                ${cartao('Saude dos nos de gatilho',
                    (q.nos || []).length
                        ? tabela(['ponto', 'status', 'fila', 'quando'],
                                 q.nos.map(n => linha([n.ponto_id, n.status, n.fila_pendente, n.timestamp])))
                        : vazio('nenhum no de gatilho registrado'))}

                ${cartao('Correlacao ambiental',
                    q.correlacao
                        ? `<p class="text-sm">
                               ${q.correlacao.variavel} em janela de ${q.correlacao.janela_s}s:
                               r = ${q.correlacao.r === null || q.correlacao.r === undefined
                                    ? '--' : Number(q.correlacao.r).toFixed(3)}
                               sobre ${q.correlacao.pares} pares
                           </p>`
                        : vazio('sem par ambiental registrado'),
                    'Correlacao nao e causa: o numero entra aqui como indicador, nao como conclusao.')}
            </div>


            <section class="surface-card p-6">
                <p class="text-sm text-gray-500 dark:text-gray-400">
                    Series temporais agregadas: esta instalacao <span class="font-semibold">nao declara</span>
                    um Grafana, entao o painel nao mostra link para lugar nenhum. Quando o endereco existir,
                    ele entra aqui — botao morto nao entra.
                </p>
            </section>
        </div>`;
};


const renderSaude = () => `
    <div class="fade-in-up space-y-6">

        <section
            class="
                grid

                grid-cols-1

                gap-4

                sm:grid-cols-2
                xl:grid-cols-4
            "
        >

            ${renderMetricCard({
                title: 'Estado geral',
                value: mockHealth.status,
                icon: 'activity',
                type: 'success',
                subtitle: `Heartbeat ${mockHealth.ultimoHeartbeat}`
            })}

            ${renderMetricCard({
                title: 'Temperatura SOC',
                value: mockHealth.temperatura,
                icon: 'thermometer',
                subtitle: mockHealth.temperatura === '--'
                    ? 'sem leitura do sensor (nao ha faixa declarada para julgar)'
                    : 'sensor lido nesta coleta (faixa de alerta nao declarada)'
            })}

            ${renderMetricCard({
                title: 'Carga (1 min)',
                value: mockHealth.cpu,
                icon: 'cpu',
                subtitle: `Memória ${mockHealth.memoria}`
            })}

            ${renderMetricCard({
                title: 'Fila local',
                value: mockHealth.filaImagens,
                icon: 'images',
                subtitle: 'Imagens aguardando processamento'
            })}

        </section>


        <section class="surface-card overflow-hidden">

            <div
                class="
                    flex

                    items-center
                    justify-between

                    border-b
                    border-light-border
                    dark:border-dark-border

                    px-5
                    py-5

                    sm:px-6
                "
            >

                <div>
                    <h2
                        class="
                            text-base
                            font-bold
                        "
                    >
                        Serviços da bancada
                    </h2>

                    <p
                        class="
                            mt-1

                            text-xs
                            text-gray-400
                        "
                    >
                        Conectividade e componentes locais
                    </p>
                </div>

                <span
                    class="
                        flex
                        items-center

                        text-xs
                        font-semibold
                        text-brand-green
                    "
                >
                    <span class="status-dot ${(mockHealth.sem_leitura || []).length === 0
                        ? 'status-success' : 'status-warning'} mr-2"></span>

                    Sistema operacional${(mockHealth.sem_leitura || []).length
                        ? ` (sem leitura: ${mockHealth.sem_leitura.join(', ')})` : ''}
                </span>

            </div>


            <div class="p-3">

                ${mockServices.map(service => `
                    <div
                        class="
                            group

                            flex
                            flex-col

                            justify-between

                            gap-4

                            rounded-2xl

                            p-4

                            transition-colors

                            hover:bg-light-bg
                            dark:hover:bg-dark-bg

                            sm:flex-row
                            sm:items-center
                        "
                    >

                        <div
                            class="
                                flex
                                items-center
                            "
                        >

                            <div
                                class="
                                    flex

                                    h-11
                                    w-11

                                    flex-shrink-0

                                    items-center
                                    justify-center

                                    rounded-xl

                                    border
                                    border-light-border
                                    dark:border-dark-border

                                    bg-white
                                    dark:bg-dark-raised

                                    text-gray-500
                                    dark:text-gray-300
                                "
                            >
                                <i
                                    data-lucide="${service.icon}"

                                    class="
                                        h-5
                                        w-5
                                    "
                                ></i>
                            </div>


                            <div class="ml-4">

                                <div
                                    class="
                                        text-sm
                                        font-bold
                                    "
                                >
                                    ${service.name}
                                </div>

                                <div
                                    class="
                                        mt-1

                                        font-mono
                                        text-xs
                                        text-gray-400
                                    "
                                >
                                    ${service.detail}
                                </div>

                            </div>

                        </div>


                        <span
                            class="
                                status-badge

                                ${
                                    service.state === 'ok'
                                        ? 'status-badge-ok'
                                        : service.state === 'warning'
                                            ? 'status-badge-pending'
                                            : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-300'
                                }
                            "
                        >
                            ${service.status}
                        </span>

                    </div>
                `).join('')}

            </div>

        </section>

    </div>
`;


const renderLote = () => {
    /*
     * Cabecalho e numeros vem dos LOTES do registro. Antes: "#L2024-89" e "14 Out 2024" fixos no
     * template, com os totais GLOBAIS exibidos sob o cabecalho de um lote unico — nem o lote existia.
     */
    /*
     * Ordena por DATA e so depois por id: id de lote e texto, e `LOTE-10` ordena antes de `LOTE-2`
     * (escolher "o mais recente" por ordem alfabetica acerta por acaso quando o padrao e ISO).
     */
    const lotes = (mockLotes || []).slice().sort((a, b) =>
        String(a.data_inicio || '').localeCompare(String(b.data_inicio || ''))
        || String(a.lote_id).localeCompare(String(b.lote_id)));

    const atual = lotes.length ? lotes[lotes.length - 1] : null;
    const pct = valor => valor === null || valor === undefined
        ? '--' : `${Math.round(valor * 100)}%`;

    const metricas = [
        ['Produzidos', atual ? atual.itens : '--'],
        ['Aprovados', atual ? atual.ok : '--'],
        ['Defeitos', atual ? atual.defeitos : '--'],
        ['Taxa', atual ? pct(atual.taxa_defeito) : '--']
    ];

    const linha = lote => `
        <tr class="border-b border-black/5 dark:border-white/5 ${lote === atual ? 'font-semibold' : ''}">
            <td class="py-1.5 pr-4 font-mono text-xs">${lote.lote_id}</td>
            <td class="py-1.5 pr-4">${lote.data_inicio}</td>
            <td class="py-1.5 pr-4">${lote.itens}</td>
            <td class="py-1.5 pr-4">${lote.ok}</td>
            <td class="py-1.5 pr-4">${lote.defeitos}</td>
            <td class="py-1.5 pr-4">${lote.inconclusivos}</td>
            <td class="py-1.5">${pct(lote.taxa_defeito)}</td>
        </tr>`;

    return `
        <div class="fade-in-up space-y-6">
            <section class="surface-card p-6">
                <div class="flex flex-wrap items-start justify-between gap-4">
                    <div>
                        <p class="text-xs font-semibold uppercase tracking-[.18em] text-gray-500">
                            Lote mais recente no registro
                        </p>

                        <h2 class="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
                            ${atual ? atual.lote_id : '(nenhum lote no registro)'}
                        </h2>

                        <p class="mt-2 flex items-center text-sm text-gray-500 dark:text-gray-400">
                            <i data-lucide="calendar-days" class="mr-2 h-4 w-4"></i>

                            ${atual ? atual.data_inicio : '--'} • ate agora
                        </p>
                    </div>


                    <button class="primary-button"
                            ${mockCapturas.length ? 'onclick="app.exportarCSV()"' : 'disabled'}>
                        <i data-lucide="download" class="mr-2 h-4 w-4"></i>

                        Exportar CSV
                    </button>
                </div>


                <div class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
                    ${metricas.map(([titulo, valor]) => `
                        <div>
                            <p class="text-xs font-semibold uppercase tracking-[.18em] text-gray-500">
                                ${titulo}
                            </p>

                            <p class="mt-1 text-2xl font-bold">${valor}</p>
                        </div>`).join('')}
                </div>


                <p class="mt-4 text-xs text-gray-400">
                    Numeros do lote ${atual ? atual.lote_id : '--'} — nao os totais de todos os lotes.
                    O resumo do registro inteiro fica na vista Operacao.
                </p>
            </section>


            <section class="surface-card p-6">
                <h3 class="text-xs font-bold uppercase tracking-[.18em] text-gray-500">
                    Todos os lotes no registro
                </h3>

                <div class="mt-3">
                    ${lotes.length
                        ? `<table class="w-full text-left text-sm">
                               <thead class="text-xs uppercase tracking-wider text-gray-400">
                                   <tr>
                                       <th class="pb-2 pr-4">lote</th>
                                       <th class="pb-2 pr-4">inicio</th>
                                       <th class="pb-2 pr-4">itens</th>
                                       <th class="pb-2 pr-4">ok</th>
                                       <th class="pb-2 pr-4">defeitos</th>
                                       <th class="pb-2 pr-4">inconclusivos</th>
                                       <th class="pb-2">taxa</th>
                                   </tr>
                               </thead>

                               <tbody>${lotes.map(linha).join('')}</tbody>
                           </table>`
                        : '<p class="text-sm text-gray-400">nenhum lote registrado</p>'}
                </div>


                <p class="mt-4 text-xs text-gray-400">
                    Soma dos lotes: ${lotes.reduce((soma, l) => soma + (l.itens || 0), 0)} itens —
                    o resumo do registro declara ${mockStats.totalLote ?? '--'}.
                </p>
            </section>


            <section class="surface-card p-6">
                <h3 class="text-xs font-bold uppercase tracking-[.18em] text-gray-500">
                    Modulos do relatorio
                </h3>

                <div class="mt-3 space-y-2 text-sm">
                    <p>
                        <span class="font-semibold">Resumo estatistico</span> — disponivel
                        (<span class="font-mono text-xs">/api/lotes</span> e
                        <span class="font-mono text-xs">/api/resumo</span>)
                    </p>

                    <p>
                        <span class="font-semibold">Excecoes</span> — disponivel
                        (<span class="font-mono text-xs">/api/capturas</span>, linhas com defeito ou
                        inconclusivas)
                    </p>

                    <p>
                        <span class="font-semibold">Assinatura digital</span> — pendente: nao existe
                        assinatura no registro, entao o relatorio nao se declara assinado
                    </p>
                </div>


                <p class="mt-4 text-xs text-gray-400">
                    Este painel mostra os dados consolidados deste registro. Series temporais
                    corporativas nao estao declaradas nesta instalacao.
                </p>
            </section>
        </div>`;
};
