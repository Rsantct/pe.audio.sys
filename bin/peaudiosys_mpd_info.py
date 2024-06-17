#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" A command line MPD audio info tool

    Usage:  peaudiosys_mpd_info.py [ -audio | -status | -current ]
"""
import sys
import mpd
from   time import sleep


def timesec2string(x):
    """ Format a given float (seconds) to "hh:mm:ss"
        (string)
    """
    # x must be float
    h = int( x / 3600 )         # hours
    x = int( round(x % 3600) )  # updating x to reamining seconds
    m = int( x / 60 )           # minutes from the new x
    s = int( round(x % 60) )    # and seconds
    return f'{h:0>2}:{m:0>2}:{s:0>2}'


def get_status():

    st = c.status()

    d = {'state': st["state"]}

    # time: 'current:total'
    if 'time' in st:
        d["time_pos"] = timesec2string( int( st["time"].split(':')[0] ) )
        d["time_tot"] = timesec2string( int( st["time"].split(':')[1] ) )

    if 'audio' in st:
        d["format"] = st["audio"]

    if 'bitrate' in st:
        d["bitrate"] = st["bitrate"]

    return d


def get_currentsong():

    d = c.currentsong()

    return d


def print_it(what):

    if what == 'audio':

        st = get_status()

        for k in 'format', 'bitrate':
            if k in st:
                print(f'{ k.ljust(15) }: { st[k] }')
            else:
                print(f'{ k.ljust(15) }: --')

    elif what == 'status':

        for k, v in get_status().items():
            print(f'{k.ljust(15)}: {v}')

    elif what == 'current_song':

        cs = get_currentsong()

        for k in 'file', 'artist', 'album', 'title':
            if k in cs:
                print(f'{ k.ljust(15) }: { cs[k] }')
            else:
                print(f'{ k.ljust(15) }: --')


if __name__ == "__main__":

    c = mpd.MPDClient()
    c.connect('localhost', 6600)

    if not sys.argv[1:]:

        print_it('status')
        print()
        print_it('current_song')

    else:
        if '-a' in sys.argv[1]:
            print_it('audio')

        elif '-s' in sys.argv[1]:
            print_it('status')

        elif '-c' in sys.argv[1]:
            print_it('current_song')

        else:
            print(__doc__)


