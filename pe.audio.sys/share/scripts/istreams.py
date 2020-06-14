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

"""
    Starts and stops Mplayer for internet streams playback like
    podcasts or internet radio stations.

    Also used to change on the fly the played stream.

    Internet stream presets can be configured inside:
        pe.audio.sys/istreams.yml

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
import sys
import os
from pathlib import Path
from time import sleep
import subprocess as sp
import yaml

UHOME = os.path.expanduser("~")

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
    sp.Popen( f'mkfifo {input_fifo}'.split() )
del(f)

# Mplayer output is redirected to a file, so it can be read what is been playing:
redirection_path = f'{UHOME}/pe.audio.sys/.istreams_events'


def load_url(url):
    try:
        command = ('loadfile ' + url + '\n' )
        print( f'(istreams.py) trying to load \'{url}\'' )
        with open( input_fifo, 'w') as f:
            f.write(command)
        # print(command) # DEBUG
        return True
    except:
        return False


def select_by_name(preset_name):
    """ loads a stream by its preset name """
    for preset, dict in presets.items():
        if dict['name'] == preset_name:
            load_url( dict['url'] )
            return True
    print( f'(istreams.py) preset \'{preset_name}\' not found' )
    return False


def select_by_preset(preset_num):
    """ loads a stream by its preset number """
    try:
        load_url( presets[ int(preset_num) ]['url'] )
        return True
    except:
        print( f'(istreams.py) error in preset # {preset_num}' )
        return False


def start():
    cmd = f'mplayer {options} -profile istreams \
           -input file={input_fifo}'
    with open(redirection_path, 'w') as redirfile:
        sp.Popen( cmd.split(), shell=False, stdout=redirfile, stderr=redirfile )


def stop():
    # Killing our mplayer instance
    sp.Popen( ['pkill', '-KILL', '-f', 'profile istreams'] )
    sleep(.5)


if __name__ == '__main__':

    ### Reading the stations presets file
    try:
        with open(f'{UHOME}/pe.audio.sys/istreams.yml', 'r') as f:
            presets = yaml.safe_load(f)
    except:
        print( '(istreams.py) ERROR reading \'pe.audio.sys/istream.yml\'' )
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
