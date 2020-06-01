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
    A daemon that stops the Brutefir convolver if the preamp signal is too low.
    (This program needs loudness_monitor_daemon.py to be running)

    usage:   powersave.py  start | stop


    NOTICE:
    Brutefir has a powersave built-in feature, but if saving CPU% is insufficient,
    this script will completely stop the convolver dynamically.

"""
import sys
from subprocess import Popen, check_output
from time import sleep
import json
import os
UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'
sys.path.append(MAINFOLDER)
from start import start_and_connect_brutefir

# SETUP HERE:
NOISE_FLOOR = -70 # will compute low levels only below this floor in dBFS
MAX_WAIT    =  60 # time in seconds before shutting down Brutefir


def sec2min(s):
    m = s // 60
    s = s % 60
    return f'{str(m).rjust(2,"0")}:{str(s).rjust(2,"0")}'


def get_dBFS():
    # Lets use LU_M (LU Momentary) from .loudness_monitor
    try:
        with open(f'{MAINFOLDER}/.loudness_monitor', 'r') as f:
            d = json.loads( f.read() )
            LU_M = d["LU_M"]
    except:
        LU_M = 0.0
    dBFS = LU_M - 23.0  # LU_M is referred to -23dBFS
    return dBFS


def brutefir_is_running():
    try:
        tmp = check_output("pgrep -f brutefir".split()).decode()
        if tmp :
            return True
        else:
            return False
    except:
        return False


def loudness_monitor_is_running():
    times = 10
    while times:
        try:
            check_output('pgrep -f loudness_monitor_daemon.py'.split()).decode()
            return
        except:
            if times == 10:
                print('(powersave.py) waiting for \'loudness_monitor_daemon.py\' ...' )
            times -= 1
        sleep(1)
    if times:
        return True
    else:
        print(f'(powersave.py) \'loudness_monitor_daemon.py\' not detected')
        return False


def mainloop():
    # Loops forever every 1 sec reading the dBFS on preamp.
    # If low level signal is detected for MAX_WAIT then stops Brutefir.
    # If signal level raises, then resumes Brutefir.

    waited = 0

    while True:

        dBFS = get_dBFS()

        if dBFS < NOISE_FLOOR:
            waited +=1
        else:
            waited = 0
            if not brutefir_is_running():
                print('(powersave.py) signal detected, so resuming Brutefir :-)')
                start_and_connect_brutefir()

        if dBFS < NOISE_FLOOR and waited >= MAX_WAIT and brutefir_is_running():
            print(f'(powersave.py) low level during {sec2min(MAX_WAIT)}, '
                  f'stopping Brutefir!')
            Popen(f'pkill -f brutefir', shell=True)

        # print('dBFS:', dBFS, 'waited:', waited)    # *** DEBUG ***

        sleep(1)


def stop():

    Popen( ['pkill', '-f', 'powersave.py'] )


def start():

    if not loudness_monitor_is_running():
        sys.exit()

    print(f'(powersave.py) Will wait until {sec2min(MAX_WAIT)} '
          f'with low level signal then will stop the Brutefir convolver.\n'
          f'Will resume Brutefir dynamically when signal level raises '
          f'above the noise floor threshold')
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
