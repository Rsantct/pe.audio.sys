#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A Brutefir peak monitor plugin

    Brutefir peaks should NEVER occur if your setup is fine.

    This plugin is mainly for testing purposes,
    during setting up your convolver stages.
    
    However, CPU consumption is minimal and can be left
    permanently activated in config.yml 'plugins' section.

    Warning messages will be displayed in the control web page,
    as well console printouts if --verbose.


    Usage:   peak_monitor.py    start | stop  [--verbose]
    
"""

import  sys
import  os
from    subprocess          import Popen
import  threading
from    collections         import deque
from    watchdog.observers  import Observer
from    watchdog.events     import FileSystemEventHandler

UHOME       = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    brutefir_mod        import cli as bf_cli
from    miscel              import send_cmd


LOGFOLDER   = f'{UHOME}/pe.audio.sys/log'
BFLOGPATH   = f'{LOGFOLDER}/brutefir.log'

VERBOSE = False


class Changed_files_handler(FileSystemEventHandler):
    """ will do something when some file has changed
    """

    def __init__(self, wanted_path=''):
        self.wanted_path = wanted_path

    def on_modified(self, event):
        #print( f'DEBUG: {event.event_type} {event.src_path}' )
        if event.src_path == self.wanted_path:
            check_bf_log()


def check_bf_log(reset_bf_peaks=True):
    """ try to read peak printouts from brutefir.log
    """

    def send_warning(peaks):
        if VERBOSE:
            print(f'PEAK MONITOR: {peaks}')
        send_cmd(f'aux warning set PEAK: {" ".join(peaks)}')
        send_cmd(f'aux warning expire 3')


    def read_last_line(fpath):
        res = ''
        try:
            res = deque(open(fpath), maxlen=1)[0].strip()
        except:
            pass
        return res


    def bf_peak_parse(pkline):
        """ Parse a peak printout line from Brutefir:

                peak: 0/197/+2.55 1/123/+0.61

            returns: a list of peaks in dB per output channel
        """
        pks = pkline.split()[1:]
        pks = [x.split('/')[-1] for x in pks]
        return pks


    def get_peak_and_reset():

        peaks = []

        bf_log_tail = read_last_line(BFLOGPATH)

        if bf_log_tail.startswith('peak:'):

            peaks = bf_peak_parse( bf_log_tail )

            if reset_bf_peaks:
                try:
                    bf_cli('rpk')
                except:
                    pass

        return peaks


    peaks = get_peak_and_reset()

    if peaks:
        send_warning(peaks)


def start():
    observer = Observer()
    observer.schedule(event_handler=Changed_files_handler(BFLOGPATH),
                      path=BFLOGPATH,
                      recursive=False)
    observer.start()
    obsloop = threading.Thread( target=observer.join() )
    obsloop.start()


def stop():
    Popen( ['pkill', '-f', 'peak_monitor.py'] )


if __name__ == "__main__":

    if '-v' in sys.argv[1:] or '--verbose' in sys.argv[1:]:
        VERBOSE = True

    if sys.argv[1:]:
        option = sys.argv[1]

        if option == 'start':
            start()

        elif option == 'stop':
            stop()

        else:
            print(__doc__)
    else:
        print(__doc__)

