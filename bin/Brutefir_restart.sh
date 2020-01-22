#!/bin/bash

# (i) keep this named "Brutefir_restart.sh" in order to avoid self killing

# FOA retrieving the needed Brutefir attenuation:
ref_level=$( grep 'ref_level_gain:' "${HOME}"/pe.audio.sys/config.yml | sed s/\ \ //g | \
             cut -d':' -f 2)
level=$( grep 'level:' "${HOME}"/pe.audio.sys/.state.yml | sed s/\ \ //g | cut -d':' -f 2)
balance=$( grep 'balance:' "${HOME}"/pe.audio.sys/.state.yml | sed s/\ \ //g | cut -d':' -f 2)
gain=$( echo "($level + $ref_level)" | bc )
gain_L=$( echo "($gain - $balance / 2.0)" | bc -l )
gain_R=$( echo "($gain + $balance / 2.0)" | bc -l )
# multiplier to be applied under Brutefir
m_gain_L=$(printf %.6f $( echo "e( l(10) * ($gain_L / 20.0) )" | bc -l ))
m_gain_R=$(printf %.6f $( echo "e( l(10) * ($gain_R / 20.0) )" | bc -l ))

# Somo help
if [[ $1 == *'-h'* ]]; then
    echo "Usage:"
    echo "    Brutefir_restart.sh  [stop]"
    exit 0
fi

# Kill Brufefir
if [[ $(jack_lsp) == *"brutefir"* ]]; then
    echo "killing"
    pkill brutefir
fi

# Exiting if only stop
if [[ $1 == 'stop' ]]; then
    exit 0
fi

# Restarting
sleep .5
echo "Restarting"
cd /home/predic/pe.audio.sys/loudspeakers/SeasFlat/
brutefir brutefir_config 1>/dev/null 2>&1 &
cd
sleep 1

# Setting the needed attenuation on Brutefir stages:
cmd_L='cffa "f.drc.L" "f.eq.L" m'"$m_gain_L"
cmd_R='cffa "f.drc.R" "f.eq.R" m'"$m_gain_R"
echo $cmd_L'; '$cmd_R'; quit' | nc -N localhost 3000

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
