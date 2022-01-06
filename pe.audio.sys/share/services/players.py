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

""" Controls and retrieve metadata info from the current player.
"""

# (i) I/O FILES MANAGED HERE:
#
# .state            'r'     pe.audio.sys state file
#
# .player_metadata  'w'     Stores the current player metadata
#

from    os.path import expanduser
import  sys
import  threading
from    time    import sleep
import  json


UHOME = expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')


from  config                        import  CONFIG, PLAYER_META_PATH

from  miscel                        import  detect_spotify_client,      \
                                            read_state_from_disk,       \
                                            read_cdda_info_from_disk,   \
                                            send_cmd, is_IP

from  players_mod.mpd               import  mpd_control,                \
                                            mpd_meta,                   \
                                            mpd_playlists

from  players_mod.mplayer           import  mplayer_control,            \
                                            mplayer_get_meta,           \
                                            mplayer_playlists

from  players_mod.librespot         import  librespot_control,          \
                                            librespot_meta

from  players_mod.spotify_desktop   import  spotify_control,            \
                                            spotify_meta,               \
                                            spotify_playlists


## Getting sources list
SOURCES = CONFIG["sources"]

## Spotify client detection
SPOTIFY_CLIENT = detect_spotify_client()

## generic metadata template (!) remember to use copies of this ;-)
METATEMPLATE = {
                'player':       '',
                'time_pos':     '-',
                'time_tot':     '-',
                'bitrate':      '-',
                'artist':       '-',
                'album':        '-',
                'title':        '-',
                'track_num':    '-',
                'tracks_tot':   '-' }

# The runtime metadata variable and refresh period in seconds
CURRENT_MD          = METATEMPLATE.copy()
CURRENT_MD_REFRESH  = 2


def remote_get_meta(host, port=9990):
    """ Get metadata from a remote pe.audio.sys system
    """
    md = METATEMPLATE.copy()
    try:
        tmp = send_cmd( cmd='player get_meta',
                        host=host, port=port, timeout=1)
        md = json.loads(tmp)
    except:
        pass
    return md


def remote_player_control( cmd, arg, host, port=9990):
    """ Controls the playback on a remote pe.audio.sys system
    """
    # short timeout for remote LAN machine conn failure
    timeout = .5
    rem_state = send_cmd( cmd=f'player {cmd} {arg}',
                          host=host, port=port, timeout=timeout)
    return rem_state


def get_meta():
    """ Returns a dictionary with the current track metadata
        including the involved source player
    """
    md = METATEMPLATE.copy()

    source = read_state_from_disk()['input']

    if 'librespot' in source or 'spotify' in source.lower():
        if SPOTIFY_CLIENT == 'desktop':
            md = spotify_meta(md)
        elif SPOTIFY_CLIENT == 'librespot':
            md = librespot_meta(md)
        # source is spotify like but no client running has been detected:
        else:
            md['player'] = 'Spotify'

    elif source == 'mpd':
        md = mpd_meta(md)

    elif source == 'istreams':
        md = mplayer_get_meta(md, service='istreams')

    elif source == 'tdt' or 'dvb' in source:
        md = mplayer_get_meta(md, service='dvb')

    elif 'cd' in source:
        md = mplayer_get_meta(md, service='cdda')

    elif source.startswith('remote'):
        # For a 'remote.....' named source, it is expected to have
        # an IP address kind of in its jack_pname field:
        #   jack_pname:  X.X.X.X:PPPP
        # so this way we can query metadata from the remote address.
        host = SOURCES[source]["jack_pname"].split(':')[0]
        port = SOURCES[source]["jack_pname"].split(':')[-1]
        if is_IP(host):
            if not port.isdigit():
                port = 9990
            md = remote_get_meta( host, port )

    # If there is no artist or album information, let's use the source name
    if md['artist'] == '-' and md['album'] == '-':
        md['artist'] = f'- {source.upper()} -'

    return md


