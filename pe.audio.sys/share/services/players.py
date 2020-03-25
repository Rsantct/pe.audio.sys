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

""" A module that controls and retrieve metadata info from the current player.
    This module is called from the TCP listening script 'server.py'.
"""

# (i) I/O FILES MANAGED HERE:
#
# .state.yml        'r'     pe.audio.sys state file
#
# .player_metadata  'w'     Stores the current player metadata
#
# .player_state     'w'     Stores the current playback state
#

import os
import subprocess as sp
import threading
import yaml
from time import sleep
import json
from  players_mod.mpd import                mpd_client
from  players_mod.librespot import          librespot_meta
from  players_mod.mplayer import            mplayer_cmd, \
                                            mplayer_meta, \
                                            cdda_meta
from  players_mod.spotify_desktop import    spotify_control, \
                                            spotify_meta, \
                                            detect_spotify_client

UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'

## Spotify client detection
spotify_client = detect_spotify_client()

## generic metadata template (!) remember to use copies of this ;-)
METATEMPLATE = {
    'player':       '',
    'time_pos':     '',
    'time_tot':     '',
    'bitrate':      '',
    'artist':       '',
    'album':        '',
    'title':        '',
    'track_num':    '',
    'state':        'stop'
    }

# Aux to get the current preamp input source
def get_source():
    """ retrieves the current input source """
    source = None
    # It is possible to fail while state file is updating :-/
    times = 4
    while times:
        try:
            with open( MAINFOLDER + '/.state.yml', 'r') as f:
                source = yaml.safe_load(f)['input']
            break
        except:
            times -= 1
        sleep(.25)
    return source

# Generic function to get meta from any player: MPD, Mplayer or Spotify
def player_get_meta(readonly=False):
    """ Makes a dictionary-like string with the current track metadata
        '{player: xxxx, artist: xxxx, album:xxxx, title:xxxx, etc... }'
        Then will return a bytes-like object from the referred string.
    """
    # 'readonly=True':
    #   Only useful for mplayer_meta(). It avoids to query Mplayer
    #   and flushing its metadata file.
    #   It is used from the 'change files handler' on lcd_service.py.

    source = get_source()

    md = METATEMPLATE.copy()

    # Getting metadata from a Spotify client:
    if   'librespot' in source or 'spotify' in source.lower():
        if spotify_client == 'desktop':
            md = spotify_meta()
        elif spotify_client == 'librespot':
            md = librespot_meta()
        # source is spotify like but no client running has been detected:
        else:
            md['player'] = 'Spotify'
            md = json.dumps( md )

    # Getting metadata from MPD:
    elif source == 'mpd':
        md = mpd_client('get_meta')

    # Getting metadata from Mplayer based sources:
    elif source == 'istreams':
        md = mplayer_meta(service='istreams', readonly=readonly)

    elif source == 'tdt' or 'dvb' in source:
        md = mplayer_meta(service='dvb', readonly=readonly)

    elif 'cd' in source:
        md = mplayer_meta(service='cdda', readonly=readonly)

    # Unknown source, blank metadata:
    else:
        md = json.dumps( METATEMPLATE.copy() )

    # As this is used by a server, we will return a bytes-like object:
    return md.encode()

# Generic function to control any player
def player_control(action):
    """ controls the playback
        returns: 'stop' | 'play' | 'pause'
    """

    source = get_source()
    result = ''

    if   source == 'mpd':
        result = mpd_client(action)

    elif source.lower() == 'spotify':
        # We can control only Spotify Desktop (not librespot)
        if   spotify_client == 'desktop':
            result = spotify_control(action)
        elif spotify_client == 'librespot':
            result = 'play'

    elif 'tdt' in source or 'dvb' in source:
        result = mplayer_cmd(cmd=action, service='dvb')

    elif source in ['istreams', 'iradio']:
        result = mplayer_cmd(cmd=action, service='istreams')

    elif source == 'cd':
        result = mplayer_cmd(cmd=action, service='cdda')

    # Currently only MPD and Spotify Desktop provide 'state' info.
    # 'result' can be 'play', 'pause', 'stop' or ''.
    if not result:
        result = '' # to avoid None.encode() error

    # Store the player state
    with open( f'{MAINFOLDER}/.player_state', 'w') as f:
        f.write(result)

    # As this is used by a server, we will return a bytes-like object:
    return result.encode()

# Interface entry function for this module from 'server.py'
def do(task):
    """ This do() is the entry interface function from a listening server.
        Only certain received 'tasks' will be validated and processed,
        then returns back some useful info to the asking client.
    """

    # First clearing the task phrase
    task = task.strip()

    # Getting METADATA
    if task == 'player_get_meta':
        with open( f'{MAINFOLDER}/.player_metadata', 'r') as f:
            return f.read().encode()

    # PLAYBACK CONTROL. (i) Some commands need to be adequated later,
    # e.g. Mplayer does not understand 'previous', 'next'
    elif task[7:] in ('state', 'stop', 'pause', 'play', 
                       'next', 'previous', 'rew', 'ff'):
        return player_control( task[7:] )

    # Special command for DISK TRACK playback
    elif task[7:18] == 'play_track_':
        return player_control( task[7:] )

    # EJECTS unconditionally the CD tray
    elif task[7:] == 'eject':
        return mplayer_cmd('eject', 'cdda')

    # An URL to be played back by the istreams Mplayer service:
    elif task[:7] == 'http://':
        sp.Popen( f'{MAINFOLDER}/share/scripts/istreams.py url {task}'
                  .split() )

# Optional init function
def init():
    """ This init function will:
        - Periodically store the metadata info to
            MAINFOLDER/.player_metadata
          so that can be read from any process interested in it.
        - Also will initiate MAINFOLDER/.player_state
    """
    def store_meta(timer=2):
        while True:
            md = player_get_meta().decode()
            with open( f'{MAINFOLDER}/.player_metadata', 'w') as f:
                f.write( md )
            sleep(timer)
    # Loop storing metadata
    meta_timer = 2
    meta_loop = threading.Thread( target=store_meta, args=(meta_timer,) )
    meta_loop.start()
    # Initiate the player state
    with open( f'{MAINFOLDER}/.player_state', 'w') as f:
        f.write('stop')

