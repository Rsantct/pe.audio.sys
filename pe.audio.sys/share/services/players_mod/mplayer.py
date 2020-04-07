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

# --- Some info about Mplayer SLAVE commands ---
#
# loadfile cdda://A-B:S     load CD tracks from A to B at speed S
#
# get_property filename     get the tracks to be played as
#                           'A' (single track)
#                           or 'A-B' (range of tracks)
#
# get_property chapter      get the current track index inside
#                           the filename property (first is 0)
#
# seek_chapter 1            go to next track
# seek_chapter -1           go to prev track
#
# seek X seconds

import os, sys
from subprocess import Popen, check_output
import json
import yaml
from time import sleep
import jack

sys.path.append( os.path.dirname(__file__) )
import cdda

ME          = __file__.split('/')[-1]
UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'

## pe.audio.sys control port
try:
    with open(f'{MAINFOLDER}/config.yml', 'r') as f:
        PEASYSCONFIG = yaml.safe_load(f)
    CTL_PORT = PEASYSCONFIG['peaudiosys_port']
except:
    print(f'({ME}) ERROR with \'pe.audio.sys/config.yml\'')
    exit()
## cdrom device to use
try:
    CDROM_DEVICE = PEASYSCONFIG['cdrom_device']
except:
    CDROM_DEVICE = '/dev/cdrom'
## CD preamp ports
try:
    CD_CAPTURE_PORT = PEASYSCONFIG['sources']['cd']['capture_port']
except:
    CD_CAPTURE_PORT = 'mplayer_cdda'

## Global variable to store the playing status
playing_status = ''

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

# Aux function to check if Mplayer has loaded a disc
def cdda_is_loaded():
    """ input:      --
        output:     True | False
        I/O:        .cdda_fifo (w),  .cdda_events (r)
    """
    # Querying Mplayer to get the FILENAME
    # (if it results void it means no playing)
    with open(f'{MAINFOLDER}/.cdda_fifo', 'w') as f:
        f.write('get_file_name\n')
    sleep(.1)
    with open(f'{MAINFOLDER}/.cdda_events', 'r') as f:
        tmp = f.read().split('\n')
    for line in tmp[-2:]:
        if line.startswith('ANS_FILENAME='):
            return True
    return False

# Aux to load all disc tracks into Mplayer playlist
def cdda_load():
    """ input:      --
        output:     --
        I/O:        .cdda_info (w), a dict with album and tracks
    """
    print( f'({ME}) loading disk ...' )
    # Save disk info into a json file
    cdda.save_disc_metadata(device=CDROM_DEVICE,
                            fname=f'{MAINFOLDER}/.cdda_info')
    # Flushing the mplayer events file
    with open(f'{MAINFOLDER}/.cdda_events', 'w') as f:
        pass
    # Loading the disk but pausing
    with open(f'{MAINFOLDER}/.cdda_fifo', 'w') as f:
        f.write( 'pausing loadfile \'cdda://1-100:1\'\n' )
    # Waiting for the disk to be loaded (usually about 8 sec)
    n = 15
    while n:
        if cdda_is_loaded():
            break
        print( f'({ME}) waiting for Mplayer to load disk' )
        sleep(1)
        n -= 1
    if n:
        print( f'({ME}) Mplayer disk loaded' )
    else:
        print( f'({ME}) TIMED OUT detecting Mplayer disk' )

