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
    permanently activated in the config.yml 'plugins' section.

    If so, when peak occurs a WARNING MESSAGE with the most peaking event
    will be displayed in the control web page, as well you can see console
    printouts if running this script with the --verbose option.

    You can also check peaks with timestamp by issuing:

        tal -F ~/pe.audio.sys/log/brutefir_peaks.log


    A BEEP sound at -10 dB will be played when detecting peaks.
    (Needs a 'brutefir' ALSA device, see .asoundrc.sample)


    Usage:   peak_monitor.py    start | stop  [--verbose]

"""

import  sys
import  os
from    subprocess          import Popen, DEVNULL
from    time                import ctime
import  threading
from    watchdog.observers  import Observer
from    watchdog.events     import FileSystemEventHandler

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    miscel              import send_cmd, read_last_line, USER, LOG_FOLDER
from    share.miscel        import do_3_beep


LOG_PATH = f'{LOG_FOLDER}/brutefir_peaks.log'

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


def log_peak(peaks):
    """ peaks is a raw list of peaks, example:

            [-inf, -inf, -8.6, 2.5, 10.1, -8.8, 1.7, 9.7]
    """

    # Brutefir Outputs MAP example:
    #   {'0': {'name': 'fr.L', 'delay': 0}, '1': {'name': 'fr.R', 'delay': 0}}

    # Will add the Output ID to make the log human readable
    peaks_str = ''

    for n, p in enumerate(peaks):

        out_name = BFOUTMAP[str(n)]["name"]

        if 'void' in out_name:
            continue

        if p > 0:
            peaks_str += f'  {out_name.rjust(4)}: {str(p).rjust(4)}'

        else:
            peaks_str += f'  {out_name.rjust(4)}:     '


    with open(LOG_PATH, 'a') as f:
        f.write( f'{ctime()} {peaks_str}\n' )


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

            returns: a list of peaks in dB per output channel, example:
            [-inf, -inf, -11.6, -1.7, 9.6, -11.4, -1.2, 10.2]
        """
        pks = []

        try:
            pks = pkline.split()[1:]
            pks = [x.split('/')[-1] for x in pks]
            # round to 1 decimal place
            pks = [round(float(x), 1) for x in pks]

        except:
            pass

        return pks



    def get_bf_peak_and_reset(reset=reset_bf_peaks):
        """ read brutefir.log to find the last peak line,

            returns: a peak info string 'PEAK OutID: XX dB'
        """

        peaks    = []
        pMaxInfo = ''

        bf_log_tail = read_last_line(BFLOGPATH)

        if bf_log_tail.startswith('peak:'):

            peaks = bf_peak_parse( bf_log_tail )
            # example: [-inf, -inf, -21.3, -3.1, 8.3, -17.4, -3.8, 7.3]

            if reset:
                try:
                    bf_cli('rpk')
                except:
                    pass

        if peaks:

            try:
                # find MAX peak
                pmaxIdx  = max(range(len(peaks)), key=peaks.__getitem__)
                pmaxdB   = peaks[pmaxIdx]
                pmaxOut  = BFOUTMAP[ str(pmaxIdx) ]['name']
                pMaxInfo = f'PEAK {pmaxOut}: {pmaxdB} dB'

            except:
                pass

        return pMaxInfo, peaks


    pMaxInfo, peaks = get_bf_peak_and_reset()

    if pMaxInfo:

        job_beep = threading.Thread(target=do_3_beep)
        job_beep.start()

        log_peak( peaks )

        send_warning( pMaxInfo )


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
        # Brutefir Outputs MAP example:
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

