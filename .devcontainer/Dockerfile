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
