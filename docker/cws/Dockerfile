FROM ghcr.io/edomora97/cms-base

LABEL org.opencontainers.image.source https://github.com/edomora97/cms
LABEL maintainer="Edoardo Morassutto <edoardo.morassutto@gmail.com>"

RUN \
 wget "https://upload.cppreference.com/mwiki/images/b/b2/html_book_20190607.zip" -O /tmp/cppreference.zip && \
 unzip -q /tmp/cppreference.zip -d /defaults/doc && \
 rm -rf /tmp/cppreference.zip

COPY docker/cws/root /

ENV CMS_CONTEST_ID=
EXPOSE 8888