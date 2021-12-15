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

""" A MPD interface module for players.py
"""
import os
import sys
import mpd

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys')

from share.miscel import timesec2string as timeFmt


def curr_playlist_is_cdda( port=6600 ):
    """ returns True if the curren playlist has only cdda tracks
    """
    # :-/ the current playlist doesn't have any kind of propiertry to
    # check if the special 'cdda.m3u' is the currently loaded one.

    c = mpd.MPDClient()
    try:
        c.connect('localhost', port)
    except:
        return False

    return [x for x in c.playlist() if 'cdda' in x ] == c.playlist()


def mpd_control( query, arg='', port=6600 ):
    """ Comuticates to MPD music player daemon
        Input:      a command to query to the MPD daemon
        Return:     playback state string
    """

    def state(dummy_arg):
        return c.status()['state']

    def stop(dummy_arg):
        c.stop()
        return c.status()['state']

    def pause(dummy_arg):
        c.pause()
        return c.status()['state']

    def play(dummy_arg):
        c.play()
        return c.status()['state']

    def next(dummy_arg):
        try:
            c.next()  # avoids error if some playlist has wrong items
        except:
            pass
        return c.status()['state']

    def previous(dummy_arg):
        try:
            c.previous()
        except:
            pass
        return c.status()['state']

    def rew(dummy_arg):  # for REW and FF will move 30 seconds
        c.seekcur('-30')
        return c.status()['state']

    def ff(dummy_arg):
        c.seekcur('+30')
        return c.status()['state']

    def list_playlists(dummy_arg):
        return [ x['playlist'] for x in c.listplaylists() ]

    def load_playlist(plistname):
        c.load(plistname)
        return f'loading \'{plistname}\''

    def clear_playlist(dummy_arg):
        c.clear()
        return 'cleared'

    def random(arg):
        if arg == 'on':
            c.random(1)
        elif arg == 'off':
            c.random(0)
        elif arg == 'toggle':
            c.random( {'0':1, '1':0}[ c.status()['random'] ])
        mode = c.status()['random']
        return {'0':'off', '1':'on'}[mode]


    c = mpd.MPDClient()
    try:
        c.connect('localhost', port)
    except:
        return 'stop'

    try:
        result = {  'state':            state,
                    'stop':             stop,
                    'pause':            pause,
                    'play':             play,
                    'next':             next,
                    'previous':         previous,
                    'rew':              rew,
                    'ff':               ff,
                    'get_playlists':    list_playlists,
                    'load_playlist':    load_playlist,
                    'clear_playlist':   clear_playlist,
                    'random':           random
                 }[query](arg)
    except:
        result = f'erron with \'{query}\''

    c.close()
    return result


def mpd_meta( md, port=6600 ):
    """ Comuticates to MPD music player daemon
        Input:      blank metadata dict
        Return:     track metadata dict
    """

    md['player'] = 'MPD'

    c = mpd.MPDClient()
    try:
        c.connect('localhost', port)
    except:
        return md

    # (i) Not all tracks have complete currentsong() fields:
    # artist, title, album, track, etc fields may NOT be provided
    # file, time, duration, pos, id           are ALWAYS provided

    # Skip if no currentsong is loaded
    if c.currentsong():
        if 'artist' in c.currentsong():
            md['artist']    = c.currentsong()['artist']

        if 'album' in c.currentsong():
            md['album']     = c.currentsong()['album']

        if 'track' in c.currentsong():
            md['track_num'] = c.currentsong()['track']

        if 'time' in c.currentsong():
            md['time_tot']  = timeFmt( float( c.currentsong()['time'] ) )

        if 'title' in c.currentsong():
            md['title']     = c.currentsong()['title']
        elif 'file' in c.currentsong():
            md['title']     = c.currentsong()['file'].split('/')[-1]

    if 'playlistlength' in c.status():
        md['tracks_tot']    = c.status()['playlistlength']

    if 'bitrate' in c.status():
        md['bitrate']       = c.status()['bitrate']  # kbps

    if 'elapsed' in c.status():
        md['time_pos']      = timeFmt( float( c.status()['elapsed'] ) )

    if 'state' in c.status():
        md['state']         = c.status()['state']

    return md
