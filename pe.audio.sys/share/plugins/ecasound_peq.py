#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Inserts a parametric EQ based on 'fil' plugin (LADSPA) hosted under Ecasound.
    'fil' plugin is an excellent 4-band parametric eq from Fons Adriaensen,
    for more info see:
        http://kokkinizita.linuxaudio.org/

    Options:  start | stop

    Notes:  You need to define the xxxxxx.ecs to load at the belonging
            plugin line under config.yml, e.g:

            -plugins
                - ecasound_peq.py: xxxxxx.ecs
                ...
                ...

            The xxxxxx.ecs file must be available under the 'share/eq' folder.
"""
import subprocess as sp
import os
import sys
from time import sleep
import yaml

UHOME       = os.path.expanduser("~")
EQFOLDER    = f'{UHOME}/pe.audio.sys/share/eq'


def init_ecasound():

    # Info
    print( f'(ecasound_peq) Loading: \'{ECSFILE}\'' )

    # Launching ecasound
    ecsCmd = f'-q --server -s:{EQFOLDER}/{ECSFILE}'
    sp.Popen( f'ecasound {ecsCmd}'.split() )
    sleep(3)

    # Inserting:
    print( f'(ecasound_peq) inserting pre_in --> ecasound --> brutefir' )
    sp.Popen( 'jack_disconnect pre_in_loop:output_1 brutefir:in.L'.split() )
    sp.Popen( 'jack_disconnect pre_in_loop:output_2 brutefir:in.R'.split() )
    sp.Popen( 'jack_connect    pre_in_loop:output_1 ecasound:in_1'.split() )
    sp.Popen( 'jack_connect    pre_in_loop:output_2 ecasound:in_2'.split() )
    sp.Popen( 'jack_connect    ecasound:out_1       brutefir:in.L'.split() )
    sp.Popen( 'jack_connect    ecasound:out_2       brutefir:in.R'.split() )


def stop():
    sp.Popen( f'pkill -f {ECSFILE}'.split() )
    sleep(1)
    # Restoring:
    print( f'(ecasound_peq) removing pre_in -x-> ecasound -x-> brutefir' )
    sp.Popen( 'jack_connect pre_in_loop:output_1 brutefir:in.L'.split() )
    sp.Popen( 'jack_connect pre_in_loop:output_2 brutefir:in.R'.split() )


if __name__ == '__main__':

    try:
        with open( f'{UHOME}/pe.audio.sys/config/config.yml', 'r') as f:
            config = yaml.safe_load(f)
            plugins_list = config['plugins']
            for plugin in plugins_list:
                if type(plugin) == dict:
                    if 'ecasound_peq.py' in plugin.keys():
                        ECSFILE = plugin['ecasound_peq.py']
                        break
    except:
        print(  f'(ecasound_peq) unable to read your .ecs file from config.yml' )
        sys.exit()

    if sys.argv[1:]:
        option = sys.argv[1]
        if option == 'start':
            init_ecasound()
        elif option == 'stop':
            stop()
        else:
            print(__doc__)
    else:
        print(__doc__)
