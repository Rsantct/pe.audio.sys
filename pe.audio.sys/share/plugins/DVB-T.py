#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Start or stop Mplayer for DVB-T playback.

    Also used to change on the fly the played stream.

    DVB-T tuned channels are ussually stored at
        ~/.mplayer/channels.conf

    User settings (presets) can be configured at
        pe.audio.sys/config/DVB-T.yml

    Usage:    DVB-T.py  start   [ <preset_num> | <channel_name> ]
                        stop
                        preset  <preset_num>
                        name    <channel_name>


    Notice:
    When loading a new stream, Mplayer jack ports will dissapear for a while,
    so you'll need to wait for Mplayer ports to re-emerge before switching
    the preamp input.


    VOLUME MANAGEMENT
    http://www.mplayerhq.hu/DOCS/HTML/en/MPlayer.html#advaudio-volume

    Mplayer SLAVE MODE
    http://www.mplayerhq.hu/DOCS/tech/slave.txt

"""

from    pathlib import Path
from    time    import sleep
from    subprocess import Popen, call, check_output
import  yaml
import  sys
import  os

UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'
sys.path.append(f'{MAINFOLDER}/share/miscel')

from miscel import wait4ports, check_Mplayer_config_file, Fmt


CHANNELS_PATH   = f'{UHOME}/.mplayer/channels.conf'
PRESETS_PATH    = f'{MAINFOLDER}/config/DVB-T.yml'
REDIR_PATH      = f'{MAINFOLDER}/.dvb_events'
INPUT_FIFO      = f'{MAINFOLDER}/.dvb_fifo'


# (i) VOLUME management
#     '-softvol-max 400' alows to amplify 12 dB for AC3 encoded streams
#     Then, when necessary we can issue a slave mode volume command
MPLAYER_OPTIONS = '-quiet -nolirc -slave -idle -softvol -softvol-max 400'


def select_by_preset(pnum):
    """ loads a stream by its presets file number id """

    try:
        channel_name = PRESETS[pnum]['name']
        select_by_name(channel_name)

    except:
        tmp = f'(DVB-T.py) error with preset # {pnum}'
        print(f'{Fmt.BOLD}{tmp}{Fmt.END}')
        sys.exit()


def select_by_name(channel_name):
    """ loads a stream by its channel.conf name """


    def get_volume():

        volume = 0

        for pnum in PRESETS:

            if PRESETS[pnum]['name'] == channel_name:
                if 'codec' in  PRESETS[pnum] and PRESETS[pnum]['codec']:
                    if 'ac3' in  PRESETS[pnum]['codec']:
                        volume = 400 # 12 dB in percent
                break

        return volume


    # Searching the channel_name in channels file
    try:
        check_output( ['grep', channel_name, CHANNELS_PATH] ).decode()

    except:
        print( f"(DVB-T.py) Channel NOT found: '{channel_name}'" )
        sys.exit()


    # Loading the DVB-T station
    try:

        # The whole address after 'loadfile' needs to be SINGLE quoted to load properly
        command = f"loadfile 'dvb://{channel_name}'"

        with open( INPUT_FIFO, 'w') as f:
            f.write( f"{command}\n" )

        print( f"(DVB-T.py) issued: {command}" )


        # Optional VOLUME for multichannel codec 'ffac3'
        volume = get_volume()

        if volume:

            # see Mplayer docs: slave.txt
            command = f"volume {volume} 1"

            with open( INPUT_FIFO, 'w') as f:
                f.write( f"{command}\n" )

            print( f"(DVB-T.py) issued: {command}" )


    except:

        print( f"(DVB-T.py) failed to load '{channel_name}'" )
        sys.exit()


    # Wait a bit for the new Mplayer ports to emerge (informational only)
    sleep(2)
    if wait4ports('mplayer_dvb', 5):
        print( f"(DVB-T.py) Mplayer JACK ports emerged" )
    else:
        print( f"(DVB-T.py) Mplayer JACK ports NOT available" )


def start():

    cmd = f'mplayer {MPLAYER_OPTIONS} -profile dvb -input file={INPUT_FIFO}'

    # (i) The "redir" file grows about 200K per hour while running mplayer
    with open(REDIR_PATH, 'w') as f:
        # clearing the file for this session
        f.write('')
        Popen( cmd.split(), shell=False, stdout=f, stderr=f )


def stop():
    # Killing our mplayer instance
    call( ['pkill', '-KILL', '-f', 'profile dvb'] )


def do_check_files():
    """ Check the necessary files for this to work
    """

    global PRESETS

    # Input FIFO for Mplayer -slave mode
    f = Path( INPUT_FIFO )
    if not f.is_fifo():
        Popen( f'mkfifo {INPUT_FIFO}'.split() )
    del(f)

    # Mplayer config file
    tmp = check_Mplayer_config_file(profile='dvb')

    if tmp != 'ok':
        print( f'{Fmt.RED}(DVB-T.py) {tmp}{Fmt.END}' )
        sys.exit()

    # Channels file
    f = Path( CHANNELS_PATH )
    if not f.is_file():
        print( f"(DVB-T.py) ERROR reading channels file: '{CHANNELS_PATH}'" )
        sys.exit()
    del(f)

    # DVB-T presets file
    try:
        with open(PRESETS_PATH, 'r') as f:
            PRESETS = yaml.safe_load(f)
    except:
        print( f"(DVB-T.py) ERROR reading user presets file: '{PRESETS_PATH}'" )
        sys.exit()


if __name__ == '__main__':

    # Check the necessary files for this to work
    do_check_files()


    ### Reading the command line
    if sys.argv[1:]:

        opc = sys.argv[1]

        # STARTS the plugin and optionally load a preset/name
        if opc == 'start':
            start()
            if sys.argv[2:]:
                opc2 = sys.argv[2]
                if opc2.isdigit():
                    select_by_preset( int(opc2) )
                elif opc2.isalpha():
                    select_by_name(opc2)

        # STOPS all this stuff
        elif opc == 'stop':
            stop()

        # ON THE FLY changing to a preset number or rotates recent
        elif opc == 'preset':
            select_by_preset( int(sys.argv[2]) )

        # ON THE FLY changing to a preset name
        elif opc == 'name':
            select_by_name( sys.argv[2] )

        elif '-h' in opc:
            print(__doc__)
            sys.exit()

        else:
            print( '(DVB-T.py) Bad option' )

    else:
        print(__doc__)
