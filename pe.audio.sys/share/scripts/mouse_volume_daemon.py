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
    v0.5beta
    Script to manage pe.audio.sys volume through by a mouse.

    Use:
            mouse_volume_daemon.py [-sNN -bHH] &

                -sNN volume step NN dBs (default 2.0 dB)
                -bLL beeps if level exceeds LL dB (default -6.0 dB)
                -h   this help

                left button   -->  vol --
                right button  -->  vol ++
                mid button    -->  togles mute

    - Access permissions -

    The user must belong to the system group wich
    can access to devices under '/dev/input' folder. This group is defined
    inside '/etc/udev/rules.d/99-input.rules', also can be seen this way:

    $ ls -l /dev/input/
    total 0
    crw-rw---- 1 root input 13, 64 Mar 19 20:53 event0
    crw-rw---- 1 root input 13, 63 Mar 19 20:53 mice
    crw-rw---- 1 root input 13, 32 Mar 19 20:53 mouse0

    On the above example it can be seen that the group is 'input'

"""
# v0.2beta: beeps by running the synth from SoX (play)
# v0.3beta: beeps by running 'aplay beep.wav'
# v0.4beta: adapted from FIRtro to pre.di.c (python3 and writen as a module)
# v0.5beta: adapted from pre.di.c to pe.audio.sys

import os
import sys
import socket
import time
import subprocess as sp
import binascii
import yaml
#import struct # only to debug see below

UHOME   =  os.path.expanduser("~")
THISDIR =  os.path.dirname( os.path.realpath(__file__) )

try:
    with open(f'{UHOME}/pe.audio.sys/config.yml', 'r') as f:
        cfg = yaml.safe_load(f)
    CONTROL_PORT = cfg['peaudiosys_port']
except KeyError:
    print(f'(mouse_volume_daemon) ERROR reading control port in config.yml')
    exit()

####################### USER SETTINGS: #################################
STEPdB      = 2.0
alertdB     = -6.0
beep        = False
beepPath    = f'{THISDIR}/mouse_volume_3beeps.wav'
alsaplugin  = 'brutefir'
# NOTE: the above needs to you to configure your .asondrc
#       to have a jack plugin that connects to brutefir
########################################################################


def send_cmd(cmd, port=CONTROL_PORT):
    host = 'localhost'
    #print( f'(mouse_volume) sending: {cmd} to {host}:{port}')  # DEBUG
    with socket.socket() as s:
        try:
            s.connect( (host, port) )
            s.send( cmd.encode() )
            s.close()
        except:
            print( f'(mouse_volume) socket error on {host}:{port}' )
    return


def get_mouse_handlers():
    """ try to find your system's mouse handler
    """

    with open('/proc/bus/input/devices', 'r') as f:
        lines = f.read().split('\n')

    handlers = []
    found = False
    for line in lines:
        if 'N: Name=' in line:
            if 'mouse' in line.lower():
                found = True
        if found:
            if 'H: Handlers=' in line:
                handlers = line.split('=')[-1].split()
                break
    found = False
    if not handlers:
        for line in lines:
            if 'mouse' in line.lower():
                found = True
            if found:
                if 'H: Handlers=' in line:
                    handlers = line.split('=')[-1].split()
                    break

    return handlers


def getMouseEvent():
    """
    /dev/input/mouseX is a stream of 3 bytes: [Button_value] [XX_value] [YY_value]

    You would get a 4 byte stream if the mouse is configured with the scroll wheel (intellimouse)

    /dev/input/mice emulates a PS/2 mouse in three-byte mode.

        0x09XXYY --> buttonLeftDown
        0x0aXXYY --> buttonRightDown
        0x0cXXYY --> buttonMid

    To see the correspondence of files /dev/input/xxxx do:

        $ cat /proc/bus/input/devices
        I: Bus=0003 Vendor=046d Product=c03d Version=0110
        N: Name="Logitech USB-PS/2 Optical Mouse"
        P: Phys=usb-3f980000.usb-1.2/input0
        S: Sysfs=/devices/platform/soc/3f980000.usb/usb1/1-1/1-1.2/1-1.2:1.0/0003:046D:C03D.0001/input/input0
        U: Uniq=
        H: Handlers=mouse0 event0
        B: PROP=0
        B: EV=17
        B: KEY=70000 0 0 0 0 0 0 0 0
        B: REL=103
        B: MSC=10
    """
    #  as per seen at /proc/bus/input/devices
    mousedevice = get_mouse_handlers()[0]
    try:
        fmice = open( f'/dev/input/{mousedevice}', 'rb' )
    except:
        print(__doc__)
        print( '\nCheck your access permissions as above.' )
        exit()

    buff = fmice.read(3)
    m = binascii.hexlify(buff).decode()
    #print m, struct.unpack('3b', buff)  # Unpacks the bytes to integers
    if   m[:2] == "09":
        return "buttonLeftDown"
    elif m[:2] == "0a":
        return "buttonRightDown"
    elif m[:2] == "0c":
        return "buttonMid"
    fmice.close()


def check_level():
    # To avoid reading issues while state.yml is written
    i = 0
    while i < 20:
        f = open( f'{UHOME}/pe.audio.sys/.state.yml', 'r')
        conte = f.read()
        f.close()
        try:
            level = conte.split('level:')[1].split()[0]
            return float(level)
        except:
            pass
        i += 1
        time.sleep(.2)
    return 0.0


def beeps():
    # The synth on Sox is too slow :-/
    #sp.Popen( 'play --null synth 1 sine 880 gain -10.0 > /dev/null 2>&1' )
    # then will use aplay
    sp.Popen( ['aplay', f'-D{alsaplugin}', beepPath],
              stdout=sp.DEVNULL, stderr=sp.DEVNULL )


def main_loop(alertdB=alertdB, beep=beep):

    level_ups = False
    beeped =    False

    while True:

        # Reading the mouse
        ev = getMouseEvent()

        # Sending the order to pe.audio.sys
        if ev == 'buttonLeftDown':
            # Level --
            send_cmd( f'level -{STEPdB} add' )
            level_ups = False

        elif ev == 'buttonRightDown':
            # Level ++
            send_cmd( f'level +{STEPdB} add' )
            level_ups = True

        elif ev == 'buttonMid':
            # Mute toggle
            send_cmd( 'mute toggle' )

        # Alert if crossed the headroom threshold
        if level_ups:
            level = check_level()
            if ( level + STEPdB )  >= alertdB:
                if not beeped and beep:
                    print('(mouse_volume_daemon.py) BEEEEEEP, BEEEEEP')
                    beeps()
                    beeped = True
            else:
                beeped = False


def stop():
    # arakiri
    sp.Popen( 'pkill -KILL -f mouse_volume_daemon.py'.split() )


if __name__ == "__main__":

    if sys.argv[1:]:
        if sys.argv[1] == 'stop':
            stop()
        elif sys.argv[1] == 'start':
            main_loop()
        else:
            print(__doc__)
    else:
        print(__doc__)
