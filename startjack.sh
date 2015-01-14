#!/bin/bash

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
