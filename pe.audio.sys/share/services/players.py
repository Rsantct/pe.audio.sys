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
    This module is called from the listening script 'server.py'.
"""

# (i) I/O FILES MANAGED HERE:
#
# .state.yml        'r'     pe.audio.sys state file
#

import os
import subprocess as sp
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

## METADATA GENERIC TEMPLATE to serve to clients as the control web page.
#  (!) remember to use copies of this ;-)
METATEMPLATE = {
    'player':       '',
    'time_pos':     '',
    'time_tot':     '',
    'bitrate':      '',
    'artist':       '',
    'album':        '',
    'title':        '',
    'track_num':    ''
    }

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

    metadata = METATEMPLATE.copy()
    source = get_source()

    if   'librespot' in source or 'spotify' in source.lower():
        if spotify_client == 'desktop':
            metadata = spotify_meta()
        elif spotify_client == 'librespot':
            metadata = librespot_meta()
        # source is spotify like but no client running has been detected:
        else:
            metadata = json.dumps( metadata )

    elif source == 'mpd':
        metadata = mpd_client('get_meta')

    elif source == 'istreams':
        metadata = mplayer_meta(service=source, readonly=readonly)

    elif source == 'tdt' or 'dvb' in source:
        metadata = mplayer_meta(service='dvb', readonly=readonly)

    elif source == 'cd':
        metadata = cdda_meta()

    else:
        metadata = json.dumps( metadata )

    # As this is used by a server, we will return a bytes-like object:
    return metadata.encode()

# Generic function to control any player
def player_control(action):
    """ controls the playback
        returns: 'stop' | 'play' | 'pause'
    """

    source = get_source()
    result = ''

    if   source == 'mpd':
        result = mpd_client(action)

    elif source.lower() == 'spotify' and spotify_client == 'desktop':
        # We can control only Spotify Desktop (not librespot)
        result = spotify_control(action)

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

    # As this is used by a server, we will return a bytes-like object:
    return result.encode()

# Gets the current input source on pre.di.c
def get_source():
    """ retrieves the current input source """
    source = None
    # It is possible to fail while state file is updating :-/
    times = 4
    while times:
        try:
            source = get_state()['input']
            break
        except:
            times -= 1
        sleep(.25)
    return source

# Gets the dictionary of pre.di.c status
def get_state():
    """ returns the YAML state info """
    with open( MAINFOLDER + '/.state.yml', 'r') as f:
        return yaml.safe_load(f)

# Interface entry function to this module
def do(task):
    """
        This do() is the entry interface function from a listening server.
        Only certain received 'tasks' will be validated and processed,
        then returns back some useful info to the asking client.
    """

    # First clearing the taksk phrase
    task = task.strip()

    # task: 'player_get_meta'
    # Tasks querying the current music player.
    if   task == 'player_get_meta':
        return player_get_meta()

    # task: 'player_xxxxxxx'
    # Playback control. (i) Some commands need to be adequated later, depending on the player,
    # e.g. Mplayer does not understand 'previous', 'next' ...
    elif task[7:] in ('state', 'stop', 'pause', 'play', 'next', 'previous', 'rew', 'ff'):
        return player_control( task[7:] )

    # task: 'player_eject' unconditionally ejects the CD tray
    elif task[7:] == 'eject':
        return mplayer_cmd('eject', 'cdda')

    # task: 'player_play_track_NN'
    # Special command for disk playback control
    elif task[7:18] == 'play_track_':
        return player_control( task[7:] )

    # task: 'http://an/url/stream/to/play
    # A pseudo task, an url to be played back:
    elif task[:7] == 'http://':
        sp.Popen( f'{MAINFOLDER}/share/scripts/istreams.py url {task}'.split() )
