#!/bin/bash

# Failed to connect to session bus for device reservation: Unable to autolaunch a dbus-daemon without a
# $DISPLAY for X11
#
# To bypass device reservation via session bus, set JACK_NO_AUDIO_RESERVATION=1 prior to starting jackd.
#
# Audio device hw:RPiCirrus,0 cannot be acquired...
# Cannot initialize driver
export JACK_NO_AUDIO_RESERVATION=1

if [[ $1 == 'stop' ]]; then
    echo '(i) STOPPING pe.audio.sys'
    $HOME/pe.audio.sys/start.py stop

elif [[ ! $1 || $1 == *'start' ]]; then
    echo '(i) RESTARTING pe.audio.sys (all printouts hidden to /dev/null)'
    echo '    Startup process logged in <pe.audio.sys/start.log>'
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
