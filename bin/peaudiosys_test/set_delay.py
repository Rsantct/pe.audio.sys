#!/usr/bin/env python3
"""
    usage:
            set_delay.py   sw|lo|mi|hi  delay  [ms|cm]

            'delay' defaults to samples, unless 'ms' or 'cm' is given
"""

from common import *


def set_delay(way='lo', d=0):

    if units == 'samples':
        samples = round(d, 0)

    elif units == 'ms':
        samples = round( d / 1000 * FS, 0)

    elif units == 'cm':
        samples = round( d / 100 / 340 * FS, 0 )

    for ch in 'L', 'R':

        cmd = f'cod "{way}.{ch}" {samples}'

        bf.cli(cmd)

    return


if __name__ == '__main__':

    delay = 0.0
    way   = ''
    units = 'samples'

    for opc in sys.argv[1:]:

        if '-h' in opc:
            print(__doc__)
            sys.exit()

        elif opc == 'ms':
            units = 'ms'

        elif opc == 'cm':
            units = 'cm'

        elif opc == 'sw' or opc == 'lo' or opc == 'mi' or opc == 'hi':
            way = opc

        else:
            delay = float(opc)

    if way:
        set_delay(way, delay)

    print_outputs()



