#!/usr/bin/env bash

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CONTEXT="$HERE/.."

# username of the owner of the images
ghcr_user=${ghcr_user:-edomora97}

set -ex

cd $CONTEXT

# Build the base image
docker build \
    -t ghcr.io/$ghcr_user/cms-base \
    -f docker/base/Dockerfile \
    .

# Build the core image
docker build \
    -t ghcr.io/$ghcr_user/cms-core \
    -f docker/core/Dockerfile \
    .

# Build the cws image
docker build \
    -t ghcr.io/$ghcr_user/cms-cws \
    -f docker/cws/Dockerfile \
    .

# Build the worker image
docker build \
    -t ghcr.io/$ghcr_user/cms-worker \
    -f docker/worker/Dockerfile \
    .

# Build the rws image
docker build \
    -t ghcr.io/$ghcr_user/cms-rws \
    -f docker/rws/Dockerfile \
    .
