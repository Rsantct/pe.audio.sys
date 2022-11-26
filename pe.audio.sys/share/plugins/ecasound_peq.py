#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Inserts a parametric EQ based on 'fil' plugin (LADSPA) hosted under Ecasound.
    'fil' plugin is an excellent 4-band parametric eq from Fons Adriaensen,
    for more info see:
        http://kokkinizita.linuxaudio.org/

    Usage:  ecasound_peq.py  start | stop

    NOTES:  You need to prepare a HUMAN READABLE .peq file and
            configure your config.yml accordingly, for example:

                -plugins
                    - ecasound_peq.py: myPEQ.peq
                    ...
                    ...

            myPEQ.peq file must be available in the loudspeaker folder.

            A .peq file can have any 4-band 'fil-plugin' blocks as needed

"""
from    subprocess import Popen
import  os
import  sys

UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'
sys.path.append(f'{MAINFOLDER}/share/miscel')

import  peq_control as pc


VERBOSE = False


def start():
    """ Runs Ecasound with a HUMAN READABLE USER PEQ filters setup
    """

    # Get user's XXXXXX.peq as Ecasound ChainSetup
    csname = pc.get_peq_in_use()
    myPEQpath = f'{pc.LSPK_FOLDER}/{csname}.peq'

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
    pc.insert_ecasound(verbose=VERBOSE)


def stop():

    # Killing
    Popen( ['pkill', '-f', f'ecasound -q --server'] )
    if VERBOSE:
        print( f'(ecasound_peq) killing Ecasound ...' )

    # Restoring ports connections
    pc.jc.connect_bypattern('pre_in_loop', 'brutefir')
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
