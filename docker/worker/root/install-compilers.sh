#!/usr/bin/env bash

set -ex

apt update
apt install -yy \
    fp-compiler \
    pypy3 \
    openjdk-17-jdk

# Cleanup
rm -rf /var/lib/apt/lists/*
