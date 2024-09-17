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
USER = getuser()

def start():
    # wait 10 s for the pe.audio.sys server to be listening at :9990
    n = 10
    while n:
        tmp = check_output( ['ss', '-tl', 'sport == :9990'] ).decode()
        if ':9990' in tmp:
            break
        n -= 1
        sleep(1)
    if n:
        print('(plugins/lcd) launching lcd daemon...')
        sleep(1)
        # The server that manages the LCD display Linux driver.
        Popen( f'LCDd -c {LCDFOLDER}/LCDd.conf'.split() )
        sleep(3)
        # The daemon to display pe.audio.sys info on the LCD
        Popen( f'python3 {LCDFOLDER}/lcd_daemon.py'.split() )
    else:
        print('(plugins/lcd) TIMEOUT: pe.audio.sys server not detected')


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
