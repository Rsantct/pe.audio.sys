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

""" A module to players.py to deal with playing services supported by Mplayer:
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

#-----------------------------------------------------------------------
# Info about CDDA playing (http://www.mplayerhq.hu/DOCS/tech/slave.txt)
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
#
# Rules:
#   - There is not a 'play' command, you must 'loadlist' or 'loadfile'
#   - 'loadlist' <playlist_file> doesn't allow smooth track changes.
#   - playback starts when 'loadfile' is issued
#   - 'pause' in Mplayer will pause-toggle
#   - 'stop' empties the loaded stuff
#   - 'seekxxxx' resumes playing
#-----------------------------------------------------------------------


from    subprocess import Popen
import  json
from    time import sleep
import  jack
import  os
import  sys
UHOME       = os.path.expanduser("~")

sys.path.append(f'{UHOME}/pe.audio.sys')
from    share.miscel import MAINFOLDER, CONFIG, timesec2string, read_last_lines

sys.path.append( os.path.dirname(__file__) )
import  cdda

ME          = __file__.split('/')[-1]


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
    cdda.save_disc_metadata()

    # Loading disc in Mplayer
    cmd = 'pausing loadfile \'cdda://1-100:1\''
    send_cmd(cmd, service='cdda')

    # Waiting for the disk to be loaded (usually ~ 5 sec)
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
        for line in tmp[-15:][::-1]:
            if line.startswith('ANS_TIME_POSITION='):
                return float( line.replace('ANS_TIME_POSITION=', '')
                              .strip() )
        return 0.0

    def calc_track_and_pos(discPos):
        trackNum = 1
        cummTracksLength = 0.0
        trackPos = 0.0
        # Iterate tracks until discPos is exceeded
        while str(trackNum) in cd_info:
            trackLength = timestring2sec(cd_info[str(trackNum)]['length'])
            cummTracksLength += trackLength
            if cummTracksLength > discPos:
                trackPos = discPos - ( cummTracksLength - trackLength )
                break
            trackNum += 1
        return trackNum, trackPos

    # We need the cd_info tracks list dict
    try:
        with open(cdda.CDDA_INFO_PATH, 'r') as f:
            cd_info = json.loads( f.read() )
    except:
        cd_info = cdda.CDDA_INFO_TEMPLATE.copy()

    discPos             = get_disc_pos()
    trackNum, trackPos  = calc_track_and_pos(discPos)

    # Ceiling track to the last available
    last_track = len( [ x for x in cd_info if x.isdigit() ] )
    if trackNum > last_track:
        trackNum = last_track

    return trackNum, trackPos


# Aux to disconect Mplayer jack ports from preamp ports.
def pre_connect(mode, pname=cdda.CD_JACK_PNAME):
    # (i) Mplayer cdda pausing becomes on strange behavior,
    #     a stutter audio frame stepping phenomena,
    #     even if a 'pausing_keep mute 1' command was issued.
    #     So will temporary disconnect jack ports
    try:
        jc = jack.Client('mplayer.py', no_start_server=True)
        sources = jc.get_ports(  pname,   is_output=True )
        sinks   = jc.get_ports( 'pre_in', is_input =True )
        if mode == 'on':
            for a, b in zip(sources, sinks):
                jc.connect(a, b)
        else:
            for a, b in zip(sources, sinks):
                jc.disconnect(a, b)
    except:
        pass
    return


# Aux to query Mplayer if paused or playing
def playing_status(service=''):
    """ Mplayer status: play or pause
    """
    if not service:
        return 'n/a'

    result = 'play'

    with open(f'{MAINFOLDER}/.{service}_fifo', 'w') as f:
        f.write( 'pausing_keep_force get_property pause\n' )
    sleep(.1)

    last_lines = read_last_lines( f'{MAINFOLDER}/.{service}_events', nlines=5)
    for line in last_lines:
        if 'ANS_pause=yes' == line:
            result = 'pause'

    return result


# Aux to send Mplayer commands through by the corresponding fifo
def send_cmd(cmd, service):
    #print(f'({ME}) sending \'{cmd}\' to Mplayer (.{service}_fifo)') # DEBUG only
    with open(f'{MAINFOLDER}/.{service}_fifo', 'w') as f:
        f.write( f'{cmd}\n' )
    if cmd == 'stop':
        # Mplayer needs a while to report the actual state ANS_pause=yes
        sleep(2)


def mplayer_playlists(cmd, arg='', service=''):
    """ This works only for CDDA
    """
    result = []
    if service == 'cdda':
        if cmd == 'list_playlist':
            with open(cdda.CDDA_INFO_PATH, 'r') as f:
                cd_info = json.loads( f.read() )
            for tnum in [x for x in cd_info.keys() if x.isdigit()]:
                result.append( cd_info[tnum]['title'] )
    return result


# MAIN Mplayer control (used for all Mplayer services: DVB, iSTREAMS and CD)
def mplayer_control(cmd, arg='', service=''):
    """ Sends a command to Mplayer trough by its input fifo
        input:  a command string
        result: a result string: 'play' | 'stop' | 'pause' | ''
    """

    supported_commands = (  'state',
                            'stop',
                            'pause',
                            'play',
                            'next',
                            'previous',
                            'rew',
                            'ff',
                            'play_track',
                            'eject'
                          )

    # (i) pe.audio.sys scripts redirects Mplayer stdout & stderr
    #     towards special files:
    #       ~/pe.audio.sys/.<service>_events
    #     so that will capture there the Mplayer's answers when
    #     a Mplayer command has been issued.
    #     Available commands: http://www.mplayerhq.hu/DOCS/tech/slave.txt

    status = playing_status(service)

    # Early return if SLAVE GETTING INFO commands:
    if cmd.startswith('get_'):
        send_cmd( cmd, service )
        return status
    # Early return if STATE or NOT SUPPORTED command:
    elif cmd == 'state'or cmd not in supported_commands:
        return status

    # Special command EJECT
    if cmd == 'eject':
        Popen( f'eject {cdda.CDROM_DEVICE}'.split() )
        # Flush .cdda_info
        with open( cdda.CDDA_INFO_PATH, 'w') as f:
            f.write( json.dumps( cdda.CDDA_INFO_TEMPLATE.copy() ) )
        # Flush Mplayer playlist and player status file
        send_cmd('stop', service)
        return playing_status(service)


    # Processing ACTION commands (playback control)
    if service == 'istreams':

        # useful when playing a mp3 stream (e.g. a podcast url)
        if   cmd == 'previous':   cmd = 'seek -300 0'
        elif cmd == 'rew':        cmd = 'seek -60  0'
        elif cmd == 'ff':         cmd = 'seek +60  0'
        elif cmd == 'next':       cmd = 'seek +300 0'

        send_cmd(cmd, service)

    elif service == 'dvb':

        # (i) all this stuff is testing and not much useful
        if   cmd == 'previous':   cmd = 'tv_step_channel previous'
        elif cmd == 'rew':        cmd = 'seek_chapter -1 0'
        elif cmd == 'ff':         cmd = 'seek_chapter +1 0'
        elif cmd == 'next':       cmd = 'tv_step_channel next'

        send_cmd(cmd, service)

    elif service == 'cdda':

        if   cmd == 'previous':
            cmd = 'seek_chapter -1 0'   # 0: relative seek

        elif cmd == 'rew':
            cmd = 'seek -30 0'

        elif cmd == 'ff':
            cmd = 'seek +30 0'

        elif cmd == 'next':
            cmd = 'seek_chapter +1 0'

        elif cmd == 'stop':
            cmd = 'stop'

        elif cmd == 'pause' and status == 'play':
            cmd = 'pausing pause'               # Mplayer will toggle to pause
            pre_connect('off')

        elif cmd == 'play':
            # Loading (and playing) disc if necessary
            if not cdda_is_loaded():
                cdda_load()
            else:
                if status == 'pause':
                    cmd = 'pausing_togle pause'       # Mplayer will toggle to play
                else:
                    cmd = ''

        elif cmd == 'play_track':
            # Loading disc if necessary
            if not cdda_is_loaded():
                cdda_load()
            if arg.isdigit():
                curr_track = int( arg )
                chapter = int(curr_track) - 1
                cmd = f'seek_chapter {str(chapter)} 1'  # 1: absolute seek
            else:
                print( f'({ME}) BAD track {cmd[11:]}' )
                return 'bad track number'

        if cmd:
            send_cmd(cmd, service)

        status = playing_status(service)

        if status == 'play':
            pre_connect('on')

    else:
        print( f'({ME}) unknown Mplayer service \'{service}\'' )

    return status


# MAIN Mplayer metadata
def mplayer_get_meta(md, service):
    """ gets metadata from Mplayer as per
        http://www.mplayerhq.hu/DOCS/tech/slave.txt

        input:      md:         a blank metadata dict to be updated
                    service:    'dvb' 'istreams' 'cdda' (*)

        output:     the updated md dict

        (*) for cdda will use the alternate function cdda_get_meta()
    """

    # Aux Mplayer metadata only for the CDDA service
    def cdda_get_meta(md):
        """ input:      a metadata blank dict
            output:     the updated one
        """
        # Getting the current track and track time position
        curr_track, trackPos = cdda_get_current_track()

        # We need the cd_info tracks list dict
        try:
            with open(cdda.CDDA_INFO_PATH, 'r') as f:
                cd_info = json.loads( f.read() )
        except:
            cd_info = cdda.CDDA_INFO_TEMPLATE.copy()

        # Updating md fields:
        md['track_num'] = '1'
        md['bitrate'] = '1411'
        md['track_num'], md['time_pos'] = str(curr_track), timesec2string(trackPos)
        md['artist'] = cd_info['artist']
        md['album'] = cd_info['album']
        if md['track_num'] in cd_info.keys():
            md['title']     = cd_info[ md['track_num'] ]['title']
            md['time_tot']  = cd_info[ md['track_num'] ]['length'][:-3]
                                                        # omit decimals
        else:
            md['title'] = 'Track ' + md['track_num']
        last_track = len( [ x for x in cd_info if x.isdigit() ] )
        md['tracks_tot'] = f'{last_track}'
        return md


    md['player'] = 'Mplayer'

    # (!) DIVERTING: this works only for DVB or iSTREAMS, but not for CDDA
    if service == 'cdda':
        return cdda_get_meta(md)

    # This is the file were Mplayer standard output has been redirected to,
    # so we can read there any answer when required to Mplayer slave daemon:
    mplayer_redirection_path = f'{MAINFOLDER}/.{service}_events'

    # Communicates to Mplayer trough by its input fifo
    # to get the current media filename and bitrate:
    mplayer_control(cmd='get_audio_bitrate', service=service)
    mplayer_control(cmd='get_file_name',     service=service)
    mplayer_control(cmd='get_time_pos',      service=service)
    mplayer_control(cmd='get_time_length',   service=service)

    # Triyng to read Mplayer output from its redirected file
    lines = []
    tries = 3
    while tries:
        # Waiting for Mplayer ANS_xxxx to be written to the output file
        sleep(.10)
        try:
            # Reading a tail of 300 bytes from the Mplayer output file
            fsize = os.path.getsize(mplayer_redirection_path)
            tail_lenght = 300
            with open(mplayer_redirection_path, 'rb') as f:
                f.seek(fsize - tail_lenght)
                lines = f.read(tail_lenght).decode().split('\n')
            break
        except:
            tries -= 1

    # Reading metadata (will take the last valid field if found in lines)
    #   Some sample lines:
    #       ANS_FILENAME='Radio 3 HQ'
    #       ANS_pause=no
    #       ANS_TIME_POSITION=4399.8
    #       ANS_LENGTH=-0.95
    #       ANS_AUDIO_BITRATE='256 kbps'
    for line in lines:
        if 'ANS_AUDIO_BITRATE=' in line:
            md['bitrate'] = line.split('=')[-1].replace("'", "").split()[0]
        if 'ANS_FILENAME=' in line:
            md['title'] = line.split('=')[-1].replace("'", "")

    return md


# Autoexec when loading this module
def init():
    cdda.save_disc_metadata()

# Autoexec when loading this module
init()
