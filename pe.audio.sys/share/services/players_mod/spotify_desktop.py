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

""" A Spotify Desktop client interface module for players.py
"""
import os
UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'

from time import sleep
from subprocess import check_output
import yaml
from pydbus import SessionBus

# The dbus interface of the Spotify Desktop client.
# You can browse it also by command line tool:
#   $ mdbus2 org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2
bus = SessionBus()
spotibus = bus.get( 'org.mpris.MediaPlayer2.spotify',
                    '/org/mpris/MediaPlayer2' )

# bitrate HARDWIRED pending on how to retrieve it from the desktop client.
SPOTIFY_BITRATE   = '320'

# User playlists
try:
    CONFIG = yaml.safe_load( open(f'{MAINFOLDER}/config.yml', 'r') )
    plist_file = CONFIG['spotify_playlists_file']
    PLAYLISTS = yaml.safe_load(open(plist_file, 'r'))
except:
    PLAYLISTS = {}


# Auxiliary to detect the Spotify Client in use: desktop or librespot
def detect_spotify_client():
    cname = None
    # Check if a desktop client is running:
    try:
        check_output( 'pgrep -f Spotify'.split() )
        cname = 'desktop'
    except:
        pass
    # Check if 'librespot' (a Spotify Connect daemon) is running:
    try:
        check_output( 'pgrep -f librespot'.split() )
        cname = 'librespot'
    except:
        pass
    return cname


# Auxiliary function to format hh:mm:ss
def timeFmt(x):
    """ in:     x seconds   (float)
        out:    'hh:mm:ss'  (string)
    """
    # x must be float
    h = int( x / 3600 )         # hours
    x = int( round(x % 3600) )  # updating x to reamining seconds
    m = int( x / 60 )           # minutes from the new x
    s = int( round(x % 60) )    # and seconds
    return f'{h:0>2}:{m:0>2}:{s:0>2}'


# Spotify Desktop control
def spotify_control(cmd, arg=''):
    """ Controls the Spotify Desktop player
        input:  a command string
        output: the resulting status string
    """

    if   cmd == 'state':
        pass

    elif cmd == 'play':
        spotibus.Play()

    elif cmd == 'pause':
        spotibus.Pause()

    elif cmd == 'next':
        spotibus.Next()

    elif cmd == 'previous':
        spotibus.Previous()

    elif cmd == 'load_playlist':
        if PLAYLISTS:
            if arg in PLAYLISTS:
                spotibus.OpenUri( PLAYLISTS[arg] )
            else:
                return 'ERROR: playlist not found'
        else:
            return 'ERROR: Spotify playlist not available'

    elif cmd == 'get_playlists':
        return list( PLAYLISTS.keys() )

    sleep(.25)
    return {'Playing':  'play',
            'Paused':   'pause',
            'Stopped':  'stop' }[spotibus.PlaybackStatus]


# Spotify Desktop metadata
def spotify_meta(md):
    """ Analize the MPRIS metadata info from spotibus.Metadata
        Input:      blank md dict
        Output:     Spotify metadata dict
    """
    md['player']  = 'Spotify Desktop Client'
    md['bitrate'] = SPOTIFY_BITRATE

    try:
        tmp = spotibus.Metadata
        # Example:
        # {
        # "mpris:trackid": "spotify:track:5UmNPIwZitB26cYXQiEzdP",
        # "mpris:length": 376386000,
        # "mpris:artUrl": "https://open.spotify.com/image/798d9b9cf2b63624c8c6cc191a3db75dd82dbcb9",
        # "xesam:album": "Doble Vivo (+ Solo Que la Una/Con Cordes del Mon)",
        # "xesam:albumArtist": ["Kiko Veneno"],
        # "xesam:artist": ["Kiko Veneno"],
        # "xesam:autoRating": 0.1,
        # "xesam:discNumber": 1,
        # "xesam:title": "Ser\u00e9 Mec\u00e1nico por Ti - En Directo",
        # "xesam:trackNumber": 3,
        # "xesam:url": "https://open.spotify.com/track/5UmNPIwZitB26cYXQiEzdP"
        # }

        # regular fields:
        for k in ('artist', 'album', 'title'):
            value = tmp[ f'xesam:{k}']
            if type(value) == list:
                md[k] = ' '.join(value)
            elif type(value) == str:
                md[k] = value
        # track_num:
        md['track_num'] = tmp["xesam:trackNumber"]
        # and time lenght:
        md['time_tot'] = timeFmt( tmp["mpris:length"] / 1e6 )

    except:
        pass

    return md
