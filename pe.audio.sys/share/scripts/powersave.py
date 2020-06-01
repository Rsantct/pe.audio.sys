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
import yaml
import os
import jack
UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'
sys.path.append(f'{MAINFOLDER}/share/services/preamp_mod')
from core import Preamp, Convolver

# YOUR SETUP HERE:
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
            d = yaml.safe_load( f )
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
            return True
        except:
            if times == 10:
                print(f'({ME}) waiting for \'loudness_monitor_daemon.py\' ...' )
            times -= 1
        sleep(1)
    print(f'({ME}) \'loudness_monitor_daemon.py\' not detected')
    return False


def get_brutefir_source_ports():
    jc = jack.Client(name='tmp', no_start_server=True)
    bf_inputs = jc.get_ports('brutefir', is_input=True)
    src_ports = []
    for p in bf_inputs:
        srcs = jc.get_all_connections(p)
        for src in srcs:
            src_ports.append( src.name )
    jc.close()
    return src_ports


def restart_and_reconnect_brutefir(bf_sources=[]):
    """ Restarts Brutefir as external process (Popen),
        then check Brutefir spawn connections to system ports,
        then reconnects Brutefir inputs.
        (i) Notice that Brutefir inputs can have sources
        other than 'pre_in_loop'
    """
    os.chdir(LSPKFOLDER)
    Popen('brutefir brutefir_config'.split())
    os.chdir(UHOME)
    print(f'({ME}) STARTING BRUTEFIR ...')

    # Waits for brutefir to be running
    sleep(3) # needed to jack.Client to work
    jc = jack.Client('check_brutefir')
    tries = 60
    while tries:
        bf_out_ports = jc.get_ports('brutefir', is_output=True)
        count = 0
        for bfop in bf_out_ports:
            conns = jc.get_all_connections(bfop)
            count += len(conns)
        if count == len(bf_out_ports):
            break
        tries -= 1
        sleep(1)

    if tries:
        bf_in_ports    = jc.get_ports('brutefir', is_input=True)
        for a, b in zip(bf_sources, bf_in_ports):
            jc.connect(a, b)
        print(f'({ME}) Brutefir running.')

    else:
        print(f'({ME}) PROBLEM RUNNING BRUTEFIR. Bye :-(')
        sys.exit()

    jc.close()
    del(jc)


def restore_brutefir_settings():
    # Restore Brutefir settings as per the current .state.yml values
    errors = ''
    with open(f'{MAINFOLDER}/.state.yml', 'r') as f:
        state = yaml.safe_load( f )
    preamp    = Preamp()
    convolver = Convolver()
    tmp = preamp._validate( state )
    if tmp  != 'done':
        errors += tmp
    tmp = convolver.set_xo ( state['xo_set']  )
    if tmp  != 'done':
        errors += tmp
    tmp = convolver.set_drc( state['drc_set'] )
    if tmp  != 'done':
        errors += tmp
    del(convolver)
    del(preamp)
    if not errors:
        print(f'({ME}) Brutefir settings restored.')
    else:
        print(f'({ME}) ERRORS restoring Brutefir settings:', errors)


def mainloop():
    # Loops forever every 1 sec reading the dBFS on preamp.
    # If low level signal is detected for MAX_WAIT then stops Brutefir.
    # If signal level raises, then resumes Brutefir.

    waited = 0
    bf_src_ports = []

    while True:

        dBFS = get_dBFS()

        if dBFS < NOISE_FLOOR:
            waited +=1
        else:
            waited = 0
            if not brutefir_is_running():
                print(f'({ME}) signal detected, so resuming Brutefir :-)')
                restart_and_reconnect_brutefir(bf_src_ports)
                restore_brutefir_settings()

        if dBFS < NOISE_FLOOR and waited >= MAX_WAIT and brutefir_is_running():
            # Memorize current brutefir sources (can differ from 'pre_in_loop')
            bf_src_ports = get_brutefir_source_ports()
            print(f'({ME}) low level during {sec2min(MAX_WAIT)}, '
                  f'stopping Brutefir!')
            Popen(f'pkill -f brutefir', shell=True)

        #print('dBFS:', dBFS, 'waited:', waited)    # *** DEBUG ***
        sleep(1)


def stop():

    Popen( ['pkill', '-f', 'powersave.py'] )


def start():

    if not loudness_monitor_is_running():
        sys.exit()

    print(f'({ME}) Will wait until {sec2min(MAX_WAIT)} '
          f'with low level signal then will stop the Brutefir convolver.\n'
          f'Will resume Brutefir dynamically when signal level raises '
          f'above the noise floor threshold')
    mainloop()


if __name__ == "__main__":

    ME    = __file__.split('/')[-1]

    with open(f'{MAINFOLDER}/config.yml', 'r') as f:
        CFG = yaml.safe_load( f )
    LSPKFOLDER = f'{MAINFOLDER}/loudspeakers/{CFG["loudspeaker"]}'

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
