#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    EXPERIMENTAL

    If you don't want the Brutefir high CPU consumption,
    this runs jackminimix replacing Brutefir  :-O

    pre_in_loop    ---- 1 ----\\
                               \\
                   ---- 2 ----( + )----> sound_card
                               /
                   ---- 3 ----/


    (!) Only works whith a FULLRANGE loudspeaker
        attached to system:playback_1/2

    Usage:

    jack_minimix.py   start | stop | adjust -gN dB [...]

        To adjust jackminimix mixer gains
        use adjust -gN dB (N:1..3)

        'stop' will restore Brutefir working

"""
import argparse
import sys
from getpass import getuser
from os.path import expanduser
from os import chdir
from subprocess import Popen, check_output, call
from time import sleep
from socket import gethostname
import yaml
# Jackminimix is controled via OSC protocol
# https://pypi.org/project/python-osc
from pythonosc.udp_client import SimpleUDPClient

UHOME = expanduser("~")
sys.path.append( f'{UHOME}/pe.audio.sys' )
from share.services.preamp_mod.core import jack_connect_bypattern


def start_brutefir():
    with open( f'{UHOME}/pe.audio.sys/config/config.yml', 'r' ) as f:
        CONFIG = yaml.safe_load(f)
    LSPK_FOLDER = f'{UHOME}/pe.audio.sys/loudspeakers/{CONFIG["loudspeaker"]}'
    chdir( LSPK_FOLDER )
    Popen( 'brutefir brutefir_config'.split() )
    chdir( UHOME )
    print( '(start.py) STARTING BRUTEFIR' )
    sleep(1)  # wait a while for Brutefir to start ...


def stop_brutefir():
    Popen( f'pkill -u {getuser()} -KILL -f brutefir >/dev/null 2>&1', shell=True )


def check_fullrange():
    # Check if pe.audio.sys loudspeaker is a fullrange kind of
    try:
        tmp = check_output('jack_lsp system:playback -c'.split()) \
                                                    .decode().split()
        for BFport in [x for x in tmp if 'brutefir:' in x]:
            if 'brutefir:fr' not in BFport:
                return False
    except:
        return False
    return True


def start_mixer():
    # Check if pe.audio.sys loudspeaker is a fullrange kind of
    if not check_fullrange():
        print(__doc__)
        sys.exit()
    # Stop Brutefir
    stop_brutefir()
    # Start JackMinix with 3 input channels
    cmd = f'jackminimix -p 9985 -c 3 -v'
    Popen( cmd.split() )
    sleep(.5)
    # Attenuate all channel gains
    client = SimpleUDPClient(gethostname(), 9985)
    client.send_message('/mixer/channel/set_gain', [1, -40.0] )
    client.send_message('/mixer/channel/set_gain', [2, -40.0] )
    client.send_message('/mixer/channel/set_gain', [3, -40.0] )
    # Connect the mixer output to the sound card
    jack_connect_bypattern('pre_in_loop', 'minimixer')
    jack_connect_bypattern('minimixer', 'system')


def stop_mixer():
    # Kills the mixer
    call( f'pkill -u {getuser()} -f "jackminimix -p"', shell=True )
    # Restarts Brutefir
    # (!!!) BE SURE that your brutefir_config has a 50dB initial level atten.
    start_brutefir()
    # Connect Brutefir
    jack_connect_bypattern('pre_in', 'brutefir')


def get_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('mode', type=str,
        help='start | stop | adjust | info')

    parser.add_argument('-a', type=str, default=gethostname(),
        help='The address of the OSC server')

    parser.add_argument('-p', type=int, default=9985,
        help='The listening port of the OSC server')

    parser.add_argument('-g1', type=float, default=None,
        help='adjust channel 1 gain')

    parser.add_argument('-g2', type=float, default=None,
        help='adjust channel 2 gain')

    parser.add_argument('-g3', type=float, default=None,
        help='adjust channel 3 gain')

    return parser.parse_args()


if __name__ == '__main__':

    args = get_args()

    if args.mode == 'start':
        start_mixer()

    elif args.mode == 'stop':
        stop_mixer()

    elif args.mode == 'adjust':
        client = SimpleUDPClient(args.a, args.p)
        if args.g1 is not None:
            client.send_message('/mixer/channel/set_gain', [1, args.g1] )
        if args.g2 is not None:
            client.send_message('/mixer/channel/set_gain', [2, args.g2] )
        if args.g3 is not None:
            client.send_message('/mixer/channel/set_gain', [3, args.g3] )

    elif args.mode == 'info':
        print(__doc__)
