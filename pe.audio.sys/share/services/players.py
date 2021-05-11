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
"""

# (i) I/O FILES MANAGED HERE:
#
# .state.yml        'r'     pe.audio.sys state file
#
# .player_metadata  'w'     Stores the current player metadata
#
# .player_state     'w'     Stores the current playback state
#

from os.path import expanduser, exists, getsize
import sys
import subprocess as sp
import threading
import yaml
from time import sleep, strftime
import json
from socket import socket

UHOME = expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'
sys.path.append(MAINFOLDER)

from  share.miscel                  import  detect_spotify_client, wait4ports \
                                            is_IP

from  players_mod.mpd               import  mpd_control,                \
                                            mpd_meta
from  players_mod.mplayer           import  mplayer_control,            \
                                            mplayer_meta
from  players_mod.librespot         import  librespot_control,          \
                                            librespot_meta
from  players_mod.spotify_desktop   import  spotify_control,            \
                                            spotify_meta


## Getting sources list
with open(f'{MAINFOLDER}/config.yml', 'r') as f:
    SOURCES = yaml.safe_load( f )["sources"]


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
                'tracks_tot':   '-' }


# Gets metadata from a remote pe.audio.sys system
def remote_get_meta(host, port=9990):
    md = ''
    md = METATEMPLATE.copy()
    ans = send_cmd( cmd='player get_meta',
                    host=host, port=port, timeout=1)
    try:
        md = json.loads(ans)
    except:
        pass
    return md


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
def player_get_meta():
    """ Returns a dictionary with the current track metadata
        '{player: xxxx, artist: xxxx, album:xxxx, title:xxxx, etc... }'
    """
    md = METATEMPLATE.copy()

    source = get_source()

    if 'librespot' in source or 'spotify' in source.lower():
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
        md = mplayer_meta(md, service='istreams')

    elif source == 'tdt' or 'dvb' in source:
        md = mplayer_meta(md, service='dvb')

    elif 'cd' in source:
        md = mplayer_meta(md, service='cdda')

    elif source.startswith('remote'):
        # For a 'remote.....' named source, it is expected to have
        # an IP address kind of in its capture_port field:
        #   capture_port:  X.X.X.X:PPPP
        # so this way we can query metadata from the remote address.
        host = SOURCES[source]["capture_port"].split(':')[0]
        port = SOURCES[source]["capture_port"].split(':')[-1]

        # (i) we assume that the remote pe.audio.sys listen at standard 9990 port
        if is_IP(host):
            if not port.isdigit():
                port = 9990
            md = remote_get_meta( host, port )


    return md


# Generic function to control any player
def player_control(cmd, arg=''):
    """ controls the playback
        returns: 'stop' | 'play' | 'pause'
        I/O:     .player_state
    """

    newState = 'stop'  # default state
    source   = get_source()

    # (i) result depends on different source modules:

    # MPD
    if source == 'mpd':
        result = mpd_control(cmd)

    # Spotify
    elif source.lower() == 'spotify':
        if   SPOTIFY_CLIENT == 'desktop':
            result = spotify_control(cmd, arg)
        elif SPOTIFY_CLIENT == 'librespot':
            result = librespot_control(cmd)
        else:
            result = 'stop'

    # DVB-T.py
    elif 'tdt' in source or 'dvb' in source:
        result = mplayer_control(cmd=cmd, service='dvb')

    # istreams.py
    elif source in ['istreams', 'iradio']:
        result = mplayer_control(cmd=cmd, service='istreams')

    # CDDA.py
    elif source == 'cd':
        result = mplayer_control(cmd=cmd, arg=arg, service='cdda')

    # A generic source without a player module
    else:
        result = 'stop'

    # Dumps the player newState
    # (fix newState to a valid value if a module answer was wrong)
    if result not in ('stop', 'play', 'pause'):
        newState = 'stop'  # default state
    with open( f'{MAINFOLDER}/.player_state', 'w') as f:
        f.write(newState)

    return result


# auto-started when loading this module
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
                f.write( json.dumps( md ))
            sleep(timer)
    # Loop storing metadata
    meta_timer = 2
    meta_loop = threading.Thread( target=store_meta, args=(meta_timer,) )
    meta_loop.start()
    # Flush state file:
    with open( f'{MAINFOLDER}/.player_state', 'w') as f:
        f.write('')


# Interface entry function for this module plugged inside 'server.py'
def do(cmd_phrase):
    """ Entry interface function for a parent server.py listener.
        - in:   a command phrase
        - out:  a string result (dicts are json dumped)
    """

    cmd_phrase = cmd_phrase.strip()
    result = 'nothing done'

    # Reading command phrase:
    cmd, arg = '', ''
    chunks = cmd_phrase.split(' ')
    cmd = chunks[0]
    if chunks[1:]:
        # allows spaces inside the arg part, e.g. 'load_playlist Hard Rock'
        arg = ' '.join(chunks[1:])

    # PLAYBACK STATE
    if cmd == 'state':
        result = player_control( cmd )

    # Getting METADATA
    elif cmd == 'get_meta':
        with open( f'{MAINFOLDER}/.player_metadata', 'r') as f:
            result = f.read()

    # PLAYLISTS
    elif cmd == 'load_playlist':
        result = player_control( cmd, arg )
    elif cmd == 'get_playlists':
        # (currently only works with Spotify playlists file)
        result = player_control( cmd )

    # PLAYBACK CONTROL. (i) Some commands need to be adequated later,
    # e.g. Mplayer does not understand 'previous', 'next'
    elif cmd in ('stop', 'pause', 'play', 'next', 'previous', 'rew', 'ff'):
        result = player_control( cmd )

    # Special command for DISK TRACK playback
    elif cmd == 'play_track':
        result = player_control( cmd, arg )

    # EJECTS unconditionally the CD tray
    elif cmd == 'eject':
        result = mplayer_control('eject', service='cdda')

    if type(result) != str:
        result = json.dumps(result)

    return result


# Will AUTO-START init() when loading this module
init()
