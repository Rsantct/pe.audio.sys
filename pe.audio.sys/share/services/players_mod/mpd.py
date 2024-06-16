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

from miscel import timesec2string as timeFmt


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


def mpd_playlists(cmd, arg='', port=6600):

    result = ''

    c = mpd.MPDClient()
    try:
        c.connect('localhost', port)
    except:
        return f'ERROR connecting to MPD at port {port}'


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

        if 'title' in c.currentsong():
            md['title']     = c.currentsong()['title']
        elif 'file' in c.currentsong():
            md['title']     = c.currentsong()['file'].split('/')[-1]

        if 'audio' in c.currentsong():
            md['audio_format'] = c.currentsong()['audio']


    if 'playlistlength' in c.status():
        md['tracks_tot']    = c.status()['playlistlength']

    if 'bitrate' in c.status():
        md['bitrate']       = c.status()['bitrate']  # kbps

    # time: 'current:total'
    if 'time' in c.status():
        md["time_pos"] = timeFmt( int( c.status()["time"].split(':')[0] ))
        md["time_tot"] = timeFmt( int( c.status()["time"].split(':')[1] ))

    if 'state' in c.status():
        md['state']         = c.status()['state']

    return md
