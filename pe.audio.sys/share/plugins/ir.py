#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Start or stop the IR receiver

    Usage:  ir.py   start|stop

"""
import  sys
import  os
from    subprocess import Popen, call
from    getpass import getuser

UHOME    = os.path.expanduser("~")
THISPATH = os.path.dirname(os.path.abspath(__file__))


def stop():
    call( ['pkill', '-u', getuser(), '-f', CMDLINE] )


def start():
    Popen( CMDLINE.split() )


if __name__ == '__main__':

    CMDLINE = f'python3 {THISPATH}/ir/ir.py'

    if sys.argv[1:]:

        if sys.argv[1] in ['stop', 'off']:
            stop()

        elif sys.argv[1] in ['start', 'on']:
            stop()
            start()

        else:
            print(__doc__)
    else:
        print(__doc__)
