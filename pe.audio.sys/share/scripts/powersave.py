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
    A daemon that stop audio processes if the LU_Integrated
    monitored value remains static for a long while.

    usage:   powersave.py  start | stop
"""
import sys
from subprocess import Popen, check_output
import time
import json
import os

# CONFIGURE HERE THE MAX TIME TO ADMIT A CONSTANT LU LEVEL:
MAX_SECONDS = 30 * 60   # 30 minutes

UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'


def sec2min(s):
    m = s // 60
    s = s % 60
    return f'{str(m).rjust(2,"0")}:{str(s).rjust(2,"0")}'


def mainloop():

    last_LUI = 0.0
    warnings = 0
    print(f'(powersave.py) Will wait until {sec2min(MAX_SECONDS)}'
          f' without level changes, then will stop pe.audio.sys')

    while True:

        try:
            with open(f'{MAINFOLDER}/.loudness_monitor', 'r') as f:
                d = json.loads( f.read() )
                LUI = d["LU_I"]
        except:
            LUI = 0.0

        # skip if LUI > 0
        if LUI > 0:
            time.sleep(1)
            continue

        if LUI != last_LUI:
            last_LUI = LUI
            warnings = 0
            #print('level has changed :-)')
        else:
            warnings +=1

        if warnings >= MAX_SECONDS:
            print(f'level not changed for {sec2min(MAX_SECONDS)}, '
                  f'stopping audio. Bye!')
            Popen(f'{MAINFOLDER}/start.py stop', shell=True)
            return

        time.sleep(1)


def stop():
    Popen( ['pkill', '-f', 'powersave.py'] )


def start():

    # Exit if loudness_monitor_daemon.py is not running
    try:
        check_output('pgrep -f loudness_monitor_daemon.py'.split()).decode()
        print(f'(powersave.py) \'loudness_monitor_daemon.py\' is running')
    except:
        print(f'(powersave.py) needs \'loudness_monitor_daemon.py\' to be running')
        return

    mainloop()


if __name__ == "__main__":

    if sys.argv[1:]:

        for opc in sys.argv[1:]:
            if opc == 'start':
                start()
            elif opc == 'stop':
                stop()
            else:
                print(__doc__)

    else:
        print(__doc__)
