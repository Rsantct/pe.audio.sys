#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A simple plugin to control the power amplifier switch

    Usage:  power_amp_control.py  start | stop

    (i) It depens on the 'amp_manager' field inside 'config.yml'

"""

from    subprocess import Popen
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


if __name__ == '__main__':

    if sys.argv[1:]:

        if sys.argv[1] == 'start':
            Popen(f'{amp_manager} on'.split())

        elif sys.argv[1] == 'stop':
            Popen(f'{amp_manager} off'.split())

        else:
            print(__doc__)
    else:
        print(__doc__)
