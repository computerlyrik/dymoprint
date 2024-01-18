FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

ARG deps="\
    libdbus-1-3 \
    libegl1 \
    libgl1 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-keysyms1 \
    libxcb-shape0 \
    libxkbcommon-x11-0 \
    "

RUN apt-get update \
    && apt-get install -y ${deps} \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip \
    && pip install pre-commit ruff

# Preinstall the dependencies (extremely hacky)
COPY ../pyproject.toml /tmp/temp-project/pyproject.toml
RUN touch /tmp/temp-project/README.md \
    && cd /tmp/temp-project \
    && git init \
    && mkdir -p src/dymoprint \
    && echo '__version__ = "0.0.0"' > src/dymoprint/_version.py \
    && pip install -e . \
    && pip uninstall -y dymoprint \
    && rm -rf /tmp/temp-project
