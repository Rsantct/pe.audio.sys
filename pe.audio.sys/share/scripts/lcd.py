#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.
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
    Starts the LCD server and lcd_daemon.py

    usage:   lcd.py   start | stop
"""

import sys
import os
from subprocess import Popen, check_output
from time import sleep

UHOME = os.path.expanduser("~")
LCDFOLDER = f'{UHOME}/pe.audio.sys/share/scripts/lcd'


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
        print('(scripts/lcd) launching lcd daemon...')
        sleep(1)
        # The server that manages the LCD display Linux driver.
        Popen( f'LCDd -c {LCDFOLDER}/LCDd.conf'.split() )
        sleep(3)
        # The daemon to display pe.audio.sys info on the LCD
        Popen( f'python3 {LCDFOLDER}/lcd_daemon.py'.split() )
    else:
        print('(scripts/lcd) TIMEOUT: pe.audio.sys server not detected')


def stop():
    Popen( ['pkill', '-f', 'lcd/LCDd.conf'] )
    Popen( ['pkill', '-f', 'lcd_daemon.py'] )
    sleep(1)


if sys.argv[1:]:
    try:
        option = {
                    'start' : start,
                    'stop'  : stop
                  }[ sys.argv[1] ]()
    except:
        print( '(scripts/lcd.py) internal error :-/' )

else:
    print(__doc__)
