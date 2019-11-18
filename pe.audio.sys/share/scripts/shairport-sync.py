#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

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
    shairport-sync  Plays audio streamed from iTunes, 
                    iOS devices and third-party AirPlay sources

    use:    shairport-sync.py   start | stop
"""

import sys
from subprocess import Popen

def start():

    cmd = 'shairport-sync -a $(hostname) -o alsa -- -d aloop'
    Popen( cmd, shell=True )

def stop():
    Popen( ['pkill', '-KILL', '-f', 'shairport-sync -a'] )

if sys.argv[1:]:
    try:
        option = {
            'start' : start,
            'stop'  : stop
            }[ sys.argv[1] ]()
    except:
        print( '(scripts/shairport-sync) bad option' )
else:
    print(__doc__)
