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

    Further info at doc/80_Multiroom_pe.audio.sys.md

"""
from subprocess import Popen
from time import sleep
import sys
import os
UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share')
from miscel import is_IP, get_my_ip, send_cmd, get_remote_sources_info


# Additional buffering (ms) (default 10, safe value 50, WiFi 100)
BUFFER = 50


def start():

    for item in REMOTES:

        source, raddr, rport = item

        # RUN REMOTE SENDER:
        remotecmd   = f'aux zita_client {MY_IP} start'
        send_cmd(remotecmd, host=raddr, port=rport)

        # RUN LOCAL RECEIVER:
        zitacmd = f'zita-n2j --jname {raddr} --buff {BUFFER} {MY_IP} {MY_ZITAPORT}'
        Popen( zitacmd.split() )
        print( f'(zita-n2j) listening for {MY_IP}:{MY_ZITAPORT}:UDP from {source} @ {raddr}' )


def stop():

    for item in REMOTES:

        source, raddr, rport = item

        # REMOTE
        remotecmd   = f'aux zita_client {MY_IP} stop'
        send_cmd(remotecmd, host=raddr, port=rport)

        # LOCAL
        Popen( 'pkill -KILL zita-n2j'.split() )
        sleep(1)


if __name__ == '__main__':

    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()

    REMOTES = get_remote_sources_info()

    if not REMOTES:
        print(f'(zita_link) ERROR getting configured remote sources')
        sys.exit()

    # The zita UDP port is derived from the last octet of my IP
    MY_IP       = get_my_ip()
    MY_ZITAPORT = f'65{MY_IP.split(".")[-1]}'

    # Reading command line: start | stop
    if sys.argv[1] == 'start':
        stop()
        start()
    elif sys.argv[1] == 'stop':
        stop()
    else:
        print(__doc__)
