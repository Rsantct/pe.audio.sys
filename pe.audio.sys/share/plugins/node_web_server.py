#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Auxiliary plugin to launch the pe.audio.sys web page Node.js server

    usage:  node_web_server.py   start|stop
"""
from subprocess import Popen, check_output
from time import sleep
import os
import sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from config import CONFIG, USER

ctrlport = CONFIG['peaudiosys_port']

cmdline = f'node {UHOME}/pe.audio.sys/share/www/nodejs/www_server.js'


def stop():
    Popen( f'pkill -u {USER} -KILL -f "{cmdline}"', shell=True )
    sleep(.5)


def start():
    # wait 60 s for pe.audio.sys server to be listening at :9990
    n = 60
    while n:
        tmp = check_output( ['ss', '-tl', f'sport == :{ctrlport}'] ).decode()
        if f':{ctrlport}' in tmp:
            break
        n -= 1
        sleep(1)
    if n:
        print('(plugins/node_web_server) launching node web server...')
        sleep(1)
        Popen(f'{cmdline} 1>/dev/null 2>&1', shell=True)
    else:
        print(f'(plugins/node_web_server) TIMEOUT server not detected on :{ctrlport}')


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
