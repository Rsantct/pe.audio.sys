#!/usr/bin/env python3
"""
    Launchs '/usr/bin/librespot': a Spotify Connect player client

    use:    librespot   start | stop
"""

import sys, os
from subprocess import Popen
from socket import gethostname

UHOME = os.path.expanduser("~")

def start():
    # 'librespot' binary prints out the playing track and some info to stdout/stderr.
    # We redirect the print outs to a temporary file that will be periodically
    # read from a player control daemon.

    cmd =  f'/usr/bin/librespot --name {gethostname()} --bitrate 320 --backend alsa' + \
           ' --device aloop --disable-audio-cache --initial-volume=99'

    logFileName = f'{UHOME}/pe.audio.sys/.librespot_events'

    with open(logFileName, 'w') as logfile:
        Popen( cmd.split(), stdout=logfile, stderr=logfile )

def stop():
    Popen( 'pkill -f librespot'.split() )

if sys.argv[1:]:
    try:
        option = {
            'start' : start,
            'stop'  : stop
            }[ sys.argv[1] ]()
    except:
        print( '(init/librespot) bad option' )
else:
    print(__doc__)
