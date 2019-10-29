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
    
    # The full_command sintax:  <command> <arg> add
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
            # 
            else:
                return (None, None, False)

    return (command, arg, add)

# MAIN FUNCTION FOR COMMAND PROCESSING
def process_commands( full_command ):
    """ Processes commands for audio control
        - input:  the command phrase
        - output: execution result, informative warnings
    """

    # The actions to be done when a command is parsed below

    def set_solo(x):
        return preamp.set_solo(x)

    def set_mono(x):
        # the 'mono' command gracefully accepts to be toggled ;-)
        # 'mono' is a former command, currently it is delegated to 'midside'
        try:
            x = {   'on':       'mid', 
                    'off':      'off',
                    'toggle':   { 'off':'mid', 'side':'off', 'mid':'off'
                                } [ preamp.state['midside'] ]
                } [x]
            return set_midside(x)
        except:
            return 'bad option'

    def set_midside(x):
        return preamp.set_midside(x)

    def set_mute(x):
        return preamp.set_mute(x)

    def set_loud_track(x):
        return preamp.set_loud_track(x)

    def set_loud_ref(x):
        return preamp.set_loud_ref(x)

    def set_treble(x):
        return preamp.set_treble(x, relative=add)

    def set_bass(x):
        return preamp.set_bass(x, relative=add)

    def set_balance(x):
        return preamp.set_balance(x, relative=add)

    def set_level(x):
        return preamp.set_level(x, relative=add)

    def get_eq(dummyarg):
        return yaml.dump( preamp.get_eq(), default_flow_style=False )
    
    def get_state(dummyarg):
        return yaml.dump( preamp.state, default_flow_style=False )

    def set_source(x):
        return preamp.select_source(x)

    def get_drc_sets(dummyarg):
        return '\n'.join(convolver.drc_sets)

    def set_drc(x):
        result = convolver.set_drc(x)
        if result == 'done':
            preamp.state['drc_set'] = x
        return result

    def get_xo_sets(dummyarg):
        return '\n'.join(convolver.xo_sets)

    def set_xo(x):
        result = convolver.set_xo(x)
        if result == 'done':
            preamp.state['xo_set'] = x
        return result

    def get_target_sets(dummyarg):
        return '\n'.join(preamp.target_sets)

    def set_target(x):
        result = preamp.set_target(x)
        if result == 'done':
            preamp.state['target'] = x
        return result
        

    # Initiate the command processing
    result  = 'nothing has been done'

    # Processing the full_command phrase or doing nothing.
    command, arg, add = analize_full_command(full_command)
    # print('COMMAND:', command, 'ARG', arg, 'ADD', add)      # debug
    if not command:
        # Do nothing
        return result
    
    # Parsing the command to his related function from the above set of functions
    try:
        result = {
            'state':            get_state,
            'status':           get_state,
            'get_state':        get_state,
            'get_eq':           get_eq,
            'get_target_sets':  get_target_sets,
            'get_drc_sets':     get_drc_sets,
            'get_xo_sets':      get_xo_sets,

            'input':            set_source,
            'source':           set_source,
            'solo':             set_solo,
            'mono':             set_mono,
            'midside':          set_midside,
            'mute':             set_mute,

            'level':            set_level,
            'balance':          set_balance,
            'treble':           set_treble,
            'bass':             set_bass,
            'loudness':         set_loud_track,
            'loudness_track':   set_loud_track,
            'loudness_ref':     set_loud_ref,

            'set_drc':          set_drc,
            'drc':              set_drc,
            'xo':               set_xo,
            'set_xo':           set_xo,
            'set_target':       set_target
            } [ command ] ( arg )
    
    except KeyError:
        result = f'unknown command: {command}'
    
    except:
        result = f'problems processing command: {command}'

    return result

