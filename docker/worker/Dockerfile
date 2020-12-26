FROM ghcr.io/edomora97/cms-base

LABEL org.opencontainers.image.source https://github.com/edomora97/cms
LABEL maintainer="Edoardo Morassutto <edoardo.morassutto@gmail.com>"

COPY docker/worker/root /

# Install compilers
RUN /install-compilers.sh