#!/bin/bash

set -ex

find -name '*.pyc' -exec rm -fv '{}' +

find -name '*.so' -exec rm -fv '{}' +

find -name '*.dsd' -exec rm -fv '{}' +

hg st -A | grep -v ^C
