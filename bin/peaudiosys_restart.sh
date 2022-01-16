#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.


if [[ ! $XDG_CURRENT_DESKTOP ]]; then
    # Needed when called w/o X environment:
    export XDG_RUNTIME_DIR=/run/user/$UID
    export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
    export JACK_NO_AUDIO_RESERVATION=1
fi


if [[ $1 == 'stop' ]]; then
    echo '(i) STOPPING pe.audio.sys'
    $HOME/pe.audio.sys/start.py stop

elif [[ ! $1 || $1 == *'start' ]]; then
    echo '(i) RESTARTING pe.audio.sys (all printouts hidden to /dev/null)'
    echo '    Startup process logged in <pe.audio.sys/log/start.log>'
    $HOME/pe.audio.sys/start.py all --log 1>/dev/null 2>&1 &

else
    echo
    echo 'USAGE:   peaudiosys_restart.sh [stop]'
    echo
    echo '         Startup process will be logged in <pe.audio.sys/log/start.log>'
    echo '         For further debugging run manually from a terminal:'
    echo '             peaudio.sys/start.py all & '
    echo

fi
