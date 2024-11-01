FROM ghcr.io/edomora97/cms-base

LABEL org.opencontainers.image.source=https://github.com/edomora97/cms
LABEL maintainer="Edoardo Morassutto <edoardo.morassutto@gmail.com>"

RUN apt update && \
    apt install -yy \
        fp-compiler \
        pypy3 \
        openjdk-17-jdk \
        mono-devel && \
    rm -r /var/lib/apt/lists/*

COPY docker/worker/root /
