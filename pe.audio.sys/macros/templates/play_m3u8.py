#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Plays an akamaized m3u8 stream througby MPD

        play_m3u8.py    station_name

        station_name as per configured within config/istreams.yml
"""

import  sys
import  os
import  yaml
import  mpd
import  m3u8
from    time import sleep

UHOME = os.path.expanduser("~")

mpdcli = mpd.MPDClient()


def mpd_connect(port=6600):
    try:
        mpdcli.connect('localhost', port)
        return True
    except:
        return False


def mpd_ping():
    try:
        mpdcli.ping()
        return True
    except:
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

    # Reading the desired station
    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()

    station_name = sys.argv[1]

    radio_url = get_url(station_name)

    if not radio_url:
        print(f'{station_name}: not found')
        sys.exit()

    ts_duration = get_m3u8_target_duration( radio_url )

    if not ts_duration:
        print(f'{station_name}: not a valid m3u8 url')
        sys.exit()

    # Connecting to MPD
    if not mpd_connect():
        print('Error with MPD')
        sys.exit()

    mpdcli.clear()
    old_consume = mpdcli.status()["consume"]
    mpdcli.consume(1)


    # Loading the M3U8 into MPD and playing it
    number_of_uris = len( get_m3u8_uris(radio_url) )
    if not number_of_uris:
        print('Error reading M3U8')
        sys.exit()

    loop_waiting = (number_of_uris - 1) * ts_duration
    try:

        # Repeat every near target duration
        while True:

            play_issued = False

            mpd_pl = [ x.split()[-1] for x in mpdcli.playlist() ]

            # URIs are changing over time
            uris = get_m3u8_uris(radio_url)

            for uri in uris:

                # Someone wants to play anything else
                if len(mpdcli.playlist()) > len(uris):
                    print('The playing queue was modified, so bye!')
                    sys.exit()

                if not uri in mpd_pl:
                    mpdcli.add(uri)

            if not play_issued:
                mpdcli.play()
                play_issued = True


            if not mpd_ping():
                print('MPD connection lost')
                sys.exit()

            sleep(loop_waiting)


    except KeyboardInterrupt:
        mpdcli.clear()
        mpdcli.consume(old_consume)
        print('\nBye!')
