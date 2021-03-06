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
    A daemon that listen for relative volume changes,
    then forward them to all remote listener pe.audio.sys.

    Usage:      remote_volume_daemon.py   start|stop

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


# Generic handler from 'watchdog' for doing actions when a file change occurs
class file_event_handler(FileSystemEventHandler):
    """ will do something when <wanted_path> file changes
    """
    # (i) This is an inherited class from the imported one 'FileSystemEventHandler',
    #     which provides the 'event' propiertie.
    #     Here we expand the class with our custom parameters:
    #     'observed_file' and 'wanted_action'

    def __init__(self, filepath, action, antibound=True):
        self.filepath = filepath
        self.action = action
        self.antibound = antibound
        self.ts = time()

    def on_modified(self, event):
        # DEBUG
        #print( f'(i) event type: {event.event_type}, file: {event.src_path}' )
        if event.src_path == self.filepath:
            if self.antibound:
                if (time() - self.ts) > .1:
                    globals()[self.action]()
                self.ts = time()
            else:
                    globals()[self.action]()


def get_curr_state():
    return yaml.safe_load( open( f'{UHOME}/pe.audio.sys/.state.yml','r') )


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


def remote_relat_level(cli_addr, rel_level_cmd):
    print( f'remote {cli_addr} sending \'{rel_level_cmd}\'' )
    miscel.send_cmd( rel_level_cmd, host=cli_addr, verbose=False )


def remote_LU_offset(cli_addr):
    """ updates the current LU offset to remote
    """
    cmd = f'lu_offset { get_curr_state()["lu_offset"] }'
    print( f'remote {cli_addr} sending \'{cmd}\'' )
    miscel.send_cmd( cmd, host=cli_addr, verbose=False )

# Action for observer1
def detect_level_changes():
    """ Read the last command from <peaudiosys.log>
        If it was about a relative level change,
        then forward it to remotes listeners.
        Also will forward the current LU offset.
    """
    global remoteClients

    # Retrieving the last 'level X add' command
    tmp = miscel.read_last_line( cmd_log_path )
    # e.g.: "2020/10/23 17:16:43; level -1 add; done"
    cmd = tmp.split(';')[1].strip()

    # Filtering <relative level> or <lu_offset> commands
    rel_level_cmd = ''
    lu_offset_cmd = ''
    if 'level' in cmd and 'add' in cmd:
        rel_level_cmd = cmd
    if 'lu_offset' in cmd:
        lu_offset_cmd = cmd

    # Early return
    if not rel_level_cmd and not lu_offset_cmd:
        return

    # Forwarding commands to remotes
    for rem_addr in remoteClients:

        # checking if remote is still listening to us
        if 'remote' in miscel.get_source_from_remote(rem_addr):

            # Updates relative VOLUME event to remote
            if rel_level_cmd:
                remote_relat_level(rem_addr, rel_level_cmd)
            # Also updates LU OFFSET to remote
            if lu_offset_cmd:
                remote_LU_offset(rem_addr)

        # purge from remotes list if not listening anymore
        else:
            print( f'remote {rem_addr} not listening by now :-/' )
            remoteClients.remove( rem_addr )
            print( f'Updated remote listening machines: {remoteClients}' )


# Action for observer2
def all_remotes_LU_offset():

    global last_lu_offset, remoteClients

    curr_lu_offset = get_curr_state()["lu_offset"]

    if curr_lu_offset != last_lu_offset:

        last_lu_offset = curr_lu_offset

        for rem_addr in remoteClients:

            if 'remote' in miscel.get_source_from_remote(rem_addr):
                # Updates LU OFFSET to remotes
                remote_LU_offset(rem_addr)
            else:
                print( f'remote {rem_addr} not listening by now :-/' )
                remoteClients.remove( rem_addr )
                print( f'Updated remote listening machines: {remoteClients}' )



# The action called from our instance of <server.py> when receiving messages.
# (See below 'server.MODULE=...' when initiating <server.py> )
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
                # set the current LU offset in the remote listener
                remote_LU_offset(cli_addr)
            result = 'ack'
        else:
            print( f'(remote_volume) Tas tonto: received \'hello\' '
                   f'from MY SELF ({cli_addr})' )

    return result


def killme():
    Popen( f'pkill -f "scripts/remote_volume_daemon.py start"', shell=True )
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
    cmd_log_path    = f'{UHOME}/pe.audio.sys/.peaudiosys_cmd.log'
    state_path      = f'{UHOME}/pe.audio.sys/.state.yml'
    last_lu_offset  = get_curr_state()["lu_offset"]

    # Detecting remote listening clients
    remoteClients = detect_remotes()
    print( f'(remote_volume) Detected {len(remoteClients)} '
           f'remote listening machines: {remoteClients}' )

    # A WATCHDOG to observe file changes
    #   https://watchdog.readthedocs.io/en/latest/
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    #   Use recursive=True to observe also subfolders
    #   Even observing recursively the CPU load is negligible,
    #   but we prefer to observe to a single folder.
    observer1 = Observer()
    observer2 = Observer()
    observer1.schedule( file_event_handler( filepath=cmd_log_path,
                                            action='detect_level_changes',
                                            antibound=True ),
                        path=f'{UHOME}/pe.audio.sys',
                        recursive=False )
    observer2.schedule( file_event_handler( filepath=state_path,
                                            action='all_remotes_LU_offset',
                                            antibound=True ),
                        path=f'{UHOME}/pe.audio.sys',
                        recursive=False )
    observer1.start()
    observer2.start()
    print( f'(remote_volume) Forwarding relative level changes to remotes ...' )

    # A server that listen for new remote listening clients to emerge
    print( f'(remote_volume) Keep listening for new remotes ...' )
    server.SERVICE = 'remote_volume_daemon'
    server.MODULE = __import__(__name__)
    server.run_server( '0.0.0.0', miscel.CONFIG['peaudiosys_port'] + 5,
                       verbose=True)
