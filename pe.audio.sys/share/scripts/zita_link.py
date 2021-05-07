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
    A LAN audio receiver based on zita-njbridge from Fons Adriaensen.

    See man zita-njbridge:

        ... similar  to  having analog audio connections between the
        sound cards of the systems using it

    Usage:    zita_link.py   start | stop


    NOTICE:

    This script replaces the former 'zita-xxx_mcast.py' versions.

    It runs just from the receiver side. The sender side zita-j2n process
    will be automagically triggered on demand from here.

    For easy usage, please customize the provided macros/examples/XX_RemoteSource

    Further info at doc/80_Remote_pe.audio.sys.md

"""
from subprocess import Popen
from time import sleep
import sys
import os
UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share')
from miscel import is_IP, get_my_ip, CONFIG, send_cmd


# Additional buffering (ms) (default 10, safe value 50, WiFi 100)
BUFFER = 50


def start():

    # RUN REMOTE SENDER:
    remotecmd   = f'aux zita_client {my_ip} start'
    send_cmd(remotecmd, host=remote_addr, port=remote_port)

    # RUN LOCAL RECEIVER:
    zitacmd = f'zita-n2j --jname {remote_addr} --buff {BUFFER} {my_ip} {zitaport}'
    Popen( zitacmd.split() )
    print( f'(zita-n2j) listening for {my_ip}:{zitaport}:UDP from {source} @ {remote_addr}' )


def stop():

    # REMOTE
    remotecmd   = f'aux zita_client {my_ip} stop'
    send_cmd(remotecmd, host=remote_addr, port=remote_port)

    # LOCAL
    Popen( 'pkill -KILL zita-n2j'.split() )
    sleep(1)


def get_remote():
    # Retrieving the remote sender address from 'config.yml'.
    # For a 'remote.....' named source, it is expected to have
    # an IP address kind of in its capture_port field:
    #   capture_port:  X.X.X.X
    # so this way we can query the remote sender to run 'zita-j2n'

    remote_addr = ''
    remote_port = 9990

    for source in CONFIG["sources"]:
        if 'remote' in source:
            cport = CONFIG["sources"][source]["capture_port"]
            if is_IP(cport):
                remote_addr = cport
                break

    if not remote_addr:
        print(f'(zita-n2j) Cannot get remote address from configured sources')
        sys.exit()
    if not is_IP(remote_addr):
        print(f'(zita-n2j) source: \'{source}\' address: \'{remote_addr}\' not valid')
        sys.exit()

    return source, remote_addr, remote_port


if __name__ == '__main__':

    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()

    source, remote_addr, remote_port = get_remote()

    # The zita UDP port is derived from the last octet of my IP
    my_ip       = get_my_ip()
    zitaport    = f'65{my_ip.split(".")[-1]}'

    # Reading command line: start | stop
    if sys.argv[1] == 'start':
        stop()
        start()
    elif sys.argv[1] == 'stop':
        stop()
    else:
        print(__doc__)
