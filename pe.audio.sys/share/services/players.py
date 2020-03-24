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


""" A module that controls and retrieve metadata info from the current player.
    This module is ussually called from a listening server.
"""

# (i) I/O FILES MANAGED HERE:
#
# .cdda_info        'w'     CDDA album and tracks info in json format
#
# .{service}_fifo   'w'     Generic Mplayer command input fifo,
#                           (remember to end commands with \n)
# .{service}_events 'r'     generic Mplayer info output is redirected here
# 
# .state.yml        'r'     pe.audio.sys state file
#

import os
import subprocess as sp
import yaml
import mpd
from time import sleep
import json
from socket import socket
from  players_mod.mpd import mpd_client
from  players_mod.librespot import librespot_meta
from  players_mod.spotify_desktop import spotify_control, \
                                         spotify_meta, \
                                         detect_spotify_client
UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'

## Spotify client detection
spotify_client = detect_spotify_client()

## pe.audio.sys services addressing
try:
    with open(f'{MAINFOLDER}/config.yml', 'r') as f:
        A = yaml.safe_load(f)['services_addressing']
        CTL_HOST, CTL_PORT = A['pasysctrl_address'], A['pasysctrl_port']
except:
    print('ERROR with \'pe.audio.sys/config.yml\'')
    exit()

## CDDA settings
# cdrom device to use from .mplayer/config
try:
    with open(f'{UHOME}/.mplayer/config', 'r') as f:
        tmp = f.readlines()
        tmp = [x for x in tmp if 'cdrom-device' in x  and not '#' in x][0] \
                .strip().split('=')[-1].strip()
        CDROM_DEVICE = tmp
except:
    CDROM_DEVICE = '/dev/cdrom'
# Global variables to store the CDDA Audio info and CDDA playing status
# (see mplayer_cmd() below)
cd_info = {}
cdda_playing_status = 'stop'

## METADATA GENERIC TEMPLATE to serve to clients as the control web page.
#  (!) remember to use copies of this ;-)
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

# Auxiliary to talk to the main pe.audio.sys control service
def control_cmd(cmd):
    host, port = CTL_HOST, CTL_PORT
    with socket() as s:
        try:
            s.connect( (host, port) )
            s.send( cmd.encode() )
            s.close()
            print (f'(players.py) sending \'{cmd }\' to \'pasysctrl\'')
        except:
            print (f'(players.py) service \'pasysctrl\' socket error on port {port}')
    return

