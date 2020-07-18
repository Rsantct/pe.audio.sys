#!/usr/bin/env python3
"""
    Modifies a Brutefir's XO filter output gain.

    This tool is intended to fine balance your XOVER gains, then you will
    be able to write down the proper values into your 'brutefir_config' file.

    Usage examples:

    - Print the current output settings from 'sw' xover filter stage:

        peaudiosys_set_xo_gain.py  sw

    - Set 1.2 dB output gain at 'hi' xover filter stage (all channels)

        peaudiosys_set_xo_gain.py  hi  1.2

    - List your Brutefir's xover filters

        peaudiosys_set_xo_gain.py  --list

"""

import sys
import os
UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/services/preamp_mod')
from core import bf_cli


def get_filters():

    lines = bf_cli('lf').split('\n')
    filters = {}

    # Starting from the 1st xover filter, i.e: the '6:....'.
    i = lines.index('> Filters:') + 1 + (7*6)

    while True:

        fname = lines[i].split(':')[1].strip().replace('"', '')

        filters[fname] = {
            'fnum':         lines[i].split(':')[0].strip(),
            'coeff':        lines[i+1].split(':')[1].strip(),
            'delay_blocks': lines[i+2].split(':')[1].strip().split()[0],
            'from_inputs':  lines[i+3].split(':')[1].strip(),
            'to_outputs':   lines[i+4].split(':')[1].strip(),
            'from_filters': lines[i+5].split(':')[1].strip(),
            'to_filters':   lines[i+6].split(':')[1].strip()
        }

        i += 7
        if not lines[i] or lines[i] == '':
            break

    return filters


def get_outputs():

    lines = bf_cli('lo').split('\n')
    outputs = {}

    i = lines.index('> Output channels:') + 1

    while True:

        onum = lines[i].split(':')[0].strip()

        outputs[onum] = {
            'name':  lines[i].split(':')[1].strip().split()[0].replace('"', ''),
            'delay': lines[i].split()[-1].strip().replace(')', '')
        }

        i += 1
        if not lines[i] or lines[i] == '':
            break

    return outputs


def get_to_output(fname):

    f = filters[fname]
    tmp = f['to_outputs'].split('/')
    out, att = tmp[:2]
    if len(tmp) == 2:
        pol = '1'
    else:
        pol = tmp[2]
    return [out, float(att), int(pol), f['to_outputs']]


def set_filter_gain(fname, gain):

    if not 'sw' in fname:
        channels = 'L', 'R'
        for ch in channels:
            out = get_to_output(f'f.{fname}.{ch}')[0]
            cmd = f'cfoa "f.{fname}.{ch}" {str(out)} {-gain}'
            #print(cmd)
            bf_cli( cmd )

    else:
        out = get_to_output(f'f.{fname}')[0]
        cmd = f'cfoa "f.{fname}" {str(out)} {-gain}'
        #print(cmd)
        bf_cli( cmd )


def print_curr(way):

    if not 'sw' in way:
        channels = 'L', 'R'
    else:
        channels = [way]

    for ch in channels:
        fname = f'f.{way}'
        if not 'sw' in way:
            fname += f'.{ch}'

        output = get_to_output(fname)
        # from attenuation to gain
        if output[1]:
            output[1] *= -1

        print(  fname.ljust(8),
                f'out: {outputs[output[0]]["name"]}'.ljust(12),
                f'gain: {output[1]}'.ljust(12),
                f'pol: {output[2]}'.ljust(12),
                f'~~  to outputs:  {output[3]}  ~~'
             )


def list_filters():
    for f in filters:
        # omit 'f.' prefix
        print(f'{f[2:].ljust(10)}', filters[f]['to_outputs'])


if __name__ == '__main__':


    outputs = get_outputs()
    filters = get_filters()

    if sys.argv[1:]:

        if '-l' in sys.argv[1]:
            list_filters()
            sys.exit()

        way = sys.argv[1]
        print('curr:')
        print_curr(way)
        if sys.argv[2:]:
            gain = float(sys.argv[2])
            set_filter_gain(way, gain)
            print('new:')
            print_curr(way)

    else:
        print(__doc__)
