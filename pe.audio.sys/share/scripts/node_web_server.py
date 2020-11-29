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
    Auxiliary script to launch the pe.audio.sys web page Node.js server

    usage:  node_web_server.py   start|stop
"""
import sys
import os
from subprocess import Popen, check_output
from time import sleep

UHOME = os.path.expanduser("~")

cmdline = f'node {UHOME}/pe.audio.sys/share/www/peasys_node.js'


def stop():
    Popen( f'pkill -KILL -f "{cmdline}"', shell=True )
    sleep(.5)


def start():
    # wait 10 s for pe.audio.sys server to be listening at :9990
    n = 10
    while n:
        tmp = check_output( ['ss', '-tl', 'sport == :9990'] ).decode()
        if ':9990' in tmp:
            break
        n -= 1
        sleep(1)
    if n:
        print('(scripts/node_web_server) launching node web server...')
        sleep(1)
        Popen( f'{cmdline} 1>/dev/null 2>&1', shell=True)
    else:
        print('(scripts/node_web_server) TIMEOUT server not detected')


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
