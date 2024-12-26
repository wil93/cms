#!/usr/bin/env bash

./cms/testsuite/scripts/reinit.sh \
    && ./cms/testsuite/scripts/fake_enable.sh \
    && ./cms/testsuite/RunTimeTest.py -w 16 -s 100 -l 'EvaluationService:20';
./cms/testsuite/scripts/fake_disable.sh