# Mplayer control (used for all Mplayer services: DVB, iSTREAMS and CD)
def mplayer_cmd(cmd, service):
    """ Sends a command to Mplayer trough by its input fifo
    """
    # Notice: Mplayer sends its responses to the terminal where Mplayer was launched,
    #         or to a redirected file.

    # See available commands at http://www.mplayerhq.hu/DOCS/tech/slave.txt

    global cdda_playing_status

    # "keep_pausing get_property pause" doesn't works well with CDDA
    # so will keep a variable to selfcontrol the CDDA plating status.
    if cmd == 'state':
        if service == 'cdda':
            return cdda_playing_status
        else:
            return 'play'

    eject_disk = False

    # Aux function to save the CD info to a json file
    def save_cd_info():

        global cd_info

        # CDDA info is based on external shell program 'cdcd'
        # Example using cdcd
        #   $ cdcd tracks
        #   Album name:     All For You
        #   Album artist:   DIANA KRALL
        #   Total tracks:   13      Disc length:    59:19
        #
        #   Track   Length      Title
        #   ----------------------------------------------------------------------------------------------------------
        #    1:     [ 2:56.13]  I'm An Errand Girl For Rhythm
        #    2:     [ 4:07.20]  Gee Baby, Ain't I Good To You
        #    3:     [ 4:37.10]  You Call It Madness
        #    4:     [ 5:00.52]  Frim Fram Sauce
        #    5:     [ 6:27.15]  Boulevard Of Broken Dreams
        #    6:     [ 3:36.10]  Baby Baby All The Time
        #    7:     [ 4:16.55]  Hit That Jive Jack
        #    8:     [ 5:33.10]  You're Looking At Me
        #    9:     [ 4:25.73]  I'm Thru With Love
        #   10:     [ 3:31.52]  Deed I Do
        #   11:     [ 5:12.58]  A Blossom Fell
        #   12:   > [ 4:56.67]  If I Had You
        #   13:     [ 4:35.00]  When I Grow Too Old To Dream

        tmp = ''
        cd_info = {}
        try:
            tmp = sp.check_output(f'/usr/bin/cdcd -d {CDROM_DEVICE} tracks', shell=True).decode('utf-8').split('\n')
        except:
            try:
                tmp = sp.check_output(f'/usr/bin/cdcd -d {CDROM_DEVICE} tracks', shell=True).decode('iso-8859-1').split('\n')
            except:
                print( '(players.py) Problem running the program \'cdcd\' for CDDA metadata reading.' )
                print( '             Check also your cdrom-device setting under .mplayer/config' )


        for line in tmp:


            if line.startswith('Album name'):
                cd_info['album'] = line[16:].strip()

            if line.startswith('Album artist'):
                cd_info['artist'] = line[16:].strip()

            if line and line[2] == ':' and line[8] == '[':
                track_num       = line[:2].strip()
                track_length    = line[9:17].strip()
                track_title     = line[20:].strip()

                cd_info[track_num] = {}
                cd_info[track_num]['length'] = track_length
                cd_info[track_num]['title']  = track_title

        with open( f'{MAINFOLDER}/.cdda_info', 'w') as f:
            f.write( json.dumps( cd_info ) )
        print( f'(players.py) CD info saved to {MAINFOLDER}/.cdda_info' )

    # Aux function to check if Mplayer has loaded a disk
    def cdda_in_mplayer():
        # Querying Mplayer to get the FILENAME (if it results void it means no playing)
        with open(f'{MAINFOLDER}/.cdda_fifo', 'w') as f:
            f.write('get_file_name\n')
        sleep(.1)
        with open(f'{MAINFOLDER}/.cdda_events', 'r') as f:
            tmp = f.read().split('\n')
        for line in tmp[-2::-1]:
            if line.startswith('ANS_FILENAME='):
                return True
        return False

    if service == 'istreams':

        # useful when playing a mp3 stream e.g. some long playing time podcast url
        if   cmd == 'previous':   cmd = 'seek -300 0'
        elif cmd == 'rew':        cmd = 'seek -60  0'
        elif cmd == 'ff':         cmd = 'seek +60  0'
        elif cmd == 'next':       cmd = 'seek +300 0'

    elif service == 'dvb':

        # (i) all this stuff is testing and not much useful
        if   cmd == 'previous':   cmd = 'tv_step_channel previous'
        elif cmd == 'rew':        cmd = 'seek_chapter -1 0'
        elif cmd == 'ff':         cmd = 'seek_chapter +1 0'
        elif cmd == 'next':       cmd = 'tv_step_channel next'

    elif service == 'cdda':

        if   cmd == 'previous':   cmd = 'seek_chapter -1 0'
        elif cmd == 'rew':        cmd = 'seek -30 0'
        elif cmd == 'ff':         cmd = 'seek +30 0'
        elif cmd == 'next':       cmd = 'seek_chapter +1 0'
        elif cmd == 'stop':
            cmd = 'stop'
            cdda_playing_status = 'stop'

        elif cmd == 'pause' or (cmd == 'play' and
                                cdda_playing_status == 'pause'):
            cmd = 'pause'
            if cdda_playing_status in ('play', 'pause'):
                cdda_playing_status =   {'play':'pause', 'pause':'play'
                                        }[cdda_playing_status]
                # (i) Because of mplayer cdda pausing becomes on
                #     strange behavior (there is a kind of brief sttuter 
                #     with audio), then we will MUTE the preamp.
                if cdda_playing_status == 'pause':
                    control_cmd('mute on')
                elif cdda_playing_status == 'play':
                    control_cmd('mute off')

        elif cmd.startswith('play'):

            # Prepare to play if a disk is not loaded into Mplayer
            if not cdda_in_mplayer():
                control_cmd('mute on')
                print( f'(players.py) loading disk ...' )
                # Save disk info into a json file
                save_cd_info()
                # Flushing the mplayer events file
                with open(f'{MAINFOLDER}/.cdda_events', 'w') as f:
                    pass
                # Loading the disk but pausing
                with open(f'{MAINFOLDER}/.cdda_fifo', 'w') as f:
                    f.write( 'pausing loadfile \'cdda://1-100:1\'\n' )
                # Waiting for the disk to be loaded (usually about 8 sec)
                n = 15
                while n:
                    if cdda_in_mplayer(): break
                    print( f'(players.py) waiting for Mplayer to load disk' ) 
                    sleep(1)
                    n -= 1
                if n:
                    print( '(players.py) Mplayer disk loaded' )
                else:
                    print( '(players.py) TIMED OUT detecting '
                            'Mplayer disk loaded' )

            # Retrieving the current track 
            curr_track = 1
            if cdda_playing_status in ('play', 'pause'):
                curr_track = json.loads( cdda_meta() )['track_num'].split()[0]

            if cmd.startswith('play_track_'):
                curr_track = cmd[11:]
                if not curr_track.isdigit():
                    return

            chapter = int(curr_track) -1
            cmd = f'seek_chapter {str(chapter)} 1'
            cdda_playing_status = 'play'

        elif cmd == 'eject':
            cmd = 'stop'
            eject_disk = True

    else:
        print( f'(players.py) unknown Mplayer service \'{service}\'' )
        return

    # Sending the command to the corresponding fifo
    print( f'(players.py) sending \'{cmd}\' to Mplayer (.{service}_fifo)' )
    with open(f'{MAINFOLDER}/.{service}_fifo', 'w') as f:
        f.write( f'{cmd}\n' )

    if service == 'cdda':
        if cmd == 'stop':
            # clearing cdda_events in order to forget last track
            with open(f'{MAINFOLDER}/.cdda_events', 'w') as f:
                pass
        elif 'seek_chapter' in cmd:
            # This delay avoids audio stutter because of above pausing,
            # done when preparing (loading) traks into Mplayer
            sleep(.5)
            control_cmd('mute off')

    if eject_disk:
        # Eject
        sp.Popen( f'eject {CDROM_DEVICE}'.split() )
        # Flush .cdda_info (blank the metadata file)
        with open( f'{MAINFOLDER}/.cdda_info', 'w') as f:
            f.write( "{}" ) 

