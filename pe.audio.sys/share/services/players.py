#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

# This is based on 'pre.di.c,' a preamp and digital crossover
# https://github.com/rripio/pre.di.c
# Copyright (C) 2018 Roberto Ripio
# 'pre.di.c' is based on 'FIRtro', a preamp and digital crossover
# https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
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

# TODO: a command line interface could be useful

import os
import subprocess as sp
import yaml
import mpd
import time
import json

UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'

# A global variable to store the CD Audio info
cd_info = {}


# MPD settings:
MPD_HOST    = 'localhost'
MPD_PORT    = 6600
MPD_PASSWD  = None

# The METADATA GENERIC TEMPLATE for pre.di.c clients, for example the web control page:
# (!) Remember to use copies of this ;-)
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

# Check for the SPOTIFY Client in use:
SPOTIFY_CLIENT = None
librespot_bitrate = '-'
spotify_bitrate   = '-'
# Check if a desktop client is running:
try:
    sp.check_output( 'pgrep -f Spotify'.split() )
    # still pending how to retrieve the Desktop client bitrate
    SPOTIFY_CLIENT = 'desktop'
except:
    pass
# Check if 'librespot' (a Spotify Connect daemon) is running:
try:
    sp.check_output( 'pgrep -f librespot'.split() )
    # Gets librespot bitrate from librespot running process:
    try:
        tmp = sp.check_output( 'pgrep -fa /usr/bin/librespot'.split() ).decode()
        # /usr/bin/librespot --name rpi3clac --bitrate 320 --backend alsa --device jack --disable-audio-cache --initial-volume=99
        librespot_bitrate = tmp.split('--bitrate')[1].split()[0].strip()
    except:
        pass
    SPOTIFY_CLIENT = 'librespot'
except:
    pass

# MPD control, status and metadata
def mpd_client(query):
    """ comuticates to MPD music player daemon """

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

# Mplayer control (used for DVB, iSTREAMS and CD)
def mplayer_cmd(cmd, service):
    """ Sends a command to Mplayer trough by its input fifo """
    # Notice: Mplayer sends its responses to the terminal where Mplayer was launched,
    #         or to a redirected file.

    # See available commands at http://www.mplayerhq.hu/DOCS/tech/slave.txt

    # Avoiding to process 'state' because Mplayer has not a such function. 
    if cmd == 'state':
        return

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
            tmp = sp.check_output('/usr/bin/cdcd tracks', shell=True).decode('utf-8').split('\n')
        except:
            try:
                tmp = sp.check_output('/usr/bin/cdcd tracks', shell=True).decode('iso-8859-1').split('\n')
            except:
                print( '(players.py) Problem running the program \'cdcd\' for CDDA metadata reading' )


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
    
    # Aux function to check if Mplayer is playing the disk
    def a_file_is_loaded():
        # Querying Mplayer to get the FILENAME (if it results void it means no playing)
        sp.Popen( f'echo "get_file_name" > {MAINFOLDER}/cdda_fifo', shell=True )
        with open(f'{MAINFOLDER}/.cdda_events', 'r') as f:
            tmp = f.read().split('\n')
        time.sleep(.5)
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
        elif cmd == 'pause':      cmd = 'pause'
        elif cmd == 'stop':       cmd = 'stop'

        elif cmd == 'play':
            # save disk info into a json file
            save_cd_info()
            # flushing the mplayer events file
            sp.Popen( f'echo "" > {MAINFOLDER}/.cdda_events', shell=True)
            cmd = f'loadfile \'cdda://1-100:1\''

        elif cmd.startswith('play_track_'):
            trackNum = cmd[11:]
            if trackNum.isdigit():
                # Checks if a filename is loaded (i.e. if a disk is loaded to be played)
                if not a_file_is_loaded():
                    # save disk info into a json file
                    save_cd_info()
                    # flushing the mplayer events file
                    sp.Popen( f'echo "" > {MAINFOLDER}/.cdda_events', shell=True)
                    # Loading the disk but pausing
                    tmp = f'pausing loadfile \'cdda://1-100:1\''
                    tmp = f'echo "{tmp}" > {MAINFOLDER}/{service}_fifo'
                    sp.Popen( tmp, shell=True)
                    # Waiting for the disk to be loaded:
                    n = 0
                    while n < 10:
                        if a_file_is_loaded(): break
                        time.sleep(1)
                        n += 1
                chapter = int(trackNum) -1 
                cmd = f'seek_chapter {str(chapter)} 1'

        elif cmd == 'eject':
            cmd = 'stop'
            eject_disk = True

    else:
        print( f'(players.py) unknown Mplayer service \'{service}\'' )
        return
    
    # sending the command to the corresponding fifo
    tmp = f'echo "{cmd}" > {MAINFOLDER}/{service}_fifo'
    #print(tmp) # debug
    sp.Popen( tmp, shell=True)

    if cmd == 'stop' and service == 'cdda':
        # clearing cdda_events in order to forget last track
        try:
            sp.Popen( f'echo "" > {MAINFOLDER}/.cdda_events', shell=True)
        except:
            pass

    if eject_disk:
        sp.Popen( 'eject' )

