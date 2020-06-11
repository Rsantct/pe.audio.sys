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
    """ Getting the machine's interface name with best metric """
    interfaces = []

    # Linux 'ip route'
    #   default via 192.168.1.1 dev eth0 src 192.168.1.236 metric 202
    #   default via 192.168.1.1 dev wlan0 proto dhcp src 192.168.1.38 metric 303
    if uname()[0] == 'Linux':
        tmp = sp.check_output('ip route'.split()).decode()
        for line in tmp.split('\n'):
            if 'default' in line:
                iface = { 'name':   line.split()[4],
                          'metric': int(line.split()[-1]) }
                interfaces.append( iface )

    # Mac OS:   route get x.x.x.x will show the best metric interface, no matter
    #           if you have more than one interface alive.
    elif uname()[0] == 'Darwin':
        tmp = sp.check_output( 'route get 10.10.10.10'.split() ).decode()
        for line in tmp.split('\n'):
            if 'interface:' in line:
                iface = { 'name':   line.split(':')[-1].strip(),
                          'metric': 1 }
                interfaces.append( iface )

    # In Linux we can have more than one interface, lets get the best metric one
    iname = ''
    best_metric = 1e6
    for i in interfaces:
        if i["metric"] < best_metric:
            iname = i["name"]
            best_metric = i["metric"]

    return iname


def start():
    interface = get_default_interface()
    if not interface:
        print( 'init/zita-n2j_mcast: cannot get your network interface name :-/' )
        return False
    else:
        print( f'(zita-n2j_mcast) listening on {interface}' )

    # Using a no reserved multicast address 224.0.0.151 and port 65151
    # https://www.iana.org/assignments/multicast-addresses/multicast-addresses.xhtml#multicast-addresses-1
    tmp = f'zita-n2j --buff {str(int(BUFFER))} 224.0.0.151 65151 {interface}'
    sp.Popen( tmp.split() )


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
