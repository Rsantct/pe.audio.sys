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

    Usage:      CDDA  start   [track] - Loads Mplayer for CDDA
                      stop            - KILLS this script

                      control_play [track]
                      control_pause
                      control_prev
                      control_next
                      control_stop
                      control_eject
"""
# --- Some info about Mplayer SLAVE commands ---
#
# loadfile cdda://A-B:S     play tracks from A to B at speed S
#
# get_property filename     get the tracks to be played as
#                           'A' (single track)
#                           or 'A-B' (range of tracks)
#
# get_property chapter      get the current track index inside
#                           the filename property (first is 0)
#
# seek_chapter 1            go to next track
# seek_chapter -1           go to prev track
#
# seek X seconds

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

def control_play(track_num=1):

    try:
        print( f'(init/CDDA) trying to load track #{track_num}' )
        # The whole address after 'loadfile' needs to be SINGLE quoted to load properly
        command = ('loadfile \'cdda://' + str(track_num)  + '-100:1\'\n' )
        #print(command) # debug
        f = open( input_fifo, 'w')
        f.write(command)
        f.close()
        return True
    except:
        print( f'(init/CDDA) failed to load track \#\'{track_num}\'' )
        return False


def control_seek(step=1):
    try:
        command = ('seek_chapter ' + str(step) + '\n' )
        f = open( input_fifo, 'w')
        f.write(command)
        f.close()
        return True
    except:
        print( f'(init/CDDA) failed to change track' )
        return False

def control_toggle():
    try:
        command = ('pause\n' )
        f = open( input_fifo, 'w')
        f.write(command)
        f.close()
        return True
    except:
        print( f'(init/CDDA) failed to toggle pause' )
        return False


def control_stop():
    try:
        command = ('stop\n' )
        f = open( input_fifo, 'w')
        f.write(command)
        f.close()
        return True
    except:
        print( f'(init/CDDA) failed to stop playing' )
        return False

def control_eject():
    control_stop()
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

    ### Reading the command line
    if sys.argv[1:]:

        opc = sys.argv[1]

        # STARTS the script and optionally starts playing a track number
        if opc == 'start':
            start()
            if sys.argv[2:]:
                opc2 = sys.argv[2]
                if opc2.isdigit():
                    control_play( int(opc2) )

        # STOPS (KILLS) all this stuff
        elif opc == 'stop':
            stop()

        # CONTROLLING PLAYING
        elif opc == 'control_play':
            if sys.argv[2:]:
                opc2 = sys.argv[2]
                if opc2.isdigit():
                    control_play( int(opc2) )
            else:
                control_play()

        elif opc == 'control_toggle' or opc=='control_pause':
            control_toggle()

        elif opc == 'control_prev':
            control_seek(-1)

        elif opc == 'control_next':
            control_seek(1)

        elif opc == 'control_stop':
            control_stop()

        elif opc == 'control_eject':
            control_eject()

        else:
            print( '(init/CDDA) Bad option' )

    else:
        print(__doc__)
