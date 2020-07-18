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

""" Controls the preamp (inputs, level, tones and convolver)
    This module is loaded by 'server.py'
"""

import json
import yaml
from time import strftime
from preamp_mod.core import Preamp, Convolver
from os.path import expanduser, exists
from os import remove
UHOME   = expanduser("~")
CONFIG  = yaml.safe_load( open(f'{UHOME}/pe.audio.sys/config.yml', 'r') )

# Command log file
PREAMP_LOG_FILE = f'{UHOME}/pe.audio.sys/.preamp_cmd.log'
if exists(PREAMP_LOG_FILE):
    remove(PREAMP_LOG_FILE)

# INITIATE A PREAMP INSTANCE
preamp = Preamp()
if 'powersave' in CONFIG and CONFIG["powersave"] == True:
    preamp.powersave('on')
preamp.save_state()

# INITIATE A CONVOLVER INSTANCE (XO and DRC management)
convolver = Convolver()


# MAIN FUNCTION FOR COMMAND PROCESSING
def process_commands( full_command ):
    """ Processes commands for audio control
        - input:  the command phrase.
        - output: 'done'             for OK command execution
                  'a warning phrase' for NOK command execution
    """

    def analize_full_command(full_cmd):
        """ returns a tuple ( <command>, <arg>, <add:True|False> )
        """
        # The full_command sintax:  <command> [arg [add] ]
        # 'arg' is given only with some commands
        # 'add' is given as an option for relative values ordering

        command, arg, add = '', '', False

        cmd_list = full_cmd.replace('\r', '').replace('\n', '').split()

        if not cmd_list[0:]:
            return ('', '', False)

        command = cmd_list[0]
        if cmd_list[1:]:
            arg = cmd_list[1]
            if cmd_list[2:]:
                if cmd_list[2] == 'add':
                    add = True
                else:
                    return ('', '', False)

        return (command, arg, add)

    # (i) Below we use *dummy to accommodate the parser mechanism wich
    # will include two arguments for any call here, even when not necessary.

    # 'mono' is a former command, here it is redirected to 'midside'
    def set_mono(x, *dummy):
        try:
            x = { 'on':     'mid',
                  'off':    'off',
                  'toggle': { 'off':'mid', 'side':'off', 'mid':'off'
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
        with open( f'{UHOME}/pe.audio.sys/doc/peaudiosys.hlp', 'r') as f:
            print(f.read())

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
            'polarity':         preamp.set_polarity,
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
            'set_xo':           set_xo,
            'xo':               set_xo,

            'convolver':        preamp.switch_convolver,
            'powersave':        preamp.powersave,

            'help':             print_help

            } [ command ] ( arg, add )

    except KeyError:
        result = f'(preamp) unknown command: {command}'

    except:
        result = f'(preamp) problems processing command: {command}'

    return result


# INTERFACE FUNCTION TO PLUG THIS MODULE ON SERVER.PY
# AND ** KEEPING UP TO DATE THE STATE FILE **
def do( cmdline ):

    result = process_commands( cmdline )

    if type(result) != str:
        result = json.dumps(result)

    if result:
        preamp.save_state()

    # Command log
    if cmdline not in ('state', 'status', 'get_state'):
        with open(PREAMP_LOG_FILE, 'a') as f:
            f.write(f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmdline}; {result}\n')

    return result
