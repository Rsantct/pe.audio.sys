#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    ------------ DEPRECATED -------------------

    before 2025-02 internet streams playback was in charge of Mplayer,
    currently it works with MPD.

    --------------------------------------------

    Start or stop Mplayer for internet streams playback such
    as podcasts or internet radio stations.

    Also used to change on the fly the played stream.

    Internet stream presets can be configured inside:
        pe.audio.sys/config/istreams.yml

    Use:    istreams    start  [ <preset_num> | <preset_name> ]
                        stop
                        preset <preset_num>
                        name   <preset_name>
                        url    <some_url_stream>

    Notice:
    When loading a new stream, Mplayer jack ports will dissapear for a while,
    so you'll need to wait for Mplayer ports to re-emerge before switching
    the preamp input.
"""
from    pathlib import Path
from    time import sleep
from    subprocess import Popen, call
import  yaml
import  sys
import  os

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from miscel import check_Mplayer_config_file, Fmt, USER


# Mplayer options:
options = '-quiet -nolirc -slave -idle'

# Aditional option to avoid Mplayer defaults to
# "Playlist parsing disabled for security reasons."
# This applies to RTVE.es, which radio urls are given in .m3u playlist format.
# - one can download the .m3u then lauch the inside url with mplayer
# - or, easy way, we can allow playlit parsing on Mplayer.
options += " -allow-dangerous-playlist-parsing"

# Input FIFO. Mplayer runs in server mode (-slave) and
# will read commands from a fifo:
input_fifo = f'{UHOME}/pe.audio.sys/.istreams_fifo'
f = Path( input_fifo )
if not f.is_fifo():
    Popen( f'mkfifo {input_fifo}'.split() )
del(f)

# Mplayer output is redirected to a file, so it can be read what is been playing:
redirection_path = f'{UHOME}/pe.audio.sys/.istreams_events'


def load_url(url):

    try:
        # a playlist
        if 'm3u' in url[-4:]:
            command = ('loadlist ' + url + '\n' )
        # a stream
        else:
            command = ('loadfile ' + url + '\n' )

        print( f'(istreams) trying to load \'{url}\'' )
        with open( input_fifo, 'w') as f:
            f.write(command)
        sleep(.5)
        return True

    except:
        return False


def select_by_name(preset_name):
    """ loads a stream by its preset name """
    for pnum, pdict in presets.items():
        if type(pdict) == dict and 'name' in pdict and pdict["name"] == preset_name:
            if 'url' in pdict:
                if load_url( pdict["url"] ):
                    return True
                else:
                    print( f'(istreams) error loading: \'{pdict["url"]}\'' )
                    return False
            else:
                print( f'(istreams) url not found in preset: \'{preset_name}\'' )
                return False
    print( f'(istreams) preset \'{preset_name}\' not found' )
    return False


def select_by_preset(preset_num):
    """ loads a stream by its preset number """
    if load_url( presets[ int(preset_num) ]["url"] ):
        return True
    else:
        print( f'(istreams) error in preset # {preset_num}' )
        return False


def start():
    tmp = check_Mplayer_config_file(profile='istreams')
    if tmp != 'ok':
        print( f'{Fmt.RED}(istreams) {tmp}{Fmt.END}' )
        sys.exit()
    cmd = f'mplayer {options} -profile istreams \
           -input file={input_fifo}'
    with open(redirection_path, 'w') as redirfile:
        Popen( cmd.split(), shell=False, stdout=redirfile, stderr=redirfile )


def stop():
    # Killing our mplayer instance
    call( ['pkill', '-u', USER, '-KILL', '-f', 'profile istreams'] )


if __name__ == '__main__':

    ### Reading the stations presets file
    config_path = f'{UHOME}/pe.audio.sys/config/istreams.yml'
    try:
        with open(config_path, 'r') as f:
            presets = yaml.safe_load(f)
    except:
        print( f'(istreams) ERROR reading \'config/istreams.yml\'' )
        sys.exit()

    ### Reading the command line
    if sys.argv[1:]:

        opc = sys.argv[1]

        # STOPS all this stuff
        if opc == 'stop':
            stop()

        # STARTS Mplayer and optionally load a preset/name
        elif opc == 'start':
            stop()
            start()
            if sys.argv[2:]:
                opc2 = sys.argv[2]
                if opc2.isdigit():
                    select_by_preset(opc2)
                elif opc2.isalpha():
                    select_by_name(opc2)

        # ON THE FLY changing a preset number
        elif opc == 'preset':
            select_by_preset( sys.argv[2] )

        # ON THE FLY changing a preset name
        elif opc == 'name':
            select_by_name( sys.argv[2] )

        # ON THE FLY loading an url stream
        elif opc == 'url':
            load_url( sys.argv[2] )

        elif '-h' in opc:
            print(__doc__)
            sys.exit()
        else:
            print( '(istreams) Bad option' )

    else:
        print(__doc__)
