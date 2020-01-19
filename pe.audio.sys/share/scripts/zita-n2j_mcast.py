#!/usr/bin/env python3

"""
    A LAN multicast audio receiver, from Fons Adriaensen's zita-njbridge.

    See man zita-njbridge:

        ... similar  to  having analog audio connections between the
        sound cards of the systems using it

    usage:    zita-n2j_mcast.py   start | stop
"""
import sys
import subprocess as sp
from os import uname

# Additional buffering (ms) (default 10, safe value 50, WiFi 100)
BUFFER = 50

def get_default_interface():
    # Getting the machine's used interface name
    interface = ''
    # Linux
    if uname()[0] == 'Linux':
        tmp = sp.check_output('ip route'.split()).decode()
        # Example $ ip route
        # default via 192.168.1.1 dev eth0 proto dhcp src 192.168.1.36 metric 202
        for line in tmp.split('\n'):
            if 'default' in line:
                interface = line.split()[4]
    # Mac OS
    elif uname()[0] == 'Darwin':
        tmp = sp.check_output( 'route get 10.10.10.10'.split() ).decode()
        for line in tmp.split('\n'):
            if 'interface:' in line:
                interface = line.split(':')[-1].strip()
    return interface

def start():
    interface = get_default_interface()
    if not interface:
        print( 'init/zita-n2j_mcast: cannot get your network interface name :-/' )
        return False
    else:
        print( f'(zita-n2j_mcast) listening on {interface}' )

    # Using a no reserved multicast address 224.0.0.151 and port 65151
    # https://www.iana.org/assignments/multicast-addresses/multicast-addresses.xhtml#multicast-addresses-1
    sp.Popen( f'zita-n2j --buff {str(int(BUFFER))} 224.0.0.151 65151 {interface}'.split() )

def stop():
    sp.Popen( 'pkill -KILL zita-n2j'.split() )

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
