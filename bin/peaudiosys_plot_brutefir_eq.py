#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Plot the run-time EQ in a Brutefir running process

    (Brutefir needs to be running)
"""
import socket
import numpy as np
from matplotlib import pyplot as plt

############ Y AXIS AUTO ADJUST #################
ypos_step   = 15     # try 15 dB, or 0 to disable
yneg_step   = 10     # try 10 dB, or 0 to disable


def bfcli(cmds=''):
    """ send commands to brutefir CLI and receive its responses
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 3000))

    s.send( f'{cmds};quit\n'.encode() )

    response = b''
    while True:
        received = s.recv(4096)
        if received:
            response = response + received
        else:
            break
    s.close()
    #print(response) # debug
    return response.decode()

def read_eq():
    tmp = bfcli( 'lmc eq "c.eq" info' )
    tmp = [x for x in tmp.split('\n') if x][2:]
    bands = tmp[0]
    mag   = tmp[1].replace('-', ' -')
    pha   = tmp[2].replace('-', ' -') # some big negative values comes glued

    bands = bands.split()[1:]
    mag   = mag.split()[1:]
    pha   = pha.split()[1:]

    bands = np.array( [float(x) for x in bands] )
    mag   = np.array( [float(x) for x in mag]   )
    pha   = np.array( [float(x) for x in pha]   )

    return bands, mag, pha

if __name__ == '__main__':

    try:
        bands, mag, pha = read_eq()
    except:
        print(__doc__)
        exit()

    # Prepare the plot
    fig = plt.figure()
    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = fig.add_subplot(2, 1, 2)
    fig.subplots_adjust(hspace=.4)

    if yneg_step:
        ymin = -yneg_step - yneg_step * (np.min(mag) // -yneg_step)
    else:
        ymin = -6
    if ypos_step:
        ymax =  ypos_step + ypos_step * (np.max(mag) //  ypos_step)
    else:
        ymax = +12
    ax1.set_ylim( ymin, ymax)

    ax1.semilogx ( bands, mag )
    ax1.set_title( 'magnitude' )

    ax2.semilogx ( bands, pha )
    ax2.set_title( 'phase' )

    plt.show()
