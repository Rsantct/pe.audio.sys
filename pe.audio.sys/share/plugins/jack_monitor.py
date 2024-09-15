#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A JACK Xruns monitor plugin

    (i) Needs silent:false under config.yml

    Xruns should never occur during normal playback,
    but can occur when emerging or vanishing a jack client.
    This is normal mainly in moderate CPU systems (Raspberri Pi ...)

    This plugin is mainly for testing purposes,
    during setting up your system.

    However, CPU consumption is minimal and can be left
    permanently activated in config.yml 'plugins' section.

    WARNING MESSAGES will be displayed in the control web page,
    as well you can see console printouts if --verbose.

    A BEEP sound at -10 dB will be played when detecting Xruns.
    (Needs a 'brutefir' ALSA device, see .asoundrc.sample)

    Usage:   jack_monitor.py    start | stop  [--verbose]

"""

import  sys
import  os
from    subprocess          import Popen, DEVNULL
import  threading
from    watchdog.observers  import Observer
from    watchdog.events     import FileSystemEventHandler

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

JACKDLOGPATH = f'{UHOME}/pe.audio.sys/log/jackd.log'

from    miscel              import send_cmd, read_last_lines, USER
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
            check_jack_log()


def check_jack_log():
    """ try to read Xrun printouts from jackd.log
    """

    def send_warning(w):
        if VERBOSE:
            print(f'JACK MONITOR: {w}')
        send_cmd(f'aux warning clear')
        send_cmd(f'aux warning set {w}')
        # Do not reset peak warning
        # send_cmd(f'aux warning expire 3')


    def get_xruns():
        """ read jackd.log to find the last peak line,

            returns: a warning string 'JACK XRUN'
        """

        jack_log_tail = read_last_lines(filename=JACKDLOGPATH, nlines=2)

        if 'xrun' in ' '.join(jack_log_tail).lower():
            return 'JACK XRUN'
        else:
            return ''


    xruns = get_xruns()

    if xruns:
        do_3_beep()
        send_warning(xruns)


def start():
    observer = Observer()
    observer.schedule(event_handler=MyFileEventHandler(fpath=JACKDLOGPATH),
                      path=JACKDLOGPATH,
                      recursive=False)
    observer.start()
    obsloop = threading.Thread( target=observer.join() )
    obsloop.start()


def stop():
    Popen( ['pkill', '-u', USER, '-f', 'jack_monitor.py'] )


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

