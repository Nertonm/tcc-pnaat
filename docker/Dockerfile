# Imagem única dos três serviços do tcc-pnaat (api, rig, ponte).
# Base python:3.11-slim: o pacote exige Python >= 3.11 e < 3.13 (src-production/pyproject.toml).
#
# Build a partir da RAIZ do repositório (o docker-compose.yml já aponta context: ..;
# o .dockerignore da raiz exclui .venv, dataset, models e .git da imagem).
#
#   docker build -f docker/Dockerfile -t tcc-pnaat:local .
#   # usuário não-root é o padrão (app, uid 1000); para rodar como root:
#   docker build --build-arg RUN_AS=root -f docker/Dockerfile -t tcc-pnaat:local .

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Usuário não-root opcional. RUN_AS=root desliga o downgrade (build-arg); default é app (uid 1000).
ARG RUN_AS=app
RUN groupadd --gid 1000 app && useradd --uid 1000 --gid app --create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Cópia do repositório inteiro; o .dockerignore na raiz remove o que a imagem não usa.
COPY . /app

# Pacote + extras: serial (pyserial), leitura (Pillow/scipy), inferencia (torch/ultralytics),
# dev (pytest/ruff). O layout flat (py-modules) instala cada módulo como top-level no
# site-packages, então api.py, rig_service/app.py e esp32cam_site.py resolvem imports irmãos.
RUN python -m pip install --upgrade pip && \
    python -m pip install "src-production[dev,leitura,serial,inferencia]"

# hub.db vive em /data (volume nomeado hub-db no compose). Pré-criado com o dono do usuário app:
# ao montar um volume nomeado vazio sobre /data o Docker copia conteúdo e ownership do diretório
# da imagem, e o serviço grava sem chown manual.
RUN mkdir -p /data && chown -R 1000:1000 /data

# CMD padrão: gateway/API, o núcleo que sobe sem hardware (cria o schema do hub.db no /api/health).
# --host fora do loopback exige token; a API lê PNAAT_API_TOKEN sozinha (ver api.py:1694).
CMD ["python", "src-production/api.py", "--db", "/data/hub.db", "--porta", "8080", "--host", "0.0.0.0"]

USER ${RUN_AS}