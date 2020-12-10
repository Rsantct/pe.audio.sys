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

import yaml
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



# Handler class to do actions (manage levels) when a
# file change occurs (a command has been issued inside the commands log file)
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
                    manage_levels()
                self.ts = time()
            else:
                manage_levels()


def manage_levels(purge=False):
    """ Read the last command, if it was about relative level change
        then forward it to remotes listeners.
        Also updates the current LU offset.
    """
    global remoteClients

    # Retrieving the last 'level X add' command
    tmp = miscel.read_last_line( peaudiosys_log )
    # e.g.: "2020/10/23 17:16:43; level -1 add; done"
    cmd = tmp.split(';')[1].strip()

    # Filtering relative level or lu_offset commands
    rel_level_cmd = ''
    lu_offset_cmd = ''
    if 'level' in cmd and 'add' in cmd:
        rel_level_cmd = cmd
    if 'lu_offset' in cmd:
        lu_offset_cmd = cmd

    # Early return if not relative level or lu_offset
    if not rel_level_cmd and not lu_offset_cmd:
        return

    # Forwarding it to remotes
    for cli_addr in remoteClients:

        # checking if still listening to us
        if 'remote' in miscel.get_source_from_remote(cli_addr):

            # Updates relative VOLUME event to remotes
            if rel_level_cmd:
                manage_volume(cli_addr, rel_level_cmd)
            # Updates LU OFFSET to remotes
            if lu_offset_cmd:
                manage_LU_offset(cli_addr)

        # if not listening anymore
        else:
            print( f'remote {cli_addr} not listening by now :-/' )
            if purge:
                remoteClients.remove( cli_addr )
                print( f'Updated remote listening machines: {remoteClients}' )


def manage_volume(cli_addr, rel_level_cmd):
    """ simply sends the relative level change to remote
    """
    print( f'remote {cli_addr} sending \'{rel_level_cmd}\'' )
    miscel.send_cmd( rel_level_cmd, host=cli_addr, verbose=False )


def manage_LU_offset(cli_addr):
    """ updates the current LU offset to remote
    """
    # retrieve current LU offset
    curr_state = yaml.safe_load( open(f'{UHOME}/pe.audio.sys/.state.yml', 'r') )
    # sending to remote
    cmd = f'lu_offset {curr_state["lu_offset"]}'
    print( f'remote {cli_addr} sending \'{cmd}\'' )
    miscel.send_cmd( cmd, host=cli_addr, verbose=False )


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

        if 'remote' in miscel.get_source_from_remote(addr).lower():
            clients.append(addr)

    return clients


# This is the 'standard' function called from server.py to process Rx messages,
# so we have offered this module to server.py in order to use this do().
# (See the 'server.MODULE=...' sentece below)
def do(cmd):

    global remoteClients

    cli_addr = server.CLIADDR[0]
    result = 'nack'

    # Only 'hello' command is processed
    if cmd == 'hello':
        if cli_addr != my_ip and '127.0.' not in cli_addr:
            print( f'(remote_volume) Received hello from: {cli_addr}' )
            if cli_addr not in remoteClients:
                # updating new client into remote clients list
                remoteClients.append(cli_addr)
                print( f'(remote_volume) Updated remote listening machines: '
                       f'{remoteClients}' )
                # set the current LU offset into remote
                manage_LU_offset(cli_addr)
            result = 'ack'
        else:
            print( f'(remote_volume) Tas tonto: received \'hello\' '
                   f'from MY SELF ({cli_addr})' )

    return result


def killme():
    Popen( f'pkill -f "scripts/remote_volume.py start"', shell=True )
    sys.exit()


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
    print( f'(remote_volume) Detected {len(remoteClients)} '
           f'remote listening machines: {remoteClients}' )


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
    print( f'(remote_volume) Forwarding relative level changes to remotes ...' )

    # A server that listen for new remote listening clients to emerge
    print( f'(remote_volume) Keep listening for new remmotes ...' )
    server.SERVICE = 'remote_volume'
    server.MODULE = __import__(__name__)
    server.run_server( '0.0.0.0', miscel.CONFIG['peaudiosys_port'] + 5,
                       verbose=True)
