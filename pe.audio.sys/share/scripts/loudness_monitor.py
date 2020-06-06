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
    Loudness monitor daemon

    usage:   loudness_monitor.py    start | stop
"""
import sys
import os
from subprocess import Popen
from time import sleep
import yaml
import json
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from share.loudness_meter import LU_meter


UHOME           = os.path.expanduser("~")
MAINFOLDER      = f'{UHOME}/pe.audio.sys'
CONFIGFNAME     = f'{MAINFOLDER}/config.yml'
STATEFNAME      = f'{MAINFOLDER}/.state.yml'
CTRLFNAME       = f'{MAINFOLDER}/.loudness_control'
MEASFNAME       = f'{MAINFOLDER}/.loudness_monitor'
METADATAFNAME   = f'{MAINFOLDER}/.player_metadata'


def stop():

    Popen( 'pkill -f "loudness_monitor.py\ start"', shell=True )
    sleep(.5)


def control_fifo_prepare(fname):
    try:
        if os.path.exists(fname):
            os.remove(fname)
        os.mkfifo(fname)
    except:
        print(f'(loudness_monitor.py) ERROR preparing fifo {fname}')
        raise


def control_fifo_read_loop(fname, meter):
    """ Loop forever listen for runtime commands through by the fifo control file:
        'reset'         force the reset flag to True
        'scope=xxxxx'   update the scope (metadata key observed to auto reset LU-I)
    """
    global scope
    while True:
        # opening fifo...
        with open(fname) as f:
            while True:
                f_data = f.read().strip()
                if len(f_data) == 0:
                    break
                # Resets the meter
                if f_data == 'reset':
                    meter.reset()
                # Changes the scope in runtime, i.e the
                # metadata key observed to autoreset LU-I)
                elif f_data[:6] == 'scope=':
                    new_scope = f_data[6:]
                    if new_scope in ('album','title', 'track'):
                        if new_scope == 'track':
                            new_scope = 'title'
                        scope = new_scope


# Handler class to do actions when a file change occurs
class My_files_event_handler(FileSystemEventHandler):
    """ Will reset the meter when:
        - input preamp changes
        - playing metadata album or title changes
    """

    def __init__(self, meter):
        self.meter = meter


    def on_modified(self, event):

        global last_input, last_scope, scope
        path = event.src_path

        # Check if preamp input has changed
        if STATEFNAME in path:
            with open( STATEFNAME, 'r' ) as f:
                preamp_state = yaml.safe_load(f)
                if not preamp_state:
                    return
                if last_input != preamp_state['input']:
                    last_input = preamp_state['input']
                    self.meter.reset()
                    sleep(.25)      # anti bouncing

        # Check if metadata info has changed
        if METADATAFNAME in path and scope:
            with open( METADATAFNAME, 'r' ) as f:
                md = yaml.safe_load(f)
                if not md:
                    return
                if last_scope != md[scope]:
                    last_scope = md[scope]
                    self.meter.reset()
                    sleep(.25)      # anti bouncing


def start():

    def initial_scope():
        # The metadata key ('album', 'title', '') to reset the measured LU-I:
        # If void '' then will reset on selected input changes.
        try:
            with open(f'{MAINFOLDER}/config.yml', 'r') as f:
                md_key = yaml.safe_load(f)['LU_reset_md_field']
                if not md_key:  # None --> ''
                    md_key = ''
        except:
            # Defaults to album if not configured
            md_key = 'album'
        if not ( md_key in ('album', 'title', 'track') ):
            raise Exception(f'(loudness_monitor) metadata field \'{md_key}\' not valid')
        # We accept 'track' to mean 'title'
        if md_key == 'track':
            md_key = 'title'
        return md_key


    def save2disk():
        # Saving to disk rounded to 1 dB
        if save2disk:
            with open( MEASFNAME, 'w') as f:
                I_LU = meter.I - -23.0      # from dBFS to dBLU ( 0 dBLU = -23dBFS )
                M_LU = meter.M - -23.0
                d = { "LU_I":  round(I_LU // meter.I_threshold * meter.I_threshold, 0),
                      "LU_M":  round(M_LU // meter.M_threshold * meter.M_threshold, 0),
                      "scope": scope }
                f.write( json.dumps(d) )


    def wait_M():
        while True:
            M_event.wait()
            save2disk()
            M_event.clear()


    def wait_I():
        while True:
            I_event.wait()
            save2disk()
            I_event.clear()


    global last_input, last_scope, scope

    # Initialize the scope
    scope = initial_scope()
    last_scope = ''

    # Reading current input source
    with open( STATEFNAME, 'r' ) as state_file:
        last_input = yaml.safe_load(state_file)['input']

    # Starts the meter and passing events to listen for changes in measuremets
    print(f'(loudness_monitor) spawn PortAudio ports in JACK')
    M_event = threading.Event()
    I_event = threading.Event()
    meter = LU_meter( device='pre_in_loop', display=False,
                     M_event=M_event,
                     I_event=I_event )
    meter.start()

    # Threading the fifo listening for controling this script
    control_fifo_prepare(CTRLFNAME)
    control = threading.Thread( target=control_fifo_read_loop,
                                args=(CTRLFNAME, meter) )
    control.start()

    # Threading an Observer watchdog for file changes
    #   https://watchdog.readthedocs.io/en/latest/
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    #   Use recursive=True to observe also subfolders
    #  (i) Even observing recursively the CPU load is negligible
    observer = Observer()
    observer.schedule( event_handler=My_files_event_handler(meter),
                       path=MAINFOLDER, recursive=False )
    obsthread = threading.Thread( target=observer.start() )
    obsthread.start()

    # Threading meter changes events
    wait_M = threading.Thread( target=wait_M )
    wait_M.start()
    wait_I = threading.Thread( target=wait_I )
    wait_I.start()


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
