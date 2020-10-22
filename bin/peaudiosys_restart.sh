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
    echo '(i) RESTARTING pe.audio.sys (all printouts redirected to /dev/null)'
    $HOME/pe.audio.sys/start.py all 1>/dev/null 2>&1 &

else
    echo 'USAGE:   peaudiosys_restart.sh [stop]'
fi
