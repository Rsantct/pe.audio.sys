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
    start or stop the IR receiver

    Usage:  ir.py   start|stop

"""
import sys
import os
import subprocess as sp

UHOME    = os.path.expanduser("~")
THISPATH = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':

    if sys.argv[1:]:
        if sys.argv[1] in ['stop', 'off']:
            sp.Popen( 'pkill -f "ir.py"', shell=True )
        elif sys.argv[1] in ['start', 'on']:
            sp.Popen( f'python3 {THISPATH}/ir/ir.py'.split() )
        else:
            print(__doc__)
    else:
        print(__doc__)
