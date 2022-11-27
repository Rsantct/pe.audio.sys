#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Inserts a parametric EQ

    The parametric EQ is based on the 'fil' plugin (LADSPA) hosted under Ecasound.

    'fil' plugin is an excellent 4-band parametric eq from Fons Adriaensen,
    for more info see:
        http://kokkinizita.linuxaudio.org/


    Usage:  ecasound_peq.py  start | stop


    NOTES:  You need to prepare a HUMAN READABLE .peq file and
            configure your config.yml accordingly, for example:

                -plugins:
                    - ecasound_peq.py: myPEQ.peq
                    ...
                    ...

            myPEQ.peq file must be hosted in the loudspeaker folder.
            
            Some 'template.peq' files are provided in the underlying folder.

            A .peq file can have any 4-band 'fil-plugin' blocks as needed.
"""
from    subprocess import Popen
import  os
import  sys

UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'
sys.path.append(f'{MAINFOLDER}/share/miscel')

import  peq_control as pc


VERBOSE = False


def insert_ecasound():

    pc.wait4ports('ecasound', timeout=5)
    pc.wait4ports('brutefir', timeout=5)

    with open('/dev/null', 'w') as f:
        Popen( 'jack_disconnect pre_in_loop:output_1 brutefir:in.L'.split(), stdout=f, stderr=f )
        Popen( 'jack_disconnect pre_in_loop:output_2 brutefir:in.R'.split(), stdout=f, stderr=f )
        Popen( 'jack_connect    pre_in_loop:output_1 ecasound:in_1'.split(), stdout=f, stderr=f )
        Popen( 'jack_connect    pre_in_loop:output_2 ecasound:in_2'.split(), stdout=f, stderr=f )
        Popen( 'jack_connect    ecasound:out_1       brutefir:in.L'.split(), stdout=f, stderr=f )
        Popen( 'jack_connect    ecasound:out_2       brutefir:in.R'.split(), stdout=f, stderr=f )

    if VERBOSE:
        print( f'(peq_control) inserting pre_in --> ecasound --> brutefir' )


def start():
    """ Runs Ecasound with a HUMAN READABLE USER PEQ filters setup
    """

    # Get user's XXXXXX.peq as Ecasound ChainSetup
    csname = pc.get_peq_in_use()
    myPEQpath = f'{pc.LSPK_FOLDER}/{csname}.peq'

    if not os.path.isfile(myPEQpath):
        print( f'(ecasound_peq) Cannot find config.py PEQ file: {myPEQpath}' )
        return

    # Parse to a filter plugins setup dictionary
    peq_dict = pc.peq_read( myPEQpath )

    # Dumps the dict to a file for Ecasound to boot with
    myECSpath = pc.peq_dump2ecs(peq_dict, csname)

    # Runs Ecasound with the dumped ECS file
    ecsCmd = f'ecasound -q --server -s:{myECSpath}'
    if VERBOSE:
        Popen( ecsCmd.split() )
        print( f'(ecasound_peq) Running Ecasound ...' )
    else:
        with open('/dev/null', 'w') as f:
            Popen( ecsCmd.split(), stdout=f, stderr=f )

    # Inserting Ecasound in jack audio path chain
    insert_ecasound()


def stop():

    # Killing
    Popen( ['pkill', '-f', f'ecasound -q --server'] )
    if VERBOSE:
        print( f'(ecasound_peq) killing Ecasound ...' )

    # Restoring ports connections
    with open('/dev/null', 'w') as f:
        Popen( 'jack_connect pre_in_loop:output_1 brutefir:in.L'.split(), stdout=f, stderr=f )
        Popen( 'jack_connect pre_in_loop:output_2 brutefir:in.R'.split(), stdout=f, stderr=f )
    if VERBOSE:
        print( f'(ecasound_peq) restoring  pre_in ---> brutefir' )


if __name__ == '__main__':

    if '-v' in sys.argv[1:]:
        VERBOSE = True

    if sys.argv[1:]:
        option = sys.argv[1]

        if option == 'start':
            start()

        elif option == 'stop':
            stop()

        else:
            print(__doc__)
    else:
        print(__doc__)