# Mplayer metadata (only for DVB or iSTREAMS, but not usable for CDDA)
def mplayer_meta(service, readonly=False):
    """ gets metadata from Mplayer as per
        http://www.mplayerhq.hu/DOCS/tech/slave.txt """

    md = METATEMPLATE.copy()
    md['player'] = 'Mplayer'

    # This is the file were Mplayer standard output has been redirected to,
    # so we can read there any answer when required to Mplayer slave daemon:
    mplayer_redirection_path = f'{MAINFOLDER}/.{service}_events'

    # Communicates to Mplayer trough by its input fifo to get the current media filename and bitrate:
    if not readonly:
        mplayer_cmd(cmd='get_audio_bitrate', service=service)
        mplayer_cmd(cmd='get_file_name',     service=service)
        mplayer_cmd(cmd='get_time_pos',      service=service)
        mplayer_cmd(cmd='get_time_length',   service=service)
        # Waiting Mplayer ANS_xxxx to be writen to output file
        sleep(.25)

    # Trying to read the ANS_xxxx from the Mplayer output file
    with open(mplayer_redirection_path, 'r') as file:
        try:
            tmp = file.read().split('\n')[-5:] # get last 4 lines plus the empty one when splitting
        except:
            tmp = []

    #print('DEBUG\n', tmp)

    # Flushing the Mplayer output file to avoid continue growing:
    if not readonly:
        with open(mplayer_redirection_path, 'w') as file:
            file.write('')

    # Reading the intended metadata chunks
    if len(tmp) >= 4: # to avoid indexes issues while no relevant metadata are available

        if 'ANS_AUDIO_BITRATE=' in tmp[0]:
            bitrate = tmp[0].split('ANS_AUDIO_BITRATE=')[1].split('\n')[0].replace("'","")
            md['bitrate'] = bitrate.split()[0]

        if 'ANS_FILENAME=' in tmp[1]:
            # this way will return the whole url:
            #md['title'] = tmp[1].split('ANS_FILENAME=')[1]
            # this way will return just the filename:
            md['title'] = tmp[1].split('ANS_FILENAME=')[1].split('?')[0].replace("'","")

        if 'ANS_TIME_POSITION=' in tmp[2]:
            time_pos = tmp[2].split('ANS_TIME_POSITION=')[1].split('\n')[0]
            md['time_pos'] = timeFmt( float( time_pos ) )

        if 'ANS_LENGTH=' in tmp[3]:
            time_tot = tmp[3].split('ANS_LENGTH=')[1].split('\n')[0]
            md['time_tot'] = timeFmt( float( time_tot ) )

    return json.dumps( md )

