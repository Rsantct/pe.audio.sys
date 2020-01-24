#!/bin/bash

# Failed to connect to session bus for device reservation: Unable to autolaunch a dbus-daemon without a
# $DISPLAY for X11
#
# To bypass device reservation via session bus, set JACK_NO_AUDIO_RESERVATION=1 prior to starting jackd.
#
# Audio device hw:RPiCirrus,0 cannot be acquired...
# Cannot initialize driver

export JACK_NO_AUDIO_RESERVATION=1

python3 "$HOME"/pe.audio.sys/start.py all  \
1>"$HOME"/pe.audio.sys/start.py.log \
2>&1 &

