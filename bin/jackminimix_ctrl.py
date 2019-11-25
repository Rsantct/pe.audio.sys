#!/usr/bin/env python3
"""
    Controls jackminimix through by OSC protocol
"""
import argparse
from socket import gethostname
from subprocess import check_output

# https://pypi.org/project/python-osc
from pythonosc.udp_client import SimpleUDPClient

def get_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('--addr', type=str, default=gethostname(),
        help='The address of the OSC server')

    parser.add_argument('-g1', type=float, default=None,
        help='channel 1 gain')

    parser.add_argument('-g2', type=float, default=None,
        help='channel 2 gain')

    parser.add_argument('-g3', type=float, default=None,
        help='channel 3 gain')

    return parser.parse_args()

def get_port():
    try:
        lines = check_output( 'pgrep -fa jackminimix'.split() ).decode()
        for line in lines.split('\n'):
            if '-p' in line and '-c' in line and not 'python' in line:
                port = int( line.split('-p')[1].strip().split()[0] )
    except:
        print('jackminimix process not found')
        exit()
    return port
    
if __name__ == '__main__':

    args = get_args()
    
    client = SimpleUDPClient( args.addr, get_port() )
        
    if args.g1 != None:
        client.send_message('/mixer/channel/set_gain', [1, args.g1] )
    if args.g2 != None:
        client.send_message('/mixer/channel/set_gain', [2, args.g2] )
    if args.g3 != None:
        client.send_message('/mixer/channel/set_gain', [3, args.g3] )
        