# Aux to retrieve the current track an time info
def cdda_get_current_track():
    """ input:      ---
        output:     trackNum (int), trackPos (float)
        I/O:        .cdda_fifo (w), .cdda_events (r)
    """
    # (i) 'get_property chapter' produces cd audio gaps :-/
    #     'get_time_pos'         does not :-)
    #     When querying Mplayer, always must use the prefix
    #     'pausing_keep', otherwise pause will be released.

    def get_disc_pos():
        # 'get_time_pos': elapsed secs refered to the whole loaded.
        with open(f'{MAINFOLDER}/.cdda_fifo', 'w') as f:
            f.write( 'pausing_keep get_time_pos\n' )
        with open(f'{MAINFOLDER}/.cdda_events', 'r') as f:
            tmp = f.read().split('\n')
        for line in tmp[-10:]:
            if line.startswith('ANS_TIME_POSITION='):
                return float( line.replace('ANS_TIME_POSITION=', '').strip() )
        return 0.0

    def calc_track_and_pos(discPos):
        trackNum = 1
        cummTracksLength = 0.0
        trackPos = 0.0
        # Iterate tracks until discPos is exceeded
        while str(trackNum) in cd_info:
            trackLength = timestring2sec( cd_info[ str(trackNum) ]['length'] )
            cummTracksLength += trackLength
            if cummTracksLength > discPos:
                trackPos = discPos - ( cummTracksLength - trackLength )
                break
            trackNum += 1
        return trackNum, trackPos

    # We need the cd_info tracks list dict
    try:
        with open(f'{MAINFOLDER}/.cdda_info', 'r') as f:
            cd_info = json.loads( f.read() )
    except:
        cd_info = cdda.cdda_info_template()

    discPos             = get_disc_pos()
    trackNum, trackPos  = calc_track_and_pos(discPos)

    # Ceiling track to the last available
    last_track = len( [ x for x in cd_info if x.isdigit() ] )
    if trackNum > last_track:
        trackNum = last_track

    return trackNum, trackPos

# MAIN Mplayer control (used for all Mplayer services: DVB, iSTREAMS and CD)
def mplayer_control(cmd, service):
    """ Sends a command to Mplayer trough by its input fifo
        input:  a command string
        result: a result string: 'play' | 'stop' | 'pause' | ''
    """

    # Sending a Mplayer command through by the corresponding fifo
    def send_cmd(cmd):
        print( f'({ME}) sending \'{cmd}\' to Mplayer (.{service}_fifo)' )
        with open(f'{MAINFOLDER}/.{service}_fifo', 'w') as f:
            f.write( f'{cmd}\n' )

    # Aux to disconect Mplayer jack ports from preamp ports.
    def pre_connect(mode, pname=CD_CAPTURE_PORT):
        try:
            jc = jack.Client('mplayer.py', no_start_server=True)
            sources = jc.get_ports(  pname,   is_output=True )
            sinks   = jc.get_ports( 'pre_in', is_input =True )
            if mode == 'on':
                for a,b in zip(sources, sinks):
                    jc.connect(a,b)
            else:
                for a,b in zip(sources, sinks):
                    jc.disconnect(a,b)
        except:
            pass
        return

    # (i) Mplayer sends its responses to the terminal where Mplayer
    #     was launched, or to a redirected file.
    #     See available commands at http://www.mplayerhq.hu/DOCS/tech/slave.txt

    # (i) "keep_pausing get_property pause" doesn't works well with CDDA
    # so will keep a variable to selfcontrol the CDDA playing status.
    global playing_status

    # Early returns if no action commands
    if cmd == 'state':
        return playing_status
    if cmd == 'eject':
        # Flush Mplayer playlist
        send_cmd('stop')
        playing_status = 'stop'
        if service == 'cdda':
            # Flush .cdda_info
            with open( f'{MAINFOLDER}/.cdda_info', 'w') as f:
                f.write( json.dumps( cdda.cdda_info_template() ) )
            Popen( f'eject {CDROM_DEVICE}'.split() )
        return playing_status

    # Action commands i.e. playback control
    if service == 'istreams':

        # useful when playing a mp3 stream e.g. some long playing time podcast url
        if   cmd == 'previous':   cmd = 'seek -300 0'
        elif cmd == 'rew':        cmd = 'seek -60  0'
        elif cmd == 'ff':         cmd = 'seek +60  0'
        elif cmd == 'next':       cmd = 'seek +300 0'

        send_cmd(cmd)

    elif service == 'dvb':

        # (i) all this stuff is testing and not much useful
        if   cmd == 'previous':   cmd = 'tv_step_channel previous'
        elif cmd == 'rew':        cmd = 'seek_chapter -1 0'
        elif cmd == 'ff':         cmd = 'seek_chapter +1 0'
        elif cmd == 'next':       cmd = 'tv_step_channel next'

        send_cmd(cmd)

    elif service == 'cdda':
        # Info about CDDA playing (http://www.mplayerhq.hu/DOCS/tech/slave.txt)
        # - There is not a 'play' command, yu must 'loadlist' or 'loadfile'
        # - 'loadlist' <playlist_file> doesn't allow smooth track changes.
        # - playback starts when 'loadfile' is issued
        # - 'pause' in Mplayer will pause-toggle
        # - 'stop' empties the loaded stuff
        # - 'seekxxxx' resumes playing

        # Loading disc if necessary
        if not cdda_is_loaded():
            cdda_load()

        if   cmd == 'previous':
            cmd = 'seek_chapter -1 0'
            playing_status = 'play'

        elif cmd == 'rew':
            cmd = 'seek -30 0'
            playing_status = 'play'

        elif cmd == 'ff':
            cmd = 'seek +30 0'
            playing_status = 'play'

        elif cmd == 'next':
            cmd = 'seek_chapter +1 0'
            playing_status = 'play'

        elif cmd == 'stop':
            playing_status = 'stop'

        elif cmd == 'pause' and playing_status == 'play':
            cmd = 'pause'
            playing_status = 'pause'

        elif cmd == 'play':
            if not playing_status == 'pause':
                curr_track, throwit = cdda_get_current_track()
                chapter = int(curr_track) -1
                cmd = f'seek_chapter {str(chapter)} 1'
                playing_status = 'play'
            else:
                cmd = ''
                playing_status = 'play'

        elif cmd.startswith('play_track_'):
            if cmd[11:].isdigit():
                curr_track = int( cmd[11:] )
                chapter = int(curr_track) -1
                cmd = f'seek_chapter {str(chapter)} 1'
                playing_status = 'play'
            else:
                print( f'({ME}) BAD track {cmd[11:]}' )
                return 'error'


        # (i) Mplayer cdda pausing becomes on strange behavior,
        #     a stutter audio frame stepping phenomena,
        #     even if a 'pausing_keep mute 1' command was issued.
        #     So will temporary disconnect jack ports
        if playing_status == 'pause':
            pre_connect('off')
        else:
            pre_connect('on')

        send_cmd(cmd)

    else:
        print( f'({ME}) unknown Mplayer service \'{service}\'' )

    return playing_status