# Mplayer metadata only for the CDDA service
def cdda_meta():

    # Aux to get the current track by using the external program 'cdcd tracks'
    # CURRENTLY NOT USED.
    def get_current_track_from_cdcd():
        t = "1"
        try:
            tmp = sp.check_output(f'/usr/bin/cdcd -d {CDROM_DEVICE} tracks', shell=True).decode('utf-8').split('\n')
        except:
            try:
                tmp = sp.check_output(f'/usr/bin/cdcd -d {CDROM_DEVICE} tracks', shell=True).decode('iso-8859-1').split('\n')
            except:
                print( 'players.py: problem running the program \'cdcd\' for CDDA metadata reading' )
                print( '             Check also your cdrom-device setting under .mplayer/config' )
        for line in tmp:
            if line and line[6] == '>':
                t = line[:2].strip()
        return t

    # Aux to get the current track by querying Mplayer 'chapter'
    # NOT USED because it is observed that querying Mplayer with
    # 'get_property chapter' produces cd audio gaps :-/
    def get_current_track_from_mplayer_chapter():
        t = 0
        # (!) Must use the prefix 'pausing_keep', otherwise pause will be released
        #     when querying 'get_property ...' or anything else.
        with open(f'{MAINFOLDER}/.cdda_fifo', 'w') as f:
            f.write( 'pausing_keep get_property chapter\n' )
        with open(f'{MAINFOLDER}/.cdda_events', 'r') as f:
            tmp = f.read().split('\n')
        for line in tmp[-10:]:
            if line.startswith('ANS_chapter='):
                t = line.replace('ANS_chapter=', '').strip()
        # ANS_chapter counts from 0 for 1st track
        return str( int(t) + 1 )

    # Aux to get the current track and track time position by querying Mplayer 'time_pos'
    # USED: fortunately querying 'time_pos' does not produce any audio gap :-)
    def get_current_track_from_mplayer_time_pos():

        # (i) When querying Mplayer, always must use the prefix 'pausing_keep',
        #     otherwise pause will be released.

        # Aux to derive the track and the track time position from
        # the whole disk relative time position.
        def get_track_and_pos(globalPos):
            trackNum = 1
            cummTracksLength = 0.0
            trackPos = 0.0
            # Iterate tracks until globalPos is exceeded
            while str(trackNum) in cd_info:
                trackLength = timestring2sec( cd_info[ str(trackNum) ]['length'] )
                cummTracksLength += trackLength
                if cummTracksLength > globalPos:
                    trackPos = globalPos - ( cummTracksLength - trackLength )
                    break
                trackNum += 1
            return trackNum, trackPos

        track    = 1
        trackPos = 0
        globalPos  = 0

        # Querying Mplayer to get the timePos, the answer in seconds will be
        # a 'global position' refered to the global disk duration.
        with open(f'{MAINFOLDER}/.cdda_fifo', 'w') as f:
            f.write( 'pausing_keep get_time_pos\n' )
        with open(f'{MAINFOLDER}/.cdda_events', 'r') as f:
            tmp = f.read().split('\n')
        for line in tmp[-10:]:
            if line.startswith('ANS_TIME_POSITION='):
                globalPos = float( line.replace('ANS_TIME_POSITION=', '').strip() )

        # Find the track and track time position
        track, trackPos = get_track_and_pos(globalPos)

        # Ceiling track to the last available
        last_track = len( [ x for x in cd_info if x.isdigit() ] )
        if track > last_track:
            track = last_track

        return str( track ), timeFmt( trackPos )

    # Initialize a metadata dictionary
    md = METATEMPLATE.copy()
    md['track_num'] = '1'
    md['bitrate'] = '1411'
    md['player']  = 'Mplayer'

    # Reading the CD info from a json file previously dumped when playing started.
    try:
        with open(f'{MAINFOLDER}/.cdda_info', 'r') as f:
            tmp = f.read()
        cd_info = json.loads(tmp)
    except:
        cd_info = {}

    # Getting the current track and track time position.
    md['track_num'], md['time_pos'] = get_current_track_from_mplayer_time_pos()

    # Completing the metadata dict, skipping if not cd_info available:
    if cd_info:

        # if cdcd cannot retrieve cddb info, artist or album field will be not dumped.
        if 'artist' in cd_info:
            if cd_info['artist']:
                md['artist'] = cd_info['artist']
        else:
            md['artist'] = 'CD info not found'

        if 'album' in cd_info:
            if cd_info['album']:
                md['album'] = cd_info['album']

        title = cd_info[ md['track_num'] ]['title']

        if title:
            md['title'] = cd_info[ md['track_num'] ]['title']
        else:
            md['title'] = 'Track ' + md['track_num']

        md['time_tot']   = cd_info[ md['track_num'] ]['length'][:-3] # omit decimals

        # adding last track to track_num metadata
        last_track = len( [ x for x in cd_info if x.isdigit() ] )
        md['track_num'] += f'\n{last_track}'

    return json.dumps( md )

