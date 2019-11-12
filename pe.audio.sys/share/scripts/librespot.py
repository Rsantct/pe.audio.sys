#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

# This is based on 'pre.di.c,' a preamp and digital crossover
# https://github.com/rripio/pre.di.c
# Copyright (C) 2018 Roberto Ripio
# 'pre.di.c' is based on 'FIRtro', a preamp and digital crossover
# https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
#
# 'pe.audio.sys' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'pe.audio.sys' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'pe.audio.sys'.  If not, see <https://www.gnu.org/licenses/>.

"""
    '/usr/bin/librespot': a headless Spotify Connect player daemon

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
    Popen( 'pkill -KILL -f bin\/librespot'.split() )

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
