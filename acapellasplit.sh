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

set -e

bpm=100
lpb=8
lpp=128
gain=12

path="$1"
total=$(soxi -D "$path")

chunktimes=($(python -c "from __future__ import division
lpm = $lpb * $bpm
i = 0
while True:
    t = i * 60 * $lpp / lpm
    print t
    if t >= $total:
        break
    i += 1
"))

function decimaldigits {
    local digits=1 minval=1
    while [[ $1 -ge $minval ]]; do
        digits=$((digits + 1))
        minval=${minval}0
    done
    echo $((digits - 1))
}

function doit {
    local prefix="${path%.*}-" format part=0 extension=".${path##*.}"
    format="%0$(decimaldigits $(($# - 2)))d" # Arg count less 2 is max value for part.
    while [[ $# -ge 2 ]]; do
        echo part $part from $1 to $2 >&2
        sox "$path" "$prefix$(printf "$format" $part)$extension" trim $1 =$2 vol ${gain}dB
        shift
        part=$((part + 1))
    done
}

doit ${chunktimes[@]}
