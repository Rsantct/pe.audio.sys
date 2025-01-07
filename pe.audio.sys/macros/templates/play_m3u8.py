#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Plays an akamaized 'm3u8' playlist througby MPD

    Usage:  play_m3u8.py    station_name (*)

        (*) as per configured in config/istreams.yml


    This program is a loop that feeds the m3u8 chunks into the MPD playlist.
    If someone modifies the MPD playlist, then this loop will end.
"""

import  sys
import  os
import  yaml
import  mpd
import  m3u8
from    time import sleep

UHOME = os.path.expanduser("~")

MPD_PORT = 6600

mpdcli = mpd.MPDClient()


def mpd_connect(port=MPD_PORT):
    try:
        mpdcli.connect('localhost', port)
        return True
    except:
        return False


def mpd_ping():

    tries = 3

    while tries:

        try:
            mpdcli.ping()
            return True
        except:
            pass

        sleep(.2)
        tries -= 1

    return False


def get_m3u8_target_duration(url):
    try:
        pl =  m3u8.load(url, timeout=5)
        return pl.target_duration
    except:
        return 0


def get_m3u8_uris(url):
    try:
        pl =  m3u8.load(url, timeout=5)
        return [x.uri for x in pl.segments]
    except:
        return []


def get_url(station_name):

    def load_istreams():

        istreams_path = f'{UHOME}/pe.audio.sys/config/istreams.yml'

        try:
            with open(istreams_path, 'r') as f:
                return yaml.safe_load(f.read())
        except:
            return {}


    url = ''
    for k, v in load_istreams().items():
        if station_name == v["name"]:
            url = v["url"]
            break
    return url


if __name__ == "__main__":

    print()

    # Reading the desired station
    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()

    station_name = sys.argv[1]

    radio_url = get_url(station_name)

    if not radio_url:
        print(f"'{station_name}': not found. Bye.")
        sys.exit()

    number_of_uris = len( get_m3u8_uris(radio_url) )
    if not number_of_uris:
        print('(play_m3u8.py) Error reading M3U8')
        sys.exit()

    ts_duration = get_m3u8_target_duration( radio_url )

    if not ts_duration:
        print(f'(play_m3u8.py) {station_name}: not a valid m3u8 url. Bye.')
        sys.exit()


    # Loading the M3U8 into MPD and playing it.
    print(f'(play_m3u8.py) Loading `{station_name}` into MPD playlist')

    if not mpd_connect():
        print('(play_m3u8.py) cannot connect to MPD. Bye.')
        sys.exit()

    mpdcli.clear()
    old_consume = mpdcli.status()["consume"]
    old_random  = mpdcli.status()["random"]
    mpdcli.consume(1)
    mpdcli.random(0)


    # At least 2 URIs will be kept loaded in the playlist

    loop_waiting = (number_of_uris - 2) * ts_duration

    try:

        print(f'(play_m3u8.py) MPD playing `{station_name}`')

        end_reason = ''

        # Repeat every near target duration
        while True:

            play_issued = False

            mpd_pl = [ x.split()[-1] for x in mpdcli.playlist() ]

            # URIs are changing over time
            uris = get_m3u8_uris(radio_url)

            for uri in uris:

                # Someone wants to play anything else
                if len(mpdcli.playlist()) > len(uris):
                    end_reason = 'The playing queue was modified'
                    break

                if not uri in mpd_pl:
                    mpdcli.add(uri)

            if not play_issued:
                mpdcli.play()
                play_issued = True


            if not mpd_ping():
                end_reason = 'MPD connection lost'
                break

            sleep(loop_waiting)

        if end_reason:
            print(f'(play_m3u8.py) {end_reason}')
        else:
            print(f'(play_m3u8.py) MPS playlist loop failed :-/')

    except KeyboardInterrupt:
        mpdcli.clear()
        mpdcli.consume(old_consume)
        mpdcli.random(old_random)
        print('\n(play_m3u8.py) Interrupted. Bye!')