# Mplayer metadata (DVB or iSTREAMS, but not usable for CDDA)
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
        time.sleep(.25)

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

def cdda_meta():
    
    # Aux to get the current track by using the external program 'cdcd tracks'
    # CURRENTLY NOT USED.
    def get_current_track_from_cdcd():
        t = "1"
        try:
            tmp = sp.check_output('/usr/bin/cdcd tracks', shell=True).decode('utf-8').split('\n')
        except:
            try:
                tmp = sp.check_output('/usr/bin/cdcd tracks', shell=True).decode('iso-8859-1').split('\n')
            except:
                print( 'players.py: problem running the program \'cdcd\' for CDDA metadata reading' )
        for line in tmp:
            if line and line[6] == '>':
                t = line[:2].strip()
        return t
    
    # (i) When querying Mplayer, always must use the prefix 'pausing_keep', 
    #     otherwise pause will be released.
    
    # Aux to get the current track by querying Mplayer 'chapter'
    # NOT USED because it is observed that querying Mplayer with 
    # 'get_property chapter' produces cd audio gaps :-/
    def get_current_track_from_mplayer_chapter():
        t = 0
        # (!) Must use the prefix 'pausing_keep', otherwise pause will be released
        #     when querying 'get_property ...' or anything else.
        sp.Popen( f'echo "pausing_keep get_property chapter" > {MAINFOLDER}/cdda_fifo', shell=True )
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

        # Aux to derive the track and the track time position from
        # the whole disk relative time position.
        def get_track_and_pos(timePos):            
            n = 1
            tracksLength = 0.0
            trackPos = 0.0
            # Iterate tracks until timePos is exceeded
            while str(n) in cd_info:
                trackLength = timestring2sec( cd_info[ str(n) ]['length'] )
                tracksLength += trackLength
                if tracksLength > timePos:
                    trackPos = timePos - ( tracksLength - trackLength )
                    break
                n += 1
            return n, trackPos
            
        track    = 1
        trackPos = 0
        timePos  = 0

        # Querying Mplayer to get the timePos over the whole disk
        sp.Popen( f'echo "pausing_keep get_time_pos" > {MAINFOLDER}/cdda_fifo', shell=True )
        with open(f'{MAINFOLDER}/.cdda_events', 'r') as f:
            tmp = f.read().split('\n')
        for line in tmp[-10:]:
            if line.startswith('ANS_TIME_POSITION='):
                timePos = float( line.replace('ANS_TIME_POSITION=', '').strip() )

        # Find the track and track time position
        track, trackPos = get_track_and_pos(timePos)
        
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

# Spotify Desktop metadata
def spotify_meta():
    """ Gets the metadata info retrieved by the daemon scripts/spotify_monitor
        which monitorizes a Spotify Desktop Client
    """
    md = METATEMPLATE.copy()
    md['player'] = 'Spotify'
    md['bitrate'] = spotify_bitrate

    try:
        events_file = f'{MAINFOLDER}/.spotify_events'
        f = open( events_file, 'r' )
        tmp = f.read()
        f.close()

        tmp = json.loads( tmp )
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
        md['time_tot'] = timeFmt( tmp["mpris:length"]/1e6 )

    except:
        pass

    return json.dumps( md )

