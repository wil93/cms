#!/usr/bin/env bash

set -e

ghcr_user="edomora97"
tag="latest"

usage() {
    echo "Build and tag the docker images"
    echo "$0 [-u username] [-t tag]"
    echo "   -u username   ghcr.io username"
    echo "   -t tag        tag to use for the images"
}

while getopts "ht:u:" opt; do
    case "$opt" in
        t) tag="$OPTARG";;
        u) ghcr_user="$OPTARG";;
        *) usage
           exit 0
           ;;
    esac
done

components=(base core cws worker rws)

for comp in "${components[@]}"; do
    image="ghcr.io/$ghcr_user/cms-$comp"
    docker push "$image:$tag"
done
