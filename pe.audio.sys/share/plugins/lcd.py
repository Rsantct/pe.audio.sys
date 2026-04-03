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
        print('(plugins/lcd) starting the LCDd driver...')
        Popen( f'LCDd -c {LCDFOLDER}/LCDd.conf'.split() )


    def run_lcd_daemon():
        print('(plugins/lcd) starting the pe.ausio.sys LCD daemon...')
        dv_flag = ''
        cv_flag = ''
        if daemon_verbose:
            dv_flag = '-v'
        if client_verbose:
            cv_flag = '-cv'
        Popen( f'python3 {LCDFOLDER}/lcd_daemon.py {dv_flag} {cv_flag}'.split() )


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


if __name__ == "__main__":

    daemon_verbose = False
    client_verbose = False

    mode    = ''

    for opc in sys.argv[1:]:

        if opc == 'start':
            mode = 'start'

        elif opc == 'stop':
            mode = 'stop'

        elif '-v' in opc or '-dv' in opc:
            daemon_verbose = True

        elif '-cv' in opc:
            client_verbose = True

    if mode == 'start':
        stop()
        sleep(.5)
        start()

    elif mode == 'stop':
        stop()

    else:
        print(__doc__)
