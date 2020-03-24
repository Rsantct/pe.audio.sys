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
import json

UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'

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

# librespot (Spotify Connect client) metatata
def librespot_meta():
    """ Input:  --
        Output: metadata info from librespot in json format
        I/O:    .librespot_events (r) - librespot redirected printouts 
    """

    # Unfortunately librespot only prints out the title metadata, nor artist neither album.
    # More info can be retrieved from the spotify web, but it is necessary to register
    # for getting a privative and unique http request token for authentication.

    # Gets librespot bitrate from librespot running process:
    try:
        tmp = sp.check_output( 'pgrep -fa /usr/bin/librespot'.split() ).decode()
        # /usr/bin/librespot --name rpi3clac --bitrate 320 --backend alsa --device jack --disable-audio-cache --initial-volume=99
        librespot_bitrate = tmp.split('--bitrate')[1].split()[0].strip()
    except:
        librespot_bitrate = '-'

    md = METATEMPLATE.copy()
    md['player'] = 'Spotify'
    md['bitrate'] = librespot_bitrate

    try:
        # Returns the current track title played by librespot.
        # 'scripts/librespot.py' handles the libresport print outs to be
        #                        redirected to 'tmp/.librespotEvents'
        # example:
        # INFO:librespot_playback::player: Track "Better Days" loaded
        #
        with open(f'{MAINFOLDER}/.librespot_events', 'r') as f:
            lines = f.readlines()[-20:]
        # Recently librespot uses to print out some 'AddrNotAvailable, message' mixed with
        # playback info messages, so we will search for the latest 'Track ... loaded' message,
        # backwards from the end of the events file:
        for line in lines[::-1]:
            if line.strip()[-6:] == "loaded":
                # raspotify flawors of librespot
                if not 'player] <' in line:
                    md['title'] = line.split('player: Track "')[-1] \
                                      .split('" loaded')[0]
                    break
                # Rust cargo librespot package
                else:
                    md['title'] = line.split('player] <')[-1] \
                                      .split('> loaded')[0]
                    break
    except:
        pass

    # json metadata
    return json.dumps( md )

