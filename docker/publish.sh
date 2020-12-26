#!/usr/bin/env bash

# username of the owner of the images
ghcr_user=${ghcr_user:-edomora97}

set -ex

docker push ghcr.io/$ghcr_user/cms-base
docker push ghcr.io/$ghcr_user/cms-core
docker push ghcr.io/$ghcr_user/cms-cws
docker push ghcr.io/$ghcr_user/cms-worker
docker push ghcr.io/$ghcr_user/cms-rws