#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Start or stop the LCD server and lcd_daemon.py

    usage:   lcd.py   start | stop
"""

import sys
import os
from subprocess import Popen, check_output, call
from time import sleep
from getpass import getuser

UHOME = os.path.expanduser("~")
LCDFOLDER = f'{UHOME}/pe.audio.sys/share/plugins/lcd'
LOGFOLDER = f'{UHOME}/pe.audio.sys/log'
USER = getuser()

def start():

    def run_lcd_driver():
        print('(plugins/lcd) launching LCDd driver...')
        Popen( f'LCDd -c {LCDFOLDER}/LCDd.conf'.split() )


    def run_lcd_daemon():
        print('(plugins/lcd) launching the pe.ausio.sys LCD daemon...')
        Popen( f'python3 {LCDFOLDER}/lcd_daemon.py'.split() )


    # wait up to 10 s for the pe.audio.sys server to be listening at :9990
    n = 10
    while n:
        tmp = check_output( ['ss', '-tl', 'sport == :9990'] ).decode()
        if ':9990' in tmp:
            break
        n -= 1
        sleep(1)

    if n:
        run_lcd_driver()
        sleep(3)
        run_lcd_daemon()

    else:
        print('(plugins/lcd) TIMEOUT: pe.audio.sys server not detected at :9990')


def stop():
    call( ['pkill', '-u', USER, '-f', 'lcd/LCDd.conf'] )
    call( ['pkill', '-u', USER, '-f', 'lcd_daemon.py'] )


if sys.argv[1:]:
    try:
        option = {
                    'start' : start,
                    'stop'  : stop
                  }[ sys.argv[1] ]()
    except:
        print( '(plugins/lcd.py) internal error :-/' )

else:
    print(__doc__)
