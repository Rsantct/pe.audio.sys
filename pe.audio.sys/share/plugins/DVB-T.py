#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.
"""
    Start or stop Mplayer in idle & slave mode for DVB-T playback.

    DVB-T tuned channels must be in:
        ~/.mplayer/channels.conf

    Usage:    DVB-T.py  start
                        stop
                        channel channel_name
                        load    channel_name
                        pan     ITU-R (default) | LR | loud | quiet

    Notice:
    When loading a new stream, Mplayer jack ports will dissapear for a while,
    so you'll need to wait for Mplayer ports to re-emerge before switching
    the preamp input.

    Mplayer SLAVE MODE
    http://www.mplayerhq.hu/DOCS/tech/slave.txt
"""

import  sys
import  os
from    pathlib import Path
from    time    import sleep
import  subprocess as sp
import  jack

UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'
sys.path.append(f'{MAINFOLDER}/share/miscel')

from miscel import wait4ports, Fmt, USER

CHANNELS_PATH   = f'{UHOME}/.mplayer/channels.conf'
EVENTS_PATH     = f'{MAINFOLDER}/.dvb_events'
INPUT_FIFO      = f'{MAINFOLDER}/.dvb_fifo'

# -- VERBOSE (use tail -f .dvb_events), see details under make_msglevel()
VERBOSE = False

# --- RESAMPLER
# Integrated resamplier
#AF_RESAMPLER = 'resample=44100:0:2'
#
# HiFi resampler
"""
   lavcresample[=srate[:length[:linear[:count[:cutoff]]]]]
          Changes the sample rate of the audio stream to an integer <srate> in Hz.  It only supports the 16-bit native-endian format.
          NOTE: With MEncoder, you need to also use -srate <srate>.
             <srate>
                  the output sample rate
             <length>
                  length of the filter with respect to the lower sampling rate (default: 16)
             <linear>
                  if 1 then filters will be linearly interpolated between polyphase entries
             <count>
                  log2 of the number of polyphase entries (..., 10->1024, 11->2048, 12->4096, ...)  (default: 10->1024)
             <cutoff>
                  cutoff frequency (0.0-1.0), default set depending upon filter length
"""
RESAMPLER = 'lavcresample=44100:32:0:12'


def make_pan(mode='itu'):
    """
        ITU-R Downmix for 5.1(side)

                0       1       2       3       4       5
                FL      FR      SL      SR      FC      LFE
            L   1.0     0.0     0.707   0.0     0.707   0.5
            R   0.0     1.0     0.0     0.707   0.707   0.5
    """


    if mode.lower() == 'lr':
        L = [1.0, 0.0, 0.0,   0.0,   0.0,  0.0]
        R = [0.0, 1.0, 0.0,   0.0,   0.0,  0.0]

    elif mode.lower() == 'itu-r':
        L = [1.0, 0.0, 0.707, 0.0,   0.707, 0.5]
        R = [0.0, 1.0, 0.0,   0.707, 0.707, 0.5]

    elif mode.lower() == 'quiet':
        L = [0.2, 0.0, 0.707, 0.0,   0.707, 0.5]
        R = [0.0, 0.2, 0.0,   0.707, 0.707, 0.5]

    elif mode.lower() == 'loud':
        L = [3.0, 0.0, 0.707, 0.0,   0.707, 0.5]
        R = [0.0, 3.0, 0.0,   0.707, 0.707, 0.5]

    else:
        print(f'BAD pan ID: {mode}')
        return ''

    pan = f'{2}'

    for l, r in zip(L,R):
        pan += f':{l}:{r}'

    # example  2:1.0:0.0:0.0:1.0:0.707:0.0:0.0:0.707:0.707:0.707:0.5:0.5

    return pan


def make_msglevel():
    """
        Available levels:
         -1   complete silence
          0   fatal messages only
          1   error messages
          2   warning messages
          3   short hints
          4   informational messages
          5   status messages (default)
          6   verbose messages
          7   debug level 2
          8   debug level 3
          9   debug level 4
    """


    # use (d)efault) or (v)erbose below
    matrix = """
        Available msg modules:
           global     - common player errors/information
           cplayer    - console player (mplayer.c)
           gplayer    - gui player
           vo         - libvo
        v  ao         - libao
        v  demuxer    - demuxer.c (general stuff)
           ds         - demux stream (add/read packet etc)
           demux      - fileformat-specific stuff (demux_*.c)
           header     - fileformat-specific header (*header.c)
           avsync     - mplayer.c timer stuff
           autoq      - mplayer.c auto-quality stuff
           cfgparser  - cfgparser.c
        v  decaudio   - av decoder
           decvideo
           seek       - seeking code
           win32      - win32 dll stuff
           open       - open.c (stream opening)
           dvd        - open.c (DVD init/read/seek)
           parsees    - parse_es.c (mpeg stream parser)
           lirc       - lirc_mp.c and input lirc driver
           stream     - stream.c
           cache      - cache2.c
           mencoder
           xacodec    - XAnim codecs
           tv         - TV input subsystem
           osdep      - OS-dependent parts
           spudec     - spudec.c
           playtree   - Playtree handling (playtree.c, playtreeparser.c)
           input
           vfilter
           osd
           network
           cpudetect
           codeccfg
           sws
           vobsub
           subreader
           osd-menu   - OSD menu messages
        v  afilter    - Audio filter messages
           netst      - Netstream
           muxer      - muxer layer
           identify   - identify output
           ass        - libass messages
           statusline - playback/encoding status line
           fixme      - messages not yet fixed to map to module
    """

    parts = []

    for line in matrix.splitlines():

        line = line.split()

        if line and len(line[0]) == 1:

            if line[0].lower() == 'd':
                level = 5
            elif line[0].lower() == 'v':
                level = 6

            module = line[1]

            parts.append( f'{module}={level}' )

    result = '-msglevel ' + ':'.join(parts)

    return result


