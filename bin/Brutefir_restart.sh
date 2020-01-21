#!/bin/bash

# keep this named Brutefir_restart.sh in order to avoid self killing

if [[ $1 == *'-h'* ]]; then
    echo "Usage:"
    echo "    Brutefir_restart.sh  [stop]"
    exit 0
fi
if [[ $(jack_lsp) == *"brutefir"* ]]; then
    echo "killing"
    pkill brutefir
fi
if [[ $1 == 'stop' ]]; then
    exit 0
fi

# Restarting
sleep .5
echo "Restarting"
cd /home/predic/pe.audio.sys/loudspeakers/SeasFlat/
brutefir brutefir_config 1>/dev/null 2>&1 &
cd

# Wait until Brutefir ports becomes active
max=60
echo "Waiting for Brutefir ports to become active"
while true; do
    echo -n .
    sleep 1
    # Brutefir will auto connect its outputs to system_playback ports
    if [[ $(jack_lsp -c brutefir) == *"system"* ]]; then
        sleep .1
        break
    fi
    if [[ "$max" -eq "0" ]]; then
        echo 'Timed out :-/'
        break
    fi
    (( max -= 1 ))
done

# Connecting Brutefir to preamp
echo "Connecting Brutefir to preamp"
jack_connect   brutefir:in.L   pre_in_loop:output_1
jack_connect   brutefir:in.R   pre_in_loop:output_2
