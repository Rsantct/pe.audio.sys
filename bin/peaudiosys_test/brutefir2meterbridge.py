#!/bin/env python3
"""
    Launch a Meterbridge for each loudspeaker way,
    grouped by channels: SW, Left, Right
"""

import sys
import subprocess as sp
from getpass import getuser


def sorted_outs( outs ):
    """ ['brutefir:hi.R', 'brutefir:lo.R'] --> ['brutefir:lo.R', 'brutefir:hi.R']
    """

    custom_order = ['lo', 'mi', 'hi']

    # Create a dictionary to map each string to its custom rank
    order_dict = {out: i for i, out in enumerate(custom_order)}

    # Sort the list based on the custom order
    sorted_outs = sorted(outs, key=lambda x: order_dict[ x.split(':')[-1][:2] ])

    return sorted_outs


def get_bf_outs():

    outs = []

    try:
        tmp = sp.check_output('jack_lsp brutefir'.split()).decode().strip()
        outs = tmp.split()

    except:
        return outs

    # Omit void outs and inputs
    outs = [ x for x in outs if (not 'void' in x) and (not 'in.' in x)]

    o_L = [x for x in outs if '.L' in x]
    o_R = [x for x in outs if '.R' in x]
    o_SW = [x for x in outs if 'sw' in x]

    o_L = sorted_outs( o_L )
    o_R = sorted_outs( o_R )

    return {'L': o_L, 'R': o_R, 'SW': o_SW}


def kill_me():
    cmd = f'pkill -u {getuser()} -TERM meterbridge'
    with open('/dev/null', 'w') as f:
        sp.call(cmd, shell=True, stdout=f, stderr=f)


if __name__ == "__main__":

    for opc in sys.argv[1:]:

        if '-h' in opc:
            print(__doc__)
            sys.exit()

        elif '-k' in opc:
            kill_me()
            sys.exit()

    kill_me()

    outs = get_bf_outs()

    for ch in ('SW', 'L', 'R'):

        if outs[ch]:

            outs_str = ' '.join( outs[ch] )

            #   meterbridge -c 3 -t dpm -n Meter_L \
            #       brutefir:lo.L \
            #       brutefir:mi.L \
            #       brutefir:hi.L

            cmd = f'meterbridge -c {len( outs[ch] )} -t dpm -n Meter_{ch} {outs_str}'

            with open('/dev/null', 'w') as f:
                sp.Popen(cmd, shell=True, stdout=f, stderr=f)


