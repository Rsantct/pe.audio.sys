#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    jacktrip: audio over network
"""

import sys
from subprocess import Popen


def start():
    cmd = 'jacktrip --jacktripserver --nojackportsconnect'
    cmd += ' --receivechannels 2 --queue 8 --redundancy 2 --bitres 16'

    Popen( cmd, shell=True )


def stop():
    Popen( ['pkill', '-KILL', '-f', 'jacktripserver'] )


if sys.argv[1:]:
    try:
        option = {  'start' : start,
                    'stop'  : stop
                  }[ sys.argv[1] ]()
    except:
        print( '(plugins/jacktrip_server) bad option' )
else:
    print(__doc__)
