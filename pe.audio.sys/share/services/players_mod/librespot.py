#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" A libresport interface module for players.py
    librespot is a Spotify Connect client:
    https://github.com/librespot-org/librespot
"""
import os
import subprocess as sp

UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'


def librespot_control(cmd, arg=''):
    """ (i) This is a fake control
        input:  a fake command
        output: the result is predefined
    """
    if cmd == 'get_playlists':
        return []

    elif cmd == 'random':
        return 'n/a'

    else:
        return 'play'


def librespot_meta(md):
    """ Input:  blank md dict
        Output: metadata dict derived from librespot printouts
        I/O:    .librespot_events (r) - librespot redirected printouts
    """

    # Unfortunately librespot only prints out the title metadata,
    # nor artist neither album.
    # More info can be retrieved from the spotify web, but it is needed
    # to register for getting a privative and unique http request token
    # for authentication.

    # Gets librespot bitrate from librespot running process:
    try:
        tmp = sp.check_output('pgrep -fa /usr/bin/librespot'.split()).decode()
        # /usr/bin/librespot ... --bitrate 320 ...
        librespot_bitrate = tmp.split('--bitrate')[1].split()[0].strip()
    except:
        librespot_bitrate = '-'

    # Minimum metadata
    md['player'] = 'librespot'
    md['bitrate'] = librespot_bitrate

    # Trying to complete metadata fields:
    try:

        # Returns the current track title played by librespot.
        # 'scripts/librespot.py' redirects printouts to .librespot_events

        # librespot uses to print out some 'AddrNotAvailable, message' mixed with
        # playback info messages, so we will search for the latest
        # 'Track ... loaded' message backwards from the end of the events file:

        with open(f'{MAINFOLDER}/.librespot_events', 'r') as f:
            lines = f.readlines()[-20:]

        for line in lines[::-1]:

            if line.endswith("loaded\n"):

                # Rust cargo format:
                if 'player] <' in line:
                    md['title'] = line.split('player] <')[-1] \
                                      .split('> (')[0]

                # former loaded message format:
                else:
                    md['title'] = line.split('player: Track "')[-1] \
                                      .split('" loaded')[0]

                break


    except:
        pass


    return md
