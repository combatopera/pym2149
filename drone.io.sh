#!/bin/bash

cd ..

hg clone https://bitbucket.org/combatopera/devutils

cd -

cd

wget http://repo.continuum.io/miniconda/Miniconda-3.0.5-Linux-x86_64.sh

yes | bash Miniconda-3.0.5-Linux-x86_64.sh

PATH="$PWD/y/bin:$PATH"

cd -

conda install numba nose

./tests
