#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    v0.5beta
    Plugin to manage pe.audio.sys volume through by a mouse.

    Use:
            mouse_volume_daemon.py [-sNN -bHH] &

                -sNN volume step NN dBs (default 2.0 dB)
                -bLL beeps if level exceeds LL dB (default -6.0 dB)
                -h   this help

                left button   -->  vol --
                right button  -->  vol ++
                mid button    -->  togles mute

    - Access permissions -

    The user must belong to the system group wich can access to devices under
    '/dev/input' folder.

    This group is defined inside '/etc/udev/rules.d/99-input.rules',
    it can be seen also this way:

    $ ls -l /dev/input/
    total 0
    crw-rw---- 1 root input 13, 64 Mar 19 20:53 event0
    crw-rw---- 1 root input 13, 63 Mar 19 20:53 mice
    crw-rw---- 1 root input 13, 32 Mar 19 20:53 mouse0

    On the above example it can be seen that the group is 'input'

"""
# v0.2beta: beeps by running the synth from SoX (play)
# v0.3beta: beeps by running 'aplay beep.wav'
# v0.4beta: python3 and writen as a module
# v0.5beta: /proc/input/devices is an empty file, now using /dev/input/mice
#           because it is always available
#           (https://www.kernel.org/doc/html/latest/input/input.html#mousedev)

import subprocess as sp
import binascii
import yaml
import sys
import os
#import struct # only to debug see below

UHOME   =  os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from miscel import send_cmd, read_state_from_disk, USER

THISDIR =  os.path.dirname( os.path.realpath(__file__) )
try:
    with open(f'{THISDIR}/mouse_volume_daemon.yml', 'r') as f:
        CFG = yaml.safe_load(f)
except:
    CFG = { 'mousedevice':  'mice',
            'STEPdB':        3.0,
            'alertdB':      -6.0,
            # (i) Beta: for beep sound you need to configure your
            # .asondrc to have a jack plugin that connects to brutefir
            'beep':         False,
            'alsaplugin':   'brutefir' }
    print(f'(mouse_volume_daemon) yaml config failed, using:\n{CFG}')


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
    try:
        fmice = open( f'/dev/input/{CFG["mousedevice"]}', 'rb' )
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


def beeps():
    # (i) It is PENDING to pythonise this stuff ;-)

    # The synth on Sox is too slow :-/
    #sp.Popen( 'play --null synth 1 sine 880 gain -10.0 > /dev/null 2>&1' )

    # then will use aplay
    beepPath    = f'{THISDIR}/mouse_volume_daemon/3beeps.wav'
    sp.Popen( ['aplay', f'-D{CFG["alsaplugin"]}', beepPath],
              stdout=sp.DEVNULL, stderr=sp.DEVNULL )


def main_loop(alertdB=CFG['alertdB'], beep=CFG['beep']):

    level_ups = False
    beeped =    False

    while True:

        # Reading the mouse
        ev = getMouseEvent()

        # Sending the order to pe.audio.sys
        if ev == 'buttonLeftDown':
            # Level --
            send_cmd( f'level -{CFG["STEPdB"]} add', sender='mouse_volume',
                      verbose=True )
            level_ups = False

        elif ev == 'buttonRightDown':
            # Level ++
            send_cmd( f'level +{CFG["STEPdB"]} add', sender='mouse_volume',
                      verbose=True )
            level_ups = True

        elif ev == 'buttonMid':
            # Mute toggle
            send_cmd( 'mute toggle', sender='mouse_volume', verbose=True )

        # Alert if crossed the headroom threshold
        if level_ups:
            level = read_state_from_disk()['level']
            if ( level + CFG['STEPdB'] )  >= alertdB:
                if not beeped and beep:
                    print('(mouse_volume_daemon) BEEEEEEP, BEEEEEP')
                    beeps()
                    beeped = True
            else:
                beeped = False


def stop():
    # arakiri
    sp.Popen( f'pkill -u {USER} -KILL -f mouse_volume_daemon.py', shell=True )


if __name__ == "__main__":
    main_loop()
