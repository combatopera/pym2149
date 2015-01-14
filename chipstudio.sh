#!/bin/bash

set -e

cd "$(dirname "$(readlink -f "$0")")"

./startjack.sh &

. ./loadenv

wait

pidof renoise || {
    renoise &>/dev/null &
}

./midi2jack.py
