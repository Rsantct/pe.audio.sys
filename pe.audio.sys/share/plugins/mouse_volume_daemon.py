#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Runs a daemon that manages the pe.audio.sys volume
    trough by a mouse.
"""
import sys
import os
from subprocess import Popen
from getpass import getuser

THISDIR =  os.path.dirname( os.path.realpath(__file__) )


def start():
    Popen( f'{THISDIR}/mouse_volume_daemon/mouse_volume_daemon.py',
              shell=True )


def stop():
    # arakiri
    Popen( f'pkill -u {getuser()} -KILL -f mouse_volume_daemon.py', shell=True )


if __name__ == "__main__":

    if sys.argv[1:]:
        if sys.argv[1] == 'stop':
            stop()
        elif sys.argv[1] == 'start':
            start()
        else:
            print(__doc__)
    else:
        print(__doc__)
