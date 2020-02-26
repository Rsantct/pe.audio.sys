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
    Inserts a parametric EQ based on 'fil' plugin (LADSPA) hosted under Ecasound.
    'fil' plugin is an excellent 4-band parametric eq from Fons Adriaensen,
    for more info see:
        http://kokkinizita.linuxaudio.org/
    
    Options:  start | stop
        
    Notes:  You need to define the xxxxxx.ecs to load at the belonging
            script line under config.yml, e.g:

            -scripts
                - ecasound_peq.py: xxxxxx.ecs
                ...
                ...
                
            The xxxxxx.ecs file must be available under the 'share/eq' folder.
"""
import subprocess as sp
import os, sys
from time import sleep
import yaml

UHOME       = os.path.expanduser("~")
EQFOLDER    = f'{UHOME}/pe.audio.sys/share/eq'

def init_ecasound():

    # Info
    print( f'(ecasound_peq_dipojorns) Loading: \'{ECSFILE}\'' )
    
    # Launching ecasound
    ecsCmd = f'-q --server -s:{EQFOLDER}/{ECSFILE}'
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
    
    try:
        with open( f'{UHOME}/pe.audio.sys/config.yml', 'r') as f:
            config = yaml.safe_load(f)
            scripts_lists = config['scripts']
            for script in scripts_lists:
                if type(script) == dict:
                    if 'ecasound_peq.py' in script.keys():
                        ECSFILE = script['ecasound_peq.py']
                        break
    except:
        print(  f'(ecasound_peq) unable to read your .ecs file from config.yml' )
        sys.exit()
    
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
