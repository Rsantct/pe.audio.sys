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

    is_way = False

    for line in lines:

        if '"f.' in line:
            if 'sw' in line or 'lo.' in line or 'mi.' in line or 'hi.' in line:
                is_way = True
                print(line)

            else:
                is_way = False

        if is_way:
            if 'delay' in line or 'outputs' in line:
                print(line)


FS = int( bf.get_config()['sampling_rate'] )
