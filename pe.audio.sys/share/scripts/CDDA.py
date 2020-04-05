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
    Starts and stops Mplayer for CDDA playback.

    Also used to CD play control and disk eject.

    Usage:      CDDA  start | stop | eject
"""

import os
UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'

import sys
import time
import subprocess as sp
from pathlib import Path
import yaml

## --- Mplayer options ---
# -quiet: see channels change
# -really-quiet: silent
options = '-quiet -nolirc -slave -idle'

## Input FIFO. Mplayer runs in server mode (-slave) and
#  will read commands from a fifo:
input_fifo = f'{MAINFOLDER}/.cdda_fifo'
f = Path( input_fifo )
if  not f.is_fifo():
    sp.Popen ( f'mkfifo {input_fifo}'.split() )
del(f)

## Mplayer output is redirected to a file,
#  so it can be read what it is been playing:
redirection_path = f'{MAINFOLDER}/.cdda_events'

## cdrom device to use
try:
    with open(f'{MAINFOLDER}/config.yml', 'r') as f:
        PEASYSCONFIG = yaml.safe_load(f)
    CDROM_DEVICE = PEASYSCONFIG['cdrom_device']
except:
    CDROM_DEVICE = '/dev/cdrom'
    print(f'(CDDA.py) Using default \'{CDROM_DEVICE}\'')

def eject():
    sp.Popen( f'eject {CDROM_DEVICE}'.split() )

def start():
    cmd = f'mplayer {options} -profile cdda -cdrom-device {CDROM_DEVICE}' \
          f' -input file={input_fifo}'
    with open(redirection_path, 'w') as redirfile:
        sp.Popen( cmd.split(), shell=False,
                  stdout=redirfile, stderr=redirfile )

def stop():
    sp.Popen( ['pkill', '-KILL', '-f', 'profile cdda'] )

if __name__ == '__main__':

    if sys.argv[1:]:

        opc = sys.argv[1]

        if opc == 'start':
            start()
        elif opc == 'stop':
            stop()
        elif opc == 'eject':
            eject()
        else:
            print(__doc__)

    else:
        print(__doc__)
