#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    jacktrip: audio over network

    usage: jacktrip_server.py  start|stop
"""

import sys
from subprocess import Popen
from getpass    import getuser


def start():
    cmd = 'jacktrip --jacktripserver --nojackportsconnect'
    cmd += ' --numchannels 2 --queue 8 --redundancy 2 --bitres 24'
    Popen( cmd, shell=True )


def stop():
    Popen( ['pkill', '-u', getuser(), '-KILL', '-f', 'jacktripserver'] )


if sys.argv[1:]:

    opt = sys.argv[1]

    if opt == 'start':
        #stop()
        start()

    elif opt == 'stop':
        stop()

    else:
        print(__doc__)

else:
    print(__doc__)
