#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" A monitor for JACK and PipeWire XRUNS

    For Jack, will set a python-jack callback

    For Pipewire, will poll periodically 'pw-top' utility

    Usage:  xrun_monitor.py  start | stop  &

    A log can be found under pe.audio.sys/log folder

"""

import  sys
import  os
import  subprocess  as sp
import  threading
from    time        import sleep
from    datetime    import datetime
import  jack
from    getpass     import getuser


UHOME   = os.path.expanduser("~")
LOGPATH = f'{UHOME}/pe.audio.sys/log/xrun_monitor.log'


PWTOP_WANTED = ['jack_sink', 'spotify']
PWTOP_PERIOD = 3


def do_log(msg, add_timestamp=True):

    with open(LOGPATH, 'a') as f:

        if add_timestamp:

            # iso format
            #now = datetime.now().isoformat(timespec='seconds')
            # journalctl format
            now = datetime.now().strftime("%b %d %H:%M:%S")

            msg = f'{now} {msg}'

        f.write(msg + '\n')
        print(msg)


def do_pw_top_loop():

    def get_pw_top_errors():
        """ queries pw-top
            returns a dict, for example  {'jack_sink': 0, 'spotify': 0}
        """

        res = {}

        try:
            tmp = sp.check_output('pw-top -b -n2'.split()).decode()

            # S   ID  QUANT   RATE    WAIT    BUSY   W/Q   B/Q  ERR FORMAT           NAME
            # C   31      0      0    ---     ---   ---   ---     0                  Dummy-Driver
            # C   32      0      0    ---     ---   ---   ---     0                  Freewheel-Driver
            # C   38      0      0    ---     ---   ---   ---     0                  jack_sink
            # C   42      0      0    ---     ---   ---   ---     0                  Midi-Bridge
            # C   53      0      0    ---     ---   ---   ---     0                  spotify
            # S   ID  QUANT   RATE    WAIT    BUSY   W/Q   B/Q  ERR FORMAT           NAME
            # S   31      0      0    ---     ---   ---   ---     0                  Dummy-Driver
            # S   32      0      0    ---     ---   ---   ---     0                  Freewheel-Driver
            # R   38    512  44100  60,7us  10,1us  0,01  0,00    0     F32P 2 44100 jack_sink
            # R   53   8192  44100  24,8us  22,2us  0,00  0,00    0    F32LE 2 44100  + spotify
            # S   42      0      0    ---     ---   ---   ---     0                  Midi-Bridge

        except:
            return res

        lines = tmp.split('\n')
        lines = [x.strip() for x in lines]

        for line in lines:

            if 'W/Q' in line and 'B/Q' in line:
                res = {}

            for wanted in PWTOP_WANTED:

                if line.endswith(wanted):

                    line_chunks = line.split()

                    count = int(line_chunks[8])

                    res[wanted] = count

        # Example:  {'jack_sink': 0, 'spotify': 0}
        return res


    while True:

        warning = ''

        errors = get_pw_top_errors()

        # example {'jack_sink': 0, 'spotify': 0}
        for k, v in errors.items():
            if v > 0:
                warning += f' {k}:{v}'

        if warning:
            warning = 'pw-top ERRORS' + warning
            do_log(warning)


        sleep(PWTOP_PERIOD)


def pw_is_running():

    try:
        sp.check_output('pgrep pipewire'.split())
        return True
    except:
        return False


def jack_xrun_handler(x):

    msg = f'jackd XRUNS: {str(x)}'
    do_log(msg)


def pw_journalctl_loop():
    """ Pendiente implementar basado en journalctl --show-cursor
    """
    pass


def start():

    # Pipewire monitoring thread only if pipewire detected:

    if pw_is_running():

        pw_top_job = threading.Thread(target=do_pw_top_loop)
        pw_top_job.start()
        tmp = "pw-top or "

    else:
        tmp = ''

    do_log( f'Starting xruns monitor in {tmp}jackd ...' )


    # Jack monitoring loop forever

    jcli = jack.Client('tmp', no_start_server=True)
    jcli.set_xrun_callback(jack_xrun_handler)

    with jcli:
        jcli.activate()

        try:
            while True:
                sleep(1)

        except Exception as e:
            jcli.deactivate()
            jcli.close()

            do_log(f'Exit Jack monitor loop...: {e}')


def stop():
    sp.Popen( ['pkill', '-u', getuser(), '-KILL', '-f', 'xrun_monitor.py start'] )


if __name__ == '__main__':

    if sys.argv[1:]:

        if sys.argv[1] == 'start':
            start()

        elif sys.argv[1] == 'stop':
            stop()

        else:
            print(__doc__)

    else:
        print(__doc__)