# Aux Mplayer metadata only for the CDDA service
def cdda_meta(md):
    """ input:      a metadata blank dict
        output:     the updated one
    """
    # Getting the current track and track time position
    curr_track, trackPos = cdda_get_current_track()

    # We need the cd_info tracks list dict
    try:
        with open(f'{MAINFOLDER}/.cdda_info', 'r') as f:
            cd_info = json.loads( f.read() )
    except:
        cd_info = cdda.cdda_info_template()

    # Updating md fields:
    md['track_num'] = '1'
    md['bitrate'] = '1411'
    md['track_num'], md['time_pos'] = str(curr_track), timeFmt(trackPos)
    md['artist'] = cd_info['artist']
    md['album'] = cd_info['album']
    if md['track_num'] in cd_info.keys():
        md['title']     = cd_info[ md['track_num'] ]['title']
        md['time_tot']  = cd_info[ md['track_num'] ]['length'][:-3] # omit decimals
    else:
        md['title'] = 'Track ' + md['track_num']
    last_track = len( [ x for x in cd_info if x.isdigit() ] )
    md['tracks_tot'] = f'{last_track}'
    return md

# MAIN Mplayer metadata
def mplayer_meta(md, service, readonly=False):
    """ gets metadata from Mplayer as per
        http://www.mplayerhq.hu/DOCS/tech/slave.txt

        input:      md:         a blank metadata dict,
                    service:    'cdda' or any else
        output:     the updated md dict
    """

    md['player'] = 'Mplayer'

    # (!) DIVERTING: this works only for DVB or iSTREAMS, but not for CDDA
    if service == 'cdda':
        return cdda_meta(md)

    # This is the file were Mplayer standard output has been redirected to,
    # so we can read there any answer when required to Mplayer slave daemon:
    mplayer_redirection_path = f'{MAINFOLDER}/.{service}_events'

    # Communicates to Mplayer trough by its input fifo to get the current media filename and bitrate:
    if not readonly:
        mplayer_control(cmd='get_audio_bitrate', service=service)
        mplayer_control(cmd='get_file_name',     service=service)
        mplayer_control(cmd='get_time_pos',      service=service)
        mplayer_control(cmd='get_time_length',   service=service)
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

    return md

