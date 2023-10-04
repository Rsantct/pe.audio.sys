#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A watchdog for USB external DAC with standby mode,
    e.g. a Topping DAC.

    If the USB DAC goes to standby, or if it becomes plugged off,
    the JACK server will not respond properly.

    A false jackd process may occur after the USB DAC was disconnected.

    When the user does switch-on the USB DAC, then pe.audio.sys will restart.

    Usage:      usb_dac_watchdog.py  start|stop

"""
import  subprocess as sp
import  os
import  sys
from    time import sleep

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from config import CONFIG


def detect_USB_DAC(cname):
    """ Check if the provided card name is available,
        and if it is USB type.
    """
    result = False
    tmp = sp.check_output('aplay -l'.split()).decode().strip().split('\n')
    for line in tmp:
        if cname in line and 'USB' in line.upper():
            result = True
    return result


def jackd_runs(cname=''):
    """ Check the jackd process

        (!) A false jackd process may occur after the USB DAC
            was disconnected

    """
    def check_jack_lsp():
        try:
            sp.check_output('jack_lsp')
            return True
        except:
            return False

    result = False

    try:
        tmp = sp.check_output('pgrep -fla jackd'.split()).decode().strip()
    except:
        tmp = ''

    if cname in tmp:
        if check_jack_lsp():
            result = True
        else:
            print('WARNING jackd process NOT RESPONDING')

    return result


def peaudiosys_restart():
    """ Restarts pe.audio.sys
        (The script peaudiosys_restart.sh will waits for it to be running)
    """
    print('Restarting pe.audio.sys ... .. .')
    sp.call(f'{UHOME}/bin/peaudiosys_restart.sh', shell=True)


def start():
    """ MAIN LOOP
    """
    card_name     = CONFIG["jack"]["device"].split(':')[-1].split(',')[0]

    while True:

        if detect_USB_DAC(card_name):

            if jackd_runs(card_name):
                print(f'JACK is running with the card \'{card_name}\'')

            else:
                peaudiosys_restart()

        else:
            print(f'USB DAC \'{card_name}\' NOT detected')

        sleep(3)


def stop():
    cmd = 'pkill -f "usb_dac_watchdog.py start"'
    sp.call(cmd, shell=True)


if __name__ == "__main__":

    if sys.argv[1:]:
        if sys.argv[1] == 'start':
            start()
        elif sys.argv[1] == 'stop':
            stop()
        else:
            print(__doc__)
    else:
        print(__doc__)

