#!/usr/bin/env python3

import  os
import sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

import  brutefir_mod    as bf
import  jack_mod        as jc


def print_outputs():

    lines = bf.cli('lo').split('\n')

    for line in lines:

        tmp = line

        if 'sw.' in line or 'lo.' in line or 'mi.' in line or 'hi.' in line:

            samples = line.split('delay:')[-1].split(':')[0].strip()
            samples = int(samples)

            ms = round(samples / FS * 1000, 2)

            cm = round(samples / FS * 340 * 100, 1)

            print(  tmp.ljust(30),
                    f'{samples} sam'.rjust(8),
                    f'{ms} ms'.rjust(8),
                    f'{cm} cm'.rjust(8)
            )


def print_filters():

    lines = bf.cli('lf').split('\n')

    is_way  = False
    filters = []

    for line in lines:

        if '"f.' in line:
            if 'sw' in line or 'lo.' in line or 'mi.' in line or 'hi.' in line:
                is_way = True
                n = line.split(':')[0].strip()
                f = line.split(':')[1].replace('"', '').strip()
                filters.append([n, f])

            else:
                is_way = False

        if is_way:

            #if 'delay' in line:
            #   filters[-1].append(line.split(':')[-1].strip())

            if 'outputs' in line:

                #     to outputs:   4/9.0/-1
                tmp = line.split(':')[-1].strip()

                out = tmp.split('/')[0]

                att = tmp.split('/')[1]
                att = round(float(att), 1)

                if len(tmp.split('/')) == 3:
                    mul = tmp.split('/')[2]
                    mul = round(float(mul), 1)

                else:
                    mul = 1.0

                filters[-1].append([out, att, mul])

    print('f#'.ljust(3), 'fname'.ljust(8), 'att'.rjust(8), 'multiplier'.rjust(12))

    for f in filters:
        print(f[0].rjust(3), f[1].ljust(8), f'{f[2][1]}'.rjust(8), f'{f[2][2]}'.rjust(12))


FS = int( bf.get_config()['sampling_rate'] )
