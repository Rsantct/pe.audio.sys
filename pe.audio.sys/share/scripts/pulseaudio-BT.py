#!/usr/bin/env python3

# Copyright (c) 2020 Rafael Sánchez
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
    Enables Pulseaudio to get sound from paired BT devices.

    usage:  pulseaudio-BT.py   start|stop

    (i) Needs Pulseaudio BT module (install it if necesssary)

            pulseaudio-module-bluetooth

"""
from subprocess import Popen
import sys

PAmodules = ['module-bluetooth-discover', 'module-bluetooth-policy']


def start():
    # Enable PA BT modules
    for m in PAmodules:
        Popen( f'pactl load-module {m}'.split() )


def stop():
    for m in modules:
        Popen( f'pactl unload-module {m}'.split() )


if __name__ == '__main__':

    enable_bt_devices()

    if sys.argv[1:]:
        if sys.argv[1] == 'stop':
            stop()
        elif sys.argv[1] == 'start':
            start()
        else:
            print(__doc__)
            sys.exit()
