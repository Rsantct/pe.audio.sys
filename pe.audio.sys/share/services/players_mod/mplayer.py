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

""" A module to deal with playing services supported by Mplayer:
        DVB-T
        CDDA
        istreams
"""

# (i) I/O FILES MANAGED HERE:
#
# .cdda_info        'w'     CDDA album and tracks info in json format
#
# .{service}_fifo   'w'     Mplayer command input fifo,
#                           (remember to end commands with \n)
# .{service}_events 'r'     Mplayer info output is redirected here
#

import os, sys
from subprocess import Popen, check_output
import json
import yaml
from time import sleep
from socket import socket

sys.path.append( os.path.dirname(__file__) )
import cdda

ME          = __file__.split('/')[-1]
UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'


## generic metadata template
METATEMPLATE = {
    'player':       'Mplayer',
    'time_pos':     '',
    'time_tot':     '',
    'bitrate':      '',
    'artist':       '',
    'album':        '',
    'title':        '',
    'track_num':    '',
    'state':        'stop'
    }

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

## pe.audio.sys services addressing
try:
    with open(f'{MAINFOLDER}/config.yml', 'r') as f:
        cfg = yaml.safe_load(f)
        CTL_PORT = cfg['peaudiosys_port']
except:
    print(f'({ME}) ERROR with \'pe.audio.sys/config.yml\'')
    exit()

# Auxiliary client to MUTE the preamp when CDDA is paused.
def audio_mute(mode):
    with socket() as s:
        try:
            host, port = 'localhost', CTL_PORT
            s.connect( (host, port) )
            s.send( f'preamp mute {mode}'.encode() )
            s.close()
            print (f'({ME}) sending \'mute {mode}\' to \'peaudiosys\'')
        except:
            print (f'({ME}) socket error on {host}:{port}')
    return

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

# Aux Mplayer metadata only for the CDDA service
def cdda_meta():

    # Aux to get the current track and track time position by querying Mplayer 'time_pos'
    # (i) 'get_property chapter' produces cd audio gaps :-/
    #     'time_pos'             does not :-)
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

    # Reading the CD info from a json file previously dumped when playing started.
    try:
        with open(f'{MAINFOLDER}/.cdda_info', 'r') as f:
            tmp = f.read()
        cd_info = json.loads(tmp)
    except:
        cd_info = cdda.cdda_meta_template()

    # Getting the current track and track time position.
    md['track_num'], md['time_pos'] = get_current_track_from_mplayer_time_pos()

    # Completing the metadata dict:
    md['artist'] = cd_info['artist']
    md['album'] = cd_info['album']

    if md['track_num'] in cd_info.keys():
        md['title']     = cd_info[ md['track_num'] ]['title']
        md['time_tot']  = cd_info[ md['track_num'] ]['length'][:-3] # omit decimals
    else:
        md['title'] = 'Track ' + md['track_num']

    # adding last track to track_num metadata
    last_track = len( [ x for x in cd_info if x.isdigit() ] )
    md['track_num'] += f'\n{last_track}'

    return md

# MAIN Mplayer metadata
def mplayer_meta(service, readonly=False):
    """ gets metadata from Mplayer as per
        http://www.mplayerhq.hu/DOCS/tech/slave.txt
    """
    # This works only for DVB or iSTREAMS, but not for CDDA
    if service == 'cdda':
        return json.dumps( cdda_meta() )

    md = METATEMPLATE.copy()

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

# MAIN Mplayer control (used for all Mplayer services: DVB, iSTREAMS and CD)
def mplayer_cmd(cmd, service):
    """ Sends a command to Mplayer trough by its input fifo
        input:  a command string
        result: a result string
    """

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


    # (i) Mplayer sends its responses to the terminal where Mplayer was launched,
    #     or to a redirected file.
    #     See available commands at http://www.mplayerhq.hu/DOCS/tech/slave.txt

    # (i) "keep_pausing get_property pause" doesn't works well with CDDA
    # so will keep a variable to selfcontrol the CDDA plating status.
    global cdda_playing_status
    if cmd == 'state':
        if service == 'cdda':
            return cdda_playing_status
        else:
            return 'play'

    eject_disk = False

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
                    audio_mute('on')
                elif cdda_playing_status == 'play':
                    audio_mute('off')

        elif cmd.startswith('play'):

            # Prepare to play if a disk is not loaded into Mplayer
            if not cdda_in_mplayer():
                audio_mute('on')
                print( f'({ME}) loading disk ...' )
                # Save disk info into a json file
                cdda.save_disc_metadata(device=CDROM_DEVICE,
                                        fname=f'{UHOME}/pe.audio.sys/.cdda_info')
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
                    print( f'({ME}) waiting for Mplayer to load disk' )
                    sleep(1)
                    n -= 1
                if n:
                    print( '({ME}) Mplayer disk loaded' )
                else:
                    print( '({ME}) TIMED OUT detecting '
                            'Mplayer disk loaded' )

            # Retrieving the current track
            curr_track = 1
            if cdda_playing_status in ('play', 'pause'):
                curr_track = cdda_meta()['track_num'].split()[0]

            if cmd.startswith('play_track_'):
                curr_track = cmd[11:]
                if not curr_track.isdigit():
                    tmp = f'({ME}) BAD command {cmd}'
                    print( tmp )
                    return tmp

            chapter = int(curr_track) -1
            cmd = f'seek_chapter {str(chapter)} 1'
            cdda_playing_status = 'play'

        elif cmd == 'eject':
            cmd = 'stop'
            eject_disk = True

    else:
        tmp = f'({ME}) unknown Mplayer service \'{service}\''
        print( tmp )
        return tmp

    # Sending the command to the corresponding fifo
    print( f'({ME}) sending \'{cmd}\' to Mplayer (.{service}_fifo)' )
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
            audio_mute('off')

    if eject_disk:
        # Eject
        Popen( f'eject {CDROM_DEVICE}'.split() )
        # Flush .cdda_info (blank the metadata file)
        with open( f'{MAINFOLDER}/.cdda_info', 'w') as f:
            f.write( json.dumps( cdda.cdda_meta_template() ) )
        # Unmute preamp
        audio_mute('off')

    return 'done'
