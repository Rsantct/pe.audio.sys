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

            The xxxxxx.ecs file must be available in the loudspeaker folder.
"""
import  subprocess as sp
import  os
import  sys
from    time import sleep

UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'
sys.path.append(f'{MAINFOLDER}/share/miscel')

from miscel import *

######## CUSTOM CONFIG ############
# choose 4, 6, 8 or 12 bands engine
PEQBANDS = 8
###################################

VERBOSE = False

def init_ecasound():

    # Info
    print( f'(ecasound_peq) Loading: \'{ECS}\'' )

    # Launching ecasound
    ecsCmd = f'-q --server -s:{ECSPATH}'
    if VERBOSE:
            sp.Popen( f'ecasound {ecsCmd}'.split() )
    else:
        with open('/dev/null', 'w') as f:
            sp.Popen( f'ecasound {ecsCmd}'.split(), stdout=f, stderr=f )

    # Inserting:
    wait4ports('ecasound', timeout=5)
    wait4ports('brutefir', timeout=60)
    print( f'(ecasound_peq) inserting pre_in --> ecasound --> brutefir' )
    with open('/dev/null', 'w') as f:
        sp.Popen( 'jack_disconnect pre_in_loop:output_1 brutefir:in.L'.split(), stdout=f, stderr=f )
        sp.Popen( 'jack_disconnect pre_in_loop:output_2 brutefir:in.R'.split(), stdout=f, stderr=f )
        sp.Popen( 'jack_connect    pre_in_loop:output_1 ecasound:in_1'.split(), stdout=f, stderr=f )
        sp.Popen( 'jack_connect    pre_in_loop:output_2 ecasound:in_2'.split(), stdout=f, stderr=f )
        sp.Popen( 'jack_connect    ecasound:out_1       brutefir:in.L'.split(), stdout=f, stderr=f )
        sp.Popen( 'jack_connect    ecasound:out_2       brutefir:in.R'.split(), stdout=f, stderr=f )


def load_PEQ_file(PEQname=''):

    fpath = f'{LSPK_FOLDER}/{PEQname}.peq'
    if not os.path.isfile(fpath):
        print(  f'(ecasound_peq) NOT FOUND: {fpath}' )
        stop()
        sys.exit()

    print(f'(ecasound_peq) Loading \'{fpath}\'')
    print('*** WIP ***')




def stop():
    sp.Popen( ['pkill', '-f', f's:{ECSPATH}'] )
    # Restoring:
    print( f'(ecasound_peq) removing pre_in -x-> ecasound -x-> brutefir' )
    with open('/dev/null', 'w') as f:
        sp.Popen( 'jack_connect pre_in_loop:output_1 brutefir:in.L'.split(), stdout=f, stderr=f )
        sp.Popen( 'jack_connect pre_in_loop:output_2 brutefir:in.R'.split(), stdout=f, stderr=f )


if __name__ == '__main__':

    FS      = read_bf_config_fs()
    THISDIR = os.path.dirname(__file__)

    ECS     = f'ecasound_peq/{FS}/{PEQBANDS}-band_flat.ecs'
    ECSPATH = f'{THISDIR}/{ECS}'

    if not os.path.isfile(ECSPATH):
        print(  f'(ecasound_peq) NOT FOUND: {ECS}' )
        sys.exit()


    if '-v' in sys.argv[1:]:
        VERBOSE = True


    if sys.argv[1:]:
        option = sys.argv[1]
        if option == 'start':
            init_ecasound()
            load_PEQ_file( get_peq_in_use() )
        elif option == 'stop':
            stop()
        else:
            print(__doc__)
    else:
        print(__doc__)
