#!/usr/bin/env python3
"""
    usage:

        set_gain.py   WAY   GAIN   [POL]

        WAY must be 'sw', 'lo', 'mi', 'hi'

        GAIN must be in float notation, i.e. for 1 dB: '1.0'

        POL can be '+', '1', '+1' or '-', '-1'

"""

from common import *


def set_gain(way='lo', g=0.0, pol='+'):

    att = -g

    if pol == '-':
        pol = '-1'
    else:
        pol = '1'

    for ch in 'L', 'R':

        # 1st POL
        cmd = f'cfoa "f.{way}.{ch}" "{way}.{ch}" m{pol}'
        bf.cli(cmd)

        # 2nd ATTEN
        cmd = f'cfoa "f.{way}.{ch}" "{way}.{ch}" {att}'
        bf.cli(cmd)

    return


if __name__ == '__main__':

    way   = ''
    gain  = 0.0
    pol   = '+'

    for opc in sys.argv[1:]:

        if '-h' in opc:
            print(__doc__)
            sys.exit()

        if opc == '+' or opc == '+1' or opc == '1':
            pol = '+'

        elif opc == '-' or opc == '-1':
            pol = '-'

        elif opc == 'sw' or opc == 'lo' or opc == 'mi' or opc == 'hi':
            way = opc

        else:
            gain = float(opc)

    if way:
        set_gain(way, gain, pol)

    print_filters()



