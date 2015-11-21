#!/bin/bash

# Copyright 2014 Andrzej Cichocki

# This file is part of pym2149.
#
# pym2149 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pym2149 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pym2149.  If not, see <http://www.gnu.org/licenses/>.

set -ex

find -name '*.pyc' -exec rm -fv '{}' +

find -name '*.so' -exec rm -fv '{}' +

find -name '*.dsd' -exec rm -fv '{}' +

find -name '*.c' -exec rm -fv '{}' +

find -name 'turbo_*.pyx' -exec rm -fv '{}' +

rm -fv pym2149/cpaste?*.pyx

rm -fv pym2149/'MinBleps('*')'

rm -rfv target

hg st -A | grep -v ^C
