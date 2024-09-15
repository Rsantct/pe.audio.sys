#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Start or stop Mplayer for CDDA playback.

    Also used to CD play control and disk eject.

    Usage:      CDDA  start | stop | eject
"""

import  subprocess as sp
from    pathlib import Path
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    config import CONFIG, MAINFOLDER, USER
from    miscel import check_Mplayer_config_file, Fmt

# CD-ROM device
CDROM_DEVICE = CONFIG['cdrom_device']


## --- Mplayer options ---
# -quiet: see channels change
# -really-quiet: silent
options = '-quiet -nolirc -slave -idle'


## Input FIFO. Mplayer runs in server mode (-slave) and
#  will read commands from a fifo:
input_fifo = f'{MAINFOLDER}/.cdda_fifo'
f = Path( input_fifo )
if not f.is_fifo():
    sp.Popen( f'mkfifo {input_fifo}'.split() )
del(f)


## Mplayer output is redirected to a file,
#  so what it is been playing can be read:
redirection_path = f'{MAINFOLDER}/.cdda_events'


def eject():
    sp.Popen( f'eject {CDROM_DEVICE}'.split() )


def start():
    tmp = check_Mplayer_config_file(profile='cdda')
    if tmp != 'ok':
        print( f'{Fmt.RED}(CDDA.py) {tmp}{Fmt.END}' )
        sys.exit()
    cmd = f'mplayer {options} -profile cdda -cdrom-device {CDROM_DEVICE}' \
          f' -input file={input_fifo}'
    with open(redirection_path, 'w') as redirfile:
        sp.Popen( cmd.split(), shell=False,
                  stdout=redirfile, stderr=redirfile )


def stop():
    sp.Popen( ['pkill', '-u', USER, '-KILL', '-f', 'profile cdda'] )


if __name__ == '__main__':

    if sys.argv[1:]:

        opc = sys.argv[1]

        if opc == 'start':
            start()
        elif opc == 'stop':
            stop()
        elif opc == 'eject':
            eject()
        else:
            print(__doc__)

    else:
        print(__doc__)
