#!/usr/bin/env python3
"""
    A LAN audio receiver based on zita-njbridge from Fons Adriaensen.

    See man zita-njbridge:

        ... similar  to  having analog audio connections between the
        sound cards of the systems using it

    usage:    zita-n2j.py   start | stop


    (i)

    This script replaces the former 'zita-xxx_mcast.py' versions.

    It works just from the receiver side. The sender side zita-j2n process
    will be automagically triggered from here.

"""
import sys
from subprocess import Popen, check_output
from time import sleep
import yaml
import ipaddress
import os

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share')
from miscel import is_IP, get_my_ip


# (i)   zita-n2j does consume high CPU% while receiving because internal
#       resampling is used always.
#       If not synced with sender, CPU% will be zero.

# Additional buffering (ms) (default 10, safe value 50, WiFi 100)
BUFFER = 50


def start():

    # RUN REMOTE SENDER:
    remotecmd   = f'aux zita_client {my_ip} start'
    Popen( f'echo "{remotecmd}" | nc -N {remote_addr} 9990', shell=True)

    # RUN LOCAL RECEIVER:
    zitacmd = f'zita-n2j --jname {remote_addr} --buff {BUFFER} {my_ip} {zitaport}'
    Popen( zitacmd.split() )
    print( f'(zita-n2j) listening for {my_ip}:{zitaport}:UDP from {source} @ {remote_addr}' )


def stop():
    # REMOTE
    my_ip       = get_my_ip()
    remotecmd   = f'aux zita_client {my_ip} stop'
    Popen( f'echo "{remotecmd}" | nc -N {remote_addr} {remote_port}', shell=True)

    # LOCAL
    Popen( 'pkill -KILL zita-n2j'.split() )
    sleep(1)


if __name__ == '__main__':

    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()

    with open(f'{UHOME}/pe.audio.sys/config.yml', 'r') as f:
        CONFIG = yaml.safe_load(f.read())

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