def playback_control(cmd, arg=''):
    """ Controls the playback, depending on the involved source player.
        returns: 'stop' | 'play' | 'pause'
    """

    result = 'stop'
    source = read_state_from_disk()['input']

    if source == 'mpd':
        result = mpd_control(cmd, arg)

    elif source.lower() == 'spotify':
        if   SPOTIFY_CLIENT == 'desktop':
            result = spotify_control(cmd, arg)
        elif SPOTIFY_CLIENT == 'librespot':
            result = librespot_control(cmd)
        else:
            result = 'stop'

    elif 'tdt' in source or 'dvb' in source:
        result = mplayer_control(cmd=cmd, service='dvb')

    elif source in ['istreams', 'iradio']:
        result = mplayer_control(cmd=cmd, service='istreams')

    elif source == 'cd':
        result = mplayer_control(cmd=cmd, arg=arg, service='cdda')

    elif source.startswith('remote'):
        # For a 'remote.....' named source, it is expected to have
        # an IP address kind of in its jack_pname field:
        #   jack_pname:  X.X.X.X:PPPP
        # so this way we can query metadata from the remote address.
        host = SOURCES[source]["jack_pname"].split(':')[0]
        port = SOURCES[source]["jack_pname"].split(':')[-1]

        # (i) we assume that the remote pe.audio.sys listen at standard 9990 port
        if is_IP(host):
            if not port.isdigit():
                port = 9990
            result = remote_player_control( cmd=cmd, arg=arg, host=host, port=port )

    return result


def playlists_control(cmd, arg):
    """ Manage playlists.
        (i) Currently only works with: Spotify Desktop, MPD.
    """
    result = []
    source = read_state_from_disk()['input']

    if source == 'mpd':
        result = mpd_playlists(cmd, arg)

    elif source == 'spotify':

        if   SPOTIFY_CLIENT == 'desktop':
            result = spotify_playlists(cmd, arg)

    elif source == 'cd':
        result = mplayer_playlists(cmd=cmd, arg=arg, service='cdda')

    return result


def random_control(arg):
    """ Controls the random/shuffle playback mode
        (i) Currently only works with: MPD
    """
    result = 'n/a'
    source = read_state_from_disk()['input']

    if source == 'mpd':
        result = mpd_control('random', arg)

    elif source == 'spotify':

        if   SPOTIFY_CLIENT == 'desktop':
            result = spotify_control('random', arg)
        elif SPOTIFY_CLIENT == 'librespot':
            result = librespot_control('random', arg)

    return result


def get_all_info():
    """ A wrapper to get all playback related info at once,
        useful for web control clients querying
    """
    return {
            'state':        playback_control( 'state' ),
            'random_mode':  random_control('get'),
            'metadata':     CURRENT_MD,
            'discid':       read_cdda_info_from_disk()['discid']
            }


# Autoexec when loading this module
def init():
    """ This init function will thread the storing metadata LOOP FOREVER
    """

    def store_meta_loop(period=2):
        global CURRENT_MD
        while True:
            # Update the global runtime variable CURRENT_MD
            CURRENT_MD = get_meta()
            # Save metadata to disk file.
            with open(PLAYER_META_PATH, 'w') as f:
                f.write( json.dumps( CURRENT_MD ) )
            # Wait for period
            sleep(period)

    # Loop storing metadata
    period = CURRENT_MD_REFRESH
    meta_loop = threading.Thread( target=store_meta_loop, args=(period,) )
    meta_loop.start()


# Main interface function for this module
def do(cmd, arg):
    """ Entry interface function for a parent server.py listener.
        - in:   a command phrase
        - out:  a string result (dicts are json dumped)
    """

    if cmd in ( 'state', 'stop', 'pause', 'play', 'next', 'previous',
                'rew', 'ff', 'play_track'):
        result = playback_control( cmd, arg )

    elif cmd == 'random_mode':
        result = random_control(arg)

    elif cmd == 'get_meta':
        result = CURRENT_MD

    elif cmd == 'get_all_info':
        result = get_all_info()

    elif '_playlist' in cmd:
        result = playlists_control( cmd, arg )

    elif cmd == 'eject':
        result = mplayer_control('eject', service='cdda')

    else:
        result = f'(players) unknown command \'{cmd}\''

    return result


# Autoexec when loading this module
init()
