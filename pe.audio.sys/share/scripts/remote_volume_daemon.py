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
    to this daemon at port <peaudiosys_base_port> + 5 (usually 9995)

"""

import sys
import os

UHOME           = os.path.expanduser("~")
BASE_DIR        = f'{UHOME}/pe.audio.sys'
STATE_PATH      = f'{BASE_DIR}/.state.yml'
LOG_DIR         = f'{UHOME}/pe.audio.sys/log'
CMD_LOG_PATH    = f'{LOG_DIR}/peaudiosys_cmd.log'

sys.path.append( f'{BASE_DIR}/share' )
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
    """ Will do something when a <fname> change occurs
    """
    # (i) This is an inherited class from the imported one 'FileSystemEventHandler',
    #     which provides the 'event' propiertie.
    #     Here we expand the class with our custom parameters:
    #     'fname' and wanted 'action'

    def __init__(self, fname, action, antibound=True):
        self.fname      = fname
        self.action     = action
        self.antibound  = antibound
        self.ts         = time()

    def on_modified(self, event):
        # DEBUG
        #print( f'(i) event type: {event.event_type}, file: {event.src_path}' )
        if event.src_path == self.fname:
            if self.antibound:
                if (time() - self.ts) > .1:
                    globals()[self.action]()
                self.ts = time()
            else:
                    globals()[self.action]()


def get_curr_state():

    state = {'lu_offset': 0}

    # Avoid a possible loading of a blank .state.yml
    tries = 3
    while tries:
        try:
            tmp = yaml.safe_load( open( f'{BASE_DIR}/.state.yml','r') )
            if tmp:
                state = tmp
                break
        except:
            sleep(.1)
            tries -= 1

    return state


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

        if 'remote' in miscel.get_remote_selected_source(addr).lower():
            clients.append(addr)

    return clients


def remote_change_level(cli_addr, level_cmd):
    print( f'(remote_volume) remote {cli_addr} sending \'{level_cmd}\'' )
    miscel.send_cmd( level_cmd, host=cli_addr, verbose=False )


def remote_update_LU_offset(cli_addr):
    """ updates the current LU offset to remote
    """
    cmd = f'lu_offset { get_curr_state()["lu_offset"] }'
    print( f'(remote_volume) remote {cli_addr} sending \'{cmd}\'' )
    miscel.send_cmd( cmd, host=cli_addr, verbose=True )


# Action for observer1
def cmd_log_file_changed():
    """ Read the last command from <peaudiosys.log>
        If it was about a relative level change or lu_offset
        then forwards it to the remotes listeners.
    """
    global remoteClients

    # Retrieving the last 'level X add' command
    tmp = miscel.read_last_line( CMD_LOG_PATH )
    # e.g.: "2020/10/23 17:16:43; level -1 add; done"
    cmd = tmp.split(';')[1].strip()

    # Filtering <relative level> or <lu_offset> commands
    level_cmd = ''
    if ('level' in cmd and 'add' in cmd) or 'lu_offset' in cmd:
        level_cmd = cmd

    # Early return
    if not level_cmd:
        return

    # Forwarding commands to remotes
    for rem_addr in remoteClients:

        # checking if remote is still listening to us
        if 'remote' in miscel.get_remote_selected_source(rem_addr):

            # Updates relative VOLUME event to remote
            if level_cmd:
                remote_change_level(rem_addr, level_cmd)

        # purge from remotes list if not listening anymore
        else:
            print( f'remote {rem_addr} not listening by now :-/' )
            remoteClients.remove( rem_addr )
            print( f'Updated remote listening machines: {remoteClients}' )


# Action for observer2
def state_file_changed():
    all_remotes_LU_offset()


# Broadcast LU_offset to all remote machines
def all_remotes_LU_offset(force=False):

    global last_lu_offset, remoteClients

    curr_lu_offset = get_curr_state()["lu_offset"]

    if (curr_lu_offset != last_lu_offset) or force:

        last_lu_offset = curr_lu_offset

        for rem_addr in remoteClients:

            if 'remote' in miscel.get_remote_selected_source(rem_addr):
                # Updates LU OFFSET to remotes
                remote_update_LU_offset(rem_addr)
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
                remote_update_LU_offset(cli_addr)
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
    observer1.schedule( file_event_handler( fname=CMD_LOG_PATH,
                                            action='cmd_log_file_changed',
                                            antibound=True ),
                                            path=LOG_DIR,
                                            recursive=False )
    observer2.schedule( file_event_handler( fname=STATE_PATH,
                                            action='state_file_changed',
                                            antibound=True ),
                                            path=LOG_DIR,
                                            recursive=False )
    observer1.start()
    observer2.start()

    print( f'(remote_volume) Balancing LU_offset on remotes ...' )
    all_remotes_LU_offset(force=True)

    print( f'(remote_volume) Forwarding relative level changes to remotes ...' )

    # A server that listen for new remote listening clients to emerge
    print( f'(remote_volume) Keep listening for new remotes ...' )
    server.SERVICE = 'remote_volume_daemon'
    server.MODULE = __import__(__name__)
    server.run_server( '0.0.0.0', miscel.CONFIG['peaudiosys_port'] + 5,
                       verbose=True)
