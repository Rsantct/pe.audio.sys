#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    This is a helper daemon to ensure that the <librespot:output> ports
    will be connected to the reserved <librespot_loop:input> ports.

    This is necessary because the libresport JACKAUDIO backend behavoir:
    - The jack port does not emerge until first time playing.
    - There is not any option to autoconnect to any destination jack port.

"""
import sys
import jack
from time import sleep


JCLI = jack.Client(name='librespot_watchdog', no_start_server=True)

LOOP_PNAMES = ['librespot_loop:input_1', 'librespot_loop:input_2']


def check_cnx():

    for p in LOOP_PNAMES:

        try:
            cnx = JCLI.get_all_connections(p)
        except Exception as e:
            if verbose:
                print('(librespot_watchdog)', str(e))
            continue

        cnx_pnames = [x.name for x in cnx]

        idx = int(p[-1:]) - 1

        psrc = f'librespot:out_{idx}'

        if psrc in cnx_pnames:
            if verbose:
                print('(librespot_watchdog)', f'{psrc} {p} (ok)')

        else:
            if verbose:
                print('(librespot_watchdog)', f'{psrc} is about to be connected to {p}')
            try:
                JCLI.connect(psrc, p)
            except Exception as e:
                if verbose:
                    print('(librespot_watchdog)', str(e))


if __name__ == "__main__":

    verbose = False
    if sys.argv[1:]:
        if '-v' in sys.argv[1]:
            verbose = True


    while True:
        check_cnx()
        sleep(3)
