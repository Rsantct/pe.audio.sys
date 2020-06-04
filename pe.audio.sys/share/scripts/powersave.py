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

    usage:   powersave.py  start | stop


    NOTICE:
    Brutefir has a powersave built-in feature, but if saving CPU% is insufficient,
    this script will completely stop and start the convolver dynamically.

"""
import sys
from subprocess import Popen, check_output
from time import sleep
import yaml
from socket import socket
import os
import jack
UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'

# YOUR SETUP HERE:
NOISE_FLOOR = -70 # will compute low levels only below this floor in dBFS
MAX_WAIT    =  60 # time in seconds before shutting down Brutefir


def control_cmd(cmd):
    host, port = CTL_HOST, CTL_PORT
    print( f'({ME}) sending: {cmd} to {host}:{port}')
    with socket() as s:
        try:
            s.connect( (host, port) )
            s.send( cmd.encode() )
            s.close()
        except:
            print( f'({ME}) socket error on {host}:{port}' )
    return


def sec2min(s):
    m = s // 60
    s = s % 60
    return f'{str(m).rjust(2,"0")}:{str(s).rjust(2,"0")}'


def read_dBFS():
    # Lets use LU_M (LU Momentary) from .loudness_monitor
    try:
        with open(f'{MAINFOLDER}/.loudness_monitor', 'r') as f:
            d = yaml.safe_load( f )
            LU_M = d["LU_M"]
    except:
        LU_M = 0.0
    dBFS = LU_M - 23.0  # LU_M is referred to -23dBFS
    return dBFS


def loudness_monitor_is_running():
    times = 10
    while times:
        try:
            check_output('pgrep -f loudness_monitor_daemon.py'.split()).decode()
            return True
        except:
            times -= 1
        sleep(1)
    return False


def brutefir_is_running():
    if jc.get_ports('brutefir'):
        return True
    else:
        return False


def start():
    """ Loops forever every 1 sec reading the dBFS on preamp.
        If low level signal is detected during MAX_WAIT then stops Brutefir.
        If signal level raises, then resumes Brutefir.
    """

    # loudness_monitor_daemon.py is preferred, else will use audio_meter.py
    print(f'({ME}) waiting for \'loudness_monitor_daemon.py\' ...' )
    loud_mon_daemon_available = loudness_monitor_is_running()

    if loud_mon_daemon_available:
        print( f'({ME}) using \'loudness_monitor_daemon.py\'' )
    else:
        # Prepare and start an audio_meter.Meter instance
        print( f'({ME}) using \'audio_meter.py\'' )
        from powersave_mod.audio_meter import Meter
        meter = Meter(device='pre_in_loop', mode='peak', bar=False)
        meter.start()

    # Loop forever each 1 sec will check signal level
    lowSigElapsed = 0
    while True:

        if loud_mon_daemon_available:
            dBFS = read_dBFS()
        else:
            dBFS = meter.L

        if dBFS > NOISE_FLOOR:
            lowSigElapsed = 0
            if not brutefir_is_running():
                print(f'({ME}) signal detected, so resuming Brutefir :-)')
                control_cmd('convolver on')
        else:
            lowSigElapsed +=1

        if dBFS < NOISE_FLOOR and lowSigElapsed >= MAX_WAIT:
            if brutefir_is_running():
                print(f'({ME}) low level during {sec2min(MAX_WAIT)}, '
                      f'stopping Brutefir!')
                control_cmd('convolver off')

        # *** DEBUG ***
        #print('Brutefir is running', brutefir_is_running())
        #print('dBFS:', dBFS, 'lowSigElapsed:', lowSigElapsed)

        sleep(1)


def stop():

    Popen( 'pkill -KILL -f "powersave.py\ start"', shell=True )


if __name__ == "__main__":

    # This script name
    ME    = __file__.split('/')[-1]

    # pe.audio.sys service addressing
    try:
        with open(f'{MAINFOLDER}/config.yml', 'r') as f:
            cfg = yaml.safe_load(f)
            CTL_HOST, CTL_PORT = cfg['peaudiosys_address'], cfg['peaudiosys_port']
    except:
        print(f'({ME}) ERROR with \'pe.audio.sys/config.yml\'')
        sys.exit()

    # Jack client to check for brutefir availability
    try:
        jc = jack.Client('powersave', no_start_server=True)
    except Exception:
        print(Exception)
        sys.exit()

    if sys.argv[1:]:

        if sys.argv[1] == 'start':
            start()
        elif sys.argv[1] == 'stop':
            stop()
        else:
            print(__doc__)

    else:
        print(__doc__)
