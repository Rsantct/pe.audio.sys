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
    'track_num':    ''
    }

# MPD control, status and metadata
def mpd_client(query):
    """ Comuticates to MPD music player daemon
        Input: a command to query to the MPD daemon
        Returns: the MPD response.
        I/O: .mpd_events (w)
    """

    def get_meta():
        """ gets info from mpd """

        md = METATEMPLATE.copy()
        md['player'] = 'MPD'

        if mpd_online:

            # We try because not all tracks have complete metadata fields:
            try:    md['artist']    = client.currentsong()['artist']
            except: pass
            try:    md['album']     = client.currentsong()['album']
            except: pass
            try:    md['title']     = client.currentsong()['title']
            except: pass
            try:    md['track_num'] = client.currentsong()['track']
            except: pass
            try:    md['bitrate']   = client.status()['bitrate']   # given in kbps
            except: pass
            try:    md['time_pos']  = timeFmt( float( client.status()['elapsed'] ) )
            except: pass
            try:    md['time_tot']  = timeFmt( float( client.currentsong()['time'] ) )
            except: pass

            client.close()

        # As an add-on, we will update an event file on the flavour of mplayer or librespot,
        # to be monitored by any event changes service as for example lcd_service.py
        with open( f'{MAINFOLDER}/.mpd_events', 'w' ) as file:
            file.write( json.dumps( md ) )

        return json.dumps( md )

    def state():
        if mpd_online:
            return client.status()['state']

    def stop():
        if mpd_online:
            client.stop()
            return client.status()['state']

    def pause():
        if mpd_online:
            client.pause()
            return client.status()['state']

    def play():
        if mpd_online:
            client.play()
            return client.status()['state']

    def next():
        if mpd_online:
            try:    client.next() # avoids error if some playlist has wrong items
            except: pass
            return client.status()['state']

    def previous():
        if mpd_online:
            try:    client.previous()
            except: pass
            return client.status()['state']

    def rew():                    # for REW and FF will move 30 seconds
        if mpd_online:
            client.seekcur('-30')
            return client.status()['state']

    def ff():
        if mpd_online:
            client.seekcur('+30')
            return client.status()['state']

    client = mpd.MPDClient()
    try:
        client.connect(MPD_HOST, MPD_PORT)
        if MPD_PASSWD:
            client.password(MPD_PASSWD)
        mpd_online = True
    except:
        mpd_online = False

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

    return result

