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
LIBRESP = '/home/pi/.cargo/bin/librespot'

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


    opt_str = ' '.join(MOREOPT)

    cmd = f'{LIBRESP} --name {gethostname()} ' + \
          f'--bitrate 320 {BACKEND_OPTS} {opt_str}'

    eventsPath = f'{UHOME}/pe.audio.sys/.librespot_events'

    with open(eventsPath, 'w') as f:
        Popen( cmd.split(), stdout=f, stderr=f )

    # A daemon to ensure librespot jack port to be connected to librespot_loop
    watchdog_cmd = f"python3 {UHOME}/pe.audio.sys/share/scripts/" + \
                    "librespot/librespot_watchdog.py"
    Popen(watchdog_cmd, shell=True)


def stop():
    Popen( 'pkill -KILL -f bin/librespot'.split() )
    Popen( 'pkill -KILL -f librespot_watchdog'.split() )
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
