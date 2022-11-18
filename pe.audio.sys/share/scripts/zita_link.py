#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A LAN audio connection based on zita-njbridge from Fons Adriaensen.

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
from    subprocess import Popen
from    time import sleep
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    miscel import *

# Additional buffering (ms) (default 10, safe value 50, WiFi 100)
BUFFER = 50


def start():

    global UDP_PORT
    zita_link_ports = {}

    for item in REMOTES:

        source_name, raddr, rport = item
        print( f'(zita_link.py) Running zita-njbridge for: {source_name}' )

        # Trying to RUN THE REMOTE SENDER zita-j2n (*)
        remote_zita_restart(raddr, rport, UDP_PORT)

        # Append the UPD_PORT to zita_link_ports
        zita_link_ports[source_name] = {'addr': raddr, 'udpport': UDP_PORT}

        # RUN LOCAL RECEIVER:
        local_zita_restart(raddr, UDP_PORT, BUFFER)

        # (i) zita will use 2 consecutive ports, so let's space by 10
        UDP_PORT += 10

    # (*) Saving the zita's UDP PORTS for future use because
    #     the remote sender could not be online at the moment ...
    with open(f'{MAINFOLDER}/.zita_link_ports', 'w') as f:
        d = json_dumps( zita_link_ports )
        f.write(d)


def stop():

    for item in REMOTES:

        _, raddr, rport = item

        # REMOTE
        zargs = json_dumps( (MY_IP, None, 'stop') )
        remotecmd = f'aux zita_j2n {zargs}'
        send_cmd(remotecmd, host=raddr, port=rport)

        # LOCAL
        zitajname  = f'zita_n2j_{ raddr.split(".")[-1] }'
        zitapattern  = f'zita-n2j --jname {zitajname}'
        Popen( ['pkill', '-KILL', '-f',  zitapattern] )
        sleep(.2)


if __name__ == '__main__':

    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()

    REMOTES = get_remote_sources()

    if not REMOTES:
        print(f'(zita_link) ERROR getting configured remote sources')
        sys.exit()

    # The zita UDP port is derived from the last octet of my IP
    MY_IP    = get_my_ip()
    UDP_PORT = 65000

    # Reading command line: start | stop
    if sys.argv[1] == 'start':
        stop()
        start()
    elif sys.argv[1] == 'stop':
        stop()
    else:
        print(__doc__)
