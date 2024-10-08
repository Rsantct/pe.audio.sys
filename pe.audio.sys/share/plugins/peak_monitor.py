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

    WARNING MESSAGES will be displayed in the control web page,
    as well you can see console printouts if --verbose.

    A BEEP sound at -10 dB will be played when detecting peaks.
    (Needs a 'brutefir' ALSA device, see .asoundrc.sample)

    Usage:   peak_monitor.py    start | stop  [--verbose]

"""

import  sys
import  os
from    subprocess          import Popen, DEVNULL
import  threading
from    watchdog.observers  import Observer
from    watchdog.events     import FileSystemEventHandler

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    miscel              import send_cmd, read_last_line, USER
from    share.miscel        import do_3_beep


VERBOSE = False


class MyFileEventHandler(FileSystemEventHandler):
    """ Subclass that will do something when a file
        has been modified.

        'fpath' parameter is expected.
    """

    def __init__(self, fpath=''):
        self.fpath = fpath

    def on_modified(self, event):
        #print( f'DEBUG: {event.event_type} {event.src_path}' ) # DEBUG
        if event.src_path == self.fpath:
            check_bf_log()


def check_bf_log(reset_bf_peaks=True):
    """ try to read peak printouts from brutefir.log
    """

    def send_warning(w):
        if VERBOSE:
            print(f'PEAK MONITOR: {w}')
        send_cmd(f'aux warning clear')
        send_cmd(f'aux warning set {w}')
        # Do not reset peak warning
        # send_cmd(f'aux warning expire 3')


    def bf_peak_parse(pkline):
        """ Parse a peak printout line from Brutefir:

                peak: 0/197/+2.55 1/123/+0.61

            returns: a list of peaks in dB per output channel
        """
        pks = pkline.split()[1:]
        pks = [x.split('/')[-1] for x in pks]
        return pks


    def get_bf_peak_and_reset(reset=reset_bf_peaks):
        """ read brutefir.log to find the last peak line,

            returns: a peak info string 'PEAK OutID: XX dB'
        """

        peaks    = []
        peakInfo = ''

        bf_log_tail = read_last_line(BFLOGPATH)

        if bf_log_tail.startswith('peak:'):

            peaks = bf_peak_parse( bf_log_tail )

            if reset:
                try:
                    bf_cli('rpk')
                except:
                    pass

        if peaks:
            try:
                peaks    = [round(float(x), 1) for x in peaks]
                pmaxIdx  = max(range(len(peaks)), key=peaks.__getitem__)
                pmaxdB   = peaks[pmaxIdx]
                pmaxOut  = BFOUTMAP[ str(pmaxIdx) ]['name']
                peakInfo = f'PEAK {pmaxOut}: {pmaxdB} dB'
            except:
                pass

        return peakInfo


    peakInfo = get_bf_peak_and_reset()

    if peakInfo:
        do_3_beep()
        send_warning(peakInfo)


def start():
    observer = Observer()
    observer.schedule(event_handler=MyFileEventHandler(fpath=BFLOGPATH),
                      path=BFLOGPATH,
                      recursive=False)
    observer.start()
    obsloop = threading.Thread( target=observer.join() )
    obsloop.start()


def stop():
    Popen( ['pkill', '-u', USER, '-f', 'peak_monitor.py start'] )


if __name__ == "__main__":

    try:
        from brutefir_mod  import cli as bf_cli, get_config_outputs, BFLOGPATH
        # Outputs map example:
        #   {'0': {'name': 'fr.L', 'delay': 0}, '1': {'name': 'fr.R', 'delay': 0}}
        BFOUTMAP = get_config_outputs()
    except:
        print(f'(peak_monitor) Brutefir not available')
        stop()
        sys.exit()


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

