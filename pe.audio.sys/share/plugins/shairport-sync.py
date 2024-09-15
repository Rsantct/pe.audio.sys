#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.
"""
    shairport-sync  Plays audio streamed from AirPlay sources.

    use:    shairport-sync.py   start | stop
"""
import sys
from subprocess import Popen, call
from socket import gethostname
from getpass import getuser

# Debian package system service NEEDS to be disabled after installing:
#     sudo systemctl stop shairport-sync.service
#     sudo systemctl disable shairport-sync.service

def start():
    # Former versions used alsa but recent debian package alows jack :-)
    cmd = f'shairport-sync -a {gethostname()} -o jack'
    Popen( cmd, shell=True )


def stop():
    call( ['pkill', '-u', getuser(), '-KILL', '-f', f'shairport-sync -a {gethostname()}'] )


if sys.argv[1:]:
    try:
        option = {  'start' : start,
                    'stop'  : stop
                  }[ sys.argv[1] ]()
    except:
        print( '(plugins/shairport-sync) bad option' )
else:
    print(__doc__)
