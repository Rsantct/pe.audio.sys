#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    This script manages '/usr/bin/librespot',
    a headless Spotify Connect player daemon

    https://github.com/librespot-org/librespot

    Usage:    librespot.py   start | stop
"""
import sys
import os
from subprocess import Popen
from socket import gethostname
from time import sleep

UHOME = os.path.expanduser("~")


# BYNARY
BYNARY = '/home/pi/.cargo/bin/librespot'

# BACKEND OPTIONS
BACKEND_OPTS = f'--backend jackaudio --device librespot'

# MORE OPTIONS LIST (do not configure here: bitrate, name, backend, device)
MOREOPT = [
    '--disable-audio-cache',
    # https://github.com/librespot-org/librespot/wiki/FAQ
    # For AUDIOPHILES
    '--mixer softvol --volume-ctrl fixed --initial-volume 100',
    '--format F32'
]


def start():
    # 'librespot' binary prints out the playing track and some info.
    # We redirect the them to a temporary file that will be periodically
    # read from a player control daemon.


    moreopt_str = ' '.join(MOREOPT)

    cmd = f'{BYNARY} --name {gethostname()} ' + \
          f'--onevent {UHOME}/pe.audio.sys/share/scripts/librespot/bind_ports.sh ' + \
          f'--bitrate 320 {BACKEND_OPTS} {moreopt_str}'

    eventsPath = f'{UHOME}/pe.audio.sys/.librespot_events'

    with open(eventsPath, 'w') as f:
        Popen( cmd.split(), stdout=f, stderr=f )


def stop():
    Popen( 'pkill -KILL -f bin/librespot'.split() )
    sleep(.5)


if sys.argv[1:]:
    if sys.argv[1] == 'start':
        stop()
        start()
    elif sys.argv[1] == 'stop':
        stop()
    else:
        print(__doc__)
else:
    print(__doc__)
