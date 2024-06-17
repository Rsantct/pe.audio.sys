#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" A MPD interface module for players.py
"""
import os
import sys
import mpd

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from miscel import timesec2string as timeFmt, sec2min

c = mpd.MPDClient()


def connect(port=6600):
    try:
        c.connect('localhost', port)
        return True
    except:
        return False


def ping():
    try:
        c.ping()
        return True
    except:
        return False


def curr_playlist_is_cdda():
    """ returns True if the curren playlist has only cdda tracks
    """
    # :-/ the current playlist doesn't have any kind of propiertry to
    # check if the special 'cdda.m3u' is the currently loaded one.

    if not ping():
        if not connect():
            return False

    plist = c.playlist()

    return [x for x in plist if 'cdda' in x ] == plist


def mpd_playlists(cmd, arg=''):

    if not ping():
        if not connect():
            return f'ERROR connecting to MPD at port {port}'

    result = ''

    if cmd == 'get_playlists':
        # Some setups could use a mount for mpdconf playlist_directory
        try:
            result = [ x['playlist'] for x in c.listplaylists() ]
        except Exception as e:
            print(f'(mpd.py) {str(e)}')

    elif cmd == 'load_playlist':
        c.load(arg)
        result = f'ordered loading \'{arg}\''

    elif cmd == 'clear_playlist':
        c.clear()
        result = 'playlist cleared'

    return result


def mpd_control( query, arg='', port=6600 ):
    """ Comuticates to MPD music player daemon
        Input:      a command to query to the MPD daemon
        Return:     playback state string
    """

    def state(dummy_arg):
        return sta['state']

    def stop(dummy_arg):
        c.stop()
        return sta['state']

    def pause(dummy_arg):
        c.pause()
        return sta['state']

    def play(dummy_arg):
        c.play()
        return sta['state']

    def next(dummy_arg):
        try:
            c.next()  # avoids error if some playlist has wrong items
        except:
            pass
        return sta['state']

    def previous(dummy_arg):
        try:
            c.previous()
        except:
            pass
        return sta['state']

    def rew(dummy_arg):  # for REW and FF will move 30 seconds
        c.seekcur('-30')
        return sta['state']

    def ff(dummy_arg):
        c.seekcur('+30')
        return sta['state']

    def random(arg):
        if arg == 'on':
            c.random(1)
        elif arg == 'off':
            c.random(0)
        elif arg == 'toggle':
            c.random( {'0':1, '1':0}[ sta['random'] ])
        mode = sta['random']
        return {'0':'off', '1':'on'}[mode]


    if not ping():
        if not connect():
            return 'stop'

    sta = c.status()

    try:
        result = {  'state':            state,
                    'stop':             stop,
                    'pause':            pause,
                    'play':             play,
                    'next':             next,
                    'previous':         previous,
                    'rew':              rew,
                    'ff':               ff,
                    'random':           random
                 }[query](arg)
    except:
        result = f'erron with \'{query}\''

    return result


def mpd_meta( md ):
    """ Comuticates to MPD music player daemon
        Input:      blank metadata dict
        Return:     track metadata dict
    """

    md['player'] = 'MPD'

    if not ping():
        if not connect():
            return md

    cs = c.currentsong()
    st = c.status()


    # (i) Not all tracks have complete currentsong() fields:
    # artist, title, album, track, etc fields may NOT be provided
    # file, time, duration, pos, id           are ALWAYS provided

    # Skip if no currentsong is loaded
    if cs:
        if 'artist' in cs:
            md['artist']    = cs['artist']

        if 'album' in cs:
            md['album']     = cs['album']

        if 'track' in cs:
            md['track_num'] = cs['track']

        if 'title' in cs:
            md['title']     = cs['title']
        elif 'file' in cs:
            md['title']     = cs['file'].split('/')[-1]

        if 'file' in cs:
            md['file'] = cs["file"]


    if 'playlistlength' in st:
        md['tracks_tot']    = st['playlistlength']

    if 'bitrate' in st:
        md['bitrate']       = st['bitrate']  # kbps

    if 'audio' in st:
        md['format'] = st['audio']

    if 'time' in st:
        # time is given as a string 'current:total', each part in seconds
        md["time_pos"] = sec2min( int( st["time"].split(':')[0] ), mode=':')
        md["time_tot"] = sec2min( int( st["time"].split(':')[1] ), mode=':')

    if 'state' in st:
        md['state']         = st['state']

    return md
