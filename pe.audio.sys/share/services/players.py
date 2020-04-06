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

""" Controls and retrieve metadata info from the current player.
    This module is loaded by 'server.py'
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
from  players_mod.mpd               import  mpd_control,                \
                                            mpd_meta
from  players_mod.mplayer           import  mplayer_control,            \
                                            mplayer_meta
from  players_mod.librespot         import  librespot_control,          \
                                            librespot_meta
from  players_mod.spotify_desktop   import  spotify_control,            \
                                            spotify_meta,               \
                                            detect_spotify_client

UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'

## Spotify client detection
SPOTIFY_CLIENT = detect_spotify_client()

## generic metadata template (!) remember to use copies of this ;-)
METATEMPLATE = {
    'player':       '',
    'time_pos':     '-',
    'time_tot':     '-',
    'bitrate':      '-',
    'artist':       '-',
    'album':        '-',
    'title':        '-',
    'track_num':    '-',
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
    """ Returns a dictionary with the current track metadata
        '{player: xxxx, artist: xxxx, album:xxxx, title:xxxx, etc... }'
    """
    # 'readonly=True':
    #   Only useful for mplayer_meta(). It avoids to query Mplayer
    #   and flushing its metadata file.
    #   It is used from the 'change files handler' on lcd_service.py.

    md = METATEMPLATE.copy()

    source = get_source()


    if   'librespot' in source or 'spotify' in source.lower():
        if SPOTIFY_CLIENT == 'desktop':
            md = spotify_meta(md)
        elif SPOTIFY_CLIENT == 'librespot':
            md = librespot_meta(md)
        # source is spotify like but no client running has been detected:
        else:
            md['player'] = 'Spotify'

    elif source == 'mpd':
        md = mpd_meta(md)

    elif source == 'istreams':
        md = mplayer_meta(md, service='istreams', readonly=readonly)

    elif source == 'tdt' or 'dvb' in source:
        md = mplayer_meta(md, service='dvb', readonly=readonly)

    elif 'cd' in source:
        md = mplayer_meta(md, service='cdda', readonly=readonly)

    return md

# Generic function to control any player
def player_control(action):
    """ controls the playback
        returns: 'stop' | 'play' | 'pause'
        I/O:     .player_state
    """
    nstate = ''

    source = get_source()

    if source == 'mpd':
        nstate = mpd_control(action)

    elif source.lower() == 'spotify':
        if   SPOTIFY_CLIENT == 'desktop':
            nstate = spotify_control(action)
        elif SPOTIFY_CLIENT == 'librespot':
            nstate = librespot_control(action)

    elif 'tdt' in source or 'dvb' in source:
        nstate = mplayer_control(cmd=action, service='dvb')

    elif source in ['istreams', 'iradio']:
        nstate = mplayer_control(cmd=action, service='istreams')

    elif source == 'cd':
        nstate = mplayer_control(cmd=action, service='cdda')

    # Store the player nstate
    with open( f'{MAINFOLDER}/.player_state', 'w') as f:
        f.write(nstate)

    return nstate

# init() will be autostarted from server.py when loading this module
def init():
    """ This init function will:
        - Periodically store the metadata info to .player_metadata file
          so that can be read from any process interested in it.
        - Also will flush the .player_state file
    """
    def store_meta(timer=2):
        while True:
            md = player_get_meta()
            with open( f'{MAINFOLDER}/.player_metadata', 'w') as f:
                f.write( json.dumps(md ))
            sleep(timer)
    # Loop storing metadata
    meta_timer = 2
    meta_loop = threading.Thread( target=store_meta, args=(meta_timer,) )
    meta_loop.start()
    # Flush state file:
    with open( f'{MAINFOLDER}/.player_state', 'w') as f:
        f.write('')

# Interface entry function for this module plugged inside 'server.py'
def do(cmd):
    """ Entry interface function for a parent server.py listener.
        - in:   a command phrase
        - out:  a string result (dicts are json dumped)
    """

    result = 'nothing done'

    # First clearing the cmd phrase
    cmd = cmd.strip()

    # Getting METADATA
    if cmd == 'get_meta':
        with open( f'{MAINFOLDER}/.player_metadata', 'r') as f:
            result = f.read()

    # PLAYBACK STATE
    elif cmd == 'state':
        result = player_control( cmd )

    # PLAYBACK CONTROL. (i) Some commands need to be adequated later,
    # e.g. Mplayer does not understand 'previous', 'next'
    elif cmd in ('stop', 'pause', 'play', 'next', 'previous', 'rew', 'ff'):
        result = player_control( cmd )

    # Special command for DISK TRACK playback
    elif cmd.startswith('play_track_'):
        result = player_control( cmd )

    # EJECTS unconditionally the CD tray
    elif cmd == 'eject':
        result = mplayer_cmd('eject', 'cdda')

    # An URL to be played back by the istreams Mplayer service:
    elif cmd.startswith('http://'):
        sp.Popen( f'{MAINFOLDER}/share/scripts/istreams.py url {cmd}'
                  .split() )
        result = 'done'

    if type(result) != str:
        result = json.dumps(result)

    return result
