#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" 
    Start or stop the IR receiver

    Usage:  ir.py   start|stop

"""
import sys
import os
import subprocess as sp

UHOME    = os.path.expanduser("~")
THISPATH = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':

    if sys.argv[1:]:
        if sys.argv[1] in ['stop', 'off']:
            sp.Popen( 'pkill -f "ir.py"', shell=True )
        elif sys.argv[1] in ['start', 'on']:
            sp.Popen( f'python3 {THISPATH}/ir/ir.py'.split() )
        else:
            print(__doc__)
    else:
        print(__doc__)