# Generic function to get meta from any player: MPD, Mplayer or Spotify
def player_get_meta(readonly=False):
    """ Makes a dictionary-like string with the current track metadata
        '{player: xxxx, artist: xxxx, album:xxxx, title:xxxx, etc... }'
        Then will return a bytes-like object from the referred string.
    """
    # 'readonly=True':
    #   Only useful for mplayer_meta(). It avoids to query Mplayer
    #   and flushing its metadata file.
    #   It is used from the 'change files handler' on lcd_service.py.

    metadata = METATEMPLATE.copy()
    source = get_source()

    if   'librespot' in source or 'spotify' in source.lower():
        if spotify_client == 'desktop':
            metadata = spotify_meta()
        elif spotify_client == 'librespot':
            metadata = librespot_meta()
        # source is spotify like but no client running has been detected:
        else:
            metadata = json.dumps( metadata )

    elif source == 'mpd':
        metadata = mpd_client('get_meta')

    elif source == 'istreams':
        metadata = mplayer_meta(service=source, readonly=readonly)

    elif source == 'tdt' or 'dvb' in source:
        metadata = mplayer_meta(service='dvb', readonly=readonly)

    elif source == 'cd':
        metadata = cdda_meta()

    else:
        metadata = json.dumps( metadata )

    # As this is used by a server, we will return a bytes-like object:
    return metadata.encode()

# Generic function to control any player
def player_control(action):
    """ controls the playback
        returns: 'stop' | 'play' | 'pause'
    """

    source = get_source()
    result = ''

    if   source == 'mpd':
        result = mpd_client(action)

    elif source.lower() == 'spotify' and spotify_client == 'desktop':
        # We can control only Spotify Desktop (not librespot)
        result = spotify_control(action)

    elif 'tdt' in source or 'dvb' in source:
        result = mplayer_cmd(cmd=action, service='dvb')

    elif source in ['istreams', 'iradio']:
        result = mplayer_cmd(cmd=action, service='istreams')

    elif source == 'cd':
        result = mplayer_cmd(cmd=action, service='cdda')

    # Currently only MPD and Spotify Desktop provide 'state' info.
    # 'result' can be 'play', 'pause', 'stop' or ''.
    if not result:
        result = '' # to avoid None.encode() error

    # As this is used by a server, we will return a bytes-like object:
    return result.encode()

# Gets the current input source on pre.di.c
def get_source():
    """ retrieves the current input source """
    source = None
    # It is possible to fail while state file is updating :-/
    times = 4
    while times:
        try:
            source = get_state()['input']
            break
        except:
            times -= 1
        sleep(.25)
    return source

# Gets the dictionary of pre.di.c status
def get_state():
    """ returns the YAML state info """
    with open( MAINFOLDER + '/.state.yml', 'r') as f:
        return yaml.safe_load(f)

# Auxiliary function to format hh:mm:ss
def timeFmt(x):
    # x must be float
    h = int( x / 3600 )         # hours
    x = int( round(x % 3600) )  # updating x to reamining seconds
    m = int( x / 60 )           # minutes from the new x
    s = int( round(x % 60) )    # and seconds
    return f'{h:0>2}:{m:0>2}:{s:0>2}'

# Aux to convert a given formatted time string "hh:mm:ss.cc" to seconds
def timestring2sec(t):
    s = 0.0
    t = t.split(':')
    if len(t) > 2:
        s += float( t[-3] ) * 3600
    if len(t) > 1:
        s += float( t[-2] ) * 60
    if len(t) >= 1:
        s += float( t[-1] )
    return s

# Interface entry function to this module
def do(task):
    """
        This do() is the entry interface function from a listening server.
        Only certain received 'tasks' will be validated and processed,
        then returns back some useful info to the asking client.
    """

    # First clearing the taksk phrase
    task = task.strip()

    # task: 'player_get_meta'
    # Tasks querying the current music player.
    if   task == 'player_get_meta':
        return player_get_meta()

    # task: 'player_xxxxxxx'
    # Playback control. (i) Some commands need to be adequated later, depending on the player,
    # e.g. Mplayer does not understand 'previous', 'next' ...
    elif task[7:] in ('state', 'stop', 'pause', 'play', 'next', 'previous', 'rew', 'ff'):
        return player_control( task[7:] )

    # task: 'player_eject' unconditionally ejects the CD tray
    elif task[7:] == 'eject':
        return mplayer_cmd('eject', 'cdda')

    # task: 'player_play_track_NN'
    # Special command for disk playback control
    elif task[7:18] == 'play_track_':
        return player_control( task[7:] )

    # task: 'http://an/url/stream/to/play
    # A pseudo task, an url to be played back:
    elif task[:7] == 'http://':
        sp.Popen( f'{MAINFOLDER}/share/scripts/istreams.py url {task}'.split() )
    
