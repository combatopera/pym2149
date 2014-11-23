#!/bin/bash

cd ..

hg clone https://bitbucket.org/combatopera/devutils

cd -

cd

wget http://repo.continuum.io/miniconda/Miniconda-3.0.5-Linux-x86_64.sh

bash Miniconda-3.0.5-Linux-x86_64.sh <<<$'\nyes\nminiconda\nno\n'

PATH="$PWD/miniconda/bin:$PATH"

cd -

conda install numpy cython pyflakes nose

./tests
