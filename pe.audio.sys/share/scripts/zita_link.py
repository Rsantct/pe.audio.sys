#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

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
from    subprocess import Popen
from    time import sleep
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from miscel import get_my_ip, send_cmd, get_remote_sources_info, json_dumps


# Additional buffering (ms) (default 10, safe value 50, WiFi 100)
BUFFER = 50


def start():

    global PORT_BASE

    for item in REMOTES:

        _, raddr, rport = item

        # RUN REMOTE SENDER:
        zargs = json_dumps( (MY_IP, PORT_BASE, 'start') )
        remotecmd   = f'aux zita_j2n {zargs}'
        print(f'(zitalink) SENDING TO REMOTE: {remotecmd}')
        send_cmd(remotecmd, host=raddr, port=rport)

        # RUN LOCAL RECEIVER:
        zitajname  = f'zita-{ raddr.split(".")[-1] }'
        zitacmd = f'zita-n2j --jname {zitajname} --buff {BUFFER} {MY_IP} {PORT_BASE}'
        print(f'(zitalink) RUNNING LOCAL:     {zitacmd}')
        with open('/dev/null', 'w') as fnull:
            Popen( zitacmd.split(), stdout=fnull, stderr=fnull )

        # (i) zita will use 2 consecutive ports, so let's space by 10
        PORT_BASE += 10


def stop():

    for item in REMOTES:

        _, raddr, rport = item

        # REMOTE
        zargs = json_dumps( (MY_IP, None, 'stop') )
        remotecmd = f'aux zita_j2n {zargs}'
        send_cmd(remotecmd, host=raddr, port=rport)

        # LOCAL
        zitajname  = f'zita-{ raddr.split(".")[-1] }'
        killcmd = f'pkill -KILL -f {zitajname}'
        Popen( killcmd.split() )
        sleep(.1)


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
    PORT_BASE   = 65000

    # Reading command line: start | stop
    if sys.argv[1] == 'start':
        stop()
        start()
    elif sys.argv[1] == 'stop':
        stop()
    else:
        print(__doc__)
