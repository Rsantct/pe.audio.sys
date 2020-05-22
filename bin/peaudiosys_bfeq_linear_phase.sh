#!/bin/bash

if [[ $1 ]]; then

    if [[ $1 == *"true"* || $1 == *"false"* ]]; then
        new="$1"
    elif [[ $1 == *"toggle"* ]]; then
        curr=$(grep "bfeq_linear_phase:" "$HOME"/pe.audio.sys/config.yml)
        curr=$(echo "$curr" | cut -d ":" -f 2)
        if [[ $curr == *"true"* ]]; then
            new='false'
        else
            new='true'
        fi
    else
        echo "Usage: peaudiosys_bfeq_linear_phase.sh  toggle | true | false"
        exit 0
    fi
else
    echo "Usage: peaudiosys_bfeq_linear_phase.sh  toggle | true | false"
    exit 0
fi

# Editing config.yml
sed -i -e '/bfeq_linear_phase/c\bfeq_linear_phase: '$new \
    "$HOME"/pe.audio.sys/config.yml

# Restarting
peaudiosys_service_restart.sh preamp \
    && sleep 2 && control level 0 add \
    && control get_eq
