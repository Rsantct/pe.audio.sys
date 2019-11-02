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
    A daemon that listen for events from Spotify Desktop
    then writes down the metadata into a file for others to read it.
"""

#################### NOTICE #############################
# spotify_monitor_daaemon_v2.py works with playerctl v2.x
#########################################################

import sys, os
import subprocess as sp
import json
import time

import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

HOME = os.path.expanduser("~")
MAINFOLDER = f'{HOME}/pe.audio.sys'

# Will watch for files changed on this folder and subfolders:
WATCHED_DIR      = MAINFOLDER

# intermediate file from playerctl --follow
PLAYERCTLfile = f'{MAINFOLDER}/.playerctl_spotify_events'

# events dumping file for pre.di.c's players.py reading:
SPOTIFYfile   = f'{MAINFOLDER}/.spotify_events'

def run_playerctl():
    """ Runs playerctl in --follow mode """
    # Kills previous
    sp.Popen( ['pkill', '-f', 'playerctl -p spotify'] )
    time.sleep(.25)
    # Launch a new one
    cmd = 'playerctl -p spotify metadata --follow'
    with open( PLAYERCTLfile, 'w' ) as redir_file:
        sp.Popen( cmd.split(), shell=False, stdout=redir_file, stderr=redir_file )

def metadata2file(metalines):
    """ Convert the metadalalines from playerclt output to
        a json dict then writes to a file for players.py to read from
    """
    # spotify mpris:trackid             spotify:track:0M99ZDKDfGxcH7hBmZx6oa
    # spotify mpris:length              455000000
    # spotify mpris:artUrl              https://open.spotify.com/image/acfd35267322cdce41fc5fa790fa963ce232e565
    # spotify xesam:album               EP02
    # spotify xesam:albumArtist         Murcof
    # spotify xesam:artist              Philip Glass
    # spotify xesam:autoRating          0.14999999999999999
    # spotify xesam:discNumber          1
    # spotify xesam:title               Metamorphosis 4
    # spotify xesam:trackNumber         1
    # spotify xesam:url                 https://open.spotify.com/track/0M99ZDKDfGxcH7hBmZx6oa

    dict = {}
    for line in metalines:
        if not line.strip():
            break
        key, value = line[8:34].strip(), line[34:].strip()
        # mpris:length to integer
        if key == 'mpris:length':
            value = int(value)
        dict[key] =  value

    # Writes down the metadata dictionary to a file
    with open(SPOTIFYfile, 'w') as f:
        f.write( json.dumps( dict ) )

class Changed_files_handler(FileSystemEventHandler):

    def on_modified(self, event):
        path = event.src_path
        if '.playerctl_spotify_events' in path:
            with open(PLAYERCTLfile, 'r') as f:
                # Playerctrl metadata shows 11 metadata property lines
                metalines = f.read().split('\n')[-12:]
                metadata2file(metalines)

if __name__ == "__main__":

    if len(sys.argv) > 1:
        print( __doc__ )
        sys.exit()

    run_playerctl()
    time.sleep(1)

    # Starts a WATCHDOG to see when <PLAYERCTLfile> changes,
    # and handle these changes to update the <SPOTIFYfile>
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    observer = Observer()
    observer.schedule(event_handler=Changed_files_handler(), path=WATCHED_DIR, recursive=False)
    observer.start()
    obsloop = threading.Thread( target = observer.join() )
    obsloop.start()
