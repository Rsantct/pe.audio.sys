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

import os
import mpd
import json

UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'

## MPD settings:
MPD_HOST    = 'localhost'
MPD_PORT    = 6600
MPD_PASSWD  = None

## generic metadata template
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

# Auxiliary function to format hh:mm:ss
def timeFmt(x):
    # x must be float
    h = int( x / 3600 )         # hours
    x = int( round(x % 3600) )  # updating x to reamining seconds
    m = int( x / 60 )           # minutes from the new x
    s = int( round(x % 60) )    # and seconds
    return f'{h:0>2}:{m:0>2}:{s:0>2}'

# MPD control, status and metadata
def mpd_client(query):
    """ Comuticates to MPD music player daemon
        Input: a command to query to the MPD daemon
        Returns: the MPD response: pb state word or metadata json string.
        I/O: .mpd_metadata (w)
    """

    def get_meta():
        """ gets info from mpd """

        md = METATEMPLATE.copy()
        md['player'] = 'MPD'

        # (i) Not all tracks have complete currentsong() fields:
        # artist, title, album, track, etc fields may NOT be provided
        # file, time, duration, pos, id           are ALWAYS provided

        try:    md['title']     = client.currentsong()['title']
        except: md['title']     = client.currentsong()['file'] \
                                               .split('/')[-1]
        try:    md['artist']    = client.currentsong()['artist']
        except: pass

        try:    md['album']     = client.currentsong()['album']
        except: pass

        try:    md['track_num'] = client.currentsong()['track']
        except: pass

        try:    md['bitrate']   = client.status()['bitrate'] # kbps
        except: pass

        try:    md['time_pos']  = timeFmt( float(
                                    client.status()['elapsed'] ) )
        except: pass

        try:    md['time_tot']  = timeFmt( float( 
                                    client.currentsong()['time'] ) )
        except: pass

        try:    md['state'] = client.status()['state']
        except: pass

        # As an add-on, we will dump metadata to a file
        with open( f'{MAINFOLDER}/.mpd_metadata', 'w' ) as file:
            file.write( json.dumps( md ) )

        return json.dumps( md )

    def state():
        return client.status()['state']

    def stop():
        client.stop()
        return client.status()['state']

    def pause():
        client.pause()
        return client.status()['state']

    def play():
        client.play()
        return client.status()['state']

    def next():
        try:
            client.next() # avoids error if some playlist has wrong items
        except:
            pass
        return client.status()['state']

    def previous():
        try:
            client.previous()
        except:
            pass
        return client.status()['state']

    def rew(): # for REW and FF will move 30 seconds
        client.seekcur('-30')
        return client.status()['state']

    def ff():
        client.seekcur('+30')
        return client.status()['state']

    client = mpd.MPDClient()
    try:
        client.connect(MPD_HOST, MPD_PORT)
        if MPD_PASSWD:
            client.password(MPD_PASSWD)
    except:
        return ''

    result = {  'get_meta':   get_meta,
                'state':      state,
                'stop':       stop,
                'pause':      pause,
                'play':       play,
                'next':       next,
                'previous':   previous,
                'rew':        rew,
                'ff':         ff
             }[query]()

    client.close()
    return result

