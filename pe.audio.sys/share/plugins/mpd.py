#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A simple user session MPD launcher

    usage:  mpd.py   start | stop

    Notice:

        Some Desktop autostarts MPD when user logins, because of the packaged file:
            /etc/xdg/autostart/mpd.desktop
        If so, please set "X-GNOME-Autostart-enabled=false" inside this file.

"""
import sys
import os
from subprocess import Popen, call, check_output
from time import sleep
from getpass import getuser

UHOME = os.path.expanduser("~")


def check_systemd_service():
    """ Some mpd packages enables MPD user systemd units, when upgraded
    """
    try:
        # Any --value xxxx, even if non existent, will return "inactive"
        tmp = check_output("systemctl --user show -p ActiveState --value mpd.service",
                            shell=True).decode().strip()
    except Exception as e:
        tmp = ''
        print('(mpd.py)', e)

    if tmp == 'active':
        print('(mpd.py)', 'disabling systemd MPD service')
        tmp =  "systemctl --user stop mpd.socket &&"
        tmp += "systemctl --user stop mpd.service &&"
        tmp += "systemctl --user disable mpd.socket &&"
        tmp += "systemctl --user disable mpd.service"
        call( tmp, shell=True )


def stop():
    call( ['pkill', '-u', getuser() , '-KILL', '-f', f'mpd {UHOME}/.mpdconf'] )


def start():
    check_systemd_service()
    with open('/dev/null', 'w') as fnull:
        Popen( f'mpd {UHOME}/.mpdconf'.split(), stdout=fnull, stderr=fnull )


if __name__ == '__main__':

    if sys.argv[1:]:

        if sys.argv[1] == 'stop':
            stop()
        elif sys.argv[1] == 'start':
            stop()
            start()
        else:
            print(__doc__)

    else:
        print(__doc__)
