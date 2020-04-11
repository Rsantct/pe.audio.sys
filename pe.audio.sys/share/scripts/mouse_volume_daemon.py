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
    Runs a daemon that manages the pe.audio.sys volume
    trough by a mouse.
"""
import sys
import os
from subprocess import Popen

THISDIR =  os.path.dirname( os.path.realpath(__file__) )


def start():
    Popen( f'{THISDIR}/mouse_volume_daemon/mouse_volume_daemon.py',
              shell=True )


def stop():
    # arakiri
    Popen( 'pkill -KILL -f mouse_volume_daemon.py'.split() )


if __name__ == "__main__":

    if sys.argv[1:]:
        if sys.argv[1] == 'stop':
            stop()
        elif sys.argv[1] == 'start':
            start()
        else:
            print(__doc__)
    else:
        print(__doc__)
