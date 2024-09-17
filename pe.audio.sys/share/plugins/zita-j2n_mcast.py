#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A LAN multicast audio sender, from Fons Adriaensen's zita-njbridge.

    See man zita-njbridge:

        ... similar  to  having analog audio connections between the
        sound cards of the systems using it

    usage:    zita-j2n_mcast.py   start | stop


    (!) NOTICE:

    2ch 44100Hz 16bit will use about ~ 1.7 Mb/s network bandwidth (UDP packets)

    *** Multicast UDP must be used in a dedicated wired Ethernet LAN ***

    (!) UPDATE:

    Currently pe.audio.sys integrates a point to point zita-njbridge system.
    Please see doc/Multiroom

"""
import sys
import subprocess as sp
from getpass import getuser


def start():

    # Getting the machine's used interface name
    interface = ''
    tmp = sp.check_output('ip route'.split()).decode()
    # Example $ ip route
    # default via 192.168.1.1 dev eth0 proto dhcp src 192.168.1.36 metric 202
    for line in tmp.split('\n'):
        if 'default' in line:
            interface = line.split()[4]
    if not interface:
        print('init/zita-j2n_mcast: cannot get your network interface name :-/')
        return False

    # Using a no reserved multicast address 224.0.0.151 and port 65151
    # https://www.iana.org/assignments/multicast-addresses/multicast-addresses.xhtml#multicast-addresses-1
    sp.Popen( f'zita-j2n --16bit --chan 2 224.0.0.151 65151 {interface}'.split() )


def stop():
    sp.Popen( f'pkill -u {getuser()} -KILL zita-j2n', shell=True )


if __name__ == '__main__':

    if sys.argv[1:]:
        option = sys.argv[1]
        if option == 'start':
            start()
        elif option == 'stop':
            stop()
        else:
            print(__doc__)
    else:
        print(__doc__)
