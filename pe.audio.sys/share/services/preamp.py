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
"""

import  sys
from    os.path             import expanduser

UHOME = expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    miscel              import CONFIG
from    preamp_mod.core     import Preamp, Convolver


# INITIATE A PREAMP INSTANCE
preamp = Preamp()
if 'powersave' in CONFIG and CONFIG["powersave"] == True:
    preamp.powersave('on')
preamp.save_state()

# INITIATE A CONVOLVER INSTANCE (XO and DRC management)
convolver = Convolver()


# Interface function for this module
def do( cmd, argstring ):
    """ Processes commands for audio control

        (i) The full_command sintax:  <command> [arg [add] ]
            'arg' is given only with some commands,
                  as an option for relative values ordering.
    """

    def analize_arg_add(argstring):
        """ returns a tuple ( <arg>, <add:True|False> )
        """

        arg, add = '', False

        args_list = argstring.replace('\r', '').replace('\n', '').split()

        if args_list[0:]:
            if args_list[-1] == 'add':
                add = True
                arg = ' '.join( args_list[:-1] )
            else:
                arg = ' '.join( args_list[:] )

        return (arg, add)

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
        return open(f'{UHOME}/pe.audio.sys/doc/peaudiosys.hlp', 'r').read()


    # extract 'add' option for relative changes
    arg, add = analize_arg_add(argstring)

    # COMMAND PROCESSING by parsing the command to his related function:
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
            'subsonic':         preamp.set_subsonic,

            'level':            preamp.set_level,
            'volume':           preamp.set_level,
            'balance':          preamp.set_balance,
            'treble':           preamp.set_treble,
            'bass':             preamp.set_bass,
            'loudness':         preamp.set_equal_loudness,
            'eq_loudness':      preamp.set_equal_loudness,
            'equal_loudness':   preamp.set_equal_loudness,
            'lu_offset':        preamp.set_lu_offset,
            'set_target':       preamp.set_target,

            'set_drc':          set_drc,
            'drc':              set_drc,
            'set_xo':           set_xo,
            'xo':               set_xo,

            'convolver':        preamp.switch_convolver,
            'powersave':        preamp.powersave,

            'help':             print_help

            } [ cmd.lower() ] ( arg, add )

        # ************************************
        # ** KEEPING UPDATED THE STATE FILE **
        # ************************************
        if result:
            preamp.save_state()

    except KeyError:
        result = f'(preamp) unknown command: \'{cmd}\''

    except Exception as e:
        result = f'(preamp) {cmd} ERROR: {str(e)}'

    return result

