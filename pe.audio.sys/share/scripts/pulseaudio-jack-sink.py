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
    Loads the pulseaudio sink, in order to
    Pulseaudio apps to default sound through by JACK.

    usage:  pulseaudio-jack-sink.py   start|stop

    NEEDED PACKAGE: pulseaudio-module-jack
"""

import sys
from subprocess import Popen
from time import sleep


def start():
    tmp = "pactl load-module module-jack-sink channels=2 " + \
          "client_name=pulse_sink connect=False"
    Popen( tmp.split() )
    sleep(.2)
    tmp = "pacmd set-default-sink jack_out"
    Popen( tmp.split() )


def stop():
    tmp = "pactl unload-module module-jack-sink"
    Popen( tmp.split() )


if sys.argv[1:]:

    if sys.argv[1] in ['stop', 'unload']:
        stop()
    elif sys.argv[1] in ['start', 'load']:
        start()
    else:
        print(__doc__)
        sys.exit()
