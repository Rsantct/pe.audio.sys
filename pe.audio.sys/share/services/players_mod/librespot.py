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

""" A libresport interface module for players.py
"""
import os
import subprocess as sp

UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'


def librespot_control(throwit):
    """ fake control, always will return 'play'
        input:  a fake command
        output: the resulting status
    """
    return 'play'


# librespot (Spotify Connect client) metatata
def librespot_meta(md):
    """ Input:  blank md dict
        Output: metadata dict derived from librespot printouts
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

    md['player'] = 'librespot'
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
                if 'player] <' not in line:
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

    return md
