FROM ghcr.io/linuxserver/baseimage-alpine:3.11 as initial

# Install build dependencies
RUN apk add --no-cache --virtual=build-dependencies \
	autoconf \
	automake \
	cups-dev \
	freetype-dev \
	g++ \
	gcc \
	libffi-dev \
	libcap-dev \
	linux-headers \
	make \
	openssl-dev \
	postgresql-dev \
	python3-dev \
	tiff-dev \
	zlib-dev

# Install runtime dependencies
RUN apk add --no-cache \
	postgresql-client \
	libcap \
	libpq \
	py3-pip \
	python3 \
	zip

# Install python dependencies
COPY requirements.txt /cms/
WORKDIR /cms
RUN pip3 install --no-cache-dir -U pip && \
	pip3 install --no-cache-dir -r requirements.txt

# Copy all but docker/
# Dirty hacks waiting for:
# - https://github.com/moby/moby/issues/15771
# - https://github.com/moby/moby/issues/37965
COPY *.py *.txt *.cfg /cms/
RUN true
COPY cms /cms/cms/
RUN true
COPY cmscommon /cms/cmscommon/
RUN true
COPY cmscontrib /cms/cmscontrib/
RUN true
COPY cmsranking /cms/cmsranking/
RUN true
COPY cmstaskenv /cms/cmstaskenv/
RUN true
COPY cmstestsuite /cms/cmstestsuite/
RUN true
COPY config /cms/config/
RUN true
COPY isolate /cms/isolate/
RUN true
COPY scripts /cms/scripts/
RUN true

# Install cms
RUN python3 prerequisites.py --yes --no-conf --as-root install && \
	python3 setup.py install

# Cleanup
RUN apk del --purge build-dependencies && \
	rm -rf /root/.cache /tmp/*

# Copy base configuration files
COPY docker/base/root /

# Multi-stage build merging all the layers from the previous step
FROM alpine:3.11
LABEL org.opencontainers.image.source https://github.com/edomora97/cms
LABEL maintainer="Edoardo Morassutto <edoardo.morassutto@gmail.com>"

COPY --from=initial / /
WORKDIR /cms

ENV CMS_CONFIG=/config/cms.conf
VOLUME ["/config"]
ENTRYPOINT ["/init"]