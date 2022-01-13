#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" A Spotify Desktop client interface module for players.py
"""

from    time        import sleep
from    subprocess  import check_output
import  yaml
from    pydbus      import SessionBus
import  logging
import  os
import  sys
UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    config  import MAINFOLDER
from    miscel  import timesec2string as timeFmt


LOGFNAME = f'{MAINFOLDER}/log/spotify_desktop.py.log'
logging.basicConfig(filename=LOGFNAME, filemode='w', level=logging.INFO)


# (i) BITRATE IS HARDWIRED pending on how to retrieve it from the desktop client.
SPOTIFY_BITRATE = '320'


# The DBUS INTERFACE with the Spotify Desktop client.
# You can browse it also by command line tool:
#   $ mdbus2 org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2
spotibus = None
tries = 3
while tries:
    try:
        # SessionBus will work if D-Bus has an available X11 $DISPLAY
        bus      = SessionBus()
        spotibus = bus.get( 'org.mpris.MediaPlayer2.spotify',
                            '/org/mpris/MediaPlayer2' )
        logging.info(f'spotibus OK')
        tries = 0
    except Exception as e:
        logging.info(f'spotibus FAILED: {e}')
        tries -=1
        sleep(.5)

# USER PLAYLISTS
plist_file = f'{MAINFOLDER}/config/spotify_plists.yml'
PLAYLISTS = {}
if os.path.exists(plist_file):
    try:
        PLAYLISTS = yaml.safe_load(open(plist_file, 'r'))
        tmp = f'READ \'{plist_file}\''
    except:
        tmp = f'ERROR reading \'{plist_file}\''
        print(f'(spotify_desktop.py) {tmp}')
    logging.info(tmp)


# External tool 'playerctl' to manage shuffle because MPRIS can only read it
def set_shuffle(mode):
    # (!) The command line tool 'playerctl' has a shuffle method
    #     BUT it does not work with Spotify Desktop :-(
    mode = { 'on':'On', 'off':'Off' }[mode]
    try:
        ans = check_output( f'playerctl shuffle {mode}'.split() ).decode()
        ans = { 'on':'on', 'off':'off', 'On':'on', 'Off':'off' }[ans]
    except:
        ans = 'off'
    return ans


def spotify_playlists(cmd, arg=''):

    result = 'command not available'

    if cmd == 'load_playlist':
        if PLAYLISTS:
            if arg in PLAYLISTS:
                spotibus.OpenUri( PLAYLISTS[arg] )
                result = 'ordered'
            else:
                result = 'ERROR: playlist not found'
        else:
            result = 'ERROR: Spotify playlist not available'

    elif cmd == 'get_playlists':
        result = list( PLAYLISTS.keys() )

    return result


# Spotify Desktop control
def spotify_control(cmd, arg=''):
    """ Controls the Spotify Desktop player
        input:  a command string
        output: the resulting status string
    """
    result = 'not connected'

    if not spotibus:
        return result

    if   cmd == 'state':
        pass

    elif cmd == 'play':
        spotibus.Play()

    elif cmd == 'pause':
        spotibus.Pause()

    elif cmd == 'next':
        spotibus.Next()

    elif cmd == 'previous':
        spotibus.Previous()

    # MPRIS Shuffle is an only-readable property.
    # (https://specifications.freedesktop.org/mpris-spec/latest/Player_Interface.html)
    elif cmd == 'random':
        if arg in ('get', ''):
            return spotibus.Shuffle
        elif arg in ('on', 'off'):
            set_shuffle(arg)
            return spotibus.Shuffle
        else:
            return f'error with \'random {arg}\''

    sleep(.25)
    result = {  'Playing':  'play',
                'Paused':   'pause',
                'Stopped':  'stop' } [spotibus.PlaybackStatus]

    return result


# Spotify Desktop metadata
def spotify_meta(md):
    """ Analize the MPRIS metadata info from spotibus.Metadata
        Input:      blank md dict
        Output:     Spotify metadata dict
    """
    md['player']  = 'Spotify Desktop Client'
    md['bitrate'] = SPOTIFY_BITRATE

    try:
        tmp = spotibus.Metadata
        # Example:
        # {
        # "mpris:trackid": "spotify:track:5UmNPIwZitB26cYXQiEzdP",
        # "mpris:length": 376386000,
        # "mpris:artUrl": "https://open.spotify.com/image/798d9b9cf2b63624c8c6cc191a3db75dd82dbcb9",
        # "xesam:album": "Doble Vivo (+ Solo Que la Una/Con Cordes del Mon)",
        # "xesam:albumArtist": ["Kiko Veneno"],
        # "xesam:artist": ["Kiko Veneno"],
        # "xesam:autoRating": 0.1,
        # "xesam:discNumber": 1,
        # "xesam:title": "Ser\u00e9 Mec\u00e1nico por Ti - En Directo",
        # "xesam:trackNumber": 3,
        # "xesam:url": "https://open.spotify.com/track/5UmNPIwZitB26cYXQiEzdP"
        # }

        # regular fields:
        for k in ('artist', 'album', 'title'):
            value = tmp[ f'xesam:{k}']
            if type(value) == list:
                md[k] = ' '.join(value)
            elif type(value) == str:
                md[k] = value
        # track_num:
        md['track_num'] = tmp["xesam:trackNumber"]
        # and time lenght:
        md['time_tot'] = timeFmt( tmp["mpris:length"] / 1e6 )

    except:
        pass

    return md
