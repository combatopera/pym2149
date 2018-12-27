#!/bin/bash

# Copyright 2014, 2018 Andrzej Cichocki

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

set -e

if [[ $# -ge 1 ]]; then
    export PYM2149_CONFIG="$(python -c "import os; print os.path.basename(os.path.dirname(os.path.abspath('$1')))")"
fi

cd "$(dirname "$(readlink -f "$0")")"

./startjack.sh

pidof renoise || (
    cd - >/dev/null
    renoise "$@" &>/dev/null
) &

./midi2jack.py
