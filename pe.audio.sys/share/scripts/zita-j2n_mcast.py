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
    A LAN multicast audio sender, from Fons Adriaensen's zita-njbridge.

    See man zita-njbridge:

        ... similar  to  having analog audio connections between the
        sound cards of the systems using it

    usage:    zita-j2n_mcast.py   start | stop


    (!) NOTICE:

    2ch 44100Hz 16bit will use about ~ 1.7 Mb/s network bandwidth (UDP packets)

    *** Multicast UDP must be used in a dedicated wired Ethernet LAN ***

    If your LAN uses WiFi, please do not use this script, you can use
    the new script 'zita_link.py' instead, just in the receiver side, the
    sender side zita-j2n will be automagically triggered from the receiver.

"""
import sys
import subprocess as sp


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
    sp.Popen( 'pkill -KILL zita-j2n'.split() )


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
