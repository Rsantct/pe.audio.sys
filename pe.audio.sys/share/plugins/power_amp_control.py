#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A simple plugin to control the power amplifier switch

    Usage:  power_amp_control.py  start | stop

    (i) It depens on the 'amp_manager' field inside 'config.yml'

"""

from    subprocess import call, Popen
from    time import sleep
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    config import CONFIG


if 'amp_manager' in CONFIG and CONFIG["amp_manager"]:
    amp_manager = CONFIG["amp_manager"]
else:
    print(f"{__file__} ERROR reading 'amp_manager' inside 'config.yml'")
    sys.exit()


def start():

    call(f'{amp_manager} on'.split())

    # wait for ~/.amplifier == on
    tries = 20
    while tries:
        with open(f'{UHOME}/.amplifier', 'r') as f:
            tmp = f.read().strip()
            if 'on' in tmp or '1' in tmp:
                print(f'(power_amp_control.py) detected ~/.amplifier = ON')
                sleep(1)
                break
            sleep(.25)
    if not tries:
        print(f'(power_amp_control.py) ERROR detecting ~/.amplifier = ON')


def stop():
    Popen(f'{amp_manager} off'.split())


if __name__ == '__main__':

    if sys.argv[1:]:

        if sys.argv[1] == 'start':
            start()

        elif sys.argv[1] == 'stop':
            stop()

        else:
            print(__doc__)
    else:
        print(__doc__)
