#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

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

    use:    librespot.py   start | stop
"""
import sys, os
from subprocess import Popen
from socket import gethostname
from time import sleep

UHOME = os.path.expanduser("~")

def try_backends():
    result = ''
    ftmp = '/tmp/librespot.test'
    for be in ('rodio', 'pulseaudio', 'alsa'):
        with open(ftmp, 'w') as f:
            tmp = Popen( f'/usr/bin/librespot --name tmp --backend {be} &',
                                shell=True, stdout=f, stderr=f)
        sleep(1)
        Popen( 'pkill -KILL -f "name tmp"', shell=True )
        with open(ftmp, 'r') as f:
            tmp = f.read()
            if not 'backend' in tmp:
                result = be
        Popen( f'rm {ftmp}'.split() )
        sleep(.25) # lets wait for rm to delete the tmpfile
        if result:
            return result
    print( tmp )
    exit()

def start():
    # 'librespot' binary prints out the playing track and some info to stdout/stderr.
    # We redirect the print outs to a temporary file that will be periodically
    # read from a player control daemon.

    backend = try_backends()
    backend_opts = f'--backend {backend}'
    if backend == 'alsa':
        backend_opts += ' --device aloop'

    cmd =  f'/usr/bin/librespot --name {gethostname()} --bitrate 320 {backend_opts}' + \
           ' --disable-audio-cache --initial-volume=99'

    logFileName = f'{UHOME}/pe.audio.sys/.librespot_events'

    with open(logFileName, 'w') as logfile:
        Popen( cmd.split(), stdout=logfile, stderr=logfile )

def stop():
    Popen( 'pkill -KILL -f bin\/librespot'.split() )
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