def connect_to_jkmeter():

    jcli = jack.Client('DVB-T', no_start_server=True)

    for i in range(6):
        try:
            jcli.connect(f'mplayer_dvb:out_{i}', f'jkmeter:in-{i+1}')
        except:
            pass

    del(jcli)


def connect_to_ebumeter():

    jcli = jack.Client('DVB-T', no_start_server=True)

    try:
        jcli.connect(f'mplayer_dvb:out_0', f'ebumeter:in.L')
        jcli.connect(f'mplayer_dvb:out_1', f'ebumeter:in.R')
    except:
        pass

    del(jcli)


def set_pan(pan_id):

    pan = make_pan(pan_id)

    if pan:
        issue_cmd(f'af_cmdline pan {pan}')


def issue_cmd(command):

    with open( INPUT_FIFO, 'w') as f:
        f.write( f"{command}\n" )

    print( f"(DVB-T.py) issued: {command}" )


def load_channel(channel_name):
    """ loads a stream by its channel.conf name """

    # Searching the channel_name in channels file
    try:
        sp.check_output( ['grep', channel_name, CHANNELS_PATH] ).decode()

    except:
        print( f"(DVB-T.py) Channel NOT found: '{channel_name}'" )
        sys.exit()


    # Loading the DVB-T station
    # The whole address after 'loadfile' needs to be SINGLE quoted to load properly
    issue_cmd( f"loadfile 'dvb://{channel_name}'" )


    # Wait a bit for the new Mplayer ports to emerge (informational only)
    sleep(2)
    if wait4ports('mplayer_dvb', 5):
        print( f"(DVB-T.py) Mplayer JACK ports emerged" )
        connect_to_ebumeter()
    else:
        print( f"(DVB-T.py) Mplayer JACK ports NOT available" )


def start():

    # Check the necessary files for this to work
    do_check_files()

    if VERBOSE:
        MSGLEVEL = make_msglevel()
    else:
        MSGLEVEL = ''

    # NOTICE for AC3 Radio streams (e.g. Radio Clasica RNE)
    # Mplayer -channels options refers the MAX number of channels to catch
    # from the input stream to be rendered to the -ao output.
    # If the stream is AC3 (6 ch), then will output 6 channels to the -ao backend
    # If you force -channels 2 (or leave it to default 2), then Mplayer will downmix the AC3 to 2 ch,
    # BUT this is not useful for Radio Clasica HQ RNE pid 2021 because this AC3
    # normally comes in stereo compatibility mode except for a few live broadcasting concerts.
    OPTIONS  = '-quiet -nolirc -slave -idle -ao jack:name=mplayer_dvb:noconnect -channels 6'


    # Run by flushing the events file, which grows about 200K per hour while running mplayer
    with open(EVENTS_PATH, 'w') as f:
        # clearing the file for this session
        f.write('')
        cmd = f'mplayer {OPTIONS} -af format=floatle,{RESAMPLER},pan={make_pan("itu-r")} {MSGLEVEL} -input file={INPUT_FIFO}'
        sp.Popen( cmd.split(), shell=False, stdout=f, stderr=f )


def stop():
    # Killing our mplayer instance
    sp.call( ['pkill', '-u', USER, '-KILL', '-f', 'dvb_fifo'] )


def do_check_files():
    """ Check the necessary files for this to work
    """

    # Input FIFO for Mplayer -slave mode
    f = Path( INPUT_FIFO )
    if not f.is_fifo():
        sp.Popen( f'mkfifo {INPUT_FIFO}'.split() )
    del(f)

    # Channels file
    f = Path( CHANNELS_PATH )
    if not f.is_file():
        print( f"(DVB-T.py) ERROR reading channels file: '{CHANNELS_PATH}'" )
        sys.exit()
    del(f)


if __name__ == '__main__':

    ### Reading the command line
    if sys.argv[1:]:

        opc = sys.argv[1]

        # STARTS the plugin
        if opc == 'start':
            stop()
            start()

        # STOPS all this stuff
        elif opc == 'stop':
            stop()

        # ON THE FLY tuning
        elif opc in ('channel', 'load'):
            if sys.argv[2:]:
                load_channel( sys.argv[2] )
            else:
                print(__doc__)

        # ON THE FLY changing PAN
        elif opc == 'pan':
            if sys.argv[2:]:
                set_pan( sys.argv[2] )
            else:
                print('missing pan ID')

        elif opc == 'pan_view':
            if sys.argv[2:]:
                tmp = make_pan( sys.argv[2] )
                print(f'pan: {tmp}')
            else:
                print('missing pan ID')

        elif '-h' in opc:
            print(__doc__)

        else:
            print( '(DVB-T.py) Bad option' )

    else:
        print(__doc__)
