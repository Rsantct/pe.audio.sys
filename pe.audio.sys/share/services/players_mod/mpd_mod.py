#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" A MPD interface module for players.py
"""
import  os
import  sys
import  mpd
from    time import sleep

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from miscel import timesec2string as timeFmt, sec2min, Fmt

MPD_PORT = 6600

c = mpd.MPDClient()


def connect(port=MPD_PORT):

    try:
        c.connect('localhost', port)
        return True

    except Exception as e:

        print(f"{Fmt.RED}(mpd_mod.py) connect ERROR: {type(e)} {str(e)}{Fmt.END}")

        if str(e) == 'Already connected':
            return True

        else:
            return False


def ping(tries=3):

    while tries:

        try:
            c.ping()
            return True
        except Exception as e:
            print(f"{Fmt.GRAY}(mpd_mod.py) retrying ping ... {str(e)}{Fmt.END}")

        sleep(.1)
        tries -= 1

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
            return 'ERROR connecting to MPD'

    result = ''

    if cmd == 'get_playlists':
        # Some setups could use a mount for mpdconf playlist_directory
        try:
            result = [ x['playlist'] for x in c.listplaylists() ]
        except Exception as e:
            print(f"{Fmt.RED}(mpd_mod.py) error with 'get_playlists' {str(e)}{Fmt.END}")

    elif cmd == 'load_playlist':
        c.load(arg)
        result = f'ordered loading \'{arg}\''

    elif cmd == 'clear_playlist':
        c.clear()
        result = 'playlist cleared'

    return result


def mpd_control( cmd, arg='', port=MPD_PORT ):
    """ Comuticates to MPD music player daemon

        Input:      a command [arg] to query to the MPD daemon

        Returns:    a playback state string ( stop | play | pause )
                    OR
                    a random mode (on/off)
    """

    # If no connection
    if not ping():
        if not connect():
            if cmd == 'random':
                return 'off'
            else:
                return 'stop'

    # Do execute the command
    match cmd:

        case 'state':
            pass

        case 'stop':
            c.stop()

        case 'pause':
            c.pause()

        case 'play':
            c.play()

        case 'next':
            try:
                c.next()    # avoids error if some playlist has wrong items
            except:
                print(f"{Fmt.GRAY}(mpd_mod.py) error with 'next'{Fmt.END}")

        case 'previous':
            try:
                c.previous()
            except:
                print(f"{Fmt.GRAY}(mpd_mod.py) error with 'previous'{Fmt.END}")

        case 'rew':         # for REW and FF will move 30 seconds
            c.seekcur('-30')

        case 'ff':
            c.seekcur('+30')

        case 'random':

            if arg == 'on':
                c.random(1)

            elif arg == 'off':
                c.random(0)

            elif arg == 'toggle':
                st = c.status()
                c.random( {'0':1, '1':0}[ st['random'] ])


    st = c.status()


    try:

        if cmd == 'random':
            return {'0':'off', '1':'on'}[ st['random'] ]
        else:
            return st['state']

    except:

        print(f"(mpd_mod.py) WRONG MPDClient.status: {st}")

        if cmd == 'random':
            return 'off'
        else:
            return 'stop'


def mpd_meta( md ):
    """ Comuticates to MPD music player daemon
        Input:      blank metadata dict
        Return:     track metadata dict
    """

    md['player'] = 'MPD'

    # If no connection
    if not ping():
        if not connect():
            return md

    st = c.status()

    cs = c.currentsong()


    # (i) Not all tracks have complete currentsong() fields. Some examples:
    #
    #   {'file': 'http://192.168.1.46:49149/qobuz/track/version/1/trackId/4526528',
    #   'artist': 'Claudio Arrau',
    #   'album': 'Liszt: Piano Sonata in B Minor / Annees De Pelerinage / Ballade No. 2 / Transcendental Etude No. 10 (Arrau) (1970-1981)',
    #   'title': 'Piano Sonata in B Minor, S. 178/R. 21',
    #   'pos': '0',
    #   'id': '135'}
    #
    #   {'file': 'https://rtvelivestream.akamaized.net/rtvesec/rne/GL0/34_2024_07_11_20_11_03_113822.ts',
    #   'pos': '0',
    #   'id': '156'}


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

            if not 'album' in cs:
                # Try to put the URL site as 'album', if available
                if '//' in md['file']:
                    md['album'] = '/'.join( md['file'].split('/')[:3] )


    if 'playlistlength' in st:
        md['tracks_tot']    = st['playlistlength']

    if 'bitrate' in st:
        # playing wav/aiff files gives bitrate: '0'
        if st['bitrate'] != '0':
            md['bitrate']       = st['bitrate']  # kbps

    if 'audio' in st:
        md['format'] = st['audio']

    if 'time' in st:
        # time is given as a string 'current:total', each part in seconds
        md["time_pos"] = sec2min( int( st["time"].split(':')[0] ), mode=':')
        md["time_tot"] = sec2min( int( st["time"].split(':')[1] ), mode=':')


    return md


connect()
