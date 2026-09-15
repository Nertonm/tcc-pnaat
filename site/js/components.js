const statusBadge = status => {
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

            ${status}
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
    const total =
        mockStats.aprovados +
        mockStats.reprovados;

    const approvedPercentage =
        (
            mockStats.aprovados /
            total *
            100
        ).toFixed(1);

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
                    subtitle: `
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

                            +12%
                        </span>

                        <span class="ml-1">
                            desde ontem
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

                        do lote atual
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
                            3 eventos
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
                            .slice()
                            .reverse()
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
                                        #L2024-89
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
                                        Processamento
                                    </span>

                                    <span class="font-semibold">
                                        450 itens
                                    </span>
                                </div>

                                <div class="progress-track">

                                    <div
                                        class="
                                            progress-fill

                                            bg-brand-red
                                        "

                                        style="width: 72%"
                                    ></div>

                                </div>

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

                    <option value="Topo">
                        Topo
                    </option>

                    <option value="Lateral">
                        Lateral
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
                    ${mockCapturas.length} registros exibidos
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
                Todas ${mockCapturas.length}
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
                OK ${mockCapturas.filter(item => item.status === 'OK').length}
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
                Defeitos ${mockCapturas.filter(item => item.status === 'Defeito').length}
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
                Pendentes ${mockCapturas.filter(item => item.status === 'Pendente').length}
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
                    data-view="${cap.vista}"
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
                            alt="${cap.id}"
                        >


                        <div
                            class="
                                absolute

                                left-3
                                top-3
                            "
                        >
                            ${statusBadge(cap.status)}
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


const renderInvestigacao = id => {
    const cap =
        mockCapturas.find(item => item.id === id) ||
        mockCapturas.find(item => item.status === 'Defeito') ||
        mockCapturas[0];

    return `
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


                            ${
                                cap.status === 'Defeito'
                                    ? `
                                        <div
                                            class="
                                                absolute

                                                border-2
                                                border-brand-red

                                                bg-brand-red/10
                                            "

                                            style="
                                                left: 40%;
                                                top: 31%;
                                                width: 21%;
                                                height: 26%;
                                            "
                                        >

                                            <div
                                                class="
                                                    absolute

                                                    -top-7
                                                    left-[-2px]

                                                    rounded-t-md

                                                    bg-brand-red

                                                    px-2
                                                    py-1

                                                    text-[10px]
                                                    font-bold
                                                    text-white
                                                "
                                            >
                                                RISCO ${cap.confianca}
                                            </div>

                                        </div>
                                    `
                                    : ''
                            }

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
                                    src="https://placehold.co/400x300/171A1D/F9FBFD?text=Outra+Vista"

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


                            <div
                                class="
                                    mt-5

                                    space-y-3
                                "
                            >

                                <button
                                    class="
                                        success-button
                                        w-full
                                    "
                                >
                                    <i
                                        data-lucide="circle-check"

                                        class="
                                            mr-2
                                            h-4
                                            w-4
                                        "
                                    ></i>

                                    Forçar aprovação
                                </button>


                                <button
                                    class="
                                        danger-button
                                        w-full
                                    "
                                >
                                    <i
                                        data-lucide="triangle-alert"

                                        class="
                                            mr-2
                                            h-4
                                            w-4
                                        "
                                    ></i>

                                    Confirmar defeito
                                </button>

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
                                    data-lucide="lock-keyhole"

                                    class="
                                        mr-1.5
                                        h-3.5
                                        w-3.5
                                    "
                                ></i>

                                Requer privilégio administrativo
                            </div>

                        </div>

                    </section>

                </aside>

            </div>

        </div>
    `;
};


const renderQualidade = () => `
    <div class="fade-in-up">

        <section
            class="
                surface-card

                mx-auto

                max-w-3xl

                p-8
                sm:p-10
            "
        >

            <div
                class="
                    flex

                    h-14
                    w-14

                    items-center
                    justify-center

                    rounded-2xl

                    bg-brand-red/10

                    text-brand-red
                "
            >
                <i
                    data-lucide="chart-no-axes-combined"

                    class="
                        h-6
                        w-6
                    "
                ></i>
            </div>


            <div class="mt-6">

                <span
                    class="
                        text-[10px]
                        font-semibold
                        uppercase
                        tracking-[.16em]

                        text-brand-red
                    "
                >
                    SITE-10
                </span>

                <h2
                    class="
                        mt-2

                        text-2xl
                        font-bold
                        tracking-tight
                    "
                >
                    Integração de qualidade
                </h2>

                <p
                    class="
                        mt-3

                        max-w-xl

                        text-sm
                        leading-6
                        text-gray-500
                        dark:text-gray-400
                    "
                >
                    As séries estatísticas agregadas permanecem reservadas
                    ao Grafana. Este painel será responsável pelo acesso
                    aos indicadores e pela ligação com as evidências
                    mantidas no PNAAT.
                </p>

            </div>


            <div
                class="
                    mt-8

                    grid

                    grid-cols-1
                    gap-4

                    sm:grid-cols-3
                "
            >

                <div
                    class="
                        rounded-2xl

                        bg-light-bg
                        dark:bg-dark-bg

                        p-5
                    "
                >
                    <i
                        data-lucide="pie-chart"

                        class="
                            h-5
                            w-5

                            text-gray-400
                        "
                    ></i>

                    <div
                        class="
                            mt-4

                            text-sm
                            font-bold
                        "
                    >
                        Defeitos
                    </div>

                    <div
                        class="
                            mt-1

                            text-xs
                            text-gray-400
                        "
                    >
                        Códigos e severidade
                    </div>
                </div>


                <div
                    class="
                        rounded-2xl

                        bg-light-bg
                        dark:bg-dark-bg

                        p-5
                    "
                >
                    <i
                        data-lucide="scan-line"

                        class="
                            h-5
                            w-5

                            text-gray-400
                        "
                    ></i>

                    <div
                        class="
                            mt-4

                            text-sm
                            font-bold
                        "
                    >
                        Registros
                    </div>

                    <div
                        class="
                            mt-1

                            text-xs
                            text-gray-400
                        "
                    >
                        Parcial ou ausente
                    </div>
                </div>


                <div
                    class="
                        rounded-2xl

                        bg-light-bg
                        dark:bg-dark-bg

                        p-5
                    "
                >
                    <i
                        data-lucide="user-check"

                        class="
                            h-5
                            w-5

                            text-gray-400
                        "
                    ></i>

                    <div
                        class="
                            mt-4

                            text-sm
                            font-bold
                        "
                    >
                        Correções
                    </div>

                    <div
                        class="
                            mt-1

                            text-xs
                            text-gray-400
                        "
                    >
                        Histórico humano
                    </div>
                </div>

            </div>


            <div
                class="
                    mt-8

                    flex
                    flex-col

                    gap-3

                    sm:flex-row
                "
            >

                <button class="primary-button">
                    <i
                        data-lucide="external-link"

                        class="
                            mr-2
                            h-4
                            w-4
                        "
                    ></i>

                    Abrir Grafana
                </button>

                <button class="secondary-button">
                    Integração pendente
                </button>

            </div>

        </section>

    </div>
`;


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
                subtitle: 'Faixa de operação normal'
            })}

            ${renderMetricCard({
                title: 'CPU',
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
                    <span class="status-dot status-success mr-2"></span>

                    Sistema operacional
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


const renderLote = () => `
    <div
        class="
            fade-in-up

            mx-auto

            max-w-6xl

            space-y-6
        "
    >

        <section
            class="
                surface-card

                relative
                overflow-hidden

                p-6
                sm:p-8
            "
        >

            <div
                class="
                    pointer-events-none

                    absolute

                    -right-20
                    -top-20

                    h-64
                    w-64

                    rounded-full

                    bg-brand-red/5

                    blur-3xl
                "
            ></div>


            <div
                class="
                    relative

                    flex
                    flex-col

                    gap-6

                    sm:flex-row
                    sm:items-center
                    sm:justify-between
                "
            >

                <div>

                    <div
                        class="
                            flex
                            flex-wrap
                            items-center

                            gap-3
                        "
                    >

                        <h2
                            class="
                                text-2xl
                                font-bold
                                tracking-tight

                                sm:text-3xl
                            "
                        >
                            Lote #L2024-89
                        </h2>

                        <span
                            class="
                                rounded-full

                                bg-brand-green/10

                                px-3
                                py-1.5

                                text-xs
                                font-bold
                                text-brand-green
                            "
                        >
                            Em andamento
                        </span>

                    </div>


                    <p
                        class="
                            mt-2

                            flex
                            items-center

                            text-sm
                            text-gray-500
                            dark:text-gray-400
                        "
                    >
                        <i
                            data-lucide="calendar-days"

                            class="
                                mr-2
                                h-4
                                w-4
                            "
                        ></i>

                        14 Out 2024 • 08:00 até agora
                    </p>

                </div>


                <button class="primary-button">
                    <i
                        data-lucide="download"

                        class="
                            mr-2
                            h-4
                            w-4
                        "
                    ></i>

                    Exportar CSV
                </button>

            </div>


            <div
                class="
                    relative

                    mt-8

                    grid

                    grid-cols-2
                    gap-4

                    lg:grid-cols-4
                "
            >

                <div
                    class="
                        rounded-2xl

                        bg-light-bg
                        dark:bg-dark-bg

                        p-5
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
                        Produzidos
                    </div>

                    <div
                        class="
                            mt-2

                            text-2xl
                            font-bold
                        "
                    >
                        ${mockStats.totalLote}
                    </div>
                </div>


                <div
                    class="
                        rounded-2xl

                        bg-light-bg
                        dark:bg-dark-bg

                        p-5
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
                        Aprovados
                    </div>

                    <div
                        class="
                            mt-2

                            text-2xl
                            font-bold
                            text-brand-green
                        "
                    >
                        ${mockStats.aprovados}
                    </div>
                </div>


                <div
                    class="
                        rounded-2xl

                        bg-light-bg
                        dark:bg-dark-bg

                        p-5
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
                        Defeitos
                    </div>

                    <div
                        class="
                            mt-2

                            text-2xl
                            font-bold
                            text-brand-red
                        "
                    >
                        ${mockStats.reprovados}
                    </div>
                </div>


                <div
                    class="
                        rounded-2xl

                        bg-light-bg
                        dark:bg-dark-bg

                        p-5
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
                        Taxa
                    </div>

                    <div
                        class="
                            mt-2

                            text-2xl
                            font-bold
                        "
                    >
                        ${mockStats.taxaDefeito}
                    </div>
                </div>

            </div>

        </section>


        <section class="surface-card overflow-hidden">

            <div
                class="
                    border-b
                    border-light-border
                    dark:border-dark-border

                    px-5
                    py-5

                    sm:px-6
                "
            >
                <h3
                    class="
                        text-base
                        font-bold
                    "
                >
                    Módulos do relatório
                </h3>

                <p
                    class="
                        mt-1

                        text-xs
                        text-gray-400
                    "
                >
                    Situação dos itens previstos no SITE-09
                </p>
            </div>


            <div class="overflow-x-auto">

                <table class="app-table">

                    <thead>
                        <tr>
                            <th>
                                Recurso
                            </th>

                            <th>
                                Descrição
                            </th>

                            <th class="text-right">
                                Estado
                            </th>
                        </tr>
                    </thead>


                    <tbody>

                        <tr>
                            <td class="font-semibold">
                                Resumo estatístico
                            </td>

                            <td class="text-gray-500 dark:text-gray-400">
                                Consolidação básica do lote atual
                            </td>

                            <td>
                                <div class="flex justify-end">
                                    <span class="status-badge status-badge-ok">
                                        Disponível
                                    </span>
                                </div>
                            </td>
                        </tr>


                        <tr>
                            <td class="font-semibold">
                                Exceções
                            </td>

                            <td class="text-gray-500 dark:text-gray-400">
                                Capturas defeituosas e pendentes
                            </td>

                            <td>
                                <div class="flex justify-end">
                                    <span class="status-badge status-badge-ok">
                                        Disponível
                                    </span>
                                </div>
                            </td>
                        </tr>


                        <tr>
                            <td class="font-semibold">
                                Assinatura digital
                            </td>

                            <td class="text-gray-500 dark:text-gray-400">
                                Integridade e autenticação do relatório
                            </td>

                            <td>
                                <div class="flex justify-end">
                                    <span
                                        class="
                                            status-badge

                                            bg-gray-100
                                            text-gray-500

                                            dark:bg-gray-800
                                            dark:text-gray-300
                                        "
                                    >
                                        Pendente
                                    </span>
                                </div>
                            </td>
                        </tr>

                    </tbody>

                </table>

            </div>

        </section>


        <div
            class="
                flex

                items-start

                rounded-2xl

                border
                border-blue-100
                dark:border-blue-900/30

                bg-blue-50
                dark:bg-blue-900/10

                p-4
            "
        >

            <i
                data-lucide="info"

                class="
                    mr-3
                    mt-0.5

                    h-5
                    w-5

                    flex-shrink-0

                    text-blue-500
                "
            ></i>

            <p
                class="
                    text-sm
                    leading-relaxed

                    text-blue-700
                    dark:text-blue-400
                "
            >
                Este painel representa apenas os dados consolidados
                localmente. Séries temporais corporativas permanecem
                destinadas ao Grafana.
            </p>

        </div>

    </div>
`;