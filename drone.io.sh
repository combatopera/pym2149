#!/bin/bash

set -ex

pwd

cd ..

hg clone https://bitbucket.org/combatopera/devutils

cd -

cd; pwd

wget http://repo.continuum.io/miniconda/Miniconda-3.0.5-Linux-x86_64.sh

bash Miniconda-3.0.5-Linux-x86_64.sh <<<$'\nyes\nminiconda\nno\n'

PATH="$PWD/miniconda/bin:$PATH"

cd -

conda install openssl=1.0.1h numpy cython pyflakes nose mock python=2.7.9-1

./tests
