FROM ghcr.io/edomora97/cms-base

LABEL org.opencontainers.image.source=https://github.com/edomora97/cms
LABEL maintainer="Edoardo Morassutto <edoardo.morassutto@gmail.com>"

COPY docker/rws/root /

ENV CMS_RANKING_CONFIG=/config/cms.ranking.conf
EXPOSE 8890
