#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

# This is based on 'pre.di.c,' a preamp and digital crossover
# https://github.com/rripio/pre.di.c
# Copyright (C) 2018 Roberto Ripio
# 'pre.di.c' is based on 'FIRtro', a preamp and digital crossover
# https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
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

""" A module interface that runs miscellaneous local tasks.
"""

import yaml
import json
from subprocess import Popen, check_output
import os

UHOME = os.path.expanduser("~")
MAIN_FOLDER = f'{UHOME}/pe.audio.sys'
MACROS_FOLDER = f'{MAIN_FOLDER}/macros'
LOUD_MON_CTRL = f'{MAIN_FOLDER}/.loudness_control'
LOUD_MON_VAL  = f'{MAIN_FOLDER}/.loudness_monitor'

with open( f'{MAIN_FOLDER}/config.yml' , 'r' ) as f:
    CFG = yaml.load( f )
try:
    AMP_MANAGER =  CFG['aux']['amp_manager']
except:
    # This will be printed out to the terminal to advice the user:
    AMP_MANAGER =  'echo For amp switching please configure config.yml'

try:
    with open( f'{MAIN_FOLDER}/web.yml' , 'r' ) as f:
        WEBCONFIG = yaml.load( f )
except:
        WEBCONFIG = { 'at_startup':{'hide_macro_buttons':False} }


def read_command_phrase(command_phrase):
    cmd, arg = None, None
    # This is to avoid empty values when there are more
    # than on space as delimiter inside the command_phrase:
    opcs = [x for x in command_phrase.split(' ') if x]
    try:
        cmd = opcs[0]
    except:
        raise
    try:
        # allows spaces inside the arg part, e.g. 'run_macro 2_Radio Clasica'
        arg = ' '.join( opcs[1:] )
    except:
        pass
    return cmd, arg

# Interface function to plug this on server.py
def do( command_phrase ):
    cmd, arg = read_command_phrase( command_phrase
                                              .replace('\n','').replace('\r','') )
    result = process( cmd, arg )
    return json.dumps(result).encode()

# Main function for command processing
def process( cmd, arg ):
    """ input:  a tuple (command, arg)
        output: a result string
    """

    result = ''

    # Amplifier switching
    if cmd == 'amp_switch':
        if arg in ('on','off'):
            print( f'(aux) {AMP_MANAGER.split("/")[-1]} {arg}' )
            Popen( f'{AMP_MANAGER} {arg}'.split(), shell=False )
        elif arg == 'state':
            try:
                with open( f'{UHOME}/.amplifier', 'r') as f:
                    tmp =  f.read().strip()
                if tmp.lower() in ('0','off'):
                    result = 'off'
                elif tmp.lower() in ('1','on'):
                    result = 'on'
            except:
                pass

    # List of macros under macros/ folder
    elif cmd == 'get_macros':
        macro_files = []
        with os.scandir( f'{MACROS_FOLDER}' ) as entries:
            for entrie in entries:
                fname = entrie.name
                if ( fname[0] in [str(x) for x in range(1,10)] ) and fname[1]=='_':
                    macro_files.append(fname)
        result = macro_files

    # Run a macro
    elif cmd == 'run_macro':
        print( f'(aux) running macro: {arg}' )
        Popen( f'"{MACROS_FOLDER}/{arg}"', shell=True)
        result = 'tried'

    # Send reset to the loudness monitor daemon through by its control file
    elif cmd == 'loudness_monitor_reset':
        try:
            with open(LOUD_MON_CTRL, 'w') as f:
                f.write('reset')
            result = 'done'
        except:
            result = 'error'

    # Get the loudness monitor value from the loudness monitor daemon's output file
    elif cmd == 'get_loudness_monitor':
        try:
            with open(LOUD_MON_VAL, 'r') as f:
                result = round( float(f.read().strip()), 1)
        except:
            result = ''

    # RESTART
    elif cmd == 'restart':
        try:
            restart_action = WEBCONFIG["reboot_button_action"]
        except:
            restart_action = 'peaudiosys_restart.sh'

        try:
            Popen( f'{restart_action}'.split() )
        except:
            print( f'(aux) Problems running \'{restart_action}\'' )

    # Get the web.config dictionary
    elif cmd == 'get_web_config':
        result = WEBCONFIG

    # Help
    elif '-h' in cmd:
        print(__doc__)
        result =  'done'

    return result


# command line use
if __name__ == '__main__':

    if sys.argv[1:]:

        command_phrase = ' '.join (sys.argv[1:] )
        cmd, arg = read_command_phrase( command_phrase )
        result = process( cmd, arg )
        print( result )


