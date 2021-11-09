#!/usr/bin/env bash

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CONTEXT="$HERE/.."

# username of the owner of the images
ghcr_user=${ghcr_user:-edomora97}
tag=${tag:-latest}

set -ex

cd $CONTEXT

# Build the base image
docker build \
    -t ghcr.io/$ghcr_user/cms-base:$tag \
    -f docker/base/Dockerfile \
    .

# Build the core image
docker build \
    -t ghcr.io/$ghcr_user/cms-core:$tag \
    -f docker/core/Dockerfile \
    .

# Build the cws image
docker build \
    -t ghcr.io/$ghcr_user/cms-cws:$tag \
    -f docker/cws/Dockerfile \
    .

# Build the worker image
docker build \
    -t ghcr.io/$ghcr_user/cms-worker:$tag \
    -f docker/worker/Dockerfile \
    .

# Build the rws image
docker build \
    -t ghcr.io/$ghcr_user/cms-rws:$tag \
    -f docker/rws/Dockerfile \
    .
