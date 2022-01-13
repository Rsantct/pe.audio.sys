#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    usage:  mpd.py  start|stop
"""
import sys
import os
from subprocess import Popen
from time import sleep

UHOME = os.path.expanduser("~")


def stop():
    # Some mpd packages enables MPD user systemd units, when upgraded:
    tmp =  "systemctl --user stop mpd.socket &&"
    tmp += "systemctl --user stop mpd.service &&"
    tmp += "systemctl --user disable mpd.socket &&"
    tmp += "systemctl --user disable mpd.service"
    Popen( tmp, shell=True )
    Popen( ['pkill', '-KILL', 'mpd'] )
    sleep(.25)


def start():
    Popen( f'mpd {UHOME}/.mpdconf'.split() )


if __name__ == '__main__':

    if sys.argv[1:]:

        if sys.argv[1] == 'stop':
            stop()
        elif sys.argv[1] == 'start':
            # Some Desktop autostarts MPD when user logins, because of the packaged file:
            #   /etc/xdg/autostart/mpd.desktop
            # If so, please set "X-GNOME-Autostart-enabled=false" inside this file.
            stop()
            start()
        else:
            print(__doc__)

    else:
        print(__doc__)
