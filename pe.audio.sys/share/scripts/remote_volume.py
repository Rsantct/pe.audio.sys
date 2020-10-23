#!/usr/bin/env python3
"""
    Listen for relative volume changes, then forward them
    to remote listening machines.
"""

import sys
import os
UHOME = os.path.expanduser("~")
sys.path.append( f'{UHOME}/pe.audio.sys/share' )
import miscel
import server

from subprocess import Popen
from time import sleep, time
import socket
import json
import threading
# This module is based on monitoring file changes under the pe.audio.sys folder
#   https://watchdog.readthedocs.io/en/latest/
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Handler class to do actions when a file change occurs.
class files_event_handler(FileSystemEventHandler):
    """ will do something when <wanted_path> file changes
    """
    # (i) This is an inherited class from the imported one 'FileSystemEventHandler',
    #     which provides the 'event' propiertie.
    #     Here we expand the class with our custom parameter 'wanted_path'.

    def __init__(self, wanted_path='', antibound=True):
        self.wanted_path = wanted_path
        self.antibound = antibound
        self.ts = time()

    def on_modified(self, event):
        # DEBUG
        #print( f'(i) event type: {event.event_type}, file: {event.src_path}' )
        if event.src_path == self.wanted_path:
            if self.antibound:
                if (time() - self.ts) > .1:
                    manage_volume()
                self.ts = time()
            else:
                manage_volume()


def read_last_line(fname=''):
    # source:
    # https://stackoverflow.com/questions/46258499/read-the-last-line-of-a-file-in-python
    # For large files it would be more efficient to seek to the end of the file,
    # and move backwards to find a newline.
    # Note that the file has to be opened in binary mode, otherwise,
    # it will be impossible to seek from the end.

    if not fname:
        return ''

    try:
        with open(fname, 'rb') as f:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
            last_line = f.readline().decode()
        return last_line.strip()

    except:
        return ''


def manage_volume():
    """ Read the last command, if it was about relative level change
        then forward it to remotes listeners.
    """
    cmd = read_last_line( peaudiosys_log )
    cmd = cmd.split(';')[1].strip()
    if 'level' not in cmd or 'add' not in cmd:
        return
    for cli_addr in remoteClients:
        miscel.send_cmd( cmd, host=cli_addr, verbose=True )


def detect_remotes():
    print('\nDetecting remote listening machines: ', end='')
    remoteClients = []
    nrange=range(233, 240)
    for n in nrange:
        addr = f'192.168.1.{str(n)}'
        if addr == my_ip:
            continue
        ans = miscel.send_cmd('state', timeout=.5, host=addr)

        if 'no answer' in ans:
            continue

        source = ''
        try:
            source = json.loads(ans)["input"]
        except:
            pass
        if 'remote' in source:
            remoteClients.append(addr)
    return remoteClients


def killme():
    Popen( f'pkill -f "scripts/remote_volume.py start"', shell=True )
    sys.exit()


# This is the 'standard' function called from server.py to process Rx messages,
# so we have offered this module to server.py in order to use this do().
# (see the 'server.MODULE=...' sentece below)
def do(argv):
    global remoteClients
    if argv == 'hello':
        print(f'Received hello from: {server.CLIADDR}')
        cli_addr = server.CLIADDR[0]
        if cli_addr not in remoteClients:
            remoteClients.append(cli_addr)
            print(f'Updated remote listening machines: {remoteClients}')
        return 'ack'
    else:
        return 'nack'


if __name__ == "__main__":


    for opc in sys.argv[1:]:
        if opc == 'stop':
            killme()
        elif opc == 'start':
            pass
        else:
            print(__doc__)
            sys.exit()


    my_hostname     = socket.gethostname()
    my_ip           = socket.gethostbyname(f'{my_hostname}.local')
    peaudiosys_log  = f'{UHOME}/pe.audio.sys/.peaudiosys_cmd.log'

    # Detecting remote listening clients
    remoteClients = detect_remotes()
    print(remoteClients)

    # Starts a WATCHDOG to observe file changes
    #   https://watchdog.readthedocs.io/en/latest/
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    #   Use recursive=True to observe also subfolders
    #   Even observing recursively the CPU load is negligible,
    #   but we prefer to observe to a single folder.

    # Will observe for changes in <.state.yml> under <pe.audio.sys> folder:
    observer = Observer()
    observer.schedule( files_event_handler( wanted_path=peaudiosys_log,
                                            antibound=True ),
                       path=f'{UHOME}/pe.audio.sys',
                       recursive=False )
    observer.start()

    # A server that listen for new remote listening clients to emerge
    server.SERVICE = 'remote_volume'
    server.MODULE = __import__(__name__)
    server.run_server('0.0.0.0', 9995, verbose=True)

    # main program will wait for <observer> thread to finish
    observer.join()
