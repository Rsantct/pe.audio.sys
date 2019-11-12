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

UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'
CONFIGFNAME = f'{MAINFOLDER}/config.yml'
STATEFNAME  = f'{MAINFOLDER}/.state.yml'
CTRLFNAME   = f'{MAINFOLDER}/.loudness_control'

def start():

    # do create the auxiliary loudness monitor control file
    with open(CTRLFNAME, 'w') as f:
        f.write('')
        
    # This is to avoid an error when getting portnames if 'none' is the
    # current input, anyway it depens on 'system' to exist on jack inputs
    # so it still can occur a runtime error under loudness_monitor.py :-/
    try:
        with open(STATEFNAME, 'r') as f:
            input_name = yaml.load( f )['input']
        with open(CONFIGFNAME, 'r') as f:
            ports = yaml.load( f )['sources'][input_name]['capture_port']
        sounddevice = ports
    except:
        sounddevice = 'system'

    cmd = f'{MAINFOLDER}/share/scripts/loudness_monitor/' \
            'loudness_monitor_daemon.py' \
           f' --input_device {sounddevice}' \
           f' --control_file  {CTRLFNAME} ' \
           f' --output_file {MAINFOLDER}/.loudness_monitor'

    Popen( cmd.split() )
    print(f'(loudness_monitor) spawned PortAudio ports in JACK')

def stop():
    Popen( 'pkill -f loudness_monitor_daemon.py'.split() )

    
if sys.argv[1:]:
    try:
        option = {
            'start' : start,
            'stop'  : stop
            }[ sys.argv[1] ]()
    except:
        print( '(loudness_monitor) ERROR cannot start' )
else:
    print(__doc__)
