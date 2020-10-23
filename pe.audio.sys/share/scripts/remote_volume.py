#!/usr/bin/env python3
"""
    A daemon that listen for relative volume changes,
    then forward them to all remote listener pe.audio.sys.

    Usage:      remote_volume.py   start|stop

    NOTE:
    A newcoming remote listener machine will need to send 'hello'
    to this daemon at port <peaudiosys_port> + 5 (usually 9995)

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
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# ------------- USER CONFIG --------------
# x.x.x.RANGE
REMOTES_ADDR_RANGE = range(230, 240)
# ----------------------------------------



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


def manage_volume(purge=False):
    """ Read the last command, if it was about relative level change
        then forward it to remotes listeners.
    """
    global remoteClients

    # Retrieving the last 'level X add' command
    tmp = miscel.read_last_line( peaudiosys_log )
    # e.g.: "2020/10/23 17:16:43; level -1 add; done"
    cmd = tmp.split(';')[1].strip()

    # Early return if not a relative level change
    if 'level' not in cmd or 'add' not in cmd:
        return

    # Forwarding it to remotes
    for cli_addr in remoteClients:

        # checking if still listening to us
        if 'remote' in miscel.get_source_from_remote(cli_addr):
            print( f'remote {cli_addr} sending \'{cmd}\'' )
            miscel.send_cmd( cmd, host=cli_addr, verbose=False )

        else:
            print( f'remote {cli_addr} not listening by now :-/' )
            if purge:
                remoteClients.remove( cli_addr )
                print( f'Updated remote listening machines: {remoteClients}' )


def detect_remotes():
    """ list of remote IPs listening to a source named *remote*
    """
    clients = []

    for n in REMOTES_ADDR_RANGE:

        addr_list = my_ip.split('.')
        addr_list[-1] = str(n)
        addr = '.'.join( addr_list )

        if addr == my_ip:
            continue

        if 'remote' in miscel.get_source_from_remote(addr):
            clients.append(addr)

    return clients


def killme():
    Popen( f'pkill -f "scripts/remote_volume.py start"', shell=True )
    sys.exit()


# This is the 'standard' function called from server.py to process Rx messages,
# so we have offered this module to server.py in order to use this do().
# (See the 'server.MODULE=...' sentece below)
def do(argv):

    global remoteClients

    if argv == 'hello':
        print( f'Received hello from: {server.CLIADDR}' )
        cli_addr = server.CLIADDR[0]
        if cli_addr not in remoteClients:
            remoteClients.append(cli_addr)
            print( f'Updated remote listening machines: {remoteClients}' )
        return 'ack'

    else:
        return 'nack'


if __name__ == "__main__":

    # Reading command line
    if sys.argv[1:]:
        if sys.argv[1] == 'stop':
            killme()
        elif sys.argv[1] == 'start':
            pass
        else:
            print(__doc__)
            sys.exit()
    else:
        print(__doc__)
        sys.exit()


    # Retrieving basic data to this to work
    my_hostname     = socket.gethostname()
    my_ip           = socket.gethostbyname(f'{my_hostname}.local')
    peaudiosys_log  = f'{UHOME}/pe.audio.sys/.peaudiosys_cmd.log'

    # Detecting remote listening clients
    remoteClients = detect_remotes()
    print( f'\nDetected remote listening machines: {remoteClients}' )


    # Will observe for changes in <.state.yml> under <pe.audio.sys> folder:
    # Starts a WATCHDOG to observe file changes
    #   https://watchdog.readthedocs.io/en/latest/
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    #   Use recursive=True to observe also subfolders
    #   Even observing recursively the CPU load is negligible,
    #   but we prefer to observe to a single folder.
    observer = Observer()
    observer.schedule( files_event_handler( wanted_path=peaudiosys_log,
                                            antibound=True ),
                       path=f'{UHOME}/pe.audio.sys',
                       recursive=False )
    observer.start()
    print( f'Forwarding relative level changes to remotes ...' )

    # A server that listen for new remote listening clients to emerge
    print( f'Keep listening for new remmotes ...' )
    server.SERVICE = 'remote_volume'
    server.MODULE = __import__(__name__)
    server.run_server( '0.0.0.0', miscel.CONFIG['peaudiosys_port'] + 5,
                       verbose=False)
