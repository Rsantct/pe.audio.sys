#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A daemon that listen for events from Spotify Desktop
    then writes down the metadata into a file for others to read it.
"""

#################### NOTICE #############################
# spotify_monitor_daaemon_v2.py works with playerctl v2.x
#########################################################

import sys
import os
import subprocess as sp
import json
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'

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
        sp.Popen( cmd.split(), shell=False, stdout=redir_file,
                                            stderr=redir_file )


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
        key, value = line[8: 34].strip(), line[34: ].strip()
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
                metalines = f.read().split('\n')[-12: ]
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
    observer.schedule(event_handler=Changed_files_handler(),
                      path=MAINFOLDER, recursive=False)
    observer.start()
    obsloop = threading.Thread( target=observer.join() )
    obsloop.start()
