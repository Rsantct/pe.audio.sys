#!/usr/bin/env python3
"""
    Tool to manage the Brutefir connections to the sound card.

    usage:
            select_ways.py [sub|sw] [lo] [mi] [hi]  |  all  |  none

"""
import  sys
import  os

from common import *


def do_wire():

    for pair in BF_CONFIG['outputsMap']:

        connect = False
        for way in ways:
            if way in pair[0]:
                connect = ways[way]

        if connect:
            jc.connect(f'brutefir:{pair[0]}', pair[1], 'on', verbose=False)
        else:
            jc.connect(f'brutefir:{pair[0]}', pair[1], 'off', verbose=False)


if __name__ == '__main__':

    ways = { 'sw': False, 'lo': False, 'mi': False, 'hi': False }

    # Reading command line

    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()

    for opc in sys.argv[1:]:

        if opc == 'all':
            ways['sw'] = ways['lo'] =  ways['mi'] = ways['hi'] = True

        elif opc == 'sub' or opc == 'sw':
            ways['sw'] = True

        elif opc == 'lo':
            ways['lo'] = True

        elif opc == 'mi':
            ways['mi'] = True

        elif opc == 'hi':
            ways['hi'] = True

        elif opc == 'none':
            ways['sw'] = ways['lo'] =  ways['mi'] = ways['hi'] = False

        elif '-h' in opc:
            print(__doc__)
            sys.exit()

        else:
            print(__doc__)
            sys.exit()

    BF_CONFIG = bf.get_config()

    do_wire()
