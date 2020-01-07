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


from core import Preamp, Convolver, save_yaml, STATE_PATH
import yaml
from os.path import expanduser
UHOME = expanduser("~")

# INITIATE A PREAMP INSTANCE
preamp = Preamp()

# INITIATE A CONVOLVER INSTANCE (XO and DRC management)
convolver = Convolver()

# INTERFACE FUNCTION TO PLUG THIS ON SERVER.PY
def do( cmdline ):
    result = process_commands( cmdline )
    save_yaml( preamp.state, STATE_PATH )
    # The server needs bytes-like (encoded) things
    return result.encode()

# Auxiliary function
def analize_full_command(full_command):
    """ returns a tuple ( <command>, <arg>, <add:True|False> )
    """

    command, arg, add = None, None, False

    # The full_command sintax:  <command> [arg [add] ]
    # 'arg' is given only with some commands
    # 'add' is given as an option for relative values ordering
    add = False
    cmd_list = full_command.replace('\r','').replace('\n','').split()

    if not cmd_list[0:]:
        return (None, None, False)

    command = cmd_list[0]
    if cmd_list[1:]:
        arg = cmd_list[1]
        if cmd_list[2:]:
            if cmd_list[2] == 'add':
                add = True
            else:
                return (None, None, False)

    return (command, arg, add)

# MAIN FUNCTION FOR COMMAND PROCESSING
def process_commands( full_command ):
    """ Processes commands for audio control
        - input:  the command phrase.
        - output: 'done'             for OK command execution
                  'a warning phrase' for NOK command execution
    """

    # Below we use *dummy to accommodate the pasysctrl.py parser mechanism wich
    # will include  two arguments for any call here, even when not necessary.

    # 'mono' is a former command, here it is redirected to 'midside'
    def set_mono(x, *dummy):
        try:
            x = {   'on':       'mid',
                    'off':      'off',
                    'toggle':   { 'off':'mid', 'side':'off', 'mid':'off'
                                } [ preamp.state['midside'] ]
                } [x]
            return preamp.set_midside(x)
        except:
            return 'bad option'

    # XO and DRC management uses the Convolver objet, so we also still need
    # to update Preamp.state in addition.
    def set_drc(x, *dummy):
        result = convolver.set_drc(x)
        if result == 'done':
            preamp.state['drc_set'] = x
        return result

    def set_xo(x, *dummy):
        result = convolver.set_xo(x)
        if result == 'done':
            preamp.state['xo_set'] = x
        return result

    def print_help(*dummy):
        with open( f'{UHOME}/pe.audio.sys/pasysctrl.hlp', 'r') as f:
            return f.read()

    # HERE BEGINS THE COMMAND PROCESSING:
    result  = 'nothing has been done'

    # Analize the full_command phrase or doing nothing.
    command, arg, add = analize_full_command(full_command)
    if not command:
        # Do nothing
        return result

    # Parsing the command to his related function
    try:
        result = {

            'state':            preamp.get_state,
            'status':           preamp.get_state,
            'get_state':        preamp.get_state,
            'get_inputs':       preamp.get_inputs,
            'get_eq':           preamp.get_eq,
            'get_target_sets':  preamp.get_target_sets,
            'get_drc_sets':     convolver.get_drc_sets,
            'get_xo_sets':      convolver.get_xo_sets,

            'input':            preamp.select_source,
            'source':           preamp.select_source,
            'solo':             preamp.set_solo,
            'mono':             set_mono,
            'midside':          preamp.set_midside,
            'mute':             preamp.set_mute,

            'level':            preamp.set_level,
            'balance':          preamp.set_balance,
            'treble':           preamp.set_treble,
            'bass':             preamp.set_bass,
            'loudness':         preamp.set_loud_track,
            'loudness_track':   preamp.set_loud_track,
            'loudness_ref':     preamp.set_loud_ref,
            'set_target':       preamp.set_target,

            'set_drc':          set_drc,
            'drc':              set_drc,
            'xo':               set_xo,
            'set_xo':           set_xo,

            'help':             print_help

            } [ command ] ( arg, add )

    except KeyError:
        result = f'unknown command: {command}'

    except:
        result = f'problems processing command: {command}'

    return result

