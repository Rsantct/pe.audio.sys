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

""" Inserts a parametric EQ based on 'fil' plugin (LADSPA) hosted under Ecasound
    'fil' plugin is a 4-band parametric eq from Fons Adriaensen, more info:
    http://kokkinizita.linuxaudio.org/
    
        options:  start | stop
"""
import subprocess as sp
import os, sys
from time import sleep
UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'

#########   YOUR CONFIG:   ############
LSPKFOLDER  = f'{MAINFOLDER}/loudspeakers/dipojorns'
ECSFILE     = 'dj_estant.ecs'
#########################################

def init_ecasound():

    # Info
    print( f'(ecasound_peq_dipojorns) Loading: \'{ECSFILE}\'' )
    
    # Launching ecasound
    ecsCmd = f'-q --server -s:{LSPKFOLDER}/{ECSFILE}'
    sp.Popen( f'ecasound {ecsCmd}'.split() )
    sleep(3)
    
    # Inserting:
    with open('/dev/null', 'w') as fnull:
        sp.Popen( 'jack_disconnect pre_in_loop:output_1 brutefir:in.L'.split(),
                    stdout=fnull, stderr=fnull )
        sp.Popen( 'jack_disconnect pre_in_loop:output_2 brutefir:in.R'.split(),
                    stdout=fnull, stderr=fnull )
        sp.Popen( 'jack_connect    pre_in_loop:output_1 ecasound:in_1'.split(),
                    stdout=fnull, stderr=fnull )
        sp.Popen( 'jack_connect    pre_in_loop:output_2 ecasound:in_2'.split(),
                    stdout=fnull, stderr=fnull )
        sp.Popen( 'jack_connect    ecasound:out_1       brutefir:in.L'.split(),
                    stdout=fnull, stderr=fnull )
        sp.Popen( 'jack_connect    ecasound:out_2       brutefir:in.R'.split(),
                    stdout=fnull, stderr=fnull )


def stop():
    sp.Popen( f'pkill -f {ECSFILE}'.split() )
    sleep(1)
    # Restoring:
    with open('/dev/null', 'w') as fnull:
        sp.Popen( 'jack_connect pre_in_loop:output_1 brutefir:in.L'.split(),
                    stdout=fnull, stderr=fnull )
        sp.Popen( 'jack_connect pre_in_loop:output_2 brutefir:in.R'.split(),
                    stdout=fnull, stderr=fnull )

if __name__ == '__main__':

    if sys.argv[1:]:
        option = sys.argv[1]
        if option == 'start':
            init_ecasound()
        elif option == 'stop':
            stop()
        else:
            print(__doc__)
    else:
        print(__doc__)