# Spotify Desktop control
def spotify_control(cmd):
    """ Controls the Spotify Desktop player
        It is assumed that you have the mpris2-dbus utility 'playerctl' installed.
            https://wiki.archlinux.org/index.php/spotify#MPRIS
        dbus-send command can also work
            http://www.skybert.net/linux/spotify-on-the-linux-command-line/
    """
    # playerctl - Available Commands:
    #   play                    Command the player to play
    #   pause                   Command the player to pause
    #   play-pause              Command the player to toggle between play/pause
    #   stop                    Command the player to stop
    #   next                    Command the player to skip to the next track
    #   previous                Command the player to skip to the previous track
    #   position [OFFSET][+/-]  Command the player to go to the position or seek forward/backward OFFSET in seconds
    #   volume [LEVEL][+/-]     Print or set the volume to LEVEL from 0.0 to 1.0
    #   status                  Get the play status of the player
    #   metadata [KEY]          Print metadata information for the current track. Print only value of KEY if passed

    # (!) Unfortunately, 'position' does not work, so we cannot rewind neither fast forward
    if cmd in ('play', 'pause', 'next', 'previous' ):
        sp.Popen( f'playerctl --player=spotify {cmd}'.split() )

    # Retrieving the playback state
    result = ''
    if cmd == 'state':
        try:
            result = sp.check_output( f'playerctl --player=spotify status'.split() ).decode()
        except:
            pass
    # playerctl just returns 'Playing' or 'Paused'
    if 'play' in result.lower():
        return 'play'
    else:
        return 'pause'

# librespot (Spotify Connect client) metatata
def librespot_meta():
    """ gets metadata info from librespot """
    # Unfortunately librespot only prints out the title metadata, nor artist neither album.
    # More info can be retrieved from the spotify web, but it is necessary to register
    # for getting a privative and unique http request token for authentication.

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
        tmp = sp.check_output( f'tail -n20 {MAINFOLDER}/.librespot_events'.split() ).decode()
        tmp = tmp.split('\n')
        # Recently librespot uses to print out some 'AddrNotAvailable, message' mixed with
        # playback info messages, so we will search for the latest 'Track ... loaded' message,
        # backwards from the end of the events file:
        for line in tmp[::-1]:
            if "Track" in line and "loaded" in line:
                md['title'] = line.split('"')[1]
                break
    except:
        pass

    # JSON for JavaScript on control web page
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
        if SPOTIFY_CLIENT == 'desktop':
            metadata = spotify_meta()
        elif SPOTIFY_CLIENT == 'librespot':
            metadata = librespot_meta()

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
    """ controls the playback """

    source = get_source()
    result = ''

    if   source == 'mpd':
        result = mpd_client(action)

    elif source.lower() == 'spotify' and SPOTIFY_CLIENT == 'desktop':
        # We can control only Spotify Desktop (not librespot)
        result = spotify_control(action)

    elif 'tdt' in source or 'dvb' in source:
        result = mplayer_cmd(cmd=action, service='dvb')

    elif source in ['istreams', 'iradio']:
        result = mplayer_cmd(cmd=action, service='istreams')

    elif source == 'cd':
        result = mplayer_cmd(cmd=action, service='cdda')

    # Currently only MPD and Spotify Desktop provide 'state' info.
    # 'result' can be 'play', 'pause', stop' or ''.
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
        time.sleep(.25)
    return source

# Gets the dictionary of pre.di.c status
def get_state():
    """ returns the YAML state info """
    with open( MAINFOLDER + '/.state.yml', 'r') as f:
        return yaml.load( f.read() )

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

    # First clearing the new line
    task = task.replace('\n','')

    # task: 'player_get_meta'
    # Tasks querying the current music player.
    if   task == 'player_get_meta':
        return player_get_meta()

    # task: 'player_xxxxxxx'
    # Playback control. (i) Some commands need to be adequated later, depending on the player,
    # e.g. Mplayer does not understand 'previous', 'next' ...
    elif task[7:] in ('eject', 'state', 'stop', 'pause', 'play', 'next', 'previous', 'rew', 'ff'):
        return player_control( task[7:] )

    # task: 'player_play_track_NN'
    # Special command for disk playback control
    elif task[7:18] == 'play_track_':
        return player_control( task[7:] )

    # task: 'http://an/url/stream/to/play
    # A pseudo task, an url to be played back:
    elif task[:7] == 'http://':
        sp.run( f'{MAINFOLDER}/share/scripts/istreams url {task}'.split() )
