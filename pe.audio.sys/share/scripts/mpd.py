#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

# This is based on 'pre.di.c,' a preamp and digital crossover
# https://github.com/rripio/pre.di.c
# Copyright (C) 2018 Roberto Ripio
# 'pre.di.c' is based on 'FIRtro', a preamp and digital crossover
# https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
#
# 'pe.audio.sys' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'pe.audio.sys' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'pe.audio.sys'.  If not, see <https://www.gnu.org/licenses/>.
"""
    usage:  mpd.py  start|stop
"""
import sys, os
from subprocess import Popen
from time import sleep

UHOME = os.path.expanduser("~")

def stop():

    # some Desktop autostarts MPD user systemd units, even if disabled:
    tmp =  "systemctl --user stop mpd.socket &&"
    tmp += "systemctl --user stop mpd.service &&"
    tmp += "systemctl --user disable mpd.socket &&"
    tmp += "systemctl --user disable mpd.service"
    Popen( tmp, shell=True )

    Popen( ['pkill', '-KILL', '-f', f'mpd {UHOME}/.mpdconf'] )
    sleep(.5)

def start():

    Popen( f'mpd {UHOME}/.mpdconf'.split() )

if __name__ == '__main__':

    if sys.argv[1:]:

        if sys.argv[1] == 'stop':
            stop()
        elif sys.argv[1] == 'start':
            start()
        else:
            print(__doc__)

    else:
        print(__doc__)
