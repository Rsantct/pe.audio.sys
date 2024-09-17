#!/usr/bin/env python3
"""
    Wire your analog input port to the pe.audio.sys preamp

    Usage:

        analog_to_preamp.py  L | R | LR

        If no parameter is given, any wired will be cleared.

    IMPORTANT:

    - Configure inside this script your physical analog capture jack port name.

    - If the capture sound card is not your pe.audio.sys sound card,
      you'll need to run an ALSA to JACK resampler, for example:

        zita-a2j -d hw:CODEC,0 -j CODEC -c 2 -Q auto -p 1024 -r 44100 &

      This emerges new capture ports under JACK, named "CODEC"

"""

import sys
from subprocess import Popen


#### configure your physical analog capture jack port name:

#ANALOG  = 'system'
ANALOG  = 'CODEC'

####


def do_clear():
    """ clearing out any direct or crossed connection
    """

    for capN in '1', '2':

        for preN in '1', '2':

            cmd = f'jack_disconnect {ANALOG}:capture_{capN}    pre_in_loop:input_{preN}'

            with open('/dev/null', 'w') as fnull:
                Popen(cmd.split(), stdout=fnull, stderr=fnull)



def do_connect(mode):

    cmd1 = cmd2 = ''

    match mode:

        case 'L' | '1':
            cmd1 = f'jack_connect {ANALOG}:capture_1    pre_in_loop:input_1'
            print(f'    analog:capture_1  --->  pre_in_loop:input_1')

        case 'R' | '2':
            cmd1 = f'jack_connect {ANALOG}:capture_1    pre_in_loop:input_2'
            print(f'    analog:capture_1  --->  pre_in_loop:input_1')

        case 'LR' | 'L+R':
            cmd1 = f'jack_connect {ANALOG}:capture_1    pre_in_loop:input_1'
            cmd2 = f'jack_connect {ANALOG}:capture_1    pre_in_loop:input_2'
            print(f'    analog:capture_1  --->  pre_in_loop:input_1')
            print(f'                           \__>  pre_in_loop:input_2')


        case _:
            print('NACK')

    if cmd1:
        with open('/dev/null', 'w') as fnull:
            Popen(cmd1.split(), stdout=fnull, stderr=fnull)

    if cmd2:
        with open('/dev/null', 'w') as fnull:
            Popen(cmd2.split(), stdout=fnull, stderr=fnull)



if __name__ == '__main__':

    do_clear()

    if not sys.argv[1:]:
        print("ANALOG INPUTS HAS BEEN DIS-CONNECTED FROM PREAMP")

    else:

        if '-h' in sys.argv[1]:
            print(__doc__)
            sys.exit()

        else:
            do_connect( sys.argv[1] )

