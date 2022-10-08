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


# CONFIGURATION
BACKEND = 'alsa'
ALSADEV = 'aloop'
OPTLIST = [ '--disable-audio-cache',
            '--initial-volume=100',
            '--format F32'
        ]


def start():
    # 'librespot' binary prints out the playing track and some info.
    # We redirect the them to a temporary file that will be periodically
    # read from a player control daemon.

    backend_opts = f'--backend {BACKEND}'
    if BACKEND == 'alsa':
        backend_opts += f' --device {ALSADEV}'

    OPTSTR = ' '.join(OPTLIST)

    cmd = f'/usr/bin/librespot --name {gethostname()} ' + \
          f'--bitrate 320 {backend_opts} {OPTSTR}'

    eventsFileName = f'{UHOME}/pe.audio.sys/.librespot_events'

    with open(eventsFileName, 'w') as logfile:
        Popen( cmd.split(), stdout=logfile, stderr=logfile )


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
