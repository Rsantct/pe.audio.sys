#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.
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
    Starts / stops the loudness_monitor.py daemon client
    use:   loudness_monitor    start | stop
"""

import sys, os
from subprocess import Popen
import yaml
from time import sleep

UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'
CONFIGFNAME = f'{MAINFOLDER}/config.yml'
STATEFNAME  = f'{MAINFOLDER}/.state.yml'
CTRLFNAME   = f'{MAINFOLDER}/.loudness_control'

def stop():
    Popen( 'pkill -f loudness_monitor_daemon.py'.split() )
    sleep(.5)

def start():
    stop()
    # Create the auxiliary loudness monitor control file
    with open(CTRLFNAME, 'w') as f:
        f.write('')

    cmd = f'{MAINFOLDER}/share/scripts/loudness_monitor/' \
            'loudness_monitor_daemon.py' \
           f' --input_device pre_in_loop' \
           f' --control_file  {CTRLFNAME} ' \
           f' --output_file {MAINFOLDER}/.loudness_monitor'

    Popen( cmd.split() )
    print(f'(loudness_monitor) spawned PortAudio ports in JACK')

if sys.argv[1:]:
    if sys.argv[1] == 'start':
        start()
    elif sys.argv[1] == 'stop':
        stop()
    else:
        print(__doc__)
else:
    print(__doc__)
