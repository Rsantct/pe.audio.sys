#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Loads the pulseaudio sink, in order to
    Pulseaudio apps to default sound through by JACK.

    usage:  pulseaudio-jack-sink.py   start|stop

    NEEDED PACKAGE: pulseaudio-module-jack
"""

import sys
from subprocess import Popen
from time import sleep


def start():
    tmp = "pactl load-module module-jack-sink channels=2 " + \
          "client_name=pulse_sink connect=False"
    Popen( tmp.split() )
    sleep(.2)
    tmp = "pacmd set-default-sink jack_out"
    Popen( tmp.split() )


def stop():
    tmp = "pactl unload-module module-jack-sink"
    Popen( tmp.split() )


if sys.argv[1:]:

    if sys.argv[1] in ['stop', 'unload']:
        stop()
    elif sys.argv[1] in ['start', 'load']:
        start()
    else:
        print(__doc__)
        sys.exit()
