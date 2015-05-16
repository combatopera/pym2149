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

seconds=5
blurb="$seconds second delay: "

pidof jackd || {

    qjackctl -s &>/dev/null &

    echo -n "$blurb"
    for s in $(seq 1 $seconds); do
        echo -n $'\u2591'
    done
    echo -n $'\r'"$blurb"

    for s in $(seq 1 $seconds); do

        sleep 1

        echo -n $'\u2588'

    done

    echo

}
