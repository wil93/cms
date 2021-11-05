#!/usr/bin/env bash

set -ex

apt update
apt install -yy \
    fp-compiler \
    pypy3

# Cleanup
rm -rf /var/lib/apt/lists/*
