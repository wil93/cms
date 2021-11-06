FROM ghcr.io/linuxserver/baseimage-ubuntu:focal as initial

# Install build dependencies
RUN apt update
RUN apt install -yy \
	build-essential \
	postgresql-client \
	python3-dev \
	cgroup-lite \
	libcap-dev \
	zip \
	libpq-dev \
	libcups2-dev \
	libyaml-dev \
	libffi-dev \
	python3-pip

# Install python dependencies
COPY requirements.txt /cms/
WORKDIR /cms
RUN pip3 install --no-cache-dir -U pip && \
	pip3 install --no-cache-dir -r requirements.txt

# Copy source files
COPY . /cms

# Install cms
RUN make -C isolate clean
RUN python3 prerequisites.py --yes --no-conf --as-root install && \
	python3 setup.py install

# Cleanup
RUN rm -rf \
	/var/lib/apt/lists/* \
	/tmp \
	/root/.cache

# Copy base configuration files
COPY docker/base/root /

# Multi-stage build merging all the layers from the previous step
FROM ghcr.io/linuxserver/baseimage-ubuntu:focal
LABEL org.opencontainers.image.source https://github.com/edomora97/cms
LABEL maintainer="Edoardo Morassutto <edoardo.morassutto@gmail.com>"

COPY --from=initial / /
WORKDIR /cms

ENV CMS_CONFIG=/config/cms.conf
VOLUME ["/config"]
ENTRYPOINT ["/init"]
