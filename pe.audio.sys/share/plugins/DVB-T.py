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

from miscel import check_Mplayer_config_file, Fmt


## USER SETTINGS: see inside DVB-T.yml

## Mplayer options:
tuner_file = f'{UHOME}/.mplayer/channels.conf'
options = '-quiet -nolirc -slave -idle'

# Input FIFO. Mplayer runs in server mode (-slave) and
# will read commands from a fifo:
input_fifo = f'{MAINFOLDER}/.dvb_fifo'
f = Path( input_fifo )
if not f.is_fifo():
    Popen( f'mkfifo {input_fifo}'.split() )
del(f)

# Mplayer output is redirected to a file,
# so it can be read what it is been playing:
redirection_path = f'{MAINFOLDER}/.dvb_events'
# (i) This file grows about 200K per hour if mplayer is the selected input
#     so players.py will periodically queries metadata info from mplayer.


def select_by_name(channel_name):
    """ loads a stream by its preset name """

    try:
        # check_output will fail if no command output
        check_output( ['grep', channel_name, tuner_file] ).decode()
    except:
        print( f'(DVB-T.py) Channel NOT found: \'{channel_name}\'' )
        return False

    try:
        print( f'(DVB-T.py) trying to load \'{channel_name}\'' )
        # The whole address after 'loadfile' needs to be
        # SINGLE quoted to load properly:
        command = ('loadfile \'dvb://' + channel_name + '\'\n' )
        with open( input_fifo, 'w') as f:
            f.write(command)
        return True
    except:
        print( f'(DVB-T.py) failed to load \'{channel_name}\'' )
        return False


def select_by_preset(preset_num):
    """ loads a stream by its preset number """
    try:
        channel_name = DVB_config['presets'][ preset_num ]
        select_by_name(channel_name)
        return True
    except:
        print( f'(DVB-T.py) error in preset # {preset_num}' )
        return False


def start():
    tmp = check_Mplayer_config_file(profile='dvb')
    if tmp != 'ok':
        print( f'{Fmt.RED}(DVB-T.py) {tmp}{Fmt.END}' )
        sys.exit()
    cmd = f'mplayer {options} -profile dvb -input file={input_fifo}'
    with open(redirection_path, 'w') as redirfile:
        # clearing the file for this session
        redirfile.write('')
        Popen( cmd.split(), shell=False, stdout=redirfile,
                                            stderr=redirfile )


def stop():
    # Killing our mplayer instance
    call( ['pkill', '-KILL', '-f', 'profile dvb'] )


if __name__ == '__main__':

    ### Reading the DVB-T config file
    DVB_config_path = f'{MAINFOLDER}/config/DVB-T.yml'
    try:
        with open(DVB_config_path, 'r') as f:
            DVB_config = yaml.safe_load(f)
    except:
        print( f'(DVB-T.py) ERROR reading \'{DVB_config_path}\'' )
        sys.exit()

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
