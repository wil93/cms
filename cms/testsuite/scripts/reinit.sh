#!/usr/bin/env bash

./scripts/cmsDropDB -y \
    && ./scripts/cmsInitDB \
    && ./cms.contrib/AddAdmin.py myadmin -p admin
